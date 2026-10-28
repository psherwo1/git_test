"""Director r02: which object / face is under given pixels of a dir_render_r02 camera (flipped-normal check).
blender -b --python dir_pick_r02.py -- <blend>"""
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
LX, LY, LF = -1.594, 2.347, 4.247
CAMS = {
    "z01": ((LX + 2.9, LY + 0.95, 3.0), (LX + 2.0, LY + 0.05, 2.8), 40, [(720, 600), (390, 500), (700, 650)]),
    "i06": ((LX, LY - 1.75, 4.0), (LX, LY - 0.15, 3.7), 16, [(430, 355), (440, 355), (450, 355), (507, 355), (1012, 354), (1015, 353), (440, 345), (440, 365)]),
    "x02": ((LX + 3.7, LF + 0.65, 3.1), (LX + 1.9, LY + 0.75, 2.7), 40, [(400, 380), (255, 335)]),
}
for nm, (loc, tgt, lens, pix) in CAMS.items():
    loc, tgt = Vector(loc), Vector(tgt)
    q = (tgt - loc).to_track_quat("-Z", "Y")
    W, H = 1280, 720
    sw = 36.0
    for (px, py) in pix:
        x = (px + 0.5 - W / 2) / W * sw / lens
        y = -(py + 0.5 - H / 2) / W * sw / lens
        d = (q @ Vector((x, y, -1.0))).normalized()
        hit, P, N, fi, ob, M = scn.ray_cast(dg, loc, d)
        if hit and nm == "i06":
            h2 = scn.ray_cast(dg, P + d * 0.002, d)
            print("  through", ob.name, tuple(round(c, 3) for c in P), "->", (h2[4].name if h2[0] else "SKY"), (tuple(round(c, 3) for c in h2[1]) if h2[0] else ""), flush=True)
        if not hit:
            print("PICK", nm, px, py, "miss", flush=True)
            continue
        facing = "BACK" if N.dot(d) > 0 else "front"
        print("PICK", nm, px, py, ob.name, "face", fi, "at", tuple(round(c, 3) for c in P), facing, flush=True)

