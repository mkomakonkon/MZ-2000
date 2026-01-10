# カラーBMPをMZ-2000で表示する
<img src="https://pbs.twimg.com/media/G-RX9YiasAE41ap?format=jpg&name=large" width="300"><br>

# MZ-2000 画像変換スクリプト用 Python セットアップ手順

この手順に従えば、BMP 画像を SHARP MZ-2000 用の  
GRAM1/2/3.mzt に変換する Python スクリプトを実行できます。

---
## 1. Python をインストールする
### Windows
1. 公式サイトから Python をダウンロード  
   https://www.python.org/downloads/
2. インストーラを起動
3. **「Add Python to PATH」 にチェックを入れる（重要）**
4. 「Install Now」を選択

### macOS
Homebrew がある場合：
```
brew install python
```
---

## 2. 必要なライブラリをインストールする

このスクリプトで必要なのは **Pillow（画像処理ライブラリ）** だけです。
```
pip install pillow
```
pip が使えない場合：
```
python -m pip install pillow
```
---

## 3. スクリプトと画像を配置する

1. 任意のフォルダを作成（例：`mz2000_converter`）
2. 以下のファイルを置く：
   - Python スクリプト（`bmp2bin.py`）
   - 入力画像（`input.bmp`）

---

## 4. スクリプトを実行する

ターミナル（または PowerShell）でフォルダに移動：
```
cd フォルダのパス
```
実行：
```
python bmp2bin.py
```
---

## 5. ディザ方式を選択する

実行すると次のような選択肢が表示されます：
```
A = Floyd–Steinberg  
B = Bayer  
C = Atkinson
```
A / B / C のいずれかを入力してください。

---

## 6. 出力ファイルを確認する
同じフォルダに以下の 3 つが生成されます：

- `GRAM1.mzt`（青プレーン）
- `GRAM2.mzt`（赤プレーン）
- `GRAM3.mzt`（緑プレーン）

これらを MZ-2000 エミュレータに読み込むことで画像が表示されます。  
”GRAMDISP.mzt”で表示ができます。  　　

---

## トラブルシューティング

### pip が動かない
python -m pip install pillow
### Python が見つからない
PATH が通っていないため、再インストール時に  
**「Add Python to PATH」** を有効にしてください。

### input.bmp が読み込めない
スクリプトと同じフォルダに置いてください。

---

## 補足
bmp2bin.pyを生成するためのCopilot への指示文
```
Python で、BMP 画像を SHARP MZ-2000 用の 8色 GRAM1/2/3.mzt に変換するスクリプトを作ってください。

要件は以下の通りです：

● 入力：input.bmp（RGB）
● 出力：GRAM1.mzt（B）、GRAM2.mzt（R）、GRAM3.mzt（G）
● 画像サイズ：640×200 にリサイズ（NEAREST）
● パレット：MZ-2000 の 8色（0/255 の RGB）
● ガンマ補正（0.8）
● UnsharpMask（radius=1, percent=160, threshold=3）

● ディザ方式は 3種類すべて実装すること：
    A = Floyd–Steinberg
    B = Bayer（4×4）
    C = Atkinson

● 実行後にユーザーへ A/B/C を選ばせるプロンプトを表示し、
   入力された方式でディザリングを行うこと。

● GRAM1/2/3 は 8ピクセル単位でビットパックし、
   LSB が左端ピクセルになるようにすること。

● .mzt のヘッダとフッタは HEX 文字列から bytes に変換して付与すること。

● コードは 1ファイルにまとめ、main() で完結する構成にすること。

以上の仕様を満たす完全な Python スクリプトを生成してください。
```
🌈 この指示文のポイント<br>
•	8色パレット<br>
•	ガンマ補正<br>
•	シャープ処理<br>
•	640×200<br>
•	3種類のディザ関数<br>
•	実行後に A/B/C を選択<br>
•	GRAM1/2/3 のビットパック<br>
•	.mzt のヘッダ＋フッタ<br>
•	main() で完結<br>




