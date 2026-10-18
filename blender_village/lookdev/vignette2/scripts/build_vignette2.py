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
REF = ROOT + r"\vignette2\ref"
HELPER_KEYS = ("scale_fig", "figure", "helper", "human", "proxy", "dummy", "measure", "ref_", "gizmo")
DESIGNS = {
    "v7_cottage": R2, "v8_byre_smokehouse": R2, "v9_ale_house": R2, "v10_net_loft_cottage": R2,
    "v3_longhouse_roundend": WORK, "v6_barn": WORK, "wattle_roundhut": WORK,
    "hilltop_keep": WORK, "tower_windmill": WORK, "v1_stone_watchtower": WORK, "v2_tiered_hall": WORK, "v4_mixed": WORK,
}
BASE = "v7_cottage"
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
for (bid, x, y, r, s) in PL:
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
    rm.inputs["From Min"].default_value = 0.80
    rm.inputs["From Max"].default_value = 0.62
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
    rcr.color_ramp.elements[0].color = (0.045, 0.040, 0.036, 1)
    rcr.color_ramp.elements[1].position = 0.65
    rcr.color_ramp.elements[1].color = (0.20, 0.18, 0.16, 1)
    L(n3.outputs["Fac"], rcr.inputs["Fac"])
    mix4 = nt.nodes.new("ShaderNodeMix")
    mix4.data_type = "RGBA"
    L(rm.outputs["Result"], mix4.inputs["Factor"])
    L(mix3.outputs["Result"], mix4.inputs["A"])
    L(rcr.outputs["Color"], mix4.inputs["B"])
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
designs_lc = bpy.context.view_layer.layer_collection.children["VG_DESIGNS"]
designs_lc.exclude = True

# ------------------------------------------------------------------ procedural set dressing
MATS = {
    "wood": simple("D_wood", (0.12, 0.08, 0.05), 0.9, 0.7),
    "plank": simple("D_plank", (0.22, 0.155, 0.09), 0.85, 0.6),
    "stone": simple("D_stone", (0.30, 0.285, 0.26), 0.95, 0.6),
    "hay": simple("D_hay", (0.55, 0.42, 0.16), 0.95, 0.4),
    "tree": simple("D_tree", (0.05, 0.11, 0.05), 0.9, 0.8),
    "trunk": simple("D_trunk", (0.07, 0.045, 0.03), 0.9),
    "sail": simple("D_sail", (0.62, 0.55, 0.42), 0.95),
    "hull": simple("D_hull", (0.30, 0.075, 0.04), 0.7),
    "hull2": simple("D_hull2", (0.10, 0.07, 0.05), 0.7),
    "fig1": simple("D_fig1", (0.28, 0.10, 0.06), 0.9),
    "fig2": simple("D_fig2", (0.16, 0.13, 0.08), 0.9),
    "fig3": simple("D_fig3", (0.10, 0.14, 0.10), 0.9),
    "skin": simple("D_skin", (0.45, 0.30, 0.22), 0.7),
    "rock": simple("D_rock", (0.13, 0.12, 0.105), 0.95, 0.9),
}
BM = {k: bmesh.new() for k in MATS}


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


# quay promenade deck + posts
for phi in range(100, 262, 5):
    x, y = pol(32.2, phi)
    box("plank", (x, y, 0.8), (3.0, 3.6, 0.3), math.radians(phi + 90))
    if phi % 10 == 0:
        px, py = pol(30.3, phi)
        cyl("wood", (px, py, -0.2), 0.17, 2.4)
