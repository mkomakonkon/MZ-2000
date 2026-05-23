import struct
import datetime
from collections import defaultdict

# ============================================================
# MID -> CMU-800 MZT Converter
# ============================================================

MZT_LOAD_ADDRESS = 0x337D

MEASURE_EVENT = bytes([0xFD, 0x0C, 0x06])
END_EVENT = bytes([0xFE, 0x0C, 0x06])

# MIDI:
TICKS_PER_BEAT = 480
TICKS_PER_MEASURE = 1920   # 4/4, 480 * 4

# CMU:
CMU_PER_BEAT = 24          # ★ここを 12→24 にしたことで 1小節≒96 になる


# ============================================================
# Utility
# ============================================================

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


# ============================================================
# MIDI NOTE
# ============================================================

class MidiNote:
    def __init__(self, channel, note, velocity, start_tick):
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.start_tick = start_tick
        self.end_tick = None


# ============================================================
# MIDI PARSER
# ============================================================

class MidiParser:
    def __init__(self, filename):
        self.filename = filename
        self.notes = []
        self.ppqn = 480

    def parse(self):
        with open(self.filename, 'rb') as f:
            data = f.read()

        if data[0:4] != b'MThd':
            raise Exception("Not MIDI")

        header_size = read_uint32_be(data, 4)
        midi_format = read_uint16_be(data, 8)
        num_tracks = read_uint16_be(data, 10)
        division = read_uint16_be(data, 12)
        self.ppqn = division

        print("FORMAT :", midi_format)
        print("TRACKS :", num_tracks)
        print("PPQN   :", division)

        pos = 8 + header_size

        for trk in range(num_tracks):
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


# ============================================================
# CMU EVENT
# ============================================================

class CmuEvent:
    def __init__(self, cv, st, gate, start_tick):
        self.cv = cv
        self.st = st
        self.gate = gate
        self.start_tick = start_tick   # 小節判定用に tick を保持


# ============================================================
# CMU CONVERTER
# ============================================================

class CmuConverter:
    def __init__(self, notes):
        self.notes = notes
        self.cmu_channels = defaultdict(list)
        for ch in range(0, 10):
            self.cmu_channels[ch] = []

    def ticks_to_cmu(self, ticks):
        v = round(ticks * CMU_PER_BEAT / TICKS_PER_BEAT)
        return max(1, min(v, 255))

    def note_to_cv(self, note):
        return note - 24   # C1=24 → CV=0

    def convert(self):
        for ch in range(1, 9):
            notes = [n for n in self.notes if n.channel == ch]
            self.convert_direct(notes, ch)

    def convert_direct(self, notes, cmu_ch):
        notes.sort(key=lambda x: x.start_tick)
        if not notes:
            return

        last_time = 0  # 曲頭 tick=0 からの経過

        for i, note in enumerate(notes):
            if note.end_tick is None:
                continue

            current_start = note.start_tick

            # 曲頭〜最初の NOTE ON、または前回 NOTE の next_start〜今回 NOTE ON の休符
            if current_start > last_time:
                rest_ticks = (current_start - last_time)/2
                rest_st = self.ticks_to_cmu(rest_ticks)
                rest_ev = CmuEvent(0, rest_st, 0, last_time)
                self.cmu_channels[cmu_ch].append(rest_ev)

            # 次の NOTE ON（なければこのノートの NOTE OFF）
            if i < len(notes) - 1:
                next_start = notes[i + 1].start_tick
            else:
                next_start = note.end_tick

            # ST：この NOTE ON から「次の NOTE ON」まで
            st_ticks = (next_start - current_start)/2

            # GT：この NOTE ON から NOTE OFF まで（実ゲート長）
            gate_ticks = (note.end_tick - current_start)/2

            st = self.ticks_to_cmu(st_ticks)
            gate = self.ticks_to_cmu(gate_ticks)

            # GT は ST を超えないように調整（ST-1 まで）
            if gate >= st:
                gate = st - 1 if st > 1 else 1

            cv = self.note_to_cv(note.note)

            ev = CmuEvent(cv, st, gate, current_start)
            self.cmu_channels[cmu_ch].append(ev)

            last_time = next_start

    def build_binary(self):
        TICKS_PER_MEASURE_HALF = TICKS_PER_MEASURE / 2
        out = bytearray()

        for ch in range(0, 10):
            events = self.cmu_channels[ch]
            events.sort(key=lambda x: x.start_tick)

            for i, ev in enumerate(events):
                # 出力順：CV, ST, GT
                out += bytes([
                    ev.cv & 0xFF,
                    ev.st & 0xFF,
                    ev.gate & 0xFF
                ])

                # 次イベントとの間で「MIDI の小節境界」を跨いだら FD0C06 を挿入
                if i < len(events) - 1:
                    next_ev = events[i + 1]

                    current_measure = (ev.start_tick   / 2) // TICKS_PER_MEASURE_HALF
                    next_measure    = (next_ev.start_tick / 2) // TICKS_PER_MEASURE_HALF

                    while current_measure < next_measure:
                        out += MEASURE_EVENT
                        current_measure += 1

            out += END_EVENT

        return out


