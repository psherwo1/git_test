"""v7_cottage builder probe (read-only): interior-volume rays.  From points inside the closed volumes (the main
attic, the wing attic, the dormer, the rooms), rays in a Fibonacci set of directions; a ray that meets no mesh and
does not go down to the ground plane escapes = a see-through / light leak.  For every leak the pinch point (the
narrowest clearance along the ray inside the building's box) is reported, clustered.
python -I probe_interior.py <file.blend> [shift_x shift_y]   (shift: the recipe's recentre shift; read from the log)
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
dg = bpy.context.evaluated_depsgraph_get()
V, T, OWN, off = [], [], [], 0
objs = [o for o in bpy.data.objects if o.type == "MESH"]
for oi, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh()
    m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3)
    m.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world)
    co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32)
    m.loop_triangles.foreach_get("vertices", tv)
    V.append(co)
    T.append(tv.reshape(-1, 3) + off)
    OWN.append(np.full(len(tv) // 3, oi))
    off += len(co)
    o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V)
T = np.concatenate(T)
OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
lo, hi = V.min(0), V.max(0)
print("bounds", lo.round(2), hi.round(2))
sx, sy = (float(a[1]), float(a[2])) if len(a) > 2 else (0.0, 0.0)


def fib(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


DIRS = fib(400)
DIRS = DIRS[DIRS[:, 2] > -0.25]


def probe(tag, pts):
    nl, nr, pinch = 0, 0, []
    for p in pts:
        o = Vector((p[0] + sx, p[1] + sy, p[2]))
        h0 = bvh.find_nearest(o)
        if h0[3] is not None and h0[3] < 0.05:
            continue
        for d in DIRS:
            dv = Vector(tuple(d))
            h = bvh.ray_cast(o, dv, 80.0)
            nr += 1
            if h[0] is not None:
                continue
            if d[2] < -1e-3:            # reaches the ground plane (no floor is modelled)
                continue
            nl += 1
            best = (9.0, None)
            for t in np.linspace(0.05, 12.0, 240):
                q = o + dv * float(t)
                if not (lo[0] - 0.2 < q.x < hi[0] + 0.2 and lo[1] - 0.2 < q.y < hi[1] + 0.2 and q.z < hi[2] + 0.2):
                    break
                dd = bvh.find_nearest(q)[3]
                if dd is not None and dd < best[0]:
                    best = (dd, q)
            if best[1] is not None:
                pinch.append((round(best[1].x - sx, 2), round(best[1].y - sy, 2), round(best[1].z, 2),
                              round(2 * best[0] * 1000)))
    print(f"{tag}: {len(pts)} points, {nr} rays, LEAKS {nl}")
    if pinch:
        P = np.array(pinch, float)
        keys = {}
        for q in P:
            k = (round(q[0] * 2) / 2, round(q[1] * 2) / 2, round(q[2] * 2) / 2)
            keys.setdefault(k, []).append(q[3])
        for k, v in sorted(keys.items(), key=lambda kv: -len(kv[1]))[:12]:
            print(f"    pinch near {k}: {len(v)} rays, aperture median {np.median(v):.0f} mm max {max(v):.0f} mm")


g = np.linspace
main_attic = [(x, y, z) for x in g(-4.4, 4.4, 9) for y in g(-1.8, 1.8, 4) for z in (3.4, 4.2, 5.0)
              if z < 2.85 + (2.75 - abs(y) - 0.4) * math.tan(math.radians(52))]
wing_attic = [(x, y, z) for x in g(-0.3, 3.3, 4) for y in g(-7.4, -3.0, 5) for z in (3.3, 4.0, 4.6)
              if z < 2.85 + (2.4 - abs(x - 1.5) - 0.4) * math.tan(math.radians(47))]
dormer = [(x, y, z) for x in g(-3.4, -2.6, 3) for y in (-1.95, -1.75, -1.55) for z in (4.3, 4.5)]   # behind the window's dark room
rooms = [(x, y, z) for x in g(-4.4, 4.4, 7) for y in g(-2.2, 2.2, 3) for z in (1.0, 2.2)] + \
        [(x, y, z) for x in g(-0.3, 3.3, 3) for y in g(-7.4, -3.2, 3) for z in (1.0, 2.2)]
probe("MAIN ATTIC", main_attic)
probe("WING ATTIC", wing_attic)
probe("DORMER", dormer)
probe("ROOMS", rooms)
print("DONE")
