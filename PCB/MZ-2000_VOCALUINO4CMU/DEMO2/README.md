# MZ-2000+CMU-800をEXINTを使って演奏させる

Arduinoのテンポクロックを **EXINT割り込み**に入れると、BASICのループの重さに関係なく、一定のテンポで演奏できます。

---

## 1. ファイル一覧

| ファイル | 役割 |
|---|---|
| `TIME LIMIT3I.mzt` | BASICプログラム |
| `TIME LIMIT3I OBJ.mzt` | マシン語プログラム(モニタからLコマンドでロード) |
| `A1_CLOCK_UNIT_VOICE_EXINT2.ino` | Arduinoのスケッチ（テンポクロック、EXINT） |
| `bgm_cmu800_v2int.asm` | 演奏ルーチン（**参考情報**）。AILZ80ASMでアセンブルする |
