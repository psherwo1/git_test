"""Follow-ups: visibility of the 3 loose islands, deep body-wall verts, low-z leak test, door clearance (from 0.3 m),
then 6 small close-up renders of the junction (eye level and 6 m)."""
import json, math, os, sys
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
exec(open(os.path.join(HERE, "a2_measure.py")).read().split("# ---- A.")[0])   # load blend, MESH, BVH, helpers

def cams():
    out = []
    for s in (-1, 1):
        for x in (-3.0, -1.0, 1.0, 3.0, 5.0):
            for d in (3.0, 5.0, 8.0, 12.0):
                out.append((x, s * d, 1.6)); out.append((x, s * d, 6.0))
    for x in (-14.0, -10.0):
        out.append((x, 0.0, 6.0)); out.append((x, 3.0, 6.0)); out.append((x, -3.0, 6.0))
    return [Vector(c) for c in out]
CAMS = cams()
def visible(P, eps=0.02):
    n = 0
    for c in CAMS:
        dv = Vector(P) - c
        h = BVH.ray_cast(c, dv.normalized(), dv.length + 0.01)
        if h[0] is not None and (h[0] - Vector(P)).length < eps:
            n += 1
    return n
out = {}
# islands: all verts of the island around the reported centre
for n, cen in (("LONG_body_roof_covering", (1.321, 2.204, 3.546)), ("LONG_body_roof_ridge", (0.658, -0.006, 5.474)),
               ("LONG_purlin_rings", (2.499, 2.478, 6.828))):
    V = MESH[n][0]
    ids = np.where(np.linalg.norm(V - np.array(cen), axis=1) < 0.35)[0]
    vis = [visible(V[i]) for i in ids]
    out[n] = dict(n=len(ids), verts_visible=int(sum(1 for k in vis if k)), max_cams=int(max(vis) if vis else 0),
                  bbox=[np.round(V[ids].min(0), 3).tolist(), np.round(V[ids].max(0), 3).tolist()])
# deep body-wall verts
for n in ("LONG_body_wall_stones", "LONG_body_wall_mortar"):
    V = MESH[n][0]
    r = np.hypot(V[:, 0] - C[0], V[:, 1] - C[1]); d = R(V[:, 2]) - r
    ids = np.where(d > 0.05)[0]
    vis = [visible(V[i]) for i in ids]
    out[n + "_deep>5cm"] = dict(n=len(ids), visible=int(sum(1 for k in vis if k)))
# low-z leak test (z 0.05..2.0) on the body side of the drum
leaks = 0; rays = 0; ex = []
for azd in np.arange(110.0, 250.01, 1.0):
    a = math.radians(azd)
    nrm = Vector((math.cos(a), math.sin(a), 0.0))
    for z in np.arange(0.05, 2.0, 0.025):
        rr = float(R(z)) - 0.02
        P = Vector((C[0] + rr * math.cos(a), C[1] + rr * math.sin(a), z))
        for c in CAMS:
            dv = P - c; L = dv.length; dn = dv.normalized()
            if nrm.dot(-dn) < 0.15:
                continue
            rays += 1
            h = BVH.ray_cast(c, dn, L + 1.0)
            if h[0] is None:
                leaks += 1; ex.append((azd, z, "sky")); continue
            if h[3] < L - 0.06:
                continue
            q = np.array(h[0]); dq = float(R(q[2]) - np.hypot(q[0] - C[0], q[1] - C[1]))
            if dq > 0.08 or h[3] > L + 0.05:
                leaks += 1; ex.append((azd, round(float(z), 3), OWNER[h[2]], round(dq, 3)))
out["lowz_leaks"] = dict(rays=rays, leaks=leaks, examples=ex[:10])
# door
ent = json.loads(bpy.context.scene["kit_entrances"])[0]
o = np.array(ent["origin"]); ov = np.array(ent["out"]); sd = np.array([-ov[1], ov[0], 0.0])
door = []
for s in np.linspace(-0.5, 0.5, 11):
    for t in (0.05, 0.3, 0.6, 1.0, 1.5):
        P = o + sd * s + ov * t
        h = BVH.ray_cast(Vector((P[0], P[1], 0.3)), Vector((0, 0, 1)), 10.0)
        door.append((round(h[0][2], 3) if h[0] is not None else 99.0, round(float(s), 2), t, OWNER[h[2]] if h[0] is not None else None))
door.sort()
out["door_overhead_min"] = door[:4]
blk = []
for s in np.linspace(-0.45, 0.45, 10):
    for z in np.arange(0.3, 2.11, 0.1):
        P0 = o + sd * s + ov * 2.0
        h = BVH.ray_cast(Vector((P0[0], P0[1], z)), Vector(tuple(-ov)), 3.0)
        if h[0] is not None and h[3] < 2.0 - 0.12:
            blk.append((round(float(s), 2), round(float(z), 2), round(h[3], 3), OWNER[h[2]]))
out["door_approach_blocked"] = blk[:10]
json.dump(out, open(os.path.join(HERE, "followup.json"), "w"), indent=1, default=str)
print("FOLLOWUP", json.dumps(out, default=str))

# ---- close-up renders -----------------------------------------------------------------------------------------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 24
sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"; pr.get_devices()
    for d in pr.devices:
        d.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU fallback", e)
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
if sc.world is None:
    sc.world = bpy.data.worlds.new("W")
sc.world.color = (0.55, 0.6, 0.68)
if not any(o.type == "LIGHT" for o in sc.objects):
    ld = bpy.data.lights.new("sun", "SUN"); ld.energy = 3.5
    lo = bpy.data.objects.new("sun", ld); sc.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(50), 0, math.radians(-140))
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.05))
cam_d = bpy.data.cameras.new("auditcam"); cam = bpy.data.objects.new("auditcam", cam_d); sc.collection.objects.link(cam)
sc.camera = cam
def shot(name, loc, tgt, lens=35):
    cam.location = loc; cam_d.lens = lens
    d = Vector(tgt) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(HERE, name + ".png")
    bpy.ops.render.render(write_still=True)
J_S = (2.9, -3.2, 2.8); J_N = (2.9, 3.2, 2.8); J_R = (1.05, 0.0, 5.5)
shot("a01_s_eave_end_eye", (-0.5, -7.5, 1.6), J_S, 40)
shot("a02_n_eave_end_eye", (-0.5, 7.5, 1.6), J_N, 40)
shot("a03_s_slope_6m", (-3.0, -7.0, 6.0), (1.8, -1.6, 4.2), 35)
shot("a04_n_slope_6m", (-3.0, 7.0, 6.0), (1.8, 1.6, 4.2), 35)
shot("a05_ridge_gable_6m", (-6.0, 1.5, 6.5), J_R, 50)
shot("a06_s_eave_lookup", (1.2, -4.6, 1.6), (3.0, -3.1, 2.7), 28)
print("RENDERS DONE")
