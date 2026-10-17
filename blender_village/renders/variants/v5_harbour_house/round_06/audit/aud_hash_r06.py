"""Auditor round-6 regression / hash-rule check (read-only): every mesh r05 accepted vs r06, exact, plus for changed
meshes the max distance of r06 vertices from the r05 surface OUTSIDE the eyebrow zone."""
import sys
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


A, B = dump(a[0]), dump(a[1])
same = [k for k in B if k in A and A[k][0].shape == B[k][0].shape and np.abs(A[k][0] - B[k][0]).max(initial=0) == 0.0]
diff = [k for k in B if k not in same]
print("r05 meshes", len(A), "r06 meshes", len(B), "bit-identical", len(same))
for k in ("HARB_wing_roof_covering", "HARB_wing_roof_deck", "HARB_wing_roof_comb", "HARB_wing_roof_rafters",
          "HARB_wing_roof_verge", "HARB_tower_top_frames", "HARB_tower_top_blockers", "HARB_tower_top_boards",
          "HARB_roof_comb", "HARB_roof_wall_abutment", "HARB_wing_roof_wall_abutment"):
    print(f"  {k:32s} bit-identical: {k in same}  in r06: {k in B}")
print("new in r06:", sorted(set(B) - set(A)), " gone:", sorted(set(A) - set(B)))
ZONE = lambda p: (np.abs(p[:, 1] + 1.57) <= 2.1) & (p[:, 0] < 1.6)
for k in diff:
    if k not in A:
        continue
    ca, ta = A[k]; cb, tb = B[k]
    bv = BVHTree.FromPolygons(ca.tolist(), ta.tolist(), all_triangles=True)
    z = ZONE(cb)
    out = cb[~z]
    d = np.array([bv.find_nearest(Vector(p))[3] for p in out]) if len(out) else np.zeros(1)
    # reverse: r05 verts outside the zone vs the r06 surface (detects removed geometry)
    bvb = BVHTree.FromPolygons(cb.tolist(), tb.tolist(), all_triangles=True)
    outa = ca[~ZONE(ca)]
    dr = np.array([bvb.find_nearest(Vector(p))[3] for p in outa]) if len(outa) else np.zeros(1)
    print(f"CHANGED {k:28s} tris r05 {len(ta):6d} r06 {len(tb):6d} | verts outside zone {len(out):6d}: r06->r05 max "
          f"{d.max()*1000:.2f} mm (>2 mm: {(d > 0.002).sum()}) | r05->r06 max {dr.max()*1000:.2f} mm (>2 mm: "
          f"{(dr > 0.002).sum()})")
    if (dr > 0.002).sum():
        bad = outa[dr > 0.002]
        print("     r05 verts not on r06 surface, bbox", np.round(bad.min(0), 2).tolist(), np.round(bad.max(0), 2).tolist())
print("DONE")
