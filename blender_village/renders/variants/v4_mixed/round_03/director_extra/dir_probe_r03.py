"""Director probes, v4_mixed round 3.  python dir_probe_r03.py <blend>
Lists objects, junction-object hygiene (non-manifold, degenerate), house parts' reach into the drum, rafter feet at
the drum face, the eave height over the house door, transforms / UVs / Mask, and decal-anchor distances."""
import json
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend = sys.argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()

MILL_AT = np.array((2.82, 1.36))
HOUSE_AT = np.array((-1.462, 0.214))


def world(ob):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices]) if len(me.vertices) else np.zeros((0, 3))
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print("N mesh objects", len(meshes))
for o in sorted(meshes, key=lambda o: o.name):
    if o.name.startswith("V4J") or o.name.startswith("V4H") or (o.name.startswith("V4M") and "corbel" not in o.name
                                                                    and "_kit" not in o.name):
        if o.data.users > 1 and not o.name.startswith("V4J"):
            continue
        V, F = world(o)
        if len(V) == 0:
            print("OBJ %-34s EMPTY" % o.name)
            continue
        print("OBJ %-34s v %7d f %7d  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f users %d" % (
            o.name, len(V), len(F), V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(),
            V[:, 2].max(), o.data.users))

# junction hygiene
for o in meshes:
    if not o.name.startswith("V4J") and o.name not in ("V4H_eave_closure",):
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    nm = [e for e in bm.edges if not e.is_manifold]
    deg = [f for f in bm.faces if f.calc_area() < 1e-9]
    mats = {}
    for e in nm:
        for f in e.link_faces:
            mi = f.material_index
            nmn = o.data.materials[mi].name if o.data.materials and mi < len(o.data.materials) and o.data.materials[mi] else "?"
            mats[nmn] = mats.get(nmn, 0) + 1
    print("HYG %-30s faces %6d nonmanifold %4d degenerate %3d  by mat %s users %d" % (
        o.name, len(bm.faces), len(nm), len(deg), mats, o.data.users))
    bm.free()


# drum field: estimate R(z) from the drum wall core / stones -- use the kit tower_of if importable
sys.path.insert(0, os.path.join(os.path.dirname(blend), "..", "..", "..", "kit"))
def R_drum(z):
    # r 2.05 at 0 -> 1.70 at 5.5 (recipe), linear
    return 2.05 + (1.70 - 2.05) * np.clip(z, 0, 5.5) / 5.5


def field(P):
    return np.hypot(P[:, 0] - MILL_AT[0], P[:, 1] - MILL_AT[1]) - R_drum(P[:, 2])


print("--- house parts into the drum (plan depth inside R(z), m; negative = inside)")
for o in sorted(meshes, key=lambda o: o.name):
    if not o.name.startswith("V4H") or o.data.users > 1:
        continue
    V, F = world(o)
    if len(V) == 0:
        continue
    f = field(V)
    if f.min() < -0.005:
        print("INTO %-30s min %.3f  n_inside(<-1cm) %d  z %.2f..%.2f" % (o.name, f.min(), int((f < -0.01).sum()),
                                                                   V[f < -0.005, 2].min(), V[f < -0.005, 2].max()))

# rafter feet near the drum face
ob = bpy.data.objects.get("V4H_rafters")
if ob:
    V, F = world(ob)
    f = field(V)
    near = V[np.abs(f) < 0.06]
    print("RAFTERS verts near drum face:", len(near))
    if len(near):
        # cluster
        from collections import defaultdict
        keys = defaultdict(list)
        for p in near:
            keys[(round(p[0] / 0.15), round(p[1] / 0.15))].append(p)
        for k, ps in sorted(keys.items()):
            ps = np.array(ps)
            rh = np.hypot(ps[:, 0].mean() - HOUSE_AT[0], ps[:, 1].mean() - HOUSE_AT[1])
            print("  foot ~(%.2f, %.2f) z %.2f..%.2f  r_house %.2f n %d" % (ps[:, 0].mean(), ps[:, 1].mean(),
                                                                         ps[:, 2].min(), ps[:, 2].max(), rh, len(ps)))
    # rafter vertices beyond wall line r 2.55+0.1 within 0.6 m of drum face -> tails near drum
for nm in ("V4H_wall_plate", "V4H_eave_closure", "V4H_battens", "V4H_purlin_rings", "V4H_roof_starter"):
    ob = bpy.data.objects.get(nm)
    if not ob:
        print("MISSING", nm)
        continue
    V, F = world(ob)
    f = field(V)
    sel = V[np.abs(f) < 0.05]
    if len(sel):
        print("FACE %-22s verts at face %d z %.2f..%.2f" % (nm, len(sel), sel[:, 2].min(), sel[:, 2].max()))

# eave height over the house door (door faces -Y at house azimuth 0): sample the roof underside above x in door span
allV, allF = [], []
for o in meshes:
    if not o.name.startswith("V4"):
        continue
    V, F = world(o)
    off = len(allV)
    allV += [tuple(v) for v in V]
    allF += [tuple(i + off for i in f) for f in F]
T = BVHTree.FromPolygons([Vector(v) for v in allV], allF)
for dx in (-0.6, -0.3, 0.0, 0.3, 0.6):
    for ry in (-2.75, -2.95, -3.10):
        o = Vector((HOUSE_AT[0] + dx, HOUSE_AT[1] + ry, 0.6))
        hit = T.ray_cast(o, Vector((0, 0, 1)), 20)
        print("EAVE over door dx %.1f y %.2f -> z %s %s" % (dx, ry, None if hit[0] is None else round(hit[0].z, 3),
                                                            None if hit[2] is None else ""))

# sky rays from under both eave ends and through the junction band from outside
def sky_count(origin, dirs):
    n = 0
    for d in dirs:
        h = T.ray_cast(Vector(origin), Vector(d).normalized(), 60)
        if h[0] is None and d[2] > -0.05:
            n += 1
    return n


# transforms / UV / mask on single-user meshes
bad = []
for o in meshes:
    me = o.data
    ident = all(abs(x) < 1e-6 for x in o.location) and all(abs(x) < 1e-6 for x in o.rotation_euler) and \
        all(abs(x - 1) < 1e-6 for x in o.scale)
    ca = me.color_attributes.get("Mask")
    if (me.users == 1 and not ident) or len(me.uv_layers) == 0 or ca is None:
        bad.append((o.name, ident, len(me.uv_layers), ca is not None))
print("BAD transforms/uv/mask:", bad[:20], len(bad))

# anchors
anc = [o for o in bpy.data.objects if o.name.startswith("DA_")]
dists = []
for a in anc:
    p = a.matrix_world.translation
    loc, nrm, idx, d = T.find_nearest(p)
    dists.append(d)
print("ANCHORS", len(anc), "max dist %.3f" % max(dists), "n > 5cm", sum(d > 0.05 for d in dists))
types = {}
for a in anc:
    t = a.get("decal_type")
    types[t] = types.get(t, 0) + 1
print("ANCHOR types", types)
# anchors on the junction: list those near the drum/house seam
for a in anc:
    p = np.array(a.matrix_world.translation)
    if abs(field(p[None])[0]) < 0.3 and np.hypot(*(p[:2] - HOUSE_AT)) < 3.4:
        print("  JA %-20s %s z %.2f surf %s" % (a.name, a.get("decal_type"), p[2], a.get("surface")))
