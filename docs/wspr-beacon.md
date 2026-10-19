# WSPR beacon (`WSPR_BEACON`)

Status (19 Oct 2026): **decoded on the air (WSJT-X); everything in the beacon has been tried on the radio: the WSPR menu, offset, max TX, click-to-start 5.7, the call and grid check ("Bad WSPR"), the plain TX % and WSJT-X power labels, and PTT being ignored with VOX on.**

> **Heat and power.** The beacon keys the PA continuously for about 110 s per transmission, much longer than CW or FT8, and the PA has no heatsink. Keep it to short, attended tests: use a low TX %, set Max TX to a few transmissions, and let the PA cool between runs. To cut heat, lower the supply voltage (about 1 W on USB-C against about 5 W on 13.8 V). The WSPR Power setting (5.3) only changes the number sent in the message, and TX Drive (3.3) does not change the beacon's output. Use at your own risk; this firmware is provided as is under the MIT license.

A stand-alone WSPR beacon inside the Pebble HF firmware: no Pico, phone or computer attached. It sends a standard WSPR message (callsign, 4-character grid, power) on one fixed frequency in the 20 m WSPR window.

## Building

The switch is on by default, so a plain build of `usdx.ino` is the beacon. Near the top of the file:

```c
//#define DIAG           1   // off here, to make room (about 1.3 KB)
#define WSPR_BEACON      1   // Stand-alone WSPR beacon ...
```

DIAG (the startup self-test) is switched off here to make room; CAT stays off. With `WSPR_BEACON`, `FREQ_PRESETS`, `MENU_WRAP`, `TX_TIMEOUT` and `VERSION_TAG` commented out and `DIAG` back on, the build is byte-for-byte the official firmware (checked: identical hex).

| Build of 1.0.7 | Flash (of 32,256) | RAM used | RAM left for stack |
|---|---|---|---|
| Official | 26,894 | 1,022 | 1,026 |
| `WSPR_BEACON`, DIAG on | 30,718 (95%) | 1,201 | 847 |
| `WSPR_BEACON`, DIAG off | 29,402 (91%) | 1,201 | 847 |
| fork default (presets, TX timeout, WSPR menu) | 31,702 (98%) | 1,211 | 837 |

Your saved settings and calibration (Ref freq, IQ phase, PA bias, VFOs) survive flashing this build: the WSPR settings live in their own EEPROM area (0x3F0–0x3FF: WSPR 0x3F0–0x3FD, TX timeout 0x3FE) and do not shift the other settings' addresses.

## Using it

Menu entries (section 5): **5.0 WSPR Menu** ("click to open") opens a list of 5.1–5.7 that scrolls round. SELECT goes back to the main list; clicking 5.7 Beacon starts the beacon and closes the menu.


| Menu | Values | Notes |
|---|---|---|
| 5.1 WSPR Call | text, up to 6 characters | standard calls only (digit as 2nd or 3rd character, e.g. N0ASL, K1ABC, G4ABC); no /P or prefixes, no blank inside the call (trailing blanks are fine) |
| 5.2 WSPR Grid | 4 characters: two letters A–R, then two digits | e.g. EN34 |
| 5.3 WSPR Power | 20 / 23 / 27 / 30 / 33 / 37 dBm | shown as WSJT-X lists them (`20 dBm  100 mW` … `37 dBm  5 W`); the value sent in the message; the radio cannot measure its output. About 5 W (37) on 13.8 V, about 1 W (30) on USB-C |
| 5.4 WSPR TX % | 5% / 10% / 25% / 50% | share of the 2-minute slots used for transmitting, the same idea as WSJT-X's Tx Pct; default 10 %. The menu shows only the percentage because the gaps are random (see below). A saved choice from an older build is read by position, so check this setting after updating |
| 5.5 WSPR Offset | −90 … +90 Hz in 10 Hz steps, or Random | shifts the signal inside the 200 Hz WSPR window (random: new value every transmission); default 0 Hz |
| 5.6 WSPR Max TX | No limit / 1 / 2 / 3 / 5 / 10 TX | the beacon stops after that many transmissions, shows `WSPR done` and returns to the normal screen |
| 5.7 WSPR Beacon | click to start | starts the beacon and closes the menu; the beacon is always off at power-up |

Buttons are named as on the Pebble HF: **MENU** (left), **SELECT** (right), the **VFO knob** (turn and click) and the **PTT** key. Text entry uses the firmware's string editor: turn the VFO knob to change a character, click the VFO knob to move to the next character, MENU to save and return to the main screen (SELECT saves and returns to the menu list). For the call the characters are limited to space, 0–9 and A–Z, in that order, wrapping around (turning down from a blank gives Z, Y, X…). The grid only offers what a grid square can contain: letters A–R in the first two positions and digits 0–9 in the last two, each wrapping around; on the first turn the field fills with AA00 so it is always valid. The cursor stops at the last position (6th for the call, 4th for the grid).

