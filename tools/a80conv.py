#!/usr/bin/env python3
"""Convert sources of "Assembler 128 for Z80" (ASM80.EXE, a GENS4 dialect by V. Mednonogov, CP866) to sjasmplus (UTF-8).

    python tools/a80conv.py <dir with .A80> <out dir> FILE1.A80 [FILE2.A80 ...]

All the files named on the command line are one program (one label space). What is translated:

* labels have 6 significant characters in ASM80: every reference is rewritten to the spelling of the definition;
* `$` inside names (PUSH$, GAM$) becomes `_`; names that are sjasmplus keywords get `_` appended;
* expressions are evaluated strictly left to right in GENS (no precedence, no brackets): brackets are added;
  `?` -> mod, `&` -> and, `!` -> or, `@` -> xor;
* MAC/ENDM with =0, =1 ... -> MACRO name p0,p1 / ENDM;
* DEFM with Cyrillic -> DEFB byte list (CP866 codes) with the text in a comment; DEFR n (random fill) -> DEFS n;
* `*F name` -> INCLUDE, `*B name` -> INCBIN (path mapped by the table BINMAP), `*Pn` -> MMU 3,n,
  DISP/ENDD -> DISP/ENT, ENT -> comment, other `*` switches -> comment.
"""
import os
import re
import sys

REG = set('A B C D E H L I R AF BC DE HL SP IX IY NZ Z NC PO PE P M'.split())
SJ_RESERVED = set('HIGH LOW NOT MOD AND OR XOR SHL SHR ABS END ORG ALIGN DEFINE MODULE PAGE SLOT SIZE DUP REPT EDUP '
                  'MACRO ENDM IF ELSE ENDIF OUTPUT DISPLAY ASSERT DEVICE INCLUDE INCBIN DISP ENT PHASE DEPHASE '
                  'DEFL EQU DS DB DW DM DZ DD DC BYTE WORD BLOCK MMU EXPORT STRUCT ENDS LUA ENDLUA DEFARRAY '
                  'UNDEFINE IFDEF IFNDEF WHILE ENDW OPT TEXTAREA UNPHASE ENDT ENDMODULE LABELSLIST SAVEBIN '
                  'SAVESNA'.split())
MNEM = set('ADC ADD AND BIT CALL CCF CP CPD CPDR CPI CPIR CPL DAA DEC DI DJNZ EI EX EXX HALT IM IN INC IND INDR INI '
           'INIR JP JR LD LDD LDDR LDI LDIR NEG NOP OR OTDR OTIR OUT OUTD OUTI POP PUSH RES RET RETI RETN RL RLA RLC '
           'RLCA RLD RR RRA RRC RRCA RRD RST SBC SCF SET SLA SRA SRL SLL SUB XOR'.split())
DIRECT = set('DEFB DEFW DEFM DEFS DEFR EQU ORG ENT DISP ENDD MAC ENDM'.split())
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_$]*')


def split_comment(line):
    q = False
    for i, ch in enumerate(line):
        if ch == '"':
            q = not q
        elif ch == ';' and not q:
            return line[:i], line[i:]
    return line, ''


def sj_name(name):
    n = name.replace('$', '_')
    if n.upper() in SJ_RESERVED or n.upper() in MNEM or n.upper() in REG:
        n += '_'
    return n


