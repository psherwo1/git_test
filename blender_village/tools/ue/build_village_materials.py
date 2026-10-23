"""Builds the village master material + 15 material instances in Unreal Engine 5 (tested on UE 5.8).

Run in the editor:  Tools > Execute Python Script > this file   (Python Editor Script Plugin must be enabled)
Run headless:       UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="<this file>" -unattended
It must sit next to import_into_unreal.py, Textures/ and textures_manifest.json (the pack folder, export/ue_texture_pack),
or live in tools/ue of the repo, or set VILLAGE_PACK_DIR to the pack folder.

Steps: (a) import the textures (import_into_unreal.import_textures; skipped for textures already imported),
(b) /Game/Village/Materials/M_Village_Master, (c) MI_<slot> for the 15 palette slots, (d) self-check and log summary.
Re-running replaces the master and the MIs (textures stay unless VILLAGE_REIMPORT=1).

The master ports lookdev/scripts/apply_lookdev.py (r2 look) as HLSL Custom nodes + parameters; see README_materials.md
for what is simplified.  The mesh must carry the vertex colour 'Mask' (R per-piece random, G wear, B moss/damp).
"""
import importlib.util
import os

import unreal

DEST_M = "/Game/Village/Materials"
DEST_T = "/Game/Village/Textures"
MASTER = "M_Village_Master"
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

# --------------------------------------------------------------------------------------------- locate pack
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()


