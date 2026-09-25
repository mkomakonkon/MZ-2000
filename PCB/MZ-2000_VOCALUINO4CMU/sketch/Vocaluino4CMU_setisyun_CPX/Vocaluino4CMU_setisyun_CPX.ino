/* 
 * Vocaluino for CMU Ver.0.1
 *  Vorcaluino4CMU用に再構築し、バージョンも振りなおし
 *  MIDIの代わりにCMU-800の下記信号を取り込み
 *   VD[5:0]
 *   GATE_DATA
 *   CH[D:A}
 *  CMU内部のGATEx信号はLS259をエミュレート
 *  GATExのアサートタイミングでVDの値をサンプリングして、その音階で歌詞を歌わせる。
 * 
 * Vocaluino Ver.5.01
 *  低音を再チューニング
 *  基本音声データを32byte(30)文字に変更
 *  (これ以上増やすと発声しないので注意)
 * Vocaluino Ver.4.03
 *  LEDはArduinoで制御しない(ATPの/PLAY端子で点灯する)
 * Vocaluino Ver.4.00
 *  弐号機の実装にLEDアサインを変更
 * Vocaluino Ver.3.90
 *  連続する同一Noteを識別できるよう変更し
 *  初音ミクの消失に対応
 * Vocaluino Ver.2.03
 *  YMZモジュールに合わせたピッチに修正
 * Vocaluino Ver.1.00
 *  2017/10/14作成(歌詞を再生)
 * Vocaluino proto type
 *  2017/10/13作成(音階のみ)
 */
#include <AquesTalk.h>
#include <Wire.h>  // I2Cライブラリ 必須！
#include <string.h>
#include <avr/pgmspace.h>
//MIDI_CREATE_INSTANCE(HardwareSerial, Serial1, MIDI);
AquesTalk atp1(AQTK_I2C_ADDR);  // デフォルトI2Cアドレス(0x2E)
AquesTalk atp2(0x2F); // もうひとつのデバイスのI2Cアドレスは下記ツールで0x2Fとする
                       //https://www.a-quest.com/products/pico_rom_writer.html

