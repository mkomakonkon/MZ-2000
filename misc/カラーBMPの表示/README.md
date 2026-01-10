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
brew install python

---

## 2. 必要なライブラリをインストールする

このスクリプトで必要なのは **Pillow（画像処理ライブラリ）** だけです。
pip install pillow
pip が使えない場合：
python -m pip install pillow

---

## 3. スクリプトと画像を配置する

1. 任意のフォルダを作成（例：`mz2000_converter`）
2. 以下のファイルを置く：
   - Python スクリプト（例：`convert.py`）
   - 入力画像（`input.bmp`）

---

## 4. スクリプトを実行する

ターミナル（または PowerShell）でフォルダに移動：
cd フォルダのパス
実行：
python convert.py
---

## 5. ディザ方式を選択する

実行すると次のような選択肢が表示されます：
A = Floyd–Steinberg B = Bayer C = Atkinson
A / B / C のいずれかを入力してください。

---

## 6. 出力ファイルを確認する
同じフォルダに以下の 3 つが生成されます：

- `GRAM1.mzt`（青プレーン）
- `GRAM2.mzt`（赤プレーン）
- `GRAM3.mzt`（緑プレーン）

これらを MZ-2000 エミュレータに読み込むことで画像が表示されます。

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

このセットアップ手順は、  
MZ-2000 用 8色ディザリング変換スクリプトに最適化されています。


