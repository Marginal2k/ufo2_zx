;**** HЛО-2. Дьяволы бездны ****
; *M-
; *D-
	DEFB	0
SYSINI	DEFB	28 ;systxt 28
MONINI	DEFB	1 ;1/0 в ScrBU нет/есть текст
xHACK	DEFB	#7 ;F;если 7f, то видимое поле []
	INCLUDE "xlid.asm"
	INCLUDE "xgamedat.asm"
FONT
	INCBIN "xfont.dat"
; 1996: CRC3 and TAB100 (100 bytes of the copy protection table) were here
	INCLUDE "xlib.asm"
xHAC2	DEFB	#D5 ;D6;если D6, то нет боя []
	INCLUDE "xlie.asm"
;--------swap-область
;*L+
	INCLUDE "xlin.asm"
	INCLUDE "xlim.asm"
	INCLUDE "xlik.asm"
	ASSERT	$ <= SwpADR+SwpLEN	; end of the battle code = end of the swap area
; The interrupt vectors: 257 equal bytes, so any byte on the data bus leads to INTJP. They are above #8000
; (I = #8E) to avoid the "snow" of the original 128K/+2, and outside the swap area, so always in memory.
	DEFS	(IM2TAB/256-1)*257-$	; #8D8D
INTJP	JP	INTRP
	DEFS	IM2TAB-$
	DEFS	257,IM2TAB/256-1
; *L+
; *D-
	DEFS	#8F3F-$	; 1996: DEFR (random bytes)
	DEFB	#20,#8E,#A1,#AB,#A0,#E1,#E2,#EC,#20,#A4,#AB,#EF,#20,#E0,#A0,#A7,#AC,#A5,#E9,#A5,#AD,#A8,#EF,#20,#E1,#E2,#A5,#AA,#A0,#20	; " Область для размещения стека "
	DEFS	#9000-$,#CC
; *L-
	INCLUDE "xli1.asm" ;нач. уст
	ORG	$
LESHA	DISP	#B000
	INCLUDE "xlesha.asm"
	ENT
LESHAE

	MMU 3,0	; page 0 at #C000  *********** Страница 0 ***********
	ORG	#C000
ASMBL1	DISP	#AB00
	INCLUDE "xlix.asm"
	ENT
	ORG	$
ASMBL2	DISP	SwpADR
	INCLUDE "xlic.asm"
; *L+
	DEFB	$/256,$ mod 256 ;xlic
; *L-
	ENT
	ORG	$
ASMBL3	DISP	SwpADR
	INCLUDE "xlif.asm"
	INCLUDE "disk.asm"
	DEFB	$/256,$ mod 256 ;xliF+disk
	ASSERT	$ <= SET_LS	; the save/load code at the end of xlic must survive the loading of this overlay
	ENT
ASMBLE