// MIDIからAquestalkのピッチに変換------------------------
const uint16_t m2t[127] PROGMEM = {
230, //NOTE_C3,No_48
216, //NOTE_CS3,No_49
203, //NOTE_D3,No_50
190, //NOTE_DS3,No_51
179, //NOTE_E3,No_52
168, //NOTE_F3,No_53
157, //NOTE_FS3,No_54
147, //NOTE_G3,No_55
138, //NOTE_GS3,No_56
129, //NOTE_A3,No_57
121, //NOTE_AS3,No_58
113, //NOTE_B3,No_59
230, //NOTE_C3,No_48
216, //NOTE_CS3,No_49
203, //NOTE_D3,No_50
190, //NOTE_DS3,No_51
179, //NOTE_E3,No_52
168, //NOTE_F3,No_53
157, //NOTE_FS3,No_54
147, //NOTE_G3,No_55
138, //NOTE_GS3,No_56
129, //NOTE_A3,No_57
121, //NOTE_AS3,No_58
113, //NOTE_B3,No_59
230, //NOTE_C3,No_48
216, //NOTE_CS3,No_49
203, //NOTE_D3,No_50
190, //NOTE_DS3,No_51
179, //NOTE_E3,No_52
168, //NOTE_F3,No_53
157, //NOTE_FS3,No_54
147, //NOTE_G3,No_55
138, //NOTE_GS3,No_56
129, //NOTE_A3,No_57
121, //NOTE_AS3,No_58
113, //NOTE_B3,No_59
230, //NOTE_C3,No_48
216, //NOTE_CS3,No_49
203, //NOTE_D3,No_50
190, //NOTE_DS3,No_51
179, //NOTE_E3,No_52
168, //NOTE_F3,No_53
157, //NOTE_FS3,No_54
147, //NOTE_G3,No_55
138, //NOTE_GS3,No_56
129, //NOTE_A3,No_57
121, //NOTE_AS3,No_58
113, //NOTE_B3,No_59
230, //NOTE_C3,No_48
216, //NOTE_CS3,No_49
203, //NOTE_D3,No_50
190, //NOTE_DS3,No_51
179, //NOTE_E3,No_52
168, //NOTE_F3,No_53
157, //NOTE_FS3,No_54
147, //NOTE_G3,No_55
138, //NOTE_GS3,No_56
129, //NOTE_A3,No_57
121, //NOTE_AS3,No_58
113, //NOTE_B3,No_59
106, //NOTE_C4,No_60
98, //NOTE_CS4,No_61
92, //NOTE_D4,No_62
86, //NOTE_DS4,No_63
81, //NOTE_E4,No_64
75, //NOTE_F4,No_65
69, //NOTE_FS4,No_66
65, //NOTE_G4,No_67
60, //NOTE_GS4,No_68
55, //NOTE_A4,No_69
51, //NOTE_AS4,No_70
47, //NOTE_B4,No_71
44, //NOTE_C5,No_72
40, //NOTE_CS5,No_73
37, //NOTE_D5,No_74
34, //NOTE_DS5,No_75
31, //NOTE_E5,No_76
28, //NOTE_F5,No_77
25, //NOTE_FS5,No_78
23, //NOTE_G5,No_79
21, //NOTE_GS5,No_80
18, //NOTE_A5,No_81
16, //NOTE_AS5,No_82
14, //NOTE_B5,No_83
13, //NOTE_C6,No_84
11, //NOTE_CS6,No_85
9, //NOTE_D6,No_86
8, //NOTE_DS6,No_87
6, //NOTE_E6,No_88
5, //NOTE_F6,No_89
3, //NOTE_FS6,No_90
2, //NOTE_G6,No_91
1, //NOTE_GS6,No_92
0, //NOTE_A6,No_93
16, //NOTE_AS6,No_94
14, //NOTE_B6,No_95
13, //NOTE_C7,No_96
11, //NOTE_CS7,No_97
9, //NOTE_D7,No_98
8, //NOTE_DS7,No_99
6, //NOTE_E7,No_100
5, //NOTE_F7,No_101
3, //NOTE_FS7,No_102
2, //NOTE_G7,No_103
1, //NOTE_GS7,No_104
0, //NOTE_A7,No_105
16, //NOTE_AS7,No_106
14, //NOTE_B7,No_107
13, //NOTE_C8,No_108
11, //NOTE_CS8,No_109
9, //NOTE_D8,No_110
8, //NOTE_DS8,No_111
};

