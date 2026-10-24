"""a1 r03 probe: stone islands whose FRONT points into the wall (area-vector of the open shell . the path's outward
normal < 0).  python -I probe_facing.py <blend> <shift_x> <shift_y> <tag>"""
import sys

import bpy  # noqa: I001
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, tag = argv[0], argv[3]
sys.path.insert(0, r"C:\GitHubDesktop\git_test\blender_village\kit")
from village_kit.components.rubble_walls import PathMap  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=blend)
if argv[1] == "auto":                       # the round wall is centred on the recipe origin
    from mathutils import Vector
    rw = next(o for o in bpy.data.objects if o.name.endswith("_round_wall_stones"))
    bb = np.array([rw.matrix_world @ Vector(c) for c in rw.bound_box])
    sx, sy = [float(v) for v in 0.5 * (bb.min(0) + bb.max(0))[:2]]
else:
    sx, sy = float(argv[1]), float(argv[2])
print(f"SHIFT {tag} {sx:.3f} {sy:.3f}", flush=True)
X_GABLE, HALF, X_END = -13.0, 2.6, -2.0
PATHS = {"_body_wall_stones": [(X_END, HALF), (X_GABLE, HALF), (X_GABLE, -HALF), (X_END, -HALF)]}
O, n, t, d = np.array([-6.2, 2.6]), np.array([0.0, 1.0]), np.array([1.0, 0.0]), float(__import__("os").environ.get("LEAN_D", "1.9"))
for k, (sa, sb) in enumerate(((-2.0, -1.6), (1.6, 2.0))):
    A0, B0 = O + t * sa, O + t * sb
    PATHS[f"_lean_to_end{k}_stones"] = [tuple(B0 - n * 0.10), tuple(B0 + n * d), tuple(A0 + n * d), tuple(A0 - n * 0.10)]


def bad_islands(ob, pm):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bm.faces.ensure_lookup_table()
    seen = np.zeros(len(bm.faces), bool)
    bad, tot = [], 0
    for f in bm.faces:
        if seen[f.index]:
            continue
        st, isl = [f], []
        seen[f.index] = True
        while st:
            a = st.pop()
            isl.append(a)
            for e in a.edges:
                for b in e.link_faces:
                    if not seen[b.index]:
                        seen[b.index] = True
                        st.append(b)
        tot += 1
        S = sum((a.normal * a.calc_area() for a in isl), start=isl[0].normal * 0.0)
        A = sum(a.calc_area() for a in isl)
        c = sum((a.calc_center_median() for a in isl), start=isl[0].normal * 0.0) / len(isl)
        q = np.array([c.x - sx, c.y - sy])
        # nearest run of the path
        best = None
        for i in range(len(pm.L)):
            a0 = pm.A[i]
            u = np.clip(np.dot(q - a0, pm.dir[i]), 0.0, pm.L[i])
            dd = np.linalg.norm(q - (a0 + u * pm.dir[i]))
            if best is None or dd < best[0]:
                best = (dd, i)
        nn = pm.nrm[best[1]]
        dot = S.x * nn[0] + S.y * nn[1]
        if S.length > 0.05 * A and dot < -0.3 * S.length:
            bad.append((tuple(round(v, 3) for v in c), min(a.index for a in isl), max(a.index for a in isl),
                        round(dot / max(S.length, 1e-9), 2), round(A, 4)))
    bm.free()
    return tot, bad


for frag, path in PATHS.items():
    ob = next((o for o in bpy.data.objects if o.name.endswith(frag)), None)
    if ob is None:
        continue
    tot, bad = bad_islands(ob, PathMap(path))
    print(f"FACING {tag} {ob.name}: islands {tot}, front INTO the wall {len(bad)}", flush=True)
    for b in bad[:12]:
        print("    ", b, flush=True)
