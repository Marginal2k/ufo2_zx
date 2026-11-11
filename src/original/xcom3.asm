; ************ "НЛО-2" после простановки защиты
;*Z80
; *O
	MMU 3,0	; page 0 at #C000
	ORG	#C000
	INCBIN "xx.b00"
	MMU 3,1	; page 1 at #C000
	ORG	#C000
	INCBIN "xx.b01"
	MMU 3,2	; page 2 at #C000
	ORG	#C000
	INCBIN "xx.b02"
	MMU 3,3	; page 3 at #C000
	ORG	#C000
	INCBIN "xx.b03"
	MMU 3,4	; page 4 at #C000
	ORG	#C000
	INCBIN "xx.b04"
	MMU 3,5	; page 5 at #C000
	ORG	#C000
	INCBIN "xx.b05"
;*P6
;	ORG #C000
;*B ..\ZX_DIsc\XX.B06
	MMU 3,7	; page 7 at #C000
	ORG	#C000
	INCBIN "xx.b07"
;--------------------
	MMU 3,0	; page 0 at #C000
	; ENT #4010
