;*** AILZ80ASM *** Z-80 Assembler
;***  CMU-800 BGM ENGINE  Ver 0.6-V2INT (曲データ形式v2専用・EXINT割り込み対応)  ***
; ※ mid2bgm2.py で作った形式v2のデータだけが鳴る。形式v1のデータ(mid2bgm.py)は、bgm_cmu800.asm を使う
;
; TIME LIMIT2 用 CMU-800 BGM演奏ルーチン (ゲーム周期駆動・待たない方式)
;
; 【使い方】 効果音(C000)を呼ぶのと同じ方法で、次のアドレスを呼ぶ
;   A000H  BGM_INIT  CMU-800を初期化して無音にする (ゲーム開始時に1回)
;   A009H  BGM_PLAY  曲を先頭から演奏開始 (場面が変わるたびに呼んでよい)
;   A003H  BGM_TICK  ゲームのメインループで1周ごとに1回呼ぶ (すぐ戻る)
;   A006H  BGM_STOP  演奏を止めて無音にする
;   A012H  BGM_INTON   EXINTの割り込みで演奏を進める(0038Hを書き換え、IM 1、EI)。BASICから USR($A003) は呼ばない
;   A015H  BGM_INTOFF  割り込みを止める(0038Hを元に戻し、IM 0)。先にArduino側を E0 にしてから呼ぶ
;   A00FH  BGM_CH8   CH8にCV=0のノートONを1回だけ送る(曲やCH1〜6とは無関係)
;                    ゲートOFF→ノートON(CV=0)→約0.8ms→ゲートOFF の順で、毎回必ずQ7が1→0に落ちる
;
; 【設定】 BASICからPOKEできる
;   A00CH  BGM_SPEED    TICKを何回呼んだら曲が1ステップ進むか (1以上, 初期値3)
;   A00DH  BGM_SONGPTR  PLAYで演奏する曲データの先頭アドレス (下位,上位の2byte)
;
;
; 【曲データ形式 v2】 1ステップの出来事を、1つの記録にまとめる
;   [ヘッダ][次の記録までのステップ数][音階,GT]x発音数 [リズム]
;   ヘッダ  bit0-5 = そのステップで発音するボイス(CH1-6)  bit6 = リズムが付く
;           00H = 発音もリズムもない(待つだけ)   0FEH lo,hi = ジャンプ   0FFH = 終了
;   音階,GT は、ヘッダのビットの小さい順(CH1から)に並ぶ。リズムは最後に1バイト
;   音階 n は 0=O0のC。GT(音を出す長さ)は、次の音までのステップ数より必ず小さくする
;   リズム: bit7=BD bit6=SD bit5=LT bit4=HT bit3=CY bit2=OH bit1=CH
;
; 【注意】 レジスタ(AF,BC,DE,HL)は保存して戻る
;          Ver 0.3: BASICのスタックを使わず、専用スタック(A520-A59F)で動く
;                   (BASICのFOR/GOSUBが深い所から呼んでも、BASICの領域を壊さないため)
;          このファイルのバイナリは、9000-CEFFのOBJより「後」にロードすること
;          (OBJのA000付近はゼロで埋まっていて、先にBGMを置くと消える)

BGM_START   EQU 0A000H
BGM_WORK    EQU 0A500H

W_ACTIVE    EQU BGM_WORK+0      ; 0=停止 1=演奏中
W_DIV       EQU BGM_WORK+1      ; TICK分周カウンタ
W_WAIT      EQU BGM_WORK+2      ; 次のイベントまでの残りステップ
W_RHY       EQU BGM_WORK+3      ; リズム信号を出している間は1
W_PTR       EQU BGM_WORK+4      ; 曲データの現在位置(2byte)
W_GT        EQU BGM_WORK+6      ; 各チャンネルの残りGT(6byte, 0=自動消音なし)
W_SP        EQU BGM_WORK+12     ; 呼び出し元(BASIC)のスタックポインタ(2byte)
W_HDR       EQU BGM_WORK+14     ; 読み込み中の記録のヘッダ(1byte)
W_SAVEJP    EQU BGM_WORK+16     ; 元の0038Hの飛び先(2byte)
BGM_STACK   EQU BGM_WORK+0A0H   ; 専用スタックの一番上(A520-A59Fの128byteを使う)

            ORG BGM_START
            JP      BGM_INIT    ; A000
            JP      BGM_TICK    ; A003
            JP      BGM_STOP    ; A006
            JP      BGM_PLAY    ; A009
