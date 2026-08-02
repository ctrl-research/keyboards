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
  including the stepped docking seam and the 8 mm rear brow (link ports
  live there). Left ≤ 128.59 × 84.2 mm, right ≤ 123.83 × 84.2 mm.
- [`kbplacer/*_matrix.kle.json`](kbplacer/) — KLE annotated with `row,col`
  legends for the [kbplacer](https://github.com/adamws/kicad-kbplacer)
  plugin.
- [`lib/gemini.pretty`](lib/) — vendored footprints (marbastlib hotswap +
  stabs, Pico, HRO USB-C, MCP23017/passives from KiCad stock) and 3D
  models; licenses in `lib/licenses/`.

## 3D exports

`docs/gemini/3d/` on the Pages site renders both boards docked/split
(three.js). Re-export after board changes:

```
kicad-cli pcb export glb --subst-models --include-tracks --include-pads \
  --include-zones --user-origin 119.0625x0mm \
  -o raw-left.glb gemini-left/gemini-left.kicad_pcb   # right: no origin arg
npx gltfpack -i raw-left.glb -o docs/gemini/3d/gemini-left.glb -cc -mi -si 0.4 -noq
```

(The +119.0625 mm origin shift puts both halves in one docked frame.
`-noq` matters: quantized output renders at the wrong scale in the viewer.)

## Before fab (rev A checklist)

- [ ] Route both boards (kbplacer placements + seam edge cuts are done)
- [ ] Verify HRO USB-C pad↔pin mapping against the datasheet
- [ ] Series resistors on link D± so a real charger/host can't hurt anything
- [ ] DRC: Pico pin rows sit at y=-3.5 (brow) and y=+14.3 (inter-row
      corridor) — confirm clear of socket pads after any placement nudges
- [ ] Confirm J1 orientation (port opening must overhang the rear edge)
- [ ] Case: ~5 mm pocket under the Pico strip (~2 mm elsewhere), rear
      cutouts for both link ports, side cutout for the Pico micro-USB
