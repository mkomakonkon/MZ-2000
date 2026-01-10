from PIL import Image, ImageFilter
import math

INPUT_FILE = "input.bmp"

# 出力ファイル（拡張子 .mzt）
OUT_B = "GRAM1.mzt"   # GRAM1 = B
OUT_R = "GRAM2.mzt"   # GRAM2 = R
OUT_G = "GRAM3.mzt"   # GRAM3 = G

WIDTH = 640
HEIGHT = 200

# --- ヘッダ（HEX → バイト列） ---
HEADER_B_HEX = "014752414D310D0D0D0D0D0D0D0D0D0D"  # GRAM1.mzt（Bプレーン）
HEADER_R_HEX = "014752414D320D0D0D0D0D0D0D0D0D0D"  # GRAM2.mzt（Rプレーン）
HEADER_G_HEX = "014752414D330D0D0D0D0D0D0D0D0D0D"  # GRAM3.mzt（Gプレーン）

HEADER_B = bytes.fromhex(HEADER_B_HEX)
HEADER_R = bytes.fromhex(HEADER_R_HEX)
HEADER_G = bytes.fromhex(HEADER_G_HEX)

HEADER_HEX = (
    "0D0D1A3F0080B100FFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
)

# --- フッタ（HEX → バイト列） ---
FOOTER_HEX = (
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "DBE8CBFFCBB7D3E82100801100C0017F"
    "3EEDB0DBE8CBF7D3E8C9"
)

HEADER = bytes.fromhex(HEADER_HEX)
FOOTER = bytes.fromhex(FOOTER_HEX)

# --- MZ-2000 の 8色パレット（0 or 255 の RGB） ---
PALETTE = [
    (0,   0,   0  ),  # 0: 黒
    (0,   0,   255),  # 1: 青
    (255, 0,   0  ),  # 2: 赤
    (255, 0,   255),  # 3: マゼンタ
    (0,   255, 0  ),  # 4: 緑
    (0,   255, 255),  # 5: シアン
    (255, 255, 0  ),  # 6: 黄
    (255, 255, 255)   # 7: 白
]


# --- ガンマ補正（線を生かす用） ---
def apply_gamma(img, gamma):
    inv = 1.0 / gamma
    return Image.eval(img, lambda v: int((v / 255.0) ** inv * 255.0))


# --- 最も近いパレット色を探す（ユークリッド距離） ---
def nearest_palette_color(r, g, b):
    best = None
    best_dist = 1e9
    for pr, pg, pb in PALETTE:
        dr = r - pr
        dg = g - pg
        db = b - pb
        dist = dr * dr + dg * dg + db * db
        if dist < best_dist:
            best_dist = dist
            best = (pr, pg, pb)
    return best


# --- Floyd–Steinberg 誤差拡散 8色ディザリング ---
def floyd_steinberg_dither(img):
    """
    img: 640x200, RGB, 0-255
    戻り値: 8色に量子化済みの Image (RGB)
    """
    w, h = img.size
    # 誤差を蓄積できるように float で持つ
    pixels = img.load()

    # 2次元配列に展開（誤差計算用）
    buf = [[[float(pixels[x, y][0]),
             float(pixels[x, y][1]),
             float(pixels[x, y][2])]
            for x in range(w)]
           for y in range(h)]

    for y in range(h):
        for x in range(w):
            old_r, old_g, old_b = buf[y][x]
            nr, ng, nb = nearest_palette_color(old_r, old_g, old_b)

            # 出力ピクセルはパレット色に置き換え
            buf[y][x] = [nr, ng, nb]

            # 誤差計算
            er = old_r - nr
            eg = old_g - ng
            eb = old_b - nb

            # 誤差拡散 (Floyd–Steinberg)
            # (x+1, y    ) += error * 7/16
            if x + 1 < w:
                br, bg, bb = buf[y][x + 1]
                buf[y][x + 1] = [
                    br + er * 7.0 / 16.0,
                    bg + eg * 7.0 / 16.0,
                    bb + eb * 7.0 / 16.0,
                ]

            # (x-1, y+1  ) += error * 3/16
            if x - 1 >= 0 and y + 1 < h:
                br, bg, bb = buf[y + 1][x - 1]
                buf[y + 1][x - 1] = [
                    br + er * 3.0 / 16.0,
                    bg + eg * 3.0 / 16.0,
                    bb + eb * 3.0 / 16.0,
                ]

            # (x,   y+1  ) += error * 5/16
            if y + 1 < h:
                br, bg, bb = buf[y + 1][x]
                buf[y + 1][x] = [
                    br + er * 5.0 / 16.0,
                    bg + eg * 5.0 / 16.0,
                    bb + eb * 5.0 / 16.0,
                ]

            # (x+1, y+1  ) += error * 1/16
            if x + 1 < w and y + 1 < h:
                br, bg, bb = buf[y + 1][x + 1]
                buf[y + 1][x + 1] = [
                    br + er * 1.0 / 16.0,
                    bg + eg * 1.0 / 16.0,
                    bb + eb * 1.0 / 16.0,
                ]

    # バッファを書き戻して Image にする
    out = Image.new("RGB", (w, h))
    out_pixels = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = buf[y][x]
            # 範囲クリップ
            r = int(max(0, min(255, round(r))))
            g = int(max(0, min(255, round(g))))
            b = int(max(0, min(255, round(b))))
            out_pixels[x, y] = (r, g, b)

    return out