BGM_SPEED:  DEFB    3           ; A00C
BGM_SONGPTR: DEFW    SONG_DEMO   ; A00D
            JP      BGM_CH8     ; A00F
            JP      BGM_INTON   ; A012
            JP      BGM_INTOFF  ; A015

;----------------------------------------------------------
; BGM_INIT : CMU-800初期化・無音
;----------------------------------------------------------
BGM_INIT:   DI                      ; 割り込み処理と重ならないようにする
            LD      (W_SP),SP
            LD      SP,BGM_STACK
            PUSH    AF
            PUSH    BC
            PUSH    DE
            PUSH    HL
            LD      A,88H
            OUT     (9BH),A     ; 8255モード設定
            LD      A,0FFH
            OUT     (99H),A     ; リズム消音
            CALL    SET_MODE0
            CALL    STOP_ALL
            CALL    CLR_GT
            XOR     A
            LD      (W_ACTIVE),A
            LD      (W_RHY),A
            POP     HL
            POP     DE
            POP     BC
            POP     AF
            LD      SP,(W_SP)
            EI
            RET

;----------------------------------------------------------
; BGM_PLAY : 曲を先頭から演奏開始
;----------------------------------------------------------
BGM_PLAY:   DI                      ; 割り込み処理と重ならないようにする
            LD      (W_SP),SP
            LD      SP,BGM_STACK
            PUSH    AF
            PUSH    BC
            PUSH    DE
            PUSH    HL
            CALL    STOP_ALL
            CALL    CLR_GT
            CALL    SET_MODE3
            LD      HL,(BGM_SONGPTR)
            LD      (W_PTR),HL
            XOR     A
            LD      (W_WAIT),A
            LD      (W_RHY),A
            INC     A
            LD      (W_DIV),A   ; 最初のTICKですぐ演奏開始
            LD      (W_ACTIVE),A
            POP     HL
            POP     DE
            POP     BC
            POP     AF
            LD      SP,(W_SP)
            EI
            RET

;----------------------------------------------------------
; BGM_STOP : 演奏停止・無音
;----------------------------------------------------------
BGM_STOP:   DI                      ; 割り込み処理と重ならないようにする
            LD      (W_SP),SP
            LD      SP,BGM_STACK
            PUSH    AF
            PUSH    BC
            PUSH    DE
            PUSH    HL
            CALL    STOP_ALL
            CALL    SET_MODE0
            CALL    CLR_GT
            XOR     A
            LD      (W_ACTIVE),A
            LD      (W_RHY),A
            POP     HL
            POP     DE
            POP     BC
            POP     AF
            LD      SP,(W_SP)
            EI
            RET

;----------------------------------------------------------
; BGM_CH8 : CH8にCV=0のノートONを1回送る(曲の演奏とは無関係。演奏中でも、止まっていても使える)
;   CMU-800のシーケンサーと同じ手順で、CH8(=7)に書く。受け側(Arduino)はゲートが
;   1→0に落ちる瞬間のCVを読むので、先にゲートOFFにして、必ず落ちる変化を作る。
;   ① ゲートOFF (CV=0, bit7=1)   ② ノートON (CV=0, bit7=0)   ③ 約0.8ms待つ   ④ ゲートOFF
;----------------------------------------------------------
BGM_CH8:    DI                      ; 割り込み処理と重ならないようにする
            LD      (W_SP),SP
            LD      SP,BGM_STACK
            PUSH    AF
            PUSH    BC
            LD      A,80H
            CALL    CH8_OUT         ; ① ゲートOFF
            XOR     A
            CALL    CH8_OUT         ; ② ノートON CV=0
            LD      B,0
CH8_W:      DJNZ    CH8_W           ; ③ 約0.8ms待つ
            LD      A,80H
            CALL    CH8_OUT         ; ④ ゲートOFF
            POP     BC
            POP     AF
            LD      SP,(W_SP)
            EI
            RET

