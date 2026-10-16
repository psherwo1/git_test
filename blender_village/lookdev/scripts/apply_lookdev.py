"""Look-dev pass for blender_village kit buildings (Blender 5.1 as a Python module).

Usage (run with the isolated flag so nothing is imported from the cwd):
    python.exe -I apply_lookdev.py <source.blend> <output_folder> [options]

Options:
    --name NAME          building name (default: derived from the source file name)
    --textures DIR       extracted texture root (default: <script dir>/../textures)
    --shots a,b,c|all|none   which shots to render (default: all)
    --samples N          Cycles samples (default 128)
    --pct N              resolution percentage of 1920x1080 (default 100)
    --no-save            do not save the lookdev .blend

The script opens the source .blend (never saves over it), rebuilds the node tree of
every palette material (M_stone ... M_moss) with the downloaded texture sets, adds a
late-afternoon sun + procedural sky + ground plane, hides helper objects/empties,
creates the shot cameras, saves <output>/<name>_lookdev.blend and renders the shots
to <output>/renders/<name>/<shot>.png.
Downloaded .blend files bundled with the textures are never opened; only image files
are loaded.
"""
import sys
import os
import math
import argparse

import bpy
from mathutils import Vector

# --------------------------------------------------------------------------- args
argv = sys.argv[1:]
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--name", default=None)
ap.add_argument("--textures", default=None)
ap.add_argument("--shots", default="all")
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--no-save", action="store_true")
ap.add_argument("--cpu", action="store_true", help="render on the CPU (if the shared GPU is out of memory)")
args = ap.parse_args(argv)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.abspath(args.textures or os.path.join(SCRIPT_DIR, "..", "textures"))
OUT = os.path.abspath(args.out)
NAME = args.name or os.path.splitext(os.path.basename(args.src))[0].replace("_lookdev_src", "")

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.src))
scene = bpy.context.scene

# --------------------------------------------------------------------------- texture sets
# size = real-world size of one texture tile in metres (from the Megascans json where
# available, otherwise an assumption, see report)
TEXSETS = {
    "rockwall": dict(size=2.0, color="lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_BaseColor.jpg",
                     rough="lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_Roughness.jpg",
                     normal="lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_Normal.jpg",
                     ao="lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_AO.jpg"),
    "lichenrock": dict(size=2.0, color="lichen_rock_2k.blend/textures/lichen_rock_diff_2k.jpg",
                       rough="lichen_rock_2k.blend/textures/lichen_rock_rough_2k.exr",
                       normal="lichen_rock_2k.blend/textures/lichen_rock_nor_gl_2k.exr"),
    "moss": dict(size=2.0, color="nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_BaseColor.jpg",
                 rough="nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_Roughness.jpg",
                 normal="nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_Normal.jpg",
                 ao="nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_AO.jpg",
                 height="nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_Bump.jpg"),
    "wood": dict(size=1.0, color="rough_wood_2k.blend/textures/rough_wood_diff_2k.jpg",
                 rough="rough_wood_2k.blend/textures/rough_wood_rough_2k.jpg",
                 normal="rough_wood_2k.blend/textures/rough_wood_nor_gl_2k.exr"),
    "thatch": dict(size=2.0, color="riet_01_2k.blend/textures/riet_01_diff_2k.jpg",
                   rough="riet_01_2k.blend/textures/riet_01_rough_2k.jpg",
                   normal="riet_01_2k.blend/textures/riet_01_nor_gl_2k.exr"),
    "rust": dict(size=2.0, color="rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_BaseColor.jpg",
                 rough="rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_Roughness.jpg",
                 normal="rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_Normal.jpg",
                 ao="rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_AO.jpg"),
    # Megascans "Pure Imperfections" pack, UE packing: R = mask (grime), G = roughness, B = 1
    "dirtymetal": dict(size=1.0, packed="dirty_metal_rmmodbdp_2k_ue_mid/Textures/T_rmmodbdp_2K_MR.png"),
    "plaster": dict(size=2.0, color="patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_diff_2k.jpg",
                    rough="patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_rough_2k.exr",
                    normal="patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_nor_gl_2k.exr"),
}

PIECE_OFFSET = (37.1, 91.7, 0.0)
_img_cache = {}


