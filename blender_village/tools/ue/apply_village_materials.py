"""Put the village material instances on static meshes that are ALREADY imported (e.g. the client's GLB imports).

Editor: Tools > Execute Python Script > apply_village_materials.py   (or -ExecCmds="py <path>\\apply_village_materials.py")
Optional env: VILLAGE_MESH_ROOTS="/Game/Buildings;/Game/Village/Buildings"   VILLAGE_MASK_GAMMA=1.0

For every StaticMesh under the roots it
  * assigns slot M_xxx -> /Game/Village/Materials/MI_M_xxx by slot NAME (slots with no instance are listed and left alone),
  * turns Nanite on if it is off (the mesh rebuilds),
  * saves the mesh.
It does not touch levels, so it can run in your working level (no mesh is spawned, nothing is moved).
IMPORTANT (vertex colour): Unreal's glTF importer reads only COLOR_0.  GLBs written by the plain Blender exporter hold Mask in
COLOR_1 (COLOR_0 is white), so the buildings look fully mossy/worn.  Fix the GLB with tools/ue/fix_glb_mask.py (seconds, no Blender)
or re-export with tools/ue/export_building_glb.py, then re-import the GLB (replace the existing assets) and run this again.
"""
import os

import unreal

EAL = unreal.EditorAssetLibrary
MAT_DIR = "/Game/Village/Materials"


def main():
    roots = [r for r in os.environ.get("VILLAGE_MESH_ROOTS", "/Game/Buildings;/Game/Village/Buildings").split(";") if r]
    total = 0
    for root in roots:
        if not EAL.does_directory_exist(root):
            unreal.log(f"Village: {root} does not exist, skipped")
            continue
        for a in EAL.list_assets(root, recursive=True):
            if EAL.find_asset_data(a).asset_class_path.asset_name != "StaticMesh":
                continue
            mesh = EAL.load_asset(a)
            ok, missing = [], []
            for i, sm in enumerate(mesh.static_materials):
                slot = str(sm.material_slot_name)
                mi = EAL.load_asset(f"{MAT_DIR}/MI_{slot}")
                if mi is None:
                    missing.append(slot)
                else:
                    mesh.set_material(i, mi)
                    ok.append(slot)
            ns = mesh.get_editor_property("nanite_settings")
            if not ns.enabled:
                ns.enabled = True
                mesh.set_editor_property("nanite_settings", ns)
            EAL.save_loaded_asset(mesh)
            total += 1
            unreal.log(f"Village: {a}: assigned {len(ok)} slots {ok}; missing {missing}; Nanite on")
    g = os.environ.get("VILLAGE_MASK_GAMMA")
    if g:
        mel = unreal.MaterialEditingLibrary
        for a in EAL.list_assets(MAT_DIR, recursive=False):
            o = EAL.load_asset(a)
            if isinstance(o, unreal.MaterialInstanceConstant):
                mel.set_material_instance_scalar_parameter_value(o, "MaskGamma", float(g))
                EAL.save_loaded_asset(o)
        unreal.log(f"Village: MaskGamma = {g} on all instances")
    unreal.log(f"Village: DONE, {total} static meshes updated")


main()