// 発声データ登録------------------------
// 送信可能データは32byte(30文字)
//                                 10        20        30
//                        123456789012345678901234567890
const char a[] PROGMEM = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char i[] PROGMEM = "iiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char u[] PROGMEM = "uuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char e[] PROGMEM = "eeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char o[] PROGMEM = "ooooooooooooooooooooooooooooo";
const char ka[] PROGMEM = "kaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ki[] PROGMEM = "kiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char ku[] PROGMEM = "kuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ke[] PROGMEM = "keeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char ko[] PROGMEM = "koooooooooooooooooooooooooooo";
const char ga[] PROGMEM = "gaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char gi[] PROGMEM = "giiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char gu[] PROGMEM = "guuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ge[] PROGMEM = "geeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char go[] PROGMEM = "goooooooooooooooooooooooooooo";
const char sa[] PROGMEM = "saaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char si[] PROGMEM = "siiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char su[] PROGMEM = "suuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char se[] PROGMEM = "seeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char so[] PROGMEM = "soooooooooooooooooooooooooooo";
const char za[] PROGMEM = "zaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char zi[] PROGMEM = "ziiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char zu[] PROGMEM = "zuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ze[] PROGMEM = "zeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char zo[] PROGMEM = "zoooooooooooooooooooooooooooo";
const char ta[] PROGMEM = "taaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ti[] PROGMEM = "tiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char tu[] PROGMEM = "tuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char te[] PROGMEM = "teeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char to[] PROGMEM = "toooooooooooooooooooooooooooo";
const char da[] PROGMEM = "daaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char di[] PROGMEM = "diiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char du[] PROGMEM = "duuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char de[] PROGMEM = "deeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char doo[] PROGMEM = "doooooooooooooooooooooooooooo";
const char na[] PROGMEM = "naaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ni[] PROGMEM = "niiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char nu[] PROGMEM = "nuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ne[] PROGMEM = "neeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char no[] PROGMEM = "noooooooooooooooooooooooooooo";
const char ha[] PROGMEM = "haaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char hi[] PROGMEM = "hiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char hu[] PROGMEM = "huuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char fu[] PROGMEM = "fuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char he[] PROGMEM = "heeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char ho[] PROGMEM = "hoooooooooooooooooooooooooooo";
const char ba[] PROGMEM = "baaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char bi[] PROGMEM = "biiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char bu[] PROGMEM = "buuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char be[] PROGMEM = "beeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char bo[] PROGMEM = "boooooooooooooooooooooooooooo";
const char pa[] PROGMEM = "paaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char pi[] PROGMEM = "piiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char pu[] PROGMEM = "puuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char pe[] PROGMEM = "peeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char po[] PROGMEM = "poooooooooooooooooooooooooooo";
const char ma[] PROGMEM = "maaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char mi[] PROGMEM = "miiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char mu[] PROGMEM = "muuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char me[] PROGMEM = "meeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char mo[] PROGMEM = "moooooooooooooooooooooooooooo";
const char mya[] PROGMEM = "myaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char myu[] PROGMEM = "myuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char mye[] PROGMEM = "myeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char myo[] PROGMEM = "myooooooooooooooooooooooooooo";
const char ya[] PROGMEM = "yaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char yi[] PROGMEM = "yiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char yu[] PROGMEM = "yuuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ye[] PROGMEM = "yeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char yo[] PROGMEM = "yoooooooooooooooooooooooooooo";
const char ra[] PROGMEM = "raaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ri[] PROGMEM = "riiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char ru[] PROGMEM = "ruuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char re[] PROGMEM = "reeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char ro[] PROGMEM = "roooooooooooooooooooooooooooo";
const char wa[] PROGMEM = "waaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char wo[] PROGMEM = "woooooooooooooooooooooooooooo";
const char n[] PROGMEM =  "n----------------------------";
const char kya[] PROGMEM = "kyaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char kyu[] PROGMEM = "kyuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char kyo[] PROGMEM = "kyooooooooooooooooooooooooooo";
const char gya[] PROGMEM = "gyaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char gyu[] PROGMEM = "gyuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char gyo[] PROGMEM = "gyooooooooooooooooooooooooooo";
const char sya[] PROGMEM = "syaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char syu[] PROGMEM = "syuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char sye[] PROGMEM = "syeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char syo[] PROGMEM = "syooooooooooooooooooooooooooo";
const char ja[] PROGMEM =  "jaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ji[] PROGMEM =  "jiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char ju[] PROGMEM =  "juuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char je[] PROGMEM =  "jeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char jo[] PROGMEM =  "joooooooooooooooooooooooooooo";
const char cha[] PROGMEM = "chaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char tya[] PROGMEM = "tyaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char chu[] PROGMEM = "chuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char tyu[] PROGMEM = "tyuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char che[] PROGMEM = "cheeeeeeeeeeeeeeeeeeeeeeeeeee";
const char cho[] PROGMEM = "chooooooooooooooooooooooooooo";
const char tyo[] PROGMEM = "tyooooooooooooooooooooooooooo";
const char thi[] PROGMEM = "thiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char dhi[] PROGMEM = "dhiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char nya[] PROGMEM = "nyaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char nyu[] PROGMEM = "nyuuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char nyo[] PROGMEM = "nyooooooooooooooooooooooooooo";
const char bya[] PROGMEM = "byaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char byu[] PROGMEM = "byuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char byo[] PROGMEM = "byoooooooooooooooooooooooooo";
const char pya[] PROGMEM = "pyaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char pyu[] PROGMEM = "pyuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char pyo[] PROGMEM = "pyoooooooooooooooooooooooooo";
const char rya[] PROGMEM = "ryaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char ryu[] PROGMEM = "ryuuuuuuuuuuuuuuuuuuuuuuuuuu";
const char ryo[] PROGMEM = "ryoooooooooooooooooooooooooo";
const char twu[] PROGMEM = "twuuuuuuuuuuuuuuuuuuuu";
const char fa[] PROGMEM = "faaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const char fi[] PROGMEM = "fiiiiiiiiiiiiiiiiiiiiiiiiiiii";
const char fe[] PROGMEM = "feeeeeeeeeeeeeeeeeeeeeeeeeeee";
const char fo[] PROGMEM = "foooooooooooooooooooooooooooo";
const char pai[] PROGMEM = "pai";
const char lets[] PROGMEM = "rextu_tu";
const char goi[] PROGMEM = "goiiiiiiiiiiiiiiiiiiiii";
const char en[] PROGMEM = "ennnnnnnnnnnnnnnnnnnnn";
const char joy[] PROGMEM = "jooiiiiiiiiiiiiii";
const char desu[] PROGMEM = "deeesu";
const char deesu[] PROGMEM = "deeeeeesu";
const char deeesu[] PROGMEM = "deeeeeeeeeesu";
const char hen[] PROGMEM = "heeeeeeeeennnnnnnnnnnnn";
const char zen[] PROGMEM = "zennnnnnnnnnnnnnnnnnnnn";
const char kai[] PROGMEM = "kaaiiiiiiiiiiiiii";
const char man[] PROGMEM = "maannnnnnnnnnnnnnnnnnnnn";
const char rin[] PROGMEM = "riinnnnnnnnnnnnnnnnnnnnn";
const char masu[] PROGMEM = "maaaaaaa_su";
const char gen[] PROGMEM = "geennnnnnnnnnnnnnnnnnnnn";
const char zin[] PROGMEM = "ziinnnnnnnnnnnnnnnnnnnnn";
const char komo[] PROGMEM = "komoo";
const char teen[] PROGMEM = "teeeennnn";
const char kara[] PROGMEM = "kaaaaraa";
const char mawa[] PROGMEM = "maawaa";
const char zutto[] PROGMEM = "zuutto";
const char kin[] PROGMEM = "kiiinnnn";
const char sinn[] PROGMEM = "siinnn";

