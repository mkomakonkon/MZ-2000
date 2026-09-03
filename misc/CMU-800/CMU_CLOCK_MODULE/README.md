# CMU-800のテンポをBPM指定できるようにする<BR>
CMU-800はTEMPOボリュームでおおまかなテンポ設定ができますが、BPMの指定ができません。  
また最速でも380BPM程度なのでギャラクシアンの開始音(450BPM)が演奏できません。（当時これが不満でしたｗ）  

CLOCK INにクロックを入れるとそれに対応したテンポで演奏することができるので、外部からクロックを入れることでテンポ指定できるようにしました。  
デモでは  
ディグダグの歩行音（112BPM）  
ディグダグの歩行音（150BPM）  
ディグダグの歩行音（180BPM）  
ギャラクシアンの開始音（450BPM）  
を演奏しています。  
＝＝＝＝＝ DEMO動画 ＝＝＝＝＝<br>
[![CMU_CLOCK_MODULE](https://img.youtube.com/vi/pMFT1GAt9vs/0.jpg)](https://www.youtube.com/watch?v=pMFT1GAt9vs)  
【ピン接続図】<BR>
　　　　　＋－－－－－－－－－－－－－－－－－＋<BR>
　　　　　｜　Ａｒｄｕｉｎｏ　Ｎａｎｏ　　　　｜<BR>
　　　　　｜　　　　　　　　　　　　　　　　　｜<BR>
Ｄ２　－－｜　ＵＰボタン（ＧＮＤへ）　　　　　｜<BR>
Ｄ３　－－｜　ＤＯＷＮボタン（ＧＮＤへ）　　　｜<BR>
Ｄ４　－－｜　ＬＥＦＴボタン（ＧＮＤへ）　　　｜<BR>
Ｄ５　－－｜　ＲＩＧＨＴボタン（ＧＮＤへ）　　｜<BR>
Ｄ６　－－｜　ＳＥＴボタン（ＧＮＤへ）　　　　｜<BR>
Ｄ９　－－｜　ＣＬＯＣＫ出力　　　　　　　　　｜<BR>
　　　　　｜　ｊａｃｋの先端（ｍｏｎｏ）に出力｜<BR>
　　　　　｜　　　　　　　　　　　　　　　　　｜<BR>
Ａ４　－－｜　ＯＬＥＤ　ＳＤＡ　　　　　　　　｜<BR>
Ａ５　－－｜　ＯＬＥＤ　ＳＣＬ　　　　　　　　｜<BR>
５Ｖ　－－｜　ＯＬＥＤ　ＶＣＣ　　　　　　　　｜<BR>
ＧＮＤ－－｜　ＯＬＥＤ　ＧＮＤ　　　　　　　　｜<BR>
　　　　　＋－－－－－－－－－－－－－－－－－＋<BR>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/CMU_CLOCK_MODULE/photo/photo1.jpg" width="800"><br>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/CMU_CLOCK_MODULE/photo/top-side.jpg" width="800"><br>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/CMU_CLOCK_MODULE/photo/bottom-side.jpg" width="800"><br>
## 部品一覧<BR>
|品名|購入先|備考|参考URL|
|---|---|---|---|
|基板|秋月|[103411]両面ガラス・ユニバーサル基板 140×40mm|https://akizukidenshi.com/catalog/g/g103411/|
|Arduino NANO|Amazonとか|Arduino IDEで[CMU_CLOCK_MODULE.ino](https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/CMU_CLOCK_MODULE/CMU_CLOCK_MODULE.ino)を書き込んでください||
|OLED|Amazonとか|OLED 0.91インチディスプレイ I2C<br>ArduinoのA4/A5/5V/GNDに接続||
|DCジャック(任意)|秋月|USB給電だと間違って書き込んでしまいそうなので…<br>実はこの開発中にもやらかしてます（＾＾；；<br>ArduinoのVINに9Vを接続|https://akizukidenshi.com/catalog/g/g109408/|
|ステレオジャック|秋月|ジャックの先端(L/MONO)を使用すること<br>CLOCK INはモノラルなのでJACK中央のRはGNDにつながります<br>ArduinoのD9に接続|https://akizukidenshi.com/catalog/g/g102460/|
|押しボタンスイッチ|アリエク|秋月にはLED無しが売ってないので…<br>ArduinoのD2/D3/D4/D5/D6に接続|[参考URL](https://ja.aliexpress.com/item/1005002884956069.html?spm=a2g0o.order_list.order_list_main.15.e9fb585aThOZR9&gatewayAdapt=glo2jpn)|
|ゴム足|Amazonとか|私のは滑ってるので、シリコンタイプのものが滑らなくて良さそうです||


CLOCK INにつないでください。<BR>
<img src="https://github.com/mkomakonkon/MZ-2000/blob/master/misc/CMU-800/CMU_CLOCK_MODULE/photo/CLOCK_IN.JPG" width="400"><br>
