#!/usr/bin/env python3
"""Host simulation of the WSPR beacon in usdx.ino (WSPR_BEACON).

Extracts the encoder and beacon code from usdx.ino, compiles it for the PC
with a simulated millis() clock and stand-ins for the LCD, Si5351 and
switch_rxtx(), and checks: start 1 s after the sync press, 110.592 s on air,
the 10-minute interval, every tone value and its timing, stop on a button
press, and refusal of a bad callsign.

Usage:  python3 test/wspr_beacon_sim.py [path/to/usdx.ino]
Needs:  g++ (or c++) on the PATH.
"""
import os, re, subprocess, sys, tempfile

HARNESS = r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <vector>
#define PROGMEM
#define pgm_read_byte(p) (*(const uint8_t*)(p))
#define F_MCU 20000000UL
#define F(s) s
typedef const char __FlashStringHelper;
enum { LSB, USB, CW };
static uint32_t now = 0;               // simulated millis()
uint32_t millis(){ return now; }
static int stop_at = -1;               // simulated button press at this time
static int btn(){ return stop_at >= 0 && (int)now >= stop_at; }
void wdt_reset(){ now++; }
#define BUTTONS 17
#define DIT 13
uint8_t inv = 0;
int digitalRead(int p){ if(p == BUTTONS) return btn(); return 1; }
struct { void noCursor(){} void setCursor(int,int){} void print(const char*){} void print(long){} void print(int){} void print(unsigned){} void print(char){} } lcd;
void lcd_blanks(){}
void show_banner(){}
void stepsize_showcursor(){}
volatile uint8_t menumode = 0, mode = USB, change = 0;
uint32_t cw_offset = 600; uint8_t rx_ph_q = 90;
struct Ev { char k; uint32_t t; long v; };
std::vector<Ev> ev;
void switch_rxtx(uint8_t on){ ev.push_back({'K', now, on}); }
struct { void freq(long f, int, int){ ev.push_back({'F', now, f}); }
         long last; void freq_calc_fine(long d){ last = d; }
         void SendPLLRegisterBulk(){ ev.push_back({'T', now, last}); } } si5351;
'''

MAIN = r'''
int main(){
  strcpy(wspr_call, "N0ASL"); strcpy(wspr_grid, "EN34"); wspr_pwr = 5; wspr_every = 3;   // 10 min
  wspr_on = 1; wspr_poll();
  printf("state after switching on: %d\n", wspr_state);
  now = 500000; wspr_press = now; wspr_sync();
  uint32_t t_sync = now;
  for(int i = 0; i < 1600000; i++){ wspr_poll(); now++; }    // ~21 min of loop time
  // analyse
  std::vector<uint32_t> keyon, keyoff; std::vector<Ev> tones;
  for(auto &e: ev){ if(e.k=='K'){ (e.v? keyon: keyoff).push_back(e.t); } if(e.k=='T') tones.push_back(e); }
  printf("transmissions: %zu\n", keyon.size());
  for(size_t i = 0; i < keyon.size(); i++)
    printf(" TX %zu: key-down %.3f s after sync, key-up after %.3f s on air\n", i, (keyon[i]-t_sync)/1250.0, (keyoff[i]-keyon[i])/1250.0);
  // tone timing and values for the first transmission
  int bad = 0; double maxerr = 0;
  for(int k = 0; k < 162; k++){
    double t = (tones[k].t - keyon[0]) / 1250.0, want = k * 8192.0/12000;
    if(t - want > maxerr) maxerr = t - want; if(t < want - 0.001) bad++;
    long expect = -600L*256 + wspr_symbol(k)*375; if(tones[k].v != expect) bad++;
  }
  printf("tone writes per TX: %zu, first-TX symbol timing late by at most %.4f s, errors %d\n", tones.size()/keyon.size(), maxerr, bad);
  // abort test
  ev.clear(); now = 5000000; wspr_on = 1; wspr_state = 0; wspr_poll(); wspr_press = now; wspr_sync(); stop_at = now + 1250*30;
  for(int i = 0; i < 300000 && wspr_state; i++){ wspr_poll(); now++; }
  int on=0, off=0; for(auto &e: ev) if(e.k=='K') (e.v? on: off)++;
  printf("abort 30 s into TX: state %d, key-down %d, key-up %d\n", wspr_state, on, off);
  // bad inputs
  stop_at = -1; strcpy(wspr_call, "ABCDEF"); wspr_on = 1; wspr_state = 0; wspr_poll(); printf("bad call -> on %d state %d\n", wspr_on, wspr_state);
  return 0;
}
'''


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "usdx.ino")
    src = open(ino).read()
    enc = re.search(r"// --- WSPR_ENCODER_BEGIN.*?// --- WSPR_ENCODER_END ---", src, re.S).group(0)
    tail = re.search(r"\n// Beacon\. Time base.*?#endif //WSPR_BEACON", src, re.S).group(0)
    tail = tail.replace("#endif //WSPR_BEACON", "")
    d = tempfile.mkdtemp()
    c, exe = os.path.join(d, "sim.cpp"), os.path.join(d, "sim")
    open(c, "w").write(HARNESS + enc + tail + MAIN)
    subprocess.check_call(["c++", "-O1", "-w", "-o", exe, c])
    out = subprocess.run([exe], capture_output=True, text=True, check=True).stdout
    print(out, end="")
    want = ["state after switching on: 1", "transmissions: 3",
            "TX 0: key-down 1.000 s after sync, key-up after 110.592 s on air",
            "TX 1: key-down 601.000 s after sync, key-up after 110.592 s on air",
            "TX 2: key-down 1201.000 s after sync, key-up after 110.592 s on air",
            "tone writes per TX: 162, first-TX symbol timing late by at most 0.0000 s, errors 0",
            "abort 30 s into TX: state 0, key-down 1, key-up 1", "bad call -> on 0 state 0"]
    missing = [w for w in want if w not in out]
    for w in missing:
        print("FAIL: expected:", w)
    print("PASS" if not missing else "FAILED")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
