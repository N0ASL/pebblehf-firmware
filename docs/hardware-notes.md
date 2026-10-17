# Hardware notes: Pebble HF V2.5

Board notes gathered while looking at an external controller (a Raspberry Pi Pico W) for the radio. **The Pico interface is parked (17 Oct 2026)**; the fork now focuses on firmware-only features. The notes are kept because the pin, test-point and power details are useful either way.

Power: DC jack → SS34 (D1) → "+12V" rail (PA) → AMS1117-5.0 (U1) → +5V rail (AVR, LCD, receiver). USB-C VBUS connects straight to the +5V rail (so on DC power the regulator's 5 V also appears on VBUS) and through SS34 (D3) to the +12V rail. AMS1117-3.3 (U5) from +5V feeds the Si5351. U1 dissipates (Vin − 5 V) × load; adding external loads to the +5V rail at 13.8 V input needs care (heat).

Source: PEBBLE HF V2.5 schematic (WB2CBA, rev V2.5, 12/5/2025) and the firmware's pin definitions. The D4/D5 connection was confirmed by continuity check on the owner's V2.5 board (17 Oct 2026).

## The serial port is on the LCD

The ATmega328P (U2, TQFP-32) drives the RC1602A LCD in 4-bit mode. Two of the LCD data lines are the UART:

| AVR pin | Port | UART | LCD pin | LCD label |
|---|---|---|---|---|
| 30 | PD0 | RXD (AVR receives) | 11 | D4 |
| 31 | PD1 | TXD (AVR sends) | 12 | D5 |

The LCD module's pins are labelled VSS, VDD, VO, RS, RW, E, D0–D7, A, K, so D4 and D5 can be tapped on the module itself. LCD RW is tied to ground, so the LCD never drives these lines. There are no series resistors or diodes on them on the board.

With CAT enabled, the firmware turns the UART off for each LCD write and back on afterwards, and holds off display updates for a short time after each CAT command.

## Wiring

| Pebble HF | Pico W | Notes |
|---|---|---|
| LCD D4 (AVR RXD) | GP0 (UART0 TX) | through **1 kΩ** series, so the AVR can still drive D4 for the display without fighting the Pico |
| LCD D5 (AVR TXD) | GP1 (UART0 RX) | through a divider, 5 V → 3.3 V (e.g. 2.2 kΩ top / 3.3 kΩ bottom) |
| GND (LCD VSS or ISP pin 6) | GND | |

Expect LCD traffic as junk bytes on the Pico's receive line and occasional lost bytes during display writes. The Pico driver must accept only well-formed replies, retry, and confirm each set by reading back. The firmware comments suggest a diode from PC2 to separate the traffic, but on the Pebble HF PC2 is the microphone input, so this project filters in software instead.

Serial: 38400 baud, 8N1, not inverted (115200 if `CAT_STREAMING` is ever enabled).

## ISP header (J3)

| J3 pin | Signal | AVR port | Radio function |
|---|---|---|---|
| 1 | MISO | PB4 | DAH (key ring) |
| 2 | +5V | | |
| 3 | SCK | PB5 | DIT (key tip / built-in key) |
| 4 | MOSI | PB3 | SIG_OUT |
| 5 | RESET | PC6 | |
| 6 | GND | | |

Keying without CAT: pull DIT low from an open-drain Pico GPIO (never drive it high) with the keyer in Straight mode.

## Test points

| TP | Net |
|---|---|
| TP1 / TP3 / TP2 | Si5351 CLK0 / CLK1 / CLK2 |
| TP9 | AD0 (PC0), receiver I channel from U10 |
| TP10 | AREF |
| TP11 | AD1 (PC1), receiver Q channel from U10 |

TP9/TP11 are biased mid-rail by 10k/10k dividers. Useful for checking the receiver, not for this interface.

## Other notes

- USB-C (J5) is power only (5.1 kΩ CC resistors, no data lines used); about 1 W output on 5 V.
- Audio: HEADPHONE jack J6, MIC/PTT/KEYER jack J2 (tip = DIT/PTT, ring = DAH).
- 26 MHz TCXO on the Si5351; 20 MHz crystal on the AVR.