; A=98hに出す値(下位6bit=CV, bit7=ゲート)。CH8を選択して反映する
CH8_OUT:    OUT     (98H),A
            LD      A,0FH           ; CH8(=7)を選択 7*2+1
            OUT     (9AH),A
            DEC     A
            OUT     (9AH),A         ; 1→0で反映
            LD      B,10
CH8_H:      DJNZ    CH8_H           ; 反映を保つ(約30us)
            LD      A,1
            OUT     (9AH),A         ; 選択を元に戻す
            RET

;----------------------------------------------------------
; EXINT割り込みで演奏を進める
;   BGM_INTON : 0038H(RST 38)の飛び先を BGM_ISR にして、IM 1 にする。元の飛び先は保存しておく
;   BGM_INTOFF: 0038Hの飛び先を元に戻し、IM 0(電源投入時の状態)にする
;   BGM_ISR   : 割り込みのたびに BGM_TICK を1回呼ぶ(BGM_SPEED=3 なら、3回の割り込みで1ステップ)
;   BGM_TICKは AF,BC,DE,HL を保存し、専用スタックで動く。IX,IY,裏レジスタは使わない
;----------------------------------------------------------
BGM_INTON:  DI
            PUSH    AF
            PUSH    DE
            PUSH    HL
            LD      HL,(0039H)      ; 今の飛び先(元は0D07)
            LD      DE,BGM_ISR
            OR      A
            SBC     HL,DE
            JR      Z,IO_2          ; すでに設置済みなら、元の値は保存し直さない
            ADD     HL,DE
            LD      (W_SAVEJP),HL
            LD      HL,BGM_ISR
            LD      (0039H),HL      ; JP BGM_ISR にする
IO_2:       IM      1               ; データバスを読まず、必ず0038Hへ飛ぶ
            POP     HL
            POP     DE
            POP     AF
            EI
            RET

BGM_INTOFF: DI
            PUSH    AF
            PUSH    HL
            LD      HL,(W_SAVEJP)
            LD      A,H
            OR      L
            JR      Z,IF_2          ; 設置していない
            LD      (0039H),HL      ; 元の飛び先に戻す
IF_2:       IM      0               ; 電源投入時の割り込みモード
            POP     HL
            POP     AF
            EI
            RET

BGM_ISR:    CALL    BGM_TICK
            EI
            RETI

;----------------------------------------------------------
; BGM_TICK : ゲームのメインループで1周ごとに呼ぶ
;----------------------------------------------------------
BGM_TICK:   LD      (W_SP),SP
            LD      SP,BGM_STACK
            PUSH    AF
            PUSH    BC
            PUSH    DE
            PUSH    HL
            CALL    TICK_MAIN
            POP     HL
            POP     DE
            POP     BC
            POP     AF
            LD      SP,(W_SP)
            RET

TICK_MAIN:  LD      A,(W_ACTIVE)
            OR      A
            RET     Z
            LD      A,(W_RHY)   ; 前回出したリズム信号を元に戻す
            OR      A
            JR      Z,TM_1
            XOR     A
            LD      (W_RHY),A
            LD      A,0FFH
            OUT     (99H),A
TM_1:       LD      A,(W_DIV)
            DEC     A
            LD      (W_DIV),A
            RET     NZ          ; まだ曲を進める時間ではない
            LD      A,(BGM_SPEED)
            LD      (W_DIV),A
            CALL    GATE_STEP   ; GTを1ステップ進め、0になったチャンネルを消音
            LD      A,(W_WAIT)
            OR      A
            JR      Z,RD_START
            DEC     A
            LD      (W_WAIT),A
            RET     NZ          ; まだ待ち時間が残っている
RD_START:   LD      HL,(W_PTR)
RD_REC:     LD      A,(HL)          ; ヘッダ
            INC     HL
            CP      0FEH
            JR      Z,RD_JUMP
            CP      0FFH
            JR      Z,RD_END
            LD      (W_HDR),A
            AND     3FH             ; 発音するボイスのビット
            LD      D,A
            LD      A,(HL)          ; 次の記録までのステップ数
            INC     HL
            LD      (W_WAIT),A
            LD      A,D
            OR      A
            JR      Z,RD_DONE       ; 発音なし
            LD      E,0             ; E=ボイス番号