# ============================================================
# MZT HEADER
# ============================================================

def build_mzt_header(data_size):

    header = bytearray(128)

    # +0: ファイルモード（属性）
    #   CMU-800はC8
    header[0x00] = 0xC8

    # +1〜+10: ファイルネーム（16文字以内）+ 0Dh
    #   まずスペースで埋める
    for i in range(0x01, 0x0F):
        header[i] = 0x20  # ' '

    today = datetime.datetime.now()
    filename = "MID2CMU" + today.strftime("%y%m%d")
    filename_bytes = filename.encode("ascii")

    # 最大 16 文字まで
    for i in range(min(len(filename_bytes), 16)):
        header[0x01 + i] = filename_bytes[i]

    # 末尾に 0Dh を付ける（ファイル名終端）
    header[0x01 + min(len(filename_bytes), 16)] = 0x0D

    # ここから先はキャプチャの並びに合わせる：
    #   ファイルサイズ
    #   ロードアドレス
    #   実行アドレス
    #
    # キャプチャでは、ファイルネーム領域の直後から
    # これらが順に並んでいる構造になっていましたので、
    # それに倣います。

    # 便宜上、オフセットを決め打ちします：
    #   +11〜+12: ファイルサイズ
    #   +13〜+14: ロードアドレス
    #   +15〜+16: 実行アドレス

    # ファイルサイズ（データブロックのサイズ）
    header[0x11] = data_size & 0xFF
    header[0x12] = (data_size >> 8) & 0xFF

    # ロードアドレス（0x337D 固定）
    header[0x13] = MZT_LOAD_ADDRESS & 0xFF
    header[0x14] = (MZT_LOAD_ADDRESS >> 8) & 0xFF

    # 実行アドレス（同じく 0x337D）
    header[0x15] = MZT_LOAD_ADDRESS & 0xFF
    header[0x16] = (MZT_LOAD_ADDRESS >> 8) & 0xFF

    return header

# ============================================================
# MAIN
# ============================================================

def convert_midi_to_mzt(midi_filename, output_filename):
    parser = MidiParser(midi_filename)
    parser.parse()

    print()
    print("NOTES :", len(parser.notes))

    converter = CmuConverter(parser.notes)
    converter.convert()

    binary = converter.build_binary()

    print("DATA SIZE :", len(binary))

    header = build_mzt_header(len(binary))

    with open(output_filename, "wb") as f:
        f.write(header)
        f.write(binary)

    print()
    print("DONE")
    print(output_filename)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print()
        print("Usage:")
        print("python mid2cmu.py input.mid output.mzt")
        print()
        sys.exit(0)

    convert_midi_to_mzt(sys.argv[1], sys.argv[2])
