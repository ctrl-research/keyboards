# Gemini

A split, row-staggered 40% whose two halves dock together to form a regular
staggered 40%. Two boards, one keyboard — hence Gemini (and it's a *mini*).

## Concept

- Each half is a standalone wired/split keyboard half with its own controller.
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

| Piece       | Width               | Height        |
|-------------|---------------------|---------------|
| Docked      | 12.75u = 242.9 mm   | 4u = 76.2 mm  |
| Left half   | 6.25–6.75u = 119.1–128.6 mm | 4u    |
| Right half  | 6.00–6.50u = 114.3–123.8 mm | 4u    |

(Plus case wall thickness on the non-seam edges; the seam faces should sit
flush metal-to-metal / plastic-to-plastic.)

## Split & docking mechanism (proposal)

- **Alignment**: the stepped seam self-aligns in x/y; add 2 press-fit dowel
  pins + receivers on the seam faces for z alignment.
- **Retention**: 4–6 pairs of 5×2 mm neodymium magnets embedded in the seam
  faces (polarity keyed so the halves only mate the correct way).
- **Electrical**:
  - Primary: TRRS or 4-pin JST between halves (works docked *and* split — one
    short jumper when docked, a long cable when split).
  - Stretch goal: spring-loaded pogo pins in the row-2/3 seam faces so docking
    needs no cable at all; TRRS remains the split-mode link.
- **Controllers**: one per half (RP2040 class, e.g. Sea-Picro / Elite-Pi
  footprint), USB-C on each half's rear edge. Left is default master; QMK
  `SPLIT_USB_DETECT` so either side can take USB.

## Matrix

Both halves are electrically 4×6:

| Half  | R1        | R2        | R3        | R4                    |
|-------|-----------|-----------|-----------|------------------------|
| Left  | 6 keys    | 6 keys    | 6 keys    | 4 keys (2 cols unused) |
| Right | 6 keys    | 6 keys    | 5 keys    | 4 keys                 |

## Default keymap sketch

Base layer as shown above. `/` lives on Fn+`.`, quote on Fn+`;` (MiniVan
conventions). Two Fn-style layers off the right `Fn` key and dual-role left
`Space` (hold) to be tuned later:

- **Fn (Raise)**: numbers on row 1, symbols on row 2, arrows on `HJKL`… or
  `IJKL` — TBD.
- **Lower**: F-keys, media, RGB/board controls.

## Keycap compatibility

All sizes are standard: 1u, 1.25u, 1.5u, 1.75u, 2u, 2.75u. Notes:

- 2.75u "spacebars" are usually sold as right-Shift caps — fine in uniform
  profiles (DSA/XDA/KAT uniform); sculpted sets will have R2 shift profile.
- 1.25u Enter is a standard size but a rare legend; blanks or novelty caps.

## Files

- `gemini_docked.kle.json` — docked layout, importable at
  keyboard-layout-editor.com (halves color-coded).
- `gemini_split.kle.json` — same layout with the halves separated 0.75u.

## Open questions

- [ ] Split space sizes: 2.75/2.75 as drawn, or asymmetric (e.g. 2.25 + Fn on
      left thumb) for a dedicated layer key on the seam?
- [ ] Right Shift 2u vs. 1u Shift + dedicated `/` or `↑`?
- [ ] Pogo pins vs. cable-only for docked mode?
- [ ] Rotary encoder in place of a 1u mod on each half?
- [ ] Case: tray-mount 3DP first article, then CNC alu gasket for v2?
