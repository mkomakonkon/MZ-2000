import os

# 1. 固定ファイル名の変数定義
BASE_MZT_FILENAME = "input-template.bin"
OUTPUT_MZT_FILENAME = "CMU-800PLAYER-V1.0CG.mzt"

def modify_mzt_fixed_output():
    print("=== CMU-800PLAYER CG作成ツール ===")
    
    input_bmp = input("表示したいBMP画像のファイル名を入力してください: ").strip()
    if not os.path.exists(input_bmp):
        print(f"[エラー] BMPファイル '{input_bmp}' が見つかりません。")
        return

    if not os.path.exists(BASE_MZT_FILENAME):
        print(f"[エラー] 元となるMZTファイル '{BASE_MZT_FILENAME}' が見つかりません。")
        return

    try:
        from PIL import Image
    except ImportError:
        print("[エラー] Pillowライブラリがインストールされていません。'pip install Pillow' を実行してください。")
        return

    # 2. 元MZTファイルのバイナリをそのまま読み込む
    with open(BASE_MZT_FILENAME, "rb") as f:
        mzt_content = bytearray(f.read())

    # 指定されたファイル内格納オフセット
    gram1_file_offset = 0x0DE0
    gram2_file_offset = 0x4DE0
    gram3_file_offset = 0x8DE0
    plane_size = 16384 # 16KB

    # BMP画像の読み込みと640x200変換
    img = Image.open(input_bmp).convert('RGB')
    if img.size != (640, 200):
        img = img.resize((640, 200), Image.Resampling.LANCZOS)

    width, height = img.size # 640 x 200

    # 各プレーン用のバッファ（初期値 00H、不足分は自動で00Hパディング）
    gram1_data = bytearray(plane_size)
    gram2_data = bytearray(plane_size)
    gram3_data = bytearray(plane_size)

    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            
            # 2x2 千鳥マトリクス
            dither_matrix = [
                [ 64, 192 ],
                [ 192, 64 ]
            ]
            dither = dither_matrix[y % 2][x % 2]
            
            b_bit = 1 if b > (255 - dither) else 0
            r_bit = 1 if r > (255 - dither) else 0
            g_bit = 1 if g > (255 - dither) else 0
            
            byte_idx = y * 80 + (x // 8)
            if byte_idx < plane_size:
                # ビット重み（LSB基準）
                bit_idx = x % 8
                
                if b_bit:
                    gram1_data[byte_idx] |= (1 << bit_idx)
                if r_bit:
                    gram2_data[byte_idx] |= (1 << bit_idx)
                if g_bit:
                    gram3_data[byte_idx] |= (1 << bit_idx)

    # 必要な最大ファイルサイズを確保
    required_max_offset = gram3_file_offset + plane_size
    if len(mzt_content) < required_max_offset:
        mzt_content.extend(bytearray(required_max_offset - len(mzt_content)))

    # 【重要】0x0DE0より前のデータは一切書き換えず、指定されたCG格納位置のみを更新
    mzt_content[gram1_file_offset : gram1_file_offset + plane_size] = gram1_data
    mzt_content[gram2_file_offset : gram2_file_offset + plane_size] = gram2_data
    mzt_content[gram3_file_offset : gram3_file_offset + plane_size] = gram3_data

    # 新しいMZTファイルの書き出し（固定ファイル名）
    with open(OUTPUT_MZT_FILENAME, "wb") as f:
        f.write(mzt_content)

    print(f"[完了] MZTファイル '{OUTPUT_MZT_FILENAME}' を作成しました！")

if __name__ == "__main__":
    modify_mzt_fixed_output()