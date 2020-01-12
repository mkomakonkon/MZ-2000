# HOVER ATTACKの改造

起動後のアドレス  
(ダンプリストのアドレスではありません)  
D0E4h:05→7Fに変更するとCARRIER残機127(これ以上は増やせない)  
D0F9h:07→7Fに変更するとATTACKER残機127(これ以上は増やせない)  
C71Eh: DD 35 05   DEC (IX+05h)　ミサイルマイナス１　この行をNOPにするとミサイルが減らない 

![CLEAR](https://github.com/mkomakonkon/MZ-2000/blob/master/IO/198511_HOVER_ATTACK/CLEAR.png)
