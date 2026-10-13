# CMU-PLAYER-CG-MAKER
CMU-800 PLAYER Ver.1.0CGの作成ツールです。<br>

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
## 2. bmpファイルを用意する。
取り込みたいBMPファイルをツールと同じフォルダに格納してください。
---

## 3. スクリプトを実行する

コマンド プロンプト（または PowerShell）でフォルダに移動：
```
cd フォルダのパス
```
実行例：
```
Usage:
  python mid2cmu.py input.mid output.mzt（1セット構成でよい場合）
  python mid2cmu.py input.mid output1.mzt output2.mzt（2セット構成を出力する場合）
TEMPO可変機能を使う場合はデフォルトBPMを入力してください。(使わない場合はEnter): 
```
<img width="834" height="371" alt="image" src="https://github.com/user-attachments/assets/054c8206-31d1-4d67-a28f-ff2b26f06df2" />

---