const char ken[] PROGMEM = "keennnnnnnnnnnnnnnnnnnnn";
const char tai[] PROGMEM = "taaiiiiiiiiiiiiii";
const char hon[] PROGMEM = "honnnnnnnnnnnnnnnnnnnnn";
const char nin[] PROGMEM = "ninnnnnnnnnnnnnnnnnnnnn";
const char nen[] PROGMEM = "neennnn";
const char mae[] PROGMEM = "maaee";
const char naaai[] PROGMEM = "na--------------------i----";
const char siiku[] PROGMEM = "siiikuu";
const char geeki[] PROGMEM = "geeekii";

const char gan[] PROGMEM = "gaaann";
const char dan[] PROGMEM = "daann";
const char rai[] PROGMEM = "raaii";
const char runn[] PROGMEM = "ruunn";
const char nai[] PROGMEM = "naiiii";
const char naai[] PROGMEM = "naaaaaaiiii";
const char naaa[] PROGMEM = "naaaaaaaaaaaii";
const char un[] PROGMEM = "uuunnn";
const char fun[] PROGMEM = "funn";
const char ren[] PROGMEM = "rennn";
const char tann[] PROGMEM = "tann";
const char ten[] PROGMEM = "tenn";
const char jan[] PROGMEM = "jann";
const char son[] PROGMEM = "sonn";
const char yes[] PROGMEM = "ie_su";
const char hai[] PROGMEM = "hai";
const char kan[] PROGMEM = "kannnn";
const char jin[] PROGMEM = "jiiinn";
const char gin[] PROGMEM = "ginn";
const char aasu[] PROGMEM = "aaaaaa_su";
const char dai[] PROGMEM = "dai";
const char ran[] PROGMEM = "rannnnn";
const char raku[] PROGMEM = "raku";
const char tei[] PROGMEM = "tei";
const char tain[] PROGMEM = "tain";
const char sen[] PROGMEM = "sen";
const char mei[] PROGMEM = "mei";
const char teki[] PROGMEM = "teki";
// 歌詞データ登録------------------------
// ハイフンは使っちゃダメ。エラーにならないが動作しない。
// その他エラーになるもの：do→doo,sin→sinn,run→runn,tan→tann
const char * const string_table[] PROGMEM = {
//11小節
ku,raku,se,ma,i,no,ga,su,ki,da,ta,
fu,ka,ku,ka,bu,ru,fu,u,doo,no,na,ka,
mu,jo,na,se,ka,i,wo,u,ran,da,me,wa,
doo,o,si,yo,mo,na,ku,a,i,wo,ho,si,te,ta,

//23小節
a,me,ni,nu,re,ru,no,ga,su,ki,da,ta,
ku,mo,ta,ka,o,ga,ni,a,u,ka,ra,
a,ra,si,ni,o,bi,e,te,ru,fu,ri,wo,si,te,
so,ra,ga,wa,re,ru,no,wo,ma,a,tei,tann,da,

//33小節
ka,ki,na,ra,se,
hi,ka,ri,no,fa,zu,de,
rai,me,wo,
to,doo,ro,ka,se,tain,da,a,

//41小節
u,ti,na,ra,se,
i,ta,mi,no,sa,ki,e,
doo,o,si,yo,
dai,bo,so,doo,mo,na,ko,doo,wo,

//56小節
ka,na,si,u,ta,ho,doo,su,ki,da,ta,
ya,sa,si,i,ki,mo,ti,ni,na,re,ru,ka,ra,

a,ka,ru,i,ba,syo,wo,mo,to,me,te,i,ta,
da,ke,doo,fu,re,ru,no,wa,ko,wa,ka,ta,

fu,ka,ku,mo,gu,ru,no,ga,su,ki,da,ta,
u,mi,no,so,ko,ni,mo,tu,ki,ga,a,ta,

da,re,ni,mo,i,wa,na,i,ha,zu,da,ta,
ga,
i,bi,tu,na,sen,ga,ya,mi,yo,wo,ha,si,ta,

//73小節
ka,ki,na,ra,se,
ma,zi,wa,ru,ka,ru,te,
ka,ku,mei,wo,
na,si,to,ge,te,mi,tai,na,a,

u,ti,na,ra,se,
na,ge,ki,no,fo,ru,te,
doo,o,si,yo,
tyo,hon,po,kyo,bo,na,hon,syo,wo,

//105小節
wa,ta,si,
u,tu,mu,i,te,ba,ka,ri,da,

so,re,de,i,
ne,ko,ze,no,ma,ma,
to,ra,ni,na,ri,ta,i,ka,ra,

//118小節
ka,ki,na,ra,se,
hi,ka,ri,no,fa,zu,de,
rai,me,wo,
to,doo,ro,ka,se,tain,da,a,

u,ti,na,ra,se,
i,ta,mi,no,sa,ki,e,
sa,a,i,ko,

dai,bo,so,doo,mo,na,ko,doo,wo,

syo,doo,teki,kan,jo,
ho,e,te,mi,

ka,ki,na,ra,se,
ra,i,me,i,wo,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
n,n,n,n,n,n,n,n,n,
};

