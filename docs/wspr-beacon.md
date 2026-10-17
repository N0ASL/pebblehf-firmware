# WSPR beacon in the Pebble HF firmware (plan)

Status: plan agreed 17 Oct 2026, not yet written. Code is developed on the `wspr-beacon` branch and merged into `main` once tested on the air.

This is a firmware-only feature: the radio becomes a stand-alone WSPR beacon with no Pico, phone or computer attached.

## What it does

1. Transmits a standard WSPR message (callsign, 4-character grid, power) on one fixed 20 m frequency inside the WSPR window, 14.0970–14.0972 MHz (USB dial 14.0956 MHz + 1400–1600 Hz). Default: 14.097100 MHz.
2. Time sync by hand: choose start in the menu, then click Select at the moment the phone's clock rolls over to an even minute.
3. Each transmission starts 1 s after an even minute and lasts 110.6 s (162 symbols of 0.6827 s, 4-FSK, 1.4648 Hz spacing).
4. Repeats on the interval chosen in the menu.
5. Any button press stops it and returns to receive.

## Menu entries

| Entry | Values | Notes |
|---|---|---|
| WSPR Call | text | uses the firmware's existing string editor (`MENU_STR`) |
| WSPR Grid | 4 characters | e.g. EN34 |
| WSPR Power | 37 / 33 / 30 / 27 dBm | 5 / 2 / 1 / 0.5 W. The radio cannot measure its output, so the operator picks the value (normal WSPR practice). About 5 W on 13.8 V, about 1 W on USB-C |
| WSPR Every | 2 / 4 / 6 / 10 / 20 min | default 10; longer intervals keep the PA cooler |
| WSPR Start | — | arms the beacon, then waits for the Select click on the even minute |

## Build

- New build switch `WSPR_BEACON` in `usdx.ino`, off by default so the stock behaviour is unchanged.
- `CAT` stays off (as in the official firmware); CAT (≈4.1 KB) and the beacon (≈2–2.4 KB) would not fit together with DIAG.
- DIAG stays on. Nothing else is turned on.

## Budget (estimates until written)

| Part | Flash |
|---|---|
| WSPR encoder (message packing, convolutional code, interleave, sync vector) | 1.0–1.5 KB |
| Beacon timing, keying, display | 0.3–0.5 KB |
| Menu entries | 0.1–0.2 KB |
| String editor (`MENU_STR`, now only built with `CW_MESSAGE`) | 0.3–0.4 KB |
| **Total** | **≈2.0–2.4 KB of 5.36 KB free** (stock 1.0.7 = 26,894 of 32,256 bytes) |

RAM: the 162 symbols pack into 41 bytes; a few bytes of timing state.

## Technical notes

- Tones: the firmware's fast Si5351 update (`freq_calc_fast(int16_t df)`) works in whole hertz. Try a finer-step version first (the PLL maths already scales by 128); if that is not clean, fall back to dithering between 1 Hz steps, which the KH1 simulation showed decodes as well as exact tones (down to −29 dB, 4 steps per symbol).
- Frequency stability: 26 MHz TCXO on the Si5351, so drift over 110 s should be negligible.
- Timing: WSPR decoders accept about ±2 s; within 1 s costs nothing. A button press against the phone's clock is good to ~0.2–0.3 s. The AVR's 20 MHz crystal drifts ~2–4 s/day, so sync at the start of each session (re-sync after ~6–12 h).
- PA heat: 110 s key-down is much longer than FT8 (13 s). Check the BS170 temperature on the first runs, starting at reduced drive or supply voltage. Class E efficiency must be healthy (≥75 %, see the Pebble HF troubleshooting guide).
- Transmit uses constant amplitude (like CW), not the SSB envelope path.

## Testing plan

1. Encoder: compare the 162 symbols with WSJT-X's reference encoder for several messages (on the PC, before flashing).
2. Bench: Practice mode / dummy load; check timing against the phone and the tone steps on a receiver running WSJT-X.
3. Air: low power, then check wsprnet.org / wspr.live for spots.
