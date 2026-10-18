# Fork notes: building the firmware

`usdx.ino` in the repo root is N4FFF's Pebble HF firmware (currently 1.0.7), unchanged except for this fork's additions, which sit behind build switches. In the `wspr-beacon` branch `WSPR_BEACON` is on and `DIAG` is off by default; commenting out `WSPR_BEACON`, `FREQ_PRESETS` and `VERSION_TAG` and restoring `DIAG` gives the official build. `VERSION_TAG` (`-N0ASL`) is appended to the version in menu 10.1 (`10.1 1.0.7-N0ASL`, with the compile date on line 2) and shown on line 2 at start-up. A default build is the official firmware.

## Building

Arduino IDE or arduino-cli, board "Arduino Uno" (ATmega328P). The Arduino IDE wants the sketch folder named like the file, so put `usdx.ino` in a folder called `usdx`. Program with an ISP programmer (see `PROGRAMMING.md`); there is no bootloader.

Before the first flash of a self-built image, back up what is on the radio:

```
avrdude -c <programmer> -p m328p -U flash:r:pebble_backup.hex:i -U eeprom:r:pebble_eeprom.hex:i
```

Do not change the fuses (factory: lfuse 0xFF, hfuse 0xD6, efuse 0xFD).

## Flash and RAM (measured 17 Oct 2026)

avr-gcc 7.3.0, ArduinoCore-avr 1.8.6, board "Arduino Uno" (32,256 bytes flash usable, 2,048 bytes RAM). The Arduino IDE may differ by a few hundred bytes.

| Build of 1.0.7 | Flash | RAM used | RAM left for stack |
|---|---|---|---|
| Official (DIAG, KEYER, CW decoder, VOX, …) | 26,894 (83%) | 1,022 | 1,026 |
| without `DIAG` | 25,578 | 1,022 | 1,026 |

Free flash in the official build: **≈5.4 KB**. The `wspr-beacon` branch turns DIAG off to make room for the beacon.

### This fork's switches

| Switch | Adds | Flash | RAM left for stack |
|---|---|---|---|
| `WSPR_BEACON` | stand-alone WSPR beacon, menu 5.1–5.5 ([docs](wspr-beacon.md)) | +3,824 (30,718 total) | 847 |
| `WSPR_BEACON`, `DIAG` off | as above, without the startup self-test | 29,402 total | 847 |
| `FREQ_PRESETS` | 8 frequency presets, Select opens the picker, Tuning Knob goes, Select stores; Tuning Knob double click swaps A/B ([docs](presets.md)) | +1,142 | 833 (with the beacon) |
| branch default: beacon, presets, `DIAG` off | | 30,564 total (94%) | 833 |

With this fork's switches off and `DIAG` on, the build is byte-identical to the official firmware.

Host tests: `python3 test/wspr_encoder_test.py`, `python3 test/wspr_beacon_sim.py` (need a C++ compiler).

### Built-in optional switches (already in the source, off in the Pebble HF build)

Measured as single additions to the official build:

| Switch | Adds | Flash | Note |
|---|---|---|---|
| `CAT` | Kenwood TS-480 style CAT on the UART (shared with LCD D4/D5) | +4,080 | was on in upstream uSDX; drives PC2 (Pebble mic input) around LCD writes, see hardware notes |
| `CAT` + `CAT_EXT` | + remote buttons (`UK`), display read (`UD`) | +4,850 | |
| `CW_MESSAGE` | one CW memory with knob text editor, "CQ Interval" repeat | +1,060 | was on in upstream uSDX |
| `CW_MESSAGE_EXT` | six 48-character memories | +1,462 | +240 bytes RAM |
| `FAST_AGC` | fast AGC option | +340 | |
| `CLOCK` | hh:mm:ss since power-on in the S-meter area (cannot be set) | +306 | |
| `MODE_BUTTON_CHANGE` | right button cycles LSB/USB/CW | +266 | N4FFF addition, not in upstream |
| `VSS_METER` | supply voltage in the S-meter area | +70 | needs 1 MΩ from 12 V to PC3 |
| `CW_INTERMEDIATE` | decoder shows partial characters | +20 | was on in upstream uSDX |

The 1.0.8 file in WB2CBA's hardware repo (`PEBBLEHF_20m.ino`) differs from 1.0.7 only by a compile-time 20 m / 40 m band selection.

## Startup self-test (DIAG)

Runs once at power-up: checks the 5 V rail (4.8–5.2 V), 3.3 V rail, AVCC, mic and receiver (I/Q) bias, Si5351 I2C speed and a 1000-write I2C error test. A failure shows e.g. `!!V5.0=4.7V` on line 2 for 1.5 s, then the radio starts normally. Nothing is shown when all checks pass.

## CAT reference (not used in this fork's builds)

| Command | Meaning |
|---|---|
| `FA;` / `FA00014074000;` | read / set VFO A (11 digits, Hz). **Set is not clamped to the band** |
| `IF;` `ID;` | status, radio ID |
| `MD;` / `MDn;` | mode: 1 LSB, 2 USB, 3 CW (4/5 = FM/AM, not Pebble modes) |
| `TX;` … `RX;` | transmit / receive (no timeout in the firmware) |

38400 baud. Each complete command stalls the main loop 10 ms, and LCD writes wait for serial traffic while CAT is active.
