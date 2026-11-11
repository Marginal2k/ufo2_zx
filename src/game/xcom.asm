;*L-
;*Z80
; *O
; *M-
; *D-
	MACRO	D_  ;debug
	DI
	HALT
	ENDM

	MACRO	PUSH_ 
	PUSH	HL
	PUSH	DE
	PUSH	BC
	ENDM
	MACRO	POP_ 
	POP	BC
	POP	DE
	POP	HL
	ENDM

	INCLUDE "xpage.asm"
	ORG	#4000
	DEFS	16	; room for the stack: on the map it is #4000-#403F and grows down over JP_ST (used once)
	ORG	#4000+16
	; ENT $
JP_ST	JP	xSTART ;вх.
	DEFS	#4040-$	; 1996: DEFR (random bytes)
;Interupt entry
INTRP	PUSH	HL
	LD	HL,SEED
	INC	(HL)
	JR	NZ,INTR2
	INC	HL
	INC	(HL)
INTR2	POP	HL
	EI
	RETI
SEED	DEFW	1 ;счётчик
NRFT	DEFB	1 ;для XIO
OVLTAB	DEFS	8	; addresses of the four packed overlays in page 0, filled in by build.py (LESHA, xlix, xlic, xlif+disk)
DSKDRV	DEFB	0	; TR-DOS drive the game was loaded from (0 = A:), set by the loader
;Interupt table
;==================================обслуживание клавиатуры
PRSROW	IN	A,(C)
	CPL
	AND	#1F
	RET

;TMO	LD	A,(KEYJOY)
;	OR	A
;	JR	NZ,TMOJOY
;	LD	C,#FE
;	LD	B,C
;TMOO	CALL	PRSROW
;	JR	NZ,TMOOK
;	RLC	B
;	JR	TMOO
;TMOOK	LD	C,A
;	RET
;TMOJOY	CALL	CONTR
;	OR	A
;	JR	Z,TMOJOY
;	RET

PRSKEY	PUSH	BC
	LD	C,#FE
	CALL	PRSROW
	POP	BC
	AND	C
	RET

CONTR	PUSH_
	LD	A,(KEYJOY)
	OR	A
	JR	Z,CO1
	LD	C,#1F
	CALL	PRSROW
	XOR	#1F
CO2	LD	(CONTRB),A
	LD	A,(PMOUSE)
	OR	A
	CALL	NZ,MOUSE
	POP_
	LD	A,(CONTRB)
	RET
CO1	LD	HL,(KEYS)
	LD	E,0
	LD	D,5
CO3	LD	C,(HL)
	INC	HL
	LD	B,(HL)
	CALL	PRSKEY
	JR	Z,CO4
	SET	5,E
CO4	RRC	E
	DEC	D
	INC	HL
	JR	NZ,CO3
	LD	A,E
	JR	CO2

DELAY	EI
	HALT
	DI
	DEC	A
	JR	NZ,DELAY
	RET	Z

;*************Параметры настройки игры**
C_ONOF	DEFB	0 ;0-вкл/1-выкл
KEYN	DEFB	0
KEYS	DEFW	KBR
KEYJOY	DEFB	0 ;(1-K.-stick)
PMOUSE	DEFB	0 ;(1-K.-mouse)

CFGLEN	EQU	$-C_ONOF
;***************************************
CONTRB	DEFB	0
KBR	DEFW	#DF01,#DF02,#FD01,#FB01,#7F07
KBR2	DEFW	#7F04,#7F08,#FE02,#FD01,#7F03
INT2	DEFW	#EF08,#EF10,#EF04,#EF02,#EF01
KUR	DEFW	#EF04,#F710,#EF10,#EF08,#EF01 ;;;

RND	PUSH	HL
	LD	HL,(RNA)
	INC	HL
;;;	LD	A,R
;;;	ADD	A,H
	LD	A,H ;;;
	AND	#1F
	LD	H,A
	LD	A,(RNB)
	RRCA
	XOR	(HL)
	ADD	A,L
	LD	(RNA),HL
	LD	(RNB),A
	POP	HL
	RET

; 1996: the IM2 vector table was here (#4100, I=#41). I pointing into #4000-#7FFF makes "snow" on the
; original 128K/+2 (the ULA misreads the refresh address), so the table lives at IM2TAB (xmain.asm) now.

xSTART	DI
	LD	SP,#4030
	CALL	START1 ;нач.уст. (1996: here the protection was initialised and the memory snapshot for the disk was taken)
start	DI
	LD	SP,#4040
	LD	A,IM2TAB/256
	LD	I,A
	IM	2
	CALL	START2 ;нач.уст
	CALL	BACK
	LD	IX,MUST
	CALL	MENUC
	CALL	MU_ENT
	CALL	NO_3D
	CALL	MLOOP ;---начало
;	CALL XEARTH  ;--удали
;	CALL COPYAT  ;
;	LD A,0       ;
;	LD (T_INTR),A;
;	LD A,4       ;
;	LD (TARoff),A;
;	LD (NRECR),A ;
;	LD (AQU),A   ;
;	CALL RECRUT  ;
;	CALL MLOOP

MUST	DEFW	#202,#3412
MU_ENT	LD	A,#BF ;ждать ENTER
	IN	A,(#FE)
	RRA
	JR	C,MU_ENT
	RET	NC
NO_3D	RRCA ;откл 3D боя
	RRCA
	RRCA
	LD	HL,xHAC2
	RET	C
	INC	(HL)
	RET
;Main procedures
	INCLUDE "xmain.asm"
