# SELF RELOCATABLE DEBUGGER  
'80/11月号(MZ-80B活用研究)掲載の物です  
  
  |コマンド|コマンド名|使用例|説明|
  |---|---|---|---|
  |M|メモリ・ダンプ|M [S-ADR] [E-ADR]|ダンプ中SPACEでEDITモード、SFT;BREAKかCRでダンプ再開<BR>ダンプ中にCRでコマンド待ち|
  |W|メモリ・ライト|W [ADR]|入力中「←」で1BYTE前へ<BR>CRかDELでコマンド待ちへ|
