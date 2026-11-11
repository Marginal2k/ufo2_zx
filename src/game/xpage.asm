;содержимое страниц
;СТРАНИЦЫ: c #C000
;0: #C000:
;1: #C000:T(256<),TWCMPR(256),WORDS,MENUS,PEDIA,NAMES
;2: *main*
;3: #C000:xSprites,xSHIP,xUFO
;4: #C000:xHERO(12k=8*16*96),#F000:xDIE(768),#F300:xBOOM(768),#F600
;5: *main*
;6: *swap*
;7: #C000:SCR,#D800:ATR,#DB00:
	MMU 3,4	; page 4 at #C000  ***********Страница 4***********
	ORG	#C000
xHERO
	INCBIN "xhero.dat"
xDIE	EQU	xHERO+#3000
xBOOM	EQU	xDIE+#300
xBUM	EQU	xBOOM+#300
xBULL	EQU	xBUM+#480
xSHIP
	INCBIN "xm0.zx0"
	DEFS	#FFFE-$	; 1996: DEFR (random bytes)
	MMU 3,3	; page 3 at #C000  ***********Cтраница 3***********
	ORG	#C000
xEARTH
	INCBIN "xsprites.dat"
xWEAPON	EQU	xEARTH+2880
xBUTTON	EQU	xEARTH+3840
xWBUTTN	EQU	xBUTTON+128
xBBUTTN	EQU	xWBUTTN+96
xSIGN	EQU	xEARTH+4192
xPARAM	EQU	xEARTH+5056
xKEY	EQU	xEARTH+5536
xPLUS	EQU	xKEY+576
xLABEL	EQU	xEARTH+6304
xMAP	EQU	xEARTH+7136
xMARKER
	INCBIN "xmarker.dat"
xUFO
	INCBIN "xm1.zx0"
xL0
	INCBIN "xl0.zx0"
xL1
	INCBIN "xl1.zx0"
	MMU 3,1	; page 1 at #C000  ***********Cтраница 1***********
	ORG	#C000
T
	INCBIN "x256.dat"
TWCMPR
	INCBIN "xcompres.dat"
WORDS
	INCBIN "xword.dat"
MENUS
	INCBIN "xmenu.dat"
PEDIA
	INCBIN "xfopedia.dat"
NAMES
	INCBIN "xname.dat"
	DEFS	#FFFE-$	; 1996: DEFR (random bytes)
	MMU 3,7	; page 7 at #C000  ***********Cтраница 7***********
	ORG	#C000

	INCBIN "xhist.scr"
	DEFS	1024,0
	DEFM	" No room for STS 4.x!  Please reload..."

	MMU 3,0	; page 0 at #C000
