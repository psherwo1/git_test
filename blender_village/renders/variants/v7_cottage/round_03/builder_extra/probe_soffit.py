"""round 3 probe: the soffit fill meshes -- face count, up / down faces, z range of each layer."""
import sys

import bpy
import numpy as np

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for ob in bpy.data.objects:
    if "soffit" not in ob.name or ob.type != "MESH":
        continue
    me = ob.data
    N = np.empty(len(me.polygons) * 3)
    C = np.empty(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", N)
    me.polygons.foreach_get("center", C)
    N, C = N.reshape(-1, 3), C.reshape(-1, 3)
    up, dn = N[:, 2] > 0.3, N[:, 2] < -0.3
    print(ob.name, "faces", len(N), "up", int(up.sum()), "down", int(dn.sum()), "side", int((~up & ~dn).sum()))
    for k in np.argsort(C[:, 0])[:: max(1, len(C) // 12)]:
        print(f"   c ({C[k, 0]:+.2f},{C[k, 1]:+.2f},{C[k, 2]:.2f}) n ({N[k, 0]:+.2f},{N[k, 1]:+.2f},{N[k, 2]:+.2f})")
