; *Z80
; *O
	MMU 3,4	; page 4 at #C000
	ORG	#C000
	INCBIN "xcom.b00"
	MMU 3,3	; page 3 at #C000
	ORG	#C000
	INCBIN "xcom.b01"
	MMU 3,1	; page 1 at #C000
	ORG	#C000
	INCBIN "xcom.b02"
	MMU 3,7	; page 7 at #C000
	ORG	#C000
	INCBIN "xcom.b03"
	MMU 3,0	; page 0 at #C000

	ORG	#C000
BLK2
	INCBIN "xcom.lp2"
BLK3
	INCBIN "xcom.lp3"
BLK4
	INCBIN "xcom.lp4"
BLK1
	INCBIN "xcom.lp1"
	DEFS	#FFF0-$	; 1996: DEFR (random bytes)
	DEFB	#8C,#AE,#EF,#20,#E0,#A0,#A1,#AE,#E2,#A0,#21	; "Моя работа!"

	ORG	#4000
	DEFW	BLK1+2
	DEFW	BLK2+2
	DEFW	BLK3+2
	DEFW	BLK4+2
	DEFS	#4000+16-$,1
	; ENT $ ;--------вход
	INCBIN "xcom.b04"
