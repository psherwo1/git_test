"""Director round-2 probe for v5_harbour_house: objects, islands, rays at junctions, anchor occlusion.
python -I dir_probe_r02.py -- <blend> <anchors.json>"""
import json
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1:]
blend, aj = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
meshes = [o for o in scn.objects if o.type == "MESH"]
print("COLLECTIONS", [(c.name, len(c.objects)) for c in bpy.data.collections])
dg = bpy.context.evaluated_depsgraph_get()
tot = 0
for o in sorted(meshes, key=lambda o: o.name):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]
    mx = [max(v[i] for v in bb) for i in range(3)]
    mats = sorted({s.material.name for s in o.material_slots if s.material})
    ca = o.data.color_attributes.get("Mask")
    act = o.data.color_attributes.active_color_name if hasattr(o.data.color_attributes, "active_color_name") else "?"
    t = sum(len(p.vertices) - 2 for p in o.data.polygons)
    tot += t
    print("OBJ %-34s tris %7d users %d ident %s mask %s act %s min %s max %s %s uv %d" % (
        o.name, t, o.data.users, o.matrix_world == o.matrix_world.Identity(4),
        (ca.domain, ca.data_type) if ca else None, act,
        tuple(round(x, 2) for x in mn), tuple(round(x, 2) for x in mx), mats, len(o.data.uv_layers)))
print("TOTAL tris", tot, "EMPTIES", len([o for o in scn.objects if o.type == "EMPTY"]))

bvh = {}
allbm = bmesh.new()
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bvh[o.name] = BVHTree.FromBMesh(bm)
    bm.free()


def ray(p, d, maxd=50.0, skip=()):
    p, d = Vector(p), Vector(d).normalized()
    best = None
    for n_, t in bvh.items():
        if any(s in n_ for s in skip):
            continue
        r = t.ray_cast(p, d, maxd)
        if r[0] is not None and (best is None or r[3] < best[1]):
            best = (n_, r[3], tuple(round(x, 3) for x in r[0]))
    return best


def nearest(p, maxd=0.5, skip=()):
    best = None
    for n_, t in bvh.items():
        if any(s in n_ for s in skip):
            continue
        r = t.find_nearest(Vector(p), maxd)
        if r[0] is not None and (best is None or r[3] < best[1]):
            best = (n_, round(r[3], 4), tuple(round(x, 3) for x in r[0]))
    return best