def load_img(rel, noncolor):
    path = os.path.join(TEX, rel)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    key = (path, noncolor)
    if key in _img_cache:
        return _img_cache[key]
    im = bpy.data.images.load(path, check_existing=False)
    im.name = ("NC_" if noncolor else "") + os.path.basename(rel)
    im.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    _img_cache[key] = im
    return im


# --------------------------------------------------------------------------- node helpers
class G:
    """Small node-graph builder bound to one material."""

    def __init__(self, mat):
        if mat.node_tree is None:
            mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.x = -1800

    def node(self, t, **props):
        n = self.nt.nodes.new(t)
        for k, v in props.items():
            setattr(n, k, v)
        n.location = (self.x, 0)
        self.x += 40
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def _in(self, node, idx_or_name, val):
        sock = node.inputs[idx_or_name] if not isinstance(idx_or_name, str) else self._sock(node.inputs, idx_or_name)
        if isinstance(val, bpy.types.NodeSocket):
            self.link(val, sock)
        elif val is not None:
            sock.default_value = val
        return sock

    @staticmethod
    def _sock(socks, name):
        for s in socks:
            if s.identifier == name and s.enabled:
                return s
        for s in socks:
            if s.name == name and s.enabled:
                return s
        for s in socks:
            if s.identifier == name or s.name == name:
                return s
        raise KeyError(name)

    def out(self, node, name):
        return self._sock(node.outputs, name)

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(n, 0, a)
        if b is not None:
            self._in(n, 1, b)
        if c is not None:
            self._in(n, 2, c)
        return n.outputs[0]

    def vmath(self, op, a, b=None, c=None, scale=None):
        n = self.node("ShaderNodeVectorMath", operation=op)
        self._in(n, 0, a)
        if b is not None:
            self._in(n, 1, b)
        if c is not None:
            self._in(n, 2, c)
        if scale is not None:
            self._in(n, "Scale", scale)
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX", clamp=True):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_result=clamp)
        self._in(n, "Factor_Float", fac)
        self._in(n, "A_Color", a)
        self._in(n, "B_Color", b)
        return self.out(n, "Result_Color")

    def mixf(self, fac, a, b):
        n = self.node("ShaderNodeMix", data_type="FLOAT")
        self._in(n, "Factor_Float", fac)
        self._in(n, "A_Float", a)
        self._in(n, "B_Float", b)
        return self.out(n, "Result_Float")

    def maprange(self, v, a, b, c=0.0, d=1.0, interp="LINEAR"):
        n = self.node("ShaderNodeMapRange", interpolation_type=interp, clamp=True)
        self._in(n, "Value", v)
        self._in(n, "From Min", a)
        self._in(n, "From Max", b)
        self._in(n, "To Min", c)
        self._in(n, "To Max", d)
        return self.out(n, "Result")

    def hsv(self, color, h=0.5, s=1.0, v=1.0):
        n = self.node("ShaderNodeHueSaturation")
        self._in(n, "Hue", h)
        self._in(n, "Saturation", s)
        self._in(n, "Value", v)
        self._in(n, "Fac", 1.0)
        self._in(n, "Color", color)
        return self.out(n, "Color")

    def tex(self, rel, vec, noncolor):
        n = self.node("ShaderNodeTexImage", image=load_img(rel, noncolor), interpolation="Linear", extension="REPEAT")
        self.link(vec, n.inputs["Vector"])
        return n

    def rgb(self, c):
        return tuple(c) + (1.0,) if len(c) == 3 else tuple(c)


def setup_common(g):
    """Mask channels, UV, up-facing factor, output + principled."""
    ca = g.node("ShaderNodeVertexColor", layer_name="Mask")
    sep = g.node("ShaderNodeSeparateColor")
    g.link(ca.outputs["Color"], sep.inputs["Color"])
    R, Gw, B = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    uvn = g.node("ShaderNodeUVMap", uv_map="UVMap")
    uv = uvn.outputs["UV"]
    geo = g.node("ShaderNodeNewGeometry")
    nz = g.out(g.node("ShaderNodeSeparateXYZ"), "Z")
    g.link(geo.outputs["Normal"], nz.node.inputs[0])
    up = g.maprange(nz, 0.3, 0.8, interp="SMOOTHSTEP")
    bsdf = g.node("ShaderNodeBsdfPrincipled")
    outn = g.node("ShaderNodeOutputMaterial")
    g.link(bsdf.outputs["BSDF"], outn.inputs["Surface"])
    bsdf.location = (600, 0)
    outn.location = (900, 0)
    return dict(R=R, G=Gw, B=B, uv=uv, up=up, bsdf=bsdf)


