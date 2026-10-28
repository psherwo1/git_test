"""Auditor v6_barn round-3 read-only probe.  blender -b -P aud_probe_r03.py -- <blend> <anchors.json>
Compliance (tris, palette, Mask, transforms), decal anchors, door / cart-entry clearance measured on the mesh,
islands / floating pieces, leaf-vs-pad and leaf-vs-post interpenetration, the leaf-to-post slit."""
import json
import math
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
mats, tri_total, bad_tf, mask_bad, nonpal_slot = set(), 0, [], [], []
V, T, OWN, NRM = [], [], [], []
per = {}
voff = 0
for oi, o in enumerate(objs):
    for s in o.material_slots:
        if s.material:
            mats.add(s.material.name)
        else:
            nonpal_slot.append(o.name)
    me = o.data
    ca = me.color_attributes.get("Mask")
    ok = ca is not None and ca.domain == "CORNER" and me.color_attributes.active_color_name == "Mask"
    if not ok:
        mask_bad.append(o.name)
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
print("triangles (evaluated)", tri_total)
print("materials", len(mats), sorted(mats), "outside palette:", sorted(mats - PAL), "empty slots:", nonpal_slot)
print("non-identity transforms", bad_tf)
print("Mask missing/bad", mask_bad)
for o in objs:
    c = per[o.name][0]
    print(f"  {o.name:34s} tris {len(per[o.name][1]):6d} bbox {np.round(c.min(0),3).tolist()} {np.round(c.max(0),3).tolist()}")
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
print("ground min z of all verts", round(float(V[:, 2].min()), 3))


def sub_bvh(pred):
    Vs, Ts, own, off = [], [], [], 0
    for o in objs:
        if not pred(o.name):
            continue
        co, tv, _ = per[o.name]
        Vs.append(co); Ts.append(tv + off); own += [o.name] * len(tv); off += len(co)
    return BVHTree.FromPolygons(np.concatenate(Vs).tolist(), np.concatenate(Ts).tolist(), all_triangles=True), own


# ---- decal anchors -------------------------------------------------------------------------------------------
da = bpy.data.collections.get("DECAL_ANCHORS")
emp = [o for o in (da.objects if da else []) if o.type == "EMPTY"]
need = ("decal_type", "size_w", "size_h", "surface", "probability", "seed")
missing = [o.name for o in emp if not all(k in o.keys() for k in need)]
J = json.load(open(ajson))
print("DECAL_ANCHORS empties", len(emp), "missing props", missing[:5], "json count", J.get("count"), len(J["anchors"]))
print("anchor name sets equal", {o.name for o in emp} == {x["name"] for x in J["anchors"]})
far, buried, wrongmat = [], [], []
MATCLASS = {"stone": ("M_stone", "M_stone_dressed", "M_mortar"), "timber": ("M_timber", "M_timber_weathered"),
            "thatch": ("M_thatch",), "shingle": ("M_roof_shingle", "M_roof_shake"), "iron": ("M_iron",),
            "lead": ("M_lead",)}
for x in J["anchors"]:
    p = Vector(x["position"]); nrm = Vector(x["normal"])
    h = bvh.ray_cast(p + nrm * 0.05, -nrm, 0.25)
    if h[0] is None:
        far.append(x["name"])
    else:
        o = objs[OWN[h[2]]]
        sl = bpy.data.objects[o.name].material_slots
    h2 = bvh.ray_cast(p + nrm * 0.005, nrm, 0.05)
    if h2[0] is not None:
        buried.append((x["name"], round(h2[3], 3)))
print("anchors with no surface within 20 cm behind:", len(far), far[:10])
print("anchors with a surface within 5 cm in front (buried):", len(buried), buried[:10])
types = {}
for x in J["anchors"]:
    types.setdefault(x["type"], []).append(x)
for k, v in types.items():
    zz = [x["position"][2] for x in v]
    print(f"  {k:14s} n={len(v):3d} z {min(zz):6.2f}..{max(zz):6.2f} surfaces {sorted({x.get('surface') for x in v})}")
print("anchor keys", sorted(J["anchors"][0].keys()))

