"""Round-8 sign-off audit: read-only geometric measurements on v3_longhouse_roundend_r8.blend.
Writes audit/measure.json and prints a summary."""
import json, math, os
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = r"C:\GitHubDesktop\git_test\blender_village"
BL = ROOT + r"\buildings\variants\v3_longhouse_roundend\redesign_r8_wip\v3_longhouse_roundend_r8.blend"
DJ = ROOT + r"\buildings\variants\v3_longhouse_roundend\redesign_r8_wip\decal_anchors_r8.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure.json")
bpy.ops.wm.open_mainfile(filepath=BL)

C = np.array([4.6098, 0.0])            # round centre (finial / cone bbox centre, recentred)
TANB = math.tan(math.radians(1.5))
R = lambda z: 3.70 - np.asarray(z) * TANB
res = {}

def mesh_np(ob):
    me = ob.data
    me.calc_loop_triangles()
    M = np.array(ob.matrix_world)
    V = np.array([v.co for v in me.vertices], float)
    V = V @ M[:3, :3].T + M[:3, 3]
    T = np.array([t.vertices for t in me.loop_triangles], int).reshape(-1, 3)
    mi = np.array([t.material_index for t in me.loop_triangles], int)
    return V, T, mi

MESH = {ob.name: mesh_np(ob) for ob in bpy.data.objects if ob.type == "MESH"}
def bvh_of(names):
    Vs, Ts, off = [], [], 0
    owner = []
    for n in names:
        V, T, _ = MESH[n]
        Vs.append(V); Ts.append(T + off); off += len(V); owner += [n] * len(T)
    V = np.concatenate(Vs); T = np.concatenate(Ts)
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], all_triangles=True), owner

ALL = list(MESH)
BVH, OWNER = bvh_of(ALL)

def depth_in(V):
    r = np.hypot(V[:, 0] - C[0], V[:, 1] - C[1])
    return R(V[:, 2]) - r                     # >0: inside the round face

# ---- A. roof parts past the drum face ---------------------------------------------------------------------------
pen = {}
for n in ["LONG_body_roof_covering", "LONG_body_roof_eave_roll", "LONG_body_roof_ridge", "LONG_body_roof_comb",
          "LONG_body_roof_deck", "LONG_body_roof_rafters", "LONG_body_roof_wall_abutment", "LONG_body_wall_stones",
          "LONG_body_wall_mortar"]:
    V = MESH[n][0]
    d = depth_in(V)
    pen[n] = dict(max_depth_m=round(float(d.max()), 4), n_gt_3cm=int((d > 0.03).sum()), n_gt_5cm=int((d > 0.05).sum()),
                  n_gt_10cm=int((d > 0.10).sum()), n_gt_15cm=int((d > 0.15).sum()), n_verts=len(V))
    if d.max() > 0.03:
        i = int(d.argmax()); pen[n]["deepest_at"] = [round(float(x), 3) for x in V[i]]
res["penetration_into_drum"] = pen

# is any roof-part vertex deeper than 3 cm visible?  ray from cameras to those vertices (first hit must be near)
def cams():
    out = []
    for s in (-1, 1):
        for x in (-3.0, -1.0, 1.0, 3.0, 5.0):
            for d in (5.0, 8.0, 12.0):
                out.append((x, s * d, 1.6)); out.append((x, s * d, 6.0))
        out.append((-6.0, s * 4.0, 1.6))
    for x in (-14.0, -10.0):
        out.append((x, 0.0, 6.0)); out.append((x, 3.0, 6.0)); out.append((x, -3.0, 6.0))
    return [Vector(c) for c in out]
CAMS = cams()

def visible(P, eps=0.02):
    """number of cameras that see point P (first hit within eps of P)."""
    n = 0
    for c in CAMS:
        dv = Vector(P) - c
        L = dv.length
        h = BVH.ray_cast(c, dv.normalized(), L + 0.01)
        if h[0] is not None and (h[0] - Vector(P)).length < eps:
            n += 1
    return n

