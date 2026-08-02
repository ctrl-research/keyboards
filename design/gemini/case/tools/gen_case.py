#!/usr/bin/env python3
"""Generate the Gemini case pieces (bottom, gasket plate, top frame) x2 halves.

Run with the case venv: .venv/bin/python tools/gen_case.py
Geometry sources: ../pcb/placement/*.csv (outlines + key positions).
Outputs: stl/ and step/ per piece + an assembly STEP per half.

Conventions: input coords are PCB coords (x right, y toward user). CAD uses
y negated (so z points up through the keycaps) to keep parts non-mirrored.
z=0 is the case interior floor.
"""
import csv
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.dirname(HERE)
PCB = os.path.join(os.path.dirname(CASE), "pcb", "placement")

P = dict(
    clear=0.25,          # PCB outline -> cavity wall
    seam_clear=0.05,     # cavity/plate clearance at the seam plane
    wall=4.25,           # PCB outline -> case outer face (non-seam)
    floor=3.0,
    seam_wall_in=3.0,    # seam wall thickness, grown inward under the PCB
    seam_wall_top=4.0,   # keeps clear of near-seam hotswap sockets (z 4.15+)
    pcb_bottom=6.0,
    ledge_z=10.1,        # lower gasket shelf
    rim_z=11.8,          # bottom/top joint line
    plate_z0=11.1, plate_z1=12.6,
    plate_margin=2.5,    # plate flange beyond PCB outline (non-seam)
    plate_pocket=3.0,    # cavity above ledge / top-case pocket (non-seam)
    lip_z=14.0,          # top-case gasket press lip underside
    top_z=16.5,
    bezel_gap=0.4,       # bezel inner edge beyond PCB outline
    sw_cut=14.2,         # MX plate cutout — FDM prints undersize; print
                         # the test coupon and tune before a full plate
    skirt_depth=1.2,     # stiffening skirt below the 1.5 mm clip web
    skirt_inset=1.0,     # skirt stays inside the PCB outline laterally
    relief_cut=15.5,     # skirt-level opening so MX clips/housing clear
    stab_dx=11.938, stab_w=6.8, stab_h=12.5, stab_dy=0.5,
    mag_d=3.2, mag_depth=2.1, mag_z=2.0,
    screw_off=2.25,      # screw column: PCB outline + this (wall centerline)
    pilot_d=1.7, thru_d=2.3, cb_d=4.2, cb_depth=2.0, notch_d=5.5,
)

SEAM_X_MIN_L = 119.0    # left half: seam verts have x >= this
SEAM_X_MAX_R = 9.6      # right half: seam verts have x <= this
ROW_Y = [9.525, 28.575, 47.625, 66.675]
SEAM_X_L = [119.0625, 123.825, 128.5875, 119.0625]
SEAM_X_R = [0.0, 4.7625, 9.525, 0.0]

SCREWS = {
    "left": [(-P["screw_off"], 3.0), (-P["screw_off"], 65.0),
             (60.0, -8.0 - P["screw_off"]), (60.0, 76.2 + P["screw_off"])],
    "right": [(123.825 + P["screw_off"], 3.0), (123.825 + P["screw_off"], 65.0),
              (60.0, -8.0 - P["screw_off"]), (60.0, 76.2 + P["screw_off"])],
}


def read_outline(half):
    with open(os.path.join(PCB, f"gemini_{half}_outline.csv")) as f:
        return [(float(r["x_mm"]), float(r["y_mm"])) for r in csv.DictReader(f)]


def read_keys(half):
    with open(os.path.join(PCB, f"gemini_{half}_placement.csv")) as f:
        return [(float(r["center_x_mm"]), float(r["center_y_mm"]),
                 float(r["width_u"])) for r in csv.DictReader(f)]


def is_seam_edge(p1, p2, half):
    if half == "left":
        return p1[0] >= SEAM_X_MIN_L and p2[0] >= SEAM_X_MIN_L
    return p1[0] <= SEAM_X_MAX_R and p2[0] <= SEAM_X_MAX_R


def offset_poly(verts, half, d_outer, d_seam):
    """Per-edge offset of a rectilinear polygon (PCB coords, y-down).
    Walk order gives outward normal = (dy, -dx). Alternating H/V edges."""
    n = len(verts)
    lines = []  # per edge: ('v', x) or ('h', y) after offsetting
    for i in range(n):
        p1, p2 = verts[i], verts[(i + 1) % n]
        d = d_seam if is_seam_edge(p1, p2, half) else d_outer
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = abs(dx) + abs(dy)
        ox, oy = dy / length, -dx / length
        if dx == 0:
            lines.append(("v", p1[0] + ox * d))
        else:
            lines.append(("h", p1[1] + oy * d))
    out = []
    for i in range(n):
        a, b = lines[i - 1], lines[i]
        if a[0] == b[0]:
            raise ValueError("outline edges must alternate H/V")
        x = a[1] if a[0] == "v" else b[1]
        y = a[1] if a[0] == "h" else b[1]
        out.append((x, y))
    return out


