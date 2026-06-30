# MIDIデータをMZ-2000のC3MSデータに変換する
C3MS:Carry lab. 3voices Music System for MZ
改版履歴<br>
V0.2:とりあえず演奏データが作れるようになったのでβ版の公開<br>
<br>
－－－－デモ－－－－－－－－－－－－－－－－－－－－－<br>
[![](https://img.youtube.com/vi/JKbdIh8v7U8/0.jpg)](https://www.youtube.com/watch?v=JKbdIh8v7U8)
# MZ-2000 変換スクリプト用 Python セットアップ手順

この手順に従えば、MIDIデータを MZ-2000のC3MSデータに変換する  
Python スクリプトを実行できます。

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
## 2. MIDIファイルを用意する。
このツールはMIDI CH1～3を三重和音に変換します。<br>
和音のMIDIデータには対応していませんので、各CHのデータは単音にして下さい。<br>
**【重要】和音を変換しようとしてもまともなデータにはなりません。**<br>

1. 対応様式は次の通り
   - Format 1
   - 分解能は任意（960と48は動作確認済）
   - トラックにマージして出力
<br>以下は私が愛用しているMusic Studio Standardシリーズの出力画面です。
<br><img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/mid2cmu/figure/MIDI_format.png" width="500"><br>
---

## 3. スクリプトとMIDIファイルを配置する

1. 任意のフォルダを作成（例：`mid2c3ms`）
2. 以下のファイルを置く：
   - Python スクリプト（`mid2cmu.py`）
   - 2.で作成した入力データ（例`Lady-Madonna.mid`）

---

## 4. スクリプトを実行する

コマンド プロンプト（または PowerShell）でフォルダに移動：
```
cd フォルダのパス
```
実行例：
```
python http://mid2c3ms_v0.2.py Lady-Madonna.mid Lady-Madonna.mzt
```
---
