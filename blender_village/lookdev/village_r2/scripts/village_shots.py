"""Village r2 contact-sheet shots: one shared camera/light set for every building.

python.exe -I village_shots.py <lookdev.blend> <render_dir> --id ID [--samples 96] [--only hero,eye]
    opens a lookdev .blend made by lookdev/scripts/apply_lookdev.py (--look r2 --shots none), never saves it.
    Ground: apply_lookdev's LD_ground moved to Z = 0.  v5_harbour_house: LD_ground hidden and land (top -0.045
    behind the quay) + water (Z -0.9) staged exactly as lookdev/harbour_house/scripts/hh_shots.py.
    Light: apply_lookdev r2 sun (6.0, warm, 24 deg elevation) + its Nishita sky, unchanged except the azimuth,
    which is rotated with the building's entrance direction (for an entrance facing -Y it is exactly the r2 default,
    sun front-right of the entrance facade).
    Shots: hero = 35 mm three-quarter of the entrance side from 12 deg above, fitted to the building's object
    bounds; eye = 28 mm three-quarter of the entrance side, camera 1.7 m above the ground, fitted to the building.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[1:]
BLEND, RDIR = argv[0], argv[1]
BID = argv[argv.index("--id") + 1]
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 96
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else ["hero", "eye"]

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
scn = bpy.context.scene
os.makedirs(RDIR, exist_ok=True)

build = [o for o in scn.objects if o.type == "MESH" and not o.hide_render and not o.name.startswith("LD_")]


def wb(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


BMIN, BMAX = wb(build)
CTR = (BMIN + BMAX) * 0.5
print("BOUNDS", BID, tuple(round(v, 2) for v in BMIN), tuple(round(v, 2) for v in BMAX), flush=True)

# ---------------------------------------------------------------- ground / staging
GROUND_Z = 0.0
g = bpy.data.objects.get("LD_ground")
if BID == "v5_harbour_house":
    GROUND_Z = -0.045
    if g:
        g.hide_render = True
        g.hide_viewport = True
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
    joint = nt.nodes.new("ShaderNodeMapRange")
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

    def box(x0, x1, y0, y1, z0, z1):
        me = bpy.data.meshes.new("HH_land")
        vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        me.from_pydata(vs, [], fs)
        me.materials.append(lm)
        o = bpy.data.objects.new("HH_land", me)
        scn.collection.objects.link(o)

    YQ = 3.427 - 0.30
    YS = 0.227 - 0.30
    box(-150, 150, -150, YS, -3.0, -0.045)
    box(-150, -0.608 - 0.30, YS, YQ, -3.0, -0.045)
    box(4.392 + 0.30, 150, YS, YQ, -3.0, -0.045)
    wm = bpy.data.materials.new("HH_water")
    wm.use_nodes = True
    wbsdf = wm.node_tree.nodes.get("Principled BSDF")
    wbsdf.inputs["Base Color"].default_value = (0.012, 0.045, 0.045, 1.0)
    wbsdf.inputs["Roughness"].default_value = 0.06
    wbsdf.inputs["IOR"].default_value = 1.33
    wbsdf.inputs["Transmission Weight"].default_value = 0.45
    wn = wm.node_tree
    wnoise = wn.nodes.new("ShaderNodeTexNoise")
    wnoise.inputs["Scale"].default_value = 2.5
    wnoise.inputs["Detail"].default_value = 4.0
    bump = wn.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.05
    wn.links.new(wnoise.outputs["Fac"], bump.inputs["Height"])
    wn.links.new(bump.outputs["Normal"], wbsdf.inputs["Normal"])
    S = 300.0
    me = bpy.data.meshes.new("HH_water")
    me.from_pydata([(-S, -S, -0.9), (S, -S, -0.9), (S, S, -0.9), (-S, S, -0.9)], [], [(0, 1, 2, 3)])
    me.materials.append(wm)
    water = bpy.data.objects.new("HH_water", me)
    scn.collection.objects.link(water)
    # fit only what stands above the harbour bed water line (the quay toe under water is not seen)
    fit_objs = build
else:
    if g:
        for v in g.data.vertices:
            v.co.z = 0.0
        g.location.z = 0.0
    fit_objs = build

# ---------------------------------------------------------------- entrance direction
# brief: main doors face -Y (apply_lookdev's find_door also takes the most -Y door).  Keep -Y unless no
# entrance / door sits on the -Y side at all.
ent_dir, ent_src = None, None
try:
    ents = json.loads(scn.get("kit_entrances") or "[]")
except ValueError:
    ents = []
skip = ("iron", "nail", "hinge", "pintle", "bolt", "step", "backing", "latch", "ring", "handle")
cands = [o for o in build if "door" in o.name.lower() and not any(k in o.name.lower() for k in skip)]
front_y = CTR.y - 0.2 * (BMAX.y - BMIN.y)
front = [e for e in ents if e.get("out", [0, 0, 0])[1] < -0.7]
front_doors = [o for o in cands if (wb([o])[0].y + wb([o])[1].y) * 0.5 < front_y]
if front or front_doors:
    ent_dir = Vector((0, -1, 0))
    ent_src = "-Y: " + (("kit_entrances:" + str(front[0].get("name", "?"))) if front else front_doors[0].name)
if ent_dir is None and ents:
    e = min(ents, key=lambda e: (e.get("out", [0, -1, 0])[1], e["origin"][1]))
    od = Vector((e.get("out", [0, -1, 0])[0], e.get("out", [0, -1, 0])[1], 0.0))
    if od.length > 0.1:
        ent_dir, ent_src = od.normalized(), "kit_entrances:" + str(e.get("name", "?"))
if ent_dir is None:
    if cands:
        o = min(cands, key=lambda o: wb([o])[0].y)
        mn, mx = wb([o])
        dv = (mn + mx) * 0.5 - CTR
        dv.z = 0.0
        if abs(dv.x) > abs(dv.y):
            ent_dir = Vector((math.copysign(1, dv.x), 0, 0))
        else:
            ent_dir = Vector((0, math.copysign(1, dv.y), 0))
        ent_src = "door:" + o.name
if ent_dir is None:
    ent_dir, ent_src = Vector((0, -1, 0)), "default -Y"
print("ENTRANCE", BID, ent_src, tuple(round(v, 2) for v in ent_dir), flush=True)


def rot(v, deg):  # counter-clockwise about +Z
    a = math.radians(deg)
    return Vector((v.x * math.cos(a) - v.y * math.sin(a), v.x * math.sin(a) + v.y * math.cos(a), 0.0))


# ---------------------------------------------------------------- light: r2 sun, azimuth follows the entrance
sun = bpy.data.objects.get("LD_sun")
sky = next((n for n in scn.world.node_tree.nodes if n.type == "TEX_SKY"), None)
ELEV = math.radians(24.0)
R2_AZ = Vector((0.72, -0.69, 0.0)).normalized()
ang = math.degrees(math.atan2(ent_dir.y, ent_dir.x) - math.atan2(-1.0, 0.0))  # rotation of -Y onto ent_dir
sd = rot(R2_AZ, ang).normalized()
sv = Vector((sd.x * math.cos(ELEV), sd.y * math.cos(ELEV), math.sin(ELEV)))
sun.rotation_euler = sv.to_track_quat("Z", "Y").to_euler()
if sky is not None:
    sky.sun_rotation = math.atan2(sd.x, sd.y)
print("SUN", BID, "azimuth rotated %.0f deg from r2 default" % ang, tuple(round(v, 2) for v in sd), flush=True)

# ---------------------------------------------------------------- render settings
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
except Exception as ex:  # noqa
    print("GPU setup failed", ex)
    scn.cycles.device = "CPU"
try:
    scn.cycles.denoiser = "OPTIX"
except TypeError:
    pass
print("DEVICE", scn.cycles.device, flush=True)
scn.render.image_settings.file_format = "PNG"
scn.render.use_persistent_data = True

cd = bpy.data.cameras.new("VR2_cam")
cd.sensor_width = 36.0
cd.sensor_fit = "HORIZONTAL"
cd.clip_start = 0.05
cd.clip_end = 2000.0
cam = bpy.data.objects.new("VR2_cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam

corners = [o.matrix_world @ Vector(c) for o in fit_objs for c in o.bound_box]
corners = [p for p in corners if p.z >= GROUND_Z - 0.6] or corners  # buried footings / quay toe not framed


def fits(pos, tgt, lens, margin):
    rm = (tgt - pos).to_track_quat("-Z", "Y").to_matrix()
    th = SENSOR_H / 2 / lens * (1 - margin)
    tv = SENSOR_H * 9 / 16 / 2 / lens * (1 - margin)
    for p in corners:
        q = rm.transposed() @ (p - pos)
        if q.z >= -0.1 or abs(q.x / -q.z) > th or abs(q.y / -q.z) > tv:
            return False
    return True


SENSOR_H = 36.0
H = BMAX.z - GROUND_Z
top_corners = corners


def shoot(name, pos, tgt, lens):
    cam.location = pos
    cd.lens = lens
    cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    print("CAMERA", BID, name, tuple(round(v, 2) for v in pos), "->", tuple(round(v, 2) for v in tgt), lens, flush=True)
    if name not in ONLY:
        return
    scn.render.filepath = os.path.join(os.path.abspath(RDIR), name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scn.render.filepath, flush=True)


# hero: 35 mm, 12 deg above, three-quarter (camera 33 deg to the left of the entrance normal, like apply_lookdev's hero)
cmn = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
cmx = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
tgt = (cmn + cmx) * 0.5
hd = rot(ent_dir, -33.0)
e = math.radians(12.0)
dvec = Vector((hd.x * math.cos(e), hd.y * math.cos(e), math.sin(e)))
lo, hi = 1.0, 600.0
for _ in range(60):
    mid = (lo + hi) / 2
    if fits(tgt + dvec * mid, tgt, 35.0, 0.07):
        hi = mid
    else:
        lo = mid
shoot("hero", tgt + dvec * hi, tgt, 35.0)

# eye: 28 mm, camera at 1.7 m, three-quarter from the other side of the entrance normal (30 deg right),
# so the sun-lit side wall shows; aim point at 40 % of the height
hd = rot(ent_dir, 30.0)
tz = GROUND_Z + 0.42 * H
lo, hi = 1.0, 600.0
for _ in range(60):
    mid = (lo + hi) / 2
    p = Vector((tgt.x + hd.x * mid, tgt.y + hd.y * mid, GROUND_Z + 1.7))
    t = Vector((tgt.x, tgt.y, tz))
    if fits(p, t, 28.0, 0.06):
        hi = mid
    else:
        lo = mid
shoot("eye", Vector((tgt.x + hd.x * hi, tgt.y + hd.y * hi, GROUND_Z + 1.7)), Vector((tgt.x, tgt.y, tz)), 28.0)
