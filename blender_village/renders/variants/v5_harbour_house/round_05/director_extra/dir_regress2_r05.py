"""Director round-5 regression probe 2.  python -I dir_regress2_r05.py -- <r04_blend> <r05_blend>
- deck / covering / comb: distance of every r05 vertex from the r04 surface (BVH), split into inside / outside the eyebrow
  zone (|y - Yc| <= 1.6 m, x < 1.0);
- hall / tower stones and hall frames: triangles present in r04 but not in r05 (by rounded centroid), and vice versa."""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
YC = -1.373
NAMES = ["HARB_roof_deck", "HARB_roof_covering", "HARB_roof_comb", "HARB_hall_stones", "HARB_tower_stones", "HARB_hall_frames"]


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for n in NAMES:
        o = bpy.data.objects[n]; e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles()
        mw = o.matrix_world
        V = [mw @ v.co for v in m.vertices]
        T = [tuple(t.vertices) for t in m.loop_triangles]
        out[n] = (V, T)
        e.to_mesh_clear()
    return out


A = load(argv[0]); B = load(argv[1])
for n in NAMES[:3]:
    va, ta = A[n]; vb, tb = B[n]
    bvh = BVHTree.FromPolygons([tuple(v) for v in va], ta)
    din, dout = [], []
    for p in vb:
        hit = bvh.find_nearest(p)
        d = (hit[0] - p).length if hit[0] is not None else 9.0
        (din if (abs(p.y - YC) <= 1.6 and p.x < 1.0) else dout).append((d, tuple(round(c, 2) for c in p)))
    din.sort(reverse=True); dout.sort(reverse=True)
    print(f"SURF {n:22s} inside-zone max {din[0][0] if din else 0:.3f} m; outside-zone max {dout[0][0] if dout else 0:.4f} m at {dout[0][1] if dout else ''}; "
          f"outside > 2 mm: {sum(1 for d, _ in dout if d > 0.002)} of {len(dout)}")
for n in NAMES[3:]:
    def cents(VT):
        V, T = VT
        return {tuple(round(c, 3) for c in (V[a] + V[b] + V[c]) / 3): (V[a], V[b], V[c]) for a, b, c in T}
    ca, cb = cents(A[n]), cents(B[n])
    gone = [k for k in ca if k not in cb]; new = [k for k in cb if k not in ca]
    print(f"TRIS {n}: r04-only {len(gone)}, r05-only {len(new)}")
    for k in gone[:12]:
        a, b, c = ca[k]; area = (b - a).cross(c - a).length / 2
        print(f"   gone centroid {k} area {area*1e4:.2f} cm2")
    for k in new[:12]:
        a, b, c = cb[k]; area = (b - a).cross(c - a).length / 2
        print(f"   new  centroid {k} area {area*1e4:.2f} cm2")