PROBES = [
    # tie beam bearing on the piers (cast down from just under the tie, outer pier zone)
    ("tie->E pier", (4.55, 3.30, 3.36), (0, 0, -1)),
    ("tie->W pier", (-0.75, 3.30, 3.36), (0, 0, -1)),
    ("tie underside up E", (4.55, 3.30, 3.0), (0, 0, 1)),
    # posts / pads in the slip (from the slip centre outward at several z)
    ("slip +X z=-0.6 (quay)", (1.9, 2.0, -0.6), (1, 0, 0)),
    ("slip +X z=0.5 (wall)", (1.9, 2.0, 0.5), (1, 0, 0)),
    ("slip -X z=-0.6 (quay)", (1.9, 2.0, -0.6), (-1, 0, 0)),
    ("slip -X z=0.5 (wall)", (1.9, 2.0, 0.5), (-1, 0, 0)),
    ("slip +X at post y=3.30 z=1.0", (1.9, 3.30, 1.0), (1, 0, 0)),
    ("slip +X at post y=3.30 z=-0.15 (pad)", (1.9, 3.30, -0.15), (1, 0, 0)),
    ("below E pad", (4.05, 3.35, -0.35), (0, 0, -1)),
    ("slip head -Y z=-0.6", (1.9, 2.0, -0.6), (0, -1, 0)),
    ("slip head -Y z=0.5 (partition)", (1.9, 2.0, 0.5), (0, -1, 0)),
    ("slip head -Y z=0.02", (1.9, 2.0, 0.02), (0, -1, 0)),
    ("partition foot down", (1.9, 0.20, 0.10), (0, 0, -1)),
    # water face: quay face vs pier face
    ("water face pier W z=0.5", (-0.8, 6.0, 0.5), (0, -1, 0)),
    ("water face pier W z=-0.5", (-0.8, 6.0, -0.5), (0, -1, 0)),
    ("water face quay x=-2.5 z=-0.5", (-2.5, 6.0, -0.5), (0, -1, 0)),
    ("water face quay x=-2.5 z=0.3 (should miss)", (-2.5, 6.0, 0.3), (0, -1, 0)),
    ("water face pier E z=0.5", (4.6, 6.0, 0.5), (0, -1, 0)),
    # arch: up through the opening at centre
    ("arch crown up", (1.892, 3.40, 1.0), (0, 0, 1)),
    ("arch crown up behind", (1.892, 3.20, 1.0), (0, 0, 1)),
    ("gable infill from water z=5", (1.0, 8.0, 5.0), (0, -1, 0)),
    ("gable infill from water z=7", (1.892, 8.0, 7.0), (0, -1, 0)),
    # jetty / quay
    ("jetty deck down", (6.8, 5.0, 0.5), (0, 0, -1)),
    ("jetty ledger -Y z=-0.3", (6.8, 4.5, -0.3), (0, -1, 0)),
    ("jetty at quay seam down", (6.8, 3.45, 0.5), (0, 0, -1)),
    # roof over the doors
    ("hall door up", (2.992, -6.2, 1.0), (0, 0, 1)),
    ("wing door up", (-5.408, -8.0, 1.0), (0, 0, 1)),
    # wing roof / hall / tower pocket
    ("pocket NW down", (-1.25, -3.40, 6.0), (0, 0, -1)),
    ("pocket N of wing ridge down", (-1.55, -3.95, 6.0), (0, 0, -1)),
]
for name, p, d in PROBES:
    print("RAY %-40s %s" % (name, ray(p, d)))

for name, p in [("E pad", (4.05, 3.35, -0.15)), ("W pad", (-0.27, 3.35, -0.15)),
                ("E post foot", (4.05, 3.35, 0.02)), ("partition foot", (1.9, 0.20, -0.03))]:
    print("NEAR %-20s %s" % (name, nearest(p, 0.5)))

# floating islands
keys = ("water_gable", "verge", "jetty", "ladder", "quay", "ironwork", "frames", "finial", "tower_top", "partition",
        "cap_collar", "eave_fill", "abutment", "comb", "dressed")
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
    isl_of = {}
    for k, isl in enumerate(islands):
        for i in isl:
            isl_of[i] = k
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
            for i in isl[::step]:
                for (co, j, dd) in kd.find_range(bm.verts[i].co, 0.06):
                    if isl_of[j] != k:
                        best = min(best, dd)
                if best < 0.03:
                    break
        if best > 0.03:
            c = sum((bm.verts[i].co for i in isl), Vector()) / len(isl)
            worst.append((round(best * 100, 1), tuple(round(x, 2) for x in c), len(isl)))
    worst.sort(reverse=True)
    print("ISLANDS %-34s n=%5d floating>3cm: %d %s" % (o.name, len(islands), len(worst), worst[:6]))
    bm.free()

# anchors: occlusion along the normal and distance to the surface
A = json.load(open(aj))["anchors"]
bad = 0
for a in A:
    p = Vector(a["position"]); n = Vector(a["normal"])
    occ = ray(p + n * 0.03, n, 0.6)
    near = nearest(p, 0.2)
    if occ is not None or near is None or near[1] > 0.05:
        bad += 1
        print("ANCHOR %-22s %-18s z %.2f occluded_by %s near %s" % (a["name"], a["surface"], p.z, occ, near))
print("ANCHORS checked", len(A), "flagged", bad)