def wp_poly(pts, z0, z1):
    """Extrude a polygon (PCB coords) between absolute z levels."""
    cad = [(x, -y) for x, y in pts]
    return (cq.Workplane("XY", origin=(0, 0, z0))
            .polyline(cad).close().extrude(z1 - z0))


def box(x0, x1, y0, y1, z0, z1):
    return wp_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def xcyl(x0, x1, y, z, d):
    """Cylinder along X (for magnet pockets)."""
    return (cq.Workplane("YZ", origin=(x0, -y, z))
            .circle(d / 2).extrude(x1 - x0))


def zcyl(x, y, z0, z1, d):
    return (cq.Workplane("XY", origin=(x, -y, z0))
            .circle(d / 2).extrude(z1 - z0))


def bottom_case(half, outline):
    o = P
    outer = offset_poly(outline, half, o["wall"], 0.0)
    cav_low = offset_poly(outline, half, o["clear"], -o["seam_wall_in"])
    cav_mid = offset_poly(outline, half, o["clear"], o["seam_clear"])
    cav_top = offset_poly(outline, half, o["plate_pocket"], o["seam_clear"])

    body = wp_poly(outer, -o["floor"], o["rim_z"])
    body = body.cut(wp_poly(cav_low, 0, o["seam_wall_top"]))
    body = body.cut(wp_poly(cav_mid, o["seam_wall_top"], o["ledge_z"]))
    body = body.cut(wp_poly(cav_top, o["ledge_z"], o["rim_z"] + 1))

    # magnet pockets in the seam wall
    seam_x = SEAM_X_L if half == "left" else SEAM_X_R
    for y, sx in zip(ROW_Y, seam_x):
        if half == "left":
            body = body.cut(xcyl(sx - o["mag_depth"], sx + 0.01, y, o["mag_z"], o["mag_d"]))
        else:
            body = body.cut(xcyl(sx - 0.01, sx + o["mag_depth"], y, o["mag_z"], o["mag_d"]))

    # port cutouts through the rear wall (connectors hang below PCB @ z 2.8-6)
    def rear_port(cx):
        return box(cx - 5.5, cx + 5.5, -8.0 - o["wall"] - 1, -8.0 + 1.5, 2.3, 6.3)

    if half == "left":
        body = body.cut(rear_port(9.5))        # host USB-C
        body = body.cut(rear_port(110.0))      # link USB-C
        # Pico micro-USB out the left side wall (z 0.1-4.0)
        body = body.cut(box(-o["wall"] - 1, 1.0, 28.575 - 5.0, 28.575 + 5.0, 0.1, 4.0))
        # BOOTSEL access through the floor
        body = body.cut(zcyl(32.0, 28.575, -o["floor"] - 1, 0.5, 8.0))
    else:
        body = body.cut(rear_port(9.5))        # link USB-C (seam corner)

    # screw pilots in the wall tops
    for sx, sy in SCREWS[half]:
        body = body.cut(zcyl(sx, sy, 2.0, o["ledge_z"] + 0.01, o["pilot_d"]))
    return body


def plate(half, outline, keys):
    """1.5 mm clip web (MX clips need exactly 1.5 mm to latch) + a
    stiffening skirt below with relieved openings — printed plates curl
    under the sustained clip force of 40+ switches without it."""
    o = P
    poly = offset_poly(outline, half, o["plate_margin"], 0.0)
    pl = wp_poly(poly, o["plate_z0"], o["plate_z1"])
    skirt_poly = offset_poly(outline, half, -o["skirt_inset"], -o["skirt_inset"])
    pl = pl.union(wp_poly(skirt_poly, o["plate_z0"] - o["skirt_depth"], o["plate_z0"] + 0.01))
    for cx, cy, w in keys:
        pl = pl.cut(box(cx - o["sw_cut"] / 2, cx + o["sw_cut"] / 2,
                        cy - o["sw_cut"] / 2, cy + o["sw_cut"] / 2,
                        o["plate_z0"] - 0.001, o["plate_z1"] + 1))
        pl = pl.cut(box(cx - o["relief_cut"] / 2, cx + o["relief_cut"] / 2,
                        cy - o["relief_cut"] / 2, cy + o["relief_cut"] / 2,
                        o["plate_z0"] - o["skirt_depth"] - 1, o["plate_z0"]))
        if w >= 2.0:
            for sgn in (-1, 1):
                sx = cx + sgn * o["stab_dx"]
                pl = pl.cut(box(sx - o["stab_w"] / 2, sx + o["stab_w"] / 2,
                                cy + o["stab_dy"] - o["stab_h"] / 2,
                                cy + o["stab_dy"] + o["stab_h"] / 2,
                                o["plate_z0"] - 0.001, o["plate_z1"] + 1))
                pl = pl.cut(box(sx - o["stab_w"] / 2 - 1, sx + o["stab_w"] / 2 + 1,
                                cy + o["stab_dy"] - o["stab_h"] / 2 - 1,
                                cy + o["stab_dy"] + o["stab_h"] / 2 + 1,
                                o["plate_z0"] - o["skirt_depth"] - 1, o["plate_z0"]))
    for sx, sy in SCREWS[half]:
        pl = pl.cut(zcyl(sx, sy, o["plate_z0"] - o["skirt_depth"] - 1,
                         o["plate_z1"] + 1, o["notch_d"]))
    return pl