char buffer[30];
// ============================================================
// ATmega328P搭載 Arduino Nano 用
//
// MIDI入力を廃止し、74LS259相当の入力からNoteを生成する。
//
// LS259入力:
//   S0  = A0 = CHA
//   S1  = A1 = CHB
//   S2  = A2 = CHC
//   /G  = A3 = CHD
//   D   = D8 = GATE
//   /CLR = +5V固定
//
// VD:
//   VD0 = D2
//   VD1 = D3
//   VD2 = D4
//   VD3 = D5
//   VD4 = D6
//   VD5 = D7
//
// VD=0  -> MIDI Note No.24
// VD=63 -> MIDI Note No.87
//
// Q0～Q7の立下り:
//   VDをサンプリングして発音開始
//
// Q0～Q7の立上り:
//   対応する発音をBreak()で停止
//
// 重要:
//   Qエッジ検出とATP3011へのI2C通信を分離するため、
//   エッジ側ではイベントをリングバッファへ入れるだけ。
// ============================================================

// ---------- LS259 input ----------
const int PIN_S0   = A0;   // CHA
const int PIN_S1   = A1;   // CHB
const int PIN_S2   = A2;   // CHC
const int PIN_G    = A3;   // CHD = /G
const int PIN_D    = 8;    // GATE = D
const int PIN_ATP_RST = 13; // *ATP_RST

// 発音させるCHを1～8で指定
// V_CH=1 → CH[C:A]=000
// V_CH=2 → CH[C:A]=001
// ...
// V_CH=8 → CH[C:A]=111
const uint8_t V_CH = 1;
const uint8_t V_Q  = V_CH - 1;

// ---------- VD input ----------
const int PIN_VD0 = 2;
const int PIN_VD1 = 3;
const int PIN_VD2 = 4;
const int PIN_VD3 = 5;
const int PIN_VD4 = 6;
const int PIN_VD5 = 7;

