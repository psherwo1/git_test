"""round 3 probe: which objects have faces near the inside eave corners / valley feet (plan coords + recentre)."""
import sys

import bpy
import numpy as np

blend = sys.argv[1]
SX, SY = -0.418, 2.587
bpy.ops.wm.open_mainfile(filepath=blend)
SPOTS = {"W_corner": (-0.9, -2.75), "E_corner": (3.9, -2.75), "W_lip": (-1.35, -3.2), "E_lip": (4.35, -3.2)}
for nm, (x, y) in SPOTS.items():
    c = np.array([x + SX, y + SY])
    print("==", nm)
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not len(ob.data.vertices):
            continue
        V = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", V)
        V = V.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        W = V @ M[:3, :3].T + M[:3, 3]
        d = np.hypot(W[:, 0] - c[0], W[:, 1] - c[1])
        m = (d < 0.6) & (W[:, 2] > 2.0) & (W[:, 2] < 3.6)
        if m.sum():
            print(f"  {ob.name:40s} n {int(m.sum()):6d} z {W[m, 2].min():.2f}..{W[m, 2].max():.2f} dmin {d[m].min():.2f}")
