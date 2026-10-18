#!/usr/bin/env python3
"""Host test for the frequency-preset code in usdx.ino (FREQ_PRESETS).

Extracts the block between "FREQ_PRESETS_BEGIN" and "FREQ_PRESETS_END", compiles it for the PC with a fake
EEPROM and LCD, and checks: erased slots read as the defaults, a stored slot is returned as stored, damaged slots
(frequency outside 14.000-14.350 MHz, bad mode) fall back to the default, and the "14.0300 CW" display text.

Usage:  python3 test/preset_test.py [path/to/usdx.ino]
Needs:  g++ (or c++) on the PATH.
"""
import os, re, subprocess, sys, tempfile

SHIM = r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <string>
#define FREQ_PRESETS 1
#define PROGMEM
#define pgm_read_dword(p) (*(const uint32_t*)(p))
#define FREQ_LIMIT_LOW  14000000UL
#define FREQ_LIMIT_HIGH 14350000UL
enum { LSB, USB, CW, FM, AM };
const char* mode_label[5] = { "LSB", "USB", "CW ", "FM ", "AM " };
static uint8_t eep[1024];
uint32_t eeprom_read_dword(const uint32_t* a){ uint32_t v; memcpy(&v, eep + (uintptr_t)a, 4); return v; }
void eeprom_write_dword(uint32_t* a, uint32_t v){ memcpy(eep + (uintptr_t)a, &v, 4); }
struct Lcd { std::string s; void print(const char* t){ s += t; } void print(char c){ s += c; }
  void print(unsigned long v){ s += std::to_string(v); } void print(unsigned int v){ s += std::to_string(v); }
  void print(int v){ s += std::to_string(v); } void print(unsigned long long v){ s += std::to_string(v); } } lcd;
%s
static std::string show(uint32_t v){ lcd.s.clear(); preset_print(v); return lcd.s; }
int main(){
  int bad = 0;
  #define CHECK(c, msg) do{ if(!(c)){ bad++; printf("FAIL: %%s\n", msg); } }while(0)
  memset(eep, 0xFF, sizeof(eep));
  CHECK(preset_get(0) == (14030000UL | ((uint32_t)CW << 24)), "erased slot 1 is 14.030 CW");
  CHECK(preset_get(4) == (14285000UL | ((uint32_t)USB << 24)), "erased slot 5 is 14.285 USB");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)USB << 24));
  CHECK(preset_get(2) == (14123400UL | ((uint32_t)USB << 24)), "stored slot 3 is returned");
  CHECK(preset_get(1) == (14060000UL | ((uint32_t)CW << 24)), "neighbour slot unchanged");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 7030000UL | ((uint32_t)CW << 24));
  CHECK(preset_get(2) == (14100000UL | ((uint32_t)CW << 24)), "out-of-band slot falls back to the default");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)AM << 24));
  CHECK(preset_get(2) == (14100000UL | ((uint32_t)CW << 24)), "bad mode falls back to the default");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 3), 14350000UL | ((uint32_t)USB << 24));
  CHECK(preset_get(3) == (14350000UL | ((uint32_t)USB << 24)), "band edge 14.350 accepted");
  CHECK(PRESET_EEPROM + 4 * N_PRESET <= 0x3F0, "preset area ends before the WSPR area at 0x3F0");
  printf("%%s\n", show(14030000UL | ((uint32_t)CW << 24)).c_str());
  printf("%%s\n", show(14285500UL | ((uint32_t)USB << 24)).c_str());
  printf("%%s\n", show(14000100UL | ((uint32_t)USB << 24)).c_str());
  printf("%%s\n", show(14000000UL | ((uint32_t)LSB << 24)).c_str());
  printf("bad %%d\n", bad);
  return bad != 0;
}
'''

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "usdx.ino")
    src = open(ino).read()
    m = re.search(r"// --- FREQ_PRESETS_BEGIN[^\n]*\n(.*?)// --- FREQ_PRESETS_END ---", src, re.S)
    if not m: sys.exit("preset block not found")
    d = tempfile.mkdtemp(); c = os.path.join(d, "p.cpp"); exe = os.path.join(d, "p")
    open(c, "w").write(SHIM % m.group(1))
    subprocess.check_call(["c++", "-O1", "-w", "-o", exe, c])
    r = subprocess.run([exe], capture_output=True, text=True)
    out = r.stdout; print(out, end="")
    want = ["14.0300 CW ", "14.2855 USB", "14.0001 USB", "14.0000 LSB", "bad 0"]
    missing = [w for w in want if w not in out.split("\n")]
    for w in missing: print("FAIL: expected line:", repr(w))
    ok = r.returncode == 0 and not missing
    print("PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
