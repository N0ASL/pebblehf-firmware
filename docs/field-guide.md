# Pebble HF Field Guide (tentative)

> **Tentative draft.** Not yet reviewed by the owner. It is a preliminary field guide for firmware 1.0.7-N0ASL, to be corrected and updated as the firmware changes. It was checked against the repo at commit ed4aa63 (18 Oct 2026) by reading `usdx.ino` and the repo docs, not by trying each step on the radio; the firmware features it describes have all been tried on the radio (last round 19 Oct 2026). For full details see [OPERATING_MANUAL.md](../OPERATING_MANUAL.md), [wspr-beacon.md](wspr-beacon.md) and [presets.md](presets.md).

| ▶️ **Video walkthrough** |
|---|
| <a href="https://youtu.be/kMhRi84KVA4"><img src="https://img.youtube.com/vi/kMhRi84KVA4/mqdefault.jpg" width="200" alt="Pebble HF firmware additions on YouTube"></a><br>[Pebble HF firmware additions on YouTube](https://youtu.be/kMhRi84KVA4) |

## At a glance

Firmware 1.0.7-N0ASL on the 20 m Pebble HF (14.000–14.350 MHz; USB, LSB, CW, FM, AM). Three controls do everything: the Tuning Knob (turn and press), MENU (left) and SELECT (right).

| Control | Action | What it does |
| --- | --- | --- |
| Tuning Knob | Turn | Tune |
| Tuning Knob | Short press | Bigger tuning step |
| Tuning Knob | Long press | Smaller tuning step |
| Tuning Knob | Press and turn | Volume (turning below 0 powers off) |
| Tuning Knob | Double click | Swap VFO A and B (turns RIT off) |
| SELECT | Short press | Open the preset picker |
| SELECT | Double click | Cycle the filter width |
| SELECT | Long press | RIT on or off; a second long press swaps VFO A and B |
| MENU | Short press | Enter the menu |
| MENU | Hold and turn | Jump through the menu quickly |

In the menu, MENU opens the value for editing and SELECT saves and steps back one level. A double click means two quick clicks, about 0.4 s apart at most; a press held longer than about 0.25 s counts as a long press.

## Everyday operation

Power it from 13.8 V for about 5 W, or from USB-C for about 1 W (USB-C carries power only). To switch off, press and turn the Tuning Knob until the volume goes below 0; the screen shows "Power-off 73 :-)".

| Task | How |
| --- | --- |
| Tune | Turn the knob. Short press = bigger step, long press = smaller step (10 MHz down to 1 Hz). Changing mode or VFO sets 1 kHz for SSB and 500 Hz for CW. |
| Volume | Press and turn the knob, 0 to 16. |
| Filter width | Double-click SELECT. SSB: Full, 3000, 2400, 1800 Hz. CW: 500, 200, 100, 50 Hz. |
| Mode | Menu 1.2: LSB, USB, CW, FM or AM. SELECT does not change mode in this build. USB is the normal voice mode on 20 m. |
| RIT | Long press SELECT; the step drops to 10 Hz. Long press again to turn RIT off and swap VFOs. |
| Digital modes | External USB sound card. Menu 3.1 VOX on, 3.2 Noise Gate 50. For a first test, turn 2.8 Practice on so nothing is transmitted. |

## Presets and VFO A/B

Eight saved frequencies (each with its mode) are one SELECT press away; double-clicking the Tuning Knob swaps VFO A and B. From the main screen, a short press of SELECT opens the picker (menu 1.14 Presets does the same). It works on whichever VFO is active; the small a or b at the start of the bottom line (a1, b6), the same one the main screen uses, shows which.

| In the picker | What happens |
| --- | --- |
| Turn the knob | Step through slots 1 to 8 (nothing is tuned yet) |
| Short press the knob | Go: tune the active VFO to that slot (RIT off); does nothing on an empty slot |
| Short press SELECT | Store the current frequency and mode in the slot shown ("Saved to n") |
| Short press MENU | Leave without changing anything |

Don't press SELECT again right after the picker opens, because that stores the current frequency into slot 1. To set both VFOs, pick a slot, double-click the knob, then pick another.

| Slot | Factory value |
| --- | --- |
| 1 | 14.030 MHz CW |
| 2 | 14.060 MHz CW |
| 3 | 14.100 MHz CW |
| 4 | 14.250 MHz USB |
| 5 | 14.285 MHz USB |
| 6 to 8 | empty |

The picker does not open inside a menu or while the WSPR beacon is running.

## WSPR beacon: quick antenna test

Set your call, grid and power once, start the beacon, then click SELECT at the start of an even minute. Check the signal on a second receiver running WSJT-X (dial 14.0956 MHz USB; the signal sits near 1500 Hz audio).

For an idea of what to expect: on 19 Oct 2026 the beacon ran at about 4 W from 11 V and about 0.8 W on USB-C into a 20 m whip, and was spotted on WSPRnet across the US and Canada. The map is in [`wspr-beacon.md`](wspr-beacon.md).

One-time setup in menu 5.0 WSPR Menu (click to open); the settings are saved:

| Menu | Setting | Default |
| --- | --- | --- |
| 5.1 | Call (standard calls only, no /P, no blank inside) | none |
| 5.2 | Grid, four characters, e.g. EN34 | none |
| 5.3 | Power sent in the message: 20, 23, 27, 30, 33 or 37 dBm | 37 |
| 5.4 | TX %: 5, 10, 25 or 50 | 10 |
| 5.5 | Offset: -90 to +90 Hz, or Random | 0 |
| 5.6 | Max TX: No limit, 1, 2, 3, 5 or 10 | No limit |

For a short test, set 5.6 Max TX to 1 to 3 so the beacon stops by itself and shows "WSPR done". Power 5.3 is only the number sent; the radio does not measure its output. Use 37 for about 5 W on 13.8 V and 30 for about 1 W on USB-C. TX % picks slots at random, as in WSJT-X: 50 % transmits every 4 minutes; at 25 % the average is 8 minutes from start to start, but a single gap can be 4 minutes or much longer. After each transmission the top line counts down the real wait.

Each test run:

1. Click 5.7 WSPR Beacon. This only arms the beacon: the menu closes, the top line shows "SEL at even min", and nothing transmits until you sync in the next step.
2. Watch a clock and click SELECT the moment an even minute starts (for example 14:32:00). The moment the button goes down is used.
3. The first transmission starts 1 s later and lasts about 110 s. The top line counts down ("WSPR TX 110s 5%"), then shows the wait until the next one ("WSPR TX in 5:21").
4. To stop, click MENU, SELECT or the Tuning Knob. PTT stops a transmission in progress, unless VOX (3.1) is on.
5. To restart, click 5.7 again and re-sync with SELECT.

Re-sync at the start of every session, because WSPR tolerates about 2 s and the crystal drifts a few seconds a day. The knob does not tune while the beacon is on. The beacon is always off at power-up. The CW sidetone sounds for the whole transmission; set 2.3 CW Side Vol to -1 to mute it. For a dry run with no RF, turn on 2.8 Practice first.

## Limits and cautions

Three things can cost you in the field: a long key-down heating the PA, a stuck key, and a settings reset that also wipes calibration.

| Caution | What to do |
| --- | --- |
| PA heat | A WSPR transmission keys the PA for about 110 s, much longer than CW or FT8. Test on a dummy load or low supply voltage first, keep TX % low, and feel the BS170 transistors after each transmission. TX Drive (3.3) does not change the beacon's output; a lower supply voltage does (about 1 W on USB-C against about 5 W on 13.8 V). |
| Stuck key or PTT | Set menu 3.6 TX Timeout (1, 2, 3, 5 or 10 min). A straight key or PTT held longer is cut and the screen shows "TX timeout" until you release it. Default is Off. It does not cover VOX, the iambic keyer, CQ messages or the beacon. |
| Iambic keyer | Menu 2.6 defaults to Straight. If you pick Iambic A or B, plug a paddle in first; with nothing connected the microphone can trigger the keyer and transmit. |
| Factory reset | Holding the Tuning Knob down at power-up resets the saved settings to defaults. That includes the calibration values (8.3 Ref freq, 8.4 IQ phase, 8.1 and 8.2 PA bias), so only do it with the EEPROM backup to hand. The WSPR call and grid may also need re-entering. The presets are stored separately. |
| PA bias | Leave 8.1 and 8.2 alone unless you understand PA biasing; wrong values can damage the PA. |
| Power off | The radio switches off when the volume goes below 0, so turn the volume down slowly while the knob is pressed. |

## Quick fixes

Most field problems are a setting or a button habit, not a fault. The start-up self-test is off in this build, so a hardware fault will not be flagged at power-up.

| What you see | Likely cause and fix |
| --- | --- |
| SELECT seems slow to react | A single press waits a moment to see whether a second click follows. Normal. |
| Preset picker opened by accident | MENU leaves it without changing anything. |
| "Bad WSPR" | The call or grid is empty or not valid; fix 5.1 or 5.2. Standard calls only (digit as 2nd or 3rd character, no /P); grid is two letters A to R then two digits. |
| Beacon not decoded, or timing looks off | Stop it, click 5.7 and re-sync with SELECT at the start of an even minute. |
| WSPR tone tens of Hz from where expected | Calibrate 8.3 Ref freq against a known signal. Still inside the 200 Hz WSPR window. |
| "TX timeout" on the screen | The key or PTT was held past the 3.6 limit. Release it. |
| Digital mode transmits when it should not | Raise 3.2 Noise Gate above 50 and keep 3.1 VOX on. |
| "Reset settings.." at power-up | The Tuning Knob was down at power-up, or the stored settings did not match the firmware. Check calibration and WSPR call and grid. |
| PA gets hot or output is low | Suspect the toroid winding first. Healthy efficiency is 75 to 79 percent (4.5 to 5.5 W at 13.8 V); below 50 percent the BS170s overheat. |

## Keeping this guide current

Checked against N0ASL/pebblehf-firmware main at commit ed4aa63 (18 Oct 2026) by reading `usdx.ino` and the repo docs, not by trying each step on the radio; the firmware features it describes have all been tried on the radio (last round 19 Oct 2026). When the firmware changes, update the matching section below, the version in the first line of At a glance, and the date at the top.

| Guide section | Re-check against |
| --- | --- |
| At a glance, Everyday operation | Button handling in the main loop of `usdx.ino`; the button table in `OPERATING_MANUAL.md` |
| Presets and VFO A/B | `docs/presets.md` and the `preset_default` table in `usdx.ino` |
| WSPR beacon | `docs/wspr-beacon.md`; menu numbers and defaults in `usdx.ino` |
| Limits and cautions | `docs/firmware.md`, `OPERATING_MANUAL.md` and `TROUBLESHOOTING.md` |
| Quick fixes | Anything above that changed |

A change that does not alter buttons, menus, defaults or messages (a size saving, for example) needs no edit here.
