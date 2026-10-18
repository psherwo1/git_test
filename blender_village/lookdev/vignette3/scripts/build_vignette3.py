"""Vignette 2: fjord village, many instances of the textured r2 lookdev buildings, 2D mountain backdrop cards.

python.exe -I build_vignette2.py <out.blend>
Reads (never writes) lookdev/village_r2/work/*_lookdev.blend and lookdev/r2_src/v7..v10_*_lookdev.blend.
Starts from v7_cottage_lookdev.blend (inherits colour management / LD_sun / world), appends each design once into an
excluded collection BLD_<id> and places linked collection-instance empties.  World: water Z 0, fjord runs +Y, village on
the west shore around a circular bay centred B=(10,0), cliff on the east (x>190), backdrop cards at y~670.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

OUT = os.path.abspath(sys.argv[-1])
ROOT = r"C:\GitHubDesktop\git_test\blender_village\lookdev"
WORK = ROOT + r"\village_r2\work"
R2 = ROOT + r"\r2_src"
TEX = ROOT + r"\textures"
REF = ROOT + r"\vignette2\ref"          # read only (concept-art backdrop crops)
ASSETS = ROOT + r"\vignette3\assets"      # kb3d_picks.blend, wooden_pier_picks.blend, textures_pier (licensed, never commit)
HELPER_KEYS = ("scale_fig", "figure", "helper", "human", "proxy", "dummy", "measure", "ref_", "gizmo")
DESIGNS = {
    "v7_cottage": R2, "v8_byre_smokehouse": R2, "v9_ale_house": R2, "v10_net_loft_cottage": R2,
    "v3_longhouse_roundend": WORK, "v6_barn": WORK, "wattle_roundhut": WORK,
    "v5_harbour_house": WORK, "hilltop_keep": WORK, "tower_windmill": WORK, "v1_stone_watchtower": WORK, "v2_tiered_hall": WORK, "v4_mixed": WORK,
}
BASE = "v7_cottage"
FOG_D, FOG_H = 0.0007, 60.0                        # haze density at ground level (1/m), height falloff (m)
AER_LOC, AER_TGT, AER_LENS = (42.0, -70.0, 36.0), (5.0, 170.0, 0.0), 30.0
rng = np.random.RandomState(7)
BX, BY, BR = 10.0, 0.0, 32.0      # bay centre / radius
EAST = 230.0                       # east shore x


def shore22(y):
    return 22.0 + 7.0 * np.sin(np.asarray(y, dtype=float) / 41.0 + 0.5) + 4.0 * np.sin(np.asarray(y, dtype=float) / 17.0 + 2.0)


def shoreE(y):
    return EAST + 10.0 * np.sin(y / 57.0)



def eligible(o):
    n = o.name.lower()
    if o.type != "MESH" or o.hide_render or o.name.startswith(("LD_", "VR2_", "HH_", "DA_")):
        return False
    if any(c.name.upper().startswith("DECAL_ANCHOR") or c.hide_render for c in o.users_collection):
        return False
    return not any(k in n for k in HELPER_KEYS)


# ------------------------------------------------------------------ base + append designs
bpy.ops.wm.open_mainfile(filepath=os.path.join(DESIGNS[BASE], BASE + "_lookdev.blend"))
scn = bpy.context.scene
base_objs = [o for o in scn.objects if eligible(o)]
for o in list(scn.objects):
    if o in base_objs or o.name == "LD_sun":
        continue
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name.upper().startswith("DECAL_ANCHOR"):
        bpy.data.collections.remove(c)
designs_root = bpy.data.collections.new("VG_DESIGNS")
scn.collection.children.link(designs_root)
dobjs = {}


def to_design_col(bid, objs):
    col = bpy.data.collections.new("BLD_" + bid)
    designs_root.children.link(col)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    dobjs[bid] = objs
    return col


to_design_col(BASE, base_objs)
for bid, folder in DESIGNS.items():
    if bid == BASE:
        continue
    with bpy.data.libraries.load(os.path.join(folder, bid + "_lookdev.blend"), link=False) as (src, dst):
        dst.objects = list(src.objects)
    got = [o for o in dst.objects if o is not None]
    keep, drop = [], []
    for o in got:
        n = o.name.lower()
        ok = (o.type == "MESH" and not o.hide_render and not o.name.startswith(("LD_", "VR2_", "HH_", "DA_"))
              and not any(k in n for k in HELPER_KEYS))
        (keep if ok else drop).append(o)
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    to_design_col(bid, keep)
    print("APPENDED", bid, len(keep), flush=True)

by_path = {}
for im in list(bpy.data.images):
    if im.source != "FILE":
        continue
    key = (os.path.normcase(os.path.abspath(bpy.path.abspath(im.filepath, library=im.library))), im.colorspace_settings.name)
    if key in by_path and by_path[key] is not im:
        im.user_remap(by_path[key])
        bpy.data.images.remove(im)
    else:
        by_path[key] = im
print("IMAGES unique", len(by_path), "missing",
      [im.name for im in bpy.data.images if im.source == "FILE" and not os.path.exists(bpy.path.abspath(im.filepath))], flush=True)
try:
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
except Exception as ex:  # noqa
    print("purge failed", ex)

bounds = {}
for bid, objs in dobjs.items():
    pts = np.array([tuple(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box])
    bounds[bid] = (pts.min(0), pts.max(0))
    print("BOUNDS", bid, np.round(pts.min(0), 1), np.round(pts.max(0), 1), flush=True)
RAD = {b: 0.5 * float(np.hypot(*(bounds[b][1][:2] - bounds[b][0][:2]))) * 0.85 for b in bounds}
CEN = {b: 0.5 * (bounds[b][0][:2] + bounds[b][1][:2]) for b in bounds}   # footprint centre offset (local)


# ------------------------------------------------------------------ layout
def pol(R, phi_deg):
    p = math.radians(phi_deg)
    return (BX + R * math.cos(p), BY + R * math.sin(p))


LOW = ["v7_cottage", "v10_net_loft_cottage", "v9_ale_house", "v3_longhouse_roundend", "wattle_roundhut",
       "v8_byre_smokehouse", "v7_cottage", "v6_barn", "v10_net_loft_cottage", "wattle_roundhut", "v3_longhouse_roundend",
       "v8_byre_smokehouse", "v7_cottage", "v9_ale_house"]
PL = []        # (design, x, y, rot_deg, scale)
lowi = [0]


def next_low():
    d = LOW[lowi[0] % len(LOW)]
    lowi[0] += 1
    return d


def face(design, x, y, tx, ty, jitter=10.0):
    dx, dy = tx - x, ty - y
    if design == "v6_barn":
        r = math.degrees(math.atan2(dy, dx))
    else:
        r = math.degrees(math.atan2(dx, -dy))
    return r + rng.uniform(-jitter, jitter)


def add(design, x, y, tx=None, ty=None, rot=None, sc=None):
    if rot is None:
        rot = face(design, x, y, tx, ty)
    PL.append((design, x, y, rot, sc if sc else float(rng.uniform(0.93, 1.1))))


for phi in (100, 120, 140, 160, 200, 220):             # row 1 round the bay (180 = plaza)
    x, y = pol(43, phi)
    add(next_low(), x, y, BX, BY)
    if phi == 100:
        PL.pop()          # v5 boathouse takes this spot (rng stream kept identical)
x, y = pol(49, 180)
add("v9_ale_house", x, y, BX, BY, sc=1.0)
for phi in (110, 130, 150, 170, 190, 210, 230, 250):  # row 2
    x, y = pol(61, phi)
    d = {130: "v2_tiered_hall", 190: "v4_mixed"}.get(phi) or next_low()
    add(d, x, y, BX, BY)
for phi in (105, 125, 160, 200, 225, 255):             # row 3
    x, y = pol(80, phi)
    add(next_low(), x, y, BX, BY)
for y in (62, 80, 98, -62, -80):       # ribbon along the fjord shore
    add(next_low(), float(shore22(y)) - 12.0, y, 60, y)
add("v10_net_loft_cottage", -31, -37, rot=-100)          # near-left foreground (street shot)
add("v7_cottage", float(shore22(-43)) - 11.0, -43, rot=-100, sc=1.05)           # right foreground (street shot)
add("tower_windmill", -82, 96, rot=-30, sc=1.0)
add("tower_windmill", -104, -58, rot=160, sc=1.0)
add("hilltop_keep", -92, 20, rot=-90, sc=1.0)
add("v1_stone_watchtower", 13, -108, rot=-90, sc=1.0)
# ---- v5 harbour house (boathouse): hero of the harbour, at the head of the bay, water gable + boat arch facing the bay (-Y)
HH_Z = 0.9
YQ, YS = 3.427 - 0.30, 0.227 - 0.30          # quay face / slip-flank lines (v5 local)
V5 = (10.0, 35.1, 172.0)
PL.append(("v5_harbour_house", V5[0], V5[1], V5[2], 1.0))
print("PLACEMENTS", len(PL), flush=True)


# ------------------------------------------------------------------ terrain height field
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def noise2(x, y, seed):
    rs = np.random.RandomState(seed)
    v = np.zeros_like(x)
    for f, a in ((1 / 47.0, 1.0), (1 / 23.0, 0.5), (1 / 11.0, 0.22)):
        p1, p2 = rs.uniform(0, 6.28, 2)
        th = rs.uniform(0, 3.14)
        u = x * math.cos(th) + y * math.sin(th)
        w = -x * math.sin(th) + y * math.cos(th)
        v += a * np.sin(u * f * 6.28 + p1) * np.sin(w * f * 6.28 * 0.8 + p2)
    return v


QUAY = 0.9


def shore22(y):
    return 22.0 + 7.0 * np.sin(y / 41.0 + 0.5) + 4.0 * np.sin(y / 17.0 + 2.0)


def shoreE(y):
    return EAST + 10.0 * np.sin(y / 57.0)



def natural_h(x, y):
    d_bay = np.hypot(x - BX, y - BY) - BR
    d_fj = np.where(x > 63.0, x - shoreE(y), shore22(y) - x)
    k = 3.0
    d = -k * np.log(np.exp(-d_bay / k) + np.exp(-d_fj / k))      # + inland
    west = QUAY + 0.035 * np.clip(d - 6.0, 0, None) + 0.35 * noise2(x, y, 3) * smooth(6.0, 20.0, d)
    hills = 0.0018 * np.clip(-x - 110.0, 0, None) ** 2
    west += 110.0 * np.tanh(hills / 110.0) * (1 + 0.15 * noise2(x * 2, y * 2, 5)) * (1.0 - 0.97 * smooth(420, 650, y))
    west += 9.0 * np.exp(-(((x + 92) / 18.0) ** 2 + ((y - 20) / 16.0) ** 2))
    west += 4.5 * np.exp(-(((x + 82) / 12.0) ** 2 + ((y - 96) / 11.0) ** 2))
    west += 4.5 * np.exp(-(((x + 104) / 12.0) ** 2 + ((y + 58) / 11.0) ** 2))
    xe = x - shoreE(y)
    fadeN = 1.0 - 0.97 * smooth(420, 650, y)
    east = QUAY + 3.0 * smooth(0, 25, xe) + fadeN * (60.0 * smooth(10, 90, xe) + 280.0 * smooth(60, 150, xe) ** 1.5) * (1 + 0.12 * noise2(x * 1.5, y * 1.5, 9))
    east += 8.0 * noise2(x * 3, y * 3, 12) * smooth(40, 90, xe) * fadeN
    # v3: rugged cliff - vertical gullies/buttresses, strata ledges, bigger mid-frequency relief
    gul = np.sin(y * 0.16 + 5.0 * noise2(x * 0.6, y * 0.6, 21)) * np.sin(y * 0.071 + 2.0)
    east += fadeN * smooth(25, 120, xe) * (22.0 * gul + 14.0 * noise2(x * 2.0, y * 2.0, 31))
    ledge = np.sin(east / 11.0 * 3.14159 + 2.0 * noise2(x, y, 41))
    east += fadeN * smooth(60, 200, xe) * 4.5 * np.sign(ledge) * np.abs(ledge) ** 0.35
    land = np.where(x > 63.0, east, west)
    sea = -1.8 - 0.8 * smooth(0.0, -40.0, d)
    sea = np.maximum(sea, -3.0)
    bank = 5.0
    t = smooth(-bank, 0.0, d)
    return sea + (land - sea) * t


def axis(parts):
    a = np.concatenate([np.arange(*p) for p in parts])
    return np.unique(np.round(a, 3))


xs = axis([(-640, -130, 8.0), (-130, 60.0001, 1.0), (60, 226, 8.0), (226, 400, 4.0), (400, 641, 12.0)])
ys = axis([(-230, -110, 8.0), (-110, 130.0001, 1.0), (130, 661, 8.0)])
X, Y = np.meshgrid(xs, ys)
H = natural_h(X, Y)

# paths ---------------------------------------------------------------- polylines (world xy)
PATHS = []
PATHS.append([pol(35.5, p) for p in range(95, 266, 6)])                  # harbour front promenade
for phi in (110, 130, 150, 170, 190, 210, 230, 250):                      # radials to row 2 doors
    PATHS.append([pol(36, phi), pol(56, phi)])
PATHS.append([pol(72, p) for p in range(100, 262, 8)])
PATHS.append([pol(35.5, 100), (14, 60), (14, 95), (14, 130)])
PATHS.append([pol(35.5, 260), (6, -60), (12, -95), (14, -105)])
PATHS.append([pol(72, 100), (-40, 110), (-80, 95)])
PATHS.append([pol(72, 258), (-60, -60), (-100, -58)])
PATHS.append([pol(72, 190), (-92, 20), (-92, 14)])
PATHS.append([(-6, -31), (-6, -42), (-8, -52)]); PATHS.append([(-6, -31), (-31, -37)])                       # street-shot foreground
PATHS.append([(-6, -45), (6, -47), (12, -48)])


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy))


D = np.full(X.shape, 1e9)
core = (np.abs(X - (-30)) < 130) & (Y > -115) & (Y < 135)
for pl in PATHS:
    for a, b in zip(pl[:-1], pl[1:]):
        D = np.minimum(D, seg_dist(X, Y, a, b))
PATHW = 1.0 - smooth(1.0, 1.8, D + 0.35 * noise2(X * 3, Y * 3, 11))
land_mask = smooth(0.5, 1.2, H)
PATHW *= land_mask
H -= 0.03 * PATHW

# building pads
PADZ = []
HOLE = None
for (bid, x, y, r, s) in PL:
    if bid == "v5_harbour_house":
        mn, mx = bounds[bid]
        c_, s_ = math.cos(math.radians(r)), math.sin(math.radians(r))
        lx = (X - x) * c_ + (Y - y) * s_
        ly = -(X - x) * s_ + (Y - y) * c_
        ex = np.maximum(np.maximum(mn[0] - 1.5 - lx, lx - mx[0] - 1.5), np.maximum(mn[1] - 4.0 - ly, ly - YQ))
        w = 1.0 - smooth(0.0, 5.0, ex)
        H = H + (HH_Z - 0.045 - 0.015 - H) * w
        PADZ.append(HH_Z + 0.04)
        HOLE = (mn[0] - 1.0, mx[0] + 1.0, mn[1] - 3.0, mx[1] + 1.5)
        continue
    rr = RAD[bid] * s + 0.5
    dd = np.hypot(X - x, Y - y)
    inside = dd < rr
    if not inside.any():
        PADZ.append(float(natural_h(np.array([x]), np.array([y]))[0]))
        continue
    h0 = float(H[inside].mean())
    w = 1.0 - smooth(0.0, 4.0 + rr * 0.3, dd - rr)
    H = H + (h0 - H) * w
    PADZ.append(h0)

# fields
FIELDS = []
for (R, phi, w, h, rot) in ((104, 125, 26, 16, 0), (106, 150, 24, 15, 20), (104, 175, 28, 14, 5), (108, 205, 24, 16, -10),
                            (106, 232, 26, 15, 10), (118, 138, 20, 14, 30), (120, 190, 22, 14, 0), (118, 222, 20, 15, -20)):
    cx, cy = pol(R, phi)
    FIELDS.append((cx, cy, w, h, math.radians(phi + 90 + rot), float(rng.uniform(0.25, 1.0))))
FLD = np.zeros(X.shape)
for (cx, cy, w, h, rot, fid) in FIELDS:
    c, s = math.cos(rot), math.sin(rot)
    lx = (X - cx) * c + (Y - cy) * s
    ly = -(X - cx) * s + (Y - cy) * c
    ins = (np.abs(lx) < w / 2) & (np.abs(ly) < h / 2)
    FLD = np.where(ins, fid, FLD)

ny, nx = X.shape
verts = np.stack([X.ravel(), Y.ravel(), H.ravel()], 1)
ii, jj = np.meshgrid(np.arange(ny - 1), np.arange(nx - 1), indexing="ij")
a = (ii * nx + jj).ravel()
quads = np.stack([a, a + 1, a + 1 + nx, a + nx], 1)
_, v5x, v5y, v5r, _ = next(p for p in PL if p[0] == "v5_harbour_house")
_c, _s = math.cos(math.radians(v5r)), math.sin(math.radians(v5r))
_cx = ((xs[jj] + xs[jj + 1]) * 0.5 - v5x).ravel()
_cy = ((ys[ii] + ys[ii + 1]) * 0.5 - v5y).ravel()
_lx = _cx * _c + _cy * _s
_ly = -_cx * _s + _cy * _c
_keep = ~((_lx > HOLE[0]) & (_lx < HOLE[1]) & (_ly > HOLE[2]) & (_ly < HOLE[3]))
quads = quads[_keep]
tm = bpy.data.meshes.new("VG_terrain")
tm.vertices.add(len(verts))
tm.vertices.foreach_set("co", verts.astype(np.float32).ravel())
tm.loops.add(quads.size)
tm.loops.foreach_set("vertex_index", quads.astype(np.int32).ravel())
tm.polygons.add(len(quads))
tm.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
tm.update(calc_edges=True)
tm.validate()
for nm, arr in (("path", PATHW), ("fld", FLD)):
    at = tm.attributes.new(nm, "FLOAT", "POINT")
    at.data.foreach_set("value", arr.ravel().astype(np.float32))
tm.polygons.foreach_set("use_smooth", np.ones(len(quads), dtype=bool))
terrain = bpy.data.objects.new("VG_terrain", tm)
scn.collection.objects.link(terrain)
print("TERRAIN verts", len(verts), "quads", len(quads), flush=True)


# ------------------------------------------------------------------ materials
def nodes_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree


def simple(name, col, rough=0.85, noise=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1)
    b.inputs["Roughness"].default_value = rough
    if noise > 0:
        nt = m.node_tree
        g = nt.nodes.new("ShaderNodeNewGeometry")
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 0.35
        n.inputs["Detail"].default_value = 6.0
        nt.links.new(g.outputs["Position"], n.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs["A"].default_value = (col[0], col[1], col[2], 1)
        mx.inputs["B"].default_value = (col[0] * (1 - 0.5 * noise), col[1] * (1 - 0.5 * noise), col[2] * (1 - 0.5 * noise), 1)
        nt.links.new(n.outputs["Fac"], mx.inputs["Factor"])
        nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    return m


def ground_material():
    m, nt = nodes_mat("VG_ground")
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 3.0, 1 / 3.0, 1 / 3.0)
    L(geo.outputs["Position"], mp.inputs["Vector"])
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(os.path.join(TEX, "nordic_moss_se4rwei_2k", "Nordic_Moss_se4rwei_2K_BaseColor.jpg"), check_existing=True)
    L(mp.outputs["Vector"], im.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.9
    hsv.inputs["Value"].default_value = 0.75
    L(im.outputs["Color"], hsv.inputs["Color"])
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.035
    n1.inputs["Detail"].default_value = 5.0
    L(geo.outputs["Position"], n1.inputs["Vector"])
    patch = nt.nodes.new("ShaderNodeMapRange")
    patch.inputs["From Min"].default_value = 0.28
    patch.inputs["From Max"].default_value = 0.40
    L(n1.outputs["Fac"], patch.inputs["Value"])
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 0.4
    n2.inputs["Detail"].default_value = 8.0
    L(geo.outputs["Position"], n2.inputs["Vector"])
    ecr = nt.nodes.new("ShaderNodeValToRGB")
    ecr.color_ramp.elements[0].color = (0.075, 0.060, 0.044, 1)
    ecr.color_ramp.elements[1].color = (0.135, 0.110, 0.080, 1)
    L(n2.outputs["Fac"], ecr.inputs["Fac"])
    grass_t = nt.nodes.new("ShaderNodeMix")
    grass_t.data_type = "RGBA"
    grass_t.blend_type = "MULTIPLY"
    grass_t.inputs["Factor"].default_value = 1.0
    grass_t.inputs["B"].default_value = (0.50, 0.70, 0.30, 1)
    L(hsv.outputs["Color"], grass_t.inputs["A"])
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    L(patch.outputs["Result"], mix1.inputs["Factor"])
    L(ecr.outputs["Color"], mix1.inputs["A"])
    L(grass_t.outputs["Result"], mix1.inputs["B"])
    # fields: colour by plot id (ramp), furrows via a wave texture
    fa = nt.nodes.new("ShaderNodeAttribute")
    fa.attribute_name = "fld"
    fm = nt.nodes.new("ShaderNodeMapRange")
    fm.inputs["From Min"].default_value = 0.08
    fm.inputs["From Max"].default_value = 0.2
    L(fa.outputs["Fac"], fm.inputs["Value"])
    fcr = nt.nodes.new("ShaderNodeValToRGB")
    fcr.color_ramp.elements[0].position = 0.25
    fcr.color_ramp.elements[0].color = (0.10, 0.17, 0.05, 1)
    fcr.color_ramp.elements[1].position = 1.0
    fcr.color_ramp.elements[1].color = (0.30, 0.22, 0.08, 1)
    e = fcr.color_ramp.elements.new(0.6)
    e.color = (0.07, 0.11, 0.04, 1)
    L(fa.outputs["Fac"], fcr.inputs["Fac"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 1.2
    wv.inputs["Distortion"].default_value = 2.0
    L(geo.outputs["Position"], wv.inputs["Vector"])
    fmul = nt.nodes.new("ShaderNodeMix")
    fmul.data_type = "RGBA"
    fmul.blend_type = "MULTIPLY"
    fmul.inputs["Factor"].default_value = 0.5
    L(fcr.outputs["Color"], fmul.inputs["A"])
    L(wv.outputs["Color"], fmul.inputs["B"])
    mixf = nt.nodes.new("ShaderNodeMix")
    mixf.data_type = "RGBA"
    L(fm.outputs["Result"], mixf.inputs["Factor"])
    L(mix1.outputs["Result"], mixf.inputs["A"])
    L(fmul.outputs["Result"], mixf.inputs["B"])
    # shore band
    shore = nt.nodes.new("ShaderNodeMapRange")
    shore.inputs["From Min"].default_value = QUAY - 0.7
    shore.inputs["From Max"].default_value = QUAY - 0.1
    shore.inputs["To Min"].default_value = 1.0
    shore.inputs["To Max"].default_value = 0.0
    L(sep.outputs["Z"], shore.inputs["Value"])
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    L(shore.outputs["Result"], mix2.inputs["Factor"])
    L(mixf.outputs["Result"], mix2.inputs["A"])
    mix2.inputs["B"].default_value = (0.075, 0.07, 0.062, 1)
    pa = nt.nodes.new("ShaderNodeAttribute")
    pa.attribute_name = "path"
    pcr = nt.nodes.new("ShaderNodeValToRGB")
    pcr.color_ramp.elements[0].color = (0.13, 0.105, 0.078, 1)
    pcr.color_ramp.elements[1].color = (0.19, 0.155, 0.115, 1)
    L(n2.outputs["Fac"], pcr.inputs["Fac"])
    mix3 = nt.nodes.new("ShaderNodeMix")
    mix3.data_type = "RGBA"
    L(pa.outputs["Fac"], mix3.inputs["Factor"])
    L(mix2.outputs["Result"], mix3.inputs["A"])
    L(pcr.outputs["Color"], mix3.inputs["B"])
    # rock on steep slopes
    nrm = nt.nodes.new("ShaderNodeNewGeometry")
    sz = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(nrm.outputs["Normal"], sz.inputs["Vector"])
    rm = nt.nodes.new("ShaderNodeMapRange")
    rm.inputs["From Min"].default_value = 0.86
    rm.inputs["From Max"].default_value = 0.68
    L(sz.outputs["Z"], rm.inputs["Value"])
    rmp = nt.nodes.new("ShaderNodeMapping")
    rmp.inputs["Scale"].default_value = (0.09, 0.09, 0.03)
    L(geo.outputs["Position"], rmp.inputs["Vector"])
    n3 = nt.nodes.new("ShaderNodeTexNoise")
    n3.inputs["Scale"].default_value = 1.0
    n3.inputs["Detail"].default_value = 10.0
    n3.inputs["Roughness"].default_value = 0.65
    L(rmp.outputs["Vector"], n3.inputs["Vector"])
    rcr = nt.nodes.new("ShaderNodeValToRGB")
    rcr.color_ramp.elements[0].position = 0.35
    rcr.color_ramp.elements[0].color = (0.30, 0.28, 0.27, 1)
    rcr.color_ramp.elements[1].position = 0.65
    rcr.color_ramp.elements[1].color = (0.75, 0.70, 0.64, 1)
    L(n3.outputs["Fac"], rcr.inputs["Fac"])
    mix4 = nt.nodes.new("ShaderNodeMix")
    mix4.data_type = "RGBA"
    L(rm.outputs["Result"], mix4.inputs["Factor"])
    L(mix3.outputs["Result"], mix4.inputs["A"])
    # v3: lichened rock texture, two scales (tile breaker), box projection from world position, darkened + ramp variation
    tcs = nt.nodes.new("ShaderNodeTexCoord")
    prev = None
    for sc_i, scl in enumerate((0.16, 0.021)):
        mpp = nt.nodes.new("ShaderNodeMapping")
        mpp.inputs["Scale"].default_value = (scl, scl, scl * 0.8)
        L(tcs.outputs["Object"], mpp.inputs["Vector"])
        tim = nt.nodes.new("ShaderNodeTexImage")
        tim.image = bpy.data.images.load(os.path.join(TEX, "lichened_rock_wall_visoeh2bw_2k", "Lichened_Rock_Wall_visoeh2bw_2K_BaseColor.jpg"), check_existing=True)
        tim.projection = "BOX"
        tim.projection_blend = 0.3
        L(mpp.outputs["Vector"], tim.inputs["Vector"])
        if prev is None:
            prev = tim.outputs["Color"]
        else:
            mm = nt.nodes.new("ShaderNodeMix")
            mm.data_type = "RGBA"
            mm.blend_type = "OVERLAY"
            mm.inputs["Factor"].default_value = 0.6
            L(prev, mm.inputs["A"])
            L(tim.outputs["Color"], mm.inputs["B"])
            prev = mm.outputs["Result"]
    rmul = nt.nodes.new("ShaderNodeMix")
    rmul.data_type = "RGBA"
    rmul.blend_type = "MULTIPLY"
    rmul.inputs["Factor"].default_value = 1.0
    L(prev, rmul.inputs["A"])
    L(rcr.outputs["Color"], rmul.inputs["B"])
    rbr = nt.nodes.new("ShaderNodeBrightContrast")
    rbr.inputs["Bright"].default_value = -0.05
    rbr.inputs["Contrast"].default_value = 0.3
    L(rmul.outputs["Result"], rbr.inputs["Color"])
    L(rbr.outputs["Color"], mix4.inputs["B"])
    L(mix4.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.92
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.5
    bmp.inputs["Distance"].default_value = 0.3
    L(n3.outputs["Fac"], bmp.inputs["Height"])
    L(bmp.outputs["Normal"], bs.inputs["Normal"])
    return m


terrain.data.materials.append(ground_material())


def water_material():
    wm = bpy.data.materials.new("VG_water")
    wm.use_nodes = True
    wb = wm.node_tree.nodes.get("Principled BSDF")
    wb.inputs["Base Color"].default_value = (0.012, 0.075, 0.085, 1.0)
    wb.inputs["Roughness"].default_value = 0.11
    wb.inputs["IOR"].default_value = 1.33
    wb.inputs["Transmission Weight"].default_value = 0.35
    nt = wm.node_tree
    wn = nt.nodes.new("ShaderNodeTexNoise")
    wn.inputs["Scale"].default_value = 0.35
    wn.inputs["Detail"].default_value = 4.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.5
    nt.links.new(wn.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], wb.inputs["Normal"])
    return wm


S = 1800.0
wme = bpy.data.meshes.new("VG_water")
wme.from_pydata([(-S, -S, 0.0), (S, -S, 0.0), (S, S, 0.0), (-S, S, 0.0)], [], [(0, 1, 2, 3)])
wme.materials.append(water_material())
scn.collection.objects.link(bpy.data.objects.new("VG_water", wme))

# ------------------------------------------------------------------ building instances
for bid, x, y, r, s in []:
    pass
inst_count = {}
for i, (bid, x, y, r, s) in enumerate(PL):
    e = bpy.data.objects.new("INST_%s_%02d" % (bid, i), None)
    e.instance_type = "COLLECTION"
    e.instance_collection = bpy.data.collections["BLD_" + bid]
    e.empty_display_size = 1.0
    scn.collection.objects.link(e)
    # collection origin = design origin; footprint centre may be offset, we place the design origin on the pad
    e.matrix_world = Matrix.Translation((x, y, PADZ[i] - 0.04)) @ Matrix.Rotation(math.radians(r), 4, "Z") @ Matrix.Scale(s, 4)
    inst_count[bid] = inst_count.get(bid, 0) + 1
print("INSTANCES", inst_count, flush=True)
# ---- v5 stage: flagstone land boxes + bed (the scene's single VG_water plane is used; v5 brings no water)
def hh_land_material():
    lm = bpy.data.materials.new("HH_land")
    lm.use_nodes = True
    nt = lm.node_tree
    nt.nodes.clear()
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1.4
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.8
    noise.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.10, 0.092, 0.078, 1.0)
    cr.color_ramp.elements[1].color = (0.20, 0.182, 0.152, 1.0)
    nt.links.new(noise.outputs["Fac"], cr.inputs["Fac"])
    joint = nt.nodes.new("ShaderNodeMapRange")
    joint.inputs["From Min"].default_value = 0.0
    joint.inputs["From Max"].default_value = 0.035
    joint.inputs["To Min"].default_value = 0.45
    joint.inputs["To Max"].default_value = 1.0
    nt.links.new(vor.outputs["Distance"], joint.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(cr.outputs["Color"], mul.inputs["A"])
    nt.links.new(joint.outputs["Result"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.9
    return lm


V5M = Matrix.Translation((V5[0], V5[1], HH_Z)) @ Matrix.Rotation(math.radians(V5[2]), 4, "Z")
_lm = hh_land_material()


def stage_box(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    vs = [V5M @ Vector((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata([tuple(v) for v in vs], [], fs)
    me.materials.append(mat)
    scn.collection.objects.link(bpy.data.objects.new(name, me))


hx0, hx1, hy0, hy1 = HOLE[0] - 1.0, HOLE[1] + 1.0, HOLE[2] - 1.0, HOLE[3]
stage_box("HH_land", hx0, hx1, hy0, YS, -3.0, -0.045, _lm)
stage_box("HH_land", hx0, -0.608 - 0.30, YS, YQ, -3.0, -0.045, _lm)
stage_box("HH_land", 4.392 + 0.30, hx1, YS, YQ, -3.0, -0.045, _lm)
_bedm = bpy.data.materials.new("VG_bed")
_bedm.use_nodes = True
_bedm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.048, 0.04, 1)
_bedm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
_bme = bpy.data.meshes.new("VG_bed")
_bme.from_pydata([tuple(V5M @ Vector(p)) for p in ((HOLE[0] - 1, HOLE[2] - 1, -2.55), (HOLE[1] + 1, HOLE[2] - 1, -2.55),
                                                    (HOLE[1] + 1, HOLE[3] + 1, -2.55), (HOLE[0] - 1, HOLE[3] + 1, -2.55))], [], [(0, 1, 2, 3)])
_bme.materials.append(_bedm)
scn.collection.objects.link(bpy.data.objects.new("VG_bed", _bme))
designs_lc = bpy.context.view_layer.layer_collection.children["VG_DESIGNS"]
designs_lc.exclude = True

# ------------------------------------------------------------------ procedural set dressing (vignette3: textured materials)
def timg(path, cs="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = cs
    return im


WOOD_IMG = timg(TEX + r"\rough_wood_2k.blend\textures\rough_wood_diff_2k.jpg")
ROCK_IMG = timg(TEX + r"\lichened_rock_wall_visoeh2bw_2k\Lichened_Rock_Wall_visoeh2bw_2K_BaseColor.jpg")
METAL_IMG = timg(TEX + r"\rusty_metal_sheet_tj4kedvcw_2k\Rusty_Metal_Sheet_tj4kedvcw_2K_BaseColor.jpg")
MOSS_IMG = timg(TEX + r"\nordic_moss_se4rwei_2k\Nordic_Moss_se4rwei_2K_BaseColor.jpg")


def tex_mat(name, img, tint=(1, 1, 1), rough=0.85, scale=0.4, bump=0.35, vcol=None, noise_tint=0.0):
    """object-space box-projected texture * tint; optional vertex colour attribute multiplies in"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links.new
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = img
    ti.projection = "BOX"
    ti.projection_blend = 0.25
    L(mp.outputs["Vector"], ti.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (tint[0], tint[1], tint[2], 1)
    L(ti.outputs["Color"], mx.inputs["A"])
    last = mx.outputs["Result"]
    if vcol:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = vcol
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type = "RGBA"
        m2.blend_type = "MULTIPLY"
        m2.inputs["Factor"].default_value = 1.0
        L(last, m2.inputs["A"])
        L(at.outputs["Color"], m2.inputs["B"])
        last = m2.outputs["Result"]
    L(last, b.inputs["Base Color"])
    bm_ = nt.nodes.new("ShaderNodeBump")
    bm_.inputs["Strength"].default_value = bump
    bm_.inputs["Distance"].default_value = 0.05
    L(ti.outputs["Color"], bm_.inputs["Height"])
    L(bm_.outputs["Normal"], b.inputs["Normal"])
    return m


def flat(name, col, rough=0.8):
    return simple(name, col, rough)


MATS = {
    "wood": tex_mat("D_wood", WOOD_IMG, (0.55, 0.47, 0.40), 0.9, 0.55),
    "plank": tex_mat("D_plank", WOOD_IMG, (0.85, 0.72, 0.58), 0.85, 0.5),
    "stone": tex_mat("D_stone", ROCK_IMG, (1.1, 1.1, 1.05), 0.95, 0.30),
    "hay": simple("D_hay", (0.55, 0.42, 0.16), 0.95, 0.4),
    "tree": tex_mat("D_tree", MOSS_IMG, (0.5, 0.75, 0.42), 0.9, 0.9, 0.25, vcol="tcol"),
    "trunk": tex_mat("D_trunk", WOOD_IMG, (0.30, 0.22, 0.17), 0.95, 0.7),
    "hull": tex_mat("D_hull", WOOD_IMG, (0.75, 0.22, 0.12), 0.7, 0.6),
    "hull2": tex_mat("D_hull2", WOOD_IMG, (0.30, 0.24, 0.20), 0.7, 0.6),
    "hull3": tex_mat("D_hull3", WOOD_IMG, (0.55, 0.68, 0.72), 0.7, 0.6),
    "iron": tex_mat("D_iron", METAL_IMG, (0.35, 0.33, 0.32), 0.6, 0.5),
    "fig1": simple("D_fig1", (0.30, 0.13, 0.08), 0.9),
    "fig2": simple("D_fig2", (0.18, 0.16, 0.10), 0.9),
    "fig3": simple("D_fig3", (0.10, 0.14, 0.12), 0.9),
    "fig4": simple("D_fig4", (0.20, 0.22, 0.28), 0.9),
    "fig5": simple("D_fig5", (0.33, 0.27, 0.15), 0.9),
    "legs": simple("D_legs", (0.07, 0.06, 0.05), 0.9),
    "skin": simple("D_skin", (0.45, 0.30, 0.22), 0.7),
    "rock": tex_mat("D_rock", ROCK_IMG, (0.75, 0.72, 0.68), 0.95, 0.18, 0.7),
}
BM = {k: bmesh.new() for k in MATS}
BM["tree"].loops.layers.color.new("tcol")
SMOOTH = {"rock", "tree", "trunk", "wood", "hull", "hull2", "hull3", "fig1", "fig2", "fig3", "fig4", "fig5", "legs", "skin", "iron", "stone", "hay"}



def M(loc=(0, 0, 0), rz=0.0, sc=(1, 1, 1), rx=0.0):
    return (Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X")
            @ Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)))


