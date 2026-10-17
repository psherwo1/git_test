"""Director round-1 probe for v5_harbour_house: object bboxes, materials, floating islands, transforms.
python -I dir_probe_r01.py <blend>"""
import sys
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
meshes = [o for o in scn.objects if o.type == "MESH"]
print("COLLECTIONS", [c.name for c in bpy.data.collections])
for o in sorted(meshes, key=lambda o: o.name):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]
    mx = [max(v[i] for v in bb) for i in range(3)]
    ident = o.matrix_world.is_identity if hasattr(o.matrix_world, "is_identity") else None
    mats = sorted({s.material.name for s in o.material_slots if s.material})
    ca = o.data.color_attributes.get("Mask")
    print("OBJ %-30s tris~%7d users %d ident %s mask %s min %s max %s %s" % (
        o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), o.data.users, ident,
        (ca.domain, ca.data_type) if ca else None,
        tuple(round(x, 2) for x in mn), tuple(round(x, 2) for x in mx), mats))
print("EMPTIES", len([o for o in scn.objects if o.type == "EMPTY"]))

# floating islands (> 1 cm from any other object or other island of the same object)
bvh = {}
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bvh[o.name] = BVHTree.FromBMesh(bm); bm.free()
keys = ("verge", "jetty", "deck", "ladder", "quay", "steps", "ironwork", "openings", "frame", "comb")
for o in meshes:
    if "blocker" in o.name or not any(k in o.name for k in keys):
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bm.verts.ensure_lookup_table()
    seen = set(); islands = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; isl = []; seen.add(v.index)
        while stack:
            w = stack.pop(); isl.append(w.index)
            for e in w.link_edges:
                u = e.other_vert(w)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        islands.append(isl)
    # per-island BVH of the same object minus the island: approximate with the whole object, excluding
    # points of the island itself by testing distance to the other objects AND to other islands' verts
    isl_of = {}
    for k, isl in enumerate(islands):
        for i in isl:
            isl_of[i] = k
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bm.verts))
    for v in bm.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    worst = []
    for k, isl in enumerate(islands):
        step = max(1, len(isl) // 80)
        best = 1e9
        for i in isl[::step]:
            p = bm.verts[i].co
            for n_, t in bvh.items():
                if n_ == o.name:
                    continue
                r = t.find_nearest(p, 0.3)
                if r[0] is not None:
                    best = min(best, r[3])
            if best < 0.01:
                break
        if best >= 0.01:
            # other islands of the same object (vertex proximity)
            for i in isl[::step]:
                for (co, j, d) in kd.find_range(bm.verts[i].co, 0.06):
                    if isl_of[j] != k:
                        best = min(best, d)
                if best < 0.03:
                    break
        if best > 0.03:
            c = sum((bm.verts[i].co for i in isl), Vector()) / len(isl)
            worst.append((round(best * 100, 1), tuple(round(x, 2) for x in c), len(isl)))
    worst.sort(reverse=True)
    print("ISLANDS %-30s n=%5d floating>3cm: %d %s" % (o.name, len(islands), len(worst), worst[:8]))
    bm.free()