def coords(g, ctx, size, per_piece=True, extra_offset=(0.0, 0.0, 0.0)):
    v = ctx["uv"]
    if per_piece:
        v = g.vmath("MULTIPLY_ADD", ctx["R"], PIECE_OFFSET, v)
    if any(extra_offset):
        v = g.vmath("ADD", v, extra_offset)
    return g.vmath("SCALE", v, scale=1.0 / size)


def sample(g, ctx, key, size_mult=1.0, per_piece=True, extra_offset=(0.0, 0.0, 0.0)):
    ts = TEXSETS[key]
    vec = coords(g, ctx, ts["size"] * size_mult, per_piece, extra_offset)
    r = {}
    if "packed" in ts:
        n = g.tex(ts["packed"], vec, True)
        sep = g.node("ShaderNodeSeparateColor")
        g.link(n.outputs["Color"], sep.inputs["Color"])
        r["mask"], r["rough"] = sep.outputs[0], sep.outputs[1]
        return r
    r["color"] = g.tex(ts["color"], vec, False).outputs["Color"]
    r["rough"] = g.tex(ts["rough"], vec, True).outputs["Color"]
    r["normal"] = g.tex(ts["normal"], vec, True).outputs["Color"]
    if "ao" in ts:
        ao = g.tex(ts["ao"], vec, True).outputs["Color"]
        r["color"] = g.mix(0.6, r["color"], ao, blend="MULTIPLY")
    if "height" in ts:
        r["height"] = g.tex(ts["height"], vec, True).outputs["Color"]
    return r


def jitter(g, ctx, color, amount=0.08, hue=0.012):
    """Per-piece value (+-amount) and tiny hue jitter from Mask R."""
    v = g.math("MULTIPLY_ADD", ctx["R"], 2 * amount, 1.0 - amount)
    fr = g.math("FRACT", g.math("MULTIPLY", ctx["R"], 13.73))
    h = g.math("MULTIPLY_ADD", fr, 2 * hue, 0.5 - hue)
    return g.hsv(color, h=h, s=1.0, v=v)


def wear(g, ctx, color, rough, light=0.18, rough_add=0.12, desat=0.15):
    """Mask G: worn pieces slightly lighter / greyer and rougher."""
    worn = g.hsv(color, 0.5, 1.0 - desat, 1.0 + light)
    color = g.mix(ctx["G"], color, worn)
    rough = g.math("MULTIPLY_ADD", ctx["G"], rough_add, rough, clamp=True)
    return color, rough


def damp(g, ctx, color, amount=0.35):
    """Mask B on non-up-facing surfaces reads as damp / dirt: darken."""
    side = g.math("SUBTRACT", 1.0, ctx["up"])
    f = g.math("MULTIPLY", g.math("MULTIPLY", ctx["B"], side), amount, clamp=True)
    return g.mix(f, color, (0.08, 0.075, 0.06, 1.0), blend="MULTIPLY")


def moss_layer(g, ctx, color, rough, normal, gain=4.0, lo=0.35, hi=0.65):
    """Blend nordic moss on top: factor from Mask B x up-facing, broken up by the moss height."""
    m = sample(g, ctx, "moss", per_piece=False)
    f = g.math("MULTIPLY", ctx["B"], ctx["up"])
    hgt = g.math("SUBTRACT", g.out(_bw(g, m["height"]), "Val"), 0.5)
    f = g.math("MULTIPLY_ADD", f, gain, g.math("MULTIPLY", hgt, 0.6))
    fac = g.maprange(f, lo, hi, interp="SMOOTHSTEP")
    mcol = g.hsv(m["color"], 0.5, 1.05, 0.95)
    color = g.mix(fac, color, mcol)
    rough = g.mixf(fac, rough, g.math("MULTIPLY_ADD", _val(g, m["rough"]), 0.6, 0.4, clamp=True))
    normal = g.mix(fac, normal, m["normal"])
    return color, rough, normal


def _bw(g, col):
    n = g.node("ShaderNodeRGBToBW")
    g.link(col, n.inputs["Color"])
    return n


def _val(g, col):
    return g.out(_bw(g, col), "Val")


