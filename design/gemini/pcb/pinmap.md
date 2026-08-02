# Gemini — electronics & pin map (rev A)

**One controller.** A single Raspberry Pi Pico on the **left** half; the
right half is passive with an **MCP23017 I/O expander**. The halves link
over **USB-C carrying I2C** — 4 conductors (3V3 on VBUS, SDA on D+, SCL on
D−, GND), so any USB 2.0 C-to-C cable works and orientation doesn't matter.
No split-sync firmware: the whole keyboard is one matrix, half of it read
over I2C (ErgoDox-style; QMK supports expander matrices natively).

## Left half — Raspberry Pi Pico (U1)

On the back, **horizontal, centered on the row-1 switch centerline**
(y = 28.575 mm), micro-USB (host port) exiting the **outer-left side
edge**. Its two header pin rows land at y ≈ 19.7 and 37.5 mm — near the
centers of the top-face corridors between switch housings, so the pins
protruding through the board clear the switch bodies sitting on top, and
no through-hole touches any socket pad or switch drill. Two row-1 diodes
(D10, D11) relocate into the brow to stay off the lower pin row.
**Mounted on low-profile headers (~2.5 mm standoff), not flat**: switch
pins protrude ~1.7 mm below the PCB and hotswap sockets are 1.85 mm tall,
so both clear underneath the module — every key above the Pico keeps its
hotswap socket. The case gets a ~5 mm pocket along this strip (elsewhere
~2 mm suffices) and a side cutout for the micro-USB.

| Pico pin    | GPIO     | Function        | Notes                          |
|-------------|----------|-----------------|--------------------------------|
| 1           | GP0      | I2C0 SDA        | to link port D+ · 4.7 kΩ pull-up (R1) |
| 2           | GP1      | I2C0 SCL        | to link port D− · 4.7 kΩ pull-up (R2) |
| 4–7         | GP2–GP5  | ROW0–ROW3       | shared row nets, left matrix   |
| 9–12, 14–15 | GP6–GP11 | COL0–COL5       | left matrix (pin 13 is GND)    |
| 21          | GP16     | LED data        | → 74AHCT1G125 (U2) → LED chain |
| 36          | 3V3      | Logic rail      | I2C pull-ups                   |
| 40          | VBUS     | +5V             | LED power + right half via link|
| 3, 8, 13, … | GND      | Ground          |                                |

Unused GPIOs break out to labeled test pads (encoder, pogo dock
detect — future).

## Host USB-C port (J2, left half, in the brow)

Alternative to the Pico's onboard micro-USB (which sits mid-board at the
side edge — usable but awkward for a desk cable). Proper device-role port:

- **CC1/CC2**: separate 5.1 kΩ pulldowns (R3/R4) so C-to-C cables and hosts
  supply VBUS.
- **VBUS → VSYS** through Schottky DV1 (B5819W), diode-ORed against the
  Pico's internal VBUS→VSYS diode — safe with both cables plugged, per the
  Pico datasheet's dual-power pattern.
- **D+/D−**: the Pico exposes USB data only on underside test points, not
  the header. J2's D± route to two pads (TP1/TP2) in the brow next to the
  module's USB end — bridge to the Pico's **TP3 (D+) / TP2 (D−)** with two
  short jumper wires at assembly (or relocate the pads under the exact TP
  positions for spring pins during routing).
- Everything downstream (LEDs, link, right half) runs off **VSYS**
  (~4.7 V after the diode) — works identically from either port.

## Right half — MCP23017-E/SO (U1, SOIC-28)

| MCP pin | Signal   | Function              |
|---------|----------|-----------------------|
| 1–6     | GPB0–GPB5| COL0–COL5 (right)     |
| 21–24   | GPA0–GPA3| ROW0–ROW3 (right)     |
| 9 / 10  | VDD / VSS| 3V3 (from link) / GND · 100 nF (C1) |
| 12 / 13 | SCL / SDA| I2C, address 0x20     |
| 15–17   | A0–A2    | tied GND              |
| 18      | /RESET   | tied 3V3              |

3V3 comes from a local **MCP1700-3302** LDO (U2) fed by the 5V link, with
1 µF caps on both sides (C2/C3).

## Link port (J1 on each half — HRO TYPE-C-31-M-12)

| USB-C pins        | Net      | Carries                  |
|-------------------|----------|--------------------------|
| GND (1/12/shield) | GND      | ground                   |
| VBUS (2/11)       | +5V      | power to right half + LEDs |
| D+ (A6/B6 = 6/7)  | SDA      | I2C data                 |
| D− (A7/B7 = 5/8)  | SCL      | I2C clock                |
| CC + SBU (3/4/9/10) | LED_LINK | WS2812 LED chain data  |

CC1/CC2 are tied together on each board so the cable's single CC wire
carries LED data regardless of plug orientation (SBUs tied too — unwired
in USB 2.0 cables, parallel in full-featured ones, harmless either way).
⚠ **Requires a basic non-e-marked C-to-C cable** — an e-marker chip loads
the CC line. ⚠ **Not a real USB port** — label it. Verify the pad↔pin
mapping against the HRO datasheet before fab. Consider series resistors on
D± so nothing dies if someone plugs in a charger.

## Per-key RGB (south-facing)

**SK6812 MINI-E** reverse-mount, one per key, on the back at the switch's
**south LED window** (key center +5.08 mm) shining up through a plated
cutout — south-facing, so no north-facing keycap interference. Chain:
GP16 → 74AHCT1G125 level shifter (3V3→5V, U2 left) → left 22 LEDs
(row-major) → link CC wire → right 21 LEDs. One 43-LED chain in firmware —
no split RGB sync. Power: 5V from Pico VBUS; **cap brightness in QMK**
(43 × ~60 mA at full white ≈ 2.6 A — far beyond a USB 2.0 port's 500 mA;
`RGB_MATRIX_MAXIMUM_BRIGHTNESS` ≈ 120 keeps worst-case near spec).

## Matrix (COL2ROW, 1N4148W SOD-123 per key)

Left 4×6 (22 keys), right 4×6 (21 keys). Diode cathode → row.
Assignments in `kbplacer/gemini_{left,right}_matrix.kle.json`; switch
centers in `placement/`.

## Hotswap coverage

**All 43 keys are hotswap.** The link USB-C connectors live in an 8 mm rear
"brow" strip above row 0 (board depth 84.2 mm total), clear of every socket
zone; the keys above the header-mounted Pico keep their sockets thanks to
the standoff (see above).

## BOM sketch (per keyboard)

| Qty | Part                                     |
|-----|------------------------------------------|
| 1   | Raspberry Pi Pico + low-profile headers  |
| 1   | MCP23017-E/SO (SOIC-28)                  |
| 1   | 74AHCT1G125 SOT-23-5 (LED level shift)   |
| 1   | MCP1700-3302 SOT-23 (right 3V3 LDO)      |
| 1   | B5819W SOD-123 Schottky (host VBUS OR)   |
| 3   | HRO TYPE-C-31-M-12 USB-C receptacle      |
| 2   | 5.1 kΩ 0603 (host port CC pulldowns)     |
| 43  | SK6812 MINI-E (reverse mount RGB)        |
| 43  | 1N4148W SOD-123                          |
| 43  | Kailh MX hotswap socket                  |
| 2   | 4.7 kΩ 0603 (I2C pull-ups, left)         |
| 1   | 100 nF 0603 + 2 × 1 µF 0603              |
| 1   | USB 2.0 C-to-C cable (link, non-e-marked)|
| 8–12| 5×2 mm neodymium magnets (case)          |
| —   | M2 heat-set inserts + screws (case)      |
