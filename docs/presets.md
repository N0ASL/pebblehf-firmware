# Frequency presets and A/B swap (`FREQ_PRESETS`)

Eight saved 20 m frequencies (each with its mode), reached with one press of Select, and a quick VFO A/B swap. On by default (switch near the top of `usdx.ino`); about +1,200 bytes of flash over the beacon build, no extra RAM to speak of.

Names follow the Pebble HF field reference: **Tuning Knob** (turn / press), **Menu Button** (left), **Select Button** (right).

## Using it

| From the main screen | What happens |
|---|---|
| Short press **Select** | Opens the preset picker (the press does nothing otherwise, as the mode-cycling option is off). |
| Menu **1.14 Presets** | Browse to it (`click to open`) and click: opens the same picker. This is the way to find the feature without knowing the shortcut. |
| **Double click Tuning Knob** | Swaps VFO A and B (also saved, so the radio starts on the same VFO). Before this, the only ways were menu 1.6 or two long presses of Select with RIT in between. |

In the picker the radio shows the keys on the top line and the slot on the bottom:

```
KNOB=go SEL=save
A1 14.0300 CW
```

| In the picker | What happens |
|---|---|
| Turn the **Tuning Knob** | Step through slots 1–8. Nothing is tuned yet, so the VFO keeps its frequency. |
| Short press **Tuning Knob** | Go: tune the **active** VFO to the slot (frequency and mode, with the usual CW/SSB filter and step) and leave the picker. Does nothing on an empty slot. |
| Short press **Select** | Store the active VFO's current frequency and mode in the slot shown. `Saved to 6` appears for a moment, then the slot is shown again. Careful: Select also opens the picker, so a quick second press right after opening stores into slot 1. |
| Short press **Menu** | Leave the picker without changing anything. |

The picker never asks for VFO A or B: it works on whichever one is active, and the letter at the start of the bottom line (`A1`, `B6`) shows which. To set both VFOs, do it once, double-click the Tuning Knob, and do it again.

Factory slots (used until you store your own over them): 1 14.030 CW, 2 14.060 CW, 3 14.100 CW, 4 14.250 USB, 5 14.285 USB. Slots 6–8 start empty (`empty`). The CW slots set the CW filter and the 500 Hz tuning step, the USB slots the 1 kHz step, as the Mode menu does.

While the beacon is running any button press stops the beacon first, so the picker opens only with the beacon off. The picker is also not available inside a menu.

## Why Select and a double click, not a two-button chord

The three buttons share one analog input (PC3, 10 k to ground): Menu connects it through 3.3 k (3.76 V), Select through 1 k (4.55 V) and the Tuning Knob straight to +5 V. Any chord that includes the knob reads as the knob alone, Menu + Select reads 4.64 V against 4.55 V for Select alone, and two buttons never go down in the same instant. Single presses and double clicks are the only gestures that can be told apart reliably. Select short press, Tuning Knob double click and Menu double click were the unused ones; Menu double click is left alone because it is in practical use (two quick clicks enter and leave the menu).

If you enable `MODE_BUTTON_CHANGE` (Select cycles the mode), the picker takes the Select short press first.

## Storage

Slots live in their own EEPROM area (0x3D0–0x3EF, four bytes each: 24-bit frequency, mode in the top byte), outside the parameter list, so no other settings move. A stored value outside 14.000–14.350 MHz, or with a bad mode, reads as the factory value for that slot (empty for 6–8). The beacon is not affected: it uses its own frequency.

## Tests

`python3 test/preset_test.py` compiles the preset code from `usdx.ino` with a fake EEPROM and a 16×2 screen model and checks the factory and empty slots, a stored slot, damaged slots, the area limits, the picker screen (hint line, A/B letter, slot text, empty slot, column 15 left for the T/R indicator) and storing the active VFO's frequency and mode. The button handling in `loop()` is not covered by a test.
