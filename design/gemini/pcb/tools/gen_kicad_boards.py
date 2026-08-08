#!/usr/bin/env python3
"""Generate KiCad boards for Gemini (left/right halves) from placement CSVs.

Architecture (rev A): ONE Raspberry Pi Pico on the left half; the right half
is passive with an MCP23017 I/O expander. Halves link over USB-C carrying
I2C + LED data (VBUS=VSYS ~5V, D+=SDA, D-=SCL, CC=WS2812 chain) — any
basic non-e-marked USB 2.0 C-to-C cable works. The left half also has a
host USB-C (J2) as an alternative to the Pico onboard port.

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

# Diodes that would sit on the Pico's lower header pin row are relocated
# into the brow (they connect to shared ROW nets; position is free).
# D00-D02 would collide with the Pico's castellation pads (upper pin row);
# D10-D12 with its lower pin row. All six live in the brow instead.
DIODE_OVERRIDE = {
    "left": {"D00": (48.0, -4.0), "D01": (54.0, -4.0), "D02": (76.0, -4.0),
             "D10": (30.0, -4.0), "D11": (36.0, -4.0), "D12": (42.0, -4.0)},
    "right": {},
}

# SK6812 MINI-E pads (datasheet): 1=VDD, 2=DOUT, 3=VSS, 4=DIN.
LED_FP = "LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount"
LED_OFFSET_Y = 5.08  # south of the switch center, in the MX LED window

# Pico physical pin -> net (left half only). GP0/GP1 = I2C0 SDA/SCL.
PICO_PINS = {
    "1": "SDA", "2": "SCL",
    "4": "ROW0", "5": "ROW1", "6": "ROW2", "7": "ROW3",
    "9": "COL0", "10": "COL1", "11": "COL2", "12": "COL3",
    "14": "COL4", "15": "COL5",
    "21": "LED_DATA",   # GP16 -> level shifter A
    "3": "GND", "8": "GND", "13": "GND", "18": "GND", "23": "GND",
    "28": "GND", "33": "GND", "38": "GND", "42": "GND",
    "36": "+3V3",
    # VSYS is the 5V-ish power rail (LEDs, link, right half). It is fed by
    # EITHER the Pico's onboard USB (module-internal schottky VBUS->VSYS)
    # OR the J2 host USB-C via DV1 — diode-ORed, safe to plug both.
    "39": "VSYS",
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
# middle D pairs tied A+B so any cable orientation works. CC and SBU pads
# (3/4/9/10) are all tied to the LED chain link: the cable's CC wire carries
# WS2812 data across (orientation-proof since both CCs are tied; SBUs are
# unwired in USB 2.0 cables). Requires a basic non-e-marked C-to-C cable —
# an e-marker chip would load the CC line. VERIFY pad map vs datasheet.
USBC_PINS = {
    "1": "GND", "12": "GND", "13": "GND",
    "2": "VSYS", "11": "VSYS",
    "6": "SDA", "7": "SDA",   # D+ (A6/B6)
    "5": "SCL", "8": "SCL",   # D- (A7/B7)
    "3": "LED_LINK", "4": "LED_LINK", "9": "LED_LINK", "10": "LED_LINK",
}


def read_placement(half):
    path = os.path.join(PCB_DIR, "placement", f"gemini_{half}_placement.csv")
    with open(path) as f:
        return list(csv.DictReader(f))


def read_outline(half):
    path = os.path.join(PCB_DIR, "placement", f"gemini_{half}_outline.csv")
    with open(path) as f:
        return [(float(r["x_mm"]), float(r["y_mm"])) for r in csv.DictReader(f)]


def uniform_inset(verts, d):
    """Inset a rectilinear polygon by d (positive = inward). Assumes the
    outline walk order used by gen_pcb_data (outward normal = (dy, -dx))."""
    n = len(verts)
    lines = []
    for i in range(n):
        p1, p2 = verts[i], verts[(i + 1) % n]
        dx_, dy_ = p2[0] - p1[0], p2[1] - p1[1]
        length = abs(dx_) + abs(dy_)
        ox, oy = dy_ / length, -dx_ / length
        if dx_ == 0:
            lines.append(("v", p1[0] - ox * d))
        else:
            lines.append(("h", p1[1] - oy * d))
    out = []
    for i in range(n):
        a, b = lines[i - 1], lines[i]
        x = a[1] if a[0] == "v" else b[1]
        y = a[1] if a[0] == "h" else b[1]
        out.append((x, y))
    return out


def add_keepout(board, rects, layer):
    """Rule area (no tracks/vias/pour) covering the given rect list."""
    for x0, y0, x1, y1 in rects:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        try:
            z.SetDoNotAllowPads(False)
        except AttributeError:
            pass
        try:
            z.SetDoNotAllowZoneFills(True)
        except AttributeError:
            z.SetDoNotAllowCopperPour(True)
        z.SetLayer(layer)
        z.Outline().NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            z.Outline().Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board.Add(z)


def add_ring_keepout(board, outline, dx=0.0, width=0.3):
    """Border keepout ring: outline with an inset hole, both copper layers.
    Keeps the router away from every board edge (incl. the future V-score
    junction on the panel)."""
    inner = uniform_inset(outline, width)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        try:
            z.SetDoNotAllowPads(False)
        except AttributeError:
            pass
        try:
            z.SetDoNotAllowZoneFills(True)
        except AttributeError:
            z.SetDoNotAllowCopperPour(True)
        z.SetLayer(layer)
        z.Outline().NewOutline()
        for x, y in outline:
            z.Outline().Append(pcbnew.FromMM(x + dx), pcbnew.FromMM(y))
        z.Outline().NewHole(0)
        for x, y in inner:
            z.Outline().Append(pcbnew.FromMM(x + dx), pcbnew.FromMM(y), 0, 0)
        board.Add(z)


def set_rules(board):
    bds = board.GetDesignSettings()
    try:
        nc = bds.m_NetSettings.GetDefaultNetclass()
    except AttributeError:
        nc = bds.GetDefault()
    nc.SetTrackWidth(pcbnew.FromMM(0.25))
    nc.SetClearance(pcbnew.FromMM(0.15))
    nc.SetViaDiameter(pcbnew.FromMM(0.8))
    nc.SetViaDrill(pcbnew.FromMM(0.4))
    bds.m_CopperEdgeClearance = pcbnew.FromMM(0.0)
    bds.m_HoleClearance = pcbnew.FromMM(0.2)   # JLC/PCBWay NPTH capability


def flip_to_back(fp):
    try:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except (AttributeError, TypeError):
        fp.Flip(fp.GetPosition(), True)


def populate(board, half, prefix="", dx=0.0):
    """Place all of one half's footprints into `board`, with optional ref/net
    prefix and x translation (used for the production panel)."""
    nets = {}

    def net(name):
        name = prefix + name
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

    def track(x1, y1, x2, y2, netname, layer=pcbnew.B_Cu, width=0.25):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(VECTOR2I_MM(x1 + dx, y1))
        t.SetEnd(VECTOR2I_MM(x2 + dx, y2))
        t.SetWidth(FromMM(width))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        board.Add(t)

    def stitch_usbc(cx, groups):
        """Freerouting never connects same-net pad pairs within one
        footprint, so tie the HRO USB-C's mirrored A/B pads with a nested
        bus fanout south of the pad row (pads at y=-7.545, innermost pair
        gets the shallowest bus so nothing crosses anything). The outer
        two groups jog around the connector's alignment pegs at x=+-2.89:
        VSYS (+-2.45) shifts inward to +-2.2, GND (+-3.225) outward to
        +-3.55 (may touch the shield pads — same net, fine)."""
        JOG = {2.45: 2.2, 3.225: 3.55}
        for xs, netname, busy in groups:
            runx = []
            for px in xs:
                jx = JOG.get(abs(px), abs(px)) * (1 if px > 0 else -1)
                if jx != px:
                    track(cx + px, -7.545, cx + px, -7.2, netname)
                    track(cx + px, -7.2, cx + jx, -7.2, netname)
                    track(cx + jx, -7.2, cx + jx, busy, netname)
                else:
                    track(cx + px, -7.545, cx + px, busy, netname)
                runx.append(jx)
            track(cx + min(runx), busy, cx + max(runx), busy, netname)

    LINK_STITCH = [
        ((-0.25, 0.25), "SDA", -6.65),
        ((-0.75, 0.75), "SCL", -6.2),
        ((-1.75, -1.25, 1.25, 1.75), "LED_LINK", -5.75),
        ((-2.45, 2.45), "VSYS", -5.3),
        ((-3.225, 3.225), "GND", -4.85),
    ]
    HOST_STITCH = [
        ((-0.25, 0.25), "USB_DP", -6.65),
        ((-0.75, 0.75), "USB_DM", -6.2),
        ((-2.45, 2.45), "VBUS_HOST", -5.3),
        ((-3.225, 3.225), "GND", -4.85),
    ]

    def place(fpname, ref, value, x, y, rot=0, back=True, pins=None):
        fp = load(fpname)
        fp.SetReference(prefix + ref)
        fp.SetValue(value)
        fp.SetPosition(VECTOR2I_MM(x + dx, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        if back:
            flip_to_back(fp)  # Flip segfaults unless the footprint is on a board
        for pin, netname in (pins or {}).items():
            assign(fp, pin, netname)
        return fp

    # --- switches, diodes, LEDs, stabs ---
    keys = read_placement(half)
    n_leds = len(keys)
    for i, row in enumerate(keys):
        r, c = row["matrix_row"], row["matrix_col"]
        w = float(row["width_u"])
        cx, cy = float(row["center_x_mm"]), float(row["center_y_mm"])
        keynet = f"N_SW{r}{c}"
        # marbastlib hotswap footprints are authored in bottom-view coords
        # (mirrored pin holes, pads on F.Cu) and must be placed flipped so
        # the socket sits on the back and pads land on B.Cu.
        place(SW_FP[w], f"SW{r}{c}", row["legend"], cx, cy, back=True,
              pins={"1": f"COL{c}", "2": keynet})
        dpx, dpy = DIODE_OVERRIDE[half].get(f"D{r}{c}", (cx - 4.0, cy + 8.0))
        place("D_SOD-123", f"D{r}{c}", "1N4148W", dpx, dpy, rot=180,
              back=True, pins={"1": f"ROW{r}", "2": keynet})  # cathode->row
        # Per-key RGB, reverse-mount on the back shining up through the
        # cutout in the switch's south LED window. Chain is row-major;
        # it enters/exits the board via LED_LINK on the USB-C CC pins.
        din = f"LED_CH{i:02d}" if i else ("LED_CH00" if half == "left" else "LED_LINK")
        dout = "LED_LINK" if (half == "left" and i == n_leds - 1) else f"LED_CH{i + 1:02d}"
        if half == "right" and i == n_leds - 1:
            dout = "LED_END"
        place(LED_FP, f"LED{r}{c}", "SK6812MINI-E", cx, cy + LED_OFFSET_Y,
              back=True, pins={"1": "VSYS", "2": dout, "3": "GND", "4": din})
        # keepouts over the LED window cutout (freerouting can't see
        # footprint Edge.Cuts): central block + mid strip, pads left open
        lx, ly = cx + dx, cy + LED_OFFSET_Y
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            add_keepout(board, [(lx - 1.9, ly - 2.2, lx + 1.9, ly + 2.2),
                                (lx - 3.95, ly - 0.28, lx + 3.95, ly + 0.28)],
                        layer)
        if w in STAB_FP:
            place(STAB_FP[w], f"ST_SW{r}{c}", f"stab {w}u", cx, cy, back=False)

    # --- half-specific electronics (all on the back) ---
    if half == "left":
        # Pico horizontal, centered on the row-1 switch centerline, micro-USB
        # out the left side edge. Header-mounted (~2.5 mm standoff). Its two
        # TH pin rows land at y=19.7 and y=37.5 — near the centers of the
        # top-face corridors between switch housings, clear of all switch
        # bodies, drills, and socket pads on both faces.
        # y = row-1 centerline - 1.0: keeps both pin rows in the top-face
        # corridors while pulling the module NPTH mounting holes clear of
        # the SW12 socket pads.
        place("RPi_Pico_SMD_TH", "U1", "Raspberry Pi Pico", 26.0, 27.575,
              rot=90, pins=PICO_PINS)

        # Link port in the brow, near the seam.
        place("HRO-TYPE-C-31-M-12-Assembly", "J1", "USB-C link", 110.0, -3.5,
              pins=USBC_PINS)
        stitch_usbc(110.0, LINK_STITCH)
        place("R_0603_1608Metric", "R1", "4k7", 58.0, -3.5,
              pins={"1": "SDA", "2": "+3V3"})
        place("R_0603_1608Metric", "R2", "4k7", 63.0, -3.5,
              pins={"1": "SCL", "2": "+3V3"})
        # 5V level shifter for WS2812 data (74AHCT1G125, SOT-23-5):
        # 1=/OE 2=A 3=GND 4=Y 5=VCC.
        place("SOT-23-5", "U2", "74AHCT1G125", 70.0, -4.0,
              pins={"1": "GND", "2": "LED_DATA", "3": "GND",
                    "4": "LED_CH00", "5": "VSYS"})
        # J2: host USB-C in the brow — alternative to the Pico's onboard
        # port. Device-role CC pulldowns (R3/R4), VBUS diode-ORed into VSYS
        # (DV1) per the Pico datasheet. D+/D- run to TP pads beside the
        # module: jumper them to the Pico's underside TP3/TP2 (short wires
        # or spring pins) — USB data is NOT on the 40-pin header.
        place("HRO-TYPE-C-31-M-12-Assembly", "J2", "USB-C host", 9.5, -3.5,
              pins={"1": "GND", "12": "GND", "13": "GND",
                    "2": "VBUS_HOST", "11": "VBUS_HOST",
                    "6": "USB_DP", "7": "USB_DP",
                    "5": "USB_DM", "8": "USB_DM",
                    "4": "CC1", "9": "CC2"})
        stitch_usbc(9.5, HOST_STITCH)
        place("R_0603_1608Metric", "R3", "5k1", 16.5, -1.5,
              pins={"1": "CC1", "2": "GND"})
        place("R_0603_1608Metric", "R4", "5k1", 16.5, -5.5,
              pins={"1": "CC2", "2": "GND"})
        place("D_SOD-123", "DV1", "B5819W", 22.0, -5.5, rot=180,
              pins={"1": "VSYS", "2": "VBUS_HOST"})  # cathode -> VSYS
        # Wire-jumper targets for the Pico's underside USB test points
        # (TP3=D+, TP2=D-), in the brow near the module's USB end. Routing
        # phase may move them directly under the exact TP positions for
        # spring-pin mounting instead of wires.
        place("TestPoint_THTPad_D1.5mm_Drill0.7mm", "TP1", "USB_DP",
              21.5, -1.5, pins={"1": "USB_DP"})
        place("TestPoint_THTPad_D1.5mm_Drill0.7mm", "TP2", "USB_DM",
              26.0, -1.5, pins={"1": "USB_DM"})
    else:
        # Passive half: MCP23017 in the socket-free strip beside the spacebar.
        place("SOIC-28W_7.5x17.9mm_P1.27mm", "U1", "MCP23017-E/SO", 46.0, 66.5,
              pins=MCP_PINS)
        # Link port in the brow, near the seam.
        place("HRO-TYPE-C-31-M-12-Assembly", "J1", "USB-C link", 9.5, -3.5,
              pins=USBC_PINS)
        stitch_usbc(9.5, LINK_STITCH)
        place("C_0603_1608Metric", "C1", "100nF", 46.0, 56.5,
              pins={"1": "+3V3", "2": "GND"})
        # Local 3V3 for the expander from the 5V link (MCP1700-3302,
        # SOT-23: 1=GND 2=VIN 3=VOUT) + 1uF in/out caps.
        place("SOT-23", "U2", "MCP1700-3302", 30.0, -4.0,
              pins={"1": "GND", "2": "VSYS", "3": "+3V3"})
        place("C_0603_1608Metric", "C2", "1uF", 24.0, -4.0,
              pins={"1": "VSYS", "2": "GND"})
        place("C_0603_1608Metric", "C3", "1uF", 36.0, -4.0,
              pins={"1": "+3V3", "2": "GND"})

    # --- silkscreen logo, front side, centred in the 8 mm rear brow ---
    # F.SilkS because the brow's back face carries the link/host ports and
    # the passives; the front face is otherwise bare there. The 6 mm-tall
    # footprint is baked from ../gemini.kicad_mod by tools/gen_logo_fp.py.
    outline = read_outline(half)
    ytop = min(y for _, y in outline)
    brow_x = [x for x, y in outline if y == ytop]
    place("Logo_Gemini", "G1", "Logo_Gemini",
          (min(brow_x) + max(brow_x)) / 2, ytop / 2, back=False)


def draw_edges(board, verts):
    for (x1, y1), (x2, y2) in zip(verts, verts[1:] + verts[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(VECTOR2I_MM(x1, y1))
        seg.SetEnd(VECTOR2I_MM(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(FromMM(0.1))
        board.Add(seg)


def save(board, dirname, name):
    out_dir = os.path.join(PCB_DIR, dirname)
    os.makedirs(out_dir, exist_ok=True)
    pcb_path = os.path.join(out_dir, f"{name}.kicad_pcb")
    board.SetFileName(pcb_path)
    pcbnew.SaveBoard(pcb_path, board)
    with open(os.path.join(out_dir, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 9)\n'
                '  (lib (name "gemini")(type "KiCad")'
                '(uri "${KIPRJMOD}/../lib/gemini.pretty")(options "")'
                '(descr "Gemini vendored footprints"))\n)\n')
    check = pcbnew.LoadBoard(pcb_path)
    print(f"{name}: {len(check.GetFootprints())} footprints, "
          f"{check.GetNetCount()} nets -> {pcb_path}")


def add_npth_keepouts(board):
    """Freerouting can't see NPTH holes — fence every one (Pico mounting
    holes, connector shields, stab inserts) with a small keepout."""
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            pos = pad.GetPosition()
            x, y = pos.x / 1e6, pos.y / 1e6
            r = max(pad.GetDrillSize().x, pad.GetDrillSize().y) / 2e6 + 0.26
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                add_keepout(board, [(x - r, y - r, x + r, y + r)], layer)


def build(half):
    board = pcbnew.BOARD()
    set_rules(board)
    populate(board, half)
    add_npth_keepouts(board)
    outline = read_outline(half)
    draw_edges(board, outline)
    add_ring_keepout(board, outline)
    save(board, f"gemini-{half}", f"gemini-{half}")


def build_panel():
    """Both halves in one board for fab: straight OUTER edges joined at x=0
    (left half's left edge against the right half's right edge — no rotation
    needed), so the snap line is a single straight V-score. The stepped seam
    edges face outward and are routed normally."""
    board = pcbnew.BOARD()
    set_rules(board)
    right = read_outline("right")
    dx = -max(x for x, _ in right)          # right half's straight outer edge -> x=0
    populate(board, "left", prefix="L_", dx=0.0)
    populate(board, "right", prefix="R_", dx=dx)
    add_npth_keepouts(board)
    left = read_outline("left")
    add_ring_keepout(board, left)
    add_ring_keepout(board, right, dx=dx)
    right_t = [(x + dx, y) for x, y in right]
    # merged outline: left verts run (0,-8) .. seam .. (0,76.2); the right
    # half's first two verts are its straight edge (now the shared junction)
    panel = left + right_t[2:]
    draw_edges(board, panel)
    # V-score line + labels (JLC/PCBWay: straight line on Edge.Cuts + note)
    vcut = pcbnew.PCB_SHAPE(board)
    vcut.SetShape(pcbnew.SHAPE_T_SEGMENT)
    vcut.SetStart(VECTOR2I_MM(0.0, -8.0))
    vcut.SetEnd(VECTOR2I_MM(0.0, 76.2))
    vcut.SetLayer(pcbnew.Edge_Cuts)
    vcut.SetWidth(FromMM(0.1))
    board.Add(vcut)
    for ty in (-10.5, 78.7):
        t = pcbnew.PCB_TEXT(board)
        t.SetText("V-CUT")
        t.SetPosition(VECTOR2I_MM(0.0, ty))
        t.SetLayer(pcbnew.Cmts_User)
        board.Add(t)
    save(board, "gemini-panel", "gemini-panel")


for half in ("left", "right"):
    build(half)
build_panel()
