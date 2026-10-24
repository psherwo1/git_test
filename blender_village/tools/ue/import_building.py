"""Import one exported kit building into Unreal 5.8 and put the village materials on it.

Run it in the editor (Tools > Execute Python Script) or headless:

    UnrealEditor.exe <Project>.uproject -ExecutePythonScript="<repo>\\tools\\ue\\import_building.py <export_dir> [--spawn]"
    (or set env VILLAGE_BUILDING_DIR=<export_dir>, VILLAGE_SPAWN=1)

<export_dir> is export/ue_buildings/<id>/ made by export_building_glb.py (or export_building_fbx.py): it holds <id>.glb (or <id>.fbx)
and <id>_export.json.  The script

  1. refuses to run if the open level has unsaved changes (same guard as build_village_materials.py v2), switches to an EMPTY
     untitled level while it imports (the v1 material build crashed a GPU with a busy level + live viewport) and reopens your
     level afterwards;
  2. imports the file to /Game/Village/Buildings/<id>/ as ONE static mesh (glTF via Interchange, or FBX with explicit options:
     vertex colour Replace, tangents from file, no materials/textures created, lightmap UVs off);
  3. turns Nanite on, assigns slot M_xxx -> /Game/Village/Materials/MI_M_xxx by slot NAME, deletes the placeholder materials the
     importer made, and checks that the mesh carries vertex colours (Mask);
  4. with --spawn, drops a static mesh actor at the origin of the (empty) level and saves nothing else.
Log lines start with "Village:".  Requires build_village_materials.py to have run once in the project.
"""
import json
import os
import sys
import time

import unreal

MAT_DIR = "/Game/Village/Materials"
DEST_ROOT = "/Game/Village/Buildings"
EAL = unreal.EditorAssetLibrary


def log(m):
    unreal.log("Village: " + str(m))


def warn(m):
    unreal.log_warning("Village: " + str(m))


def _current_level():
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        return w.get_path_name().split(".")[0] if w else None
    except Exception:  # noqa
        return None


def _enter_empty_level():
    if os.environ.get("VILLAGE_KEEP_LEVEL") == "1":
        return None
    prev = _current_level()
    if not prev:
        return None
    if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
        raise RuntimeError("Village: the open level has unsaved changes - save it (Ctrl+S) and run the script again. "
                           "Nothing was changed.")
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    log(f"switched to an empty level for the import (will reopen {prev} afterwards)")
    return None if prev.startswith("/Temp/") else prev


def _leave_empty_level(prev):
    if prev:
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(prev)
            log(f"reopened {prev}")
        except Exception as e:  # noqa
            warn(f"could not reopen {prev} ({e}); open it from the Content Browser")


