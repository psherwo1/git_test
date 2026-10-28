"""round 5 probe: object list and the wing-ridge / main-ridge heights near the join (world, recentred blend)."""
import sys

import bpy
import numpy as np

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=argv[0])
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != "MESH":
            continue
        V = np.array([v.co for v in o.data.vertices]) if len(o.data.vertices) else np.zeros((1, 3))
        mw = np.array(o.matrix_world)
        V = V @ mw[:3, :3].T + mw[:3, 3]
        print(f"OBJ {o.name:40s} polys {len(o.data.polygons):7d} lo {np.round(V.min(0), 2)} hi {np.round(V.max(0), 2)}")
    for nm in ("COTT_wing_roof_ridge", "COTT_roof_ridge", "COTT_wing_valley"):
        o = bpy.data.objects.get(nm)
        if o is None:
            continue
        V = np.array([v.co for v in o.data.vertices])
        for y in np.arange(-4.0, 1.01, 0.25):
            m = np.abs(V[:, 1] - y) < 0.06
            if m.any():
                print(f"{nm} y {y:+.2f}: z max {V[m, 2].max():.3f}  x {V[m, 0].min():.2f}..{V[m, 0].max():.2f}")
