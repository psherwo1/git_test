"""Auditor round-5 hash-rule check (read-only): default code paths of the changed kit modules reproduce round 4.
Compares evaluated vertex arrays (exact) of the meshes built by GableRoof without eyebrows (wing roof) and by the timber
opening path with the default room_pad (tower top windows), plus every mesh, r04 accepted vs r05."""
import sys
import bpy
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]


def dump(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh()
        co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co)
        out[o.name] = co.reshape(-1, 3); o.evaluated_get(dg).to_mesh_clear()
    return out


A, B = dump(a[0]), dump(a[1])
same = [k for k in A if k in B and A[k].shape == B[k].shape and np.abs(A[k] - B[k]).max(initial=0) == 0.0]
diff = [k for k in A if k not in same]
print("r04 meshes", len(A), "r05 meshes", len(B), "bit-identical", len(same))
print("not bit-identical:", diff)
for k in ("HARB_wing_roof_covering", "HARB_wing_roof_deck", "HARB_wing_roof_comb", "HARB_wing_roof_rafters",
          "HARB_wing_roof_verge", "HARB_tower_top_frames", "HARB_tower_top_blockers", "HARB_tower_top_boards"):
    print(f"  {k:32s} bit-identical: {k in same}")
print("new in r05:", sorted(set(B) - set(A)))
