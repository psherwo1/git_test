"""Auditor a1_longhouse_addons round-4 read-only probe.  blender -b -P aud_probe_r04.py -- <blend> <anchors.json>
Compliance (tris, palette, Mask, transforms), decal anchors (collection vs json, surface behind / buried, the new
round-roof moss anchors), door clearance measured on the mesh (host front door under the porch, the lean-to's open
front), islands / floating pieces, add-on geometry poking into the host room, poke-through from above on the add-on
roofs, and the wall thickness used by the see-through probe.
World = plan + (+4.606, -0.328): host N face y 2.272, S face y -2.928, gable face x -8.394, round centre (4.606,-0.328);
door x -2.394 (1.0 wide, 2.10 high); lean-to x -3.594..0.406, front y 4.272; porch front beam y -3.928."""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
blend, ajson = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()
PAL = {"M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber", "M_timber_weathered",
       "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_earth", "M_moss"}
objs = [o for o in bpy.data.objects if o.type == "MESH"]
print("MESH objects", len(objs), "all objects", len(bpy.data.objects))
mats, tri_total, bad_tf, mask_bad, empty_slot = set(), 0, [], [], []
V, T, OWN = [], [], []
per = {}
voff = 0
for oi, o in enumerate(objs):
    for s in o.material_slots:
        if s.material:
            mats.add(s.material.name)
        else:
            empty_slot.append(o.name)
    me = o.data
    ca = me.color_attributes.get("Mask")
    ok = ca is not None and ca.domain == "CORNER" and me.color_attributes.active_color_name == "Mask"
    if not ok:
        mask_bad.append((o.name, None if ca is None else ca.domain, me.color_attributes.active_color_name))
    ev = o.evaluated_get(dg)
    m = ev.to_mesh(); m.calc_loop_triangles()
    n = len(m.vertices)
    co = np.empty(n * 3, np.float64); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    nt = len(m.loop_triangles)
    tv = np.empty(nt * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    ne = len(m.edges)
    ed = np.empty(ne * 2, np.int32); m.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    mw = np.array(o.matrix_world, dtype=np.float64)
    if not np.allclose(mw, np.eye(4)):
        bad_tf.append(o.name)
    cw = (np.c_[co, np.ones(n)] @ mw.T)[:, :3]
    per[o.name] = (cw, tv, ed)
    V.append(cw); T.append(tv + voff); OWN.append(np.full(nt, oi)); voff += n
    tri_total += nt
    ev.to_mesh_clear()
print("triangles (evaluated)", tri_total, "cap 1,000,000:", "PASS" if tri_total <= 1_000_000 else "FAIL")
print("materials", len(mats), sorted(mats), "outside palette:", sorted(mats - PAL), "empty slots:", empty_slot)
print("non-identity transforms", bad_tf)
print("Mask missing/bad", mask_bad)
for o in objs:
    c = per[o.name][0]
    print(f"  {o.name:36s} tris {len(per[o.name][1]):7d} bbox {np.round(c.min(0),3).tolist()} {np.round(c.max(0),3).tolist()}")
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
names = [o.name for o in objs]
print("min z of all verts", round(float(V[:, 2].min()), 3))


def nm(h):
    return names[OWN[h[2]]] if h[0] is not None else None


# ---- decal anchors -------------------------------------------------------------------------------------------
da = bpy.data.collections.get("DECAL_ANCHORS")
emp = [o for o in (da.objects if da else []) if o.type == "EMPTY"]
need = ("decal_type", "size_w", "size_h", "surface", "probability", "seed")
missing = [o.name for o in emp if not all(k in o.keys() for k in need)]
J = json.load(open(ajson))
print("DECAL_ANCHORS empties", len(emp), "missing props", missing[:5], "json count", J.get("count"), len(J["anchors"]))
print("anchor name sets equal", {o.name for o in emp} == {x["name"] for x in J["anchors"]})
far, buried, onobj = [], [], {}
for x in J["anchors"]:
    p = Vector(x["position"]); nrm = Vector(x["normal"])
    h = bvh.ray_cast(p + nrm * 0.05, -nrm, 0.25)
    if h[0] is None:
        far.append(x["name"])
    else:
        onobj[nm(h)] = onobj.get(nm(h), 0) + 1
    h2 = bvh.ray_cast(p + nrm * 0.005, nrm, 0.05)
    if h2[0] is not None:
        buried.append((x["name"], round(h2[3], 3), nm(h2)))
print("anchors with no surface within 20 cm behind:", len(far), far[:10])
print("anchors with a surface within 5 cm in front (buried):", len(buried), buried[:10])
print("anchor surfaces (object behind):", dict(sorted(onobj.items(), key=lambda kv: -kv[1])))
types = {}
for x in J["anchors"]:
    types.setdefault(x["type"], []).append(x)
for k, v in types.items():
    zz = [x["position"][2] for x in v]
    print(f"  {k:14s} n={len(v):3d} z {min(zz):6.2f}..{max(zz):6.2f} surfaces {sorted({x.get('surface') for x in v})}")
lean_anch = [x for x in J["anchors"] if -3.9 < x["position"][0] < 0.8 and x["position"][1] > 2.35]
print("anchors over the lean-to footprint:", len(lean_anch),
      sorted({(x["type"], x.get("surface")) for x in lean_anch}))
for x in lean_anch[:8]:
    print("   ", x["name"], [round(c, 3) for c in x["position"]], [round(c, 2) for c in x["normal"]])
print("anchor keys", sorted(J["anchors"][0].keys()))

# ---- wall thickness (for the see-through probe) ------------------------------------------------------------------
for lab, o, d in (("N wall", (-4.5, 0.0, 1.5), (0, 1, 0)), ("S wall", (-4.5, 0.0, 1.5), (0, -1, 0)),
                  ("gable", (-5.0, 0.0, 1.5), (-1, 0, 0)), ("S wall W", (-6.5, -0.3, 1.0), (0, -1, 0)),
                  ("round E", (4.606, -0.328, 1.5), (1, 0, 0)), ("round N", (4.606, -0.328, 1.5), (0, 1, 0)),
                  ("round SE", (4.606, -0.328, 1.0), (0.7071, -0.7071, 0))):
    o = Vector(o); d = Vector(d)
    h = bvh.ray_cast(o, d, 20)
    hb = bvh.ray_cast(o + d * 20, -d, 20)
    print(f"WALL {lab}: inner face at {None if h[0] is None else [round(c,3) for c in h[0]]} ({nm(h)}), "
          f"outer face at {None if hb[0] is None else [round(c,3) for c in hb[0]]} ({nm(hb)})")

# ---- door clearance ------------------------------------------------------------------------------------------------
YS, DX = -2.928, -2.394
print("HOST FRONT DOOR (x %.3f, S face y %.3f): lowest overhead per row out from the face (rays up from z 0.3)" % (DX, YS))
for out in (0.05, 0.15, 0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.2, 1.35, 1.5):
    best = (99, None); best_nw = (99, None)
    for ox in np.linspace(-0.6, 0.6, 25):
        h = bvh.ray_cast(Vector((DX + ox, YS - out, 0.3)), Vector((0, 0, 1)), 30)
        if h[0] is None:
            continue
        if h[0].z < best[0]:
            best = (h[0].z, nm(h))
        if "body_wall" not in nm(h) and h[0].z < best_nw[0]:
            best_nw = (h[0].z, nm(h))
    print(f"   out {out:4.2f}: lowest {best[0]:.3f} {best[1]}; lowest not host wall {best_nw[0]:.3f} {best_nw[1]}")
# the door opening itself (head in the reveal)
for dy in (0.05, 0.2, 0.35):
    h = bvh.ray_cast(Vector((DX, YS + dy, 0.5)), Vector((0, 0, 1)), 10)
    print(f"   door head ray in the reveal (+{dy} m in): {None if h[0] is None else (round(h[0].z,3), nm(h))}")
w = []
for dx in np.linspace(-0.8, 0.8, 161):
    h = bvh.ray_cast(Vector((DX + dx, YS - 1.0, 1.0)), Vector((0, 1, 0)), 2.0)
    w.append((dx, h[3] if h[0] is not None else 9))
deep = [dx for dx, t in w if t > 1.2]
print(f"   door opening width at z 1.0 (horizontal rays): {min(deep):.3f}..{max(deep):.3f} -> {max(deep)-min(deep):.3f} m"
      if deep else "   no deep rays")
# porch brackets / posts within the path in front of the door (z 0.3..2.3)
blk = 0
for ox in np.linspace(-0.5, 0.5, 21):
    for z in np.linspace(0.1, 2.25, 44):
        h = bvh.ray_cast(Vector((DX + ox, YS - 2.0, z)), Vector((0, 1, 0)), 1.95)
        if h[0] is not None:
            blk += 1
print("   anything in the 1.0 x 2.25 m approach path to the door (2 m out to the face):", blk)

LX0, LX1, LF, LN = -3.594, 0.406, 4.272, 2.272
print("LEAN-TO OPEN FRONT (x %.3f..%.3f, front y %.3f): lowest overhead per row (rays up from z 0.3)" % (LX0, LX1, LF))
for dy in (-0.6, -0.3, -0.15, 0.0, 0.1, 0.25, 0.4, 0.55, 0.7):
    best = (99, None); prof = []
    for x in np.linspace(LX0 + 0.45, LX1 - 0.45, 33):
        h = bvh.ray_cast(Vector((x, LF + dy, 0.3)), Vector((0, 0, 1)), 30)
        if h[0] is None:
            continue
        prof.append(round(h[0].z, 2))
        if h[0].z < best[0]:
            best = (h[0].z, nm(h))
    print(f"   y LF{dy:+.2f}: lowest {best[0]:.3f} {best[1]}   profile {prof[::4]}")
# open front width / post
row = []
for x in np.linspace(LX0, LX1, 401):
    h = bvh.ray_cast(Vector((x, LF + 1.5, 1.2)), Vector((0, -1, 0)), 3.0)
    row.append((x, h[3] if h[0] is not None else 9))
op = [x for x, t in row if t > 1.8]
if op:
    segs = []; s0 = op[0]; pv = op[0]
    for x in op[1:]:
        if x - pv > 0.015:
            segs.append((s0, pv)); s0 = x
        pv = x
    segs.append((s0, pv))
    print("   open bays at z 1.2:", [(round(s, 3), round(e, 3), round(e - s, 3)) for s, e in segs])

# ---- add-on geometry inside the host room (poking through the host wall) ------------------------------------------
ADD = [n for n in names if "_lean_to" in n or "_porch" in n]
SEAL = [n for n in names if n.endswith("_mortar") and ("wall_head" in n or "gable_corner" in n)]
print("add-on objects", ADD)
print("seal objects", SEAL)


def in_room(P, inset):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    body = (x > -8.394 + inset) & (x < 2.606) & (y > -2.928 + inset) & (y < 2.272 - inset) & (z > 0.0)
    r = np.hypot(x - 4.606, y + 0.328)
    drum = r < 3.53 - inset
    return (body | drum) & (z < 9.0)


for n in ADD + SEAL:
    co = per[n][0]
    for inset in (0.25, 0.45, 0.60):
        k = in_room(co, inset)
        if k.any():
            print(f"   ROOM {n}: {k.sum()} verts inside the room inset {inset}: bbox {np.round(co[k].min(0),3).tolist()} "
                  f"{np.round(co[k].max(0),3).tolist()}")
            break
    else:
        print(f"   ROOM {n}: none inside the room (inset 0.25)")
for n in SEAL:
    co = per[n][0]
    print(f"   SEAL {n}: bbox {np.round(co.min(0),3).tolist()} {np.round(co.max(0),3).tolist()}; "
          f"verts outside N face (y>2.272) {(co[:,1] > 2.272 + 1e-3).sum()}, outside S face (y<-2.928) "
          f"{(co[:,1] < -2.928 - 1e-3).sum()}, outside gable (x<-8.394) {(co[:,0] < -8.394 - 1e-3).sum()}")

# ---- poke-through from above on the add-on roofs -------------------------------------------------------------------
for lab, xr, yr in (("LEAN-TO", (LX0 - 0.7, LX1 + 0.7), (LN - 0.4, LF + 0.9)), ("PORCH", (DX - 1.6, DX + 1.6), (-4.4, -2.7))):
    tally = {}
    for x in np.arange(xr[0], xr[1], 0.02):
        for y in np.arange(yr[0], yr[1], 0.02):
            h = bvh.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 40)
            k = nm(h) or "GROUND"
            tally[k] = tally.get(k, 0) + 1
    print(f"{lab} first hit from above (2 cm grid):", dict(sorted(tally.items(), key=lambda kv: -kv[1])))
    bad = {k: v for k, v in tally.items() if any(s in k for s in ("framing", "deck", "rafter", "ledger", "plate"))}
    print(f"   framing / deck seen from above: {bad}")

