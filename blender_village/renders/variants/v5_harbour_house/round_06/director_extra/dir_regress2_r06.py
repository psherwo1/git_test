"""Director round-6 regression probe 2 (dir_regress2_r05.py, zone moved to the round-6 wave).
python -I dir_regress2_r06.py -- <r05_accepted_blend> <r06_blend>
- deck / covering / comb: distance of every r06 vertex from the r05 surface (BVH), inside / outside the round-6 eyebrow
  zone (|y - YC| <= 2.0 m, x < 1.6; the wave spans y -3.32..0.18, the fade reaches x ~1.42);
- comb / stones / wing covering / hall stones: triangles present in r05 but not in r06 (rounded centroid), and vice versa,
  with area and position (are the recounts hidden-face cull noise or a missing visible piece?)."""
import sys

import bpy
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
YC = -1.57
SURF = ["HARB_roof_deck", "HARB_roof_covering", "HARB_roof_comb"]
TRI = ["HARB_roof_comb", "HARB_tower_stones", "HARB_wing_roof_covering", "HARB_hall_stones"]
NAMES = sorted(set(SURF + TRI))


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for n in NAMES:
        o = bpy.data.objects[n]; e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles()
        mw = o.matrix_world
        out[n] = ([mw @ v.co for v in m.vertices], [tuple(t.vertices) for t in m.loop_triangles])
        e.to_mesh_clear()
    return out


A = load(argv[0]); B = load(argv[1])
for n in SURF:
    va, ta = A[n]; vb, tb = B[n]
    bvh = BVHTree.FromPolygons([tuple(v) for v in va], ta)
    din, dout = [], []
    for p in vb:
        hit = bvh.find_nearest(p)
        d = (hit[0] - p).length if hit[0] is not None else 9.0
        (din if (abs(p.y - YC) <= 2.0 and p.x < 1.6) else dout).append((d, tuple(round(c, 2) for c in p)))
    din.sort(reverse=True); dout.sort(reverse=True)
    print(f"SURF {n:22s} inside-zone max {din[0][0] if din else 0:.3f} m; outside-zone max {dout[0][0] if dout else 0:.4f} m "
          f"at {dout[0][1] if dout else ''}; outside > 2 mm: {sum(1 for d, _ in dout if d > 0.002)} of {len(dout)}", flush=True)
    for d, p in dout[:6]:
        if d > 0.002:
            print(f"   outside {d:.4f} m at {p}")
for n in TRI:
    def cents(VT):
        V, T = VT
        return {tuple(round(c, 3) for c in (V[a] + V[b] + V[c]) / 3): (V[a], V[b], V[c]) for a, b, c in T}
    ca, cb = cents(A[n]), cents(B[n])
    gone = [k for k in ca if k not in cb]; new = [k for k in cb if k not in ca]
    ga = sum((ca[k][1] - ca[k][0]).cross(ca[k][2] - ca[k][0]).length / 2 for k in gone)
    print(f"TRIS {n}: r05-only {len(gone)} ({ga*1e4:.1f} cm2), r06-only {len(new)}", flush=True)
    for k in sorted(gone, key=lambda k: -(ca[k][1] - ca[k][0]).cross(ca[k][2] - ca[k][0]).length)[:10]:
        a, b, c = ca[k]; area = (b - a).cross(c - a).length / 2
        print(f"   gone centroid {k} area {area*1e4:.2f} cm2")
    for k in new[:6]:
        a, b, c = cb[k]; area = (b - a).cross(c - a).length / 2
        print(f"   new  centroid {k} area {area*1e4:.2f} cm2")
