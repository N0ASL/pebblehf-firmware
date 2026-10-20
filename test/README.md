# PC-side checks for the added code

These are the fork author's own checks of the code this fork adds to `usdx.ino`. You do not need them to build, flash or use the firmware.

Each script pulls a marked block of code out of `usdx.ino`, compiles it on a PC with stand-ins for the hardware (a simulated clock, EEPROM and LCD), and checks the result. They only work with this firmware's code.

| Script | What it checks |
|---|---|
| `wspr_encoder_test.py` | The WSPR encoder, symbol by symbol, against a separate reference encoder (itself checked against WSJT-X's), including bad calls |
| `wspr_beacon_sim.py` | The beacon against a simulated clock: start 1 s after the sync press, 110.6 s on air, slot choice and TX %, every tone, stop on a button press, refusal of a bad call |
| `preset_test.py` | The frequency presets: factory and empty slots, storing and recalling in all five modes, damaged slots, the picker screen |
| `menu_nav_test.py` | Navigation through the WSPR menu |

## Running them

You need Python 3 and a C++ compiler (`g++` or `c++`) on the PATH. From the repository root:

```
python3 test/wspr_encoder_test.py
python3 test/wspr_beacon_sim.py
python3 test/preset_test.py
python3 test/menu_nav_test.py
```

## What these checks are, and are not

They are regression checks written by the same side that wrote the code, so they confirm the code does what was intended, not that the intent is right. The encoder test is the one partly independent check, since it compares against a separate reference. They do not replace your own testing, and they are not proof that something works on the air. If you change the beacon, preset or menu code, they are a quick way to see that you haven't broken it by accident, and you should test on a radio as well.

What has been tried on a real radio (a Pebble HF V2.5) is listed in [`docs/firmware.md`](../docs/firmware.md).
