# ============================================================
# MZT CMU-800 Analyzer
# ============================================================

import sys

MEASURE_EVENT = bytes([0xFD, 0x0C, 0x06])
END_EVENT = bytes([0xFE, 0x0C, 0x06])

HEADER_SIZE = 128


def read_channel_events(data, pos):
    """
    CH1つ分のイベントを読み取る
    戻り値: (events, next_pos)
    events = [("note", cv, st, gate), ("measure",), ...]
    """

    events = []
    i = pos

    while i < len(data):
        chunk = data[i:i+3]

        # END_EVENT
        if chunk == END_EVENT:
            return events, i + 3

        # MEASURE_EVENT
        if chunk == MEASURE_EVENT:
            events.append(("measure",))
            i += 3
            continue

        # 通常イベント (CV, ST, GT)
        if len(chunk) < 3:
            break

        cv, st, gate = chunk
        events.append(("note", cv, st, gate))
        i += 3

    return events, i


def analyze_mzt(filename):
    with open(filename, "rb") as f:
        data = f.read()

    # ヘッダをスキップ
    pos = HEADER_SIZE

    # CH0〜CH9 を順番に読む
    channels = {}

    for ch in range(10):
        events, pos = read_channel_events(data, pos)
        channels[ch] = events

    # ============================================================
    # CH1〜CH8 の TOTAL ST を集計
    # ============================================================

    # all_st.txt
    with open("all_st.txt", "w", encoding="utf-8") as f_all:

        for ch in range(1, 9):
            events = channels[ch]

            measure_st = []
            current_st = 0

            for ev in events:
                if ev[0] == "note":
                    _, cv, st, gate = ev
                    current_st += st

                elif ev[0] == "measure":
                    measure_st.append(current_st)
                    current_st = 0

            # 最終小節が measure_event で終わらない場合
            if current_st > 0:
                measure_st.append(current_st)

            total_sum = sum(measure_st)
            f_all.write(f"CH{ch}:ALL TOTAL ST={total_sum}\n")

    # ============================================================
    # total_st.txt
    # ============================================================

    with open("total_st.txt", "w", encoding="utf-8") as f_detail:

        for ch in range(1, 9):
            events = channels[ch]

            measure_st = []
            current_st = 0

            for ev in events:
                if ev[0] == "note":
                    _, cv, st, gate = ev
                    current_st += st

                elif ev[0] == "measure":
                    measure_st.append(current_st)
                    current_st = 0

            if current_st > 0:
                measure_st.append(current_st)

            f_detail.write(f"【CH{ch}】\n")

            for i, st in enumerate(measure_st):
                mark = "★" if st != 96 else ""
                f_detail.write(f"MEAS{i+1} TOTAL ST={st}{mark}\n")

            f_detail.write("\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("python mzt_analyzer.py input.mzt")
        sys.exit(0)

    analyze_mzt(sys.argv[1])