def finish(g, ctx, color, rough, normal=None, nstrength=0.6, metallic=0.0, rough_min=0.0, rough_max=1.0):
    b = ctx["bsdf"]
    g.link(color, b.inputs["Base Color"])
    if isinstance(rough, bpy.types.NodeSocket) and rough.type == "RGBA":
        rough = _val(g, rough)
    if rough_min != 0.0 or rough_max != 1.0:
        rough = g.maprange(rough, 0.0, 1.0, rough_min, rough_max)
    if isinstance(rough, bpy.types.NodeSocket):
        g.link(rough, b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    if isinstance(metallic, bpy.types.NodeSocket):
        g.link(metallic, b.inputs["Metallic"])
    else:
        b.inputs["Metallic"].default_value = metallic
    if normal is not None:
        nm = g.node("ShaderNodeNormalMap", uv_map="UVMap")
        nm.inputs["Strength"].default_value = nstrength
        g.link(normal, nm.inputs["Color"])
        g.link(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Specular IOR Level"].default_value = 0.45


# --------------------------------------------------------------------------- materials
def soften(g, col, contrast):
    """Lower contrast: tames the bright white lichen splotches of lichen_rock."""
    n = g.node("ShaderNodeBrightContrast")
    g.link(col, n.inputs["Color"])
    n.inputs["Contrast"].default_value = contrast
    return n.outputs["Color"]


def mat_stone(mat, dressed=False, mossy=True, moss_gain=3.5):
    g = G(mat)
    c = setup_common(g)
    if dressed:
        a = sample(g, c, "lichenrock")
        color = g.hsv(soften(g, a["color"], -0.3), 0.5, 0.6, 1.15)  # lighter, less lichen (flattened, desaturated)
        rough, normal = _val(g, a["rough"]), a["normal"]
    else:
        a = sample(g, c, "rockwall")
        b = sample(g, c, "lichenrock", extra_offset=(11.3, 5.7, 0.0))
        pick = g.math("GREATER_THAN", c["R"], 0.5)
        bcol = g.hsv(soften(g, b["color"], -0.2), 0.5, 0.6, 1.0)
        color = g.mix(pick, a["color"], bcol)
        rough = g.mixf(pick, _val(g, a["rough"]), _val(g, b["rough"]))
        normal = g.mix(pick, a["normal"], b["normal"])
    color = jitter(g, c, color)
    color, rough = wear(g, c, color, rough, light=0.12, rough_add=0.08)
    color = damp(g, c, color)
    if mossy:
        color, rough, normal = moss_layer(g, c, color, rough, normal, gain=moss_gain, lo=0.4, hi=0.7)
    finish(g, c, color, rough, normal, nstrength=0.8)


def mat_mortar(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "lichenrock", size_mult=0.4, per_piece=False)
    col = g.hsv(a["color"], 0.5, 0.2, 0.9)
    col = g.mix(0.5, col, (0.34, 0.31, 0.26, 1.0))  # towards grey-beige lime
    col = damp(g, c, col, 0.25)
    finish(g, c, col, _val(g, a["rough"]), a["normal"], nstrength=0.5, rough_min=0.55, rough_max=1.0)


WOOD_GRADES = {
    # name: (tint multiply colour, saturation, value)
    "M_timber": ((1.0, 0.86, 0.70), 1.15, 0.80),
    "M_timber_weathered": ((0.98, 0.97, 0.95), 0.45, 1.25),
    "M_roof_shingle": ((0.98, 0.96, 0.92), 0.55, 1.15),
    "M_roof_shake": ((1.0, 0.94, 0.86), 0.75, 0.92),
}


def mat_wood(mat, mossy):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "wood")
    tint, s, v = WOOD_GRADES[mat.name]
    col = g.mix(1.0, a["color"], tint + (1.0,), blend="MULTIPLY")
    col = g.hsv(col, 0.5, s, v)
    col = jitter(g, c, col, amount=0.09)
    col, rough = wear(g, c, col, _val(g, a["rough"]), light=0.2, rough_add=0.1, desat=0.25)
    col = damp(g, c, col, 0.3)
    normal = a["normal"]
    if mossy:
        col, rough, normal = moss_layer(g, c, col, rough, normal, gain=6.5, lo=0.32, hi=0.62)
    finish(g, c, col, rough, normal, nstrength=0.7)


def mat_thatch(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "thatch")
    col = g.mix(1.0, a["color"], (1.35, 1.12, 0.78, 1.0), blend="MULTIPLY")
    col = g.hsv(col, 0.5, 1.05, 0.95)
    col = jitter(g, c, col, amount=0.07)
    col, rough = wear(g, c, col, _val(g, a["rough"]), light=0.12, rough_add=0.05, desat=0.3)
    col = damp(g, c, col, 0.3)
    col, rough, normal = moss_layer(g, c, col, rough, a["normal"], gain=5.5, lo=0.3, hi=0.8)
    finish(g, c, col, rough, normal, nstrength=0.9)


def mat_iron(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "rust")
    col = g.mix(0.6, a["color"], (0.045, 0.042, 0.04, 1.0))  # darken towards wrought iron
    col = jitter(g, c, col, amount=0.06)
    rough = _val(g, a["rough"])
    # rusty (saturated, bright) areas non-metallic, dark areas metallic
    met = g.maprange(_val(g, a["color"]), 0.05, 0.25, 0.75, 0.1)
    finish(g, c, col, rough, a["normal"], nstrength=0.6, metallic=met, rough_min=0.35, rough_max=0.95)


def mat_lead(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "dirtymetal")
    base = (0.20, 0.215, 0.24, 1.0)  # desaturated blue-grey
    col = jitter(g, c, g.mix(0.0, base, base), amount=0.05, hue=0.0)
    grime = g.math("MULTIPLY", a["mask"], 2.5, clamp=True)
    col = g.mix(grime, col, (0.12, 0.12, 0.12, 1.0))
    col, rough = wear(g, c, col, a["rough"], light=0.1, rough_add=0.1)
    finish(g, c, col, rough, None, metallic=0.2, rough_min=0.7, rough_max=0.95)


def mat_moss(mat, earth=False):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "moss")
    col = a["color"]
    if earth:
        col = g.hsv(col, 0.5, 0.55, 0.45)
    col = jitter(g, c, col, amount=0.06)
    finish(g, c, col, a["rough"], a["normal"], nstrength=0.8, rough_min=0.5, rough_max=1.0)