# ---- cart entry geometry ---------------------------------------------------------------------------------------
pads = per["BARN_cart_entry_pads"][0]
frame = per["BARN_cart_entry_frame"][0]
cx = float(0.5 * (pads[:, 0].min() + pads[:, 0].max()))
yf = float(frame[:, 1].min())
print(f"CART ENTRY centre x {cx:.3f}, frame front face y {yf:.3f}, pads bbox {np.round(pads.min(0),3).tolist()} "
      f"{np.round(pads.max(0),3).tolist()}")
DOORS = lambda nm: nm.startswith("BARN_cart_doors")
bv_nodoor, own_nd = sub_bvh(lambda nm: not DOORS(nm))
# clear width between the posts / under the arch, measured with horizontal rays at several depths through the frame
for yd in (0.02, 0.08, 0.14, 0.20, 0.26):
    y = yf + yd
    row = []
    for z in (0.05, 0.14, 0.5, 1.0, 1.5, 1.9, 2.2, 2.5, 2.8, 3.0, 3.2):
        L = bv_nodoor.ray_cast(Vector((cx, y, z)), Vector((-1, 0, 0)), 5.0)
        R = bv_nodoor.ray_cast(Vector((cx, y, z)), Vector((1, 0, 0)), 5.0)
        w = (L[3] if L[0] else 9) + (R[3] if R[0] else 9)
        row.append((z, round(w, 3)))
    print(f"  clear width at depth {yd:.2f} (y {y:.3f}):", row)
# arch crown / head at centre (ray up)
for yd in (0.05, 0.14, 0.24):
    h = bv_nodoor.ray_cast(Vector((cx, yf + yd, 0.5)), Vector((0, 0, 1)), 10)
    print(f"  head ray up at depth {yd}:", None if h[0] is None else (round(h[0].z, 3), own_nd[h[2]]))
# cart envelope 2.4 x 2.8 centred: any non-door geometry inside the box through the whole frame depth?
inside_pts = 0
for xx in np.linspace(cx - 1.2, cx + 1.2, 49):
    for zz in np.linspace(0.0, 2.8, 57):
        h = bv_nodoor.ray_cast(Vector((xx, yf - 1.0, zz)), Vector((0, 1, 0)), 1.3)
        if h[0] is not None and h[0].y < yf + 0.30:
            inside_pts += 1
print("  cart envelope 2.4 x 2.8 (rays along +y through the frame depth, non-door hits inside):", inside_pts)
# lowest overhead (eave / soffit) over the cart doorway outside the wall: rays up from the ground
rows = []
for out in (0.05, 0.3, 0.6, 1.0, 1.5):
    zmin, who = 99, None
    for ox in np.linspace(-1.8, 1.8, 37):
        h = bvh.ray_cast(Vector((cx + ox, yf - out, 0.2)), Vector((0, 0, 1)), 30)
        if h[0] is not None and h[0].z < zmin:
            zmin, who = h[0].z, objs[OWN[h[2]]].name
    rows.append((out, round(zmin, 3), who))
print("  overhead over the cart doorway (out from the frame face, lowest hit over +-1.8 m):", rows)
# man door (east gable)
md = [o for o in objs if o.name.startswith("BARN_walls")]
xe = float(V[:, 0].max())
for yy in np.linspace(-2.2, -0.4, 10):
    pass
# find the east man door: horizontal rays from outside at z 1.0 along -x; the deepest hit = the doorway
best = None
for yy in np.linspace(-3.4, 3.4, 69):
    h = bvh.ray_cast(Vector((xe + 1.0, yy, 1.0)), Vector((-1, 0, 0)), 3.0)
    d = h[3] if h[0] else 9
    if best is None or d > best[0]:
        best = (d, yy)
print("  east doorway search: deepest at y", round(best[1], 2), "depth", round(best[0], 3))
ys = [yy for yy in np.linspace(-3.4, 3.4, 137)
      if (lambda h: (h[3] if h[0] else 9))(bvh.ray_cast(Vector((xe + 1.0, yy, 1.0)), Vector((-1, 0, 0)), 3.0)) > 1.25]
