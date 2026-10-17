"""Junction test shots (textured r2 lookdev vs clay) for v3_longhouse_roundend r06 and v2_tiered_hall r07.

Usage (Blender 5.1 as a Python module):
    python.exe -I jt_shots.py textured <lookdev.blend> <render_dir> <building> [--samples N] [--only a,b]
        opens the r2 lookdev .blend made by lookdev/scripts/apply_lookdev.py (--shots none), adds the shot
        cameras below and renders 1920x1080 Cycles OptiX, denoised.  Never saves the .blend.
    python.exe -I jt_shots.py clay <building.blend> <render_dir> <building> [--only a,b]
        clay twin with the director's clay setup (dir_render6.py / dir_v2r7_junctions.py): clay override, sun
        rot (52, 0, -38) 3.5, sky-blue world 0.45, AgX, 1280x720, 24 samples.  For shots with no director clay.

Camera sources:
  d03 / d23        renders/variants/v3_longhouse_roundend/round_06/director_extra/dir_render6.py (exact)
  a08 / c13 / c17 / o01  director's v2 r7 junction script (dir_v2r7_junctions.py, found in the session scratchpad,
                   not in round_07/director_extra) (exact)
  actor_closeup    tools/render_review.py VIEWS["actor_closeup"] from the round's stats.json bbox (exact)
  pan8m / up6m     placed by hand for this test
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[1:]
MODE, BLEND, RDIR, BUILDING = argv[0], argv[1], argv[2], argv[3]
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 112
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None


def actor_closeup(lo, hi):
    """tools/render_review.py actor_closeup, from the stats.json bbox."""
    lo, hi = Vector(lo), Vector(hi)
    center = (lo + hi) / 2
    size = max((hi - lo).x, (hi - lo).y, (hi - lo).z, 4.0)
    az, el = math.radians(-20), math.radians(2)
    target = Vector((center.x, lo.y, lo.z + 1.5))
    dist = max(size * 0.45, 4.0)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    loc = target + d * dist
    loc.z = max(lo.z + 1.65, loc.z)
    return tuple(loc), tuple(target), 28


# name: (location, target, lens, pan_deg_per_s or 0)
SHOTS = {
    "v3_longhouse_roundend": {
        "d03_s_crossing_east_eye": ((6.2, -5.6, 1.65), (2.3, -3.1, 2.5), 50, 0),
        "actor_closeup": actor_closeup((-8.887384414672852, -4.278973579406738, -0.05000000074505806),
                                       (8.887384414672852, 4.278973579406738, 7.644298553466797)) + (0,),
        "d23_door_closeup": ((-2.4, -5.6, 1.65), (-2.4, -2.6, 1.25), 35, 0),
        # slow-pan frame: eye level, 8 m out from the south wall (y -2.6), the SE crossing right of centre
        "pan8m_front": ((0.6, -10.6, 1.65), (1.3, -3.0, 2.3), 35, 0),
        # the same frame during a quick pan (60 deg/s, 24 fps, 180 deg shutter -> 1.25 deg of blur)
        "pan8m_front_blur60": ((0.6, -10.6, 1.65), (1.3, -3.0, 2.3), 35, 60),
    },
    "v2_tiered_hall": {
        "a08_turE_apron_N_flank": ((7.4, 3.0, 6.0), (5.0, 1.3, 4.3), 55, 0),
        "c13_turE_cheek_S_lookup": ((6.7, -2.6, 1.9), (5.8, -1.2, 3.4), 35, 0),
        "c17_turE_cheek_S_tight": ((6.55, -2.05, 3.3), (5.85, -1.22, 3.45), 45, 0),
        "actor_closeup": actor_closeup((-6.141589164733887, -6.1409759521484375, -0.05000000074505806),
                                       (7.336888790130615, 6.141299724578857, 18.508424758911133)) + (0,),
        "o01_door_closeup": ((0.9, -7.6, 1.6), (0.0, -5.0, 1.2), 35, 0),
        # ground level, ~6 m SE of the E turret / skirt1 junction (cheek at 5.85, -1.25, 3.45), looking up
        "up6m_turE_junction": ((9.3, -6.1, 1.65), (5.7, -1.1, 3.9), 35, 0),
        "up6m_turE_junction_blur60": ((9.3, -6.1, 1.65), (5.7, -1.1, 3.9), 35, 60),
    },
}[BUILDING]


def gpu(scn):
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        scn.cycles.device = "GPU" if any(d.use for d in prefs.devices) else "CPU"
    except Exception as e:  # noqa
        print("GPU setup failed", e)
        scn.cycles.device = "CPU"
    print("DEVICE", scn.cycles.device, flush=True)


bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
scn = bpy.context.scene
os.makedirs(RDIR, exist_ok=True)

if MODE == "clay":
    clay = bpy.data.materials.new("_DIR_clay")
    clay.use_nodes = True
    b = clay.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
    b.inputs["Roughness"].default_value = 0.65
    scn.view_layers[0].material_override = clay
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.052 if BUILDING == "v2_tiered_hall" else -0.002))
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.angle = math.radians(2.0)
    world = bpy.data.worlds.new("_DIR_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.45
    scn.world = world
    scn.render.engine = "CYCLES"
    scn.cycles.samples = 24
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = 1280, 720
    scn.render.resolution_percentage = 100
    scn.view_settings.view_transform = "AgX"
    try:
        scn.view_settings.look = "None"
    except TypeError:
        pass
else:
    scn.cycles.samples = SAMPLES
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
    scn.render.resolution_percentage = 100
gpu(scn)
scn.render.image_settings.file_format = "PNG"
scn.render.use_persistent_data = True

cd = bpy.data.cameras.new("JT_cam")
cd.sensor_width = 36.0
cd.sensor_fit = "AUTO"   # the director's camera_add() default (horizontal for 16:9)
cd.clip_start = 0.02
cd.clip_end = 2000.0
cam = bpy.data.objects.new("JT_cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam
FPS = 24

for name, (loc, tgt, lens, pan) in SHOTS.items():
    if ONLY and name not in ONLY:
        continue
    if MODE == "clay" and pan:
        continue
    cam.animation_data_clear()
    cam.location = Vector(loc)
    cd.lens = lens
    rot = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.rotation_euler = rot
    scn.frame_set(1)
    if pan:
        step = math.radians(pan) / FPS
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
        for f, k in ((0, -1), (1, 0), (2, 1)):
            cam.rotation_euler = (rot.x, rot.y, rot.z + k * step)
            cam.keyframe_insert("rotation_euler", frame=f)
        scn.frame_set(1)
        print("pan step deg/frame", round(math.degrees(step), 3), "rot z at f1", round(math.degrees(cam.rotation_euler.z), 3),
              "expected", round(math.degrees(rot.z), 3), flush=True)
        scn.render.use_motion_blur = True
        scn.render.motion_blur_shutter = 0.5
        scn.render.motion_blur_position = "CENTER"
    else:
        scn.render.use_motion_blur = False
    scn.render.filepath = os.path.join(os.path.abspath(RDIR), name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scn.render.filepath, "loc", tuple(round(v, 3) for v in loc), "lens", lens, flush=True)