// ---------- event queue ----------
enum EventType : uint8_t {
  EVENT_Q_FALL = 0,
  EVENT_Q_RISE = 1
};

struct QEvent {
  uint8_t type;
  uint8_t q;
  uint8_t vd;
};

const uint8_t EVENT_QUEUE_SIZE = 32;
volatile QEvent eventQueue[EVENT_QUEUE_SIZE];
volatile uint8_t eventHead = 0;
volatile uint8_t eventTail = 0;

// ---------- LS259 state ----------
volatile uint8_t qLatch = 0;

// ---------- two ATP3011 voices ----------
struct VoiceState {
  bool active;
  int8_t q;
  uint8_t note;
};

VoiceState voice[2] = {
  {false, -1, 0},
  {false, -1, 0}
};

// Vocaluino lyric index
int x = 0;


// ------------------------------------------------------------
// VD0～VD5を読む
// 0～63の6bit値
// ------------------------------------------------------------
static inline uint8_t readVD()
{
  // D2～D7 = ATmega328PのPORTD bit2～bit7
  return (uint8_t)((PIND >> 2) & 0x3F);
}

// ------------------------------------------------------------
// 現在のLS259 Q状態を計算
//
// /G=HIGH : latch保持
// /G=LOW  : addressで選択されたQがDに追従
// ------------------------------------------------------------
static inline uint8_t calculateQ(uint8_t s0,
                                 uint8_t s1,
                                 uint8_t s2,
                                 uint8_t g,
                                 uint8_t d)
{
  uint8_t q = qLatch;

  if (!g) {
    uint8_t address = s0 | (s1 << 1) | (s2 << 2);

    if (d) {
      q |= (uint8_t)(1u << address);
    } else {
      q &= (uint8_t)~(1u << address);
    }
  }

  return q;
}

// ------------------------------------------------------------
// イベントをキューへ追加
// ISRから呼ばれる
// ------------------------------------------------------------
static inline void pushEventFromISR(uint8_t type,
                                    uint8_t q,
                                    uint8_t vd)
{
  uint8_t next = (uint8_t)((eventHead + 1) % EVENT_QUEUE_SIZE);

  if (next == eventTail) {
    // キュー満杯。
    // 発音処理側が追いついていないのでイベントを捨てる。
    return;
  }

  eventQueue[eventHead].type = type;
  eventQueue[eventHead].q = q;
  eventQueue[eventHead].vd = vd;
  eventHead = next;
}

// ------------------------------------------------------------
// LS259入力変化割り込み（ATmega328P Pin Change Interrupt）
//
// A0～A3 = PC0～PC3 = PCINT8～11
// D8     = PB0     = PCINT0
// D2～D7 はVDなのでISR内ではPINDから直接読む。
// I2Cはここでは絶対に実行しない。
// ------------------------------------------------------------
static inline void ls259ISR_fast()
{
  uint8_t pc = PINC;
  uint8_t pb = PINB;

  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  uint8_t oldQ = qLatch;
  uint8_t newQ = calculateQ(s0, s1, s2, g, d);

  if (newQ == oldQ) {
    return;
  }

  qLatch = newQ;

  uint8_t falling = oldQ & (uint8_t)~newQ;
  uint8_t rising  = (uint8_t)~oldQ & newQ;

  if (falling) {
    uint8_t vd = readVD();

    for (uint8_t q = 0; q < 8; q++) {
      if (falling & (uint8_t)(1u << q)) {
        pushEventFromISR(EVENT_Q_FALL, q, vd);
      }
    }
  }

  if (rising) {
    for (uint8_t q = 0; q < 8; q++) {
      if (rising & (uint8_t)(1u << q)) {
        pushEventFromISR(EVENT_Q_RISE, q, 0);
      }
    }
  }
}

ISR(PCINT1_vect)
{
  ls259ISR_fast();
}

ISR(PCINT0_vect)
{
  ls259ISR_fast();
}

// ------------------------------------------------------------
// イベントを1件取り出す
// ------------------------------------------------------------
bool popEvent(QEvent &ev)
{
  noInterrupts();

  if (eventTail == eventHead) {
    interrupts();
    return false;
  }

  ev.type = eventQueue[eventTail].type;
  ev.q    = eventQueue[eventTail].q;
  ev.vd   = eventQueue[eventTail].vd;

  eventTail = (uint8_t)((eventTail + 1) % EVENT_QUEUE_SIZE);

  interrupts();
  return true;
}

