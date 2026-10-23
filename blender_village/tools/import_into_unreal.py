"""Unreal Engine 5 import for the village texture pack.  NOT yet run in an editor (no UE install on the authoring
machine): treat the first run as a test.

In the Unreal Editor: enable Plugins > Python Editor Script Plugin (restart), then Tools > Execute Python Script
and pick this file (it must sit next to the Textures folder and textures_manifest.json).

It imports every PNG in Textures/ into /Game/Village/Textures with the right settings
  *_BC   sRGB on,  compression Default (BC7 if you set the texture group to 'World')
  *_N    DirectX normal (green already flipped), compression Normalmap, sRGB off
  *_ORM  sRGB off, compression Masks (R = AO, G = roughness, B = metallic)
  *_MR   (grime pack) sRGB off, compression Masks
and builds one simple material per set in /Game/Village/Materials (M_Village_<Set>) with a 'UVScale' scalar
parameter, BC -> Base Color, ORM -> AO / Roughness / Metallic, N -> Normal.  Nanite meshes want world-space UVs or the
kit UVs (~1 UV unit per metre): UVScale defaults to the set's tile size (UV 1 = 1 m, tile = tile_m).
"""
import json
import os

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(HERE, "Textures")
MAN = json.load(open(os.path.join(HERE, "textures_manifest.json")))
DEST_T = "/Game/Village/Textures"
DEST_M = "/Game/Village/Materials"

tasks = []
for f in sorted(os.listdir(TEX_DIR)):
    if not f.lower().endswith(".png"):
        continue
    t = unreal.AssetImportTask()
    t.filename = os.path.join(TEX_DIR, f)
    t.destination_path = DEST_T
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

for f in sorted(os.listdir(TEX_DIR)):
    name = os.path.splitext(f)[0]
    tex = unreal.EditorAssetLibrary.load_asset(f"{DEST_T}/{name}")
    if not tex:
        continue
    if name.endswith("_BC"):
        tex.set_editor_property("srgb", True)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    elif name.endswith("_N"):
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("flip_green_channel", False)
    else:                                   # _ORM, _MR
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)

mel = unreal.MaterialEditingLibrary
for sname, s in MAN["sets"].items():
    if sname == "GrimeMask":
        continue
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        f"M_Village_{sname}", DEST_M, unreal.Material, unreal.MaterialFactoryNew())
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1100, 200)
    sc.set_editor_property("parameter_name", "UVScale")
    sc.set_editor_property("default_value", 1.0 / s["tile_m"])
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -700, 60)
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")

    def samp(suffix, y):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, y)
        node.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(f"{DEST_T}/T_Village_{sname}_{suffix}"))
        mel.connect_material_expressions(mul, "", node, "UVs")
        return node
    bc, nm, orm = samp("BC", -300), samp("N", 0), samp("ORM", 300)
    mel.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    mel.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("Village texture import done")
