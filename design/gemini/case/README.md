# case

3D-printable case for both halves — three pieces per half, generated
parametrically by [`tools/gen_case.py`](tools/) (CadQuery) from the same
outline/placement CSVs as the PCBs.

## Stack-up (z from interior floor, per half)

| z (mm)      | What                                                      |
|-------------|-----------------------------------------------------------|
| −3.0 … 0    | bottom case floor                                         |
| 0 … 5.5     | component space (sockets 1.85, Pico stack ≈ 4.5)          |
| 6.0 … 7.6   | PCB (floats — gasket mount, nothing screws into it)       |
| 10.1        | lower gasket ledge (bottom case)                          |
| 11.1 … 12.6 | switch plate (1.5 mm), flange rides the gaskets           |
| 11.8        | bottom-case rim / top-case joint line                     |
| 14.0        | upper gasket press lip (top case underside)               |
| 16.5        | top-case bezel top (caps bottom out ≈ 18)                 |

Gasket: 1.5 mm poron strips above and below the plate's 2.5 mm perimeter
flange, on all edges **except the seam edge**.

## The seam edge (docking side)

Nothing may protrude past the seam plane above PCB level, or the halves
couldn't dock flush. So:

- **Bottom case**: seam wall rises only to z = 4.0 (under the PCB, clear of
  the near-seam hotswap sockets), 3 mm thick *inward*, outer face exactly on
  the seam plane. It carries 4 × Ø3×2 mm magnet pockets (axis horizontal,
  z = 2) whose positions mirror across the halves; polarity alternates N/S
  along the seam so the halves only dock in the correct alignment.
- **Plate and PCB**: extend flush to the seam plane; their edges are the
  visible seam when docked. No gasket on this edge (the plate flange stops).
- **Top case**: C-shaped — open on the seam side, zero material past the
  seam plane.

Docked appearance: caps keep near-normal spacing; below them the two plate
edges and case skirts meet at the stepped seam line.

## Pieces (× left/right)

1. **`*_bottom.stl/.step`** — floor + walls, gasket ledge, magnet pockets,
   port cutouts (host USB-C at left-rear corner L, link USB-C at seam-rear
   corner both halves, micro-USB side cutout L), BOOTSEL finger hole in the
   floor (L), M2 screw pilot bores in the wall tops.
2. **`*_plate.stl/.step`** — gasket-mount plate engineered against
   print-curl (see below): 1.5 mm clip web + 1.2 mm stiffening skirt
   (2.7 mm total), MX cutouts, stab cutouts, perimeter flange (1.5 mm, so
   the gasket stack is unchanged) with notches at the screw columns. Or fab
   flat 1.5 mm FR4/POM/alu from the STEP's top web.
3. **`*_top.stl/.step`** — bezel frame: presses the upper gaskets via its
   inner lip, slim ~2.9 mm bezel, counterbored M2 screws (4/half) from the
   top into the bottom-case wall pilots.

## Fasteners & hardware (per keyboard)

| Qty | Part                          |
|-----|-------------------------------|
| 8   | M2 × 12 screw (top → bottom wall) |
| 8   | Ø3 × 2 mm neodymium magnet (seam, glued, alternating polarity) |
| ~1 m| 1.5 mm poron gasket strip     |

## Printed plates and curl

A thin printed plate bows upward days after switches go in: every MX
switch's clips push outward on their cutout continuously, and 40+ switches
of sustained stress creep a 1.5 mm printed plate into a banana — PLA is the
worst offender. Countermeasures baked into the generator:

- **Clip web + skirt**: MX clips need exactly 1.5 mm of material to latch,
  so the plate keeps a 1.5 mm top web at nominal cutout size, backed by a
  1.2 mm skirt whose openings are relieved to 15.5 mm (clips and housing
  never touch it). ~2.7 mm effective thickness ≈ 6× the bending stiffness
  of a bare 1.5 mm plate, with zero change to how switches seat.
- **Fit tolerance**: `sw_cut` defaults to 14.2 mm because FDM holes print
  undersize. **Print `stl/plate_fit_coupon.stl` first** (three cutouts:
  14.1 / 14.2 / 14.3, engraved) in your actual plate material and
  orientation. Pick the size where a switch clicks in and holds without
  forcing — a too-tight fit is exactly what stores the curling stress. Set
  `P["sw_cut"]`, regenerate.
- **Material**: PETG minimum; ASA/ABS or PC better (higher creep
  resistance). Avoid PLA for the plate. Print flat, 5+ perimeters or 100%
  infill.

## Regenerate

```
cd design/gemini/case
.venv/bin/python tools/gen_case.py     # venv: python3.12 -m venv .venv && .venv/bin/pip install cadquery
```

## Known v0.1 limitations (iterate before committing to a print)

- Stab cutouts are simplified rectangles — replace with proper Cherry
  plate-mount profiles before a metal plate order.
- BOOTSEL hole position is approximate (module-center offset); verify
  against a real Pico.
- No dowel pins yet — magnets + the stepped-seam interlock handle alignment.
- Tenting/feet, bumpon recesses, and the docked-mode pogo idea are future.