// ------------------------------------------------------------
// 音声データをstring_tableから取得
// ATmega328PではPROGMEMを使い、SRAMを節約する。
// ------------------------------------------------------------
static inline void loadSpeechString(int index)
{
  if (index < 0) index = 0;

  // string_table自体も文字列もFlash上に置く
  const char *p = (const char *)pgm_read_word(&string_table[index]);
  strcpy_P(buffer, p);
}

// ------------------------------------------------------------
// 発音開始
//
// freeなATP3011を探して割り当てる。
// Q番号をvoiceに記録するので、同じNoteNoでも正しく停止できる。
// ------------------------------------------------------------
void startVoice(uint8_t q, uint8_t vd)
{
  // 指定したCHだけ発音する
  if (q != V_Q) {
    return;
  }

  if (vd > 63) {
    return;
  }

  // VD + 24 がMIDI NoteNo
  uint8_t noteNo = (uint8_t)(vd + 36);// ★

  loadSpeechString(x);

  // 1CHだけなのでATP1のみ使用
  atp1.SetPitch(pgm_read_word(&m2t[noteNo]));
  atp1.Synthe(buffer);

  voice[0].active = true;
  voice[0].q = q;
  voice[0].note = noteNo;

  x++;

  if (x >= (int)(sizeof(string_table) / sizeof(string_table[0]))) {
    x = 0;
  }
}

// ------------------------------------------------------------
// Q番号に対応する発音を停止
// ------------------------------------------------------------
void stopVoice(uint8_t q)
{
  // 指定したCHだけ停止する
  if (q != V_Q) {
    return;
  }

  if (voice[0].active && voice[0].q == q) {
    atp1.Break();
    voice[0].active = false;
    voice[0].q = -1;
    voice[0].note = 0;
  }
}

// ------------------------------------------------------------
// setup
// ------------------------------------------------------------
void setup()
{
  pinMode(PIN_ATP_RST, OUTPUT);
  digitalWrite(PIN_ATP_RST, HIGH);

  pinMode(PIN_S0, INPUT);
  pinMode(PIN_S1, INPUT);
  pinMode(PIN_S2, INPUT);
  pinMode(PIN_G,  INPUT);
  pinMode(PIN_D,  INPUT);

  pinMode(PIN_VD0, INPUT);
  pinMode(PIN_VD1, INPUT);
  pinMode(PIN_VD2, INPUT);
  pinMode(PIN_VD3, INPUT);
  pinMode(PIN_VD4, INPUT);
  pinMode(PIN_VD5, INPUT);

  Wire.begin();

  atp1.SetAccent(0x00);
  atp2.SetAccent(0x00);

  atp1.SetSpeed(190);
  atp2.SetSpeed(190);

  // 現在の入力状態からLS259初期状態を作る。
  uint8_t pc = PINC;
  uint8_t pb = PINB;
  uint8_t s0 = (pc >> 0) & 1;
  uint8_t s1 = (pc >> 1) & 1;
  uint8_t s2 = (pc >> 2) & 1;
  uint8_t g  = (pc >> 3) & 1;
  uint8_t d  = (pb >> 0) & 1;

  qLatch = calculateQ(s0, s1, s2, g, d);

  // ATmega328PにはA0～A3/D8用の外部割り込みがないため、
  // Pin Change Interruptを使用する。
  PCICR |= _BV(PCIE1);   // PCINT8～15 = PORTC
  PCMSK1 |= _BV(PCINT8) | _BV(PCINT9) | _BV(PCINT10) | _BV(PCINT11);

  PCICR |= _BV(PCIE0);   // PCINT0～7 = PORTB
  PCMSK0 |= _BV(PCINT0); // D8 = PB0

  // PCINT有効化前の状態を読み捨てておく
  (void)PINC;
  (void)PINB;
}

// ------------------------------------------------------------
// loop
// ------------------------------------------------------------
void loop()
{
  QEvent ev;

  while (popEvent(ev)) {

    if (ev.type == EVENT_Q_FALL) {
      startVoice(ev.q, ev.vd);
    }
    else {
      stopVoice(ev.q);
    }
  }
}
