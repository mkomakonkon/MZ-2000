# VOCALUINO4CMU用デモプログラム  
[![DEMO](https://img.youtube.com/vi/Gk1N_0d0dyk/0.jpg)](https://www.youtube.com/watch?v=Gk1N_0d0dyk)  

## ハードウェア  

使用部品.pdfの赤で囲った部品を実装すれば動作します。  
喋らなくて良ければU1周辺回路も不要です。  
Arduino NanoのスケッチはA1,A2のロケーション通りに書き込んでください。  
AOCALUINO4CMUのMIDI端子(OUT)をMIDI音源のMIDI-INに接続してください。
VOUT1はスピーカーに接続してください。  
このデモは歌わないので、ATP3011シリーズなら何でも動作します。　　
歌うのはATP3011R4-PUのみです。このデモではATP3011F4-PUを実装しています。    

## ソフトウェア  
MZ-2000でMZ-1Z001(BASIC)をLOAD  
LOADコマンドで"TIME LIMIT3.mzt"をLOAD  
MONでモニタに移ってLコマンドで”TIME LIMIT3 OBJ.mzt”をLOAD  
RUNでゲームが始まります。  