def _load_importer():
    spec = importlib.util.spec_from_file_location("village_import", os.path.join(HERE, "import_into_unreal.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # name != __main__, so its main() does not run
    return mod


IMP = _load_importer()
PACK = IMP.find_pack_dir()
MAN = IMP.load_manifest(PACK)


def tile_scale(set_name, size_mult=1.0):
    """UV units (1 per metre) -> texture repeats: 1 / (real tile size in m * size_mult)."""
    return 1.0 / (MAN["sets"][set_name]["tile_m"] * size_mult)


# --------------------------------------------------------------------------------------------- parameters
# name: (default, group).  Scalars unless the default is a tuple (-> vector parameter, linear colour).
P = {
    # mapping
    "TileScale": (0.5, "Mapping"), "TileScaleB": (0.5, "Mapping"), "TileX": (1.0, "Mapping"), "TileY": (1.0, "Mapping"),
    "PieceOffset": (1.0, "Mapping"), "BOffsetX": (11.3, "Mapping"), "BOffsetY": (5.7, "Mapping"),
    "MossTile": (0.5, "Mapping"), "GrimeTile": (1.0, "Mapping"),
    "MaskGamma": (1.0, "Mask"), "MaskOverrideAmount": (0.0, "Mask"), "MaskOverride": ((0.5, 0.0, 0.0), "Mask"),
    # base sets
    "AOAmount": (0.6, "Base"), "SetBAmount": (0.0, "Base"), "SetBNoiseMode": (0.0, "Base"),
    "BNoiseScale": (1.3, "Base"), "BNoiseLo": (0.42, "Base"), "BNoiseHi": (0.58, "Base"),
    "A_Sat": (1.0, "Base"), "A_Val": (1.0, "Base"), "A_Cap": (0.0, "Base"),
    "B_Sat": (1.0, "Base"), "B_Val": (1.0, "Base"), "B_Cap": (0.0, "Base"),
    # colour
    "TintMultiply": ((1.0, 1.0, 1.0), "Colour"), "Sat": (1.0, "Colour"), "Val": (1.0, "Colour"),
    "FlattenAmount": (0.0, "Colour"), "FlattenColor": ((0.5, 0.5, 0.5), "Colour"),
    "ColorMixAmount": (0.0, "Colour"), "ColorMixColor": ((0.5, 0.5, 0.5), "Colour"),
    "FlatColorAmount": (0.0, "Colour"), "FlatColor": ((0.2, 0.2, 0.2), "Colour"),
    "GrimeAmount": (0.0, "Colour"), "GrimeColor": ((0.065, 0.065, 0.065), "Colour"),
    "FilmBase": (0.0, "Colour"), "FilmUp": (0.0, "Colour"), "FilmColor": ((0.085, 0.085, 0.025), "Colour"),
    "EdgeEarth": (0.0, "Colour"),
    "JitterVal": (0.08, "Piece jitter"), "JitterHue": (0.012, "Piece jitter"),
    # wear / damp
    "WearAmount": (1.0, "Wear"), "WearLight": (0.12, "Wear"), "WearRough": (0.08, "Wear"), "WearDesat": (0.15, "Wear"),
    "DampAmount": (0.35, "Damp"),
    # moss
    "MossAmount": (0.25, "Moss"), "MossGain": (3.5, "Moss"), "MossLo": (0.4, "Moss"), "MossHi": (0.7, "Moss"),
    "MossHue": (0.0, "Moss"), "MossHeightMean": (0.73, "Moss"), "MossHeightGain": (1.0, "Moss"),
    "UseWorldPatches": (0.0, "Moss"), "PatchScale": (0.45, "Moss"), "PatchLo": (0.45, "Moss"), "PatchHi": (0.62, "Moss"),
    "PatchAmount": (0.7, "Moss"),
    # surface
    "NormalStrength": (0.8, "Surface"), "RoughMin": (0.0, "Surface"), "RoughMax": (1.0, "Surface"),
    "RoughFromGrime": (0.0, "Surface"), "Metallic": (0.0, "Surface"), "MetalFromLuma": (0.0, "Surface"),
}

# texture parameters: name -> (default asset, sampler type)
ST = unreal.MaterialSamplerType
TEXPARAMS = {
    "A_BC": ("T_Village_RoughWood_BC", ST.SAMPLERTYPE_COLOR), "A_N": ("T_Village_RoughWood_N", ST.SAMPLERTYPE_NORMAL),
    "A_ORM": ("T_Village_RoughWood_ORM", ST.SAMPLERTYPE_MASKS),
    "B_BC": ("T_Village_LichenRock_BC", ST.SAMPLERTYPE_COLOR), "B_N": ("T_Village_LichenRock_N", ST.SAMPLERTYPE_NORMAL),
    "B_ORM": ("T_Village_LichenRock_ORM", ST.SAMPLERTYPE_MASKS),
    "Moss_BC": ("T_Village_NordicMoss_BC", ST.SAMPLERTYPE_COLOR), "Moss_N": ("T_Village_NordicMoss_N", ST.SAMPLERTYPE_NORMAL),
    "Moss_ORM": ("T_Village_NordicMoss_ORM", ST.SAMPLERTYPE_MASKS),
    "Grime_MR": ("T_Village_GrimeMask_MR", ST.SAMPLERTYPE_MASKS),
}


WIRING_ERRORS = []


def conn(src, src_pin, dst, dst_pin):
    ok = mel.connect_material_expressions(src, src_pin, dst, dst_pin)
    if not ok:
        WIRING_ERRORS.append((src.get_name(), src_pin, dst.get_name(), dst_pin))
        unreal.log_error(f"Village: connect failed {src.get_name()}.{src_pin!r} -> {dst.get_name()}.{dst_pin!r}")
    return ok


def connp(src, src_pin, prop):
    ok = mel.connect_material_property(src, src_pin, prop)
    if not ok:
        WIRING_ERRORS.append((src.get_name(), src_pin, str(prop), ""))
        unreal.log_error(f"Village: connect to material property {prop} failed")
    return ok


# --------------------------------------------------------------------------------------------- HLSL snippets
SV = "float3 {v} = lerp(dot({v},float3(0.2126,0.7152,0.0722)).xxx,{v},{s})*({val});"   # saturation / value
HUE = ("{{ float a_ = ({t})*6.2831853; float3 k_ = float3(0.57735,0.57735,0.57735);"
       " {v} = {v}*cos(a_) + cross(k_,{v})*sin(a_) + k_*dot(k_,{v})*(1.0-cos(a_)); }}")


def sv(v, s, val):
    return f"{v} = lerp(dot({v},float3(0.2126,0.7152,0.0722)).xxx,{v},{s})*({val});"


def hue(v, t):
    return HUE.format(v=v, t=t)


CODE_MASK = "return lerp(pow(saturate(VC), MaskGamma), MaskOverride, MaskOverrideAmount);"

CODE_UV = ("float2 p = UV + Mask.r*PieceOffset*float2(37.1,91.7) + Extra;"
           " return p*Scale*float2(TileX,TileY);")

CODE_UVM = "return UV*MossTile;"

CODE_UP = "return smoothstep(0.3, 0.8, N.z);"

CODE_NOISE = """float3 p = P*0.01*Scale;
float v = 0.0; float amp = 0.5; float tot = 0.0;
for (int o = 0; o < 4; o++) {
  float3 ii = floor(p); float3 ff = frac(p); ff = ff*ff*(3.0-2.0*ff);
  float c = 0.0;
  for (int k = 0; k < 8; k++) {
    float3 d = float3(k & 1, (k >> 1) & 1, (k >> 2) & 1);
    float3 w = lerp(1.0-ff, ff, d);
    c += w.x*w.y*w.z*frac(sin(dot(ii+d, float3(127.1,311.7,74.7)))*43758.5453);
  }
  v += c*amp; tot += amp; amp *= 0.5; p = p*2.03 + 17.1;
}
v = v/tot;
// widen the value-noise histogram towards Blender's noise (mean 0.5, wider spread)
v = saturate(0.5 + (v-0.5)*1.8);
return smoothstep(Lo, Hi, v)*Amount;"""

CODE_MOSSFAC = """float h = (MH - HMean)*HGain;
float f = Mask.b*Up*Gain + h*0.6 + Patch;
return smoothstep(Lo, Hi, f)*Amount;"""

CODE_COLOR = "\n".join([
    "float3 cap = float3(0.21,0.205,0.195);",
    "float3 a = ACol*lerp(1.0, AAO, AOAmount);",
    sv("a", "A_Sat", "A_Val"),
    "a = lerp(a, min(a, cap), 0.75*A_Cap);",
    "float3 b = BCol*lerp(1.0, BAO, AOAmount);",
    sv("b", "B_Sat", "B_Val"),
    "b = lerp(b, min(b, cap), 0.75*B_Cap);",
    "float3 col = lerp(a, b, MixB);",
    "col = lerp(col, FlatColor, FlatColorAmount);",
    "col = lerp(col, FlattenColor, FlattenAmount);",
    "col *= TintMultiply;",
    sv("col", "Sat", "Val"),
    "col = lerp(col, ColorMixColor, ColorMixAmount);",
    # per-piece jitter (Mask R): value +-JitterVal, hue +-JitterHue (turns)
    "float jv = Mask.r*2.0*JitterVal + 1.0 - JitterVal;",
    "float jh = (frac(Mask.r*13.73)*2.0-1.0)*JitterHue;",
    hue("col", "jh"),
    "col *= jv;",
    # lead grime
    "col = lerp(col, GrimeColor, saturate(GrimeMask*2.5)*GrimeAmount);",
    # wear (Mask G): lighter, greyer
    "float3 worn = col;",
    sv("worn", "(1.0-WearDesat)", "(1.0+WearLight)"),
    "col = lerp(col, worn, saturate(Mask.g*WearAmount));",
    # daub: broken patch edges (high wear) towards earth
    "float3 earthy = col;",
    hue("earthy", "-0.01"),
    sv("earthy", "1.25", "0.7"),
    "earthy = lerp(earthy, float3(0.36,0.27,0.18), 0.45);",
    "col = lerp(col, earthy, smoothstep(0.35,0.8,Mask.g)*EdgeEarth);",
    # thatch: olive algae film, stronger on up-facing slopes
    "col = lerp(col, FilmColor, saturate(FilmBase + Up*FilmUp));",
    # damp (Mask B on non-up-facing surfaces): darken
    "float fd = saturate(Mask.b*(1.0-Up)*DampAmount);",
    "col = lerp(col, col*float3(0.08,0.075,0.06), fd);",
    # moss layer
    "float3 m = MCol*lerp(1.0, MAO, AOAmount);",
    hue("m", "MossHue"),
    sv("m", "1.05", "0.95"),
    "col = lerp(col, m, MossFac);",
    "return col;",
])

CODE_ROUGH = """float r = lerp(ARough, BRough, MixB);
r = lerp(r, GrimeG, RoughFromGrime);
r = saturate(r + Mask.g*WearAmount*WearRough);
r = lerp(r, MRough*0.6 + 0.4, MossFac);
return lerp(RMin, RMax, saturate(r));"""

CODE_NORMAL = """float3 n = lerp(AN, BN, MixB);
n = lerp(n, MN, MossFac);
n.xy *= Strength;
return normalize(n);"""

CODE_METAL = """float l = dot(ACol, float3(0.2126,0.7152,0.0722));
float fromLuma = lerp(0.75, 0.1, saturate((l-0.05)/0.2));
return lerp(Metal, fromLuma, FromLuma);"""


# --------------------------------------------------------------------------------------------- graph builder
class Builder:
    def __init__(self, mat):
        self.mat = mat
        self.cache = {}
        self.y = 0

    def node(self, cls, x, y):
        return mel.create_material_expression(self.mat, cls, x, y)

    def param(self, name):
        if name in self.cache:
            return self.cache[name]
        default, group = P[name]
        i = len(self.cache)
        if isinstance(default, tuple):
            n = self.node(unreal.MaterialExpressionVectorParameter, -2600, i * 70)
            n.set_editor_property("default_value", unreal.LinearColor(default[0], default[1], default[2], 1.0))
        else:
            n = self.node(unreal.MaterialExpressionScalarParameter, -2600, i * 70)
            n.set_editor_property("default_value", float(default))
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("group", group)
        self.cache[name] = (n, "")
        return self.cache[name]

    def tex(self, name, uv):
        asset, stype = TEXPARAMS[name]
        key = "tex:" + name
        i = len(self.cache)
        n = self.node(unreal.MaterialExpressionTextureSampleParameter2D, -1500, i * 40 + 800)
        n.set_editor_property("parameter_name", name)
        n.set_editor_property("group", "Textures")
        n.set_editor_property("sampler_type", stype)
        n.set_editor_property("texture", EAL.load_asset(f"{DEST_T}/{asset}"))
        conn(uv[0], uv[1], n, "UVs")
        self.cache[key] = n
        return n

    def custom(self, desc, code, out_type, inputs, x, y):
        """inputs: {hlsl_name: (node, output_pin) or parameter name}"""
        n = self.node(unreal.MaterialExpressionCustom, x, y)
        cis = []
        for nm in inputs:
            ci = unreal.CustomInput()
            ci.set_editor_property("input_name", nm)
            cis.append(ci)
        n.set_editor_property("inputs", cis)
        n.set_editor_property("code", code)
        n.set_editor_property("description", desc)
        n.set_editor_property("output_type", out_type)
        for nm, src in inputs.items():
            if isinstance(src, str):
                src = self.param(src)
            conn(src[0], src[1], n, nm)
        return (n, "")


def build_master():
    path = f"{DEST_M}/{MASTER}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(MASTER, DEST_M, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    b = Builder(mat)
    F1, F2, F3 = (unreal.CustomMaterialOutputType.CMOT_FLOAT1, unreal.CustomMaterialOutputType.CMOT_FLOAT2,
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3)

    # geometry inputs
    vc = b.node(unreal.MaterialExpressionVertexColor, -3000, 0)
    tc = b.node(unreal.MaterialExpressionTextureCoordinate, -3000, 200)
    vn = b.node(unreal.MaterialExpressionVertexNormalWS, -3000, 400)
    wp = b.node(unreal.MaterialExpressionWorldPosition, -3000, 600)
    mask = b.custom("Mask (R piece, G wear, B moss/damp)", CODE_MASK, F3, {"VC": (vc, ""), "MaskGamma": "MaskGamma", "MaskOverride": "MaskOverride", "MaskOverrideAmount": "MaskOverrideAmount"}, -2800, 0)
    # extra UV offset for set B is a float2 built from two scalars
    off = b.node(unreal.MaterialExpressionAppendVector, -2800, 200)
    conn(*b.param("BOffsetX"), off, "A")
    conn(*b.param("BOffsetY"), off, "B")
    zero2 = b.node(unreal.MaterialExpressionConstant2Vector, -2800, 300)
    uvA = b.custom("UV set A", CODE_UV, F2, {"UV": (tc, ""), "Mask": mask, "PieceOffset": "PieceOffset", "Extra": (zero2, ""),
                                           "Scale": "TileScale", "TileX": "TileX", "TileY": "TileY"}, -2400, 0)
    uvB = b.custom("UV set B", CODE_UV, F2, {"UV": (tc, ""), "Mask": mask, "PieceOffset": "PieceOffset", "Extra": (off, ""),
                                           "Scale": "TileScaleB", "TileX": "TileX", "TileY": "TileY"}, -2400, 200)
    uvM = b.custom("UV moss", CODE_UVM, F2, {"UV": (tc, ""), "MossTile": "MossTile"}, -2400, 400)
    uvG = b.custom("UV grime", CODE_UV, F2, {"UV": (tc, ""), "Mask": mask, "PieceOffset": "PieceOffset", "Extra": (zero2, ""),
                                           "Scale": "GrimeTile", "TileX": "TileX", "TileY": "TileY"}, -2400, 600)
    tA = {k: b.tex("A_" + k, uvA) for k in ("BC", "N", "ORM")}
    tB = {k: b.tex("B_" + k, uvB) for k in ("BC", "N", "ORM")}
    tM = {k: b.tex("Moss_" + k, uvM) for k in ("BC", "N", "ORM")}
    tG = b.tex("Grime_MR", uvG)

    up = b.custom("Up-facing factor (world normal Z)", CODE_UP, F1, {"N": (vn, "")}, -1200, -300)
    # patch amount = PatchAmount * UseWorldPatches
    pa = b.node(unreal.MaterialExpressionMultiply, -1400, -150)
    conn(*b.param("PatchAmount"), pa, "A")
    conn(*b.param("UseWorldPatches"), pa, "B")
    patches = b.custom("World noise patches", CODE_NOISE, F1,
                       {"P": (wp, ""), "Scale": "PatchScale", "Lo": "PatchLo", "Hi": "PatchHi", "Amount": (pa, "")}, -1200, -150)
    one = b.node(unreal.MaterialExpressionConstant, -1400, -50)
    one.set_editor_property("r", 1.0)
    bn = b.custom("World noise blend A/B", CODE_NOISE, F1,
                  {"P": (wp, ""), "Scale": "BNoiseScale", "Lo": "BNoiseLo", "Hi": "BNoiseHi", "Amount": (one, "")}, -1200, 0)
    # MixB = SetBAmount * lerp(step(0.5, R), noise, SetBNoiseMode)
    mixb = b.custom("Set B blend factor",
                    "return SetBAmount*lerp(step(0.5, Mask.r), BNoise, NoiseMode);", F1,
                    {"Mask": mask, "BNoise": bn, "NoiseMode": "SetBNoiseMode", "SetBAmount": "SetBAmount"}, -1000, 0)
    mossfac = b.custom("Moss factor", CODE_MOSSFAC, F1,
                       {"Mask": mask, "Up": up, "MH": (tM["ORM"], "R"), "HMean": "MossHeightMean", "HGain": "MossHeightGain",
                        "Gain": "MossGain", "Patch": patches, "Lo": "MossLo", "Hi": "MossHi", "Amount": "MossAmount"}, -1000, 200)
    color = b.custom("Base colour", CODE_COLOR, F3, {
        "ACol": (tA["BC"], "RGB"), "AAO": (tA["ORM"], "R"), "BCol": (tB["BC"], "RGB"), "BAO": (tB["ORM"], "R"),
        "MCol": (tM["BC"], "RGB"), "MAO": (tM["ORM"], "R"), "MixB": mixb, "MossFac": mossfac, "Mask": mask, "Up": up,
        "GrimeMask": (tG, "R"), "AOAmount": "AOAmount", "A_Sat": "A_Sat", "A_Val": "A_Val", "A_Cap": "A_Cap",
        "B_Sat": "B_Sat", "B_Val": "B_Val", "B_Cap": "B_Cap", "FlatColor": "FlatColor", "FlatColorAmount": "FlatColorAmount",
        "FlattenColor": "FlattenColor", "FlattenAmount": "FlattenAmount", "TintMultiply": "TintMultiply", "Sat": "Sat",
        "Val": "Val", "ColorMixColor": "ColorMixColor", "ColorMixAmount": "ColorMixAmount", "JitterVal": "JitterVal",
        "JitterHue": "JitterHue", "GrimeColor": "GrimeColor", "GrimeAmount": "GrimeAmount", "WearDesat": "WearDesat",
        "WearLight": "WearLight", "WearAmount": "WearAmount", "EdgeEarth": "EdgeEarth", "FilmColor": "FilmColor",
        "FilmBase": "FilmBase", "FilmUp": "FilmUp", "DampAmount": "DampAmount", "MossHue": "MossHue"}, -600, 0)
    rough = b.custom("Roughness", CODE_ROUGH, F1, {
        "ARough": (tA["ORM"], "G"), "BRough": (tB["ORM"], "G"), "MRough": (tM["ORM"], "G"), "GrimeG": (tG, "G"),
        "MixB": mixb, "MossFac": mossfac, "Mask": mask, "RoughFromGrime": "RoughFromGrime", "WearAmount": "WearAmount",
        "WearRough": "WearRough", "RMin": "RoughMin", "RMax": "RoughMax"}, -600, 300)
    normal = b.custom("Normal", CODE_NORMAL, F3, {
        "AN": (tA["N"], "RGB"), "BN": (tB["N"], "RGB"), "MN": (tM["N"], "RGB"), "MixB": mixb, "MossFac": mossfac,
        "Strength": "NormalStrength"}, -600, 500)
    metal = b.custom("Metallic", CODE_METAL, F1, {
        "ACol": (tA["BC"], "RGB"), "Metal": "Metallic", "FromLuma": "MetalFromLuma"}, -600, 700)

    connp(color[0], "", unreal.MaterialProperty.MP_BASE_COLOR)
    connp(rough[0], "", unreal.MaterialProperty.MP_ROUGHNESS)
    connp(normal[0], "", unreal.MaterialProperty.MP_NORMAL)
    connp(metal[0], "", unreal.MaterialProperty.MP_METALLIC)
    # make sure every P entry exists as a parameter even if some are only read by MIs
    for name in P:
        b.param(name)
    mel.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    unreal.log(f"Village: master built with {len(b.cache)} nodes cached, {len(P)} parameters")
    return mat


# --------------------------------------------------------------------------------------------- material instances
def wood_slot(name, tint, sat, val, moss=0.0):
    p = dict(TileScale=tile_scale("RoughWood"), TintMultiply=tint, Sat=sat, Val=val, JitterVal=0.09,
             WearLight=0.2, WearRough=0.1, WearDesat=0.25, DampAmount=0.3, NormalStrength=0.7, MossAmount=moss)
    if moss:
        p.update(MossGain=6.5, MossLo=0.32, MossHi=0.62)
    return name, dict(A="RoughWood", B=None, p=p)


ROOF = MAN.get("roof_moss_scale", 0.25)
SLOTS = dict([
    ("M_stone", dict(A="RockWall", B="LichenRock", p=dict(
        TileScale=tile_scale("RockWall"), TileScaleB=tile_scale("LichenRock"), SetBAmount=1.0, B_Sat=0.6, B_Val=1.0,
        WearLight=0.12, WearRough=0.08, MossAmount=1.0, MossGain=3.5, MossLo=0.4, MossHi=0.7, NormalStrength=0.8))),
    ("M_rubble", dict(A="RockWall", B="LichenRock", p=dict(
        TileScale=tile_scale("RockWall"), TileScaleB=tile_scale("LichenRock"), SetBAmount=1.0, B_Sat=0.6, B_Val=1.0,
        WearLight=0.12, WearRough=0.08, MossAmount=1.0, MossGain=3.5, MossLo=0.4, MossHi=0.7, NormalStrength=0.8))),
    ("M_stone_dressed", dict(A="LichenRock", B=None, p=dict(
        TileScale=tile_scale("LichenRock"), A_Sat=0.6, A_Val=0.805, A_Cap=1.0, WearLight=0.08, WearRough=0.08,
        MossAmount=1.0, MossGain=2.0, MossLo=0.4, MossHi=0.7, NormalStrength=0.8))),
    ("M_mortar", dict(A="LichenRock", B=None, p=dict(
        TileScale=tile_scale("LichenRock", 0.4), PieceOffset=0.0, Sat=0.2, Val=0.9, ColorMixColor=(0.34, 0.31, 0.26),
        ColorMixAmount=0.5, JitterVal=0.0, JitterHue=0.0, WearAmount=0.0, DampAmount=0.25, MossAmount=0.0,
        NormalStrength=0.5, RoughMin=0.55, RoughMax=1.0))),
    ("M_daub", dict(A="ClayPlaster", B="ClayPlaster", p=dict(
        TileScale=tile_scale("ClayPlaster", 0.5), TileScaleB=tile_scale("ClayPlaster", 0.37), BOffsetX=0.31, BOffsetY=0.57,
        SetBAmount=1.0, SetBNoiseMode=1.0, BNoiseScale=1.3, BNoiseLo=0.42, BNoiseHi=0.58,
        FlattenAmount=0.5, FlattenColor=(0.379, 0.281, 0.21), TintMultiply=(1.12, 1.08, 0.92), Sat=0.9, Val=0.92,
        JitterVal=0.06, JitterHue=0.006, WearAmount=0.0, EdgeEarth=1.0, DampAmount=0.3, MossAmount=0.0,
        NormalStrength=0.3, RoughMin=0.6, RoughMax=1.0))),
    ("M_wattle", dict(A="RoughWood", B=None, p=dict(
        TileScale=1.0, TileX=0.30, TileY=0.36, TintMultiply=(0.95, 0.75, 0.50), Sat=0.9, Val=1.0, JitterVal=0.15,
        JitterHue=0.02, WearLight=0.1, WearRough=0.1, WearDesat=0.1, DampAmount=0.35, MossAmount=0.0,
        NormalStrength=0.8, RoughMin=0.45, RoughMax=1.0))),
    wood_slot("M_timber", (1.0, 0.86, 0.70), 1.15, 0.80),
    wood_slot("M_timber_weathered", (0.98, 0.97, 0.95), 0.45, 1.25),
    wood_slot("M_roof_shingle", (0.98, 0.96, 0.92), 0.55, 1.15, moss=ROOF),
    wood_slot("M_roof_shake", (1.0, 0.94, 0.86), 0.75, 0.92, moss=ROOF),
    ("M_thatch", dict(A="Thatch", B=None, p=dict(
        TileScale=tile_scale("Thatch"), TintMultiply=(1.06, 1.0, 0.70), Sat=0.8, Val=0.8, JitterVal=0.07,
        WearLight=0.08, WearRough=0.05, WearDesat=0.3, FilmBase=0.2 * ROOF, FilmUp=0.15 * ROOF,
        FilmColor=(0.085, 0.085, 0.025), DampAmount=0.3, UseWorldPatches=1.0, PatchScale=0.45, PatchLo=0.45,
        PatchHi=0.62, PatchAmount=0.7, MossAmount=ROOF, MossGain=7.0, MossLo=0.25, MossHi=0.75, MossHue=0.025,
        NormalStrength=0.9))),
    ("M_iron", dict(A="RustyMetal", B=None, p=dict(
        TileScale=tile_scale("RustyMetal"), ColorMixColor=(0.045, 0.042, 0.04), ColorMixAmount=0.6, JitterVal=0.06,
        WearAmount=0.0, DampAmount=0.0, MossAmount=0.0, NormalStrength=0.6, RoughMin=0.35, RoughMax=0.95,
        MetalFromLuma=1.0))),
    ("M_lead", dict(A="RoughWood", B=None, p=dict(     # textures unused: flat colour + grime mask (R darkening, G roughness)
        TileScale=tile_scale("RoughWood"), GrimeTile=1.0 / MAN["sets"]["GrimeMask"]["tile_m"],
        FlatColor=(0.115, 0.122, 0.135), FlatColorAmount=1.0, JitterVal=0.05, JitterHue=0.0, GrimeAmount=1.0,
        GrimeColor=(0.065, 0.065, 0.065), RoughFromGrime=1.0, WearLight=0.1, WearRough=0.1, DampAmount=0.0,
        MossAmount=0.0, NormalStrength=0.0, Metallic=0.2, RoughMin=0.7, RoughMax=0.95))),
    ("M_earth", dict(A="NordicMoss", B=None, p=dict(
        TileScale=tile_scale("NordicMoss"), Sat=0.55, Val=0.45, JitterVal=0.06, WearAmount=0.0, DampAmount=0.0,
        MossAmount=0.0, NormalStrength=0.8, RoughMin=0.5, RoughMax=1.0))),
    ("M_moss", dict(A="NordicMoss", B=None, p=dict(
        TileScale=tile_scale("NordicMoss"), JitterVal=0.06, WearAmount=0.0, DampAmount=0.0, MossAmount=0.0,
        NormalStrength=0.8, RoughMin=0.5, RoughMax=1.0))),
])


def build_instances(master):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for name, d in SLOTS.items():
        path = f"{DEST_M}/MI_{name}"
        if EAL.does_asset_exist(path):
            EAL.delete_asset(path)
        mi = tools.create_asset(f"MI_{name}", DEST_M, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, master)
        sets = {"A": d["A"], "B": d["B"] or d["A"], "Moss": "NordicMoss"}
        for pre, sname in sets.items():
            for suf in ("BC", "N", "ORM"):
                tex = EAL.load_asset(f"{DEST_T}/T_Village_{sname}_{suf}")
                mel.set_material_instance_texture_parameter_value(mi, f"{pre}_{suf}", tex)
        mel.set_material_instance_texture_parameter_value(mi, "Grime_MR", EAL.load_asset(f"{DEST_T}/T_Village_GrimeMask_MR"))
        for k, v in d["p"].items():
            if isinstance(P[k][0], tuple):
                mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
            else:
                mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
        mel.update_material_instance(mi)
        EAL.save_loaded_asset(mi)
        made.append(name)
    return made


# --------------------------------------------------------------------------------------------- self check
def verify(master):
    errors = 0
    try:
        st = mel.get_statistics(master)
        unreal.log(f"Village: master statistics: VS instr {st.num_vertex_shader_instructions}, PS instr "
                   f"{st.num_pixel_shader_instructions}, samplers {st.num_samplers}, "
                   f"vertex interp. {st.num_vertex_texture_samples}/{st.num_pixel_texture_samples} tex samples")
    except Exception as e:  # noqa
        unreal.log_warning(f"Village: get_statistics unavailable: {e}")
    try:
        names = [str(n) for n in mel.get_scalar_parameter_names(master)] + [str(n) for n in mel.get_vector_parameter_names(master)] \
            + [str(n) for n in mel.get_texture_parameter_names(master)]
        missing = [k for k in list(P) + list(TEXPARAMS) if k not in names]
        unreal.log(f"Village: master exposes {len(names)} parameters, missing: {missing}")
        errors += len(missing)
    except Exception as e:  # noqa
        unreal.log_warning(f"Village: parameter name listing failed: {e}")
    for name, d in SLOTS.items():
        mi = EAL.load_asset(f"{DEST_M}/MI_{name}")
        if not mi:
            unreal.log_error(f"Village: MI_{name} missing")
            errors += 1
            continue
        bad = []
        for k, v in d["p"].items():
            if isinstance(P[k][0], tuple):
                got = mel.get_material_instance_vector_parameter_value(mi, k)
                if max(abs(got.r - v[0]), abs(got.g - v[1]), abs(got.b - v[2])) > 1e-4:
                    bad.append((k, got, v))
            else:
                got = mel.get_material_instance_scalar_parameter_value(mi, k)
                if abs(got - float(v)) > 1e-4:
                    bad.append((k, got, v))
        for k in TEXPARAMS:
            if mel.get_material_instance_texture_parameter_value(mi, k) is None:
                bad.append((k, None, "texture"))
        parent = mi.get_editor_property("parent")
        if parent is None or parent.get_name() != MASTER:
            bad.append(("parent", parent, MASTER))
        unreal.log(f"Village: MI_{name} parameters resolve: {'OK' if not bad else 'FAIL ' + str(bad)}")
        errors += len(bad)
    return errors


def main():
    unreal.log("Village: step 1/3 textures")
    present = IMP.import_textures(PACK)
    need = [f"T_Village_{s}_{x}" for s in ("RockWall", "LichenRock", "NordicMoss", "RoughWood", "Thatch", "RustyMetal", "ClayPlaster")
            for x in ("BC", "N", "ORM")] + ["T_Village_GrimeMask_MR"]
    miss = [n for n in need if n not in present]
    if miss:
        raise RuntimeError(f"textures missing after import: {miss}")
    unreal.log("Village: step 2/3 master material")
    master = build_master()
    unreal.log("Village: step 3/3 material instances")
    made = build_instances(master)
    err = verify(master)
    unreal.log(f"Village: DONE master={MASTER} instances={len(made)} verify_errors={err}")


main()
