;**** HЛО-2. Дьяволы бездны ****
;      Модуль концовки игры
	ORG	#C000

musEND
	INCBIN "xend.mus"
scrEND
	INCBIN "xend1.scr"
txtEND
	INCBIN "xend.dat"
	DEFS	#F000-$,26
	DEFW	musEND
	DEFW	scrEND
	DEFW	txtEND

ENDEND