RD_VLOOP:   SRL     D
            JR      NC,RD_VNEXT
            LD      C,(HL)          ; C=音階
            INC     HL
            LD      B,(HL)          ; B=GT
            INC     HL
            PUSH    HL              ; データ位置
            LD      HL,W_GT
            LD      A,L
            ADD     A,E
            LD      L,A
            LD      (HL),B          ; 残りGTをセット(W_GTは256バイト境界をまたがない)
            LD      A,C
            CALL    NOTE_ON         ; A=音階 E=ボイス (AF,DE,HLは保存される)
            POP     HL
RD_VNEXT:   INC     E
            LD      A,D
            OR      A
            JR      NZ,RD_VLOOP     ; 残りのボイスがなければ終わり
RD_DONE:    LD      A,(W_HDR)
            BIT     6,A
            JR      Z,RD_SAVE
            LD      A,(HL)          ; リズム
            INC     HL
            AND     0FEH            ; bit0は未使用
            CPL                     ; 鳴らすビットを0にする(1→0で発音)
            OUT     (99H),A
            LD      A,1
            LD      (W_RHY),A       ; 次のTICKで1に戻す
RD_SAVE:    LD      (W_PTR),HL
            RET
RD_JUMP:    LD      E,(HL)
            INC     HL
            LD      D,(HL)
            EX      DE,HL
            JR      RD_REC
RD_END:     CALL    STOP_ALL
            CALL    SET_MODE0
            CALL    CLR_GT
            XOR     A
            LD      (W_ACTIVE),A
            RET

;----------------------------------------------------------
; GT(音を出す長さ)の管理
;----------------------------------------------------------
; 1ステップごとに呼ぶ。残りGTを1減らし、0になったチャンネルを消音する
GATE_STEP:  LD      HL,W_GT
            LD      E,0
GS_1:       LD      A,(HL)
            OR      A
            JR      Z,GS_2      ; 0=自動消音なし(または消音済み)
            DEC     A
            LD      (HL),A
            JR      NZ,GS_2
            PUSH    HL
            CALL    NOTE_OFF    ; E=チャンネル
            POP     HL
GS_2:       INC     HL
            INC     E
            LD      A,E
            CP      6
            JR      NZ,GS_1
            RET

; 全チャンネルの残りGTを0にする
CLR_GT:     LD      HL,W_GT
            LD      B,6
CG_1:       LD      (HL),0
            INC     HL
            DJNZ    CG_1
            RET

;----------------------------------------------------------
; CMU-800 ハード制御
;----------------------------------------------------------
; 8253を停止モード(モード0)にする
SET_MODE0:  LD      A,30H
            OUT     (93H),A
            OUT     (97H),A
            LD      A,70H
            OUT     (93H),A
            OUT     (97H),A
            LD      A,0B0H
            OUT     (93H),A
            OUT     (97H),A
            RET

; 8253を演奏モード(モード3・矩形波)にする
SET_MODE3:  LD      A,36H
            OUT     (93H),A
            OUT     (97H),A
            LD      A,76H
            OUT     (93H),A
            OUT     (97H),A
            LD      A,0B6H
            OUT     (93H),A
            OUT     (97H),A
            RET

; 全チャンネル消音 + リズム消音
STOP_ALL:   LD      A,0FFH
            OUT     (99H),A
            LD      E,0
SA_1:       CALL    NOTE_OFF
            INC     E
            LD      A,E
            CP      6
            JR      NZ,SA_1
            RET

; 発音  A=音階(0=O0のC)  E=チャンネル(0-5)
NOTE_ON:    PUSH    AF
            PUSH    DE
            PUSH    HL
            LD      L,A
            LD      H,0
            ADD     HL,HL
            LD      BC,NOTE_TABLE
            ADD     HL,BC
            LD      C,(HL)
            INC     HL
            LD      B,(HL)      ; BC=周波数カウンタ値
