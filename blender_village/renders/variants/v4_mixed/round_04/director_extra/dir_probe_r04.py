"""Director probes, v4_mixed round 4, on the delivered .blend.
1  r3 probe 5 (house wall head, 4 m / 6 m eye-level rings) -- back-face hits on ANY V4 object, not only the r3 list
2  wide ring probe: eye-level rings (z 1.0 / 1.65) at 4 m and 6 m round each wing, rays over the whole visible wall
   (z 0.2-3.4 on the house, 0.2-5.4 on the drum), back-face hits per object
3  door-head probe: rays from the door approach into the door head / eave cheek region
4  hygiene: triangles (evaluated), objects, palette, Mask, UVs, transforms, degenerate faces and edges with > 2 faces
   on the parts touched this round, boundary edges of the wall-head band parts
5  decal anchors: count, type mix, distance to the nearest surface
python dir_probe_r04.py <blend>"""
import math
import sys
from collections import Counter, defaultdict

import bpy  # noqa: I001 (bpy before bmesh)
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
H = Vector((-1.462, 0.214, 0.0))
M = Vector((2.82, 1.36, 0.0))


def cast(cam, p):
    d = (p - cam).normalized()
    return d, scn.ray_cast(dg, cam, d)


# ---- 1 probe 5 (any object) ----------------------------------------------------------------------------------
tot = back = 0
by = Counter()
for R in (4.0, 6.0):
    for az in range(-180, 180, 15):
        a = math.radians(az)
        cam = H + Vector((math.cos(a) * R, math.sin(a) * R, 1.65))
        if (cam - M).to_2d().length < 2.4:
            continue
        for da in range(-24, 25, 2):
            for zi in range(0, 11):
                aa = a + math.radians(da)
                for rr in (2.45, 2.60, 2.75):
                    p = H + Vector((math.cos(aa) * rr, math.sin(aa) * rr, 2.45 + 0.05 * zi))
                    d, (hit, loc, nrm, idx, ob, Mx) = cast(cam, p)
                    if not hit or not ob.name.startswith("V4"):
                        continue
                    tot += 1
                    if nrm.dot(d) > 0:
                        back += 1
                        by[(ob.name, az, R)] += 1
print("PROBE5-ANY back-face hits %d of %d" % (back, tot))
agg = Counter()
for (n, az, R), k in by.items():
    agg[n] += k
print("  by object", dict(agg))
print("  by camera", sorted(((az, R, n), k) for (n, az, R), k in by.items())[:40])

# ---- 2 wide ring probe -----------------------------------------------------------------------------------------
for wname, C, rw, z0, z1 in (("house", H, 2.55, 0.2, 3.4), ("drum", M, 1.95, 0.2, 5.4)):
    tot = back = sky = 0
    objs = Counter()
    zs = Counter()
    for R in (rw + 1.5, rw + 3.5):
        for ze in (1.0, 1.65):
            for az in range(-180, 180, 10):
                a = math.radians(az)
                cam = C + Vector((math.cos(a) * R, math.sin(a) * R, ze))
                other = M if wname == "house" else H
                orad = 2.3 if wname == "house" else 2.9
                if (cam - other).to_2d().length < orad:
                    continue
                for da in range(-30, 31, 6):
                    aa = a + math.radians(da)
                    for zi in range(0, 12):
                        z = z0 + (z1 - z0) * zi / 11.0
                        p = C + Vector((math.cos(aa) * rw, math.sin(aa) * rw, z))
                        d, (hit, loc, nrm, idx, ob, Mx) = cast(cam, p)
                        if not hit:
                            continue
                        if not ob.name.startswith("V4"):
                            continue
                        tot += 1
                        if nrm.dot(d) > 0:
                            back += 1
                            objs[ob.name] += 1
                            zs[round(loc.z, 1)] += 1
    print(f"WIDE {wname}: back-face hits {back} of {tot}; {dict(objs.most_common(12))}")
    print(f"   z of back hits {sorted(zs.items())[:30]}")

