"""Unreal Engine 5 import for the village texture pack (tested headless on UE 5.8, see README_materials.md).

Run it in the editor: Tools > Execute Python Script (needs the Python Editor Script Plugin), or headless:
    UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="<this file>"
It must sit next to the Textures folder and textures_manifest.json (the pack folder), or set VILLAGE_PACK_DIR.

What it does
  1. imports every PNG in Textures/ to /Game/Village/Textures (skips textures that already exist unless
     VILLAGE_REIMPORT=1) and sets the import settings
       *_BC   sRGB on,  compression Default (BC7 for the World group), texture group World
       *_N    DirectX normal (green already flipped), compression Normalmap, sRGB off, Flip Green off
       *_ORM  sRGB off, compression Masks, R = AO, G = roughness, B = metallic
       *_MR   (grime pack) sRGB off, compression Masks, R = grime mask, G = roughness
  2. builds one simple material per set in /Game/Village/Materials (M_Village_<Set>) with a UVScale parameter.
build_village_materials.py imports this file as a module and calls import_textures() (step 1 only).
"""
import json
import os

import unreal

DEST_T = "/Game/Village/Textures"
DEST_M = "/Game/Village/Materials"


def find_pack_dir():
    env = os.environ.get("VILLAGE_PACK_DIR")
    cands = [env] if env else []
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.getcwd()
    cands += [here, os.path.join(here, "..", "..", "export", "ue_texture_pack")]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "textures_manifest.json")) and os.path.isdir(os.path.join(c, "Textures")):
            return os.path.abspath(c)
    raise RuntimeError("textures_manifest.json + Textures/ not found next to the script (tried %s); set VILLAGE_PACK_DIR" % cands)


def load_manifest(pack=None):
    pack = pack or find_pack_dir()
    with open(os.path.join(pack, "textures_manifest.json")) as fh:
        return json.load(fh)


def _tex_settings(name):
    """(srgb, compression, lod group) for a texture asset name."""
    TC, TG = unreal.TextureCompressionSettings, unreal.TextureGroup
    if name.endswith("_BC"):
        return True, TC.TC_DEFAULT, TG.TEXTUREGROUP_WORLD
    if name.endswith("_N"):
        return False, TC.TC_NORMALMAP, TG.TEXTUREGROUP_WORLD_NORMAL_MAP
    return False, TC.TC_MASKS, TG.TEXTUREGROUP_WORLD_SPECULAR   # _ORM, _MR


def _set(obj, prop, value, optional=False):
    try:
        obj.set_editor_property(prop, value)
    except Exception as e:  # noqa
        (unreal.log if optional else unreal.log_warning)(f"Village: cannot set {prop} on {obj.get_name()}: {e}")


def import_textures(pack=None, reimport=None):
    """Import (if missing) and configure all textures. Returns the list of asset names that are present."""
    pack = pack or find_pack_dir()
    if reimport is None:
        reimport = os.environ.get("VILLAGE_REIMPORT") == "1"
    tex_dir = os.path.join(pack, "Textures")
    files = [f for f in sorted(os.listdir(tex_dir)) if f.lower().endswith(".png")]
    tasks = []
    for f in files:
        name = os.path.splitext(f)[0]
        if not reimport and unreal.EditorAssetLibrary.does_asset_exist(f"{DEST_T}/{name}"):
            continue
        t = unreal.AssetImportTask()
        t.filename = os.path.join(tex_dir, f)
        t.destination_path = DEST_T
        t.destination_name = name
        t.replace_existing = True
        t.automated = True
        t.save = False
        tasks.append(t)
    if tasks:
        unreal.log(f"Village: importing {len(tasks)} textures from {tex_dir}")
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    present = []
    for f in files:
        name = os.path.splitext(f)[0]
        tex = unreal.EditorAssetLibrary.load_asset(f"{DEST_T}/{name}")
        if not tex:
            unreal.log_error(f"Village: texture {name} missing after import")
            continue
        srgb, comp, grp = _tex_settings(name)
        _set(tex, "srgb", srgb)
        _set(tex, "compression_settings", comp)
        _set(tex, "lod_group", grp)
        if name.endswith("_N"):
            _set(tex, "flip_green_channel", False)
        _set(tex, "virtual_texture_streaming", False, optional=True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        present.append(name)
    return present


def build_set_materials(pack=None):
    """One simple material per set (BC/N/ORM -> base colour/normal/AO,roughness,metallic) with a UVScale parameter."""
    man = load_manifest(pack)
    mel = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for sname, s in man["sets"].items():
        if sname == "GrimeMask":
            continue
        path = f"{DEST_M}/M_Village_{sname}"
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
        mat = tools.create_asset(f"M_Village_{sname}", DEST_M, unreal.Material, unreal.MaterialFactoryNew())
        uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
        sc = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1100, 200)
        sc.set_editor_property("parameter_name", "UVScale")
        sc.set_editor_property("default_value", 1.0 / s["tile_m"])   # kit UVs are ~1 unit per metre
        mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -700, 60)
        mel.connect_material_expressions(uv, "", mul, "A")
        mel.connect_material_expressions(sc, "", mul, "B")

        def samp(suffix, y, stype):
            node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, y)
            node.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(f"{DEST_T}/T_Village_{sname}_{suffix}"))
            node.set_editor_property("sampler_type", stype)
            mel.connect_material_expressions(mul, "", node, "UVs")
            return node
        ST = unreal.MaterialSamplerType
        bc, nm, orm = samp("BC", -300, ST.SAMPLERTYPE_COLOR), samp("N", 0, ST.SAMPLERTYPE_NORMAL), samp("ORM", 300, ST.SAMPLERTYPE_MASKS)
        mel.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
        mel.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        mel.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        made.append(mat.get_name())
    return made


def main():
    pack = find_pack_dir()
    present = import_textures(pack)
    made = build_set_materials(pack)
    unreal.log(f"Village texture import done: {len(present)} textures, per-set materials {made}")


if __name__ == "__main__":
    main()
