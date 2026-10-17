"""Director round-4 probe: main-roof eave / verge corners.  python -I dir_probe_r04.py -- <blend>
For each of the four corners of the hall roof (final coords: hall faces x -1.608 / 5.392, y -5.773 / 3.427), report the
lowest point of the bargeboard (HARB_roof_verge), the eave lip (lowest shingle / starter / soffit vertices) and the
rafter-tail pieces within 1.2 m of the corner."""
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
dg = bpy.context.evaluated_depsgraph_get()


def verts(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return np.zeros((0, 3))
    m = o.evaluated_get(dg).to_mesh()
    v = np.array([(o.matrix_world @ p.co)[:] for p in m.vertices])
    o.evaluated_get(dg).to_mesh_clear()
    return v


names = [o.name for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("HARB_roof")] + ["HARB_rafters"]
V = {n: verts(n) for n in names}
for n, v in V.items():
    if len(v):
        print(f"OBJ {n:28s} n={len(v):6d} x {v[:,0].min():6.2f}..{v[:,0].max():6.2f} y {v[:,1].min():6.2f}..{v[:,1].max():6.2f} "
              f"z {v[:,2].min():5.2f}..{v[:,2].max():5.2f}")
XW, XE, Y0, Y1 = -1.608, 5.392, -5.773, 3.427
for cx, sx in ((XW, -1), (XE, 1)):
    for cy, sy in ((Y0, -1), (Y1, 1)):
        print(f"CORNER x={cx} y={cy}")
        for n in ("HARB_roof_verge", "HARB_roof_shingles", "HARB_roof_starter", "HARB_roof_covering",
                  "HARB_roof_soffit_deck", "HARB_roof_rafters", "HARB_rafters", "HARB_roof_deck"):
            v = V.get(n)
            if v is None or not len(v):
                continue
            # outside the wall faces, within 1.2 m of the corner
            sel = (sx * (v[:, 0] - cx) > 0.0) & (sx * (v[:, 0] - cx) < 1.2) & (sy * (v[:, 1] - cy) > -1.2) & (sy * (v[:, 1] - cy) < 1.2)
            if not sel.any():
                print(f"   {n:24s} none"); continue
            w = v[sel]
            i = np.argmin(w[:, 2])
            far = np.argmax(sx * (w[:, 0] - cx))
            print(f"   {n:24s} lowest z {w[i,2]:5.2f} at ({w[i,0]:6.2f},{w[i,1]:6.2f})   furthest out {sx*(w[far,0]-cx):4.2f} m "
                  f"(z {w[far,2]:5.2f})   y-extent {sy*(w[:,1]-cy).max():4.2f}")
