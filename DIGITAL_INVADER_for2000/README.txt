I/O 1982年6月号に掲載された
DIGITAL INVADERをMZ-2000用に移植したものです。
著作権は工藤一郎様にあります。

－－デモ動画－－－－－－－－－－－－－－－－－－－  
[![MZ-80K/CのDIGITAL INVADERをMZ-2000に移植してみました](https://img.youtube.com/vi/xXplv1aI-i4/0.jpg)](https://www.youtube.com/watch?v=xXplv1aI-i4)  

－－ファイルの説明－－－－－－－－－－－－－－－－
■DIGITAL_INVADER_for2000.wav
テープイメージ（MZ-1Z001で動作確認済）
モニターからロードするとゲームが始まります
START ADR:BD00
END ADR  :CFFF
JUMP ADR :BE00

■DIGITAL_INVADE.dis：ディスアセンブルしたソースとメモ

■フローチャート.xlsx：移植時に作ったメモ用ファイル

－－今分かっているバグと仕様－－－－－－－－－－－－
1.ゼロサプレス(無駄な0非表示)がうまく動かない
（前回修正で一時直ったがどこを直したか忘れた）

2.時間をコンペアしているので効果音を流すと
コンペア時間を通り過ぎて、長い待ち時間が発生することがある
（数字が出てこなくなったら少し待ってみてください。）

3.効果音がただのBEEP。↑の件もあり、効果音後はタイマーを
リセットする仕様変更が必要そう。

・GO NEXTの画面が出ない（仕様？）

・PUSH [S] KEYが流れる画面が早すぎのため一時的に
BEEP音でwaitしているがうるさい。

以下はバグというより仕様によるもの
・UFO出現はランダム（本家は確か足して10で出現だったはず）
・音楽のテンポがめちゃ遅い（80年代はのんびりしていたかも？）→修正済のはず

[![MZ-80K/CのDIGITAL INVADERをMZ-2000に移植してみました](https://img.youtube.com/vi/xXplv1aI-i4/0.jpg)](https://www.youtube.com/watch?v=xXplv1aI-i4)