def mat_daub(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "plaster")
    # pinkish plaster -> cream hand-applied daub
    col = g.mix(1.0, a["color"], (1.12, 1.08, 0.92, 1.0), blend="MULTIPLY")
    col = g.hsv(col, 0.5, 0.9, 0.92)
    col = jitter(g, c, col, amount=0.06, hue=0.006)
    # high wear (broken patch edges): darker, warmer, towards earth
    earthy = g.mix(0.45, g.hsv(col, 0.49, 1.25, 0.7), (0.36, 0.27, 0.18, 1.0))
    edge = g.maprange(c["G"], 0.35, 0.8, interp="SMOOTHSTEP")
    col = g.mix(edge, col, earthy)
    col = damp(g, c, col, 0.3)
    finish(g, c, col, a["rough"], a["normal"], nstrength=0.6, rough_min=0.6, rough_max=1.0)


def mat_wattle(mat):
    # no texture downloaded: plain brown willow with per-rod jitter
    g = G(mat)
    c = setup_common(g)
    willow = (0.17, 0.105, 0.055, 1.0)
    col = jitter(g, c, g.mix(0.0, willow, willow), amount=0.15, hue=0.02)
    col, rough = wear(g, c, col, 0.65, light=0.1, rough_add=0.1, desat=0.1)
    finish(g, c, col, rough, None)


BUILDERS = {
    "M_stone": lambda m: mat_stone(m),
    "M_rubble": lambda m: mat_stone(m),
    "M_stone_dressed": lambda m: mat_stone(m, dressed=True, mossy=True, moss_gain=2.0),
    "M_mortar": mat_mortar,
    "M_daub": mat_daub,
    "M_wattle": mat_wattle,
    "M_timber": lambda m: mat_wood(m, mossy=False),
    "M_timber_weathered": lambda m: mat_wood(m, mossy=False),
    "M_roof_shingle": lambda m: mat_wood(m, mossy=True),
    "M_roof_shake": lambda m: mat_wood(m, mossy=True),
    "M_thatch": mat_thatch,
    "M_iron": mat_iron,
    "M_lead": mat_lead,
    "M_earth": lambda m: mat_moss(m, earth=True),
    "M_moss": lambda m: mat_moss(m),
}

