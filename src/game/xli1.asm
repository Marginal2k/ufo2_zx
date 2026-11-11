;Начальные установки
; 1996: START1 also computed the check sums CRC2, CRC3, CRC4 of the copy protection and then erased itself.
START1	LD	HL,start
	LD	(JP_ST+1),HL
	CALL	SWPBAT	; the battle code goes to page 7
	CALL	LDASM1	; map/menu overlays in
	CALL	LDASM2
	JP	MEM7
START2	LD	A,R
	JR	STRT2
	DEFM	"*** Hello, my dear! You find hidden entry in my subject! ***"
	DEFM	" (812)1433303 *** UFO-2 by Vyacheslav Mednonogov (c)1996 ***"
STRT2	LD	(RNB),A
	LD	(NX_RNB),A
;------------созд игр данных
	M_ 3
	LD	HL,DATA
	LD	DE,NEWDAT
	LD	B,6
JJ0	PUSH	BC
	PUSH	HL
JJ1	CALL	RND
	CP	192
	JR	NC,JJ1
	INC	A
	LD	(N_AQU),A
	CALL	RND
	LD	(RNBgen),A
	CALL	RND
	LD	(RNAgen+1),A
	AND	#F
	INC	A
	LD	(TARoff),A
	LD	BC,480
	LDIR
	POP	HL
	POP	BC
	DJNZ	JJ0
	JP	MEM7