def box(k, c, size, rz=0.0):
    bmesh.ops.create_cube(BM[k], size=1.0, matrix=M(c, rz, size))


def cyl(k, c, r, h, rz=0.0, rx=0.0, seg=8, r2=None):
    bmesh.ops.create_cone(BM[k], cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2,
                          depth=h, matrix=M(c, rz, (1, 1, 1), rx))


def ell(k, c, radii, rz=0.0, seg=10):
    bmesh.ops.create_uvsphere(BM[k], u_segments=seg, v_segments=max(6, seg // 2), radius=1.0, matrix=M(c, rz, radii))


def rock(c, r):
    res = bmesh.ops.create_icosphere(BM["rock"], subdivisions=1, radius=1.0,
                                     matrix=M(c, float(rng.uniform(0, 6.28)), (r * rng.uniform(0.8, 1.4), r * rng.uniform(0.8, 1.3), r * rng.uniform(0.5, 0.9))))
    for v in res["verts"]:
        v.co += Vector(rng.uniform(-0.18, 0.18, 3)) * r


def hull(k, c, rad, rz):
    """open boat shell: lower part of an ellipsoid"""
    res = bmesh.ops.create_uvsphere(BM[k], u_segments=14, v_segments=8, radius=1.0, matrix=M((0, 0, 0), 0, rad))
    kill = [v for v in res["verts"] if v.co.z > 0.18 * rad[2]]
    bmesh.ops.delete(BM[k], geom=kill, context="VERTS")
    left = [v for v in res["verts"] if v.is_valid]
    bmesh.ops.transform(BM[k], matrix=M(c, rz), verts=left)


def gz(x, y):
    return float(natural_h(np.array([x]), np.array([y]))[0])


def aside(c, phi_deg, d):
    p = math.radians(phi_deg + 90)
    return (c[0] + d * math.cos(p), c[1] + d * math.sin(p))


# ---- kit / pier assets
PIERPATH = ASSETS + r"\wooden_pier_picks.blend"
KITPATH = ASSETS + r"\kb3d_picks.blend"
with bpy.data.libraries.load(PIERPATH) as (src, dst):
    dst.objects = list(src.objects)
PIER = {o.name.replace("modular_wooden_pier_", ""): o for o in dst.objects if o}
for im in bpy.data.images:
    if im.source == "FILE" and "modular_wooden_pier" in im.name:
        im.filepath = os.path.join(ASSETS, "textures_pier", os.path.basename(im.filepath))
        im.reload()
with bpy.data.libraries.load(KITPATH) as (src, dst):
    dst.objects = list(src.objects)
KIT = {o.name[5:]: o for o in dst.objects if o}
print("PIER parts", sorted(PIER), "KIT picks", sorted(KIT), flush=True)
for me_ in (o.data for o in KIT.values()):
    pass
KMAP = {"BoatBodyPanelsDarkWornB": "hull2", "BoatBodyPanelsWhiteWornB": "hull3", "BoatBodyPanelsWornA": "hull"}
KMAT = {
    "hull": tex_mat("K_hull", WOOD_IMG, (0.62, 0.20, 0.11), 0.65, 1.8),
    "hull2": tex_mat("K_hull2", WOOD_IMG, (0.22, 0.17, 0.14), 0.65, 1.8),
    "hull3": tex_mat("K_hull3", WOOD_IMG, (0.70, 0.66, 0.55), 0.65, 1.8),
    "metal": tex_mat("K_iron", METAL_IMG, (0.30, 0.28, 0.27), 0.6, 1.5),
    "rope": simple("K_rope", (0.30, 0.22, 0.12), 0.95, 0.6),
    "net": simple("K_net", (0.10, 0.085, 0.06), 0.95),
    "wood": tex_mat("K_wood", WOOD_IMG, (0.55, 0.46, 0.38), 0.85, 1.5),
    "buoy": simple("K_buoy", (0.55, 0.12, 0.06), 0.7),
}
for k, o in KIT.items():
    me = o.data
    for i, sl in enumerate(list(me.materials)):
        n = sl.name.replace("KB3D_SOL_", "") if sl else ""
        if n in KMAP:
            nm = KMAP[n]
        elif "Rope" in n:
            nm = "rope"
        elif "Net" in n:
            nm = "net"
        elif "Metal" in n or "Steel" in n:
            nm = "metal"
        elif "Airship" in n:
            nm = "buoy"
        elif "Wood" in n:
            nm = "wood"
        else:
            nm = "hull2"
        me.materials[i] = KMAT[nm]
    for p in me.polygons:
        p.use_smooth = True


def kit_obj(key, loc, rz, sc, name=None):
    o = bpy.data.objects.new(name or "K_" + key, KIT[key].data)
    scn.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Diagonal((sc, sc, sc, 1.0))
    return o


def vminmax(me, ax):
    a = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    return float(a[:, ax].min()), float(a[:, ax].max())


PS = 0.85          # pier scale: deck ~2.1 m wide
PDX = 0.97         # local x centre of the pier modules
PDZ = 2.68         # local z of the pier deck top
DECK = 1.0         # world deck height


def pier(base, rz, L, tall_at=None, name="PIER"):
    """modular wooden pier: section_01 (shore end), alternating 02/03, section_04 (tip); modules are chained by their y extents"""
    seq = ["section_01"]
    nmid = max(2, int(L / (PS * 2.95)) - 1)
    seq += ["section_02" if i % 2 == 0 else "section_03" for i in range(nmid)] + ["section_04"]
    cur = 0.0
    starts = []
    for i, s in enumerate(seq):
        y0, y1 = vminmax(PIER[s].data, 1)
        o = bpy.data.objects.new("%s_%02d" % (name, i), PIER[s].data)
        scn.collection.objects.link(o)
        o.matrix_world = (Matrix.Translation(base) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(PS, 4)
                          @ Matrix.Translation((-PDX, cur - y0, -PDZ)))
        starts.append(cur)
        cur += (y1 - y0) - 0.45
    if tall_at is not None and tall_at < len(seq):
        y0, _ = vminmax(PIER["section_05"].data, 1)
        o = bpy.data.objects.new(name + "_gate", PIER["section_05"].data)
        scn.collection.objects.link(o)
        o.matrix_world = (Matrix.Translation(base) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(PS, 4)
                          @ Matrix.Translation((-PDX, starts[tall_at] - y0, -PDZ)))
    return cur * PS, starts


def pier_pt(base, rz, dist, side=0.0):
    d = Vector((-math.sin(rz), math.cos(rz), 0))
    s = Vector((math.cos(rz), math.sin(rz), 0))
    return Vector(base) + d * dist + s * side


def quad_from_dir(dx, dy):
    return math.atan2(-dx, dy)


# quay promenade deck (planks) + rounded bollards
for phi in range(100, 262, 5):
    x, y = pol(32.2, phi)
    box("plank", (x, y, 0.8), (3.0, 3.6, 0.3), math.radians(phi + 90))
    if phi % 10 == 0:
        px, py = pol(31.0, phi)
        cyl("wood", (px, py, -0.2), 0.17, 2.4, seg=10)
for phi in range(105, 258, 9):
    px, py = pol(31.5, phi)
    if phi < 110 or phi > 225:      # none by the boathouse jetty or in the street-camera foreground
        continue
    cyl("wood", (px, py, 1.22), 0.16, 0.55, seg=12)
    ell("wood", (px, py, 1.5), (0.2, 0.2, 0.15), seg=12)
    cyl("iron", (px, py, 1.12), 0.2, 0.05, seg=12)
# piers from the modular wooden pier
PIERS = [(205, 22.0, None), (155, 16.5, None), (235, 13.5, None), (125, 11.5, None)]
PIER_INFO = []
for k, (phi, L, tall) in enumerate(PIERS):
    d = (-math.cos(math.radians(phi)), -math.sin(math.radians(phi)))
    rz = quad_from_dir(*d)
    bx, by = pol(32.4, phi)
    ln, st = pier((bx, by, DECK), rz, L, tall_at=None if tall is None else 2 + tall, name="PIER%d" % k)
    PIER_INFO.append(((bx, by), rz, ln))
# fjord jetty on the south ribbon (runs east)
JB = (float(shore22(-48)) - 3.0, -48.0)
ln, st = pier((JB[0], JB[1], DECK), quad_from_dir(1.0, 0.0), 18.0, name="JETTY")
PIER_INFO.append((JB, quad_from_dir(1.0, 0.0), ln))
# rope ladders and buoys at pier tips
for (bx_by, rz, ln) in PIER_INFO:
    p = pier_pt((bx_by[0], bx_by[1], 0), rz, ln - 0.6, 1.15)
    kit_obj("ladder", (p.x, p.y, DECK - 1.25), rz, 0.42, "LADDER")
    for dd in (0.35, 0.7):
        p = pier_pt((bx_by[0], bx_by[1], 0), rz, ln * dd, 1.3)
        kit_obj("buoyA" if dd < 0.5 else "buoyB", (p.x, p.y, DECK + 0.3), rng.uniform(0, 6), 1.0, "BUOY")# kit boats (moored in the bay)
for (c, rz, sc, tint) in (((6.0, -11.0), 100, 0.32, "a"), ((-1.0, 13.0), 80, 0.28, "b"), ((20.0, -26.0), 70, 0.26, "c")):
    kit_obj("boat", (c[0], c[1], -0.8 + 3.76 * sc), math.radians(rz), sc, "KBOAT")
# netting racks + anchor on the quay
for phi in (128, 188, 256):
    x, y = pol(34.6, phi)
    z0 = 0.95
    tang = math.radians(phi + 90)
    for sd in (-1.5, 1.5):
        cyl("wood", (x + sd * math.cos(tang), y + sd * math.sin(tang), z0 + 1.0), 0.07, 2.0, seg=8)
    cyl("wood", (x, y, z0 + 1.95), 0.05, 3.2, rz=tang, rx=math.pi / 2 * 0, seg=8)
    BM["wood"]  # noqa
    n = kit_obj("netA" if phi != 188 else "netB", (x, y, z0 + 1.95 - 0.8), tang, 1.5, "NET")
ax, ay = pol(33.4, 150)
kit_obj("anchor", (ax, ay, 1.05), 0.7, 0.55, "ANCHOR")


def rowboat(c, rz, L, key):
    """lofted open rowing boat with thickness, thwarts and two oars"""
    bm = bmesh.new()
    N, J = 12, 4
    rows_ = []
    for i in range(N + 1):
        u = i / N * 2 - 1
        w = 0.5 * L * 0.30 * max(1e-3, (1 - abs(u) ** 2.2)) ** 0.6
        hg = 0.34 * (1 + 0.5 * u ** 2 * (1.3 if u > 0 else 1.0))
        dp = 0.34 * (1 - 0.8 * abs(u) ** 3)
        r = []
        for j in range(-J, J + 1):
            s = j / J
            r.append(bm.verts.new((u * L / 2, s * w, (hg - dp) + dp * abs(s) ** 1.5 + 0.0 * s)))
        rows_.append(r)
    for i in range(N):
        for j in range(2 * J):
            try:
                bm.faces.new((rows_[i][j], rows_[i + 1][j], rows_[i + 1][j + 1], rows_[i][j + 1]))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.04)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Rotation(math.radians(rz), 4, "Z"), verts=bm.verts[:])
    tmp = bpy.data.meshes.new("tmp")
    bm.to_mesh(tmp)
    bm.free()
    BM[key].from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    ang = math.radians(rz)
    ca, sa = math.cos(ang), math.sin(ang)
    for off in (-0.45, 0.2):
        wx = L * 0.15
        box("plank", (c[0] + off * ca, c[1] + off * sa, c[2] + 0.34 * 0.9), (0.22, wx * 2.2, 0.04), ang)
    for sd in (-1, 1):
        cyl("wood", (c[0] - 0.12 * ca - sd * 0.62 * sa, c[1] - 0.12 * sa + sd * 0.62 * ca, c[2] + 0.55), 0.02, 2.0, rz=ang, rx=0.5 * sd, seg=6)


