"""Vignette: the nine r2 lookdev buildings assembled into one small fjord-harbour village.

python.exe -I build_vignette.py <out.blend>
    Reads (never writes) lookdev/village_r2/work/<id>_lookdev.blend.  Starts from hilltop_keep_lookdev.blend so the
    r2 colour management / LD_sun / LD_world (Nishita sky) are inherited, strips its cameras, ground and hidden
    helpers, appends the other eight buildings' renderable meshes, parents each building to BLD_<id>, builds the
    terrain + water + path, and saves to <out.blend> (a new file).

World datum: water surface Z 0.  Harbour house quay datum (its local Z 0) at world Z +0.9, so its water (local
-0.9) is exactly the world water plane, its land (local -0.045) at world 0.855, its bed (local -2.5) at -1.6.
Water is to the south (-Y); the village climbs north.  Lighting A ("r2 day") is the inherited sun + sky; lighting
B ("cinematic") is applied at render time by render_vignette.py (it only changes sun, sky and adds the fog domain,
which is built here hidden as VG_fog).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

OUT = os.path.abspath(sys.argv[-1])
SRC = r"C:\GitHubDesktop\git_test\blender_village\lookdev\village_r2\work"
TEX = r"C:\GitHubDesktop\git_test\blender_village\lookdev\textures"
HELPER_KEYS = ("scale_fig", "figure", "helper", "human", "proxy", "dummy", "measure", "ref_", "gizmo")
HH_Z = 0.9          # harbour house quay datum in world Z
QUAY_LAND = HH_Z - 0.045

# id: (x, y, rot_deg).  Local -Y is every building's entrance side except the barn (+X).
LAYOUT = {
    "v5_harbour_house":      (0.0, -26.0, 180.0),   # water gable (+Y local) faces the harbour (-Y world)
    "v1_stone_watchtower":   (-33.0, -36.0, 35.0),  # on the west headland at the harbour mouth
    "v2_tiered_hall":        (2.0, 6.0, -8.0),      # central, entrance to the harbour
    "hilltop_keep":          (-17.0, 41.0, 18.0),   # highest rise at the back
    "tower_windmill":        (47.0, 36.0, -35.0),   # its own rise to the NE
    "v3_longhouse_roundend": (-26.0, 2.0, 90.0),    # west of the square, entrance faces east
    "wattle_roundhut":       (-19.0, -13.0, -25.0), # between the longhouse and the harbour house
    "v4_mixed":              (26.0, -7.0, 28.0),    # mill-house east of the harbour
    "v6_barn":               (24.0, 20.0, 180.0),   # NE of the hall, doors (local +X) face west to the path
}
ORDER = ["hilltop_keep", "wattle_roundhut", "tower_windmill", "v1_stone_watchtower", "v2_tiered_hall",
         "v3_longhouse_roundend", "v4_mixed", "v5_harbour_house", "v6_barn"]


def eligible(o):
    n = o.name.lower()
    if o.type != "MESH" or o.hide_render or o.name.startswith(("LD_", "VR2_", "HH_")):
        return False
    if any(c.name.upper().startswith("DECAL_ANCHOR") or c.hide_render for c in o.users_collection):
        return False
    return not any(k in n for k in HELPER_KEYS)


# ---------------------------------------------------------------- base file: the keep
bpy.ops.wm.open_mainfile(filepath=os.path.join(SRC, "hilltop_keep_lookdev.blend"))
scn = bpy.context.scene
keep_objs = [o for o in scn.objects if eligible(o)]
for o in list(scn.objects):
    if o in keep_objs or o.name == "LD_sun":
        continue
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name.upper().startswith("DECAL_ANCHOR"):
        bpy.data.collections.remove(c)
bld_objs = {"hilltop_keep": keep_objs}

# ---------------------------------------------------------------- append the other eight
for bid in ORDER:
    if bid == "hilltop_keep":
        continue
    path = os.path.join(SRC, bid + "_lookdev.blend")
    # names of the eligible objects: read via a temporary link-less load of the object list + collection info
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    got = [o for o in dst.objects if o is not None]
    col = bpy.data.collections.new("BLD_" + bid)
    scn.collection.children.link(col)
    keep, drop = [], []
    for o in got:
        n = o.name.lower()
        ok = (o.type == "MESH" and not o.hide_render and not o.name.startswith(("LD_", "VR2_", "HH_", "DA_"))
              and not any(k in n for k in HELPER_KEYS))
        (keep if ok else drop).append(o)
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in keep:
        col.objects.link(o)
    bld_objs[bid] = keep
    print("APPENDED", bid, len(keep), "dropped", len(drop), flush=True)

# keep's objects into their own collection too (they stay in their KEEP_* collections)
col = bpy.data.collections.new("BLD_hilltop_keep")
scn.collection.children.link(col)

# ---------------------------------------------------------------- de-duplicate images by file path
by_path, n_dup = {}, 0
for im in list(bpy.data.images):
    if im.source != "FILE":
        continue
    key = (os.path.normcase(os.path.abspath(bpy.path.abspath(im.filepath, library=im.library))), im.colorspace_settings.name)
    if key in by_path and by_path[key] is not im:
        im.user_remap(by_path[key])
        bpy.data.images.remove(im)
        n_dup += 1
    else:
        by_path[key] = im
print("IMAGES unique", len(by_path), "duplicates merged", n_dup, flush=True)
missing = [im.name for im in bpy.data.images if im.source == "FILE" and not os.path.exists(bpy.path.abspath(im.filepath))]
print("IMAGES missing", missing, flush=True)
try:
    print("PURGED", bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True), flush=True)
except Exception as ex:  # noqa
    print("purge failed", ex)

# ---------------------------------------------------------------- placement empties
bounds = {}
for bid, objs in bld_objs.items():
    pts = np.array([tuple(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box])
    bounds[bid] = (pts.min(0), pts.max(0))


def place_matrix(bid, z):
    x, y, r = LAYOUT[bid]
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(r), 4, "Z")


# ---------------------------------------------------------------- terrain height field
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


HHX, HHY, _ = LAYOUT["v5_harbour_house"]
YQ, YS = 3.427 - 0.30, 0.227 - 0.30            # hh_shots land lines (local)
SHORE_HH = HHY - YQ                            # world y of the quay face line (rot 180)


def shore_y(x):
    return (SHORE_HH - 14.0 * np.exp(-((x + 34.0) / 10.0) ** 2)     # west headland (harbour mouth)
            + 6.0 * smooth(14.0, 55.0, x) - 3.0 * smooth(-60.0, -95.0, x))


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


def natural_h(x, y):
    d = y - shore_y(x)                                         # + inland
    near_hh = np.exp(-((x - HHX) / 14.0) ** 2)
    # land terrace at the quay level; bank steep next to the harbour house, a gentler beach elsewhere
    bank_w = 1.5 * near_hh + 5.0 * (1 - near_hh)
    land = QUAY_LAND + 0.05 * np.clip(d - 8.0, 0, None) + 0.5 * noise2(x, y, 3) * smooth(6.0, 20.0, d)
    land += 7.5 * np.exp(-(((x + 17.0) / 15.0) ** 2 + ((y - 42.0) / 13.0) ** 2))      # keep rise
    land += 4.5 * np.exp(-(((x - 47.0) / 11.0) ** 2 + ((y - 36.0) / 10.0) ** 2))      # windmill rise
    land += 0.6 * np.exp(-(((x + 34.0) / 8.0) ** 2 + ((y + 37.0) / 6.0) ** 2))        # headland knoll
    sea = -1.75 - 0.6 * smooth(0.0, -30.0, d)
    t = smooth(-bank_w, 0.0, d)
    h = sea + (land - sea) * t
    # fjord walls (far, beyond the village) so the horizon is land and not the plane edge
    # (kept low enough that a 10 deg sun from any side clears them: h / distance < tan 10 deg out to the grid edge)
    wall = 0.0008 * np.clip(np.abs(x) - 140.0, 0, None) ** 2 + 0.0008 * np.clip(y - 110.0, 0, None) ** 2
    wall *= 1.0 + 0.2 * np.sin(y / 61.0 + 1.3) * np.sin(x / 47.0)
    return h + wall


def axis(core0, core1, step, far0, far1, coarse):
    a = list(np.arange(core0, core1 + 1e-6, step))
    lo = list(np.arange(core0 - coarse, far0 - 1e-6, -coarse))[::-1]
    hi = list(np.arange(core1 + coarse, far1 + 1e-6, coarse))
    return np.array(lo + a + hi)


xs = axis(-80.0, 80.0, 0.5, -420.0, 420.0, 6.0)
ys = axis(-60.0, 66.0, 0.5, -420.0, 480.0, 6.0)
X, Y = np.meshgrid(xs, ys)        # shape (ny, nx)
H = natural_h(X, Y)


# path: polyline network (world xy), 2.6 m wide packed earth
PATHS = [
    [(-3.0, -17.0), (-1.0, -12.0), (0.5, -5.0), (1.3, 0.6)],                      # harbour house -> hall door
    [(5.9, -17.0), (-1.0, -12.0)],                                                # harbour house wing door
    [(0.5, -5.0), (-7.0, 4.0), (-11.0, 18.0), (-14.0, 30.0), (-15.3, 36.5)],      # -> keep door
    [(-1.0, -12.0), (-12.0, -6.0), (-22.6, -0.4)],                                # -> longhouse door
    [(-12.0, -6.0), (-16.0, -17.0), (-20.4, -17.2)],                              # -> roundhut door
    [(-16.0, -17.0), (-24.0, -24.0), (-28.0, -33.0), (-30.6, -38.4)],             # -> watchtower door
    [(-1.0, -12.0), (12.0, -10.0), (26.3, -11.0)],                                # -> mill-house door
    [(12.0, -10.0), (13.0, 8.0), (16.3, 21.3)],                                   # -> barn door
    [(13.0, 8.0), (32.0, 26.0), (44.5, 32.5)],                                    # -> windmill door
]


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy))


D = np.full(X.shape, 1e9)
for pl in PATHS:
    for a, b in zip(pl[:-1], pl[1:]):
        D = np.minimum(D, seg_dist(X, Y, a, b))
PATHW = 1.0 - smooth(1.1, 1.9, D + 0.35 * noise2(X * 3, Y * 3, 11))
H -= 0.04 * PATHW

# building pads: flatten under each footprint (rotated local bounds + 0.6 m), blend over 4 m
place_z = {}
for bid in ORDER:
    mn, mx = bounds[bid]
    x0, y0, r = LAYOUT[bid]
    c, s = math.cos(math.radians(r)), math.sin(math.radians(r))
    lx = (X - x0) * c + (Y - y0) * s            # world -> building local
    ly = -(X - x0) * s + (Y - y0) * c
    if bid == "v5_harbour_house":
        # land side only (local y < YQ); quay level, terrain 1.5 cm under the stage boxes
        ex = np.maximum(np.maximum(mn[0] - 1.5 - lx, lx - mx[0] - 1.5), np.maximum(mn[1] - 4.0 - ly, ly - YQ))
        w = 1.0 - smooth(0.0, 5.0, ex)
        H = H + (QUAY_LAND - 0.015 - H) * w
        place_z[bid] = HH_Z
        continue
    ex = np.maximum(np.maximum(mn[0] - 0.6 - lx, lx - mx[0] - 0.6), np.maximum(mn[1] - 0.6 - ly, ly - mx[1] - 0.6))
    inside = ex <= 0
    h0 = float(H[inside].mean())
    hmin, hmax = float(H[inside].min()), float(H[inside].max())
    blend = float(np.clip(2.0 * (hmax - hmin), 4.0, 12.0))     # wider apron where the pad cuts a slope
    w = 1.0 - smooth(0.0, blend, ex)
    H = H + (h0 - H) * w
    place_z[bid] = h0 - 0.04                    # sink 4 cm (footings at local -0.05 go 9 cm under)
    print("PAD", bid, "h0 %.2f natural range %.2f..%.2f" % (h0, hmin, hmax), flush=True)

# harbour house hole: terrain faces whose centre is inside the stage rectangle are removed
mn, mx = bounds["v5_harbour_house"]
HOLE = (mn[0] - 1.0, mx[0] + 1.0, mn[1] - 3.0, mx[1] + 1.5)     # local x0, x1, y0, y1

ny, nx = X.shape
verts = np.stack([X.ravel(), Y.ravel(), H.ravel()], 1)
ii, jj = np.meshgrid(np.arange(ny - 1), np.arange(nx - 1), indexing="ij")
cx = (xs[jj] + xs[jj + 1]) * 0.5
cy = (ys[ii] + ys[ii + 1]) * 0.5
lcx, lcy = -(cx - HHX), -(cy - HHY)              # rot 180
keepf = ~((lcx > HOLE[0]) & (lcx < HOLE[1]) & (lcy > HOLE[2]) & (lcy < HOLE[3]))
a = (ii * nx + jj)[keepf]
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
attr = tm.attributes.new("path", "FLOAT", "POINT")
attr.data.foreach_set("value", PATHW.ravel().astype(np.float32))
tm.polygons.foreach_set("use_smooth", np.ones(len(quads), dtype=bool))
# drop unused vertices (inside the hole) is unnecessary; they are unreferenced loose verts -> remove
terrain = bpy.data.objects.new("VG_terrain", tm)
scn.collection.objects.link(terrain)
print("TERRAIN verts", len(verts), "quads", len(quads), flush=True)


# ---------------------------------------------------------------- terrain material
def ground_material():
    m = bpy.data.materials.new("VG_ground")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    # moss texture (palette) tiled every 3 m as the grass break-up
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 3.0, 1 / 3.0, 1 / 3.0)
    L(geo.outputs["Position"], mp.inputs["Vector"])
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(os.path.join(TEX, "nordic_moss_se4rwei_2k", "Nordic_Moss_se4rwei_2K_BaseColor.jpg"), check_existing=True)
    L(mp.outputs["Vector"], im.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.9
    hsv.inputs["Value"].default_value = 0.7
    L(im.outputs["Color"], hsv.inputs["Color"])
    # large patches grass <-> worn earth
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.035
    n1.inputs["Detail"].default_value = 5.0
    L(geo.outputs["Position"], n1.inputs["Vector"])
    patch = nt.nodes.new("ShaderNodeMapRange")
    patch.inputs["From Min"].default_value = 0.36
    patch.inputs["From Max"].default_value = 0.48
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
    grass_t.inputs["B"].default_value = (0.50, 0.66, 0.30, 1)
    L(hsv.outputs["Color"], grass_t.inputs["A"])
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    L(patch.outputs["Result"], mix1.inputs["Factor"])
    L(ecr.outputs["Color"], mix1.inputs["A"])          # earth
    L(grass_t.outputs["Result"], mix1.inputs["B"])     # grass
    # shore band: below the quay level, darker wet shingle
    shore = nt.nodes.new("ShaderNodeMapRange")
    shore.inputs["From Min"].default_value = QUAY_LAND - 0.25
    shore.inputs["From Max"].default_value = QUAY_LAND + 0.05
    shore.inputs["To Min"].default_value = 1.0
    shore.inputs["To Max"].default_value = 0.0
    L(sep.outputs["Z"], shore.inputs["Value"])
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    L(shore.outputs["Result"], mix2.inputs["Factor"])
    L(mix1.outputs["Result"], mix2.inputs["A"])
    mix2.inputs["B"].default_value = (0.055, 0.052, 0.046, 1)
    # path
    pa = nt.nodes.new("ShaderNodeAttribute")
    pa.attribute_name = "path"
    pcr = nt.nodes.new("ShaderNodeValToRGB")
    pcr.color_ramp.elements[0].color = (0.115, 0.092, 0.068, 1)
    pcr.color_ramp.elements[1].color = (0.17, 0.140, 0.105, 1)
    L(n2.outputs["Fac"], pcr.inputs["Fac"])
    mix3 = nt.nodes.new("ShaderNodeMix")
    mix3.data_type = "RGBA"
    L(pa.outputs["Fac"], mix3.inputs["Factor"])
    L(mix2.outputs["Result"], mix3.inputs["A"])
    L(pcr.outputs["Color"], mix3.inputs["B"])
    L(mix3.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.93
    bmp = nt.nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.25
    bmp.inputs["Distance"].default_value = 0.05
    L(n2.outputs["Fac"], bmp.inputs["Height"])
    L(bmp.outputs["Normal"], bs.inputs["Normal"])
    return m


terrain.data.materials.append(ground_material())


# ---------------------------------------------------------------- hh_shots land (flagstone) + water, verbatim recipes
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


def water_material():
    wm = bpy.data.materials.new("HH_water")
    wm.use_nodes = True
    wb = wm.node_tree.nodes.get("Principled BSDF")
    wb.inputs["Base Color"].default_value = (0.012, 0.045, 0.045, 1.0)
    wb.inputs["Roughness"].default_value = 0.06
    wb.inputs["IOR"].default_value = 1.33
    wb.inputs["Transmission Weight"].default_value = 0.45
    wn = wm.node_tree
    wnoise = wn.nodes.new("ShaderNodeTexNoise")
    wnoise.inputs["Scale"].default_value = 2.5
    wnoise.inputs["Detail"].default_value = 4.0
    bump = wn.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.05
    wn.links.new(wnoise.outputs["Fac"], bump.inputs["Height"])
    wn.links.new(bump.outputs["Normal"], wb.inputs["Normal"])
    return wm


hh_empty_m = place_matrix("v5_harbour_house", HH_Z)
lm = hh_land_material()
stage = []


def box(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    scn.collection.objects.link(o)
    stage.append(o)
    return o


# the three hh_shots land boxes, clipped to the hole + 1 m overlap, top at local -0.045
hx0, hx1, hy0, hy1 = HOLE[0] - 1.0, HOLE[1] + 1.0, HOLE[2] - 1.0, HOLE[3]
box("HH_land", hx0, hx1, hy0, YS, -3.0, -0.045, lm)
box("HH_land", hx0, -0.608 - 0.30, YS, YQ, -3.0, -0.045, lm)
box("HH_land", 4.392 + 0.30, hx1, YS, YQ, -3.0, -0.045, lm)
# harbour bed under the stage (local -2.5 = the apply_lookdev ground level) so the slip is not bottomless
bedm = bpy.data.materials.new("VG_bed")
bedm.use_nodes = True
bedm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.048, 0.04, 1)
bedm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
bed = bpy.data.meshes.new("VG_bed")
bed.from_pydata([(HOLE[0] - 1, HOLE[2] - 1, -2.55), (HOLE[1] + 1, HOLE[2] - 1, -2.55),
                 (HOLE[1] + 1, HOLE[3] + 1, -2.55), (HOLE[0] - 1, HOLE[3] + 1, -2.55)], [], [(0, 1, 2, 3)])
bed.materials.append(bedm)
bo = bpy.data.objects.new("VG_bed", bed)
scn.collection.objects.link(bo)
stage.append(bo)

S = 1500.0
wme = bpy.data.meshes.new("HH_water")
wme.from_pydata([(-S, -S, 0.0), (S, -S, 0.0), (S, S, 0.0), (-S, S, 0.0)], [], [(0, 1, 2, 3)])
wme.materials.append(water_material())
water = bpy.data.objects.new("VG_water", wme)
scn.collection.objects.link(water)

# ---------------------------------------------------------------- empties + parenting
for bid in ORDER:
    e = bpy.data.objects.new("BLD_" + bid, None)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = 3.0
    scn.collection.objects.link(e)
    for o in bld_objs[bid]:
        o.parent = e
        o.matrix_parent_inverse = Matrix.Identity(4)
    if bid == "v5_harbour_house":
        for o in stage:
            if o.name.startswith(("HH_land", "VG_bed")):
                o.parent = e
                o.matrix_parent_inverse = Matrix.Identity(4)
    e.matrix_world = place_matrix(bid, place_z[bid])
    e["vignette_xy_rot"] = list(LAYOUT[bid])
    e["vignette_z"] = place_z[bid]
    print("PLACED", bid, LAYOUT[bid], "z %.3f" % place_z[bid], flush=True)

# ---------------------------------------------------------------- fog domain (lighting B), hidden by default
fm = bpy.data.materials.new("VG_fog")
fm.use_nodes = True
nt = fm.node_tree
nt.nodes.clear()
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Color"].default_value = (0.92, 0.88, 0.82, 1)
pv.inputs["Density"].default_value = 0.003
pv.inputs["Anisotropy"].default_value = 0.6
fo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(pv.outputs["Volume"], fo.inputs["Volume"])
F = 500.0
fme = bpy.data.meshes.new("VG_fog")
vs = [(x, y, z) for z in (-2.0, 25.0) for y in (-F, F) for x in (-F, F)]
fs = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
fme.from_pydata(vs, [], fs)
fme.materials.append(fm)
fog = bpy.data.objects.new("VG_fog", fme)
scn.collection.objects.link(fog)
fog.hide_render = True
fog.hide_viewport = True

# ---------------------------------------------------------------- stats + save
dg = bpy.context.evaluated_depsgraph_get()
tris, nobj = 0, 0
per = {}
for o in scn.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    o.evaluated_get(dg).to_mesh_clear()
    tris += n
    nobj += 1
    k = o.parent.name if o.parent else o.name
    per[k] = per.get(k, 0) + n
print("STATS mesh objects", nobj, "tris", tris, flush=True)
for k, v in sorted(per.items(), key=lambda kv: -kv[1]):
    print("STATS_PER", k, v, flush=True)
print("STATS images", len([i for i in bpy.data.images if i.source == "FILE"]), "materials", len(bpy.data.materials), flush=True)
scn["vignette_tris"] = tris
scn["vignette_mesh_objects"] = nobj
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True, compress=False)
print("SAVED", OUT, flush=True)