# ---- 3 door head -------------------------------------------------------------------------------------------------
tot = back = through = 0
objs = Counter()
for cx in (-0.9, -0.45, 0.0, 0.45, 0.9):
    for cy, cz in ((-3.4, 1.0), (-3.6, 1.65), (-4.3, 1.65), (-3.2, 1.4)):
        cam = H + Vector((cx, cy, cz))
        for tx in range(-12, 13):
            for tz in range(0, 9):
                p = H + Vector((tx * 0.06, -2.6, 2.15 + tz * 0.05))
                d, (hit, loc, nrm, idx, ob, Mx) = cast(cam, p)
                if not hit:
                    through += 1
                    continue
                tot += 1
                if nrm.dot(d) > 0:
                    back += 1
                    objs[ob.name] += 1
print(f"DOORHEAD back-face hits {back} of {tot}, sky {through}; {dict(objs)}")

# ---- 4 hygiene ---------------------------------------------------------------------------------------------------
tris = 0
mats = set()
nomask, nouv, xf = [], [], []
for ob in scn.objects:
    if ob.type != "MESH":
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    ev.to_mesh_clear()
    for s in ob.material_slots:
        if s.material:
            mats.add(s.material.name)
    if "Mask" not in ob.data.color_attributes:
        nomask.append(ob.name)
    if not ob.data.uv_layers:
        nouv.append(ob.name)
    if ob.data.users == 1:
        mw = ob.matrix_world
        if any(abs(mw[i][j] - (1.0 if i == j else 0.0)) > 1e-5 for i in range(4) for j in range(4)):
            xf.append(ob.name)
print(f"TRIS {tris}; objects {len([o for o in scn.objects if o.type == 'MESH'])}; mats {len(mats)} {sorted(mats)}")
print(f"  no Mask {nomask}; no UV {nouv}; non-identity single-user {xf[:10]} ({len(xf)})")
for name in ("V4H_daub", "V4H_wall_plate", "V4H_posts", "V4H_wattle_rods", "V4H_door_frame", "V4H_eave_closure",
             "V4H_roof_shingles", "V4M_base_stones", "V4M_base_dressed", "V4M_arcade_dressed", "V4M_tower_boards",
             "V4M_wheel_blades", "V4J_roof_tower_fillet", "V4J_abutment_posts"):
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("  missing", name)
        continue
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    deg = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
    many = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bnd = [e for e in bm.edges if e.is_boundary]
    hb = sum(1 for e in bnd if 2.30 <= (e.verts[0].co.z + e.verts[1].co.z) / 2 <= 3.0)
    print(f"  {name}: {len(bm.faces)} faces, degenerate {deg}, >2-face edges {many}, boundary {len(bnd)} "
          f"(z 2.30-3.00: {hb})")
    bm.free()

# ---- 5 anchors ---------------------------------------------------------------------------------------------------
col = bpy.data.collections.get("DECAL_ANCHORS")
meshes = [o for o in scn.objects if o.type == "MESH"]
trees = []
for o in meshes:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    trees.append(BVHTree.FromBMesh(bm))
    bm.free()
if col:
    ems = [o for o in col.all_objects if o.type == "EMPTY"]
    dist = []
    types = Counter()
    zs = defaultdict(list)
    for e in ems:
        p = e.matrix_world.translation
        best = min((t.find_nearest(p)[3] for t in trees if t.find_nearest(p)[0] is not None), default=9)
        dist.append(best)
        tp = e.get("decal_type")
        types[tp] += 1
        zs[tp].append(round(p.z, 2))
    print(f"ANCHORS {len(ems)}; max dist {max(dist):.3f}; >5cm {sum(1 for d in dist if d > 0.05)}; {dict(types)}")
    for k, v in zs.items():
        print(f"   {k}: z {min(v)}..{max(v)}")
