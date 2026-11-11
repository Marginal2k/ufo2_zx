; ZX0 decoder by Einar Saukas & Urusergi, "standard" version (68 bytes), format v2.
;   HL = packed stream, DE = destination. Uses AF, BC, DE, HL and 4 bytes of stack.
; In UFO-2 every packed block is: word N, N bytes of stream - so callers pass HL = block + 2.
; (1996: the blocks were packed with the author's own LZ packer "LPC"; its unpacker had the same
; entry and name - see src/original/delpc.asm and tools/lpc.py.)
DELPC	LD	BC,#FFFF	; default offset 1
	PUSH	BC
	INC	BC
	LD	A,#80
.lit	CALL	.elias	; length of the literals
	LDIR
	ADD	A,A	; copy from the last offset or a new offset?
	JR	C,.newofs
	CALL	.elias
.copy	EX	(SP),HL	; keep the source, take the offset
	PUSH	HL
	ADD	HL,DE
	LDIR
	POP	HL
	EX	(SP),HL
	ADD	A,A	; literals or a new offset?
	JR	NC,.lit
.newofs	POP	BC
	LD	C,#FE
	CALL	.eloop	; high byte of the offset
	INC	C
	RET	Z	; end mark
	LD	B,C
	LD	C,(HL)
	INC	HL
	RR	B	; the last bit of the offset is the first bit of the length
	RR	C
	PUSH	BC
	LD	BC,1
	CALL	NC,.eback
	INC	BC
	JR	.copy
.elias	INC	C	; interlaced Elias gamma code
.eloop	ADD	A,A
	JR	NZ,.eskip
	LD	A,(HL)
	INC	HL
	RLA
.eskip	RET	C
.eback	ADD	A,A
	RL	C
	RL	B
	JR	.eloop