# row boats (several kinds)
rows = [((-3.5, -22.0), 75), ((-10.0, -17.5), 55), ((29.0, -44.0), 95), ((34.0, -53.0), 80), ((-6.5, -2.0), 70), ((-13.5, -19.0), 60), ((-9.0, 24.0), 110),
        ((8.0, 30.0), 100), ((20.0, 14.0), 85), ((-26.0, 1.5), 12), ((-22.5, -12.0), 40)]
for i, (c, rz) in enumerate(rows):
    rowboat((c[0], c[1], 0.12), rz, float(rng.uniform(3.6, 4.6)), ("hull", "hull2", "hull3")[i % 3])
for c, rz in (((70.0, 70.0), 80), ((95.0, 160.0), 100), ((60.0, 230.0), 75)):
    rowboat((c[0], c[1], 0.12), rz, 4.0, "hull2")
# hay, woodpiles, well, crates
for (R, phi) in ((92, 130), (95, 160), (95, 212), (90, 240), (98, 180), (96, 118)):
    x, y = pol(R, phi)
    z = gz(x, y)
    cyl("hay", (x, y, z + 1.0), 1.4, 2.0, r2=1.2, seg=14)
    cyl("hay", (x, y, z + 2.5), 1.2, 1.4, r2=0.05, seg=14)
