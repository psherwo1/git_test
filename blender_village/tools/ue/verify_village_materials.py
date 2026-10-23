"""Verification + preview for build_village_materials.py (run AFTER it, same project):
    UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="<this file>" -unattended -AllowCommandletRendering
  1. wiring check: every Custom node input and the 4 material outputs are connected
  2. statistics of the compiled master (instruction counts), parameter listing
  3. a preview: new blank level, 15 cubes (one per MI) + a sphere row, a directional sun, a SceneCapture2D, PNG to
     <project>/Saved/VillagePreview/village_preview.png   (VILLAGE_PREVIEW_DIR overrides)
The preview needs a working RHI; it is skipped with a log line if the world cannot be created.  Meshes without a
'Mask' vertex colour render with Mask = (0.5, 0, 0) from the material's MaskOverride parameter.
"""
import os
import time

import unreal

mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
DEST_M = "/Game/Village/Materials"
SLOTS = ["M_stone", "M_rubble", "M_stone_dressed", "M_mortar", "M_daub", "M_wattle", "M_timber", "M_timber_weathered",
         "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_earth", "M_moss"]
OUT = os.environ.get("VILLAGE_PREVIEW_DIR") or os.path.join(unreal.Paths.project_saved_dir(), "VillagePreview")

master = EAL.load_asset(f"{DEST_M}/M_Village_Master")
unreal.log(f"Verify: master {master.get_name()} blend={master.get_editor_property('blend_mode')} "
           f"two_sided={master.get_editor_property('two_sided')} expressions={mel.get_num_material_expressions(master)}")

# 1. wiring
bad = 0
for e in mel.get_material_expressions(master):
    if isinstance(e, unreal.MaterialExpressionCustom):
        ins = mel.get_inputs_for_material_expression(master, e)
        names = list(e.get_editor_property("inputs"))
        for ci, src in zip(names, ins):
            if src is None:
                bad += 1
                unreal.log_error(f"Verify: Custom '{e.get_editor_property('description')}' input {ci.get_editor_property('input_name')} unconnected")
for prop in (unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_ROUGHNESS,
             unreal.MaterialProperty.MP_NORMAL, unreal.MaterialProperty.MP_METALLIC):
    if mel.get_material_property_input_node(master, prop) is None:
        bad += 1
        unreal.log_error(f"Verify: material output {prop} unconnected")
unreal.log(f"Verify: wiring problems = {bad}")

# 2. statistics
try:
    mel.recompile_material(master)
    st = mel.get_statistics(master)
    unreal.log(f"Verify: statistics VS {st.num_vertex_shader_instructions} PS {st.num_pixel_shader_instructions} "
               f"samplers {st.num_samplers} pixel tex samples {st.num_pixel_texture_samples}")
except Exception as e:  # noqa
    unreal.log_warning(f"Verify: statistics failed: {e}")

# 3. preview
try:
    for s in SLOTS:   # preview-only overrides, not saved
        mi = EAL.load_asset(f"{DEST_M}/MI_{s}")
        mel.set_material_instance_scalar_parameter_value(mi, "MaskOverrideAmount", 1.0)
        mel.set_material_instance_vector_parameter_value(mi, "MaskOverride", unreal.LinearColor(0.37, 0.3, 0.7, 1.0))
        mel.update_material_instance(mi)
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")

    def spawn(mesh, loc, mat=None, scale=(1, 1, 1)):
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc))
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        a.set_actor_scale3d(unreal.Vector(*scale))
        if mat:
            c.set_material(0, mat)
        return a

    spawn(plane, (300, 0, -50), None, (14, 8, 1))
    for i, s in enumerate(SLOTS):
        mi = EAL.load_asset(f"{DEST_M}/MI_{s}")
        col, row = i % 5, i // 5
        spawn(cube, (col * 130.0, row * 130.0 - 130.0, 0), mi, (1, 1, 1))
        spawn(sphere, (col * 130.0, row * 130.0 - 130.0, 110), mi, (0.6, 0.6, 0.6))
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, -35, 40))
    sun.light_component.set_editor_property("intensity", 9.0)
    sun.light_component.set_editor_property("light_color", unreal.Color(255, 220, 180, 255))
    fill = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(0, -50, 200))
    fill.light_component.set_editor_property("intensity", 3.0)
    fill.light_component.set_editor_property("cast_shadows", False)
    fill.light_component.set_editor_property("light_color", unreal.Color(170, 200, 255, 255))
    cam = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(260, -520, 420), unreal.Rotator(0, -35, 90))
    comp = cam.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("capture_source", getattr(unreal.SceneCaptureSource, os.environ.get("VILLAGE_CAPTURE_SOURCE", "SCS_FINAL_COLOR_LDR")))
    comp.set_editor_property("fov_angle", 60.0)
    os.makedirs(OUT, exist_ok=True)
    for attempt in range(int(os.environ.get("VILLAGE_CAPTURE_TRIES", "6"))):
        comp.capture_scene()
        time.sleep(5)
        unreal.log(f"Verify: capture attempt {attempt}")
    unreal.RenderingLibrary.export_render_target(world, rt, OUT, "village_preview.png")
    unreal.log(f"Verify: preview written to {OUT}")
except Exception as e:  # noqa
    unreal.log_warning(f"Verify: preview skipped: {e}")
unreal.log("Verify: finished")
