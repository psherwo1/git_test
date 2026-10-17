"""Harbour house (v5_harbour_house) textured look test: r05 (accepted, small eyebrow) vs r06 (bigger eyebrow).

python.exe -I hh_shots.py <lookdev.blend> <render_dir> [--samples N] [--only a,b]
    opens the r2 lookdev .blend made by lookdev/scripts/apply_lookdev.py (--look r2 --shots none), hides the
    apply_lookdev ground plane (it sits at the harbour bed, Z -2.51), stages land + water, adds the cameras and
    renders 1920x1080 Cycles OptiX, denoised.  Never saves the .blend.

Staging (same for both rounds), coordinates after the build's recentre (see dir_render_r05.py):
  land  = the director's quay-datum footprint (round_04/05 dir_render): everywhere behind the slip head
          (y < 0.227 - 0.30) and either side of the slip behind the quay face line (y < 3.427 - 0.30),
          top Z -0.045 (just under the -0.04 quay coping so the quay blocks are not buried), flagstone grey-brown.
  water = plane at Z -0.9 everywhere (seaward and inside the slip), dark blue-green, glossy, part transmissive.
  light = apply_lookdev r2 sun (6.0, warm, 24 deg elevation) + Nishita sky.  The r2 default azimuth puts the sun
          SE (+X, -Y), which leaves the west (eyebrow) slope and the water gable in shadow, so shots a-d and f use
          the same sun swung to the WNW (-X, +Y, like ref4 where the eyebrow slope and the water gable are lit);
          shot e (land side from the SE) keeps the r2 default azimuth.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[1:]
BLEND, RDIR = argv[0], argv[1]
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 112
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
scn = bpy.context.scene
os.makedirs(RDIR, exist_ok=True)

# ---------------------------------------------------------------- ground plane from apply_lookdev -> hide
g = bpy.data.objects.get("LD_ground")
if g:
    g.hide_render = True
    g.hide_viewport = True
    print("hid LD_ground at z", round(g.data.vertices[0].co.z + g.location.z, 3), flush=True)

# ---------------------------------------------------------------- land
lm = bpy.data.materials.new("HH_land")
lm.use_nodes = True
nt = lm.node_tree
nt.nodes.clear()
bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
tc = nt.nodes.new("ShaderNodeTexCoord")
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.feature = "DISTANCE_TO_EDGE"
vor.inputs["Scale"].default_value = 1.4
nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 0.8
noise.inputs["Detail"].default_value = 6.0
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.10, 0.092, 0.078, 1.0)
cr.color_ramp.elements[1].color = (0.20, 0.182, 0.152, 1.0)
nt.links.new(noise.outputs["Fac"], cr.inputs["Fac"])
joint = nt.nodes.new("ShaderNodeMapRange")       # dark joints between flags
joint.inputs["From Min"].default_value = 0.0
joint.inputs["From Max"].default_value = 0.035
joint.inputs["To Min"].default_value = 0.45
joint.inputs["To Max"].default_value = 1.0
nt.links.new(vor.outputs["Distance"], joint.inputs["Value"])
mul = nt.nodes.new("ShaderNodeMix")
mul.data_type = "RGBA"
mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
nt.links.new(cr.outputs["Color"], mul.inputs["A"])
nt.links.new(joint.outputs["Result"], mul.inputs["B"])
nt.links.new(mul.outputs["Result"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.9

TOP = -0.045
aux = []


def box(x0, x1, y0, y1, z0, z1):
    me = bpy.data.meshes.new("HH_land")
    vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs)
    me.materials.append(lm)
    o = bpy.data.objects.new("HH_land", me)
    scn.collection.objects.link(o)
    aux.append(o)


YQ = 3.427 - 0.30          # behind the quay blocks
YS = 0.227 - 0.30          # behind the slip head
box(-150, 150, -150, YS, -3.0, TOP)
box(-150, -0.608 - 0.30, YS, YQ, -3.0, TOP)
box(4.392 + 0.30, 150, YS, YQ, -3.0, TOP)

# ---------------------------------------------------------------- water
wm = bpy.data.materials.new("HH_water")
wm.use_nodes = True
wb = wm.node_tree.nodes.get("Principled BSDF")
wb.inputs["Base Color"].default_value = (0.012, 0.045, 0.045, 1.0)
wb.inputs["Roughness"].default_value = 0.06
wb.inputs["IOR"].default_value = 1.33
wb.inputs["Transmission Weight"].default_value = 0.45
wn = wm.node_tree
wnoise = wn.nodes.new("ShaderNodeTexNoise")
wnoise.inputs["Scale"].default_value = 2.5
wnoise.inputs["Detail"].default_value = 4.0
bump = wn.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.08
bump.inputs["Distance"].default_value = 0.05
wn.links.new(wnoise.outputs["Fac"], bump.inputs["Height"])
wn.links.new(bump.outputs["Normal"], wb.inputs["Normal"])
S = 300.0
me = bpy.data.meshes.new("HH_water")
me.from_pydata([(-S, -S, -0.9), (S, -S, -0.9), (S, S, -0.9), (-S, S, -0.9)], [], [(0, 1, 2, 3)])
me.materials.append(wm)
water = bpy.data.objects.new("HH_water", me)
scn.collection.objects.link(water)

# ---------------------------------------------------------------- light: r2 sun, azimuth per shot
sun = bpy.data.objects.get("LD_sun")
sky = next((n for n in scn.world.node_tree.nodes if n.type == "TEX_SKY"), None)
ELEV = math.radians(24.0)
AZ = {"r2": Vector((0.72, -0.69, 0.0)).normalized(), "wnw": Vector((-0.80, 0.45, 0.0)).normalized()}


def set_sun(key):
    d = AZ[key]
    v = Vector((d.x * math.cos(ELEV), d.y * math.cos(ELEV), math.sin(ELEV)))
    sun.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    if sky is not None:
        sky.sun_rotation = math.atan2(d.x, d.y)


# ---------------------------------------------------------------- render
scn.cycles.samples = SAMPLES
scn.cycles.use_adaptive_sampling = True
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = 100
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
scn.render.image_settings.file_format = "PNG"
scn.render.use_persistent_data = True

cd = bpy.data.cameras.new("HH_cam")
cd.sensor_width = 36.0
cd.sensor_fit = "AUTO"
cd.clip_start = 0.02
cd.clip_end = 2000.0
cam = bpy.data.objects.new("HH_cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam

# name: (location, target, lens, sun)
SHOTS = {
    # director round-5 e01 (exact): ref4 three-quarter of the eyebrow (west) side, from the NW over the water
    "a_ref4_three_quarter": ((-12.0, 10.0, 10.0), (-0.6, -1.6, 4.6), 34, "wnw"),
    # standing on the quay W of the slip, eye level, ~9 m from the eyebrow (centre y ~ -1.4, face x ~ -0.8, z ~ 4.4)
    "b_eyebrow_closeup_quay_eye": ((-8.5, 1.6, 1.7), (-0.8, -1.4, 4.5), 55, "wnw"),
    # water gable from the jetty end (deck end y ~ 8.6), eye level; director z06 position, widened (z06 at 26 mm
    # cut the arch off at the water line)
    "c_water_gable_jetty_eye": ((7.3, 8.5, 1.65), (2.4, 3.4, 3.0), 18, "wnw"),
    # side elevation from the W (eyebrow slope, ridge saddle in silhouette); the director's x34 is the same frame from the E
    "d_side_elevation_W": ((-18.0, -0.8, 2.0), (1.9, -0.8, 4.2), 30, "wnw"),
    # director y15 (exact): land side three-quarter at eye level, r2 default sun
    "e_land_three_quarter_eye": ((12.0, -16.0, 1.65), (1.0, -3.0, 4.0), 28, "r2"),
    # director e10 (exact): 45 m establishing from the W
    "f_establishing_45m": ((-38.0, 8.0, 14.0), (0.5, -2.0, 4.0), 50, "wnw"),
}

for name, (loc, tgt, lens, sk) in SHOTS.items():
    if ONLY and not any(name.startswith(p) for p in ONLY):
        continue
    set_sun(sk)
    cam.location = Vector(loc)
    cd.lens = lens
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(os.path.abspath(RDIR), name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scn.render.filepath, flush=True)
