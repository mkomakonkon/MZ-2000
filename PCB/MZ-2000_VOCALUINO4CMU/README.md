この基板にはCMU-800と同じアドレスデコードと8255が載っていて、<br>
MZとCMUがやり取りしている信号のうち、CVに関するデータをArduinoが受け取って、その音階でATP3011R4-PUを発音させています。<br>
歌詞はスケッチ内に書き込んでいるので、曲が変わる度にスケッチを書き換える必要があります（＾＾；<br>
また、MZとCMUが通信している信号をもらう仕様上、この基板単体では動作しません。★CMU-800本体が必要です★<br>
[![VOCALUINO4CMU](https://img.youtube.com/vi/i1UvYEcTje4/0.jpg)](https://www.youtube.com/watch?v=i1UvYEcTje4)  

Rev.0.2<br>
MZ-2000_VOCALUINO4CMU.zipはKiCADデータです。<br>
sketchはArduino Nano用の書込みデータです。<br>
VO-SEISYUN-CPX.mzt：CMU-800用の曲データです。<br>
試作機のバグ対応を埋め込んだとりあえずのバージョンで実績はありません。<br>
次のバージョンでドラム連携機能を追加したい。<br>
リアルタイムテンポ調整機能を思いついたのでそれも入れたいかも…<br>
<br>
MZ-2000の拡張基板として作っているけど、今のところCMU-800の信号しか使っていないので、他のマイコンでも動作すると思います。<br>
<br>
詳細はこれから書きます。<br>
要望や質問があればyoutubeのコメントに書いてもらえれば対応できるものは対応します。<br>
