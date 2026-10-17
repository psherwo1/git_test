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
    --look r1|r2         material grade (default r2).  r1 = the first look test (lookdev/renders/, 2026-10-16);
                         r2 = the producer's review tweaks (dressed stone, thatch, plaster, wattle bark, mill
                         blades, darker lead), see lookdev/renders_r2/NOTES.md
    --render-dir DIR     write the shots to DIR (default <output>/renders/<name>)
    --blend-out FILE     save the lookdev .blend as FILE (default <output>/<name>_lookdev.blend)
    (lookdev/scripts/run_r2.ps1 renders the r2 set for the five r2 buildings, at most 3 at once.)

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
ap.add_argument("--look", choices=("r1", "r2"), default="r2",
                help="material grade: r1 = the first look test (2026-10-16), r2 = with the producer's review tweaks")
ap.add_argument("--render-dir", default=None, help="write the shots here (default <out>/renders/<name>)")
ap.add_argument("--blend-out", default=None, help="save the lookdev .blend here (default <out>/<name>_lookdev.blend)")
args = ap.parse_args(argv)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.abspath(args.textures or os.path.join(SCRIPT_DIR, "..", "textures"))
OUT = os.path.abspath(args.out)
LOOK = args.look
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
# r2 wattle bark.  The shortlist's willow bark (Poly Haven bark_willow_02) has not been downloaded yet; once its
# images are extracted to textures/bark_willow_02_2k.blend/textures/ the script uses them automatically.  Until
# then the bark is a PROXY: the rough_wood images, compressed round the rod and graded to grey-brown willow.
_BARK_DIR = "bark_willow_02_2k.blend/textures/"
if os.path.isfile(os.path.join(TEX, _BARK_DIR, "bark_willow_02_diff_2k.jpg")):
    TEXSETS["bark"] = dict(size=1.0, color=_BARK_DIR + "bark_willow_02_diff_2k.jpg",
                           rough=_BARK_DIR + "bark_willow_02_rough_2k.jpg",
                           normal=_BARK_DIR + "bark_willow_02_nor_gl_2k.exr", proxy=False)
else:
    TEXSETS["bark"] = dict(TEXSETS["wood"], proxy=True)

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


def moss_layer(g, ctx, color, rough, normal, gain=4.0, lo=0.35, hi=0.65, extra=None, hue=0.5):
    """Blend nordic moss on top: factor from Mask B x up-facing, broken up by the moss height.
    extra (r2): an additional factor socket, e.g. broad world-space moss patches."""
    m = sample(g, ctx, "moss", per_piece=False)
    f = g.math("MULTIPLY", ctx["B"], ctx["up"])
    hgt = g.math("SUBTRACT", g.out(_bw(g, m["height"]), "Val"), 0.5)
    f = g.math("MULTIPLY_ADD", f, gain, g.math("MULTIPLY", hgt, 0.6))
    if extra is not None:
        f = g.math("ADD", f, extra)
    fac = g.maprange(f, lo, hi, interp="SMOOTHSTEP")
    mcol = g.hsv(m["color"], hue, 1.05, 0.95)
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
    if LOOK == "r2":
        col = obj_darken(g, col)
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
    # desaturated blue-grey; r2 darker: in the r2 renders the r1 value read near-white against the olive thatch and
    # mossy shingles (keep wing flashing, hut / v4 cap collars)
    r1 = LOOK == "r1"
    base = (0.20, 0.215, 0.24, 1.0) if r1 else (0.115, 0.122, 0.135, 1.0)
    col = jitter(g, c, g.mix(0.0, base, base), amount=0.05, hue=0.0)
    grime = g.math("MULTIPLY", a["mask"], 2.5, clamp=True)
    col = g.mix(grime, col, (0.12, 0.12, 0.12, 1.0) if r1 else (0.065, 0.065, 0.065, 1.0))
    col, rough = wear(g, c, col, a["rough"], light=0.1, rough_add=0.1)
    normal = None
    if not r1:
        col, rough, normal = lead_grime(g, col, rough)
    finish(g, c, col, rough, normal, nstrength=0.5, metallic=0.2, rough_min=0.7, rough_max=0.95)


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


