"""Auditor v6_barn round 4 (read-only, WIDE post-head window x 1.6-3.4, z 2.9-4.4): size the openings into the barn found by aud_seethru_r03.py.
blender -b -P aud_holes_r03.py -- <v6_barn.blend> [<fast_uncull.blend>]
(a) the post-head pockets under the eyelid: rays from eye-level (1.7 m) and 6 m viewpoints onto a target grid round
    each post head; a ray that reaches the interior volume = a hole.  For every hole ray: the aperture = the narrowest
    clearance (nearest-surface distance x 2) along its path through the wall zone (y -3.60 .. -2.95).
(b) the arch-to-leaf slit (same method on targets along the arch intrados).
(c) the east-gable plinth stone seen from behind: face normals there, culled vs the FAST (uncull) build."""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    V, T, OWN, off, per = [], [], [], 0, {}
    for oi, o in enumerate(objs):
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
        co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
        tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
        tv = tv.reshape(-1, 3)
        per[o.name] = (co, tv)
        V.append(co); T.append(tv + off); OWN.append(np.full(len(tv), oi)); off += len(co)
        o.evaluated_get(dg).to_mesh_clear()
    V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True), [o.name for o in objs], OWN, per


bvh, names, OWN, per = load(a[0])
CX, FW, BW, GW, GE = 0.058, -3.499, 3.501, -6.942, 7.058
SH = 0.45
IX0, IX1, IY0, IY1 = GW + SH, GE - SH, FW + SH, BW - SH


def roof_top(x, y):
    h = bvh.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 40)
    return h[0].z if h[0] is not None else 0.0


def reaches_interior(o, d, tmax):
    t = 0.0
    while t < tmax:
        p = o + d * t
        if IX0 < p.x < IX1 and IY0 < p.y < IY1 and 0.05 < p.z < roof_top(p.x, p.y) - 0.8:
            return True
        t += 0.03
    return False


def probe(tag, targets, views):
    nh, nr, aps, crossings, per_view = 0, 0, [], [], {}
    for vn, v in views.items():
        v = Vector(v); k = 0
        for tg in targets:
            d = (Vector(tg) - v); L = d.length; d.normalize()
            h = bvh.ray_cast(v, d, 60.0)
            nr += 1
            th = h[3] if h[0] is not None else 60.0
            tg0 = (-v.z / d.z) if d.z < -1e-9 else 1e9
            tf = min(th, tg0)
            # only rays that cross the front wall zone before their first hit
            if d.y <= 0:
                continue
            t_in = (FW - 0.10 - v.y) / d.y
            if t_in > tf:
                continue
            if not reaches_interior(v + d * max(t_in, 0.0), d, tf - max(t_in, 0.0)):
                continue
            nh += 1; k += 1
            # aperture: the narrowest clearance along the path through the wall zone
            t0, t1 = (FW - 0.12 - v.y) / d.y, (FW + 0.55 - v.y) / d.y
            best = (9.0, None)
            for t in np.linspace(t0, t1, 120):
                p = v + d * t
                dist = bvh.find_nearest(p)[3]
                if dist < best[0]:
                    best = (dist, p)
            aps.append(2 * best[0]); crossings.append(best[1])
        per_view[vn] = k
    print(f"{tag}: rays {nr}, rays into the interior {nh}; per viewpoint {per_view}")
    if aps:
        aps = np.array(aps); C = np.array([list(p) for p in crossings])
        print(f"   aperture (2 x narrowest clearance on the hole rays): median {np.median(aps)*1000:.1f} mm, "
              f"max {aps.max()*1000:.1f} mm, p90 {np.percentile(aps, 90)*1000:.1f} mm")
        print(f"   pinch points bbox x {C[:,0].min():.3f}..{C[:,0].max():.3f}  y {C[:,1].min():.3f}..{C[:,1].max():.3f}  "
              f"z {C[:,2].min():.3f}..{C[:,2].max():.3f}")
        # who bounds the widest pinch point
        i = int(np.argmax(aps)); p = Vector(C[i])
        near = set()
        for dv in [Vector(x) for x in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0))]:
            hh = bvh.ray_cast(p, dv, 0.5)
            if hh[0] is not None:
                near.add((names[OWN[hh[2]]], tuple(round(c, 2) for c in dv), round(hh[3], 3)))
        print("   widest pinch at", [round(c, 3) for c in p], "bounded by", sorted(near))


eye = lambda sg: {f"eye_{dx:+.0f}_{dy:.0f}": (CX + sg * 2.2 + dx, FW - dy, 1.7)
                  for dx in (-3.0, -1.5, 0.0, 1.5, 3.0) for dy in (2.0, 3.5, 6.0)}
six = lambda sg: {f"6m_{dx:+.0f}_{dy:.0f}": (CX + sg * 2.2 + dx, FW - dy, 6.0)
                  for dx in (-3.0, 0.0, 3.0) for dy in (4.0, 6.0, 9.0)}
for sg, side in ((-1, "W"), (1, "E")):
    tg = [(CX + sg * x, FW + 0.02, z) for x in np.arange(1.60, 3.40, 0.02) for z in np.arange(2.90, 4.40, 0.02)]
    probe(f"POST HEAD {side} eye 1.7 m", tg, eye(sg))
    probe(f"POST HEAD {side} 6 m", tg, six(sg))
print("DONE")