1. Set call, grid, power and TX % once (they are saved).
2. Click **5.7 WSPR Beacon**: the menu closes. The top line shows `SEL at even min` (or `Bad WSPR` if the call or grid does not fit a standard message: check 5.1 and 5.2); the second line shows the message being sent, e.g. `N0ASL EN01 27` (power in dBm, without the unit: the last column belongs to the radio's T/R indicator, which shows `T` while transmitting and `R` while receiving), and stays that way while the beacon is on.
3. Watch the phone's clock and **click SELECT the moment an even minute starts** (e.g. 14:32:00). The moment the button goes down is used, not the end of the click.
4. The first transmission starts 1 s later, in the slot you synced on, and lasts 110.6 s (top line `WSPR TX 110s 5%`: the seconds left count down, with the TX % at the right). Between transmissions the top line counts down to the next one (`WSPR TX in 5:21`; there is no room for the TX % on that screen). The radio receives on the VFO frequency between transmissions, but the VFO knob does not tune while the beacon is on.
5. **MENU, SELECT or a VFO knob click stops the beacon**, between or during transmissions. PTT stops a transmission in progress (and the beacon), except with VOX (3.1) on: then the DIT/PTT line is ignored during a transmission, because a sound card on the jack can hold it low (see 1.0.4); between transmissions PTT keys the radio normally. To restart, click 5.7 again and re-sync with SELECT.

Slots are picked as in WSJT-X: at random, so that beacons on fixed schedules do not keep colliding, with the chosen percentage as the long-run share. Unlike WSJT-X, a transmission is always followed by at least one idle slot, so the PA is never keyed for two slots in a row (at 50 % it alternates exactly, about 46 % key-down). Time from the start of one transmission to the start of the next (the shortest gap leaves about 2 min 9 s of quiet after a transmission ends):

| TX % | Shortest | Average | 9 gaps in 10 under | 99 in 100 under |
|---|---|---|---|---|
| 50% | 4 min | 4 min (always) | 4 min | 4 min |
| 25% | 4 min | 8 min | 16 min | 28 min |
| 10% | 4 min | 20 min | 44 min | 84 min |
| 5% | 4 min | 40 min | 90 min | about 3 h |

Once a transmission has ended the next slot is already chosen, and the top line counts down to it. For a predictable antenna test use 50 % (every 4 minutes) with a small Max TX.

Re-sync at the start of each session: WSPR tolerates about ±2 s and the radio's crystal drifts a few seconds a day.

## How it works

- Frequency: tone 0 at 14 097 098 Hz; the four tones span 14 097 098–14 097 102.4 Hz, centred in the 14.0970–14.0972 MHz WSPR window (`WSPR_FREQ`).
- Transmit uses the CW path (constant carrier, key-click shaping). The tones are made by moving the Si5351 PLL in steps of 1/256 Hz (`freq_calc_fine()`, same registers the SSB transmitter uses); the PLL's real resolution is about 0.1 Hz. Computed from the register arithmetic, the tones are within 0.05 Hz of the exact 1.4648 Hz spacing, for every CW Tone setting.
- Timing: `millis()` runs 1.25× fast on the 20 MHz crystal (the core is built for 16 MHz); all times are converted with `WSPR_U()`. Symbols are 8192/12000 s, timed from the key-down moment.
- The message is encoded when the beacon is switched on (41 bytes: 21 bytes of data bits in RAM, the sync vector in flash).
- Practice mode (menu 2.8) is honoured: the beacon runs and times everything but sends no RF. Good for the first try.

## Things to watch on the first runs

- **PA heat:** 110 s key-down is much longer than CW or FT8. Start with a dummy load, low supply voltage (or USB-C) and a low TX %; feel the BS170s after each transmission for testing. Healthy Class E efficiency matters (see `TROUBLESHOOTING.md`).
- **Sidetone:** the CW sidetone sounds for the whole transmission. Set 2.3 CW Side Vol to −1 to mute it.
- **Frequency:** check the tones land where expected with another receiver running WSJT-X (dial 14.0956 USB, signal at ~1500 Hz audio). An offset of tens of Hz means the Si5351 reference (8.3 Ref freq) needs calibrating; it is still inside the 200 Hz window.

## Tests (run on a PC)

- `python3 test/wspr_encoder_test.py` — compiles the encoder block from `usdx.ino` and compares its 162 symbols with a reference encoder (the KH1 project's, verified against WSJT-X) on 2,000 messages, plus 10 invalid inputs that must be rejected. Also matches the published start of the `K1ABC FN42 37` test vector.
- `python3 test/wspr_beacon_sim.py` — runs the beacon code against a simulated clock: start 1.000 s after the sync press, 110.592 s on air, slot choice (each TX % measured over 200,000 picks, never two slots in a row), every tone value and time, stop on a button press, refusal of a bad callsign, and the countdown text on a simulated 16x2 display (checked every 5 s against the real time left).

## TX Timeout (`TX_TIMEOUT`)

Menu 3.6 TX Timeout: Off (default) / 1 / 2 / 3 / 5 / 10 minutes. A key or PTT held longer than that is cut and the display shows `TX timeout` until the key is released. It covers a straight key or PTT held down only: not VOX transmit, the iambic keyer or CQ messages. The beacon already ends each transmission after 110.6 s. Stored at EEPROM 0x3FE.
