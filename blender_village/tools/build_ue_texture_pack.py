"""Builds the Unreal-ready texture pack for the village buildings.

python.exe -I tools/build_ue_texture_pack.py <out_dir>

Reads the texture sets the lookdev (lookdev/scripts/apply_lookdev.py TEXSETS) uses, and writes per set, at 2048 px,
8-bit PNG: T_Village_<Set>_BC (base colour, sRGB), _N (DirectX normal, green flipped from the OpenGL sources, so
import with no flip), _ORM (R = AO, G = roughness, B = metallic; linear). Plus textures_manifest.json (tile sizes,
UE tiling, palette-slot to set mapping) and a copy of import_into_unreal.py.
"""
import json
import os
import shutil
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
TEX = os.path.join(ROOT, "lookdev", "textures")
OUT = os.path.abspath(sys.argv[-1])
os.makedirs(os.path.join(OUT, "Textures"), exist_ok=True)
N = 2048

R = "rock_wall_visoeh2bw"
SETS = {   # name: (tile size in metres, colour, rough, normal(gl), ao or None, metal value, source note)
    "RockWall": (2.0, "lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_BaseColor.jpg",
                 "lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_Roughness.jpg",
                 "lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_Normal.jpg",
                 "lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K_AO.jpg", 0.0, "Quixel Megascans"),
    "LichenRock": (2.0, "lichen_rock_2k.blend/textures/lichen_rock_diff_2k.jpg",
                   "lichen_rock_2k.blend/textures/lichen_rock_rough_2k.exr",
                   "lichen_rock_2k.blend/textures/lichen_rock_nor_gl_2k.exr", None, 0.0, "Poly Haven lichen_rock"),
    "NordicMoss": (2.0, "nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_BaseColor.jpg",
                   "nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_Roughness.jpg",
                   "nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_Normal.jpg",
                   "nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K_AO.jpg", 0.0, "Quixel Megascans"),
    "RoughWood": (1.0, "rough_wood_2k.blend/textures/rough_wood_diff_2k.jpg",
                  "rough_wood_2k.blend/textures/rough_wood_rough_2k.jpg",
                  "rough_wood_2k.blend/textures/rough_wood_nor_gl_2k.exr", None, 0.0, "Poly Haven rough_wood"),
    "Thatch": (2.0, "riet_01_2k.blend/textures/riet_01_diff_2k.jpg",
               "riet_01_2k.blend/textures/riet_01_rough_2k.jpg",
               "riet_01_2k.blend/textures/riet_01_nor_gl_2k.exr", None, 0.0, "Poly Haven riet_01"),
    "RustyMetal": (2.0, "rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_BaseColor.jpg",
                   "rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_Roughness.jpg",
                   "rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_Normal.jpg",
                   "rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K_AO.jpg", 0.0, "Quixel Megascans"),
    "ClayPlaster": (2.0, "patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_diff_2k.jpg",
                    "patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_rough_2k.exr",
                    "patterned_clay_plaster_2k.blend/textures/patterned_clay_plaster_nor_gl_2k.exr", None, 0.0,
                    "Poly Haven patterned_clay_plaster"),
}


def load(rel):
    im = bpy.data.images.load(os.path.join(TEX, rel))
    im.colorspace_settings.name = "Non-Color"      # raw values in, raw values out
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)
    if (w, h) != (N, N):                           # nearest resample (all sources are 2k; safety only)
        yi = (np.arange(N) * h // N)
        xi = (np.arange(N) * w // N)
        a = a[yi][:, xi]
    return np.clip(a, 0.0, 1.0)


def save(a, path):
    im = bpy.data.images.new(os.path.basename(path), N, N, alpha=True, float_buffer=False)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(np.ascontiguousarray(a, np.float32).ravel())
    im.file_format = "PNG"
    im.filepath_raw = path
    im.save()
    bpy.data.images.remove(im)


manifest = dict(units="cm", tile_note="UV scale for world-aligned/triplanar mapping in UE = 1 / (tile_m * 100)", sets={})
for name, (size, c, r, n, ao, metal, src) in SETS.items():
    bc = load(c)
    bc[..., 3] = 1.0
    save(bc, os.path.join(OUT, "Textures", f"T_Village_{name}_BC.png"))
    nm = load(n)
    nm[..., 1] = 1.0 - nm[..., 1]                  # OpenGL (+Y) -> DirectX (-Y)
    nm[..., 3] = 1.0
    save(nm, os.path.join(OUT, "Textures", f"T_Village_{name}_N.png"))
    rr = load(r)[..., 0]
    orm = np.stack([load(ao)[..., 0] if ao else np.ones_like(rr), rr, np.full_like(rr, metal), np.ones_like(rr)], -1)
    save(orm, os.path.join(OUT, "Textures", f"T_Village_{name}_ORM.png"))
    manifest["sets"][name] = dict(tile_m=size, ue_uv_scale_per_cm=1.0 / (size * 100.0), source=src,
                                  maps=[f"T_Village_{name}_BC", f"T_Village_{name}_N", f"T_Village_{name}_ORM"])
    print("set", name, flush=True)

# the Megascans "Pure Imperfections" grime pack is already UE-packed: R = grime mask, G = roughness, B = 1
gsrc = os.path.join(TEX, "dirty_metal_rmmodbdp_2k_ue_mid", "Textures", "T_rmmodbdp_2K_MR.png")
shutil.copy(gsrc, os.path.join(OUT, "Textures", "T_Village_GrimeMask_MR.png"))
manifest["sets"]["GrimeMask"] = dict(tile_m=1.0, ue_uv_scale_per_cm=0.01, source="Quixel Megascans Pure Imperfections",
                                     maps=["T_Village_GrimeMask_MR"], note="R = grime mask, G = roughness, B = 1")

manifest["palette_slots"] = {          # the kit's 15 slots -> which sets the lookdev shaders blend (lookdev r2)
    "M_stone": ["RockWall", "LichenRock", "NordicMoss"], "M_rubble": ["RockWall", "LichenRock", "NordicMoss"],
    "M_stone_dressed": ["LichenRock", "NordicMoss"], "M_mortar": ["LichenRock"],
    "M_daub": ["ClayPlaster"], "M_wattle": ["RoughWood"],
    "M_timber": ["RoughWood"], "M_timber_weathered": ["RoughWood"],
    "M_roof_shingle": ["RoughWood", "NordicMoss"], "M_roof_shake": ["RoughWood", "NordicMoss"],
    "M_thatch": ["Thatch", "NordicMoss"], "M_iron": ["RustyMetal", "GrimeMask"], "M_lead": ["GrimeMask"],
    "M_earth": ["NordicMoss"], "M_moss": ["NordicMoss"]}
manifest["vertex_colour_Mask"] = dict(R="per-piece random 0-1 (tint / UV offset)", G="wear 0-1", B="moss / damp 0-1",
                                      note="The kit writes Mask as the CORNER byte colour attribute 'Mask'; export it as "
                                           "vertex colour and read it with a VertexColor node in the master material.")
manifest["roof_moss_scale"] = 0.25
json.dump(manifest, open(os.path.join(OUT, "textures_manifest.json"), "w"), indent=2)
shutil.copy(os.path.join(HERE, "import_into_unreal.py"), os.path.join(OUT, "import_into_unreal.py"))
print("DONE", OUT)