class Program:
    def __init__(self, srcdir, files, binmap=None, incname=None):
        self.srcdir = srcdir
        self.files = files
        self.binmap = binmap or (lambda p: p)
        self.incname = incname or (lambda n: n.lower() + '.asm')
        self.text = {f: open(os.path.join(srcdir, f), 'rb').read().decode('cp866').replace('\x1a', '').splitlines()
                     for f in files}
        self.defs = {}          # 6-char key -> full spelling of the definition
        self.macros = {}        # macro name -> number of parameters
        self.warn = []
        self.collect()

    def collect(self):
        for f, lines in self.text.items():
            mac = None
            for ln in lines:
                code, _ = split_comment(ln)
                if not code.strip() or code[0] == '*':
                    continue
                if mac:
                    for m in re.finditer(r'=(\d)', code):
                        self.macros[mac] = max(self.macros[mac], int(m.group(1)) + 1)
                    if re.match(r'\s+ENDM\b', code):
                        mac = None
                    continue
                if code[0] not in ' \t':
                    name = re.match(r'\S+', code).group(0)
                    rest = code[len(name):].split()
                    if rest and rest[0] == 'MAC':
                        mac = name
                        self.macros.setdefault(name, 0)
                        continue
                    key = name[:6]
                    if key in self.defs and self.defs[key] != name:
                        self.warn.append(f'{f}: labels {self.defs[key]} and {name} are the same for ASM80')
                    self.defs.setdefault(key, name)

    # ---- expressions
    def ident(self, name):
        if name in self.macros:
            return sj_name(name)
        if name.upper() in REG and name[:6] not in self.defs:
            return name
        full = self.defs.get(name[:6])
        if full is None:
            if name.upper() not in REG and name != "AF'":
                self.warn.append(f'undefined label {name}')
            return sj_name(name)
        return sj_name(full)

    def expr(self, e):
        """One flat GENS expression -> sjasmplus expression with explicit left-to-right brackets."""
        toks = re.findall(r'"[^"]*"|#[0-9A-Fa-f]+|%[01]+|\d+|[A-Za-z_][A-Za-z0-9_$]*\'?|\$|[-+*/?&!@]|\S', e)
        out = []
        for t in toks:
            if IDENT.fullmatch(t.rstrip("'")):
                out.append(t if t == "AF'" else self.ident(t))
            else:
                out.append(t)
        ops = [t for i, t in enumerate(out) if t in '+-*/?&!@' and len(t) == 1 and i > 0]
        opmap = {'?': ' mod ', '&': ' and ', '!': ' or ', '@': ' xor '}
        if not any(o in '*/?&!@' for o in ops) or len(ops) < 2:
            return ''.join(opmap.get(t, t) if (len(t) == 1 and i > 0) else t for i, t in enumerate(out))
        # left to right
        res = ''
        i = 0
        cur = ''
        if out and out[0] in ('-', '+'):
            cur = out[0]
            i = 1
        cur += out[i]
        i += 1
        first = True
        while i < len(out):
            op, term = out[i], out[i + 1] if i + 1 < len(out) else ''
            if not first:
                cur = '(' + cur + ')'
            cur = cur + opmap.get(op, op) + term
            first = False
            i += 2
        return cur

    def operand(self, o):
        o = o.strip()
        if o.startswith('"') and o.endswith('"') and o.count('"') == 2:
            return o
        if o.startswith('(') and o.endswith(')'):
            return '(' + self.expr(o[1:-1]) + ')'
        return self.expr(o)

    def operands(self, s):
        parts, cur, q, depth = [], '', False, 0
        for ch in s:
            if ch == '"':
                q = not q
            if ch == ',' and not q:
                parts.append(cur)
                cur = ''
            else:
                cur += ch
        parts.append(cur)
        return ','.join(self.operand(p) for p in parts)

    @staticmethod
    def take_operands(rest):
        """Operand field: tokens separated by blanks belong together only while joined by an operator or comma."""
        rest = rest.strip()
        if not rest:
            return '', ''
        out, i, q = '', 0, False
        n = len(rest)
        while i < n:
            ch = rest[i]
            if ch == '"':
                q = not q
            if ch in ' \t' and not q:
                j = i
                while j < n and rest[j] in ' \t':
                    j += 1
                if j >= n:
                    break
                prev, nxt = out[-1:], rest[j]
                if prev in ',+-*/?&!@' or nxt in ',+-*/?&!@':
                    i = j
                    continue
                return out, rest[j:]
            out += ch
            i += 1
        return out, ''

    def defm(self, arg, comment):
        m = re.fullmatch(r'\s*"(.*)"\s*', arg)
        if not m:
            return None
        s = m.group(1)
        if all(32 <= ord(c) < 127 for c in s) and '"' not in s:
            return f'\tDEFM\t"{s}"'
        data = s.encode('cp866')
        return '\tDEFB\t' + ','.join(f'#{b:02X}' for b in data) + f'\t; "{s}"'

    def convert_file(self, f):
        out = []
        mac = None
        for ln in self.text[f]:
            ln = ln.rstrip()
            code, com = split_comment(ln)
            if not code.strip():
                out.append(com)
                continue
            if code[0] == '*':
                out.extend(self.star(code, com))
                continue
            label = ''
            if code[0] not in ' \t':
                label = re.match(r'\S+', code).group(0)
                code = code[len(label):]
            parts = code.split(None, 1)
            op = parts[0] if parts else ''
            rest = parts[1] if len(parts) > 1 else ''
            opu = op.upper()
            tail = (' ' + com) if com else ''
            if opu == 'MAC':
                mac = label
                n = self.macros[label]
                out.append(f'\tMACRO\t{sj_name(label)} ' + ','.join(f'p{i}' for i in range(n)) + tail)
                continue
            lab = self.ident(label) if label else ''
            if not op:
                out.append(lab + tail)
                continue
            args, extra = self.take_operands(rest)
            if extra:
                tail = ' ; ' + extra + (' ' + com if com else '')
            if mac:
                args = re.sub(r'=(\d)', r'p\1', args)
            if opu == 'ENDM':
                mac = None
                out.append('\tENDM' + tail)
            elif opu == 'DEFM':
                r = self.defm(rest if '"' in rest else args, com)
                if r is None:
                    self.warn.append(f'{f}: odd DEFM: {ln}')
                    r = '\tDEFM\t' + args
                rr = split_comment(rest)[0]
                out.append(lab + r + (' ' + com if com else ''))
            elif opu == 'DEFR':
                a = self.operands(args).split(',')[0]
                out.append(f'{lab}\tDEFS\t{a}\t; 1996: DEFR (random bytes)' + tail)
            elif opu == 'ENT':
                out.append(f'{lab}\t; ENT {args}' + tail)
            elif opu == 'ENDD':
                out.append(f'{lab}\tENT' + tail)
            elif op in self.macros and op.upper() not in MNEM:
                out.append(f'{lab}\t{sj_name(op)}' + (' ' + self.operands(args) if args else '') + tail)
            elif opu in MNEM or opu in DIRECT:
                if opu == 'EX' and args.replace(' ', '').upper() == 'AF,AF':
                    args = "AF,AF'"
                a = self.operands(args) if args else ''
                out.append(f'{lab}\t{opu}' + ('\t' + a if a else '') + tail)
            else:
                self.warn.append(f'{f}: unknown operation: {ln}')
                out.append(ln)
        return out

    def star(self, code, com):
        m = re.match(r'\*([A-Za-z$]\w*)\s*(\S*)(.*)', code)
        key, arg, rest = m.group(1), m.group(2), m.group(3).strip()
        ku = key.upper()
        tail = ('\t; ' + rest if rest else '') + (' ' + com if com else '')
        if ku == 'F':
            return [f'\tINCLUDE "{self.incname(os.path.splitext(arg)[0].upper())}"' + tail]
        if ku == 'B':
            return [f'\tINCBIN "{self.binmap(arg)}"' + tail]
        if re.fullmatch(r'P\d', ku):
            return [f'\tMMU 3,{ku[1]}\t; page {ku[1]} at #C000' + ('  ' + arg + ' ' + rest if arg else '') + (' ' + com if com else '')]
        return ['; ' + code.strip() + (' ' + com if com else '')]

    def run(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        for f in self.files:
            lines = self.convert_file(f)
            path = os.path.join(outdir, self.incname(os.path.splitext(f)[0].upper()))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as h:
                h.write('\n'.join(lines) + '\n')
        return self.warn


if __name__ == '__main__':
    p = Program(sys.argv[1], sys.argv[3:])
    for w in dict.fromkeys(p.run(sys.argv[2])):
        print('warning:', w)
