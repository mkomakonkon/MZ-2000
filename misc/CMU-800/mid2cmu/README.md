# MIDIデータをMZ-2000+CMU-800のデータに変換する(β版)
改版履歴<br>
V0.5:小節またぎの音符が途切れていたので途切れないよう修正<br>
V0.4:小節またぎを正確に実行、変換誤差が出ないよう事前にMIDIデータをクオンタイズ<br>
V0.3:スタートアドレスを12A0にして、CMUプレーヤーでのLOAD改善、どの分解能でも変換可能（分解能960と48のみ動作確認済）<br>
V0.2:V0.1で分かっている不具合修正。mztのヘッダミス修正（CMU-800 playerはV0.2以降LOAD可）<br>
V0.1:単純なデータ変換のみ<br>
[![](https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/mid2cmu/figure/CMU.png)](https://x.com/mkomapfu/status/2057637990839804357?s=20)
# MZ-2000 変換スクリプト用 Python セットアップ手順

この手順に従えば、MIDIデータを MZ-2000 + CMU-800用の  
output.mzt に変換する Python スクリプトを実行できます。

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
このツールはMIDI CH1～8をCMU-800のCH1～8に変換します。<br>
和音には対応していませんので、各CHのデータは単音にして下さい。<br>
**【重要】和音を変換しようとしてもまともなデータにはなりません。**<br>
リズムも未対応です。<br>

1. 対応様式は次の通り
   - Format 1
   - 分解能は任意（960と48は動作確認済）
   - トラックにマージして出力
<br>以下は私が愛用しているMusic Studio Standardシリーズの出力画面です。
<br><img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/mid2cmu/figure/MIDI_format.png" width="500"><br>
---

## 3. スクリプトとMIDIファイルを配置する

1. 任意のフォルダを作成（例：`mid2cmu`）
2. 以下のファイルを置く：
   - Python スクリプト（`mid2cmu.py`）
   - 2.で作成した入力データ（`input.mid`）

---

## 4. スクリプトを実行する

コマンド プロンプト（または PowerShell）でフォルダに移動：
```
cd フォルダのパス
```
実行例：
```
python mid2cmu_v0.5.py input.mid output.mzt
```
---