def _fbx_task(path, dest):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("automated_import_should_detect_type", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    sm = ui.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("vertex_color_import_option", unreal.VertexColorImportOption.REPLACE)
    sm.set_editor_property("build_nanite", True)
    sm.set_editor_property("generate_lightmap_u_vs", False)
    sm.set_editor_property("auto_generate_collision", False)
    sm.set_editor_property("remove_degenerates", True)
    sm.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    sm.set_editor_property("normal_generation_method", unreal.FBXNormalGenerationMethod.MIKK_T_SPACE)
    t = unreal.AssetImportTask()
    t.set_editor_property("options", ui)
    return t


def start_import(export_dir, bid):
    glb, fbx = os.path.join(export_dir, bid + ".glb"), os.path.join(export_dir, bid + ".fbx")
    path = glb if os.path.exists(glb) else fbx
    if not os.path.exists(path):
        raise RuntimeError(f"Village: no {bid}.glb / {bid}.fbx in {export_dir}")
    dest = f"{DEST_ROOT}/{bid}"
    if EAL.does_directory_exist(dest):
        EAL.delete_directory(dest)           # clean re-import: the importer would otherwise keep stale material slots
    t = _fbx_task(path, dest) if path.endswith(".fbx") else unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", False)
    log(f"importing {path} -> {dest} ({os.path.getsize(path)/1e6:.0f} MB, about a minute for 1 M triangles)")
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return dest


def find_mesh(dest):
    meshes = []
    for a in EAL.list_assets(dest, recursive=True):
        if EAL.find_asset_data(a).asset_class_path.asset_name == "StaticMesh":
            meshes.append(a)
    return meshes

def apply_materials(mesh):
    """slot name -> MI_<slot>.  Returns (assigned, missing)."""
    ok, missing = [], []
    for i, sm in enumerate(mesh.static_materials):
        slot = str(sm.material_slot_name)
        mi = EAL.load_asset(f"{MAT_DIR}/MI_{slot}")
        if mi is None:
            missing.append(slot)
            continue
        mesh.set_material(i, mi)
        ok.append(slot)
    return ok, missing


def set_mask_gamma(g):
    """MaskGamma on all 15 instances (the master does pow(VertexColor, MaskGamma))."""
    mel = unreal.MaterialEditingLibrary
    n = 0
    for a in EAL.list_assets(MAT_DIR, recursive=False):
        o = EAL.load_asset(a)
        if isinstance(o, unreal.MaterialInstanceConstant) and o.get_name().startswith("MI_M_"):
            mel.set_material_instance_scalar_parameter_value(o, "MaskGamma", float(g))
            EAL.save_loaded_asset(o)
            n += 1
    log(f"MaskGamma = {g} on {n} instances")


def set_nanite(mesh):
    ns = mesh.get_editor_property("nanite_settings")
    if not ns.enabled:
        ns.enabled = True
        mesh.set_editor_property("nanite_settings", ns)
        log("Nanite switched on (the mesh rebuilds)")
    return mesh.get_editor_property("nanite_settings").enabled


def vertex_colours_present(mesh):
    try:
        return bool(mesh.get_editor_property("has_vertex_colors"))
    except Exception:  # noqa
        return None


def main(export_dir=None, spawn=None, on_done=None):
    """Starts the import.  In the editor the glTF/Interchange import finishes asynchronously, so the rest (materials, Nanite,
    spawn, reopening the level) runs from a tick callback once the static mesh exists; on_done(mesh, actor) is called then."""
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    export_dir = export_dir or os.environ.get("VILLAGE_BUILDING_DIR") or (args[0] if args else None)
    if spawn is None:
        spawn = os.environ.get("VILLAGE_SPAWN") == "1" or "--spawn" in sys.argv
    if not export_dir:
        raise RuntimeError("Village: pass the export folder (export/ue_buildings/<id>) as the argument or VILLAGE_BUILDING_DIR")
    export_dir = os.path.abspath(export_dir)
    bid = os.path.basename(export_dir.rstrip("\\/"))
    if os.path.exists(os.path.join(export_dir, bid + "_export.json")):
        info = json.load(open(os.path.join(export_dir, bid + "_export.json")))
        bid = info.get("id", bid)
        log(f"{bid}: {info['triangles']} triangles, slots {info['slots']}")
    if not EAL.does_asset_exist(f"{MAT_DIR}/MI_M_stone"):
        raise RuntimeError("Village: /Game/Village/Materials/MI_M_* not found - run build_village_materials.py first")
    prev = _enter_empty_level()
    dest = start_import(export_dir, bid)
    state = {"t0": time.time(), "seen": None, "handle": None}

    def finish():
        paths = find_mesh(dest)
        meshes = [EAL.load_asset(p) for p in paths]
        meshes.sort(key=lambda m: -(m.get_bounding_box().max - m.get_bounding_box().min).length())
        if len(meshes) > 1:
            warn(f"{len(meshes)} static meshes imported; using the biggest")
        mesh = meshes[0]
        bb = mesh.get_bounding_box()
        log(f"imported {mesh.get_path_name().split('.')[0]}; size cm {bb.max - bb.min}")
        ok, missing = apply_materials(mesh)
        log(f"material slots assigned: {ok}")
        if missing:
            warn(f"slots with no MI_ instance (left as imported): {missing}")
        set_nanite(mesh)
        if os.environ.get("VILLAGE_MASK_GAMMA"):
            set_mask_gamma(float(os.environ["VILLAGE_MASK_GAMMA"]))
        mdir = dest + "/Materials"
        if EAL.does_directory_exist(mdir):
            EAL.delete_directory(mdir)          # the importer's placeholder materials are no longer used
        EAL.save_loaded_asset(mesh)
        log(f"Nanite: {mesh.get_editor_property('nanite_settings').enabled}; check the Mask in the viewport (README step 5)")
        actor = None
        if spawn:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
            actor.set_actor_label(bid)
            log(f"spawned {bid} at the origin of the empty level (the level is not saved)")
        else:
            _leave_empty_level(prev)
        log(f"DONE {bid}")
        if on_done:
            on_done(mesh, actor)

    def tick(dt):
        try:
            now = time.time()
            if int(now) % 15 == 0 and state.get("lastlog") != int(now):
                state["lastlog"] = int(now)
                log(f"waiting for import... mesh found={bool(find_mesh(dest))} registry loading={unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets()}")
            if find_mesh(dest) and not unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets():
                if state["seen"] is None:
                    state["seen"] = now
                if now - state["seen"] > 4.0:           # mesh registered and quiet for 4 s
                    unreal.unregister_slate_post_tick_callback(state["handle"])
                    finish()
            else:
                state["seen"] = None
            if now - state["t0"] > 1800:
                unreal.unregister_slate_post_tick_callback(state["handle"])
                warn("timed out waiting for the import (30 min)")
        except Exception as e:  # noqa
            unreal.unregister_slate_post_tick_callback(state["handle"])
            unreal.log_error(f"Village: {e}")
            raise

    state["handle"] = unreal.register_slate_post_tick_callback(tick)


if os.environ.get("VILLAGE_NO_AUTORUN") != "1":
    main()
