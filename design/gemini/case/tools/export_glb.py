#!/usr/bin/env python3
"""Export the case pieces as GLB for the docs 3D viewer.

Same docked coordinate frame as the PCB GLBs (kicad-cli exports):
  glb_x = docked_x - 119.0625,  glb_y = up,  glb_z = pcb_y
The PCB top face sits at glb_y = 0, so case geometry (z = 0 at interior
floor, PCB top at z = 7.6) shifts down by 7.6 mm.

Run with the case venv: .venv/bin/python tools/export_glb.py
"""
import json
import os
import struct
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_case as g

DOCS = os.path.normpath(os.path.join(
    g.CASE, "..", "..", "..", "docs", "gemini", "3d"))

COLORS = {
    "bottom": cq.Color(0.30, 0.31, 0.34),
    "plate": cq.Color(0.78, 0.74, 0.66),
    "top": cq.Color(0.42, 0.40, 0.38),
}


def glb_bounds(path):
    """Read position accessor bounds from a GLB to sanity-check units."""
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
    mins, maxs = [], []
    for a in doc.get("accessors", []):
        if a.get("type") == "VEC3" and "min" in a:
            mins.append(a["min"])
            maxs.append(a["max"])
    lo = [min(v[i] for v in mins) for i in range(3)]
    hi = [max(v[i] for v in maxs) for i in range(3)]
    return lo, hi


for half in ("left", "right"):
    outline = g.read_outline(half)
    keys = g.read_keys(half)
    solids = {
        "bottom": g.bottom_case(half, outline),
        "plate": g.plate(half, outline, keys),
        "top": g.top_case(half, outline),
    }
    xoff = -119.0625 if half == "left" else 0.0
    asm = cq.Assembly()
    for name, solid in solids.items():
        asm.add(solid.translate((xoff, 0, -7.6)), name=name, color=COLORS[name])
    out = os.path.join(DOCS, f"gemini_{half}_case.glb")
    try:
        asm.export(out)
    except AttributeError:
        asm.save(out)
    lo, hi = glb_bounds(out)
    size = os.path.getsize(out)
    print(f"{half}: {size/1024:.0f} KB  bounds x[{lo[0]:.4g},{hi[0]:.4g}] "
          f"y[{lo[1]:.4g},{hi[1]:.4g}] z[{lo[2]:.4g},{hi[2]:.4g}]")
