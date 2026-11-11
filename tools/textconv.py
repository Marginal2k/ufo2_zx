#!/usr/bin/env python3
"""Texts of UFO-2: a port of WORDER.CPP (words, names, menus, encyclopedia, ending) and XINSTR.CPP (the manual).

Texts are stored as codes of the game font (table CODE), lines end with 126/127, and the 128 most frequent
pairs of characters are replaced by one byte 128..255 (the pair table goes to xcompres.dat, 256 bytes).
Input files are UTF-8 with CR LF or LF line ends (the originals were CP866 with CR LF).
"""

CODE = ('0123456789?-.,: '
        'АБВГДЕЁЖЗИЙКЛМНО'
        'ПРСТУФХЦЧШЩЬЫЭЮЯ'
        'абвгдеёжзийклмно'
        'прстуфхцчшщьыэюя'
        'DFGIJLNQRSUVWYZ!'
        '()_/%>"$ФФФФФФФФ'
        'ъ^\'')
CODE_INSTR = (' яазвсьедцрфжтгб'
              'ыхнуймиколпЧэЭюШ'
              'ёЯАЗВЕСДЬЦЖФРТГБ'
              'ХЫУЙНМКИОЛПъшщчЩ'
              'ZЮVNSDFGJLWQRYUI'
              '2513460987,.:;-/'
              ')(!$%"+?Ё#+++++')


def load(path):
    """Text file -> the bytes the 1996 tools saw (CP866, CR LF)."""
    t = open(path, encoding='utf-8').read().replace('\r\n', '\n').replace('\n', '\r\n')
    return bytearray(t.encode('cp866'))


def _code(table, c, what):
    j = table.find(bytes([c]))
    if j < 0:
        raise ValueError(f'character {bytes([c]).decode("cp866")!r} ({c}) cannot be used in {what}')
    return j


def convert_word(m):
    tab = CODE.encode('cp866')
    out = bytearray()
    i = 0
    while i < len(m):
        c = m[i]
        if c == 13:
            out.append(126)
            i += 1
        else:
            out.append(_code(tab, 32 if c == ord('#') else c, 'the dictionary'))
        i += 1
    return out


def convert_menu(m):
    tab = CODE.encode('cp866')
    out = bytearray()
    i = 0
    while i < len(m):
        c = m[i]
        if c == 13:
            out.append(127)
            i += 1
        elif c == 0xFD:          # the currency sign in CP866: end of a line inside a menu
            out.append(126)
        else:
            out.append(_code(tab, c, 'menus'))
        i += 1
    return out


def convert_ufopedia(m):
    tab = CODE.encode('cp866')
    m = bytearray(m) + b'\0\0\0'
    n = len(m) - 3
    m[0] = m[1] = 32
    out = bytearray()
    i = 0
    while i < n:
        c = m[i]
        if c == 13:
            out.append(127)
            i += 1
            if 48 <= m[i + 1] < 128:        # the two-digit number of the next article
                m[i + 1] = m[i + 2] = 32
        elif c == ord('&'):
            pass
        elif c == ord('#'):
            out.append(126)
        else:
            out.append(_code(tab, c, 'the encyclopedia'))
        i += 1
    return out


def formatter(m):
    """Word wrap of the encyclopedia at 27 columns (as in WORDER.CPP, including its quirks)."""
    mx = k = maxi = 0
    for i in range(len(m)):
        c = m[i]
        if c in (126, 127, 15):
            if c != 15:
                mx = k
            if k > 27:
                if m[maxi] < 126:
                    m[maxi] = 126
                mx = k = k - mx
                maxi = i
            elif c < 126:
                mx = k
                k += 1
                maxi = i
            else:
                maxi = i
                mx = 0
                k = 0
        else:
            k += 1


class Pairs:
    def __init__(self, lo, hi):
        self.lo, self.hi = lo, hi
        self.n = hi - lo
        self.data = [[0] * self.n for _ in range(self.n)]
        self.cmpr = bytearray(256)

    def search(self, m):
        lo, hi = self.lo, self.hi
        for i in range(len(m) - 1):
            a, b = m[i], m[i + 1]
            if lo <= a < hi and lo <= b < hi:
                self.data[a - lo][b - lo] += 1

    def ini(self):
        d = self.data
        for k in range(128):
            mx = mi = mj = 0
            for i in range(self.n):
                row = d[i]
                rm = max(row)
                if rm > mx:
                    mx, mi, mj = rm, i, row.index(rm)
            self.cmpr[k * 2] = mi + self.lo
            self.cmpr[k * 2 + 1] = mj + self.lo
            d[mi][mj] = -(k + 1)
        for i in range(self.n):
            d[i] = [0 if v > 0 else -v for v in d[i]]

    def compress(self, m):
        lo, hi = self.lo, self.hi
        out = bytearray()
        i = 0
        n = len(m)
        while i < n:
            a = m[i]
            b = m[i + 1] if i + 1 < n else 255
            if lo <= a < hi and lo <= b < hi and self.data[a - lo][b - lo] > 0:
                out.append(self.data[a - lo][b - lo] + 127)
                i += 1
            else:
                out.append(a)
            i += 1
        return out


def worder(word, name, menu, pedia, end):
    """Five text files (bytes, CP866) -> dict of .dat files."""
    mw, mn, me = convert_word(word), convert_word(name), convert_word(end)
    mm = convert_menu(menu)
    mp = convert_ufopedia(pedia)
    formatter(mp)
    p = Pairs(15, 80)
    for t in (mw, mn, mm, mp):
        p.search(t)
    p.ini()
    return {'xword.dat': bytes(p.compress(mw)), 'xname.dat': bytes(p.compress(mn)),
            'xfopedia.dat': bytes(p.compress(mp)), 'xmenu.dat': bytes(p.compress(mm)),
            'xend.dat': bytes(me), 'xcompres.dat': bytes(p.cmpr), 'x256.dat': bytes(range(256))}


def instr(text):
    """The manual: xinstr.txt -> (xinstr.dat, xinstrcm.dat)."""
    tab = CODE_INSTR.encode('cp866')
    m = bytearray(text)
    out = bytearray()
    i = 0
    n = len(m)
    while i < n:
        if m[i] == ord('*'):
            m[i] = 32
        if m[i] == 32 and i + 1 < n and m[i + 1] == 13:
            i += 1
        c = m[i]
        if c == 13:
            out.append(126)
            i += 1
        elif c == ord('='):
            out.append(127)
        else:
            out.append(_code(tab, c, 'the manual'))
        i += 1
    p = Pairs(0, 100)
    p.search(out)
    p.ini()
    return bytes(p.compress(out)), bytes(p.cmpr)
