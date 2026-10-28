"""Auditor v6_barn round 3 (read-only): inverted (inside-out) pieces.  blender -b -P aud_stones_r03.py -- <blend>...
For every island of every mesh: the area-weighted share of faces whose normal points toward the island's centroid
(an inside-out stone / board scores ~1, a normal piece ~0).  Lists islands with share > 0.6 and area > 0.01 m2."""
import sys

import bpy
import numpy as np

for path in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    print("FILE", path)
    tot = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
        tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
        tv = tv.reshape(-1, 3)
        ed = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
        o.evaluated_get(dg).to_mesh_clear()
        lab = np.arange(len(co))
        if len(ed):
            while True:
                mm = np.minimum(lab[ed[:, 0]], lab[ed[:, 1]]); new = lab.copy()
                np.minimum.at(new, ed[:, 0], mm); np.minimum.at(new, ed[:, 1], mm); new = new[new][new]
                if np.array_equal(new, lab):
                    break
                lab = new
        tl = lab[tv[:, 0]]
        cr = np.cross(co[tv[:, 1]] - co[tv[:, 0]], co[tv[:, 2]] - co[tv[:, 0]])
        ar = 0.5 * np.linalg.norm(cr, axis=1)
        fc = co[tv].mean(1)
        bad = []
        for L in np.unique(tl):
            s = tl == L
            if ar[s].sum() < 0.01 or s.sum() < 8:
                continue
            c = (fc[s] * ar[s, None]).sum(0) / ar[s].sum()
            inward = (np.einsum("ij,ij->i", cr[s], fc[s] - c) < 0)
            share = (ar[s] * inward).sum() / ar[s].sum()
            if share > 0.6:
                bad.append((round(float(share), 2), round(float(ar[s].sum()), 3), np.round(c, 2).tolist()))
        if bad:
            tot += len(bad)
            print(f"  {o.name:32s} inside-out islands {len(bad)}:", sorted(bad, key=lambda b: -b[1])[:8])
    print("  TOTAL inside-out islands", tot)
print("DONE")