for (x, y, rz) in ((-30.0, -27.0, 0.3), (-41.0, 19.0, 1.0), (-14.0, -34.5, 0.3), (-16.0, -55.0, 0.5), (-45.0, -2.0, 2.0), (-12.0, 49.0, 0.2), (3.0, 66.0, 1.2)):
    z = gz(x, y)
    for row, n in enumerate((6, 5, 4)):
        for k in range(n):
            lx = (k - (n - 1) / 2) * 0.28
            cyl("wood", (x + lx * math.cos(rz), y + lx * math.sin(rz), z + 0.17 + row * 0.26), 0.13, 1.5, rz=rz + math.pi / 2, rx=math.pi / 2, seg=8)
wx, wy = pol(35.0, 168)
wz = gz(wx, wy)
cyl("stone", (wx, wy, wz + 0.45), 1.0, 0.9, seg=16)
for sx in (-0.9, 0.9):
    box("plank", (wx + sx, wy, wz + 1.5), (0.14, 0.14, 2.0))
box("plank", (wx, wy, wz + 2.5), (2.2, 0.16, 0.14))
cyl("plank", (wx, wy, wz + 2.9), 1.5, 0.7, seg=4, r2=0.05, rz=math.pi / 4)
# barrels / crates on the quay
for k in range(14):
    phi = rng.uniform(112, 248)
    x, y = pol(rng.uniform(32.5, 34.3), phi)
    _rot = rng.uniform(0, 3)
    if phi > 225:
        continue
    if k % 2:
        cyl("wood", (x, y, 0.95 + 0.4), 0.32, 0.8, seg=12)
        for zz in (0.2, 0.62):
            cyl("iron", (x, y, 0.95 + zz), 0.335, 0.05, seg=12)
    else:
        box("plank", (x, y, 0.95 + 0.3), (0.7, 0.7, 0.6), _rot)


