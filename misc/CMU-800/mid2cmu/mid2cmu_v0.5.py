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
# MIDI NOTE
# ---------------------------

class MidiNote:
    def __init__(self, channel, note, velocity, start_tick):
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.start_tick = start_tick
        self.end_tick = None


# ---------------------------
# MIDI PARSER
# ---------------------------

class MidiParser:
    def __init__(self, filename):
        self.filename = filename
        self.notes = []
        self.ppqn = 480  # 初期値（実際にはヘッダで必ず上書きされる）

    def parse(self):
        with open(self.filename, 'rb') as f:
            data = f.read()

        if data[0:4] != b'MThd':
            raise Exception("Not MIDI")

        header_size = read_uint32_be(data, 4)
        midi_format = read_uint16_be(data, 8)
        num_tracks = read_uint16_be(data, 10)
        division = read_uint16_be(data, 12)
        self.ppqn = division  # 分解能をそのまま使用

        pos = 8 + header_size

        for _ in range(num_tracks):
            if data[pos:pos + 4] != b'MTrk':
                raise Exception("MTrk not found")

            track_size = read_uint32_be(data, pos + 4)
            track_data = data[pos + 8: pos + 8 + track_size]
            self.parse_track(track_data)
            pos += 8 + track_size

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
    def __init__(self, notes, ppqn):
        self.notes = notes
        self.ppqn = ppqn
        self.TICKS_PER_BEAT = ppqn
        self.TICKS_PER_MEASURE = ppqn * 4  # 4/4 前提
        self.cmu_channels = defaultdict(list)

    def ticks_to_cmu(self, ticks):
        v = round(ticks * 24 / self.TICKS_PER_BEAT)
        return max(1, v)

    def note_to_cv(self, note):
        return note - 24

    def convert(self):
        for ch in range(1, 9):
            ch_notes = [n for n in self.notes if n.channel == ch]
            self.convert_channel(ch_notes, ch)

    def convert_channel(self, notes, cmu_ch):
        notes.sort(key=lambda x: x.start_tick)
        if not notes:
            return

        last_time = 0

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
                measure_idx = last_time // self.TICKS_PER_MEASURE
                measure_end = (measure_idx + 1) * self.TICKS_PER_MEASURE
                seg_end = min(note_on, measure_end)

                rest_ticks = seg_end - last_time
                if rest_ticks > 0:
                    st = self.ticks_to_cmu(rest_ticks)
                    ev = CmuEvent(0, st, 0, last_time)
                    self.cmu_channels[cmu_ch].append(ev)

                last_time = seg_end

            # 2) ノート区間
            seg_start = note_on
            while seg_start < next_start:
                measure_idx = seg_start // self.TICKS_PER_MEASURE
                measure_end = (measure_idx + 1) * self.TICKS_PER_MEASURE
                seg_end = min(next_start, measure_end)

                st_ticks = seg_end - seg_start

                if seg_start < note_off:
                    gate_ticks = max(0, min(seg_end, note_off) - seg_start)
                    cv = cv_note
                else:
                    gate_ticks = 0
                    cv = 0

                st = self.ticks_to_cmu(st_ticks)
                gate = self.ticks_to_cmu(gate_ticks) if gate_ticks > 0 else 0

                # ★ 小節またぎ判定（最重要）
                #   ・このセグメントが小節末尾まで伸びている
                #   ・ノート自体は次小節まで続いている
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
        for ch in range(0, 10):
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

        return out


# ---------------------------
# MZT HEADER
# ---------------------------

def build_mzt_header(data_size, user_filename=None):
    header = bytearray(128)

    # +00: ファイルモード (CMU-800 は C8h 固定)
    header[0x00] = 0xC8

    # +01〜+12: ファイル名（最大16文字）＋ 0Dh → 合計 17 バイト
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

def quantize_midi_notes(notes, ppqn):
    """
    MIDI ノートを CMU の 1ST 単位にクオンタイズする。
    1ST = PPQN / 24 tick に丸めることで、ST 計算時の誤差を完全に消す。
    """
    tick_per_st = ppqn / 24

    for n in notes:
        # 開始 tick を 1ST 単位に丸める
        n.start_tick = int(round(n.start_tick / tick_per_st) * tick_per_st)

        # 終了 tick も丸める
        if n.end_tick is not None:
            n.end_tick = int(round(n.end_tick / tick_per_st) * tick_per_st)

    # ノート順序が変わる可能性があるのでソートし直す
    notes.sort(key=lambda x: x.start_tick)


# ---------------------------
# MAIN
# ---------------------------

def convert_midi_to_mzt(midi_filename, output_filename):
    user_filename = input("MZTファイル名を入力してください（Enterで自動命名）: ")

    parser = MidiParser(midi_filename)
    parser.parse()

    # ★ クオンタイズ前処理（ここが重要）
    quantize_midi_notes(parser.notes, parser.ppqn)

    converter = CmuConverter(parser.notes, parser.ppqn)
    converter.convert()

    binary = converter.build_binary()
    header = build_mzt_header(len(binary), user_filename)

    with open(output_filename, "wb") as f:
        f.write(header)
        f.write(binary)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python mid2cmu.py input.mid output.mzt")
        sys.exit(0)

    convert_midi_to_mzt(sys.argv[1], sys.argv[2])
