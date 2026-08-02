# Gemini

A split, row-staggered 40% whose two halves dock together to form a regular
staggered 40%. Two boards, one keyboard — hence Gemini (and it's a *mini*).

## Concept

- One Raspberry Pi Pico drives the whole board from the left half; the right
  half is passive (I/O expander) and links over a USB-C cable carrying I2C.
- Apart: a classic two-piece ergo split you can tent and shoulder-width.
- Docked: the halves mate along a staggered seam and become a conventional
  12.75u × 4u 40% (MiniVan-class footprint), visually indistinguishable from a
  one-piece board.
- The row stagger is the joint: the seam steps rightward as it descends, so the
  halves interlock like puzzle pieces instead of meeting at a straight line.

## Docked layout (12.75u × 4u)

```
|Tab  | Q | W | E | R | T ‖ Y | U | I | O | P | Bksp |
|Ctrl  | A | S | D | F | G ‖ H | J | K | L | ; | Ent |
|Shift   | Z | X | C | V | B ‖ N | M | , | . | Shift  |
|Ctl |Gui|Alt |   Space    ‖   Space   | Fn | Alt |Ctl|
```

`‖` marks the seam. Widths are approximate above; exact geometry below.

### Row geometry (units of u, x measured from left edge)

| Row | Left half                                  | Seam x | Right half                                     |
|-----|--------------------------------------------|--------|------------------------------------------------|
| 1   | Tab 1.25 · Q W E R T (5×1u)                | 6.25   | Y U I O P (5×1u) · Bksp 1.5                    |
| 2   | Ctrl 1.5 · A S D F G (5×1u)                | 6.50   | H J K L ; (5×1u) · Enter 1.25                  |
| 3   | Shift 1.75 · Z X C V B (5×1u)              | 6.75   | N M , . (4×1u) · Shift 2                       |
| 4   | Ctrl 1.25 · GUI 1 · Alt 1.25 · Space 2.75  | 6.25   | Space 2.75 · Fn 1.25 · Alt 1.25 · Ctrl 1.25    |

Every row totals 12.75u. Standard row stagger (Tab 1.25 → Ctrl 1.5 → Shift
1.75) so the docked board reads as a normal staggered 40%.

### Seam path

Tracing the boundary of the left half from the top edge down
(coordinates in u, origin at top-left of the docked board):

```
(6.25, 0) → (6.25, 1) → (6.50, 1) → (6.50, 2) → (6.75, 2)
→ (6.75, 3) → (6.25, 3) → (6.25, 4)
```

Rows 1–3 step 0.25u right per row (following the alpha stagger); row 4 steps
back to 6.25 at the split spacebars, giving the right half a 0.5u tooth that
hooks under the left half's row 3 — a natural mechanical interlock.

### Dimensions (1u = 19.05 mm)

| Piece       | Width               | Depth                  |
|-------------|---------------------|------------------------|
| Docked      | 12.75u = 242.9 mm   | 4u + 8 mm brow = 84.2 mm |
| Left half   | 6.25–6.75u = 119.1–128.6 mm | 84.2 mm        |
| Right half  | 6.00–6.50u = 114.3–123.8 mm | 84.2 mm        |

The 8 mm rear "brow" above row 0 hosts the USB-C link ports (and the
Pico's micro-USB reach); the seam runs straight through it at 6.25u. The
key field itself stays exactly 4u deep.

(Plus case wall thickness on the non-seam edges; the seam faces should sit
flush metal-to-metal / plastic-to-plastic.)

## Split & docking mechanism (proposal)

- **Alignment**: the stepped seam self-aligns in x/y; add 2 press-fit dowel
  pins + receivers on the seam faces for z alignment.
- **Retention**: 4–6 pairs of 5×2 mm neodymium magnets embedded in the seam
  faces (polarity keyed so the halves only mate the correct way).
- **Electrical**:
  - One controller: a Raspberry Pi Pico on the left half (header-mounted on
    the back); the right half is passive with an MCP23017 I/O expander.
  - Halves link over **USB-C carrying I2C** (3V3/SDA/SCL/GND) — any USB 2.0
    C-to-C cable, orientation-proof. Works docked and split.
  - Stretch goal: spring-loaded pogo pins in the row-2/3 seam faces carrying
    the same 4 signals so docking needs no cable at all.
  - Details: [`pcb/pinmap.md`](pcb/pinmap.md).

## Matrix

Both halves are electrically 4×6 (left scanned by the Pico, right read over
I2C via the expander):

| Half  | R1        | R2        | R3        | R4                    |
|-------|-----------|-----------|-----------|------------------------|
| Left  | 6 keys    | 6 keys    | 6 keys    | 4 keys (2 cols unused) |
| Right | 6 keys    | 6 keys    | 5 keys    | 4 keys                 |

## Default keymap

See [`layout/keymap.md`](layout/keymap.md) — Base + Raise (hold right `Fn`)
+ Lower (hold left `Space`) + Adjust, MiniVan conventions, vim arrows on
`HJKL`, full 104-key coverage.

## Keycap compatibility

All sizes are standard: 1u, 1.25u, 1.5u, 1.75u, 2u, 2.75u. Notes:

- 2.75u "spacebars" are usually sold as right-Shift caps — fine in uniform
  profiles (DSA/XDA/KAT uniform); sculpted sets will have R2 shift profile.
- 1.25u Enter is a standard size but a rare legend; blanks or novelty caps.

## Project structure

- [`layout/`](layout/) — KLE layouts (docked + split, importable at
  keyboard-layout-editor.com) and the default keymap layer maps; VIA
  definition lands here too.
- [`pcb/`](pcb/) — KiCad projects for both halves.
- [`case/`](case/) — 3D-printed case CAD + STL/STEP exports.
- [`firmware/`](firmware/) — QMK keyboard definition, VIA support, built
  `.uf2` images.

## Open questions

- [ ] Split space sizes: 2.75/2.75 as drawn, or asymmetric (e.g. 2.25 + Fn on
      left thumb) for a dedicated layer key on the seam?
- [ ] Right Shift 2u vs. 1u Shift + dedicated `/` or `↑`?
- [ ] Pogo pins vs. cable-only for docked mode?
- [ ] Rotary encoder in place of a 1u mod on each half?
- [ ] Case: tray-mount 3DP first article, then CNC alu gasket for v2?
