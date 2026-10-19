#!/usr/bin/env python3
"""Host test for the WSPR encoder in usdx.ino.

Extracts the block between "WSPR_ENCODER_BEGIN" and "WSPR_ENCODER_END" from
usdx.ino, compiles it for the PC with small shims for the AVR-only names, and
compares its 162 channel symbols with a reference encoder written in Python.

The reference is the encoder from N0ASL's KH1/Pico project (wspr_tx.py), which
was checked symbol for symbol against WSJT-X's reference encoder on 300 random
messages.

Usage:  python3 test/wspr_encoder_test.py [path/to/usdx.ino] [count]
Needs:  g++ (or c++) on the PATH.
"""
import os
import random
import re
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------- reference
PR3 = (1,1,0,0,0,0,0,0,1,0,0,0,1,1,1,0,0,0,1,0,0,1,0,1,1,1,1,0,0,0,0,0,0,0,1,0,
       0,1,0,1,0,0,0,0,0,0,1,0,1,1,0,0,1,1,0,1,0,0,0,1,1,0,1,0,0,0,0,1,1,0,1,0,
       1,0,1,0,1,0,0,1,0,0,1,0,1,1,0,0,0,1,1,0,1,0,1,0,0,0,1,0,0,0,0,0,1,0,0,1,
       0,0,1,1,1,0,1,1,0,0,1,1,0,1,0,0,0,1,1,1,0,0,0,0,0,1,0,1,0,0,1,1,0,0,0,0,
       0,0,0,1,1,0,1,0,1,1,0,0,0,1,1,0,0,0)


def _par(x):
    x ^= x >> 16; x ^= x >> 8; x ^= x >> 4; x ^= x >> 2; x ^= x >> 1
    return x & 1


def _cc(ch):
    if "0" <= ch <= "9":
        return ord(ch) - 48
    if ch == " ":
        return 36
    if "A" <= ch <= "Z":
        return ord(ch) - 55
    raise ValueError("bad character")


def pack_call(call):
    if not 3 <= len(call) <= 6:
        raise ValueError("length")
    if call[2].isdigit():
        c6 = call
    elif call[1].isdigit():
        c6 = " " + call
    else:
        raise ValueError("no digit")
    if len(c6) > 6:
        raise ValueError("too long after padding")
    c6 = (c6 + "      ")[:6]
    c = [_cc(ch) for ch in c6]
    if c[2] > 9 or c[3] < 10 or c[4] < 10 or c[5] < 10:
        raise ValueError("form")
    n = c[0]
    n = n * 36 + c[1]
    n = n * 10 + c[2]
    n = n * 27 + c[3] - 10
    n = n * 27 + c[4] - 10
    n = n * 27 + c[5] - 10
    return n


def pack_grid(g, dbm):
    m = (179 - 10 * (ord(g[0]) - 65) - int(g[2])) * 180 + 10 * (ord(g[1]) - 65) + int(g[3])
    return m * 128 + dbm + 64


def ref_symbols(call, grid, dbm):
    v = (pack_call(call) << 22) | pack_grid(grid, dbm)
    bits = [(v >> (49 - i)) & 1 for i in range(50)] + [0] * 31
    st, enc = 0, []
    for b in bits:
        st = ((st << 1) | b) & 0xFFFFFFFF
        enc.append(_par(st & 0xF2D05351))
        enc.append(_par(st & 0xE4613C47))
    out = [0] * 162
    p = 0
    for i in range(256):
        j = int("{:08b}".format(i)[::-1], 2)
        if j < 162:
            out[j] = enc[p]
            p += 1
    return [2 * out[i] + PR3[i] for i in range(162)]


# ---------------------------------------------------------------- device code
SHIM = r"""
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#define PROGMEM
#define pgm_read_byte(p) (*(const uint8_t *)(p))
%s
int main(){
  char call[16], grid[16]; int dbm;
  while(scanf("%%15s %%15s %%d", call, grid, &dbm) == 3){
    if(call[0] == '_') call[0] = 0;
    for(char* q = call; *q; q++) if(*q == '.') *q = ' ';  // '.' stands for a blank inside the call
    uint8_t r = wspr_encode(call, grid, (uint8_t)dbm);
    if(r){ printf("E%%d\n", r); continue; }
    for(uint8_t k = 0; k != 162; k++) putchar('0' + wspr_symbol(k));
    putchar('\n');
  }
  return 0;
}
"""


def build(ino):
    src = open(ino).read()
    m = re.search(r"//[^\n]*WSPR_ENCODER_BEGIN.*?\n(.*?)//[^\n]*WSPR_ENCODER_END", src, re.S)
    if not m:
        sys.exit("encoder block not found in " + ino)
    d = tempfile.mkdtemp()
    c = os.path.join(d, "enc.cpp")
    exe = os.path.join(d, "enc")
    open(c, "w").write(SHIM % m.group(1))
    subprocess.check_call(["c++", "-O1", "-Wall", "-o", exe, c])
    return exe


def random_call(rnd):
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    D = "0123456789"
    form = rnd.choice(["LDLLL", "LLDLLL", "LDL", "LDLL", "LLDL", "LLDLL", "DLDLL", "LDDLL", "DDDLLL"])
    s = "".join(rnd.choice(L if f == "L" else D) for f in form)
    return s


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "usdx.ino")
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    exe = build(ino)
    rnd = random.Random(1)
    cases = [("K1ABC", "FN42", 37), ("N0ASL", "EN34", 37), ("G4ABC", "IO91", 23), ("W1AW", "FN31", 30),
             ("AA1A", "AA00", 0), ("ZZ9ZZZ", "RR99", 60), ("PE1NNZ", "JO22", 33)]
    powers = [p for p in range(0, 61) if p % 10 in (0, 3, 7)]
    while len(cases) < count:
        g = rnd.choice("ABCDEFGHIJKLMNOPQR") + rnd.choice("ABCDEFGHIJKLMNOPQR") + rnd.choice("0123456789") + rnd.choice("0123456789")
        cases.append((random_call(rnd), g, rnd.choice(powers)))
    # Invalid inputs the device must reject (1 = callsign, 2 = grid)
    bad = [("K1", "FN42", 37, 1), ("ABCDEF", "FN42", 37, 1), ("K1ABCDE", "FN42", 37, 1), ("KK1ABCD", "FN42", 37, 1),
           ("K1A2C", "FN42", 37, 1), ("K1ABC", "SN42", 37, 2), ("K1ABC", "FNA2", 37, 2), ("K1ABC", "FN4", 37, 2),
           ("K1-BC", "FN42", 37, 1), ("_", "FN42", 37, 1), ("N0A.SL", "EN34", 37, 1), (".N0ASL", "EN34", 37, 1)]
    inp = "".join("%s %s %d\n" % c for c in cases) + "".join("%s %s %d\n" % b[:3] for b in bad)
    out = subprocess.run([exe], input=inp, capture_output=True, text=True, check=True).stdout.split("\n")
    fails = 0
    for (call, grid, dbm), line in zip(cases, out):
        try:
            want = "".join(str(s) for s in ref_symbols(call, grid, dbm))
        except ValueError:
            want = "E1"
        if line != want:
            fails += 1
            if fails < 5:
                print("MISMATCH", call, grid, dbm, "\n device:", line, "\n ref:   ", want)
    for b, line in zip(bad, out[len(cases):]):
        if line != "E%d" % b[3]:
            fails += 1
            print("NOT REJECTED", b, "->", line[:20])
    ok = len(cases) + len(bad) - fails
    print("%d of %d cases agree with the reference" % (ok, len(cases) + len(bad)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
