この基板にはCMU-800と同じアドレスデコードと8255が載っていて、<br>
MZとCMUがやり取りしている信号のうち、CVに関するデータをArduinoが受け取って、その音階でATP3011R4-PUを発音させています。<br>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/PCB/MZ-2000_VOCALUINO4CMU/Images/PCB-photo1.png" width="600"><br>
歌詞はスケッチ内に書き込んでいるので、曲が変わる度にスケッチを書き換える必要があります（＾＾；<br>
また、MZとCMUが通信している信号をもらう仕様上、この基板単体では動作しません。★CMU-800本体が必要です★<br>
<br>
＝＝＝＝＝ DEMO動画 ＝＝＝＝＝<br>
[![VOCALUINO4CMU](https://img.youtube.com/vi/i1UvYEcTje4/0.jpg)](https://www.youtube.com/watch?v=i1UvYEcTje4)  

Rev.0.2<br>
MZ-2000_VOCALUINO4CMU.zipはKiCADデータです。<br>
（試作機のバグ対応を埋め込んだとりあえずのバージョンで実績はありません。）<br>
sketchはArduino Nano用の書込みデータです。<br>
VO-SEISYUN-CPX.mzt：CMU-800用の曲データです。<br>
<br>
MZ-2000の拡張基板として作っているけど、今のところCMU-800の信号しか使っていないので、他のマイコンでも動作すると思います。<br>

<br>
詳細はこれから書きます。<br>
要望や質問があればyoutubeのコメントに書いてもらえれば対応できるものは対応します。<br>
<br>
今後の予定<br>
・拡張I/Oポートに入れるとArduinoのマニュアルリセットができなくなるので、コマンドでのリセットは欲しい。<br>
　当初ドラムデータのみ使用ビット(bit7)が使えないか検討したけど、ドラム信号解除に使っていたので検討中止。<br>
・外付けドラム連携機能<br>

~~・リアルタイムテンポ調整機能を思いついたのでそれも入れたいかも…~~
<br>→
[mid2cmu](https://github.com/mkomakonkon/MZ-2000/tree/master/misc/CMU-800/mid2cmu) 側で対応済<br><br>

## MZ-2000以外の機種でも使えるようにCMU-800のピンアサインの変換基板を作りました。<br>
VOCALUINO4CMUの2x22のピンヘッダー用端子に接続することで、CMU-800のI/F基板と50pinのフラットケーブルで接続できるようになります。<br>
VOCALUINO4CMU-ADP.zip<br>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/PCB/MZ-2000_VOCALUINO4CMU/Images/ADP-F.png" width="300"><img src="https://github.com/mkomakonkon/MZ-2000/blob/master/PCB/MZ-2000_VOCALUINO4CMU/Images/ADP-B.png" width="300"><br>
カードエッジ用のコネクタはアリエクなどで入手可能です。<br>
https://ja.aliexpress.com/item/33056457025.html?spm=a2g0o.order_list.order_list_main.116.79cf585aADnaRj&gatewayAdapt=glo2jpn<br>
