import sys
import re
from mido import Message, MidiFile, MidiTrack, MetaMessage

PPQN = 480  # mid2cmu.py と完全互換
ST_PER_MEASURE = 96  # CMU基準：1小節＝96ST

NOTE_TABLE = {
    'c': 0, 'c+': 1,
    'd': 2, 'd+': 3,
    'e': 4,
    'f': 5, 'f+': 6,
    'g': 7, 'g+': 8,
    'a': 9, 'a+': 10,
    'b': 11
}

# 🎵 ドラムノート割り当て（こまさん仕様）
DRUM_MAP = {
    7: 42,  # Closed HH
    8: 46,  # Open HH
    9: 49,  # Cymbal
    10: 50, # High Tom
    11: 45, # Low Tom
    12: 38, # Snare
    13: 36  # Bass Drum
}

def st_to_ticks(st):
    """CMUのSTをMIDI tickに変換"""
    ticks_per_st = (PPQN * 4) / ST_PER_MEASURE
    return int(st * ticks_per_st)

def parse_length(tokens, idx, last_length):
    """音長（数字）と付点（.）とタイ（^）を処理してSTを返す"""
    length = last_length
    dot_count = 0
    tie = False

    if idx < len(tokens) and tokens[idx].isdigit():
        length = int(tokens[idx])
        idx += 1

    if length == 0:
        length = last_length
    if length <= 0:
        length = 4  # デフォルト4分音符

    while idx < len(tokens) and tokens[idx] == '.':
        dot_count += 1
        idx += 1

    if idx < len(tokens) and tokens[idx] == '^':
        tie = True
        idx += 1

    base_st = ST_PER_MEASURE / length
    mult = 1.0
    for i in range(dot_count):
        mult += 1 / (2 ** (i + 1))

    st = base_st * mult
    return st, idx, tie, length

def parse_mml_channel(lines, ch):
    """1チャンネル分のMMLを解析してイベントを返す"""
    events = []
    oct = 4
    last_length = 4
    pos_st = 0

    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue
        if "//" in line:
            line = line.split("//")[0]
        cleaned.append(line)

    text = "".join(cleaned)
    tokens = re.findall(r'[<>]|O[0-9]+|[a-g][+]?|r|[0-9]+|\.|\^|&', text)

    i = 0
    while i < len(tokens):
        t = tokens[i]

        if t.startswith("O"):
            oct = int(t[1:])
            i += 1
            continue

        if t == '>':
            oct += 1
            i += 1
            continue

        if t == '<':
            oct -= 1
            i += 1
            continue

        if t == 'r':
            st, i2, tie, last_length = parse_length(tokens, i + 1, last_length)
            pos_st += st
            i = i2
            continue

        if t in NOTE_TABLE:
            note_base = NOTE_TABLE[t]

            # ドラムチャンネルなら専用ノート
            if 7 <= ch <= 13:
                midi_note = DRUM_MAP[ch]
            else:
                midi_note = 12 * oct + note_base

            st, i2, tie, last_length = parse_length(tokens, i + 1, last_length)
            total_st = st

            # タイ（^）処理
            while tie:
                st2, i3, tie2, last_length = parse_length(tokens, i2, last_length)
                total_st += st2
                i2 = i3
                tie = tie2

            # & 処理（同音ならまとめる）
            while i2 < len(tokens) and tokens[i2] == '&':
                i2 += 1
                if i2 < len(tokens) and tokens[i2] in NOTE_TABLE:
                    next_note_base = NOTE_TABLE[tokens[i2]]
                    next_midi_note = (DRUM_MAP[ch] if 7 <= ch <= 13 else 12 * oct + next_note_base)
                    if next_midi_note == midi_note:
                        st2, i3, tie2, last_length = parse_length(tokens, i2 + 1, last_length)
                        total_st += st2
                        i2 = i3
                        while tie2:
                            st3, i4, tie3, last_length = parse_length(tokens, i2, last_length)
                            total_st += st3
                            i2 = i4
                            tie2 = tie3
                    else:
                        break
                else:
                    break

            events.append(("note", midi_note, pos_st, total_st))
            pos_st += total_st
            i = i2
            continue

        i += 1

    return events

def mml_to_midi(mml_filename, midi_filename):
    """MMLファイルを読み込み、MIDIファイルを生成"""
    try:
        with open(mml_filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(mml_filename, "r", encoding="shift_jis") as f:
            lines = f.readlines()

    tempo_bpm = 120
    tempo_matches = re.findall(r'T([0-9]+)', "".join(lines))
    if tempo_matches:
        tempo_bpm = int(tempo_matches[-1])
    tempo_us = int(60000000 / tempo_bpm)

    channels = {}
    current_ch = None
    for line in lines:
        if line.startswith("[Channel"):
            current_ch = int(re.findall(r'\d+', line)[0])
            channels[current_ch] = []
        else:
            if current_ch is not None:
                channels[current_ch].append(line)

    mid = MidiFile(type=1)
    mid.ticks_per_beat = PPQN

    tempo_track = MidiTrack()
    tempo_track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))
    mid.tracks.append(tempo_track)

    for ch in range(1, 14):
        if ch not in channels:
            continue

        track = MidiTrack()
        mid.tracks.append(track)

        if 1 <= ch <= 6:
            midi_ch = ch - 1
        else:
            midi_ch = 9  # ドラムは常に ch10

        events = parse_mml_channel(channels[ch], ch)
        events.sort(key=lambda e: e[2])

        last_tick = 0
        for ev in events:
            kind, note, start_st, length_st = ev
            start_tick = st_to_ticks(start_st)
            length_tick = st_to_ticks(length_st)
            delta = start_tick - last_tick

            track.append(Message('note_on', note=note, velocity=100, time=delta, channel=midi_ch))
            track.append(Message('note_off', note=note, velocity=0, time=length_tick, channel=midi_ch))

            last_tick = start_tick + length_tick

    mid.save(midi_filename)
    print(f"MIDI saved: {midi_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python mml2mid.py input.mml output.mid")
        sys.exit(0)

    mml_to_midi(sys.argv[1], sys.argv[2])
