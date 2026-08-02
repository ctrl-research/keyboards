#!/usr/bin/env python3
"""Generate PCB placement data for Gemini from the canonical layout geometry.

Outputs (into design/gemini/pcb/):
  placement/gemini_{left,right}_placement.csv  - switch centers in mm
  placement/gemini_{left,right}_outline.csv    - edge-cut polygon vertices in mm
  kbplacer/gemini_{left,right}_matrix.kle.json - KLE annotated with row,col for kbplacer
"""
import csv
import json
import os

U = 19.05  # mm per key unit
OUT = "/Users/jonathan.ng/projects/keyboards/design/gemini/pcb"

# (legend, width_u) per row; x offsets are cumulative from the half's local origin.
# Left half local origin == docked origin. Right half local origin is x=6.25u docked.
LEFT_ROWS = [
    [("Tab", 1.25), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1)],
    [("Esc/Ctrl", 1.5), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1)],
    [("Shift", 1.75), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1)],
    [("Ctrl", 1.25), ("GUI", 1), ("Alt", 1.25), ("Space", 2.75)],
]
# Right half: row start offsets relative to local origin (seam stagger)
RIGHT_ROWS = [
    (0.00, [("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("Bksp", 1.5)]),
    (0.25, [("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("Enter", 1.25)]),
    (0.50, [("N", 1), ("M", 1), (",", 1), (".", 1), ("Shift", 2)]),
    (0.00, [("Space", 2.75), ("Fn", 1.25), ("Alt", 1.25), ("Ctrl", 1.25)]),
]
SEAM = [6.25, 6.50, 6.75, 6.25]  # docked seam x per row, in u
BOARD_W, BOARD_H = 12.75, 4.0
BROW_MM = 8.0            # rear strip above row 0 hosting the USB-C link ports
BROW_U = BROW_MM / U


def keys(rows, right=False):
    """Yield (row, col, legend, width_u, x_u, y_u) with x from the half's local origin."""
    for r, row in enumerate(rows):
        x = row[0] if right else 0.0
        keyseq = row[1] if right else row
        for c, (legend, w) in enumerate(keyseq):
            yield r, c, legend, w, x, float(r)
            x += w


def write_placement(name, rows, right=False):
    path = os.path.join(OUT, "placement", f"gemini_{name}_placement.csv")
    with open(path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["ref", "legend", "matrix_row", "matrix_col",
                      "width_u", "center_x_mm", "center_y_mm"])
        n = 0
        for r, c, legend, w, x, y in keys(rows, right):
            n += 1
            wtr.writerow([f"SW{r}{c}", legend, r, c, w,
                          round((x + w / 2) * U, 3), round((y + 0.5) * U, 3)])
    return n, path


def write_outline(name, verts_u):
    path = os.path.join(OUT, "placement", f"gemini_{name}_outline.csv")
    with open(path, "w", newline="") as f:
        wtr = csv.writer(f)
        wtr.writerow(["x_mm", "y_mm"])
        for x, y in verts_u:
            wtr.writerow([round(x * U, 4), round(y * U, 4)])
    return path


def seam_steps(local_offset=0.0):
    """Seam polyline top->bottom in local coords."""
    pts = []
    for i, s in enumerate(SEAM):
        pts.append((s - local_offset, float(i)))
        pts.append((s - local_offset, float(i + 1)))
    return pts


def kle_matrix(name, rows, right=False):
    """KLE json with 'row,col' legends for kbplacer net/footprint mapping."""
    out = [{"name": f"Gemini {name} (matrix-annotated for kbplacer)"}]
    for r, row in enumerate(rows):
        kle_row = []
        offset = row[0] if right else 0.0
        keyseq = row[1] if right else row
        for c, (_legend, w) in enumerate(keyseq):
            props = {}
            if c == 0 and offset:
                props["x"] = offset
            if w != 1:
                props["w"] = w
            if props:
                kle_row.append(props)
            kle_row.append(f"{r},{c}")
        out.append(kle_row)
    path = os.path.join(OUT, "kbplacer", f"gemini_{name}_matrix.kle.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    return path


os.makedirs(os.path.join(OUT, "placement"), exist_ok=True)
os.makedirs(os.path.join(OUT, "kbplacer"), exist_ok=True)

# Left outline: CCW-ish from top-left, seam on the right side. The rear brow
# extends the top edge to y = -BROW_U; the seam runs straight through it.
left_seam = seam_steps()
left_seam[0] = (left_seam[0][0], -BROW_U)
left_outline = [(0.0, -BROW_U)] + left_seam + [(0.0, BOARD_H)]
# Right outline in local coords (origin at docked x=6.25u): seam on the left side
right_seam = seam_steps(local_offset=6.25)
right_seam[0] = (right_seam[0][0], -BROW_U)
right_w = BOARD_W - 6.25  # 6.5u
# start top-right, go down the right edge, back up the seam
right_outline = [(right_w, -BROW_U), (right_w, BOARD_H)] + right_seam[::-1]

nl, _ = write_placement("left", LEFT_ROWS)
nr, _ = write_placement("right", RIGHT_ROWS, right=True)
write_outline("left", left_outline)
write_outline("right", right_outline)
kle_matrix("left", LEFT_ROWS)
kle_matrix("right", RIGHT_ROWS, right=True)

print(f"left keys: {nl}, right keys: {nr}, total: {nl + nr}")
print(f"left max width: {max(SEAM) * U:.4f} mm, right width: {right_w * U:.4f} mm, "
      f"depth: {BOARD_H * U + BROW_MM:.1f} mm (incl {BROW_MM} mm brow)")
