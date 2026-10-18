import struct
import datetime
from collections import defaultdict

MZT_LOAD_ADDRESS = 0x337D
MEASURE_EVENT = bytes([0xFD, 0x0C, 0x06])
END_EVENT = bytes([0xFE, 0x0C, 0x06])

# ドラムノート (MIDI Note -> CMU Drum Bit) マッピング
DRUM_NOTE_MAP = {
    # bit6 (B)
    35: 1 << 6, 36: 1 << 6,
    # bit5 (S)
    38: 1 << 5, 40: 1 << 5,
    # bit4 (L)
    41: 1 << 4, 43: 1 << 4, 45: 1 << 4, 47: 1 << 4,
    # bit3 (H)
    48: 1 << 3, 50: 1 << 3,
    # bit2 (Y)
    49: 1 << 2, 57: 1 << 2, 51: 1 << 2, 52: 1 << 2, 53: 1 << 2, 55: 1 << 2, 59: 1 << 2,
    # bit1 (O)
    46: 1 << 1,
    # bit0 (C)
    42: 1 << 0, 44: 1 << 0
}

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
        self.events = []

    def add_tempo(self, tick, microseconds_per_quarter):
        bpm = 60000000.0 / microseconds_per_quarter
        self.events.append((tick, bpm))

    def finalize(self):
        self.events.sort(key=lambda x: x[0])
        if not self.events or self.events[0][0] > 0:
            self.events.insert(0, (0, 120.0))

    def get_tempo_summary(self, max_tick):
        if not self.events:
            return []
        
        tempo_durations = defaultdict(float)
        sorted_events = sorted(self.events, key=lambda x: x[0])
        
        total_ticks = max(max_tick, sorted_events[-1][0])
        if total_ticks == 0:
            return [(sorted_events[0][1], 100.0)]

        for i in range(len(sorted_events)):
            t_start, bpm = sorted_events[i]
            if i < len(sorted_events) - 1:
                t_end = sorted_events[i + 1][0]
            else:
                t_end = total_ticks
            
            duration = t_end - t_start
            if duration > 0:
                tempo_durations[bpm] += duration

        summary = []
        sum_dur = sum(tempo_durations.values())
        if sum_dur == 0:
            sum_dur = 1

        for bpm, dur in sorted(tempo_durations.items(), key=lambda x: x[0]):
            percentage = (dur / sum_dur) * 100.0
            summary.append((bpm, percentage))
        
        return summary

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
    def __init__(self, cv, st, gate, start_tick=0):
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
        self.drum_measure_patterns = []

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
        if self.default_bpm is not None:
            pseudo_bpm = self.get_current_bpm(measure_start_tick)
            total_st = round(96.0 * self.default_bpm / pseudo_bpm)
            return max(1, total_st)
        else:
            return 96

    def note_to_cv(self, note):
        adjusted_note = note
        while adjusted_note < 24:
            adjusted_note += 12
        return adjusted_note - 24

    def convert(self):
        drum_notes = [n for n in self.notes if n.channel == 10]
        if drum_notes:
            self.convert_drum_system(drum_notes)

        for ch in range(1, 9):
            ch_notes = [n for n in self.notes if n.channel == ch]
            self.convert_channel(ch_notes, ch)

    def convert_channel(self, notes, cmu_ch):
        notes.sort(key=lambda x: x.start_tick)
        if not notes:
            return

        last_time = 0
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

            if i < len(notes) - 1:
                next_start = notes[i + 1].start_tick
            else:
                next_start = note_off

            while last_time < note_on:
                m_idx = last_time // self.TICKS_PER_MEASURE
                if m_idx != current_measure_idx:
                    current_measure_idx = m_idx
                    measure_start_tick = m_idx * self.TICKS_PER_MEASURE
                    measure_total_st = self.get_measure_total_st(measure_start_tick)
                    accumulated_st = 0

                measure_end = measure_start_tick + self.TICKS_PER_MEASURE
                seg_end = min(note_on, measure_end)

                target_accumulated_st = round(((seg_end - measure_start_tick) / self.TICKS_PER_MEASURE) * measure_total_st)
                st = max(1, target_accumulated_st - accumulated_st)
                accumulated_st += st

                ev = CmuEvent(0, st, 0, last_time)
                self.cmu_channels[cmu_ch].append(ev)

                last_time = seg_end

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

                target_accumulated_st = round(((seg_end - measure_start_tick) / self.TICKS_PER_MEASURE) * measure_total_st)
                st = max(1, target_accumulated_st - accumulated_st)
                accumulated_st += st

                if seg_start < note_off:
                    gate_ticks = max(0, min(seg_end, note_off) - seg_start)
                    gate_ratio = gate_ticks / (seg_end - seg_start) if seg_end > seg_start else 0
                    gate = max(1, round(st * gate_ratio))
                    cv = cv_note
                else:
                    gate = 0
                    cv = 0

                if seg_end == measure_end and note_off > measure_end:
                    gate = st
                else:
                    if gate > 0 and gate >= st:
                        gate = st - 1 if st > 1 else 1

                ev = CmuEvent(cv, st, gate, seg_start)
                self.cmu_channels[cmu_ch].append(ev)

                seg_start = seg_end

            last_time = next_start

    def _build_drum_pattern_events(self, start_tick, end_tick, total_st, tick_drums):
        max_steps = 16
        measure_ticks = sorted([t for t in tick_drums.keys() if start_tick <= t < end_tick])
        measure_pattern_events = []

        can_use_standard_st = True
        step_ticks = (end_tick - start_tick) // max_steps if max_steps > 0 else 1
        
        if measure_ticks and step_ticks > 0:
            for t in measure_ticks:
                if (t - start_tick) % step_ticks != 0:
                    can_use_standard_st = False
                    break

        if can_use_standard_st:
            accumulated_st = 0
            for step in range(max_steps):
                step_start_tick = start_tick + (step * step_ticks)
                step_end_tick = step_start_tick + step_ticks

                target_accumulated_st = round(((step + 1) / max_steps) * total_st)
                st = max(1, target_accumulated_st - accumulated_st)
                accumulated_st += st

                drum_pattern = 0
                for t, pat in tick_drums.items():
                    if step_start_tick <= t < step_end_tick:
                        drum_pattern |= pat

                cmu_drum_val = 0x7F ^ drum_pattern
                gate = 1 if drum_pattern != 0 else 0
                measure_pattern_events.append((cmu_drum_val, st, gate))
        else:
            assigned_st_sum = 0
            for i in range(max_steps):
                if i < len(measure_ticks):
                    current_t = measure_ticks[i]
                    next_t = measure_ticks[i + 1] if i + 1 < len(measure_ticks) else end_tick

                    if i == 0 and current_t > start_tick:
                        rest_target_st = round(((current_t - start_tick) / (end_tick - start_tick)) * total_st)
                        st = max(1, rest_target_st - assigned_st_sum)
                        assigned_st_sum += st
                        measure_pattern_events.append((0x7F, st, 0))
                    
                    target_accumulated_st = round(((next_t - start_tick) / (end_tick - start_tick)) * total_st)
                    st = max(1, target_accumulated_st - assigned_st_sum)
                    assigned_st_sum += st

                    drum_pattern = tick_drums[current_t]
                    cmu_drum_val = 0x7F ^ drum_pattern
                    gate = 1
                    measure_pattern_events.append((cmu_drum_val, st, gate))
                else:
                    measure_pattern_events.append((0x7F, 0, 0))

            while len(measure_pattern_events) < max_steps:
                measure_pattern_events.append((0x7F, 0, 0))
            measure_pattern_events = measure_pattern_events[:max_steps]

        return measure_pattern_events

    def convert_drum_system(self, notes):
        tick_drums = defaultdict(int)
        max_tick = 0
        for n in notes:
            if n.note in DRUM_NOTE_MAP:
                tick_drums[n.start_tick] |= DRUM_NOTE_MAP[n.note]
                if n.start_tick > max_tick:
                    max_tick = n.start_tick

        if max_tick == 0 and not tick_drums:
            return

        total_measures = (max_tick // self.TICKS_PER_MEASURE) + 1
        steps_per_measure = 16
        step_ticks = self.TICKS_PER_MEASURE // steps_per_measure

        pattern_registry = {}  
        pattern_list = []      

        cmu_measure_counter = 1

        for m_idx in range(total_measures):
            m_start_tick = m_idx * self.TICKS_PER_MEASURE
            m_end_tick = m_start_tick + self.TICKS_PER_MEASURE
            total_st = self.get_measure_total_st(m_start_tick)

            measure_ticks = sorted([t for t in tick_drums.keys() if m_start_tick <= t < m_end_tick])

            if len(measure_ticks) > 16:
                mid_tick = m_start_tick + (self.TICKS_PER_MEASURE // 2)
                st_part1 = total_st // 2
                st_part2 = total_st - st_part1

                pat1_events = self._build_drum_pattern_events(m_start_tick, mid_tick, st_part1, tick_drums)
                pat2_events = self._build_drum_pattern_events(mid_tick, m_end_tick, st_part2, tick_drums)

                key1 = tuple(pat1_events)
                if key1 not in pattern_registry:
                    pid1 = len(pattern_registry) + 1
                    pattern_registry[key1] = pid1
                    pattern_list.append(pat1_events)
                else:
                    pid1 = pattern_registry[key1]

                key2 = tuple(pat2_events)
                if key2 not in pattern_registry:
                    pid2 = len(pattern_registry) + 1
                    pattern_registry[key2] = pid2
                    pattern_list.append(pat2_events)
                else:
                    pid2 = pattern_registry[key2]

                print(f"CH0:PATTERN{pid1}に収まらなかったためPATTERN{pid2}を追加")
                print(f"CH9:MEAS{cmu_measure_counter},MEAS{cmu_measure_counter+1}が対象")

                self.drum_measure_patterns.append(pid1)
                self.drum_measure_patterns.append(pid2)

                cmu_measure_counter += 2

            else:
                can_use_standard_st6 = True
                if measure_ticks:
                    for t in measure_ticks:
                        if (t - m_start_tick) % step_ticks != 0:
                            can_use_standard_st6 = False
                            break

                measure_pattern_events = self._build_drum_pattern_events(m_start_tick, m_end_tick, total_st, tick_drums)

                pattern_key = tuple(measure_pattern_events)
                if pattern_key not in pattern_registry:
                    pattern_id = len(pattern_registry) + 1
                    pattern_registry[pattern_key] = pattern_id
                    pattern_list.append(measure_pattern_events)
                else:
                    pattern_id = pattern_registry[pattern_key]

                self.drum_measure_patterns.append(pattern_id)
                cmu_measure_counter += 1

        for pat_events in pattern_list:
            for cv, st, gate in pat_events:
                self.cmu_channels[0].append(CmuEvent(cv, st, gate))

    def build_binary(self):
        out = bytearray()

        # 1) CH0 (パターンデータ) の構築
        ch0_events = self.cmu_channels[0]
        for i, ev in enumerate(ch0_events):
            out += bytes([ev.cv & 0xFF, ev.st & 0xFF, ev.gate & 0xFF])
            if (i + 1) % 16 == 0:
                out += MEASURE_EVENT
        out += END_EVENT

        # 2) CH1 〜 CH8 (メロディデータ) の構築
        for ch in range(1, 9):
            events = self.cmu_channels[ch]
            events.sort(key=lambda x: x.start_tick)

            for i, ev in enumerate(events):
                out += bytes([ev.cv & 0xFF, ev.st & 0xFF, ev.gate & 0xFF])

                if i < len(events) - 1:
                    next_ev = events[i + 1]
                    current_measure = ev.start_tick // self.TICKS_PER_MEASURE
                    next_measure = next_ev.start_tick // self.TICKS_PER_MEASURE
                    while current_measure < next_measure:
                        out += MEASURE_EVENT
                        current_measure += 1

            if events:
                out += MEASURE_EVENT
            out += END_EVENT

        # 3) CH9 (小節ごとのパターン番号指定) の構築
        for pat_id in self.drum_measure_patterns:
            out += bytes([pat_id & 0xFF, 0x00, 0x00])

        # CH9の最後は MEASURE_EVENT を挟まずに END_EVENT のみ
        out += END_EVENT

        return out

# ---------------------------
# MZT HEADER
# ---------------------------

def build_mzt_header(data_size, user_filename=None):
    header = bytearray(128)
    header[0x00] = 0xC8

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
    header[0x12] = data_size & 0xFF
    header[0x13] = (data_size >> 8) & 0xFF
    header[0x14] = MZT_LOAD_ADDRESS & 0xFF
    header[0x15] = (MZT_LOAD_ADDRESS >> 8) & 0xFF
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

def prompt_default_bpm(tempo_summary):
    print("\n[MIDI テンポ分析結果]")
    if len(tempo_summary) == 1:
        bpm, pct = tempo_summary[0]
        print(f"  検出されたテンポ: BPM {bpm:.1f} ({pct:.1f}%)")
    else:
        print("  検出されたテンポ一覧:")
        for bpm, pct in tempo_summary:
            print(f"    - BPM {bpm:.1f}: {pct:.1f}%")
    print("-" * 25)

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
    parser = MidiParser(midi_filename)
    parser.parse()

    max_tick = 0
    if parser.notes:
        max_tick = max(n.end_tick if n.end_tick is not None else n.start_tick for n in parser.notes)
    tempo_summary = parser.tempo_map.get_tempo_summary(max_tick)

    default_bpm = prompt_default_bpm(tempo_summary)

    quantize_midi_notes(parser.notes, parser.ppqn)

    # CH1〜8, CH10(Drum) -> output1
    notes_1_8 = [n for n in parser.notes if (1 <= n.channel <= 8) or n.channel == 10]
    converter1 = CmuConverter(notes_1_8, parser.ppqn, parser.tempo_map, default_bpm)
    converter1.convert()
    binary1 = converter1.build_binary()
    header1 = build_mzt_header(len(binary1), "OUT1")

    with open(output1, "wb") as f:
        f.write(header1)
        f.write(binary1)

    # CH11〜16 -> CMU CH1〜6 マッピング -> output2
    notes_map = []
    for n in parser.notes:
        if 11 <= n.channel <= 16:
            mapped_ch = n.channel - 10
            mn = MidiNote(mapped_ch, n.note, n.velocity, n.start_tick)
            mn.end_tick = n.end_tick
            notes_map.append(mn)

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
    parser = MidiParser(midi_filename)
    parser.parse()

    max_tick = 0
    if parser.notes:
        max_tick = max(n.end_tick if n.end_tick is not None else n.start_tick for n in parser.notes)
    tempo_summary = parser.tempo_map.get_tempo_summary(max_tick)

    default_bpm = prompt_default_bpm(tempo_summary)

    user_filename = input("MZTファイル名を入力してください（Enterで自動命名）: ")

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