# --------------------------------------------------------------------------- r2 grade
# The producer's review of the first look test (lookdev/renders/, 2026-10-16):
#   dressed stone 20-30 % less bright (the lichen blew out); thatch more olive and mossy (ref2), less golden;
#   plaster tile half the size with a lower normal strength (the trowel swirls read as fish scales);
#   wattle with a willow bark texture instead of a flat colour; windmill fan blades less pale.
DRESSED_VALUE_R1, DRESSED_VALUE_R2 = 1.15, 0.805  # HSV value on the softened lichen_rock: -30 % albedo
OBJECT_DARKEN = {  # object-name suffix -> 'lookdev_darken' (r2); UE: a per-mesh material-instance scalar
    "_wheel_blades": 0.45,
}
# The client's mitigation for the tiered hall (accepted at round 7, 2026-10-17): the sunlit turret lead aprons read as
# a pale sawtooth band in the junction test, so they get darker, grimier lead with a hammered-sheet normal.
OBJECT_GRIME = {  # object-name suffix -> 'lookdev_grime' (r2, M_lead only); UE: a per-mesh material-instance scalar
    "HALL_skirt1_tur_e_flashing": 1.0,
    "HALL_skirt1_tur_nw_flashing": 1.0,
    "HALL_skirt1_tur_e_flashing_cheek": 1.0,
    "HALL_skirt1_tur_nw_flashing_cheek": 1.0,
    # the hall's other roof-into-body flashings, so the darker turret aprons do not sit next to pale lead bands
    "HALL_skirt1_drum_flashing": 1.0,
    "HALL_skirt2_lantern_flashing": 1.0,
    # the harbour house's roof-to-tower abutment flashings (client, 2026-10-17: the same darker lead as the hall)
    "HARB_roof_wall_abutment": 1.0,
    "HARB_wing_roof_wing_abutment": 1.0,
}


def obj_darken(g, col):
    """Per-object darkening from the object's custom property 'lookdev_darken' (absent = 0 = unchanged):
    value x (1 - d), saturation x (1 - 0.3 d)."""
    n = g.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="lookdev_darken")
    d = g.out(n, "Fac")
    v = g.math("SUBTRACT", 1.0, d)
    s = g.math("MULTIPLY_ADD", d, -0.3, 1.0)
    return g.hsv(col, 0.5, s, v)


