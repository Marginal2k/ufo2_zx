; UFO-2. Devils of the Abyss (c) 1996 V. Mednonogov - the game, one assembly for sjasmplus.
;
; Memory of the running game (ZX Spectrum 128K):
;   #4000-#403F  the stack on the map (the entry JP_ST at #4010 is used once, then it is stack too)
;   #4040-#757F  resident code and data (xcom, xlid, xgamedat, font, xlib, xlie, the start of the battle code)
;   #7580-#8D7F  swap area SwpADR/SwpLEN: the rest of the battle code (xlin, xlim, xlik) or, on the map, overlay
;                xlic or xlif+disk; the part not in use is kept in page 7 at #E600, XORed with #C6 (SWPBAT)
;   #8D8D        INTJP: jump to the interrupt handler;  #8E00-#8F00 IM2TAB: the interrupt vectors (I = #8E)
;   #8F3F-#8F7F  the stack in a battle
;   #9000-#AAFF  DSCR: work screen / buffer (the start-up code xli1 runs from #9000 once)
;   #AB00-#BD..  overlay xlix;   #B000-#C4FF overlay xlesha (the 3D fight of the ships, loaded over xlix)
;   page 0  the four overlays, packed (build.py)        page 1  texts
;   page 3  sprites, landscape sets 0/1, maps 0/1       page 4  hero sprites
;   page 6  work page                                   page 7  the screen that is shown, history picture, swap
; The picture is always drawn in page 7 (the second screen): the normal screen memory holds code.
; Packed data are ZX0 (src/lib/dzx0.asm, DELPC). The disk is used only through src/game/disk.asm.
;
; Output (build/game/): main.bin = #4000..end of xli1, ovl_*.bin = unpacked overlays, pageN.bin.

	DEVICE ZXSPECTRUM128
	INCLUDE "xcom.asm"

	MMU 3,0
	SAVEBIN "main.bin",#4000,LESHA-#4000
	SAVEBIN "ovl_lesha.bin",LESHA,LESHAE-LESHA
	SAVEBIN "ovl_xlix.bin",ASMBL1,ASMBL2-ASMBL1
	SAVEBIN "ovl_xlic.bin",ASMBL2,ASMBL3-ASMBL2
	SAVEBIN "ovl_xlif.bin",ASMBL3,ASMBLE-ASMBL3
	MMU 3,1
	SAVEBIN "page1.bin",#C000,#4000
	MMU 3,3
	SAVEBIN "page3.bin",#C000,#4000
	MMU 3,4
	SAVEBIN "page4.bin",#C000,#4000
	MMU 3,7
	SAVEBIN "page7.bin",#C000,#4000
