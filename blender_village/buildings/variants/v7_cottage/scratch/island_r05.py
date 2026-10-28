"""round 5: the linked island of a face: size, open edges, how many faces point out of its centroid."""
import sys

import bpy
import bmesh  # noqa: E402  (after bpy)
import numpy as np

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=argv[0])
    ob = bpy.data.objects[argv[1]]
    for fi in argv[2:]:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        f0 = bm.faces[int(fi)]
        seen, stack = {f0.index}, [f0]
        while stack:
            f = stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        F = [bm.faces[i] for i in seen]
        C = np.array([f.calc_center_median() for f in F])
        N = np.array([f.normal for f in F])
        c = C.mean(0)
        out = int(((C - c) * N).sum(1).__gt__(0).sum())
        edges = {e for f in F for e in f.edges}
        open_e = sum(1 for e in edges if len(e.link_faces) < 2)
        print(f"ISLAND face {fi}: {len(F)} faces, {open_e} open edges, {out} outward / {len(F)}; centroid "
              f"{np.round(c, 3)}  bbox {np.round(C.min(0), 2)} .. {np.round(C.max(0), 2)}; face n {np.round(N[0], 2)}")
        print("   face0", np.round(np.array(f0.calc_center_median()), 3), "n", np.round(np.array(f0.normal), 3))
        bm.free()
