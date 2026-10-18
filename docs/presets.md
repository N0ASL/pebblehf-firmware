# Frequency presets (`FREQ_PRESETS`)

Five saved 20 m frequencies (each with its mode) that you step through from the menu, plus a way to store the frequency you are on. On in this branch (switch near the top of `usdx.ino`); +858 bytes of flash, +2 bytes of RAM.

## Using it

| Menu | What it does |
|---|---|
| 1.14 Preset | Turn the VFO knob to step through slots 1–5. The second line shows the slot, the frequency and the mode, e.g. `1 14.0300 CW`. The radio tunes as you turn, and the VFO you are on (A or B) takes the frequency and the mode, so leave the menu (MENU) to stay there. |
| 1.15 Preset Save | Tune to the frequency you want to keep first, then open this item and turn the knob to the slot number (the second line shows what will be stored, e.g. `3 14.2500 USB`). Leave the item with MENU, SELECT or a knob click and the frequency and mode are stored (`Saved to 3` appears for a moment). `Off` stores nothing. |

Factory slots (used until you store your own; an empty slot always reads as its factory value): 1 14.030 CW, 2 14.060 CW, 3 14.100 CW, 4 14.250 USB, 5 14.285 USB. The CW slots set the CW filter and the 500 Hz tuning step, the USB slots the 1 kHz step, as the Mode menu does.

Stored slots live in their own EEPROM area (0x3D0–0x3E3, four bytes each: 24-bit frequency, mode in the top byte), so no other settings move. A stored value outside 14.000–14.350 MHz, or with a bad mode, reads as the factory slot. The beacon is not affected: it uses its own frequency.

## Tests

`python3 test/preset_test.py` compiles the preset code from `usdx.ino` with a fake EEPROM and checks the defaults, a stored slot, damaged slots, the band edge, the display text (`14.0300 CW`) and that the area ends before the WSPR area.