def fit_coupon():
    """Test strip with three cutout sizes — print flat in your plate
    material, click a switch into each, pick the size that grips without
    force, set P['sw_cut'] to it, regenerate."""
    o = P
    sizes = [14.1, 14.2, 14.3]
    pitch = 24.0
    w429 = len(sizes) * pitch
    body = box(0, w429, 0, 24, 0, 1.5)
    body = body.union(box(1.5, w429 - 1.5, 1.5, 22.5, -o["skirt_depth"], 0.01))
    for i, sz in enumerate(sizes):
        cx, cy = pitch / 2 + i * pitch, 12.0
        body = body.cut(box(cx - sz / 2, cx + sz / 2, cy - sz / 2, cy + sz / 2, -0.001, 2))
        body = body.cut(box(cx - o["relief_cut"] / 2, cx + o["relief_cut"] / 2,
                            cy - o["relief_cut"] / 2, cy + o["relief_cut"] / 2,
                            -o["skirt_depth"] - 1, 0))
        tag = (cq.Workplane("XY", origin=(cx, -2.6, 1.5))
               .text(f"{sz}", 3.2, -0.5, halign="center", valign="center"))
        body = body.cut(tag)
    return body


def top_case(half, outline):
    o = P
    outer = offset_poly(outline, half, o["wall"], 0.0)
    opening = offset_poly(outline, half, o["bezel_gap"], 2.0)   # open at seam
    pocket = offset_poly(outline, half, o["plate_pocket"], 2.0)

    body = wp_poly(outer, o["rim_z"], o["top_z"])
    body = body.cut(wp_poly(opening, o["rim_z"] - 1, o["top_z"] + 1))
    body = body.cut(wp_poly(pocket, o["rim_z"] - 0.01, o["lip_z"]))
    for sx, sy in SCREWS[half]:
        body = body.cut(zcyl(sx, sy, o["rim_z"] - 1, o["top_z"] + 1, o["thru_d"]))
        body = body.cut(zcyl(sx, sy, o["top_z"] - o["cb_depth"], o["top_z"] + 1, o["cb_d"]))
    return body


def export(solid, name, drop_to_bed=True):
    os.makedirs(os.path.join(CASE, "stl"), exist_ok=True)
    os.makedirs(os.path.join(CASE, "step"), exist_ok=True)
    s = solid
    if drop_to_bed:
        zmin = s.val().BoundingBox().zmin
        s = s.translate((0, 0, -zmin))
    cq.exporters.export(s, os.path.join(CASE, "stl", f"{name}.stl"))
    cq.exporters.export(s, os.path.join(CASE, "step", f"{name}.step"))
    print(f"  {name}: ok")


def main():
    export(fit_coupon(), "plate_fit_coupon")
    for half in ("left", "right"):
        print(f"{half}:")
        outline = read_outline(half)
        keys = read_keys(half)
        b = bottom_case(half, outline)
        p = plate(half, outline, keys)
        t = top_case(half, outline)
        export(b, f"gemini_{half}_bottom")
        export(p, f"gemini_{half}_plate")
        export(t, f"gemini_{half}_top")
        asm = cq.Assembly()
        asm.add(b, name="bottom", color=cq.Color(0.35, 0.35, 0.38))
        asm.add(p, name="plate", color=cq.Color(0.75, 0.72, 0.65))
        asm.add(t, name="top", color=cq.Color(0.45, 0.42, 0.4))
        asm.save(os.path.join(CASE, "step", f"gemini_{half}_assembly.step"))
        print(f"  gemini_{half}_assembly.step: ok")


if __name__ == "__main__":
    main()
