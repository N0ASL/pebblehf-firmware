#!/usr/bin/env python3
"""Host simulation of the WSPR beacon in usdx.ino (WSPR_BEACON).

Extracts the encoder and beacon code from usdx.ino, compiles it for the PC
with a simulated millis() clock and stand-ins for the LCD, Si5351 and
switch_rxtx(), and checks: start 1 s after the sync press, 110.592 s on air,
the slot choice (TX %, never back to back), every tone value and its timing, stop on a button
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
#include <string>
struct Lcd { char scr[2][17]; int r = 0, c = 0;
  Lcd(){ memset(scr, ' ', sizeof(scr)); scr[0][16] = scr[1][16] = 0; }
  void noCursor(){}
  void setCursor(int cc, int rr){ c = cc; r = rr; }
  void put(char ch){ if(c < 16) scr[r][c] = ch; c++; }
  void print(const char* t){ for(; *t; t++) put(*t); }
  void print(long v){ print(std::to_string(v).c_str()); }
  void print(int v){ print((long)v); } void print(unsigned v){ print((long)v); } void print(unsigned long v){ print((long)v); }
  void print(char ch){ put(ch); } } lcd;
void lcd_blanks(){ lcd.print("        "); }
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
  strcpy(wspr_call, "N0ASL"); strcpy(wspr_grid, "EN34"); wspr_pwr = 5; wspr_pct = 5;   // 50%: every other slot
  wspr_on = 1; wspr_poll();
  printf("state after switching on: %d\n", wspr_state);
  lcd.scr[1][15] = 'T';   // the radio's T/R indicator must survive every redraw of line 2
  wspr_line2(); printf("line 2, 5-character call: '%s'\n", lcd.scr[1]);
  strcpy(wspr_call, "N0ASLX"); wspr_line2(); printf("line 2, 6-character call: '%s'\n", lcd.scr[1]);
  strcpy(wspr_call, "K1A"); wspr_line2(); printf("line 2, 3-character call: '%s'\n", lcd.scr[1]);
  strcpy(wspr_call, "N0ASL"); lcd.scr[1][15] = ' ';
  now = 500000; wspr_press = now; wspr_sync();
  uint32_t t_sync = now;
  int samples = 0, badshow = 0, first_bad = 0;
  for(int i = 0; i < 1600000; i++){
    wspr_poll(); now++;
    if((i % 6250) == 0 && wspr_state == 2 && (int32_t)(wspr_next - now) > 1250){  // every 5 s of real time, between transmissions
      int m = 0, sec = 0; char *p = strstr(lcd.scr[0], "TX ");
      if(p){ p += 3; if(!strncmp(p, "in ", 3)) p += 3; if(sscanf(p, "%d:%d", &m, &sec) != 2) m = -1; } else m = -1;
      double real = (int32_t)(wspr_next - now) / 1250.0;     // real seconds left, 1250 millis() units per second
      samples++; if(m < 0 || m * 60 + sec < real - 1.5 || m * 60 + sec > real + 1.5){ badshow++; if(!first_bad){ first_bad = 1; printf("BAD SHOW: '%s' real left %.1f\n", lcd.scr[0], real); } }
    }
  }
  printf("countdown display samples: %d, wrong: %d\n", samples, badshow);
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
  // slot choice: long-run share of slots, and never two transmissions in a row
  for(int p = 0; p < 6; p++){
    wspr_pct = p; wspr_next = 0; uint32_t slots = 0, n = 200000, mingap = 99;
    for(uint32_t i = 0; i < n; i++){ uint32_t a = wspr_next; wspr_plan(); uint32_t g = (wspr_next - a) / 150000; slots += g; if(g < mingap) mingap = g; }
    printf("TX %d%%: measured %.1f%%, shortest gap %u slots\n", wspr_pctv[p], 100.0 * n / slots, mingap);
  }
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
    want = ["state after switching on: 1", "line 2, 5-character call: 'N0ASL EN34 37  T'",
            "line 2, 6-character call: 'N0ASLX EN34 37 T'", "line 2, 3-character call: 'K1A EN34 37    T'", "transmissions: 10",
            "TX 0: key-down 1.000 s after sync, key-up after 110.592 s on air",
            "TX 1: key-down 241.000 s after sync, key-up after 110.592 s on air",
            "TX 2: key-down 481.000 s after sync, key-up after 110.592 s on air",
            "countdown display samples: 253, wrong: 0",
            "tone writes per TX: 162, first-TX symbol timing late by at most 0.0000 s, errors 0",
            "abort 30 s into TX: state 0, key-down 1, key-up 1",
            "TX 5%: measured 5.0%, shortest gap 2 slots", "TX 10%: measured 10.0%, shortest gap 2 slots",
            "TX 20%: measured 20.0%, shortest gap 2 slots", "TX 25%: measured 25.0%, shortest gap 2 slots",
            "TX 33%: measured 33.3%, shortest gap 2 slots", "TX 50%: measured 50.0%, shortest gap 2 slots", "bad call -> on 0 state 0"]
    missing = [w for w in want if w not in out]
    for w in missing:
        print("FAIL: expected:", w)
    print("PASS" if not missing else "FAILED")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
