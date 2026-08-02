#!/usr/bin/env python3
"""Generate KiCad boards for Gemini (left/right halves) from placement CSVs.

Architecture (rev A): ONE Raspberry Pi Pico on the left half; the right half
is passive with an MCP23017 I/O expander. Halves link over USB-C carrying
I2C (VBUS=3V3, D+=SDA, D-=SCL) — any USB 2.0 C-to-C cable works.

Run with KiCad's bundled python3 (needs pcbnew). Produces per half:
  pcb/gemini-<half>/gemini-<half>.kicad_pcb  - footprints placed + netlisted
  pcb/gemini-<half>/fp-lib-table             - points at ../lib/gemini.pretty
Unrouted by design: routing happens interactively in KiCad.

All 43 keys are hotswap. The Pico mounts on ~2.5 mm low-profile headers
(NOT flat/castellated): switch pins (~1.7 mm) and hotswap sockets (1.85 mm)
clear underneath. The USB-C link ports live in an 8 mm rear "brow" strip
above row 0 (see gen_pcb_data.py), clear of all socket zones.
"""
import csv
import os

import wx
import pcbnew
from pcbnew import VECTOR2I_MM, FromMM

_app = wx.App()  # pcbnew's settings manager needs a wx app outside the GUI

PCB_DIR = "/Users/jonathan.ng/projects/keyboards/design/gemini/pcb"
LIB = os.path.join(PCB_DIR, "lib", "gemini.pretty")

SW_FP = {  # width_u -> hotswap footprint name
    1.0: "SW_MX_HS_CPG151101S11_1u",
    1.25: "SW_MX_HS_CPG151101S11_1.25u",
    1.5: "SW_MX_HS_CPG151101S11_1.5u",
    1.75: "SW_MX_HS_CPG151101S11_1.75u",
    2.0: "SW_MX_HS_CPG151101S11_1u",    # 2u/2.75u use 1u footprint + stab
    2.75: "SW_MX_HS_CPG151101S11_1u",
}
STAB_FP = {2.0: "STAB_MX_2u", 2.75: "STAB_MX_2.75u"}

# Pico physical pin -> net (left half only). GP0/GP1 = I2C0 SDA/SCL.
PICO_PINS = {
    "1": "SDA", "2": "SCL",
    "4": "ROW0", "5": "ROW1", "6": "ROW2", "7": "ROW3",
    "9": "COL0", "10": "COL1", "11": "COL2", "12": "COL3",
    "14": "COL4", "15": "COL5",
    "3": "GND", "8": "GND", "13": "GND", "18": "GND", "23": "GND",
    "28": "GND", "33": "GND", "38": "GND", "42": "GND",
    "36": "+3V3",
}

# MCP23017 SOIC-28 pin -> net (right half only).
MCP_PINS = {
    "1": "COL0", "2": "COL1", "3": "COL2", "4": "COL3",   # GPB0-3
    "5": "COL4", "6": "COL5",                              # GPB4-5
    "9": "+3V3", "10": "GND",
    "12": "SCL", "13": "SDA",
    "15": "GND", "16": "GND", "17": "GND",                 # A0-A2 = addr 0x20
    "18": "+3V3",                                          # /RESET tied high
    "21": "ROW0", "22": "ROW1", "23": "ROW2", "24": "ROW3", # GPA0-3
}

# HRO TYPE-C-31-M-12 (12 pads L->R + 13 shield). Pads 1/12 GND, 2/11 VBUS;
# middle D pairs tied A+B so any cable orientation works. VERIFY against the
# HRO datasheet before fab.
USBC_PINS = {
    "1": "GND", "12": "GND", "13": "GND",
    "2": "+3V3", "11": "+3V3",
    "6": "SDA", "7": "SDA",   # D+ (A6/B6)
    "5": "SCL", "8": "SCL",   # D- (A7/B7)
}


def read_placement(half):
    path = os.path.join(PCB_DIR, "placement", f"gemini_{half}_placement.csv")
    with open(path) as f:
        return list(csv.DictReader(f))


def read_outline(half):
    path = os.path.join(PCB_DIR, "placement", f"gemini_{half}_outline.csv")
    with open(path) as f:
        return [(float(r["x_mm"]), float(r["y_mm"])) for r in csv.DictReader(f)]


def flip_to_back(fp):
    try:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except (AttributeError, TypeError):
        fp.Flip(fp.GetPosition(), True)