# ---- islands / floating pieces ----------------------------------------------------------------------------------
def islands(nv, edges):
    lab = np.arange(nv)
    if len(edges) == 0:
        return lab
    a_, b_ = edges[:, 0], edges[:, 1]
    while True:
        m = np.minimum(lab[a_], lab[b_])
        new = lab.copy()
        np.minimum.at(new, a_, m); np.minimum.at(new, b_, m)
        new = new[new]; new = new[new]
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
    cand = np.arange(0, j1); cand = cand[cand != k]
    c = (his[cand, 0] >= los[k, 0]) & (los[cand, 1] <= his[k, 1]) & (his[cand, 1] >= los[k, 1]) & \
        (los[cand, 2] <= his[k, 2]) & (his[cand, 2] >= los[k, 2])
    if not c.any() and los[k, 2] > -0.03 + -E:
        iso.append(order[k])
print("islands whose 2 cm-inflated AABB touches no other island (and not on the ground):", len(iso))
for i in iso[:40]:
    print("   ISO", bown[i], np.round(B[i], 3).tolist())
# add-on and seal islands: nearest distance to geometry of OTHER objects (sampled verts)
for n in ADD + SEAL:
    co, tv, ed = per[n]
    lab = islands(len(co), ed)
    others = [o.name for o in objs if o.name != n]
    Vs, Ts, off = [], [], 0
    for m_ in others:
        c2, t2, _ = per[m_]
        Vs.append(c2); Ts.append(t2 + off); off += len(c2)
    oth = BVHTree.FromPolygons(np.concatenate(Vs).tolist(), np.concatenate(Ts).tolist(), all_triangles=True)
    own = BVHTree.FromPolygons(co.tolist(), tv.tolist(), all_triangles=True)
    tlab = lab[tv[:, 0]]
    labs = np.unique(lab[np.unique(tv.ravel())])
    worst = []
    for L in labs:
        pts = co[lab == L]
        pts = pts[::max(1, len(pts) // 400)]
        d = 9.0
        for p in pts:
            q = Vector(p)
            h = oth.find_nearest(q)
            if h[0] is not None:
                d = min(d, h[3])
            if d <= 0.02:
                break
            for hh in own.find_nearest_range(q, 0.02):
                if tlab[hh[2]] != L:
                    d = min(d, hh[3])
            if d <= 0.02:
                break
        worst.append((round(d, 3), np.round(pts.mean(0), 2).tolist(), len(pts)))
    worst.sort(key=lambda t: -t[0])
    far_ = [w_ for w_ in worst if w_[0] > 0.02]
    print(f"   FLOAT {n}: islands {len(labs)}, islands > 2 cm from any other island: {len(far_)}; worst {worst[:3]}")
print("DONE")