NO_1:       CP      64
            JR      C,NO_2
            SUB     12
            JR      NO_1
NO_2:       OUT     (98H),A     ; CV出力(bit7=0で発音)
            LD      A,E
            SLA     A
            OR      1
            OUT     (9AH),A     ; チャンネル選択
            DEC     A
            OUT     (9AH),A     ; 1→0で反映
            LD      A,C
            LD      D,0
            EX      DE,HL
            LD      DE,CMU_IO_TBL
            ADD     HL,DE
            LD      C,(HL)
            OUT     (C),A       ; 周波数 下位
            LD      A,B
            OUT     (C),A       ; 周波数 上位
            LD      A,1
            OUT     (9AH),A
            POP     HL
            POP     DE
            POP     AF
            RET

; 消音  E=チャンネル(0-5)
NOTE_OFF:   PUSH    AF
            PUSH    DE
            PUSH    HL
            LD      A,80H
            OUT     (98H),A     ; ゲートOFF
            LD      A,E
            SLA     A
            OR      1
            OUT     (9AH),A
            DEC     A
            OUT     (9AH),A
            LD      D,0
            EX      DE,HL
            LD      DE,CMU_IO_TBL
            ADD     HL,DE
            LD      C,(HL)
            LD      A,1
            OUT     (C),A       ; 周波数 下位(最低値)
            DEC     A
            OUT     (C),A       ; 周波数 上位
            LD      A,1
            OUT     (9AH),A
            POP     HL
            POP     DE
            POP     AF
            RET

CMU_IO_TBL: DEFB    90H,91H,92H,94H,95H,96H

NOTE_TABLE:
;           C      C+     D      D+     E      F      F+     G      G+     A      A+     B
            DEFW    9741H,8EBEH,86BBH,7F2EH,780BH,714EH,6AEDH,64ECH,5F41H,59E8H,54D9H,5015H ; O0
            DEFW    4B95H,4754H,4353H,3F8DH,3BFCH,389EH,356EH,326EH,2F99H,2CEDH,2A66H,2805H ; O1
            DEFW    25C5H,23A5H,21A5H,1FC3H,1DFBH,1C4CH,1AB4H,1934H,17CAH,1674H,1531H,1401H ; O2
            DEFW    12E1H,11D1H,10D1H,0FE1H,0EFDH,0E26H,0D59H,0C99H,0BE4H,0B39H,0A98H,0A00H ; O3
            DEFW    0970H,08E8H,0868H,07F0H,077EH,0712H,06ACH,064CH,05F2H,059CH,054CH,0500H ; O4
            DEFW    04B8H,0474H,0434H,03F8H,03BFH,0389H,0356H,0326H,02F9H,02CEH,02A6H,0280H ; O5
            DEFW    025CH,023AH,021AH,01FCH,01DFH,01C4H,01ABH,0193H,017CH,0167H,0153H,0140H ; O6
            DEFW    012EH,011DH,010DH,00FEH,00F0H,00E2H,00D5H,00C9H,00BEH,00B3H,00A9H,00A0H ; O7
            DEFW    0097H,008EH,0086H,007FH,0078H,0071H,006AH,0064H,005FH,0059H,0054H,0050H ; O8
            DEFW    004BH,0047H,0043H,003FH,003CH                                           ; O9

;----------------------------------------------------------
; 動作確認用の曲 (ド・ミ・ソ・ドをメロディ、ベースとドラム付き)
;----------------------------------------------------------
SONG_DEMO:
DEMO_LOOP:  DEFB    43H,4           ; CH1+CH2+リズム, 次の記録まで4ステップ
            DEFB    48,3            ; CH1 O4のC  GT=3
            DEFB    24,3            ; CH2 O2のC
            DEFB    80H             ; バスドラム
            DEFB    43H,4
            DEFB    52,3,24,3       ; E
            DEFB    40H             ; スネア
            DEFB    43H,4
            DEFB    55,3,24,3       ; G
            DEFB    80H
            DEFB    43H,4
            DEFB    60,3,24,3       ; O5のC
            DEFB    40H
            DEFB    0FEH
            DEFW    DEMO_LOOP