# --- Bayer（4×4）ディザリング ---
def bayer_dither(img):
    """
    img: 640x200, RGB, 0-255
    戻り値: 8色に量子化済みの Image (RGB)
    """

    # 4x4 Bayer マトリクス（0〜15）
    B4 = [
        [0,  8,  2, 10],
        [12, 4, 14, 6],
        [3, 11, 1,  9],
        [15, 7, 13, 5]
    ]

    w, h = img.size
    pixels = img.load()

    out = Image.new("RGB", (w, h))
    out_pixels = out.load()

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]

            # 0〜1 に正規化
            nr = r / 255.0
            ng = g / 255.0
            nb = b / 255.0

            # Bayer のしきい値（0〜1）
            threshold = (B4[y % 4][x % 4] + 0.5) / 16.0

            # R/G/B それぞれを Bayer で 0/1 に丸める
            rbit = 1 if nr > threshold else 0
            gbit = 1 if ng > threshold else 0
            bbit = 1 if nb > threshold else 0

            # 8色パレットの RGB に変換
            pr = 255 if rbit else 0
            pg = 255 if gbit else 0
            pb = 255 if bbit else 0

            out_pixels[x, y] = (pr, pg, pb)

    return out


# --- Atkinson ディザリング関数 ---
def atkinson_dither(img):
    """
    img: 640x200, RGB, 0-255
    戻り値: 8色に量子化済みの Image (RGB)
    """

    w, h = img.size
    pixels = img.load()

    # 誤差を蓄積できるように float バッファに展開
    buf = [[[float(pixels[x, y][0]),
             float(pixels[x, y][1]),
             float(pixels[x, y][2])]
            for x in range(w)]
           for y in range(h)]

    for y in range(h):
        for x in range(w):
            old_r, old_g, old_b = buf[y][x]

            # 最も近い 8色パレット色
            nr, ng, nb = nearest_palette_color(old_r, old_g, old_b)

            # 出力ピクセルをパレット色に置き換え
            buf[y][x] = [nr, ng, nb]

            # 誤差
            er = old_r - nr
            eg = old_g - ng
            eb = old_b - nb

            # Atkinson の誤差拡散（1/8 を周囲に配る）
            def spread(dx, dy, factor=1/8):
                xx = x + dx
                yy = y + dy
                if 0 <= xx < w and 0 <= yy < h:
                    br, bg, bb = buf[yy][xx]
                    buf[yy][xx] = [
                        br + er * factor,
                        bg + eg * factor,
                        bb + eb * factor,
                    ]

            # 拡散パターン
            spread(1, 0)
            spread(2, 0)
            spread(-1, 1)
            spread(0, 1)
            spread(1, 1)
            spread(0, 2)

    # Image に戻す
    out = Image.new("RGB", (w, h))
    out_pixels = out.load()

    for y in range(h):
        for x in range(w):
            r, g, b = buf[y][x]
            r = int(max(0, min(255, round(r))))
            g = int(max(0, min(255, round(g))))
            b = int(max(0, min(255, round(b))))
            out_pixels[x, y] = (r, g, b)

    return out


# --- LSB が左端になるように 8bit パック ---
def pack_bits_reverse(bits):
    """
    bits: 長さ8の 0/1 配列
    LSB が左端ピクセルになるように配置
    """
    b = 0
    for i, bit in enumerate(bits):
        b |= (bit & 1) << i
    return b


def main():
    # --- 実行後にディザ方式を選択 ---
    print("ディザ方式を選んでください：")
    print("  A = Floyd–Steinberg（- 線が細いアニメ向き）")
    print("  B = Bayer（レトロ感、参考用）")
    print("  C = Atkinson（塗りが多いアニメ向き）")

    mode = input("モードを入力してください (A/B/C): ").strip().upper()
    if mode not in ("A", "B", "C"):
        print("無効な入力です。C（Atkinson）を使用します。")
        mode = "C"

    # 入力画像読み込み
    img = Image.open(INPUT_FILE).convert("RGB")

    # ガンマ補正（線と暗部を強調）
    img = apply_gamma(img, 0.8)

    # シャープ処理（線を太らせる）
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=160, threshold=3))

    # 640x200 にリサイズ
    img = img.resize((WIDTH, HEIGHT), Image.NEAREST)

    # --- ディザ方式切り替え ---
    if mode == "A":
        dimg = floyd_steinberg_dither(img)
    elif mode == "B":
        dimg = bayer_dither(img)
    else:  # "C"
        dimg = atkinson_dither(img)


    # GRAM プレーンバッファ
    plane_b = bytearray()
    plane_r = bytearray()
    plane_g = bytearray()

    pixels = dimg.load()

    for y in range(HEIGHT):
        for x_byte in range(0, WIDTH, 8):
            bits_b = []
            bits_r = []
            bits_g = []

            for x in range(x_byte, x_byte + 8):
                r, g, b = pixels[x, y]

                # 8色パレットは 0 or 255 なので単純に 128 で判定
                rbit = 1 if r >= 128 else 0
                gbit = 1 if g >= 128 else 0
                bbit = 1 if b >= 128 else 0

                bits_b.append(bbit)
                bits_r.append(rbit)
                bits_g.append(gbit)

            plane_b.append(pack_bits_reverse(bits_b))
            plane_r.append(pack_bits_reverse(bits_r))
            plane_g.append(pack_bits_reverse(bits_g))

    # --- ヘッダ＋本体＋フッタを連結して .mzt に出力 ---
    with open(OUT_B, "wb") as f:
        f.write(HEADER_B + HEADER + plane_b + FOOTER)

    with open(OUT_R, "wb") as f:
        f.write(HEADER_R + HEADER + plane_r + FOOTER)

    with open(OUT_G, "wb") as f:
        f.write(HEADER_G + HEADER + plane_g + FOOTER)

    print("出力完了：生成した GRAM1/2/3データ を .mzt で保存しました")


if __name__ == "__main__":
    main()