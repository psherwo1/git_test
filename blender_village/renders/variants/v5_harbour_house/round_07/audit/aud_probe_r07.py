"""Auditor round-4 read-only probe for v5_harbour_house.  python -I aud_probe_r04.py <blend> <anchors.json>
Compliance (tris, slots, Mask, transforms, collections, anchors), door clearance, islands / floating pieces,
verge-rafter vs bargeboard penetration at the four main eave corners."""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend, ajson = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()
PAL = {"M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber", "M_timber_weathered",
       "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_earth", "M_moss"}

objs = [o for o in bpy.data.objects if o.type == "MESH"]
print("MESH objects", len(objs), " all objects", len(bpy.data.objects))
print("collections", {c.name: len(c.objects) for c in bpy.data.collections})
mats, tri_total, bad_tf, mask_bad = set(), 0, [], []
V, T, OWN = [], [], []
voff = 0
per = {}
for oi, o in enumerate(objs):
    if any(abs(v) > 1e-6 for v in o.location) or any(abs(v) > 1e-6 for v in o.rotation_euler) or \
            any(abs(v - 1) > 1e-6 for v in o.scale):
        bad_tf.append(o.name)
    for s in o.material_slots:
        if s.material:
            mats.add(s.material.name)
    me = o.data
    ca = me.color_attributes.get("Mask")
    ok = ca is not None and ca.domain == "CORNER" and ca.data_type in ("BYTE_COLOR", "FLOAT_COLOR") and \
        me.color_attributes.active_color_name == "Mask" and \
        me.color_attributes[me.color_attributes.render_color_index].name == "Mask"
    if not ok:
        mask_bad.append(o.name)
    ev = o.evaluated_get(dg)
    m = ev.to_mesh()
    m.calc_loop_triangles()
    n = len(m.vertices)
    co = np.empty(n * 3, np.float32); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nt = len(m.loop_triangles)
    tv = np.empty(nt * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    ne = len(m.edges)
    ev_ = np.empty(ne * 2, np.int32); m.edges.foreach_get("vertices", ev_); ev_ = ev_.reshape(-1, 2)
    per[o.name] = (co.copy(), tv.copy(), ev_.copy())
    mw = np.array(o.matrix_world, dtype=np.float64)
    cw = (np.c_[co, np.ones(n)] @ mw.T)[:, :3]
    V.append(cw); T.append(tv + voff); OWN.append(np.full(nt, oi)); voff += n
    tri_total += nt
    ev.to_mesh_clear()
print("triangles (evaluated)", tri_total)
print("materials", len(mats), sorted(mats), "outside palette:", sorted(mats - PAL))
print("non-identity transforms", bad_tf)
print("Mask missing/bad", mask_bad)
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
print("BVH built", len(T))

# ---- decal anchors -----------------------------------------------------------------------------------------
da = bpy.data.collections.get("DECAL_ANCHORS")
emp = [o for o in (da.objects if da else []) if o.type == "EMPTY"]
need = ("decal_type", "size_w", "size_h", "surface", "probability", "seed")
missing = [o.name for o in emp if not all(k in o.keys() for k in need)]
J = json.load(open(ajson))
print("DECAL_ANCHORS empties", len(emp), "missing props", missing[:5], "json count", J["count"], len(J["anchors"]))
names_b = {o.name for o in emp}; names_j = {a["name"] for a in J["anchors"]}
print("anchor name sets equal", names_b == names_j)
# anchor -> surface distance along -normal, and surface material class
far, wrongside = [], []
for a in J["anchors"]:
    p = Vector(a["position"]); nrm = Vector(a["normal"])
    hit = bvh.ray_cast(p + nrm * 0.05, -nrm, 0.25)
    if hit[0] is None:
        far.append(a["name"])
print("anchors with no surface within 20 cm behind them", len(far), far[:10])
zs = {}
for a in J["anchors"]:
    zs.setdefault(a["type"], []).append(round(a["position"][2], 2))
for k, v in zs.items():
    print(f"  {k:13s} n={len(v):3d} z {min(v):6.2f}..{max(v):6.2f}")

# ---- door clearance -----------------------------------------------------------------------------------------
DOORS = {"hall land door": (2.992, -5.773), "wing S door": (-5.908, -7.673)}
for nm, (dx, dy) in DOORS.items():
    rows = []
    for out in (0.15, 0.30, 0.50, 0.75, 1.0, 1.3):
        zmin = 99.0; who = None
        for ox in np.linspace(-0.6, 0.6, 13):
            o = Vector((dx + ox, dy - out, 0.05))
            h = bvh.ray_cast(o, Vector((0, 0, 1)), 30.0)
            if h[0] is not None and h[0].z < zmin:
                zmin = h[0].z; who = objs[OWN[h[2]]].name
        rows.append((out, round(zmin, 3), who))
    print("DOOR", nm, rows)
    # head of the opening itself (ray up just inside the reveal)
    h = bvh.ray_cast(Vector((dx, dy + 0.15, 0.3)), Vector((0, 0, 1)), 10)
    print("   opening head (ray up 15 cm inside the face):", None if h[0] is None else round(h[0].z, 3),
          None if h[0] is None else objs[OWN[h[2]]].name)
    # threshold height
    h = bvh.ray_cast(Vector((dx, dy + 0.05, 1.0)), Vector((0, 0, -1)), 10)
    print("   threshold (ray down at the face):", None if h[0] is None else round(h[0].z, 3),
          None if h[0] is None else objs[OWN[h[2]]].name)

# ---- islands / floating pieces ---------------------------------------------------------------------------------
def islands(nv, edges):
    lab = np.arange(nv)
    if len(edges) == 0:
        return lab
    a, b = edges[:, 0], edges[:, 1]
    while True:
        m = np.minimum(lab[a], lab[b])
        new = lab.copy()
        np.minimum.at(new, a, m); np.minimum.at(new, b, m)
        new = new[new]
        new = new[new]
        if np.array_equal(new, lab):
            return lab
        lab = new


boxes, bown = [], []
for o in objs:
    co, tv, ed = per[o.name]
    if len(co) == 0:
        continue
    lab = islands(len(co), ed)
    used = np.unique(tv.ravel())
    u, inv = np.unique(lab[used], return_inverse=True)
    lo = np.full((len(u), 3), np.inf); hi = np.full((len(u), 3), -np.inf)
    np.minimum.at(lo, inv, co[used]); np.maximum.at(hi, inv, co[used])
    for i in range(len(u)):
        boxes.append(np.r_[lo[i], hi[i]]); bown.append(o.name)
B = np.array(boxes); bown = np.array(bown)
print("islands total", len(B))
E = 0.02
lo, hi = B[:, :3] - E, B[:, 3:] + E
order = np.argsort(lo[:, 0]); los, his = lo[order], hi[order]
iso = []
for k in range(len(order)):
    j1 = np.searchsorted(los[:, 0], his[k, 0], side="right")
    cand = np.arange(0, j1)
    cand = cand[cand != k]
    c = (his[cand, 0] >= los[k, 0]) & (los[cand, 1] <= his[k, 1]) & (his[cand, 1] >= los[k, 1]) & \
        (los[cand, 2] <= his[k, 2]) & (his[cand, 2] >= los[k, 2])
    if not c.any():
        iso.append(order[k])
print("islands whose 2 cm-inflated AABB touches no other island:", len(iso))
for i in iso[:40]:
    print("   ISO", bown[i], np.round(B[i], 3).tolist())

# ---- verge rafter tails vs bargeboards at the four eave corners --------------------------------------------------
def obj_bvh(name):
    co, tv, _ = per[name]
    return BVHTree.FromPolygons(co.tolist(), tv.tolist(), all_triangles=True), co


def inside(bv, p):
    n = 0; o = Vector(p); d = Vector((0.0123, 0.0071, 1.0)).normalized()
    while True:
        h = bv.ray_cast(o, d, 50)
        if h[0] is None:
            return n % 2 == 1
        n += 1; o = h[0] + d * 1e-4


vb, _ = obj_bvh("HARB_roof_verge")
rco = per["HARB_roof_rafters"][0]
for (cx, cy) in ((-1.608, 3.427), (5.392, -5.773), (5.392, 3.427)):
    sel = rco[(np.abs(rco[:, 0] - cx) < 1.2) & (np.abs(rco[:, 1] - cy) < 0.9) & (rco[:, 2] < 3.2)]
    ins = [p for p in sel if inside(vb, p)]
    dep = 0.0
    for p in ins:
        loc, nrm, idx, dist = vb.find_nearest(Vector(p))
        dep = max(dep, dist)
    zmin = sel[:, 2].min() if len(sel) else None
    print(f"CORNER ({cx},{cy}) rafter verts near {len(sel)}, inside bargeboard {len(ins)}, max depth {dep:.3f} m, "
          f"rafter z min {zmin}")
# ---- round 6: eyebrow-specific geometric checks (bigger wave) -----------------------------------------------------
brow = [o.name for o in objs if "eyebrow" in o.name]
print("EYEBROW objects", brow)
allb = np.concatenate([per[n][0] for n in brow])
blo, bhi = allb.min(0), allb.max(0)
print("EYEBROW bbox", np.round(blo, 3).tolist(), np.round(bhi, 3).tolist())
for n in brow:
    c = per[n][0]
    print(f"   {n:30s} tris {len(per[n][1]):5d} bbox {np.round(c.min(0),3).tolist()} {np.round(c.max(0),3).tolist()}")
FX = float(blo[0]); YC = float((blo[1] + bhi[1]) / 2); ZC = float((blo[2] + bhi[2]) / 2)
E = Vector((FX, YC, ZC)); print("EYEBROW front centre (min x, mid y, mid z)", tuple(round(v, 3) for v in E))
others_idx = [i for i, o in enumerate(objs) if "eyebrow" not in o.name]
Vo, To = [], []; off = 0
for i in others_idx:
    co, tv, _ = per[objs[i].name]
    Vo.append(co); To.append(tv + off); off += len(co)
bvh_o = BVHTree.FromPolygons(np.concatenate(Vo).tolist(), np.concatenate(To).tolist(), all_triangles=True)
# (a) floating: each eyebrow island's nearest distance to (non-eyebrow surfaces) OR (any other eyebrow island)
isl = []
for nm in brow:
    co, tv, ed = per[nm]
    lab = islands(len(co), ed)
    for L in np.unique(lab[np.unique(tv.ravel())]):
        vm = lab == L
        tm = vm[tv[:, 0]]
        isl.append((nm, co, tv[tm], vm))
unsupported = []
for k, (nm, co, tvk, vm) in enumerate(isl):
    pts = co[vm]
    samp = pts[:: max(1, len(pts) // 80)]
    d1 = min(bvh_o.find_nearest(Vector(p))[3] for p in samp)
    Vb, Tb, ofs = [], [], 0
    for j, (nm2, co2, tv2, vm2) in enumerate(isl):
        if j == k:
            continue
        Vb.append(co2); Tb.append(tv2 + ofs); ofs += len(co2)
    bb = BVHTree.FromPolygons(np.concatenate(Vb).tolist(), np.concatenate(Tb).tolist(), all_triangles=True)
    d2 = min((bb.find_nearest(Vector(p))[3] for p in samp), default=99)
    if min(d1, d2) > 0.02:
        unsupported.append((nm, round(d1, 3), round(d2, 3), np.round(pts.mean(0), 2).tolist()))
print(f"EYEBROW islands {len(isl)}; > 2 cm from every other surface (roof AND other eyebrow parts): {len(unsupported)}",
      unsupported[:10])
# (b) eyebrow verts inside covering pieces (tucked under the wave's eave; visual check in grey views)
cov_b, cov_co = obj_bvh("HARB_roof_covering")
for nm in brow:
    co = per[nm][0]
    deep = []
    for p in co:
        loc, nrm, idx, dist = cov_b.find_nearest(Vector(p))
        if loc is not None and (Vector(p) - loc).dot(nrm) < 0 and dist > 0.02:
            deep.append((round(dist, 3), np.round(p, 2).tolist()))
    deep.sort(reverse=True)
    print(f"  {nm}: verts {len(co)}, verts > 2 cm inside a covering piece: {len(deep)}  deepest {deep[:4]}")
# (c) the comb over the wave vs either side
comb = per["HARB_roof_comb"][0]
roofparts = [i for i, o in enumerate(objs) if o.name in ("HARB_roof_covering", "HARB_roof_deck", "HARB_roof_shingles",
                                                          "HARB_roof_starter", "HARB_roof_underlap")]
Vr, Tr = [], []; off = 0
for i in roofparts:
    co, tv, _ = per[objs[i].name]; Vr.append(co); Tr.append(tv + off); off += len(co)
bvh_r = BVHTree.FromPolygons(np.concatenate(Vr).tolist(), np.concatenate(Tr).tolist(), all_triangles=True)
for y0, y1, tag in ((YC - 1.6, YC + 1.6, "over eyebrow"), (-5.2, -4.4, "reference S"), (0.6, 1.4, "reference N")):
    sel = comb[(comb[:, 1] > y0) & (comb[:, 1] < y1)]
    d = np.array([bvh_r.find_nearest(Vector(p))[3] for p in sel])
    print(f"COMB {tag} y {y0:.2f}..{y1:.2f}: verts {len(sel)}, nearest-roof distance max {d.max():.3f} m, "
          f"p95 {np.percentile(d, 95):.3f}")
# (d) dense ray probe aimed at the front / wave / lip from outside (origins 4 m out). A miss is classified:
#     target ABOVE the roof surface (ray straight up from it hits nothing) = open air over the hood, not a hole;
#     target under the roof = a see-through. First hits on interior objects = a peek into the hall.
INTERIOR = ("HARB_rafters", "HARB_purlin_rings", "HARB_partition", "HARB_hall_frames", "HARB_water_gable",
            "HARB_hall_floor", "HARB_tower_floor")
leaks_air, leaks_hole, peeks, n, hitobj = 0, [], {}, 0, {}
up, dn = Vector((0, 0, 1)), Vector((0, 0, -1))
for yaw in (-60, -35, -15, 0, 15, 35, 60):
    for pitch in (-35, -15, 0, 15, 30):
        a, b = math.radians(180 + yaw), math.radians(pitch)
        dvec = -Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
        for yy in np.arange(blo[1] - 0.25, bhi[1] + 0.25, 0.04):
            for zz in np.arange(blo[2] - 0.1, bhi[2] + 0.45, 0.04):
                tgt = Vector((FX + 0.02, yy, zz))
                o = tgt - dvec * 4.0
                h = bvh.ray_cast(o, dvec, 30.0)
                n += 1
                if h[0] is None:
                    if bvh.ray_cast(tgt, up, 30.0)[0] is None:
                        leaks_air += 1
                    else:
                        leaks_hole.append((yaw, pitch, round(float(yy), 2), round(float(zz), 2)))
                    continue
                nm = objs[OWN[h[2]]].name
                hitobj[nm] = hitobj.get(nm, 0) + 1
                if nm.startswith(INTERIOR):
                    peeks[nm] = peeks.get(nm, 0) + 1
print(f"EYEBROW RAY PROBE: {n} rays; misses over open air above the hood {leaks_air}; misses through a target UNDER "
      f"the roof (see-through) {len(leaks_hole)} {leaks_hole[:12]}; first hits on interior objects {peeks}")
print("   first-hit objects:", dict(sorted(hitobj.items(), key=lambda kv: -kv[1])[:14]))
# (e) clearance of the eyebrow from the tower abutment / wing roof (nearest distance, eyebrow verts vs those objects)
for nm2 in ("HARB_roof_wall_abutment", "HARB_wing_roof_covering", "HARB_partition", "HARB_tower_stones"):
    if nm2 in per:
        bv2, _ = obj_bvh(nm2)
        dmin = min(bv2.find_nearest(Vector(p))[3] for p in allb[::3])
        print(f"CLEAR eyebrow objects -> {nm2}: min distance {dmin:.3f} m")
print("DONE")