def figure(x, y, z, kk, hat=True):
    cyl("legs", (x, y, z + 0.42), 0.13, 0.84, seg=8, r2=0.11)
    cyl(kk, (x, y, z + 1.12), 0.21, 0.55, seg=10, r2=0.17)
    ell(kk, (x, y, z + 1.42), (0.17, 0.17, 0.12), seg=10)
    ell(kk, (x, y, z + 0.84), (0.21, 0.21, 0.1), seg=10)
    ell("skin", (x, y, z + 1.62), (0.105, 0.105, 0.125), seg=10)
    if hat:
        ell("legs", (x, y, z + 1.68), (0.115, 0.115, 0.07), seg=8)
    ang = float(rng.uniform(0, 6.28))
    for sd in (-1, 1):
        cyl(kk, (x + sd * 0.25 * math.cos(ang), y + sd * 0.25 * math.sin(ang), z + 1.2), 0.05, 0.6, seg=6)


FIGS = ["fig1", "fig2", "fig3", "fig4", "fig5"]
for i, (x, y) in enumerate(((-12.5, -26.5), (-16.0, -33.0), (-21.5, -9.0), (-27.5, -4.0), (-20.0, -20.0), (-26.0, 14.0))):
    figure(x, y, gz(x, y), FIGS[i % 5])
