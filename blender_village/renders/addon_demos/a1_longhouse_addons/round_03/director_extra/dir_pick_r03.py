"""Director r03: trace the red pixels of i13 (host attic, far W) through every surface to the sky.
blender -b --python dir_pick_r03.py -- <blend>"""
import sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
LX, LY, SY = -1.594, 2.347, -0.05
CAMS = {"i13": ((LX - 3.0, LY - 1.6 + SY, 4.1), (LX - 3.0, LY - 0.1 + SY, 3.8), 18,
                [(62, 708), (70, 708), (80, 708), (88, 708), (94, 708), (75, 707), (75, 709)])}
for nm, (loc, tgt, lens, pix) in CAMS.items():
    loc, tgt = Vector(loc), Vector(tgt)
    q = (tgt - loc).to_track_quat("-Z", "Y")
    W, H, sw = 1280, 720, 36.0
    for (px, py) in pix:
        x = (px + 0.5 - W / 2) / W * sw / lens
        y = -(py + 0.5 - H / 2) / W * sw / lens
        d = (q @ Vector((x, y, -1.0))).normalized()
        P, chain = loc.copy(), []
        for _ in range(8):
            hit, Q, N, fi, ob, M = scn.ray_cast(dg, P, d)
            if not hit:
                chain.append("SKY")
                break
            chain.append(f"{ob.name}#{fi}@{tuple(round(c, 3) for c in Q)}{'B' if N.dot(d) > 0 else 'F'}")
            P = Q + d * 0.002
        print("PICK", nm, px, py, " -> ".join(chain), flush=True)
