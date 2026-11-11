; UFO-2: the manual viewer. Two blocks: pictures for page 7 (#DB00) and the program with the text (#7000).
	DEVICE ZXSPECTRUM128
	INCLUDE "xbinstr.asm"
	SAVEBIN "manual.bin",#7000,MANEND-#7000
	MMU 3,7
	SAVEBIN "manual7.bin",#DB00,P7END-#DB00
