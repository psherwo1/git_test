"""a1 r03 probe: inverted (negative signed volume) stone islands on the lean-to end walls, and whether host face
99666 (A1L_body_wall_stones, the r02 pick at world (0.65, 2.352, 2.705)) is also present, same facing, in v3.
python -I probe_normals.py <a1.blend> [<v3.blend>]"""
import sys

import bpy  # noqa: I001  (bpy first: it puts bmesh on the path)
import bmesh
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def islands(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    seen = np.zeros(len(bm.faces), bool)
    out = []
    for f in bm.faces:
        if seen[f.index]:
            continue
        st = [f]
        seen[f.index] = True
        isl = []
        while st:
            a = st.pop()
            isl.append(a)
            for e in a.edges:
                for b in e.link_faces:
                    if not seen[b.index]:
                        seen[b.index] = True
                        st.append(b)
        c = Vector((0, 0, 0))
        nv = 0
        for a in isl:
            for v in a.verts:
                c += v.co
                nv += 1
        c /= max(nv, 1)
        vol = 0.0
        closed = all(e.is_manifold for a in isl for e in a.edges)
        for a in isl:
            co = [lo.vert.co - c for lo in a.loops]
            for i in range(1, len(co) - 1):
                vol += co[0].dot(co[i].cross(co[i + 1]))
        out.append(dict(faces=[a.index for a in isl], vol=vol / 6.0, closed=closed,
                        c=tuple(round(x, 3) for x in (ob.matrix_world @ c))))
    bm.free()
    return out


def report(tag, ob):
    isl = islands(ob)
    neg = [i for i in isl if i["vol"] < 0]
    opn = sum(1 for i in isl if not i["closed"])
    print(f"NORM {tag} {ob.name}: islands {len(isl)}, open {opn}, NEGATIVE-volume {len(neg)}", flush=True)
    for i in neg[:8]:
        print(f"    neg island at {i['c']} faces {min(i['faces'])}-{max(i['faces'])} (n {len(i['faces'])}) "
              f"vol {i['vol']:.6f} closed {i['closed']}", flush=True)
    return isl


bpy.ops.wm.open_mainfile(filepath=argv[0])
for ob in sorted((o for o in bpy.data.objects if o.type == "MESH" and "_lean_to_end" in o.name
                  and ("_stones" in o.name or "_quoins" in o.name)), key=lambda o: o.name):
    report("a1", ob)
rw = next(o for o in bpy.data.objects if o.name.endswith("_round_wall_stones"))
bb = np.array([rw.matrix_world @ Vector(c) for c in rw.bound_box])
c_a1 = 0.5 * (bb.min(0) + bb.max(0))
bw = next(o for o in bpy.data.objects if o.name.endswith("_body_wall_stones"))
FI = 99666
if len(bw.data.polygons) > FI:
    p = bw.data.polygons[FI]
    P = np.array(bw.matrix_world @ p.center)
    N = np.array((bw.matrix_world.to_3x3() @ p.normal).normalized())
    print(f"HOST a1 {bw.name} face {FI} at {np.round(P, 3)} normal {np.round(N, 3)}", flush=True)
else:
    P = None
if len(argv) > 1 and P is not None:
    rel = P - c_a1
    bpy.ops.wm.open_mainfile(filepath=argv[1])
    rw = next(o for o in bpy.data.objects if o.name.endswith("_round_wall_stones"))
    bb = np.array([rw.matrix_world @ Vector(c) for c in rw.bound_box])
    c_v3 = 0.5 * (bb.min(0) + bb.max(0))
    Q = c_v3 + rel
    bw = next(o for o in bpy.data.objects if o.name.endswith("_body_wall_stones"))
    M = bw.matrix_world
    best = None
    for q in bw.data.polygons:
        d = (np.array(M @ q.center) - Q)
        dd = float(np.dot(d, d))
        if best is None or dd < best[0]:
            best = (dd, q.index, np.array((M.to_3x3() @ q.normal).normalized()))
    print(f"HOST v3 {bw.name}: nearest face {best[1]} at {best[0] ** 0.5:.4f} m from the a1 point, normal "
          f"{np.round(best[2], 3)}, dot with a1 normal {float(np.dot(best[2], N)):.3f}", flush=True)