vis_pen = {}
for n in ["LONG_body_roof_covering", "LONG_body_roof_eave_roll", "LONG_body_roof_ridge", "LONG_body_roof_comb",
          "LONG_body_roof_deck", "LONG_body_roof_rafters", "LONG_body_roof_wall_abutment"]:
    V = MESH[n][0]
    d = depth_in(V)
    idx = np.where(d > 0.03)[0]
    if len(idx) > 400:
        idx = np.random.default_rng(1).choice(idx, 400, replace=False)
    seen = [(int(i), visible(V[i])) for i in idx]
    seen = [(i, k) for i, k in seen if k > 0]
    vis_pen[n] = dict(tested=len(idx), visible=len(seen),
                      examples=[dict(p=[round(float(x), 3) for x in V[i]], depth=round(float(d[i]), 3), n_cams=k)
                                for i, k in seen[:8]])
res["visible_deep_roof_verts"] = vis_pen

# ---- B. see-through leaks at the junction: cameras -> targets 2 cm behind the drum face ---------------------------
leaks = []
n_rays = 0
for azd in np.arange(110.0, 250.01, 1.0):              # body side of the drum (-x)
    a = math.radians(azd)
    for z in np.arange(2.0, 6.05, 0.025):
        rr = float(R(z)) - 0.02
        P = Vector((C[0] + rr * math.cos(a), C[1] + rr * math.sin(a), z))
        for c in CAMS:
            dv = P - c
            L = dv.length
            dn = dv.normalized()
            # only cameras on the outside of this face point
            nrm = Vector((math.cos(a), math.sin(a), 0.0))
            if nrm.dot(-dn) < 0.15:
                continue
            n_rays += 1
            h = BVH.ray_cast(c, dn, L + 1.0)
            if h[0] is None:
                leaks.append((azd, z, tuple(c), None, "sky", None)); continue
            dist = h[3]
            if dist < L - 0.06:
                continue                          # occluded in front, or hit on the face itself
            q = np.array(h[0])
            dq = float(depth_in(q[None])[0])
            if dq > 0.08 or dist > L + 0.05:
                leaks.append((azd, z, tuple(c), [round(float(x), 3) for x in q], OWNER[h[2]], round(dq, 3)))
