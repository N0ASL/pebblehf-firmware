#!/usr/bin/env python3
"""Host test for the frequency-preset code in usdx.ino (FREQ_PRESETS).

Extracts the block between "FREQ_PRESETS_BEGIN" and "FREQ_PRESETS_END", compiles it for the host computer with a fake EEPROM and a
16x2 LCD model, and checks: factory slots and empty slots, a stored slot, damaged slots falling back, the EEPROM area
limits, the picker screen (hint line, small a/b VFO glyph, slot text, empty slot, column 15 left alone for the T/R indicator),
and storing the active VFO's frequency and mode (all five modes, AM and FM included). Then, for the band builds (BAND_40M and
BAND_10M), the factory slots of that band and a 20m slot left in EEPROM falling back to them.

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
#define F(s) s
#define pgm_read_dword(p) (*(const uint32_t*)(p))
#define FREQ_LIMIT_LOW  14000000UL
#define FREQ_LIMIT_HIGH 14350000UL
enum { LSB, USB, CW, FM, AM };
const char* mode_label[5] = { "LSB", "USB", "CW ", "FM ", "AM " };
static uint8_t eep[1024];
uint32_t eeprom_read_dword(const uint32_t* a){ uint32_t v; memcpy(&v, eep + (uintptr_t)a, 4); return v; }
void eeprom_write_dword(uint32_t* a, uint32_t v){ memcpy(eep + (uintptr_t)a, &v, 4); }
void wdt_reset(){}
void delay(int){}
volatile int32_t freq = 14000000; volatile uint8_t mode = USB, vfosel = 0;
struct Lcd { char scr[2][17]; int r = 0, c = 0;
  Lcd(){ memset(scr, ' ', sizeof(scr)); scr[0][16] = scr[1][16] = 0; }
  void noCursor(){}
  void setCursor(int cc, int rr){ c = cc; r = rr; }
  void put(char ch){ if(ch == 6) ch = 'a'; if(ch == 7) ch = 'b'; if(c < 16) scr[r][c] = ch; c++; }  // custom glyphs 6/7: small a/b
  void print(const char* t){ for(; *t; t++) put(*t); }
  void print(char ch){ put(ch); }
  void print(unsigned long v){ print(std::to_string(v).c_str()); } void print(unsigned int v){ print((unsigned long)v); }
  void print(int v){ print(std::to_string(v).c_str()); } void print(long v){ print(std::to_string(v).c_str()); } } lcd;
%s
static std::string show(uint32_t v){ lcd.r = 0; lcd.c = 0; memset(lcd.scr, ' ', sizeof(lcd.scr)); lcd.scr[0][16] = lcd.scr[1][16] = 0; preset_print(v); std::string o(lcd.scr[0]); while(!o.empty() && o.back() == ' ') o.pop_back(); return o; }
static void mark(){ lcd.scr[1][15] = 'T'; }   // the radio's T/R indicator
int main(){
  int bad = 0;
  #define CHECK(c, msg) do{ if(!(c)){ bad++; printf("FAIL: %%s\n", msg); } }while(0)
  memset(eep, 0xFF, sizeof(eep));
  CHECK(preset_get(0) == (14030000UL | ((uint32_t)CW << 24)), "erased slot 1 is 14.030 CW");
  CHECK(preset_get(4) == (14285000UL | ((uint32_t)USB << 24)), "erased slot 5 is 14.285 USB");
  CHECK(preset_get(5) == 0 && preset_get(7) == 0, "erased slots 6-8 are empty");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)USB << 24));
  CHECK(preset_get(2) == (14123400UL | ((uint32_t)USB << 24)), "stored slot 3 is returned");
  CHECK(preset_get(1) == (14060000UL | ((uint32_t)CW << 24)), "neighbour slot unchanged");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 7030000UL | ((uint32_t)CW << 24));
  CHECK(preset_get(2) == (14100000UL | ((uint32_t)CW << 24)), "out-of-band slot falls back to the default");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)AM << 24));
  CHECK(preset_get(2) == (14123400UL | ((uint32_t)AM << 24)), "AM slot is returned");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)FM << 24));
  CHECK(preset_get(2) == (14123400UL | ((uint32_t)FM << 24)), "FM slot is returned");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 2), 14123400UL | ((uint32_t)(AM + 1) << 24));
  CHECK(preset_get(2) == (14100000UL | ((uint32_t)CW << 24)), "bad mode falls back to the default");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 6), 7030000UL | ((uint32_t)CW << 24));
  CHECK(preset_get(6) == 0, "damaged empty slot stays empty");
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 3), 14350000UL | ((uint32_t)USB << 24));
  CHECK(preset_get(3) == (14350000UL | ((uint32_t)USB << 24)), "band edge 14.350 accepted");
  CHECK(PRESET_EEPROM + 4 * N_PRESET <= 0x3F0, "preset area ends before the WSPR area at 0x3F0");
  memset(eep, 0xFF, sizeof(eep));
  printf("%%s\n", show(14030000UL | ((uint32_t)CW << 24)).c_str());
  printf("%%s\n", show(14285500UL | ((uint32_t)USB << 24)).c_str());
  printf("%%s\n", show(14000100UL | ((uint32_t)USB << 24)).c_str());
  printf("%%s\n", show(14000000UL | ((uint32_t)LSB << 24)).c_str());
  preset_sel = 0; vfosel = 0; mark(); preset_draw();
  printf("top '%%s'\nslot 1 VFO A '%%s'\n", lcd.scr[0], lcd.scr[1]);
  vfosel = 1; preset_sel = 5; mark(); preset_draw();
  printf("slot 6 VFO B '%%s'\n", lcd.scr[1]);
  freq = 14123400; mode = USB; mark(); preset_store();
  CHECK(preset_get(5) == (14123400UL | ((uint32_t)USB << 24)), "store: slot 6 holds the VFO's frequency and mode");
  printf("after store '%%s'\n", lcd.scr[1]);
  freq = 14286000; mode = AM; preset_sel = 6; preset_store();
  CHECK(preset_get(6) == (14286000UL | ((uint32_t)AM << 24)), "store: AM is kept (was lost before)");
  printf("after AM store '%%s'\n", lcd.scr[1]);
  printf("bad %%d\n", bad);
  return bad != 0;
}
'''

BAND_SHIM = r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#define FREQ_PRESETS 1
#define PROGMEM
#define F(s) s
#define pgm_read_dword(p) (*(const uint32_t*)(p))
enum { LSB, USB, CW, FM, AM };
const char* mode_label[5] = { "LSB", "USB", "CW ", "FM ", "AM " };
static uint8_t eep[1024];
uint32_t eeprom_read_dword(const uint32_t* a){ uint32_t v; memcpy(&v, eep + (uintptr_t)a, 4); return v; }
void eeprom_write_dword(uint32_t* a, uint32_t v){ memcpy(eep + (uintptr_t)a, &v, 4); }
void wdt_reset(){}
void delay(int){}
volatile int32_t freq = 0; volatile uint8_t mode = USB, vfosel = 0;
struct Lcd { void noCursor(){} void setCursor(int, int){} void print(const char*){} void print(char){} void print(unsigned long){}
  void print(unsigned int){} void print(int){} void print(long){} } lcd;
%s
int main(){
  memset(eep, 0xFF, sizeof(eep));
  for(int i = 0; i != N_PRESET; i++){ uint32_t v = preset_get(i); printf("slot %%d %%lu %%d\n", i + 1, (unsigned long)(v & 0xFFFFFFUL), (int)(v >> 24)); }
  eeprom_write_dword((uint32_t*)(PRESET_EEPROM + 4 * 0), 14123400UL | ((uint32_t)USB << 24));  // left over from a 20m build
  uint32_t v = preset_get(0); printf("20m leftover %%lu %%d\n", (unsigned long)(v & 0xFFFFFFUL), (int)(v >> 24));
  return 0;
}
'''

def band_check(block, band, lo, hi):
    d = tempfile.mkdtemp(); c = os.path.join(d, "b.cpp"); exe = os.path.join(d, "b")
    open(c, "w").write(BAND_SHIM % block)
    subprocess.check_call(["c++", "-O1", "-w", "-D" + band, "-DFREQ_LIMIT_LOW=%dUL" % lo, "-DFREQ_LIMIT_HIGH=%dUL" % hi, "-o", exe, c])
    return subprocess.run([exe], capture_output=True, text=True).stdout.split("\n")

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
    want = ["14.0300 CW", "14.2855 USB", "14.0001 USB", "14.0000 LSB",
            "top 'KNOB=go SEL=save'", "slot 1 VFO A 'a1 14.0300 CW  T'", "slot 6 VFO B 'b6 empty       T'",
            "after store 'b6 14.1234 USB T'", "after AM store 'b7 14.2860 AM  T'", "bad 0"]
    lines = out.split("\n")
    missing = [w for w in want if w not in lines]
    for w in missing: print("FAIL: expected line:", repr(w))
    # LSB=0 USB=1 CW=2
    bands = [("BAND_40M", 7000000, 7300000, ["slot 1 7030000 2", "slot 2 7040000 2", "slot 3 7074000 1", "slot 4 7200000 0",
                                             "slot 5 7285000 0", "slot 6 0 0", "slot 8 0 0", "20m leftover 7030000 2"]),
             ("BAND_10M", 28000000, 29700000, ["slot 1 0 0", "slot 5 0 0", "slot 8 0 0", "20m leftover 0 0"])]
    for band, lo, hi, exp in bands:
        got = band_check(m.group(1), band, lo, hi)
        miss = [w for w in exp if w not in got]
        for w in miss: print("FAIL (%s): expected line:" % band, repr(w))
        if not miss: print("%s factory slots OK" % band)
        missing += miss
    ok = r.returncode == 0 and not missing
    print("PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