if ys:
    y0, y1 = min(ys), max(ys); ym = 0.5 * (y0 + y1)
    xfa = xe + 1.0 - min((bvh.ray_cast(Vector((xe + 1.0, yy, 2.4)), Vector((-1, 0, 0)), 3.0)[3]) for yy in (y0, ym, y1))
    print(f"  east man door opening y {y0:.2f}..{y1:.2f} (width ~{y1-y0:.2f})")
    hh = bvh.ray_cast(Vector((xe - 0.9, ym, 0.6)), Vector((0, 0, 1)), 5)
    print("   head ray (inside the reveal):", None if hh[0] is None else (round(hh[0].z, 3), objs[OWN[hh[2]]].name))
    rows = []
    for out in (0.2, 0.5, 0.8, 1.1):
        zmin, who = 99, None
        for oy in np.linspace(y0, y1, 9):
            h = bvh.ray_cast(Vector((xe - 0.75 + out, oy, 0.3)), Vector((0, 0, 1)), 30)
            if h[0] is not None and h[0].z < zmin:
                zmin, who = h[0].z, objs[OWN[h[2]]].name
        rows.append((round(out, 2), round(zmin, 3), who))
    print("   overhead outside the east door (x from ~the wall face):", rows)

# ---- leaves vs pads / posts: interpenetration depth --------------------------------------------------------------
def inside(bv, p):
    n = 0; o = Vector(p); d = Vector((0.0123, 0.0071, 1.0)).normalized()
    for _ in range(60):
        h = bv.ray_cast(o, d, 50)
        if h[0] is None:
            return n % 2 == 1
        n += 1; o = h[0] + d * 1e-4
    return n % 2 == 1


pb = BVHTree.FromPolygons(pads.tolist(), per["BARN_cart_entry_pads"][1].tolist(), all_triangles=True)
for nm in ("BARN_cart_doors_leaves", "BARN_cart_doors_backing", "BARN_cart_doors_ledges", "BARN_cart_doors_ironwork"):
    co = per[nm][0]
    sel = co[co[:, 2] < 0.2]
    ins = [p for p in sel if inside(pb, p)]
    dep = max([pb.find_nearest(Vector(p))[3] for p in ins], default=0.0)
    print(f"LEAF/PAD {nm}: verts below 0.2 {len(sel)}, inside a pad {len(ins)}, max depth {dep:.3f}",
          np.round(np.array(ins).min(0), 3).tolist() if ins else "", np.round(np.array(ins).max(0), 3).tolist() if ins else "")
lv = per["BARN_cart_doors_leaves"][0]
print("LEAVES bbox", np.round(lv.min(0), 3).tolist(), np.round(lv.max(0), 3).tolist())
bk = per["BARN_cart_doors_backing"][0]
print("BACKING bbox", np.round(bk.min(0), 3).tolist(), np.round(bk.max(0), 3).tolist())
# post inner faces from the frame verts below the springing
fl = frame[(frame[:, 2] > 0.3) & (frame[:, 2] < 1.5)]
for sg in (-1, 1):
    side = fl[(fl[:, 0] - cx) * sg > 0]
    inner = side[np.argmin(np.abs(side[:, 0] - cx))]
    print(f"POST {sg:+d}: inner face x ~{inner[0]:.3f}; post y {side[:,1].min():.3f}..{side[:,1].max():.3f}; "
          f"leaves x-extent on this side {(lv[(lv[:,0]-cx)*sg>0][:,0]).min():.3f}..{(lv[(lv[:,0]-cx)*sg>0][:,0]).max():.3f}")

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
# hoist pieces: nearest distance of each hoist island to non-hoist geometry
for nm in ("BARN_hoist_frame", "BARN_hoist_ironwork"):
    co, tv, ed = per[nm]
    lab = islands(len(co), ed)
    oth, _ = sub_bvh(lambda n2: n2 != nm)
    for L in np.unique(lab[np.unique(tv.ravel())]):
        pts = co[lab == L]
        d = min(oth.find_nearest(Vector(p))[3] for p in pts[::max(1, len(pts) // 60)])
        if d > 0.01:
            print(f"   HOIST island {nm} centre {np.round(pts.mean(0),2).tolist()} nearest other surface {d:.3f} m")
print("DONE")