res["leak_rays"] = n_rays
res["leak_count"] = len(leaks)
# cluster leaks by (az, z) cell
cells = {}
for azd, z, c, q, own, dq in leaks:
    key = (int(azd // 3) * 3, round(z // 0.1 * 0.1, 1))
    e = cells.setdefault(key, dict(n=0, cams=set(), owners=set(), ex=None))
    e["n"] += 1; e["cams"].add(c); e["owners"].add(own)
    if e["ex"] is None:
        e["ex"] = dict(az=azd, z=round(float(z), 3), cam=c, hit=q, hit_depth=dq,
                       target=[round(C[0] + (float(R(z)) - 0.02) * math.cos(math.radians(azd)), 3),
                               round(C[1] + (float(R(z)) - 0.02) * math.sin(math.radians(azd)), 3), round(float(z), 3)])
res["leak_cells"] = [dict(az_cell=k[0], z_cell=k[1], n=v["n"], n_cams=len(v["cams"]), owners=sorted(map(str, v["owners"])),
                          example=v["ex"]) for k, v in sorted(cells.items(), key=lambda kv: -kv[1]["n"])][:60]

# ---- C. floating islands near the drum ---------------------------------------------------------------------------
def islands(V, T):
    p = np.arange(len(V))
    def f(i):
        while p[i] != i:
            p[i] = p[p[i]]; i = p[i]
        return i
    for a, b, c in T:
        ra, rb, rc = f(a), f(b), f(c)
        p[rb] = ra; p[f(rc)] = ra
    roots = np.array([f(i) for i in range(len(V))])
    return roots

float_res = {}
OTHER_BVH = {}
for n in ["LONG_body_roof_wall_abutment", "LONG_body_roof_covering", "LONG_body_roof_eave_roll", "LONG_body_roof_ridge",
          "LONG_body_roof_comb", "LONG_body_roof_rafters", "LONG_body_roof_deck", "LONG_purlin_rings"]:
    V, T, _ = MESH[n]
    roots = islands(V, T)
    others = [m for m in ALL if m != n]
    ob_bvh, _o = bvh_of(others)
    kd = KDTree(len(V))
    for i, v in enumerate(V):
        kd.insert(v, i)
    kd.balance()
    near = depth_in(V) > -0.5
    out = []
    for r in np.unique(roots[near]):
        ids = np.where(roots == r)[0]
        dmin = 1e9
        for i in ids[:: max(1, len(ids) // 60)]:
            h = ob_bvh.find_nearest(Vector(V[i]))
            if h[0] is not None:
                dmin = min(dmin, h[3])
            for (co, j, dd) in kd.find_n(V[i], 8):
                if roots[j] != r:
                    dmin = min(dmin, dd)
        if dmin > 0.02:
            out.append(dict(n_verts=len(ids), gap_m=round(dmin, 3), centre=[round(float(x), 3) for x in V[ids].mean(0)]))
    float_res[n] = dict(islands_near_drum=int(len(np.unique(roots[near]))), floating=out[:20], n_floating=len(out))
res["floating"] = float_res

# ---- D. cone eave clearance over the thatch -----------------------------------------------------------------------
cone_names = ["LONG_roof_shingles", "LONG_roof_starter", "LONG_roof_underlap", "LONG_rafters", "LONG_battens",
              "LONG_roof_soffit_deck", "LONG_eave_fill", "LONG_roof_blocker", "LONG_purlin_rings"]
cone_bvh, cown = bvh_of(cone_names)
clr = []
for n in ["LONG_body_roof_covering", "LONG_body_roof_ridge", "LONG_body_roof_comb", "LONG_body_roof_eave_roll",
          "LONG_body_roof_wall_abutment"]:
    V = MESH[n][0]
    r = np.hypot(V[:, 0] - C[0], V[:, 1] - C[1])
    for i in np.where(r < 4.5)[0]:
        h = cone_bvh.ray_cast(Vector(V[i]), Vector((0, 0, 1)), 20.0)
        if h[0] is not None:
            clr.append((h[3], n, cown[h[2]], [round(float(x), 3) for x in V[i]]))
clr.sort(key=lambda t: t[0])
res["cone_clearance_min"] = [dict(gap_m=round(g, 3), roof_part=a, cone_part=b, at=p) for g, a, b, p in clr[:8]]
res["cone_min_z"] = {n: round(float(MESH[n][0][:, 2].min()), 3) for n in cone_names}
res["thatch_max_z_under_cone"] = round(max(float(MESH[n][0][np.hypot(MESH[n][0][:, 0] - C[0], MESH[n][0][:, 1] - C[1]) < 4.3][:, 2].max(initial=0))
                                          for n in ["LONG_body_roof_covering", "LONG_body_roof_ridge", "LONG_body_roof_comb",
                                                    "LONG_body_roof_wall_abutment"]), 3)
# any cone vertex inside the thatch envelope?  (cone parts below the thatch top near the junction)
# ---- E. door clearance --------------------------------------------------------------------------------------------
ent = json.loads(bpy.context.scene["kit_entrances"])[0]
o = np.array(ent["origin"]); out_v = np.array(ent["out"]); side = np.array([-out_v[1], out_v[0], 0.0])
door = []
for s in np.linspace(-0.5, 0.5, 11):
    for t in (0.05, 0.3, 0.6, 1.0, 1.5):
        P = o + side * s + out_v * t
        h = BVH.ray_cast(Vector((P[0], P[1], 0.02)), Vector((0, 0, 1)), 10.0)
        door.append((h[0][2] if h[0] is not None else 99.0, s, t, OWNER[h[2]] if h[0] is not None else None))
door.sort()
res["door_overhead_min"] = [dict(z=round(float(z), 3), side=round(float(s), 2), out=t, hit=w) for z, s, t, w in door[:5]]
blk = []
for s in np.linspace(-0.45, 0.45, 10):
    for z in np.arange(0.1, 2.11, 0.1):
        P0 = o + side * s + out_v * 2.0
        h = BVH.ray_cast(Vector((P0[0], P0[1], z)), Vector(tuple(-out_v)), 3.0)
        if h[0] is not None and h[3] < 2.0 - 0.10:
            blk.append(dict(side=round(float(s), 2), z=round(float(z), 2), dist=round(h[3], 3), hit=OWNER[h[2]]))
res["door_approach_blocked"] = blk[:10]
res["door_entrance"] = ent

# ---- F. Mask attribute and decal anchors ---------------------------------------------------------------------------
res["mask_missing"] = [ob.name for ob in bpy.data.objects if ob.type == "MESH" and "Mask" not in ob.data.attributes]
dj = json.load(open(DJ))
res["decal_json_top"] = list(dj)[:20] if isinstance(dj, dict) else f"list[{len(dj)}]"
anchors = dj.get("anchors", dj.get("decals", [])) if isinstance(dj, dict) else dj
far = []
kinds = {}
for a in anchors:
    p = a.get("position") or a.get("location") or a.get("pos") or a.get("p")
    kinds[a.get("type", a.get("kind", "?"))] = kinds.get(a.get("type", a.get("kind", "?")), 0) + 1
    if p is None:
        continue
    h = BVH.find_nearest(Vector(p))
    if h[0] is None or h[3] > 0.06:
        far.append(dict(name=a.get("name"), p=p, d=None if h[0] is None else round(h[3], 3)))
res["decal_n"] = len(anchors); res["decal_kinds"] = kinds; res["decal_far_from_surface"] = far[:10]
res["decal_n_far"] = len(far)
res["decal_example"] = anchors[0] if anchors else None
res["da_empties"] = sum(1 for ob in bpy.data.objects if ob.type == "EMPTY" and ob.name.startswith("DA_"))

# ---- G. eave-end aprons: lead islands of the abutment ---------------------------------------------------------------
V, T, mi = MESH["LONG_body_roof_wall_abutment"]
mats = [m.name for m in bpy.data.objects["LONG_body_roof_wall_abutment"].data.materials]
ap = []
for k, mname in enumerate(mats):
    sel = np.unique(T[mi == k].ravel())
    if mname == "M_lead":
        roots = islands(V, T)
        for r in np.unique(roots[sel]):
            ids = np.where(roots == r)[0]
            d = depth_in(V[ids])
            ap.append(dict(n_verts=len(ids), bbox_min=[round(float(x), 3) for x in V[ids].min(0)],
                           bbox_max=[round(float(x), 3) for x in V[ids].max(0)],
                           depth_into_face_max=round(float(d.max()), 3), outer_max=round(float(-d.min()), 3)))
res["aprons"] = ap
# flaunching (mortar) vs face: radial distance of its verts
sel = np.unique(T[mi == mats.index("M_mortar")].ravel())
d = depth_in(V[sel])
res["flaunching_depth_range"] = [round(float(d.min()), 3), round(float(d.max()), 3)]

json.dump(res, open(OUT, "w"), indent=1, default=str)
print("WROTE", OUT)
for k in ("penetration_into_drum", "visible_deep_roof_verts", "leak_rays", "leak_count", "cone_clearance_min", "cone_min_z",
          "thatch_max_z_under_cone", "door_overhead_min", "door_approach_blocked", "mask_missing", "decal_n", "decal_kinds",
          "decal_n_far", "decal_far_from_surface", "da_empties", "aprons", "flaunching_depth_range"):
    print(k, json.dumps(res.get(k), default=str)[:1500])
print("floating", json.dumps(res["floating"], default=str)[:2500])
print("leak_cells", json.dumps(res["leak_cells"][:25], default=str)[:5000])
