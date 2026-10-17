# WSPR beacon (`WSPR_BEACON`)

Status (17 Oct 2026): **written and host-tested, not yet tried on a radio.** Developed on the `wspr-beacon` branch; merged into `main` once it has worked on the air.

A stand-alone WSPR beacon inside the Pebble HF firmware: no Pico, phone or computer attached. It sends a standard WSPR message (callsign, 4-character grid, power) on one fixed frequency in the 20 m WSPR window.

## Building

Enable the switch near the top of `usdx.ino`:

```c
#define WSPR_BEACON    1   // Stand-alone WSPR beacon ...
```

Nothing else changes; DIAG stays on, CAT stays off. With the switch off the build is byte-for-byte the official firmware (checked: identical hex).

| Build of 1.0.7 | Flash (of 32,256) | RAM used | RAM left for stack |
|---|---|---|---|
| Official | 26,894 | 1,022 | 1,026 |
| `WSPR_BEACON` | 29,960 (92%) | 1,196 | 852 |

Your saved settings and calibration (Ref freq, IQ phase, PA bias, VFOs) survive flashing this build: the WSPR settings live in their own EEPROM area (0x3F0–0x3FB) and do not shift the other settings' addresses.

## Using it

Menu entries (section 5):

| Menu | Values | Notes |
|---|---|---|
| 5.1 WSPR Call | text, up to 6 characters | standard calls only (digit as 2nd or 3rd character, e.g. N0ASL, K1ABC, G4ABC); no /P or prefixes |
| 5.2 WSPR Grid | 4 characters | e.g. EN34 |
| 5.3 WSPR Power | 20 / 23 / 27 / 30 / 33 / 37 dBm | the value sent in the message; the radio cannot measure its output. About 5 W (37) on 13.8 V, about 1 W (30) on USB-C |
| 5.4 WSPR Every | 2 / 4 / 6 / 10 / 20 min | time between transmission starts; default 10 |
| 5.5 WSPR Beacon | OFF / ON | not stored; always OFF at power-up |

Text entry uses the firmware's string editor: turn the knob to change a character, click the knob to move to the next character, left button to save.

1. Set call, grid, power and interval once (they are saved).
2. Set **5.5 WSPR Beacon** to ON and leave the menu. The top line shows `R at even minute` (or `WSPR: bad call` / `WSPR: bad grid`).
3. Watch the phone's clock and **click the right button the moment an even minute starts** (e.g. 14:32:00). The moment the button goes down is used, not the end of the click.
4. The first transmission starts 1 s later and lasts 110.6 s (top line `WSPR TX` and symbols left). Between transmissions the top line counts down (`WSPR next 8:21`); the radio receives normally, and the knob still tunes.
5. **Any button press stops the beacon** (also during a transmission, as does the key/PTT). Switch it on again from the menu and re-sync.

Re-sync at the start of each session: WSPR tolerates about ±2 s and the radio's crystal drifts a few seconds a day.

## How it works

- Frequency: tone 0 at 14 097 098 Hz; the four tones span 14 097 098–14 097 102.4 Hz, centred in the 14.0970–14.0972 MHz WSPR window (`WSPR_FREQ`).
- Transmit uses the CW path (constant carrier, key-click shaping). The tones are made by moving the Si5351 PLL in steps of 1/256 Hz (`freq_calc_fine()`, same registers the SSB transmitter uses); the PLL's real resolution is about 0.1 Hz. Computed from the register arithmetic, the tones are within 0.05 Hz of the exact 1.4648 Hz spacing, for every CW Tone setting.
- Timing: `millis()` runs 1.25× fast on the 20 MHz crystal (the core is built for 16 MHz); all times are converted with `WSPR_U()`. Symbols are 8192/12000 s, timed from the key-down moment.
- The message is encoded when the beacon is switched on (41 bytes: 21 bytes of data bits in RAM, the sync vector in flash).
- Practice mode (menu 2.8) is honoured: the beacon runs and times everything but sends no RF. Good for the first try.

## Things to watch on the first runs

- **PA heat:** 110 s key-down is much longer than CW or FT8. Start with a dummy load, low supply voltage (or USB-C) and the 10-minute interval; feel the BS170s after each transmission. Healthy Class E efficiency matters (see `TROUBLESHOOTING.md`).
- **Sidetone:** the CW sidetone sounds for the whole transmission. Set 2.3 CW Side Vol to −1 to mute it.
- **Frequency:** check the tones land where expected with another receiver running WSJT-X (dial 14.0956 USB, signal at ~1500 Hz audio). An offset of tens of Hz means the Si5351 reference (8.3 Ref freq) needs calibrating; it is still inside the 200 Hz window.

## Tests (run on a PC)

- `python3 test/wspr_encoder_test.py` — compiles the encoder block from `usdx.ino` and compares its 162 symbols with a reference encoder (the KH1 project's, verified against WSJT-X) on 2,000 messages, plus 10 invalid inputs that must be rejected. Also matches the published start of the `K1ABC FN42 37` test vector.
- `python3 test/wspr_beacon_sim.py` — runs the beacon code against a simulated clock: start 1.000 s after the sync press, 110.592 s on air, 10-minute interval, every tone value and time, stop on a button press, refusal of a bad callsign.

## Not done (possible later)

- WWV time sync (experimental idea: receive 10 MHz, find the minute tone and the even/odd bit).
- Frequency offset within the window, compound callsigns (type 2/3 messages), other bands.