# piers
PIERS = [(205, 30.5, 8.0), (155, 30.5, 14.0), (235, 30.5, 17.0), (125, 30.5, 19.0)]
for phi, R0, R1 in PIERS:
    L = R0 - R1
    mid = (R0 + R1) / 2
    x, y = pol(mid, phi)
    box("plank", (x, y, 0.72), (L, 2.2, 0.22), math.radians(phi))
    for k in range(int(L // 3) + 1):
        for sd in (-1.0, 1.0):
            px, py = pol(R1 + 1.0 + k * 3.0, phi)
            px, py = aside((px, py), phi, sd * 1.05)
            cyl("wood", (px, py, -0.4), 0.14, 2.6)
# fjord jetty on the south ribbon
for k in range(7):
    JX = float(shore22(-48)) - 2.0
    box("plank", (JX + k * 3, -48, 0.72), (3.0, 2.0, 0.2))
    cyl("wood", (JX + k * 3 + 1.0, -49.0, -0.4), 0.14, 2.6)
    cyl("wood", (JX + k * 3 + 1.0, -47.0, -0.4), 0.14, 2.6)
# boats
for (c, rz, sc) in (((6.0, -11.0), 100, 1.0), ((-1.0, 13.0), 80, 0.95)):
    hull("hull", (c[0], c[1], 0.65), (3.8 * sc, 1.25 * sc, 1.1 * sc), math.radians(rz))
    cyl("wood", (c[0], c[1], 4.4), 0.11, 8.8)
    ang = math.radians(rz)
    cyl("wood", (c[0] + 1.8 * math.cos(ang), c[1] + 1.8 * math.sin(ang), 2.1), 0.07, 3.6, rz=ang, rx=math.pi / 2 * 0)
    # sail: triangle in the boat's own plane
    p0 = Vector((c[0], c[1], 8.3))
    d1 = Vector((math.cos(ang), math.sin(ang), 0))
    for off in (-0.04, 0.04):
        a0 = p0 + Vector((0, 0, off))
        v1 = BM["sail"].verts.new(a0 + d1 * 0.1)
        v2 = BM["sail"].verts.new(a0 - Vector((0, 0, 5.2)) + d1 * 0.1)
        v3 = BM["sail"].verts.new(a0 - Vector((0, 0, 5.2)) + d1 * 3.4)
        BM["sail"].faces.new((v1, v2, v3))
rows = [((-3.5, -22.0), 75, 0.0), ((-10.0, -17.5), 55, 0.0), ((29.0, -44.0), 95, 0.0), ((34.0, -53.0), 80, 0.0), ((-6.5, -2.0), 70, 0.0), ((-13.5, -19.0), 60, 0.0), ((-9.0, 24.0), 110, 0.0), ((8.0, 30.0), 100, 0.0), ((20.0, 14.0), 85, 0.0),
        ((-26.0, 1.5), 12, 0.0), ((-22.5, -12.0), 40, 0.0)]
for (c, rz, _) in rows:
    hull("hull" if rng.rand() > 0.3 else "hull2", (c[0], c[1], 0.28), (1.9, 0.72, 0.62), math.radians(rz))
    box("plank", (c[0], c[1], 0.34), (0.2, 1.2, 0.08), math.radians(rz))
for c, rz in (((70.0, 70.0), 80), ((95.0, 160.0), 100), ((60.0, 230.0), 75)):
    hull("hull", (c[0], c[1], 0.28), (1.9, 0.72, 0.62), math.radians(rz))
# hay, woodpiles, well, crates
for (R, phi) in ((92, 130), (95, 160), (95, 212), (90, 240), (98, 180), (96, 118)):
    x, y = pol(R, phi)
    z = gz(x, y)
    cyl("hay", (x, y, z + 1.0), 1.4, 2.0, r2=1.2)
    cyl("hay", (x, y, z + 2.5), 1.2, 1.4, r2=0.05)
for (x, y, rz) in ((-30.0, -27.0, 0.3), (-41.0, 19.0, 1.0), (-14.0, -34.5, 0.3), (-16.0, -55.0, 0.5), (-45.0, -2.0, 2.0), (-12.0, 49.0, 0.2), (3.0, 66.0, 1.2)):
    z = gz(x, y)
    for row, n in enumerate((6, 5, 4)):
        for k in range(n):
            lx = (k - (n - 1) / 2) * 0.28
            cyl("wood", (x + lx * math.cos(rz), y + lx * math.sin(rz), z + 0.17 + row * 0.26), 0.13, 1.5, rz=rz + math.pi / 2, rx=math.pi / 2 * 0 + math.pi / 2 * 0)
# well on the plaza
wx, wy = pol(35.0, 168)
wz = gz(wx, wy)
cyl("stone", (wx, wy, wz + 0.45), 1.0, 0.9, seg=14)
for sx in (-0.9, 0.9):
    box("wood", (wx + sx, wy, wz + 1.5), (0.14, 0.14, 2.0))
box("wood", (wx, wy, wz + 2.5), (2.2, 0.16, 0.14))
cyl("wood", (wx, wy, wz + 2.9), 1.5, 0.7, seg=4, r2=0.05, rz=math.pi / 4)
# barrels / crates on the quay and figures
for k in range(14):
    phi = rng.uniform(112, 248)
    x, y = pol(rng.uniform(32.5, 34.3), phi)
    if k % 2:
        cyl("wood", (x, y, 0.95 + 0.4), 0.32, 0.8, seg=10)
    else:
        box("plank", (x, y, 0.95 + 0.3), (0.7, 0.7, 0.6), rng.uniform(0, 3))
for (x, y, kk) in ((-12.5, -26.5, "fig1"), (-2.5, -25.5, "fig2"), (-16.0, -33.0, "fig2"), (-21.5, -9.0, "fig2"), (-27.5, -4.0, "fig1"),
                   (-20.0, -20.0, "fig3"), (-26.0, 14.0, "fig1"), (-3.5, -28.0, "fig2")):
    z = gz(x, y)
    cyl(kk, (x, y, z + 0.65), 0.34, 1.3, r2=0.16, seg=8)
    ell("skin", (x, y, z + 1.45), (0.12, 0.12, 0.13), seg=8)
    ell(kk, (x, y, z + 1.5), (0.15, 0.15, 0.13), seg=8)
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
            z = gz(px, py)
            cyl("wood", (px, py, z + 0.55), 0.06, 1.1, seg=5)
        for zz in (0.45, 0.85):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            box("wood", (mx, my, gz(mx, my) + zz), (L, 0.05, 0.08), ang)
# rocks
for k in range(70):
    phi = rng.uniform(95, 265)
    x, y = pol(rng.uniform(30.0, 33.5), phi)
    rock((x, y, gz(x, y) + 0.05), rng.uniform(0.2, 0.65))
for k in range(30):
    x, y = (EAST + rng.uniform(-6, 4), rng.uniform(-100, 400))
    rock((x, y, gz(x, y) + 0.5), rng.uniform(1.0, 4.0))
for k in range(25):
    y = rng.choice([-1, 1]) * rng.uniform(40, 110)
    x = float(shore22(y)) - rng.uniform(0, 4)
    rock((x, y, gz(x, y) + 0.1), rng.uniform(0.5, 1.6))
# trees (merged mesh)
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
while len(pts) < 1500 and tries < 40000:
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
for (x, y, z) in pts:
    hgt = rng.uniform(6.0, 13.0) * (1.0 + 0.4 * smooth(-100, -250, x))
    w = hgt * rng.uniform(0.22, 0.30)
    cyl("trunk", (x, y, z + hgt * 0.1), 0.16 * hgt / 8, hgt * 0.2, seg=5)
    for t in range(4):
        zb = z + hgt * (0.12 + 0.2 * t)
        rr = w * (1.0 - 0.2 * t)
        cyl("tree", (x, y, zb + hgt * 0.17), rr, hgt * 0.34, seg=8, r2=0.05 * rr)
print("TREES", len(pts), flush=True)
dress = []
for k, mat in MATS.items():
    me = bpy.data.meshes.new("DR_" + k)
    BM[k].to_mesh(me)
    BM[k].free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
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


bpy.context.view_layer.update()
cam("CAM_street", (-6.0, -31.5, 0), (40.0, 660.0, 42.0), 21.0, eye=1.7)
cam("CAM_aerial", (8.0, -88.0, 58.0), (48.0, 150.0, 4.0), 24.0)

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