def lead_grime(g, col, rough):
    """Per-object lead grime from the object's custom property 'lookdev_grime' (absent = 0 = unchanged): value
    x (1 - 0.4 k), dark run-off streaks (object-space noise stretched along Z), rougher, and a hammered-sheet normal
    (a tangent-space colour nudged off flat by noise) so the sheet no longer reads as one pale flat band."""
    k = g.out(g.node("ShaderNodeAttribute", attribute_type="OBJECT", attribute_name="lookdev_grime"), "Fac")
    col = g.hsv(col, 0.5, g.math("MULTIPLY_ADD", k, -0.3, 1.0), g.math("MULTIPLY_ADD", k, -0.4, 1.0))
    tc = g.node("ShaderNodeTexCoord")
    st = g.node("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 6.0
    st.inputs["Detail"].default_value = 6.0
    g.link(g.vmath("MULTIPLY", tc.outputs["Object"], (1.0, 1.0, 0.25)), st.inputs["Vector"])
    streak = g.math("MULTIPLY", g.maprange(g.out(st, "Fac"), 0.45, 0.7, interp="SMOOTHSTEP"), k)
    col = g.mix(g.math("MULTIPLY", streak, 0.8), col, (0.035, 0.035, 0.033, 1.0))
    rough = g.math("MULTIPLY_ADD", streak, 0.1, _val(g, rough) if rough.type == "RGBA" else rough, clamp=True)
    hm = g.node("ShaderNodeTexNoise")
    hm.inputs["Scale"].default_value = 28.0
    hm.inputs["Detail"].default_value = 3.0
    g.link(tc.outputs["Object"], hm.inputs["Vector"])
    normal = g.mix(g.math("MULTIPLY", k, 0.25), (0.5, 0.5, 1.0, 1.0), g.out(hm, "Color"))
    return col, rough, normal


def world_noise(g, scale, lo, hi, amount):
    """Low-frequency patch factor (0..amount) from object-space noise (buildings sit at the origin with identity
    transforms, so object space = world space; UE: a world-aligned noise texture)."""
    tc = g.node("ShaderNodeTexCoord")
    n = g.node("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 4.0
    g.link(tc.outputs["Object"], n.inputs["Vector"])
    return g.maprange(g.out(n, "Fac"), lo, hi, 0.0, amount, interp="SMOOTHSTEP")


def mat_stone_dressed_r2(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "lichenrock")
    color = g.hsv(soften(g, a["color"], -0.3), 0.5, 0.6, DRESSED_VALUE_R2)  # r1: value 1.15
    # cap the white lichen splotches (partial per-channel min against a mid grey)
    color = g.mix(0.75, color, (0.21, 0.205, 0.195, 1.0), blend="DARKEN")
    rough, normal = _val(g, a["rough"]), a["normal"]
    color = jitter(g, c, color)
    color, rough = wear(g, c, color, rough, light=0.08, rough_add=0.08)  # r1 light 0.12
    color = damp(g, c, color)
    color, rough, normal = moss_layer(g, c, color, rough, normal, gain=2.0, lo=0.4, hi=0.7)
    finish(g, c, color, rough, normal, nstrength=0.8)


def mat_thatch_r2(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "thatch")
    # r1 multiplied by (1.35, 1.12, 0.78), a golden straw; r2 grades the dark reed towards olive
    col = g.mix(1.0, a["color"], (0.95, 1.05, 0.55, 1.0), blend="MULTIPLY")
    col = g.hsv(col, 0.5, 0.85, 0.72)
    col = jitter(g, c, col, amount=0.07)
    col, rough = wear(g, c, col, _val(g, a["rough"]), light=0.08, rough_add=0.05, desat=0.3)
    # olive algae film over the whole roof (ref2), stronger on up-facing slopes
    film = g.math("MULTIPLY_ADD", c["up"], 0.15, 0.2)
    col = g.mix(film, col, (0.085, 0.085, 0.025, 1.0))
    col = damp(g, c, col, 0.3)
    # moss: Mask B x up as before, plus broad world-space patches; more coverage than r1 (gain 5.5, lo 0.3)
    patches = world_noise(g, 0.45, 0.45, 0.62, 0.7)
    col, rough, normal = moss_layer(g, c, col, rough, a["normal"], gain=7.0, lo=0.25, hi=0.75, extra=patches,
                                         hue=0.525)  # slightly greener moss than r1
    finish(g, c, col, rough, normal, nstrength=0.9)


def mat_daub_r2(mat):
    g = G(mat)
    c = setup_common(g)
    a = sample(g, c, "plaster", size_mult=0.5)  # r1: 2 m tile -> 1 m, trowel swirls half the size
    # break the regular rows of swirls (they still read as scales in skylit shade, v4 wall_closeup): blend in a
    # second, offset sample at a non-commensurate 0.74 m tile through low-frequency world-space noise
    b = sample(g, c, "plaster", size_mult=0.37, extra_offset=(0.31, 0.57, 0.0))
    f = world_noise(g, 1.3, 0.42, 0.58, 1.0)
    a = dict(color=g.mix(f, a["color"], b["color"]), rough=g.mix(f, a["rough"], b["rough"]),
             normal=g.mix(f, a["normal"], b["normal"]))
    # also halve the contrast of the dark trowel-stroke lines in the albedo (towards the image mean)
    col = g.mix(0.5, a["color"], (0.379, 0.281, 0.21, 1.0))
    col = g.mix(1.0, col, (1.12, 1.08, 0.92, 1.0), blend="MULTIPLY")
    col = g.hsv(col, 0.5, 0.9, 0.92)
    col = jitter(g, c, col, amount=0.06, hue=0.006)
    earthy = g.mix(0.45, g.hsv(col, 0.49, 1.25, 0.7), (0.36, 0.27, 0.18, 1.0))
    edge = g.maprange(c["G"], 0.35, 0.8, interp="SMOOTHSTEP")
    col = g.mix(edge, col, earthy)
    col = damp(g, c, col, 0.3)
    finish(g, c, col, a["rough"], a["normal"], nstrength=0.3, rough_min=0.6, rough_max=1.0)  # r1 normal 0.6


# wattle rod UVs (kit rods/stakes): U wraps once round the rod, V runs along it at ~11 UV units per metre
BARK_UV_SCALE = (0.30, 0.36, 1.0)  # one bark tile ~ 0.3 x the circumference, ~0.25 m along the rod
WILLOW_TINT = (0.95, 0.75, 0.50)   # rough_wood (linear mean ~0.145, 0.122, 0.096) -> grey-brown willow bark


def mat_wattle_r2(mat):
    g = G(mat)
    c = setup_common(g)
    ts = TEXSETS["bark"]
    vec = g.vmath("MULTIPLY_ADD", c["R"], PIECE_OFFSET, c["uv"])  # per-rod offset
    vec = g.vmath("MULTIPLY", vec, BARK_UV_SCALE)
    col = g.tex(ts["color"], vec, False).outputs["Color"]
    rough = _val(g, g.tex(ts["rough"], vec, True).outputs["Color"])
    normal = g.tex(ts["normal"], vec, True).outputs["Color"]
    if ts.get("proxy"):
        # board grain -> bark, graded to weathered grey-brown willow
        col = g.mix(1.0, col, WILLOW_TINT + (1.0,), blend="MULTIPLY")
        col = g.hsv(col, 0.5, 0.9, 1.0)
    col = jitter(g, c, col, amount=0.15, hue=0.02)  # per-rod variation as in r1
    col, rough = wear(g, c, col, rough, light=0.1, rough_add=0.1, desat=0.1)
    col = damp(g, c, col, 0.35)
    finish(g, c, col, rough, normal, nstrength=0.8, rough_min=0.45, rough_max=1.0)


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
if LOOK == "r2":
    BUILDERS.update({
        "M_stone_dressed": mat_stone_dressed_r2,
        "M_daub": mat_daub_r2,
        "M_wattle": mat_wattle_r2,
        "M_thatch": mat_thatch_r2,
    })
print("look", LOOK, "| bark", "PROXY (rough_wood)" if TEXSETS["bark"].get("proxy") else "bark_willow_02")

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

if LOOK == "r2":
    for o in build_objs:
        for suffix, d in OBJECT_DARKEN.items():
            if o.name.endswith(suffix):
                o["lookdev_darken"] = d
                print("lookdev_darken", o.name, d)
        for suffix, k in OBJECT_GRIME.items():
            if o.name.endswith(suffix):
                o["lookdev_grime"] = k
                print("lookdev_grime", o.name, k)

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
        # kit >= 1.10 buildings store their entrances on the scene (the door may be merged into a frames mesh)
        import json
        try:
            ents = json.loads(scene.get("kit_entrances") or "[]")
        except ValueError:
            ents = []
        ents = [e for e in ents if e.get("out", [0, -1, 0])[1] < -0.7] or ents
        if not ents:
            return None
        e = min(ents, key=lambda e: e["origin"][1])
        o = Vector(e["origin"])
        return "kit_entrances:" + e.get("name", "?"), Vector((o.x, o.y, e.get("head", 2.1) / 2)), Vector((0, o.y, 0)), None
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
elif NAME == "v3_longhouse_roundend":
    def _v3_thatch():
        tb = bounds_of_material("M_thatch") or (BMIN, BMAX)
        c = (tb[0] + tb[1]) * 0.5
        tgt = Vector((c.x, tb[0].y + 0.25 * (tb[1].y - tb[0].y), tb[0].z + 0.45 * (tb[1].z - tb[0].z)))
        pos = Vector((tgt.x - 0.35 * (tb[1].x - tb[0].x), tb[0].y - 5.0, 2.6))
        return place_look("CAM_thatch_closeup", pos, tgt, 35.0)
    SHOTS["thatch_closeup"] = _v3_thatch
elif NAME == "v4_mixed":
    def _v4_wall():
        tgt = find_daub_patch()
        if tgt is None:
            return None
        objs = [o for o in build_objs if o.name.startswith("V4H_")] or build_objs
        hmn, hmx = world_bounds(objs)
        ctr = (hmn + hmx) * 0.5
        radial = Vector((tgt.x - ctr.x, tgt.y - ctr.y, 0.0)).normalized()
        side = Vector((-radial.y, radial.x, 0.0))
        tgt = tgt + Vector((0, 0, 0.35))
        pos = tgt + radial * 2.6 + side * 0.6
        pos.z = 1.5
        return place_look("CAM_wall_closeup", pos, tgt, 35.0)
    SHOTS["wall_closeup"] = _v4_wall

want = list(SHOTS) if args.shots == "all" else ([] if args.shots == "none" else args.shots.split(","))
cams = {}
for s in SHOTS:
    cam = SHOTS[s]()
    if cam is None:
        print("camera", s, "skipped (no target)")
        continue
    cams[s] = cam
    print("camera", s, tuple(round(v, 2) for v in cams[s].location))
scene.camera = cams.get("hero") or next(iter(cams.values()))

os.makedirs(OUT, exist_ok=True)
if not args.no_save:
    blend_out = os.path.abspath(args.blend_out) if args.blend_out else os.path.join(OUT, NAME + "_lookdev.blend")
    os.makedirs(os.path.dirname(blend_out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_out, relative_remap=True, copy=False)
    try:
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()
    except Exception as e:  # noqa
        print("relative paths failed:", e)
    print("saved", blend_out)

rdir = os.path.abspath(args.render_dir) if args.render_dir else os.path.join(OUT, "renders", NAME)
os.makedirs(rdir, exist_ok=True)
for s in want:
    if s not in cams:
        print("no such shot", s)
        continue
    scene.camera = cams[s]
    scene.render.filepath = os.path.join(rdir, s + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
