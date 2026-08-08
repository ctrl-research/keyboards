#!/usr/bin/env python3
"""Bake a scaled, origin-centred logo footprint from the source artwork.

Source: ../gemini.kicad_mod — bitmap2component output, 35.914 x 13.850 mm,
polygons on F.SilkS. That is far too tall for the 8 mm rear brow, so this
scales every fp_poly vertex about the artwork's bounding-box centre and
writes lib/gemini.pretty/Logo_Gemini.kicad_mod with its origin at the
logo's centre (so placement is just "put the centre here").

TARGET_H is bounded below by silkscreen resolution, not by taste: at 6 mm
the thinnest stroke is 0.40 mm and the tightest counter (the enclosed gap
in the small "by: j6n" glyphs) is 0.22 mm, both comfortably above the
0.15 mm minimum JLCPCB/PCBWay quote for silkscreen. Going much below
~4.5 mm starts closing those counters.

Plain python3 — no pcbnew needed.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DIR = os.path.dirname(HERE)
SRC = os.path.join(PCB_DIR, "gemini.kicad_mod")
DST = os.path.join(PCB_DIR, "lib", "gemini.pretty", "Logo_Gemini.kicad_mod")

TARGET_H = 6.0   # mm, artwork height (brow is 8 mm)


def main():
    src = open(SRC).read()
    pts = [(float(a), float(b))
           for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', src)]
    if not pts:
        raise RuntimeError(f"no polygon vertices found in {SRC}")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = TARGET_H / h

    def xform(m):
        x, y = float(m.group(1)), float(m.group(2))
        return f"(xy {(x - cx) * k:.6f} {(y - cy) * k:.6f})"

    out = re.sub(r'\(xy ([-\d.]+) ([-\d.]+)\)', xform, src)
    out = out.replace('(footprint "LOGO"', '(footprint "Logo_Gemini"')
    # board-only artwork: the reference must not print as stray silk
    out = out.replace(
        '(fp_text reference "G***" (at 0 0) (layer "F.SilkS")',
        '(fp_text reference "G***" (at 0 0) (layer "F.SilkS") hide')
    out = out.replace('(fp_text value "LOGO" (at 0.75 0)',
                      '(fp_text value "Logo_Gemini" (at 0 0)')
    with open(DST, "w") as f:
        f.write(out)
    print(f"{w:.3f} x {h:.3f} mm  x{k:.6f}  ->  "
          f"{w * k:.3f} x {h * k:.3f} mm\n-> {DST}")


if __name__ == "__main__":
    main()
