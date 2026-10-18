"""round 3 probe: cast rays through given pixels of a review shot and print what they hit (object, z, normal)."""
import sys

import bpy
from mathutils import Vector

blend = sys.argv[1]
SX, SY = -0.418, 2.587
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()
scn = bpy.context.scene
SHOTS = {
    "x08": ((1.5, -5.6, 7.1), (1.5, -1.6, 5.9), 60, [(600, 240), (605, 250), (680, 240), (675, 250), (640, 230)]),
    "x17": ((6.2, -6.2, 4.6), (3.9, -2.8, 3.3), 45, [(690, 400), (650, 430), (720, 420), (700, 470), (740, 440), (630, 440), (700, 390)]),
}
for nm, (loc, tgt, lens, pix) in SHOTS.items():
    o = Vector((loc[0] + SX, loc[1] + SY, loc[2]))
    t = Vector((tgt[0] + SX, tgt[1] + SY, tgt[2]))
    q = (t - o).to_track_quat("-Z", "Y")
    fx = lens / 36.0 * 1280
    print("==", nm)
    for (px, py) in pix:
        d = Vector(((px - 640) / fx, -(py - 360) / fx, -1.0))
        d = (q @ d).normalized()
        hit, p, n, i, ob, _ = scn.ray_cast(dg, o, d)
        if hit:
            print(f"  px {px},{py}: {ob.name:36s} p ({p.x - SX:+.2f},{p.y - SY:+.2f},{p.z:.2f}) n ({n.x:+.2f},{n.y:+.2f},{n.z:+.2f})")
        else:
            print(f"  px {px},{py}: miss")


