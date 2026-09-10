#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cmuadd.py

使い方:
    python cmuadd.py メロディー.mzt リズム.mzt

出力:
    元ファイル名=ALL.mzt

構成:
    CH0  <- リズム CH0 (パターンデータ)
    CH1  <- メロディ CH1
    CH2  <- メロディ CH2
    CH3  <- メロディ CH3
    CH4  <- メロディ CH4
    CH5  <- メロディ CH5
    CH6  <- メロディ CH6
    CH7  <- メロディ CH7 (無ければ空)
    CH8  <- メロディ CH8 (無ければ空)
    CH9  <- リズム CH9 (テーブルデータ)
"""

import sys
from pathlib import Path

HEADER_SIZE = 0x80
ENDMARK = b"\xFE\x0C\x06"


def split_channels(data):
    """
    FE 0C 06 を終端としてチャンネル分割。
    終端コード自身は含まない。
    """

    channels = []

    pos = 0

    while True:
        idx = data.find(ENDMARK, pos)

        if idx < 0:
            break

        channels.append(data[pos:idx])
        pos = idx + len(ENDMARK)

    return channels


def get_channel(channels, index):
    """
    指定チャンネル取得。
    存在しなければ空データを返す。
    """

    if 0 <= index < len(channels):
        return channels[index]

    return b""


def create_header(melody_header, body_size):
    """
    指定仕様でヘッダ生成
    """

    header = bytearray(128)

    # 00h～11h
    header[0:0x12] = melody_header[0:0x12]

    # 12h～13h
    # ファイルサイズ(ヘッダ除く)
    # 下位→上位
    header[0x12] = body_size & 0xFF
    header[0x13] = (body_size >> 8) & 0xFF

    # 14h～17h
    header[0x14:0x18] = bytes.fromhex("7D33A012")

    # 18h～7Fh
    # すべて00
    for i in range(0x18, 0x80):
        header[i] = 0x00

    return bytes(header)


def main():

    if len(sys.argv) != 3:
        print("使い方:")
        print("  python cmuadd.py メロディー.mzt リズム.mzt")
        return

    melody_file = Path(sys.argv[1])
    rhythm_file = Path(sys.argv[2])

    melody = melody_file.read_bytes()
    rhythm = rhythm_file.read_bytes()

    melody_header = melody[:HEADER_SIZE]

    melody_channels = split_channels(melody[HEADER_SIZE:])
    rhythm_channels = split_channels(rhythm[HEADER_SIZE:])

    if len(rhythm_channels) < 10:
        print(
            f"エラー: リズムMZTのチャンネル数不足 ({len(rhythm_channels)})"
        )
        return

    out_body = bytearray()

    #
    # CH0
    #
    out_body.extend(get_channel(rhythm_channels, 0))
    out_body.extend(ENDMARK)

    #
    # CH1～CH8
    #
    for ch in range(1, 9):
        out_body.extend(get_channel(melody_channels, ch))
        out_body.extend(ENDMARK)

    #
    # CH9
    #
    out_body.extend(get_channel(rhythm_channels, 9))
    out_body.extend(ENDMARK)

    # ヘッダ作成
    header = create_header(melody_header, len(out_body))

    # 出力ファイル名
    out_file = melody_file.with_name(
        melody_file.stem + "=ALL.mzt"
    )

    out_file.write_bytes(header + out_body)

    print(f"作成完了: {out_file}")


if __name__ == "__main__":
    main()