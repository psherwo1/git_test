"""Builder round-2 close-ups (copy of bx_render_r01.py, round-2 coordinates: shift +4.606, -0.253; a 1.8 m figure under the lean-to opening at (-2.00, 4.05)) of the two WALL add-ons on a1_longhouse_addons (coordinates after the build's recentre:
shift +4.606, -0.450 -> lean-to centre x -1.294 (4.0 x 2.2 m), north face y 2.150, front y 4.350; porch centre x -2.394, south face
y -3.050, front beam y -4.050).  Adapted from renders/variants/v5_harbour_house/round_08/director_extra/dir_render_r08.py
(clay, sun, ground; `red` twins: black override, red world, no ground / figure: see-through check).
python -I bx_render_r01.py -- <blend> <out_dir> [only_prefix ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], argv[1]
only = argv[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_BX_clay", (0.42, 0.41, 0.39))
black = mat("_BX_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.002)); gnd = bpy.context.object
gnd.scale = (200, 200, 1); aux.append(gnd)
for (x, y) in ((0.6, -5.6), (-4.6, 5.8), (-2.00, 4.05)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=(x, y, 0.725)); aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, 1.68)); aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38))); sun = bpy.context.object
sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_BX_world"); world.use_nodes = True
bg = world.node_tree.nodes["Background"]; scn.world = world
scn.render.engine = "CYCLES"; scn.cycles.device = "CPU"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    if any(d.use for d in prefs.devices):
        scn.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

LX, LY, LF = -1.594, 2.347, 4.247          # lean-to centre x, host north face, lean-to front (round 2)
PX, PY, PF = -2.394, -2.853, -3.853        # porch centre x, host south face, porch front beam (round 2)
SHOTS = {
    "L01_leanto_NE_eye": ((LX + 4.2, LF + 4.2, 1.7), (LX, LY + 0.9, 1.4), 30, True),
    "L02_leanto_front_square": ((LX, LF + 4.5, 1.3), (LX, LY + 0.6, 1.2), 30, True),
    "L03_leanto_junction_6m": ((LX + 2.0, LF + 3.2, 4.6), (LX, LY + 0.1, 2.2), 40, True),
    "L04_leanto_W_verge_apron": ((LX - 4.0, LY + 1.8, 3.0), (LX - 2.15, LY, 2.9), 45, True),
    "L05_leanto_E_verge_apron": ((LX + 4.0, LY + 1.8, 3.0), (LX + 2.15, LY, 2.9), 45, True),
    "L06_leanto_inside_lookup": ((LX + 0.3, LY + 1.3, 0.7), (LX - 0.3, LY + 0.05, 2.1), 18, True),
    "L07_leanto_back_elev_12m": ((LX + 1.0, LF + 12.0, 3.0), (LX + 1.0, LY, 2.4), 35, False),
    "L08_leanto_figure_headroom": ((LX - 1.6, LF + 3.6, 1.4), (LX - 0.3, LF - 0.2, 1.9), 35, False),
    "L09_leanto_front_eave_arch": ((LX, LF + 6.0, 2.1), (LX, LY + 0.8, 2.2), 32, False),
    "P07_porch_E_verge_vs_roll": ((PX + 2.6, PF - 0.6, 2.9), (PX + 1.2, PY - 0.5, 3.15), 40, True),
    "P01_porch_SW_eye": ((PX - 3.0, PF - 3.6, 1.65), (PX, PY - 0.5, 2.5), 32, True),
    "P02_porch_square_eye": ((PX, PY - 5.5, 1.65), (PX, PY - 0.4, 2.6), 35, False),
    "P03_porch_lookup": ((PX + 1.2, PF - 0.9, 1.6), (PX, PY - 0.3, 2.9), 24, True),
    "P04_porch_junction_side_high": ((PX - 3.0, PF - 1.3, 3.7), (PX - 1.1, PY, 3.15), 40, True),
    "P05_porch_crane_6m": ((PX + 3.0, PF - 4.5, 6.0), (PX, PY - 0.4, 3.0), 35, True),
    "P06_porch_bracket_E": ((PX + 2.4, PF - 1.2, 1.9), (PX + 1.05, PY - 0.4, 2.1), 40, True),
}


def shoot(name, loc, tgt, lens, red):
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    for o in aux:
        o.hide_render = False
    sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1); bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24; scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png"); bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1); bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4; scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(out, name + "_red.png"); bpy.ops.render.render(write_still=True)


for name, (loc, tgt, lens, red) in SHOTS.items():
    if only and not any(name.startswith(p) for p in only):
        continue
    shoot(name, loc, tgt, lens, red)
    print("SHOT", name, flush=True)


