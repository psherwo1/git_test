"""Director inspection, round 10: objects, wattle patch clusters, decal-anchor audit.
Run: blender -b <blend> --python dir_inspect_r10.py -- <anchors.json> <out.json>
"""
import bpy, json, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
anch_path, out_path = argv[0], argv[1]
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
res = {}

objs = []
for o in scn.objects:
    if o.type == "MESH":
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        objs.append((o.name, len(me.loop_triangles), [s.material.name if s.material else None for s in o.material_slots],
                     o.users_collection[0].name if o.users_collection else None, o.data.users))
        ev.to_mesh_clear()
res["objects"] = sorted(objs, key=lambda t: -t[1])

# wattle rod clusters by azimuth (az = atan2(x, -y): 0 = door / -Y, +90 = +X)
rods = bpy.data.objects.get("HUT_wattle_rods")
clusters = []
if rods:
    pts = [rods.matrix_world @ v.co for v in rods.data.vertices]
    bins = {}
    for p in pts:
        az = math.degrees(math.atan2(p.x, -p.y))
        b = int(math.floor(az))
        bins.setdefault(b, []).append(p.z)
    keys = sorted(bins)
    cur = None
    for k in keys:
        if cur and k - cur["hi"] <= 2:
            cur["hi"] = k; cur["z"] += bins[k]
        else:
            if cur: clusters.append(cur)
            cur = {"lo": k, "hi": k, "z": list(bins[k])}
    if cur: clusters.append(cur)
    clusters = [{"az": [c["lo"], c["hi"] + 1], "z": [round(min(c["z"]), 3), round(max(c["z"]), 3)], "n": len(c["z"])} for c in clusters]
res["rod_clusters"] = clusters

# Decal anchors
J = json.load(open(anch_path))
col = bpy.data.collections.get("DECAL_ANCHORS")
empties = {o.name: o for o in (col.all_objects if col else [])}
rep = []
slot_of = lambda ob, fi: (ob.material_slots[ob.data.polygons[fi].material_index].material.name
                         if ob and ob.type == "MESH" and ob.material_slots else None)
for a in J["anchors"]:
    p = Vector(a["position"]); n = Vector(a["normal"]).normalized(); up = Vector(a["up"]).normalized()
    rt = up.cross(n).normalized()
    e = empties.get(a["name"])
    emp_ok = None
    if e:
        mw = e.matrix_world
        ez = (mw.to_3x3() @ Vector((0, 0, 1))).normalized()
        emp_ok = ((mw.translation - p).length < 1e-3, round(ez.dot(n), 4),
                  all(k in e.keys() for k in ("decal_type", "size_w", "size_h", "surface", "probability", "seed")))
    hit, loc, nor, fi, ob, _ = scn.ray_cast(dg, p + n * 0.15, -n, distance=0.4)
    centre = None
    if hit:
        centre = (ob.name, slot_of(ob, fi), round((loc - p).length, 4), round(nor.dot(n), 3))
    w, h = a["size"]
    fp = []
    nsum = Vector()
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            q = p + rt * (i * 0.45 * w) + up * (j * 0.45 * h)
            hh, ll, nn, ff, oo, _ = scn.ray_cast(dg, q + n * 0.15, -n, distance=0.4)
            if hh:
                s = slot_of(oo, ff)
                fp.append(s == a["surface"] and abs((ll - q).dot(n)) < 0.06)
                nsum += nn
            else:
                fp.append(False)
    rep.append({"name": a["name"], "type": a["type"], "pos": [round(x, 3) for x in a["position"]],
                "n": [round(x, 2) for x in a["normal"]], "size": a["size"], "surf": a["surface"],
                "empty": emp_ok, "centre": centre, "fp_ok": sum(fp),
                "fp_ndot": round(nsum.normalized().dot(n), 3) if nsum.length else None})
res["anchors"] = rep
res["empties_in_col"] = len(empties)
res["json_count"] = len(J["anchors"])
json.dump(res, open(out_path, "w"), indent=1)
print("DONE", out_path)

