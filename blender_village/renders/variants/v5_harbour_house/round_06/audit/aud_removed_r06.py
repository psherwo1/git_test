"""Auditor round-6 (read-only, OUTSIDE the eyebrow zone |y+1.57|<=2.1 & x<1.6): r05 triangles with no counterpart on the r06 surface (any mesh). For each: is it on
the r04 surface (r06 restored the r04 state), and if not, can it be seen from outside in r05, and what does the SAME
ray hit in r06 (nothing = see-through; something > 2 cm behind the old triangle = a new opening)."""
import math, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]


def dump(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
        co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co)
        tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
        out[o.name] = (co.reshape(-1, 3), tv.reshape(-1, 3)); o.evaluated_get(dg).to_mesh_clear()
    return out


R4, R5, R6 = dump(a[0]), dump(a[1]), dump(a[2])


def scene_bvh(D):
    V, T, off = [], [], 0
    for k, (c, t) in D.items():
        V.append(c); T.append(t + off); off += len(c)
    return BVHTree.FromPolygons(np.concatenate(V).tolist(), np.concatenate(T).tolist(), all_triangles=True)


B5, B6 = scene_bvh(R5), scene_bvh(R6)
dirs = []
for i in range(400):                       # Fibonacci sphere, upper 85 % (rays from below ground excluded)
    z = 1 - (i + 0.5) / 400 * 1.7
    r = math.sqrt(max(0, 1 - z * z)); phi = i * math.pi * (3 - math.sqrt(5))
    dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
tot_reach, tot_open = 0, 0
for k in R5:
    if k not in R6 or "eyebrow" in k:
        continue
    c5, t5 = R5[k]; c6, t6 = R6[k]
    if c5.shape == c6.shape and np.abs(c5 - c6).max(initial=0) == 0:
        continue
    b6 = BVHTree.FromPolygons(c6.tolist(), t6.tolist(), all_triangles=True)
    cen = c5[t5].mean(1)
    d6 = np.array([b6.find_nearest(Vector(p))[3] for p in cen])
    miss = np.nonzero(d6 > 0.002)[0]
    if k in R4:
        c4, t4 = R4[k]; b4 = BVHTree.FromPolygons(c4.tolist(), t4.tolist(), all_triangles=True)
        d4 = np.array([b4.find_nearest(Vector(p))[3] for p in cen[miss]])
    else:
        d4 = np.full(len(miss), 9.0)
    on4 = int((d4 <= 0.002).sum())
    rest = miss                       # every off-r06 triangle (r04 state or not), outside the zone below
    pz = cen[rest]; inz = (np.abs(pz[:, 1] + 1.57) <= 2.1) & (pz[:, 0] < 1.6)
    print(f"   {k}: off-r06-and-off-r04 tris inside the eyebrow zone {int(inz.sum())} (reshaped by design), outside {int((~inz).sum())}"
          + (f" bbox {np.round(pz[~inz].min(0),2).tolist()} {np.round(pz[~inz].max(0),2).tolist()}" if (~inz).any() else ""), flush=True)
    rest = rest[~inz]
    reach, opened, ex = 0, 0, []
    for ti in rest:
        p = Vector(cen[ti]); rr = 0; oo = 0
        for d in dirs:
            o = p + d * 15.0
            h5 = B5.ray_cast(o, -d, 16.0)
            if h5[0] is None or (h5[0] - p).length > 0.01:
                continue
            rr += 1
            h6 = B6.ray_cast(o, -d, 40.0)
            if h6[0] is None or h6[3] > 15.0 + 0.02:
                oo += 1
        reach += rr > 0; opened += oo > 0
        if oo:
            ex.append((np.round(cen[ti], 2).tolist(), rr, oo))
    tot_reach += reach; tot_open += opened
    print(f"{k:28s} r05 tris {len(t5):6d} r06 {len(t6):6d} | r05 tris off the r06 surface {len(miss):5d}: on the r04 "
          f"surface {on4}, not {len(rest)}; of those reachable from outside in r05 {reach}; and through which the SAME "
          f"ray in r06 goes > 2 cm deeper / misses: {opened} {ex[:6]}", flush=True)
print("TOTAL reachable", tot_reach, "opened", tot_open)
print("DONE")