# bounds of the building (before adding ground)
mesh_objs = [o for o in scene.objects if o.type == "MESH"]


def world_bounds(objs):
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objs:
        for co in o.bound_box:
            w = o.matrix_world @ Vector(co)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


# --------------------------------------------------------------------------- hide helpers
HELPER_KEYS = ("scale_fig", "figure", "helper", "human", "proxy", "dummy", "measure", "ref_", "gizmo")
hidden = []
for o in scene.objects:
    n = o.name.lower()
    in_decal = any(c.name.upper().startswith("DECAL_ANCHOR") for c in o.users_collection)
    if o.type != "MESH" or in_decal or any(k in n for k in HELPER_KEYS):
        if o.type in {"CAMERA", "LIGHT"}:
            continue
        o.hide_render = True
        hidden.append(o.name)
for c in bpy.data.collections:
    if c.name.upper().startswith("DECAL_ANCHOR") or any(k in c.name.lower() for k in ("helper", "scale_fig", "figure")):
        c.hide_render = True
build_objs = [o for o in mesh_objs if not o.hide_render]
print("hidden objects:", len(hidden), [h for h in hidden if not h.startswith("DA_")])
BMIN, BMAX = world_bounds(build_objs)
print("building bounds", tuple(round(v, 2) for v in BMIN), tuple(round(v, 2) for v in BMAX))

done = []
for m in bpy.data.materials:
    if m.name in BUILDERS:
        BUILDERS[m.name](m)
        done.append(m.name)
print("rebuilt palette materials:", done)
unknown = sorted({s.material.name for o in build_objs for s in o.material_slots if s.material and s.material.name not in BUILDERS})
if unknown:
    print("WARNING non-palette materials left untouched:", unknown)

# --------------------------------------------------------------------------- lighting / world
SUN_ELEV = math.radians(24.0)
SUN_AZ_DIR = Vector((0.72, -0.69, 0.0)).normalized()  # sun stands to the front-right (-Y side, +X)
sun_vec = Vector((SUN_AZ_DIR.x * math.cos(SUN_ELEV), SUN_AZ_DIR.y * math.cos(SUN_ELEV), math.sin(SUN_ELEV)))

