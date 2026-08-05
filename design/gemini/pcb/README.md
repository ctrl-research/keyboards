# pcb

KiCad projects for the Gemini PCBs — one board per half.

**Architecture (rev A): one controller.** A single Raspberry Pi Pico on the
left half (header-mounted on the back, ~2.5 mm standoff); the right half is
passive with an MCP23017 I/O expander. The halves link over **USB-C
carrying I2C** (3V3/SDA/SCL/GND — any USB 2.0 C-to-C cable). Full pin map,
link wiring, socket-DNP keys and BOM: [`pinmap.md`](pinmap.md).

## Generated projects

- [`gemini-left/`](gemini-left/), [`gemini-right/`](gemini-right/) —
  generated `.kicad_pcb` per half: all footprints placed, nets assigned,
  seam edge cuts drawn. **Unrouted** — routing is interactive work.
- [`gemini-panel/`](gemini-panel/) — **production panel** for JLCPCB/PCBWay:
  both halves in one board, joined along their straight *outer* edges at
  x = 0 with a single **V-score** snap line (the stepped seam can't be
  V-scored — it faces outward and is routed normally). Refs and nets are
  prefixed `L_`/`R_`. Route the individual halves first, then regenerate —
  or route the panel directly and it supersedes them. When ordering: pick
  "panel by customer", 2 designs, and note "V-cut where marked" in remarks.
  Snapped V-score edges land inside the case (the seam-inset walls cover
  all board edges), so no cosmetic cleanup matters.
- Regenerate with KiCad's bundled python (wx workaround included):

  ```
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/gen_kicad_boards.py
  ```

## Inputs (source of truth: `../layout/gemini_docked.kle.json`)

- [`tools/gen_pcb_data.py`](tools/) — derives everything below from the
  layout geometry; [`tools/gen_kicad_boards.py`](tools/) builds the boards.
- [`placement/*_placement.csv`](placement/) — switch centers in mm with
  matrix row/col (per-half origin at its top-left corner).
- [`placement/*_outline.csv`](placement/) — Edge.Cuts vertices in mm
  including the stepped docking seam (inset 1.45 mm from the key boundary —
  the case seam wall carries the true boundary) and the 8 mm rear brow
  (link ports live there). Left ≤ 127.14 × 84.2 mm, right ≤ 122.38 × 84.2 mm.
- [`kbplacer/*_matrix.kle.json`](kbplacer/) — KLE annotated with `row,col`
  legends for the [kbplacer](https://github.com/adamws/kicad-kbplacer)
  plugin.
- [`lib/gemini.pretty`](lib/) — vendored footprints (marbastlib hotswap +
  stabs, Pico, HRO USB-C, MCP23017/passives from KiCad stock) and 3D
  models; licenses in `lib/licenses/`.

## 3D exports

The docs page's **3D model tab** (`docs/gemini/#model`) renders the full
assembly — boards + case pieces, docked/split and exploded/assembled
(three.js; GLBs live in `docs/gemini/3d/`). Re-export after board changes:

```
kicad-cli pcb export glb --subst-models --include-tracks --include-pads \
  --include-zones --user-origin 119.0625x0mm \
  -o raw-left.glb gemini-left/gemini-left.kicad_pcb   # right: no origin arg
npx gltfpack -i raw-left.glb -o docs/gemini/3d/gemini-left.glb -cc -mi -si 0.4 -noq
```

(The +119.0625 mm origin shift puts both halves in one docked frame.
`-noq` matters: quantized output renders at the wrong scale in the viewer.)

## Before fab (rev A checklist)

- [x] Route both boards (autorouted + USB-C escapes rebuilt by hand: the
      generated nested stitch fenced the inner nets on B.Cu, so each link
      /host connector now fans out through 0.6/0.3 vias to F.Cu; DRC: 0
      unconnected on both halves and the panel)
- [ ] Verify HRO USB-C pad↔pin mapping against the datasheet (incl. which
      pads are CC vs SBU — the LED chain crosses on CC)
- [ ] Verify SK6812 MINI-E pad order (assumed 1=VDD 2=DOUT 3=VSS 4=DIN)
- [ ] Host port TP1/TP2 pads: bridge to Pico underside TP3 (D+) / TP2 (D−)
      — decide jumper wires vs relocating pads under the TPs for spring pins
- [ ] Series resistors on link D± so a real charger/host can't hurt anything
- [ ] QMK: cap `RGB_MATRIX_MAXIMUM_BRIGHTNESS` (~120) — 43 LEDs at full
      white would far exceed a 500 mA USB 2.0 budget
- [ ] DRC: Pico pin rows sit at y=19.7 and y=37.5, in the corridors between
      switch rows on both faces — confirm clearances after any nudges
- [ ] Confirm J1 orientation (port opening must overhang the rear edge)
- [ ] Case: ~5 mm pocket under the Pico strip (~2 mm elsewhere), rear
      cutouts for both link ports, side cutout for the Pico micro-USB
