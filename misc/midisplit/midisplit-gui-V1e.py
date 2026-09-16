#V1c ラウンドロビンで分割成功。元のデータは残していない
#V1d 元のデータも残す
#V1e NOTE ONが全てなくなったら分割CHをリセット
from mido import MidiFile, MidiTrack
from collections import deque

INPUT_FILE = "input.mid"
OUTPUT_FILE = "output.mid"

# 分割元CH
SOURCE_CH = 7

# 出力CH
DEST_CHS = [1, 3, 4, 5, 6, 2]


mid = MidiFile(INPUT_FILE)

# 出力MIDI
out_mid = MidiFile()
for tr in mid.tracks:

    new_track = MidiTrack()

    for msg in tr:
        new_track.append(msg.copy())

    out_mid.tracks.append(new_track)
out_mid.ticks_per_beat = mid.ticks_per_beat

# CHごとのイベント蓄積
# {ch: [(abs_time, msg), ...]}
track_events = {
    ch: []
    for ch in DEST_CHS
}

# 空きCH管理
free_channels = deque(DEST_CHS)

# note -> 利用CH
active_notes = {}

for track in mid.tracks:

    abs_time = 0

    for msg in track:

        abs_time += msg.time

        if not hasattr(msg, "channel"):
            continue

        if msg.channel != (SOURCE_CH - 1):
            continue

        #
        # Note ON
        #
        if msg.type == "note_on" and msg.velocity > 0:

            if free_channels:
                ch = free_channels.popleft()
            else:
                # CH不足時は最後のCHへ
                ch = DEST_CHS[-1]

            active_notes.setdefault(msg.note, [])
            active_notes[msg.note].append(ch)

            new_msg = msg.copy(
                channel=ch - 1,
                time=0
            )

            track_events[ch].append(
                (abs_time, new_msg)
            )

        #
        # Note OFF
        #
        elif (
            msg.type == "note_off"
            or (
                msg.type == "note_on"
                and msg.velocity == 0
            )
        ):

            if (
                msg.note in active_notes
                and active_notes[msg.note]
            ):

                ch = active_notes[msg.note].pop(0)

                free_channels.append(ch)
                
                # 空になったらキー削除
                if not active_notes[msg.note]:
                    del active_notes[msg.note]
                    
                # 全音停止
                if len(active_notes) == 0:
                
                    free_channels = deque(DEST_CHS)

                new_msg = msg.copy(
                    channel=ch - 1,
                    time=0
                )

                track_events[ch].append(
                    (abs_time, new_msg)
                )

#
# CH別トラック生成
#
for ch in DEST_CHS:

    track = MidiTrack()

    events = sorted(
        track_events[ch],
        key=lambda x: x[0]
    )

    last_time = 0

    for abs_time, msg in events:

        delta = abs_time - last_time

        track.append(
            msg.copy(time=delta)
        )

        last_time = abs_time

    out_mid.tracks.append(track)

out_mid.save(OUTPUT_FILE)

print("変換完了")