def build(half):
    out_dir = os.path.join(PCB_DIR, f"gemini-{half}")
    os.makedirs(out_dir, exist_ok=True)
    pcb_path = os.path.join(out_dir, f"gemini-{half}.kicad_pcb")

    board = pcbnew.BOARD()
    board.SetFileName(pcb_path)
    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    def load(fpname):
        fp = pcbnew.FootprintLoad(LIB, fpname)
        if fp is None:
            raise RuntimeError(f"footprint not found: {fpname}")
        return fp

    def assign(fp, padnum, netname):
        for pad in fp.Pads():
            if pad.GetNumber() == str(padnum):
                pad.SetNet(net(netname))

    def place(fpname, ref, value, x, y, rot=0, back=True, pins=None):
        fp = load(fpname)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPosition(VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        if back:
            flip_to_back(fp)  # Flip segfaults unless the footprint is on a board
        for pin, netname in (pins or {}).items():
            assign(fp, pin, netname)
        return fp

    # --- switches, diodes, stabs ---
    for row in read_placement(half):
        r, c = row["matrix_row"], row["matrix_col"]
        w = float(row["width_u"])
        cx, cy = float(row["center_x_mm"]), float(row["center_y_mm"])
        keynet = f"N_SW{r}{c}"
        # marbastlib hotswap footprints are authored in bottom-view coords
        # (mirrored pin holes, pads on F.Cu) and must be placed flipped so
        # the socket sits on the back and pads land on B.Cu.
        place(SW_FP[w], f"SW{r}{c}", row["legend"], cx, cy, back=True,
              pins={"1": f"COL{c}", "2": keynet})
        place("D_SOD-123", f"D{r}{c}", "1N4148W", cx - 4.0, cy + 7.4, rot=180,
              back=True, pins={"1": f"ROW{r}", "2": keynet})  # cathode->row
        if w in STAB_FP:
            place(STAB_FP[w], f"ST_SW{r}{c}", f"stab {w}u", cx, cy, back=False)

    # --- half-specific electronics (all on the back) ---
    if half == "left":
        # Pico horizontal across the brow/row-0 boundary, micro-USB out the
        # left side edge. Header-mounted (~2.5 mm standoff). Its two TH pin
        # rows land at y=-3.5 (in the brow) and y=+14.3 (the corridor between
        # row 0's socket pads and row 1's sockets) — clear of all drills/pads.
        place("RPi_Pico_SMD_TH", "U1", "Raspberry Pi Pico", 26.0, 5.4, rot=90,
              pins=PICO_PINS)
        # Link port in the brow, near the seam.
        place("HRO-TYPE-C-31-M-12-Assembly", "J1", "USB-C link", 110.0, -3.5,
              pins=USBC_PINS)
        place("R_0603_1608Metric", "R1", "4k7", 58.0, -3.5,
              pins={"1": "SDA", "2": "+3V3"})
        place("R_0603_1608Metric", "R2", "4k7", 63.0, -3.5,
              pins={"1": "SCL", "2": "+3V3"})
    else:
        # Passive half: MCP23017 in the socket-free strip beside the spacebar.
        place("SOIC-28W_7.5x17.9mm_P1.27mm", "U1", "MCP23017-E/SO", 46.0, 66.5,
              pins=MCP_PINS)
        # Link port in the brow, near the seam.
        place("HRO-TYPE-C-31-M-12-Assembly", "J1", "USB-C link", 9.5, -3.5,
              pins=USBC_PINS)
        place("C_0603_1608Metric", "C1", "100nF", 46.0, 56.5,
              pins={"1": "+3V3", "2": "GND"})

    # --- edge cuts ---
    verts = read_outline(half)
    for (x1, y1), (x2, y2) in zip(verts, verts[1:] + verts[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(VECTOR2I_MM(x1, y1))
        seg.SetEnd(VECTOR2I_MM(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(FromMM(0.1))
        board.Add(seg)

    pcbnew.SaveBoard(pcb_path, board)

    with open(os.path.join(out_dir, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 9)\n'
                '  (lib (name "gemini")(type "KiCad")'
                '(uri "${KIPRJMOD}/../lib/gemini.pretty")(options "")'
                '(descr "Gemini vendored footprints"))\n)\n')

    check = pcbnew.LoadBoard(pcb_path)
    print(f"{half}: {len(check.GetFootprints())} footprints, "
          f"{check.GetNetCount()} nets -> {pcb_path}")


for half in ("left", "right"):
    build(half)
