import struct
import datetime
from collections import defaultdict

MZT_LOAD_ADDRESS = 0x337D
MEASURE_EVENT = bytes([0xFD, 0x0C, 0x06])
END_EVENT = bytes([0xFE, 0x0C, 0x06])

# ---------------------------
# Utility
# ---------------------------

def read_uint32_be(data, offset):
    return struct.unpack('>I', data[offset:offset + 4])[0]

def read_uint16_be(data, offset):
    return struct.unpack('>H', data[offset:offset + 2])[0]

def read_vlq(data, pos):
    value = 0
    while True:
        b = data[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if (b & 0x80) == 0:
            break
    return value, pos

# ---------------------------
# MIDI NOTE & TEMPO MAP
# ---------------------------

class MidiNote:
    def __init__(self, channel, note, velocity, start_tick):
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.start_tick = start_tick
        self.end_tick = None


class TempoMap:
    def __init__(self):
        # (tick, bpm)
        self.events = []

    def add_tempo(self, tick, microseconds_per_quarter):
        bpm = 60000000.0 / microseconds_per_quarter
        self.events.append((tick, bpm))

    def finalize(self):
        self.events.sort(key=lambda x: x[0])
        # tick 0 にテンポ設定がなければデフォルト120BPMとする
        if not self.events or self.events[0][0] > 0:
            self.events.insert(0, (0, 120.0))

# ---------------------------
# MIDI PARSER
# ---------------------------

class MidiParser:
    def __init__(self, filename):
        self.filename = filename
        self.notes = []
        self.tempo_map = TempoMap()
        self.ppqn = 480

    def parse(self):
        with open(self.filename, 'rb') as f:
            data = f.read()

        if data[0:4] != b'MThd':
            raise Exception("Not MIDI")

        header_size = read_uint32_be(data, 4)
        num_tracks = read_uint16_be(data, 10)
        division = read_uint16_be(data, 12)
        self.ppqn = division

        pos = 8 + header_size

        for _ in range(num_tracks):
            if data[pos:pos + 4] != b'MTrk':
                raise Exception("MTrk not found")

            track_size = read_uint32_be(data, pos + 4)
            track_data = data[pos + 8: pos + 8 + track_size]
            self.parse_track(track_data)
            pos += 8 + track_size

        self.tempo_map.finalize()

    def parse_track(self, track_data):
        pos = 0
        tick = 0
        running_status = None
        active_notes = {}

        while pos < len(track_data):
            delta, pos = read_vlq(track_data, pos)
            tick += delta
            status = track_data[pos]

            if status < 0x80:
                status = running_status
            else:
                pos += 1
                running_status = status

            if status == 0xFF:
                meta_type = track_data[pos]
                pos += 1
                length, pos = read_vlq(track_data, pos)

                # テンポ変更イベント (FF 51 03)
                if meta_type == 0x51 and length == 3:
                    mpq = (track_data[pos] << 16) | (track_data[pos + 1] << 8) | track_data[pos + 2]
                    self.tempo_map.add_tempo(tick, mpq)

                pos += length
                continue

            if status in [0xF0, 0xF7]:
                length, pos = read_vlq(track_data, pos)
                pos += length
                continue

            event_type = status & 0xF0
            channel = (status & 0x0F) + 1

            if event_type == 0x90:
                note = track_data[pos]
                velocity = track_data[pos + 1]
                pos += 2

                if velocity == 0:
                    key = (channel, note)
                    if key in active_notes:
                        active_notes[key].end_tick = tick
                        self.notes.append(active_notes[key])
                        del active_notes[key]
                else:
                    n = MidiNote(channel, note, velocity, tick)
                    active_notes[(channel, note)] = n

            elif event_type == 0x80:
                note = track_data[pos]
                velocity = track_data[pos + 1]
                pos += 2
                key = (channel, note)
                if key in active_notes:
                    active_notes[key].end_tick = tick
                    self.notes.append(active_notes[key])
                    del active_notes[key]

            elif event_type in [0xA0, 0xB0, 0xE0]:
                pos += 2

            elif event_type in [0xC0, 0xD0]:
                pos += 1

# ---------------------------
# CMU EVENT
# ---------------------------

class CmuEvent:
    def __init__(self, cv, st, gate, start_tick):
        self.cv = cv
        self.st = st
        self.gate = gate
        self.start_tick = start_tick


# ---------------------------
# CMU CONVERTER
# ---------------------------

class CmuConverter:
    def __init__(self, notes, ppqn, tempo_map=None, default_bpm=None):
        self.notes = notes
        self.ppqn = ppqn
        self.tempo_map = tempo_map
        self.default_bpm = default_bpm
        self.TICKS_PER_BEAT = ppqn
        self.TICKS_PER_MEASURE = ppqn * 4  # 4/4 前提
        self.cmu_channels = defaultdict(list)

    def get_current_bpm(self, tick):
        if not self.tempo_map or not self.tempo_map.events:
            return 120.0
        
        current_bpm = self.tempo_map.events[0][1]
        for t, bpm in self.tempo_map.events:
            if tick >= t:
                current_bpm = bpm
            else:
                break
        return current_bpm

    def get_measure_total_st(self, measure_start_tick):
        """小節全体の目標 TOTAL ST を計算（全CH共通）"""
        if self.default_bpm is not None:
            pseudo_bpm = self.get_current_bpm(measure_start_tick)
            # 96 * デフォルトBPM / 疑似BPM
            total_st = round(96.0 * self.default_bpm / pseudo_bpm)
            return max(1, total_st)
        else:
            return 96  # デフォルト（24 * 4 = 96）

    def note_to_cv(self, note):
        return note - 24

    def convert(self):
        # ★ CH1〜16すべて変換対象にする
        for ch in range(1, 17):
            ch_notes = [n for n in self.notes if n.channel == ch]
            self.convert_channel(ch_notes, ch)

    def convert_channel(self, notes, cmu_ch):
        notes.sort(key=lambda x: x.start_tick)
        if not notes:
            return

        last_time = 0

        # 小節内での補正（合わせ込み）用変数
        current_measure_idx = -1
        measure_start_tick = 0
        measure_total_st = 96
        accumulated_st = 0

        for i, note in enumerate(notes):
            if note.end_tick is None:
                continue

            note_on = note.start_tick
            note_off = note.end_tick
            cv_note = self.note_to_cv(note.note)

            # 次のノート開始位置
            if i < len(notes) - 1:
                next_start = notes[i + 1].start_tick
            else:
                next_start = note_off

            # 1) 無音区間（休符）
            while last_time < note_on:
                m_idx = last_time // self.TICKS_PER_MEASURE
                if m_idx != current_measure_idx:
                    current_measure_idx = m_idx
                    measure_start_tick = m_idx * self.TICKS_PER_MEASURE
                    measure_total_st = self.get_measure_total_st(measure_start_tick)
                    accumulated_st = 0

                measure_end = measure_start_tick + self.TICKS_PER_MEASURE
                seg_end = min(note_on, measure_end)

                # 小節内位置(0.0〜1.0)に基づく目標累積ST
                target_accumulated_st = round(((seg_end - measure_start_tick) / self.TICKS_PER_MEASURE) * measure_total_st)
                st = max(1, target_accumulated_st - accumulated_st)
                accumulated_st += st

                ev = CmuEvent(0, st, 0, last_time)
                self.cmu_channels[cmu_ch].append(ev)

                last_time = seg_end

            # 2) ノート区間
            seg_start = note_on
            while seg_start < next_start:
                m_idx = seg_start // self.TICKS_PER_MEASURE
                if m_idx != current_measure_idx:
                    current_measure_idx = m_idx
                    measure_start_tick = m_idx * self.TICKS_PER_MEASURE
                    measure_total_st = self.get_measure_total_st(measure_start_tick)
                    accumulated_st = 0

                measure_end = measure_start_tick + self.TICKS_PER_MEASURE
                seg_end = min(next_start, measure_end)

                # 小節内位置(0.0〜1.0)に基づく目標累積ST
                target_accumulated_st = round(((seg_end - measure_start_tick) / self.TICKS_PER_MEASURE) * measure_total_st)
                st = max(1, target_accumulated_st - accumulated_st)
                accumulated_st += st

                # GATEタイム計算
                if seg_start < note_off:
                    gate_ticks = max(0, min(seg_end, note_off) - seg_start)
                    gate_ratio = gate_ticks / (seg_end - seg_start) if seg_end > seg_start else 0
                    gate = max(1, round(st * gate_ratio))
                    cv = cv_note
                else:
                    gate = 0
                    cv = 0

                # ★ 小節またぎ判定とGATE調整
                if seg_end == measure_end and note_off > measure_end:
                    gate = st
                else:
                    if gate > 0 and gate >= st:
                        gate = st - 1 if st > 1 else 1

                ev = CmuEvent(cv, st, gate, seg_start)
                self.cmu_channels[cmu_ch].append(ev)

                seg_start = seg_end

            last_time = next_start

    def build_binary(self):
        out = bytearray()

        # CH0〜8 までのイベントを出力
        for ch in range(0, 9):
            events = self.cmu_channels[ch]
            events.sort(key=lambda x: x.start_tick)

            for i, ev in enumerate(events):
                out += bytes([
                    ev.cv & 0xFF,
                    ev.st & 0xFF,
                    ev.gate & 0xFF
                ])

                if i < len(events) - 1:
                    next_ev = events[i + 1]
                    current_measure = ev.start_tick // self.TICKS_PER_MEASURE
                    next_measure = next_ev.start_tick // self.TICKS_PER_MEASURE
                    while current_measure < next_measure:
                        out += MEASURE_EVENT
                        current_measure += 1

            out += END_EVENT

        # CH9 は生成しないが、末尾（END_EVENT）のみを追加
        out += END_EVENT

        return out

# ---------------------------
# MZT HEADER
# ---------------------------

def build_mzt_header(data_size, user_filename=None):
    header = bytearray(128)

    # +00: ファイルモード (CMU-800 は C8h 固定)
    header[0x00] = 0xC8

    # +01〜+12: ファイル名（最大16文字）＋ 0Dh → 合計17バイト
    for i in range(0x01, 0x13):
        header[i] = 0x20

    if user_filename is None or user_filename.strip() == "":
        today = datetime.datetime.now()
        filename = "MID2CMU" + today.strftime("%y%m%d")
    else:
        filename = user_filename.strip()

    filename_bytes = filename.encode("ascii", errors="ignore")

    for i in range(min(len(filename_bytes), 16)):
        header[0x01 + i] = filename_bytes[i]

    header[0x01 + min(len(filename_bytes), 16)] = 0x0D

    # +12〜+13: ファイルサイズ
    header[0x12] = data_size & 0xFF
    header[0x13] = (data_size >> 8) & 0xFF

    # +14〜+15: ロードアドレス 0x337D
    header[0x14] = MZT_LOAD_ADDRESS & 0xFF
    header[0x15] = (MZT_LOAD_ADDRESS >> 8) & 0xFF

    # +16〜+17: 実行アドレス 12A0h
    header[0x16] = 0xA0
    header[0x17] = 0x12

    return header


# ---------------------------
# QUANTIZE
# ---------------------------

def quantize_midi_notes(notes, ppqn):
    tick_per_st = ppqn / 24

    for n in notes:
        n.start_tick = int(round(n.start_tick / tick_per_st) * tick_per_st)
        if n.end_tick is not None:
            n.end_tick = int(round(n.end_tick / tick_per_st) * tick_per_st)

    notes.sort(key=lambda x: x.start_tick)


# ---------------------------
# TEMPO HELPER
# ---------------------------

def prompt_default_bpm():
    user_input = input("TEMPO可変機能を使う場合はデフォルトBPMを入力してください。(使わない場合はEnter): ").strip()
    if not user_input:
        return None
    try:
        return float(user_input)
    except ValueError:
        print("無効な入力のため、TEMPO可変機能はオフで処理します。")
        return None


# ---------------------------
# 2分割出力
# ---------------------------

def convert_midi_to_two_mzt(midi_filename, output1, output2):
    default_bpm = prompt_default_bpm()

    parser = MidiParser(midi_filename)
    parser.parse()

    quantize_midi_notes(parser.notes, parser.ppqn)

    # CH1〜8 → output1
    notes_1_8 = [n for n in parser.notes if 1 <= n.channel <= 8]
    converter1 = CmuConverter(notes_1_8, parser.ppqn, parser.tempo_map, default_bpm)
    converter1.convert()
    binary1 = converter1.build_binary()
    header1 = build_mzt_header(len(binary1), "OUT1")

    with open(output1, "wb") as f:
        f.write(header1)
        f.write(binary1)

    # CH11〜16 → CMU CH1〜6 にマッピングして output2.mzt を作る
    notes_map = []
    for n in parser.notes:
        if n.channel == 11:
            notes_map.append(MidiNote(1, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick
        elif n.channel == 12:
            notes_map.append(MidiNote(2, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick
        elif n.channel == 13:
            notes_map.append(MidiNote(3, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick
        elif n.channel == 14:
            notes_map.append(MidiNote(4, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick
        elif n.channel == 15:
            notes_map.append(MidiNote(5, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick
        elif n.channel == 16:
            notes_map.append(MidiNote(6, n.note, n.velocity, n.start_tick))
            notes_map[-1].end_tick = n.end_tick

    converter2 = CmuConverter(notes_map, parser.ppqn, parser.tempo_map, default_bpm)
    converter2.convert()
    binary2 = converter2.build_binary()
    header2 = build_mzt_header(len(binary2), "OUT2")

    with open(output2, "wb") as f:
        f.write(header2)
        f.write(binary2)


# ---------------------------
# MAIN
# ---------------------------

def convert_midi_to_mzt(midi_filename, output_filename):
    default_bpm = prompt_default_bpm()

    user_filename = input("MZTファイル名を入力してください（Enterで自動命名）: ")

    parser = MidiParser(midi_filename)
    parser.parse()

    quantize_midi_notes(parser.notes, parser.ppqn)

    converter = CmuConverter(parser.notes, parser.ppqn, parser.tempo_map, default_bpm)
    converter.convert()

    binary = converter.build_binary()
    header = build_mzt_header(len(binary), user_filename)

    with open(output_filename, "wb") as f:
        f.write(header)
        f.write(binary)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        convert_midi_to_mzt(sys.argv[1], sys.argv[2])

    elif len(sys.argv) == 4:
        convert_midi_to_two_mzt(sys.argv[1], sys.argv[2], sys.argv[3])

    else:
        print("Usage:")
        print("  python mid2cmu.py input.mid output.mzt")
        print("  python mid2cmu.py input.mid output1.mzt output2.mzt")
        sys.exit(0)