for (phi, R) in ((150, 33.0), (183, 34.0), (214, 33.4)):
    px, py = pol(R, phi)
    figure(px, py, 0.95, FIGS[(phi // 7) % 5])
# fences
FENCES = [[pol(98, p) for p in range(120, 252, 6)], [pol(112, p) for p in range(125, 240, 6)], [(11.5, 47), (11.5, 57)],
          [(-22, -58), (-16, -56), (-12, -57)], [(-20, 30), (-30, 37), (-38, 38)]]
for fl in FENCES:
    for a, b in zip(fl[:-1], fl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 2.2))
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for k in range(n + 1):
            t = k / n
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            cyl("wood", (px, py, gz(px, py) + 0.55), 0.06, 1.1, seg=6)
        for zz in (0.45, 0.85):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            box("plank", (mx, my, gz(mx, my) + zz), (L, 0.05, 0.08), ang)


# rocks: displaced subdivided icospheres with the lichened rock texture (smooth shaded)
def rock2(c, r, sub=2, flat_=0.6):
    ph = rng.uniform(0, 6.28, 6)
    res = bmesh.ops.create_icosphere(BM["rock"], subdivisions=sub, radius=1.0)
    sx, sy = rng.uniform(0.8, 1.5), rng.uniform(0.8, 1.4)
    rz = float(rng.uniform(0, 6.28))
    for v in res["verts"]:
        p = v.co.copy()
        d = (1 + 0.28 * math.sin(2.3 * p.x + ph[0]) * math.sin(2.1 * p.y + ph[1]) + 0.16 * math.sin(4.7 * p.z + ph[2] + 3 * p.x)
             + 0.07 * math.sin(9.0 * p.x + ph[3]) * math.sin(8.0 * p.y + ph[4]) + rng.uniform(-0.03, 0.03))
        q = p * d
        q.z = max(q.z, -0.45) * flat_
        v.co = Matrix.Rotation(rz, 3, "Z") @ Vector((q.x * sx * r, q.y * sy * r, q.z * r)) + Vector(c)


for k in range(70):
    phi = rng.uniform(95, 265)
    x, y = pol(rng.uniform(30.0, 33.5), phi)
    rock2((x, y, gz(x, y) + 0.05), rng.uniform(0.25, 0.7), 2, 0.7)
for k in range(110):
    y = rng.uniform(-100, 420)
    x = float(shoreE(y)) + rng.uniform(-4, 16)
    zg = gz(x, y)
    rock2((x, y, zg + 0.2), rng.uniform(1.0, 5.0) * (1.0 + 1.0 * (rng.rand() < 0.15)), 3, 0.8)
for k in range(30):     # boulders up the cliff face
    y = rng.uniform(-60, 380)
    x = float(shoreE(y)) + rng.uniform(15, 110)
    rock2((x, y, gz(x, y) + 0.5), rng.uniform(3.0, 9.0), 3, 0.95)
for k in range(25):
    y = rng.choice([-1, 1]) * rng.uniform(40, 110)
    x = float(shore22(y)) - rng.uniform(0, 4)
    rock2((x, y, gz(x, y) + 0.1), rng.uniform(0.5, 1.6), 2, 0.65)
# trees (merged mesh, per-tree tint via the 'tcol' attribute, 3 species)
pts = []
avoid = np.array([(p[1], p[2]) for p in PL])
fcent = np.array([(f[0], f[1]) for f in FIELDS])


def ok_tree(x, y):
    if np.min(np.hypot(avoid[:, 0] - x, avoid[:, 1] - y)) < 11:
        return False
    if np.min(np.hypot(fcent[:, 0] - x, fcent[:, 1] - y)) < 17:
        return False
    if math.hypot(x - BX, y - BY) < 68:
        return False
    return True


tries = 0
while len(pts) < 1700 and tries < 50000:
    tries += 1
    r = rng.rand()
    if r < 0.62:
        x, y = rng.uniform(-340, -100), rng.uniform(-200, 600)
        if x > -135 and rng.rand() < 0.5 and y < 130:
            continue
    elif r < 0.82:
        x, y = rng.uniform(-110, 8), rng.uniform(135, 560)
    elif r < 0.9:
        x, y = rng.uniform(-120, -60), rng.uniform(-190, -110)
    else:
        x, y = rng.uniform(EAST + 1, EAST + 60), rng.uniform(-150, 560)
    if not ok_tree(x, y):
        continue
    z = gz(x, y)
    if z < 1.2 or z > 80:
        continue
    pts.append((x, y, z))
colL = BM["tree"].loops.layers.color["tcol"]


def paint(verts, col):
    for v in verts:
        for lp in v.link_loops:
            lp[colL] = (col[0], col[1], col[2], 1.0)


for (x, y, z) in pts:
    sp = rng.rand()
    sc_ = float(np.exp(rng.normal(0, 0.28)))
    sc_ = min(max(sc_, 0.55), 1.7)
    hgt = rng.uniform(6.0, 13.0) * (1.0 + 0.4 * smooth(-100, -250, x)) * sc_
    lean = Vector((rng.normal(0, 0.04), rng.normal(0, 0.04), 0))
    if sp < 0.60:        # spruce, 3-5 tiers
        w = hgt * rng.uniform(0.18, 0.32)
        g = rng.uniform(0.75, 1.3)
        col = (0.55 * g, 0.9 * g, 0.55 * g)
        cyl("trunk", (x, y, z + hgt * 0.1), 0.16 * hgt / 8, hgt * 0.2, seg=6)
        nt_ = int(rng.randint(3, 6))
        for t in range(nt_):
            zb = z + hgt * (0.1 + 0.8 / nt_ * t)
            rr = w * (1.0 - 0.75 * t / nt_)
            vc = len(BM["tree"].verts)
            bmesh.ops.create_cone(BM["tree"], cap_ends=False, cap_tris=False, segments=int(rng.randint(7, 11)), radius1=rr, radius2=0.04 * rr, depth=hgt * 0.8 / nt_ * 1.5,
                                  matrix=M((x + lean.x * t, y + lean.y * t, zb + hgt * 0.5 / nt_), float(rng.uniform(0, 6.28))))
            paint(list(BM["tree"].verts)[vc:], col)
    elif sp < 0.72:      # tall narrow fir
        w = hgt * 0.11
        g = rng.uniform(0.6, 0.95)
        cyl("trunk", (x, y, z + hgt * 0.07), 0.12 * hgt / 8, hgt * 0.14, seg=5)
        vc = len(BM["tree"].verts)
        bmesh.ops.create_cone(BM["tree"], cap_ends=False, cap_tris=False, segments=7, radius1=w, radius2=0.03, depth=hgt * 0.95, matrix=M((x, y, z + hgt * 0.55)))
        paint(list(BM["tree"].verts)[vc:], (0.45 * g, 0.75 * g, 0.5 * g))
    else:                # broadleaf: trunk + clustered blobs
        hh = hgt * 0.75
        cyl("trunk", (x, y, z + hh * 0.3), 0.2 * hh / 6, hh * 0.6, seg=6, r2=0.12 * hh / 8)
        k_ = rng.rand()
        col = (1.0, 1.15, 0.5) if k_ < 0.4 else ((1.5, 0.95, 0.3) if k_ < 0.55 else (0.8, 1.2, 0.6))
        col = tuple(c * rng.uniform(0.8, 1.2) for c in col)
        for bl in range(int(rng.randint(3, 6))):
            rr = hh * rng.uniform(0.2, 0.32)
            off = Vector((rng.normal(0, 0.18 * hh), rng.normal(0, 0.18 * hh), rng.uniform(0.62, 0.95) * hh))
            vc = len(BM["tree"].verts)
            res = bmesh.ops.create_icosphere(BM["tree"], subdivisions=2, radius=1.0, matrix=M((x + off.x, y + off.y, z + off.z), 0, (rr, rr, rr * 0.8)))
            for v in res["verts"]:
                v.co += Vector(rng.uniform(-0.12, 0.12, 3)) * rr
            paint(res["verts"], col)
print("TREES", len(pts), flush=True)


dress = []
for k, mat in MATS.items():
    me = bpy.data.meshes.new("DR_" + k)
    BM[k].to_mesh(me)
    BM[k].free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = k in SMOOTH
    o = bpy.data.objects.new("DR_" + k, me)
    scn.collection.objects.link(o)
    dress.append(o)

# ------------------------------------------------------------------ backdrop cards (PLACEHOLDER: concept-art crops)


def card(name, png, W, Hc, cx, y, strength):
    img = bpy.data.images.load(os.path.join(REF, png), check_existing=True)
    img.alpha_mode = "STRAIGHT"
    m, nt = nodes_mat("VG_" + name)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = img
    ti.interpolation = "Cubic"
    ti.extension = "EXTEND"
    L(ti.outputs["Color"], em.inputs["Color"])
    L(ti.outputs["Alpha"], mx.inputs["Fac"])
    L(tr.outputs["BSDF"], mx.inputs[1])
    L(em.outputs["Emission"], mx.inputs[2])
    L(mx.outputs["Shader"], out.inputs["Surface"])
    me = bpy.data.meshes.new("VG_" + name)
    z0 = -3.0
    me.from_pydata([(cx - W / 2, y, z0), (cx + W / 2, y, z0), (cx + W / 2, y, z0 + Hc), (cx - W / 2, y, z0 + Hc)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UV")
    for lp, uvc in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[lp.index].uv = uvc
    me.materials.append(m)
    o = bpy.data.objects.new("VG_" + name, me)
    scn.collection.objects.link(o)
    o.visible_shadow = False
    o.visible_diffuse = False
    o.visible_transmission = False
    o.visible_volume_scatter = False
    return o


CW = 1500.0
st = card("backdrop_street", "backdrop_street.png", CW, CW * 352 / 985, 30 - 0.17 * CW, 670, 1.5)
ae = card("backdrop_aerial", "backdrop_aerial.png", CW, CW * 292 / 940, 40 - 0.20 * CW, 670, 1.5)

# ------------------------------------------------------------------ light (golden, from the NNW, behind the backdrop side)
sun = bpy.data.objects["LD_sun"]
sky = next(n for n in scn.world.node_tree.nodes if n.type == "TEX_SKY")
az = Vector((-0.9, 0.3, 0.0)).normalized()
el = math.radians(30.0)
v = Vector((az.x * math.cos(el), az.y * math.cos(el), math.sin(el)))
sun.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
sun.data.color = (1.0, 0.80, 0.58)
sun.data.energy = 6.5
sky.sun_elevation = el
sky.sun_rotation = math.atan2(az.x, az.y)
for an, val in (("air_density", 1.3), ("aerosol_density", 3.5), ("dust_density", 3.0)):
    if hasattr(sky, an):
        setattr(sky, an, val)

# ------------------------------------------------------------------ cameras
dg = bpy.context.evaluated_depsgraph_get()


def cam(name, loc, tgt, lens, eye=None):
    cd = bpy.data.cameras.new(name)
    cd.sensor_width = 36.0
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 4000.0
    o = bpy.data.objects.new(name, cd)
    scn.collection.objects.link(o)
    p = Vector(loc)
    if eye is not None:
        hit, hl, *_ = scn.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((p.x, p.y, 300.0)), Vector((0, 0, -1)))
        p.z = (hl.z if hit else 0.9) + eye
    o.location = p
    o.rotation_euler = (Vector(tgt) - p).to_track_quat("-Z", "Y").to_euler()
    return o


# ---- v3 haze: world volume, density falls off with height (valley mist), slightly forward-scattering
wt = scn.world.node_tree
for n in [n for n in wt.nodes if n.type == "OUTPUT_WORLD"]:
    wout = n
gE = wt.nodes.new("ShaderNodeNewGeometry")
sE = wt.nodes.new("ShaderNodeSeparateXYZ")
wt.links.new(gE.outputs["Position"], sE.inputs["Vector"])
mxz = wt.nodes.new("ShaderNodeMath")
mxz.operation = "MAXIMUM"
mxz.inputs[1].default_value = 0.0
wt.links.new(sE.outputs["Z"], mxz.inputs[0])
mz = wt.nodes.new("ShaderNodeMath")
mz.operation = "MULTIPLY"
mz.inputs[1].default_value = -1.0 / FOG_H
wt.links.new(mxz.outputs["Value"], mz.inputs[0])
ex = wt.nodes.new("ShaderNodeMath")
ex.operation = "POWER"
ex.inputs[0].default_value = 2.71828
wt.links.new(mz.outputs["Value"], ex.inputs[1])
dn = wt.nodes.new("ShaderNodeMath")
dn.operation = "MULTIPLY"
dn.inputs[1].default_value = FOG_D
wt.links.new(ex.outputs["Value"], dn.inputs[0])
pv = wt.nodes.new("ShaderNodeVolumeScatter")
pv.inputs["Color"].default_value = (0.78, 0.85, 0.92, 1)
pv.inputs["Anisotropy"].default_value = 0.35
wt.links.new(dn.outputs["Value"], pv.inputs["Density"])
wt.links.new(pv.outputs["Volume"], wout.inputs["Volume"])
scn.cycles.volume_bounces = 1
scn.cycles.volume_step_rate = 1.5

bpy.context.view_layer.update()
cam("CAM_street", (-6.0, -31.5, 0), (40.0, 660.0, 42.0), 21.0, eye=1.7)
cam("CAM_aerial", AER_LOC, AER_TGT, AER_LENS)

# ------------------------------------------------------------------ stats + save
tri = {}
for bid, objs in dobjs.items():
    t = 0
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        t += len(me.loop_triangles)
    tri[bid] = t
for o in [terrain] + dress:
    o.data.calc_loop_triangles()
    tri[o.name] = len(o.data.loop_triangles)
inst_tris = sum(tri[b] * c for b, c in inst_count.items())
unique_tris = sum(tri[b] for b in dobjs)
other = sum(v for k, v in tri.items() if k not in dobjs)
print("STATS unique building tris", unique_tris, "instanced building tris", inst_tris, "terrain+dressing tris", other, flush=True)
for k, v in tri.items():
    print("STATS_PER", k, v, "x", inst_count.get(k, 1), flush=True)
scn["vg2_inst_tris"] = inst_tris
scn["vg2_unique_tris"] = unique_tris
scn["vg2_other_tris"] = other
scn["vg2_instances"] = len(PL)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True, compress=False)
print("SAVED", OUT, flush=True)






