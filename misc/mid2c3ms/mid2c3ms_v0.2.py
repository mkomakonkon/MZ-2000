import struct
import datetime
from collections import defaultdict

MZT_LOAD_ADDRESS = 0x8000
MEASURE_EVENT = bytes([0xFD, 0x0C, 0x06])  # 使わないが互換のため残しておく
END_EVENT = bytes([0xFF, 0x00, 0x00, 0x00, 0x00])  # 曲データ終了 (ヘッダ=FF, 残り4バイトは0埋め)


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

            # CH1〜CH3のみ使用する前提だが、パース自体は全CH行う
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
# クオンタイズ
# ---------------------------

def quantize_midi_notes(notes, ppqn):
    """
    MIDI ノートを「mid2cmuの倍の長さ」の 1ST 単位にクオンタイズする。
    mid2cmu: 1ST = PPQN / 24 tick → 4分音符 = 24ST
    mid2c3ms: 1ST = PPQN / 48 tick → 4分音符 = 48ST
    """
    tick_per_st = ppqn / 48.0

    for n in notes:
        n.start_tick = int(round(n.start_tick / tick_per_st) * tick_per_st)
        if n.end_tick is not None:
            n.end_tick = int(round(n.end_tick / tick_per_st) * tick_per_st)

    notes.sort(key=lambda x: x.start_tick)


def note_to_cv(note):
    """
    CMU と同じく note-24 を CV とする。
    0〜72 にクリップ。0 は休符扱い。
    """
    v = note - 24
    if v < 0:
        v = 0
    if v > 72:
        v = 72
    return v


def ticks_to_st(ticks, ppqn):
    if ticks <= 0:
        return 0

    # 4分音符 = 48 ST
    raw = ticks * 48.0 / ppqn

    # 6 の倍数に丸める（32分音符単位）
    st = int(round(raw / 6.0) * 6)

    # 最小 6、最大 192 に制限
    if st < 6:
        st = 6
    if st > 192:
        st = 192

    return st


# ---------------------------
# C3MS CONVERTER（三重和音）
# ---------------------------

class C3msConverter:
    def __init__(self, notes, ppqn):
        self.ppqn = ppqn
        # CH1〜CH3のみ使用
        self.channel_notes = {
            1: [],
            2: [],
            3: []
        }

        for n in notes:
            if n.end_tick is None:
                continue
            if n.channel in self.channel_notes:
                self.channel_notes[n.channel].append(n)

        for ch in self.channel_notes:
            self.channel_notes[ch].sort(key=lambda x: x.start_tick)

    def build_timeline(self):
        """
        CH1〜CH3の全ノートの開始・終了 tick を集めて、
        「音が変化するタイミング」の一覧を作る。
        """
        change_points = set()
        for ch in self.channel_notes:
            for n in self.channel_notes[ch]:
                change_points.add(n.start_tick)
                change_points.add(n.end_tick)

        if not change_points:
            return []

        points = sorted(change_points)
        # 先頭が 0 でなければ 0 を追加（曲頭の休符対応）
        if points[0] != 0:
            points = [0] + points

        return points

    def get_active_cv(self, ch, t_start, t_end):
        """
        区間 [t_start, t_end) において有効なノートがあればその CV、
        なければ 0（休符）を返す。
        単純に「t_start を含むノート」を探す。
        """
        notes = self.channel_notes[ch]
        for n in notes:
            if n.start_tick <= t_start < n.end_tick:
                return note_to_cv(n.note)
        return 0

    def convert(self):
        """
        ヘッダ(00), ST, CV1, CV2, CV3 の 5バイトを順に並べたバイナリを生成。
        ST は CV1〜CV3 のうち最短の音長に合わせて区切るが、
        これは「全CHのノート境界で区切る」ことで実現できる。
        """
        timeline = self.build_timeline()
        if not timeline or len(timeline) < 2:
            # ノートがない場合でも、終了ヘッダだけは出す
            return bytearray(END_EVENT)

        out = bytearray()

        for i in range(len(timeline) - 1):
            t_start = timeline[i]
            t_end = timeline[i + 1]
            ticks = t_end - t_start
            if ticks <= 0:
                continue

            st = ticks_to_st(ticks, self.ppqn)
            if st == 0:
                continue

            cv1 = self.get_active_cv(1, t_start, t_end)
            cv2 = self.get_active_cv(2, t_start, t_end)
            cv3 = self.get_active_cv(3, t_start, t_end)

            # 3chとも完全休符ならスキップしてもよいが、
            # 「休符も明示的に欲しい」場合はここを残す。
            # とりあえず休符も出力する仕様にしておく。
            out += bytes([
                0x00,          # ヘッダ: 音符データ
                st & 0xFF,     # 音長 ST
                cv1 & 0xFF,    # CV1
                cv2 & 0xFF,    # CV2
                cv3 & 0xFF     # CV3
            ])

        # 曲データ終了
        out += END_EVENT

        return out


# ---------------------------
# MZT HEADER
# ---------------------------

def build_mzt_header(data_size, user_filename=None):
    header = bytearray(128)

    # +00: ファイルモード (WICS は 01h 固定)
    header[0x00] = 0x01

    # +01〜+12: ファイル名（最大16文字）＋ 0Dh → 合計 17 バイト
    for i in range(0x01, 0x13):
        header[i] = 0x20

    if user_filename is None or user_filename.strip() == "":
        today = datetime.datetime.now()
        filename = "MID2C3MS" + today.strftime("%y%m%d")
    else:
        filename = user_filename.strip()

    filename_bytes = filename.encode("ascii", errors="ignore")

    for i in range(min(len(filename_bytes), 16)):
        header[0x01 + i] = filename_bytes[i]

    header[0x01 + min(len(filename_bytes), 16)] = 0x0D

    # +12〜+13: ファイルサイズ
    header[0x12] = data_size & 0xFF
    header[0x13] = (data_size >> 8) & 0xFF

    # +14〜+15: ロードアドレス 0x7000
    header[0x14] = MZT_LOAD_ADDRESS & 0xFF
    header[0x15] = (MZT_LOAD_ADDRESS >> 8) & 0xFF

    # +16〜+17: 実行アドレス 0x1503
    header[0x16] = 0x03
    header[0x17] = 0x15

    return header


# ---------------------------
# MAIN
# ---------------------------

def convert_midi_to_mzt(midi_filename, output_filename):
    user_filename = input("MZTファイル名を入力してください（Enterで自動命名）: ")

    parser = MidiParser(midi_filename)
    parser.parse()

    # クオンタイズ（mid2cmu の倍の長さ）
    quantize_midi_notes(parser.notes, parser.ppqn)

    converter = C3msConverter(parser.notes, parser.ppqn)
    binary = converter.convert()
    header = build_mzt_header(len(binary), user_filename)

    with open(output_filename, "wb") as f:
        f.write(header)
        f.write(binary)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python mid2c3ms.py input.mid output.mzt")
        sys.exit(0)

    convert_midi_to_mzt(sys.argv[1], sys.argv[2])
