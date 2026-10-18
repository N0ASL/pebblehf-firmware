#!/usr/bin/env python3
"""Host test of the WSPR sub-menu navigation (wspr_menu_nav) extracted from usdx.ino."""
import os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "..", "usdx.ino")).read()
blk = re.search(r"// --- MENU_NAV_BEGIN.*?// --- MENU_NAV_END ---", src, re.S).group(0)
main = r'''
#include <stdint.h>
#include <stdio.h>
#define WSPR_BEACON 1
enum { PRESETS = 40, WSPR_MENU = 50, WSPR_CALL, WSPR_GRID, WSPR_PWR, WSPR_PCT, WSPR_OFF, WSPR_MAX, WSPR_RUN, SWVER };
''' + blk + r'''
int main(){
  int bad = 0;
  #define CHK(got, want) if((got) != (want)){ printf("FAIL line %d: got %d want %d\n", __LINE__, (int)(got), (int)(want)); bad++; }
  CHK(wspr_menu_nav(WSPR_CALL, 1, 0), WSPR_RUN + 1)    // forward in main list skips the seven items
  CHK(wspr_menu_nav(WSPR_RUN, 1, 0), WSPR_RUN + 1)
  CHK(wspr_menu_nav(WSPR_RUN, -1, 0), WSPR_MENU)       // backward lands on the entry
  CHK(wspr_menu_nav(WSPR_CALL, -1, 0), WSPR_MENU)
  CHK(wspr_menu_nav(WSPR_MENU, 1, 0), WSPR_MENU)       // entry itself is left alone
  CHK(wspr_menu_nav(PRESETS, 1, 0), PRESETS)
  CHK(wspr_menu_nav(WSPR_CALL - 1, -1, 1), WSPR_RUN)   // sub list wraps both ways
  CHK(wspr_menu_nav(WSPR_RUN + 1, 1, 1), WSPR_CALL)
  CHK(wspr_menu_nav(WSPR_PWR, 1, 1), WSPR_PWR)
  printf(bad ? "FAILED\n" : "PASS\n"); return bad;
}
'''
d = tempfile.mkdtemp(); c, exe = os.path.join(d, "n.cpp"), os.path.join(d, "n")
open(c, "w").write(main)
subprocess.check_call(["c++", "-w", "-o", exe, c])
sys.exit(subprocess.run([exe]).returncode)