sun_data = bpy.data.lights.new("LD_sun", "SUN")
sun_data.energy = 6.0
sun_data.color = (1.0, 0.72, 0.46)
sun_data.angle = math.radians(1.2)
sun = bpy.data.objects.new("LD_sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = sun_vec.to_track_quat("Z", "Y").to_euler()

world = bpy.data.worlds.new("LD_world")
scene.world = world
if world.node_tree is None:
    world.use_nodes = True
wn = world.node_tree
wn.nodes.clear()
sky = wn.nodes.new("ShaderNodeTexSky")
for t in ("MULTIPLE_SCATTERING", "NISHITA", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
    try:
        sky.sky_type = t
        break
    except TypeError:
        continue
for attr, val in (("sun_disc", False), ("sun_elevation", SUN_ELEV), ("altitude", 300.0),
                  ("air_density", 1.0), ("dust_density", 2.5), ("aerosol_density", 2.5), ("ozone_density", 1.0),
                  ("sun_rotation", math.atan2(SUN_AZ_DIR.x, SUN_AZ_DIR.y))):
    try:
        setattr(sky, attr, val)
    except (AttributeError, TypeError):
        pass
print("sky type", sky.sky_type)
bg = wn.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.1
wout = wn.nodes.new("ShaderNodeOutputWorld")
wn.links.new(sky.outputs["Color"], bg.inputs["Color"])
wn.links.new(bg.outputs["Background"], wout.inputs["Surface"])

# ground plane: neutral earthy grey-brown with a little procedural break-up
gm = bpy.data.meshes.new("LD_ground")
S = 300.0
gz = BMIN.z - 0.01
gm.from_pydata([(-S, -S, gz), (S, -S, gz), (S, S, gz), (-S, S, gz)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new("LD_ground", gm)
scene.collection.objects.link(ground)
gmat = bpy.data.materials.new("LD_ground")
gmat.use_nodes = True
gnt = gmat.node_tree
gnt.nodes.clear()
gp = gnt.nodes.new("ShaderNodeBsdfPrincipled")
go = gnt.nodes.new("ShaderNodeOutputMaterial")
gnt.links.new(gp.outputs["BSDF"], go.inputs["Surface"])
noise = gnt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 0.6
noise.inputs["Detail"].default_value = 6.0
cr = gnt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.085, 0.07, 0.052, 1.0)
cr.color_ramp.elements[1].color = (0.15, 0.125, 0.095, 1.0)
gnt.links.new(noise.outputs["Fac"], cr.inputs["Fac"])
gnt.links.new(cr.outputs["Color"], gp.inputs["Base Color"])
gp.inputs["Roughness"].default_value = 0.92
ground.data.materials.append(gmat)

# --------------------------------------------------------------------------- render settings
scene.render.engine = "CYCLES"
try:
    if args.cpu:
        raise RuntimeError("--cpu requested")
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
    print("devices", [(d.name, d.type, d.use) for d in prefs.devices])
except Exception as e:  # noqa
    print("GPU setup skipped/failed, rendering on CPU:", e)
    scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = "OPTIX"
except TypeError:
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.max_bounces = 8
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = args.pct
scene.render.film_transparent = False
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scene.view_settings.exposure = 0.0

# --------------------------------------------------------------------------- cameras
SENSOR = 36.0


def place_look(name, pos, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 2000.0
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)
    pos = Vector(pos)
    cam.location = pos
    cam.rotation_euler = (Vector(target) - pos).to_track_quat("-Z", "Y").to_euler()
    return cam


def place_fit(name, horiz_dir, elev_deg, lens, margin=0.08, target=None, bounds=None):
    """Camera looking along -dir (dir points from target to camera), distance fitted to the bounds."""
    mn, mx = bounds or (BMIN, BMAX)
    tgt = Vector(target) if target else (mn + mx) * 0.5
    e = math.radians(elev_deg)
    hd = Vector((horiz_dir[0], horiz_dir[1], 0.0)).normalized()
    d = Vector((hd.x * math.cos(e), hd.y * math.cos(e), math.sin(e)))
    rot = (-d).to_track_quat("-Z", "Y")
    rm = rot.to_matrix()
    th = math.tan(math.atan(SENSOR / 2 / lens)) * (1 - margin)
    tv = math.tan(math.atan(SENSOR * 9 / 16 / 2 / lens)) * (1 - margin)
    if bounds is None:  # per-object boxes are much tighter than the global box
        corners = [o.matrix_world @ Vector(co) for o in build_objs for co in o.bound_box]
    else:
        corners = [Vector((x, y, z)) for x in (mn.x, mx.x) for y in (mn.y, mx.y) for z in (mn.z, mx.z)]
    lo, hi = 1.0, 500.0
    for _ in range(60):
        dist = (lo + hi) / 2
        pos = tgt + d * dist
        ok = True
        for p in corners:
            q = rm.transposed() @ (p - pos)
            if q.z >= -0.1 or abs(q.x / -q.z) > th or abs(q.y / -q.z) > tv:
                ok = False
                break
        if ok:
            hi = dist
        else:
            lo = dist
    return place_look(name, tgt + d * hi, tgt, lens)


def find_door():
    """Main door = door leaf on the most -Y side (brief: doors face -Y); the opening centre comes
    from a door frame / surround if there is one (the leaf may be modelled swung open)."""
    def pick(keys, skip=()):
        c = [o for o in build_objs if any(k in o.name.lower() for k in keys) and not any(k in o.name.lower() for k in skip)]
        return min(c, key=lambda o: world_bounds([o])[0].y) if c else None
    leaf = pick(("door_leaf",)) or pick(("door",), ("iron", "nail", "hinge", "pintle", "bolt", "step", "frame", "surround", "backing")) or pick(("thresh",))
    if leaf is None:
        return None
    opening = pick(("door_frame", "door_surround")) or leaf
    lmn, lmx = world_bounds([leaf])
    omn, omx = world_bounds([opening])
    centre = Vector((((omn + omx) * 0.5).x, ((lmn + lmx) * 0.5).y, ((lmn + lmx) * 0.5).z))
    return leaf.name, centre, Vector((0, min(lmn.y, omn.y), 0)), lmx


def find_daub_patch():
    """Centre of the broken-daub patch (daub corners with high Mask G) nearest the front (-Y)."""
    pts = []
    for o in build_objs:
        if "interior" in o.name.lower() or not any(s.material and s.material.name == "M_daub" for s in o.material_slots):
            continue
        me = o.data
        if "Mask" not in me.color_attributes:
            continue
        att = me.color_attributes["Mask"]
        for li, lp in enumerate(me.loops):
            if att.data[li].color[1] > 0.5:
                pts.append(o.matrix_world @ me.vertices[lp.vertex_index].co)
    if not pts:
        return None
    seed = min(pts, key=lambda p: p.y)
    near = [p for p in pts if (p - seed).length < 0.6]
    return sum(near, Vector()) / len(near)

def bounds_of_material(matname):
    objs = [o for o in build_objs if any(s.material and s.material.name == matname for s in o.material_slots)]
    return world_bounds(objs) if objs else None


SHOTS = {}
door = find_door()
print("door:", door[0] if door else None, tuple(round(v, 2) for v in door[1]) if door else None)

SHOTS["hero"] = lambda: place_fit("CAM_hero", (-0.55, -0.84), 10.0, 35.0, margin=0.07)
SHOTS["front"] = lambda: place_fit("CAM_front", (0.0, -1.0), 5.0, 40.0, margin=0.06)
if door:
    dc = door[1]
    SHOTS["entrance_closeup"] = lambda: place_look("CAM_entrance_closeup", (dc.x + 0.9, door[2].y - 4.5, 1.7),
                                                   (dc.x, dc.y, 1.35), 28.0)

if NAME == "hilltop_keep":
    SHOTS["roof_detail"] = lambda: place_look("CAM_roof_detail", (-0.8, -10.5, 8.6), (-4.6, 1.2, 4.9), 40.0)
    SHOTS["thatch_closeup"] = lambda: place_look("CAM_thatch_closeup", (-11.2, -3.4, 2.7), (-7.6, 0.8, 3.7), 35.0)
elif NAME == "tower_windmill":
    def _wm_roof():
        mn, mx = BMIN, BMAX
        sb = bounds_of_material("M_roof_shingle") or (mn, mx)
        c = (sb[0] + sb[1]) * 0.5
        c.z = sb[0].z + 0.3 * (sb[1].z - sb[0].z)
        r = max(sb[1].x - sb[0].x, sb[1].y - sb[0].y)
        # from behind/right so the sail wheel on the -Y side does not block the cap
        pos = c + Vector((0.75, 0.55, 0.35)).normalized() * (r * 1.6 + 2.5)
        return place_look("CAM_roof_detail", pos, c, 45.0)
    SHOTS["roof_detail"] = _wm_roof
elif NAME == "wattle_roundhut":
    def _hut_wall():
        tgt = find_daub_patch()
        if tgt is None:
            db = bounds_of_material("M_daub") or (BMIN, BMAX)
            tgt = (db[0] + db[1]) * 0.5
        print("daub patch centre", tuple(round(v, 2) for v in tgt))
        ctr = (BMIN + BMAX) * 0.5
        radial = Vector((tgt.x - ctr.x, tgt.y - ctr.y, 0.0)).normalized()
        side = Vector((-radial.y, radial.x, 0.0))
        tgt = tgt + Vector((0, 0, 0.35))
        pos = tgt + radial * 2.6 + side * 0.6
        pos.z = 1.5
        return place_look("CAM_wall_closeup", pos, tgt, 35.0)

    SHOTS["wall_closeup"] = _hut_wall

want = list(SHOTS) if args.shots == "all" else ([] if args.shots == "none" else args.shots.split(","))
cams = {}
for s in SHOTS:
    cams[s] = SHOTS[s]()
    print("camera", s, tuple(round(v, 2) for v in cams[s].location))
scene.camera = cams.get("hero") or next(iter(cams.values()))

os.makedirs(OUT, exist_ok=True)
if not args.no_save:
    blend_out = os.path.join(OUT, NAME + "_lookdev.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_out, relative_remap=True, copy=False)
    try:
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()
    except Exception as e:  # noqa
        print("relative paths failed:", e)
    print("saved", blend_out)

rdir = os.path.join(OUT, "renders", NAME)
os.makedirs(rdir, exist_ok=True)
for s in want:
    if s not in cams:
        print("no such shot", s)
        continue
    scene.camera = cams[s]
    scene.render.filepath = os.path.join(rdir, s + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
