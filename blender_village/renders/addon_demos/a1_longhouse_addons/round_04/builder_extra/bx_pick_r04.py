"""Builder r04 (from the director's dir_pick_r03.py): find the red pixels of an interior shot's _red twin and trace
each through every surface to the sky.  python -I bx_pick_r04.py <blend> <shot> <red_png>
Cameras as bx_render_r04.py (round-4 world: SY = -0.075 against round 2)."""
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, shot, png = argv[0], argv[1], argv[2]
LX, LY, SY = -1.594, 2.347, -0.075
CAMS = {"i13": ((LX - 3.0, LY - 1.6, 4.1), (LX - 3.0, LY - 0.1, 3.8), 18),
        "i15": ((-4.9, 1.0, 3.6), (-6.15, 2.25, 2.75), 30),
        "i16": ((-4.9, -2.1, 3.6), (-6.15, -3.35, 2.75), 30)}
im = bpy.data.images.load(png)
W, H = im.size
px = im.pixels[:]
red = []
for i in range(0, len(px), 4):
    if px[i] > 0.5 and px[i + 1] < 0.2 and px[i + 2] < 0.2:
        k = i // 4
        red.append((k % W, H - 1 - k // W))              # Blender pixels run bottom-up
print("RED", shot, len(red), red[:40], flush=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
loc, tgt, lens = CAMS[shot]
loc, tgt = Vector((loc[0], loc[1] + SY, loc[2])), Vector((tgt[0], tgt[1] + SY, tgt[2]))
q = (tgt - loc).to_track_quat("-Z", "Y")
sw = 36.0
for (x_, y_) in red[:40]:
    x = (x_ + 0.5 - W / 2) / W * sw / lens
    y = -(y_ + 0.5 - H / 2) / W * sw / lens
    d = (q @ Vector((x, y, -1.0))).normalized()
    P, chain = loc.copy(), []
    for _ in range(8):
        hit, Q, N, fi, ob, M = scn.ray_cast(dg, P, d)
        if not hit:
            chain.append("SKY")
            break
        chain.append(f"{ob.name}#{fi}@{tuple(round(c, 3) for c in Q)}{'B' if N.dot(d) > 0 else 'F'}")
        P = Q + d * 0.002
    print("PICK", shot, x_, y_, " -> ".join(chain), flush=True)
