# HOVER ATTACKの改造

起動後のアドレス  
(ダンプリストのアドレスではありません)  
B604:05→7Fに変更するとCARRIER残機127(これ以上は増やせない)  
B619:07→7Fに変更するとATTACKER残機127(これ以上は増やせない)  
C71E: DD 35 05   DEC (IX+05h)　ミサイルマイナス１　この行をNOPにするとミサイルが減らない 

残機は面クリアすると初期値に戻ってしまいます。(別に設定値があるようです)

![CLEAR](https://github.com/mkomakonkon/MZ-2000/blob/master/IO/198511_HOVER_ATTACK/CLEAR.png)
