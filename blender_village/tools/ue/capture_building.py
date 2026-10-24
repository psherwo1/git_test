"""Lookdev screenshot of an imported building (editor with a RENDERING viewport, i.e. no -nullrhi).

    UnrealEditor.exe <Project>.uproject -ExecutePythonScript="<repo>\\tools\\ue\\capture_building.py" -unattended
    env: VILLAGE_BUILDING_DIR=<export dir>, SHOT_DIR=<where the PNGs go>, SHOT_WAIT=<s before the first capture, default 90>,
         DEBUG_MASK=1 (also shoot the mesh with a material that shows the vertex colour), MARKERS=1 (spheres on decal anchors)

Builds an empty level (import_building.py, --spawn), adds directional light + sky light + sky atmosphere + grey ground, and takes
SceneCapture2D shots: <id>_34.png (3/4 view), <id>_close.png (door side, close), <id>_top.png (roof from above), then quits.
"""
import importlib.util
import json
import math
import os
import time

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["VILLAGE_NO_AUTORUN"] = "1"
spec = importlib.util.spec_from_file_location("village_import", os.path.join(HERE, "import_building.py"))
IB = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IB)

EXISTING = os.environ.get("EXISTING_MESH")      # /Game/... static mesh already imported (e.g. from the client GLB): skip the import
EXPORT = os.environ.get("VILLAGE_BUILDING_DIR", EXISTING or "")
BID = os.path.basename(EXPORT.rstrip("\\/"))
SHOT = os.environ.get("SHOT_DIR", EXPORT)
WAIT = float(os.environ.get("SHOT_WAIT", "90"))
os.makedirs(SHOT, exist_ok=True)
ELL = unreal.EditorLevelLibrary

def go(mesh, actor):
    global bb, c, size, R, H, rt, cap, cc, prefix, names, st, VIEWS
    actor.set_actor_label("Building")
    if os.environ.get("DEBUG_MASK") == "1":
        am = unreal.AssetToolsHelpers.get_asset_tools()
        path = "/Game/Village/Debug/M_DebugMask"
        mat = unreal.EditorAssetLibrary.load_asset(path)
        if mat is None:
            mat = am.create_asset("M_DebugMask", "/Game/Village/Debug", unreal.Material, unreal.MaterialFactoryNew())
            mel = unreal.MaterialEditingLibrary
            vc = mel.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -300, 0)
            mel.connect_material_property(vc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            mel.recompile_material(mat)
        comp = actor.static_mesh_component
        for i in range(comp.get_num_materials()):
            comp.set_material(i, mat)

    bb = mesh.get_bounding_box()
    c = (bb.min + bb.max) * 0.5
    size = bb.max - bb.min
    R = max(size.x, size.y) * 0.5
    H = bb.max.z
    ground = ELL.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(c.x, c.y, bb.min.z))
    ground.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane"))
    ground.set_actor_scale3d(unreal.Vector(60, 60, 1))
    ground.static_mesh_component.set_material(0, unreal.EditorAssetLibrary.load_asset("/Game/Village/Materials/MI_M_earth"))
    ELL.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, -38, 205))
    ELL.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
    ELL.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))

    if os.environ.get("MARKERS") == "1":
        anc = json.load(open(os.path.join(EXPORT, "decal_anchors.json")))["anchors"]
        sph = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
        for a in anc[::3]:
            m = ELL.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*a["pos_cm"]))
            m.static_mesh_component.set_static_mesh(sph)
            m.set_actor_scale3d(unreal.Vector(0.12, 0.12, 0.12))

    # door faces +Y in Unreal (Blender -Y): shoot from the +Y side
    def view(dx, dy, dz, tz):
        return (unreal.Vector(c.x + dx * R, c.y + dy * R, dz * R), unreal.Vector(c.x, c.y, tz))

    VIEWS = {
        "34": view(2.0, 2.9, 1.1, H * 0.38),
        "close": view(0.8, 2.2, 0.35, H * 0.2),
        "top": view(1.0, 2.4, 3.6, H * 0.3),
        "back": view(-2.0, -2.9, 1.1, H * 0.38),
    }
    rt = unreal.RenderingLibrary.create_render_target2d(ELL.get_editor_world(), 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    cap = ELL.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    cc = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
    cc.set_editor_property("texture_target", rt)
    cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    cc.set_editor_property("capture_every_frame", False)
    cc.set_editor_property("capture_on_movement", False)
    cc.set_editor_property("fov_angle", 55.0)
    prefix = BID + ("_dbg" if os.environ.get("DEBUG_MASK") == "1" else "")
    names = list(VIEWS.keys())
    st = {"t0": time.time(), "i": 0, "phase": 0, "t": 0}


    def tick(dt):
        el = time.time() - st["t0"]
        if el < WAIT or st["i"] >= len(names):
            if st["i"] >= len(names) and el > st["t"] + 3:
                IB.log("SHOTS DONE")
                unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
            return
        name = names[st["i"]]
        if st["phase"] == 0:
            pos, tgt = VIEWS[name]
            cap.set_actor_location(pos, False, False)
            cap.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(pos, tgt), False)
            st["phase"], st["t"] = 1, el
        elif st["phase"] in (1, 2, 3) and el > st["t"] + 4:
            cc.capture_scene()
            st["phase"] += 1
            st["t"] = el
        elif st["phase"] == 4 and el > st["t"] + 4:
            unreal.RenderingLibrary.export_render_target(ELL.get_editor_world(), rt, SHOT, f"{prefix}_{name}.png")
            IB.log(f"saved {prefix}_{name}.png")
            st["i"] += 1
            st["phase"], st["t"] = 0, el


    unreal.register_slate_post_tick_callback(tick)

if EXISTING:
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    _m = unreal.EditorAssetLibrary.load_asset(EXISTING)
    IB.apply_materials(_m)
    go(_m, unreal.EditorLevelLibrary.spawn_actor_from_object(_m, unreal.Vector(0, 0, 0)))
else:
    IB.main(EXPORT, spawn=True, on_done=go)

