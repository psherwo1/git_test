"""Exact loose islands (covering / ridge / purlin) -> visibility from outside-drum cameras, + 2 close-ups."""
import json, math, os
import bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "a2_measure.py")).read().split("# ---- A.")[0])
CAMS = []
for s in (-1, 1):
    for x in (-3.0, -1.0, 1.0, 3.0, 5.0):
        for d in (5.0, 8.0, 12.0):
            for z in (1.6, 6.0):
                c = (x, s * d, z)
                if math.hypot(x - C[0], s * d) > 4.6:
                    CAMS.append(Vector(c))
for x in (-14.0, -10.0):
    for y in (0.0, 3.0, -3.0):
        CAMS.append(Vector((x, y, 6.0)))
def islands(V, T):
    p = np.arange(len(V))
    def f(i):
        while p[i] != i:
            p[i] = p[p[i]]; i = p[i]
        return i
    for a, b, c in T:
        ra = f(a); p[f(b)] = ra; p[f(c)] = ra
    return np.array([f(i) for i in range(len(V))])
out = {}
for n, cen in (("LONG_body_roof_covering", (1.321, 2.204, 3.546)), ("LONG_body_roof_ridge", (0.658, -0.006, 5.474)),
               ("LONG_purlin_rings", (2.499, 2.478, 6.828))):
    V, T, _ = MESH[n]
    roots = islands(V, T)
    best = None
    for r in np.unique(roots):
        ids = np.where(roots == r)[0]
        dc = np.linalg.norm(V[ids].mean(0) - np.array(cen))
        if best is None or dc < best[0]:
            best = (dc, ids)
    ids = best[1]
    seen = 0; hits = {}
    for i in ids:
        P = Vector(V[i]); k = 0
        for c in CAMS:
            dv = P - c
            h = BVH.ray_cast(c, dv.normalized(), dv.length + 0.01)
            if h[0] is not None:
                hits[OWNER[h[2]]] = hits.get(OWNER[h[2]], 0) + 1
                if (h[0] - P).length < 0.01 and OWNER[h[2]] == n:
                    k += 1
        seen += k > 0
    out[n] = dict(n_verts=len(ids), verts_seen=int(seen), bbox=[np.round(V[ids].min(0), 3).tolist(), np.round(V[ids].max(0), 3).tolist()],
                  first_hits=hits)
print("ISLANDS", json.dumps(out))
json.dump(out, open(os.path.join(HERE, "islands.json"), "w"), indent=1)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.use_denoising = True
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
ld = bpy.data.lights.new("sun", "SUN"); ld.energy = 3.5
lo = bpy.data.objects.new("sun", ld); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(50), 0, math.radians(-140))
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, tgt, lens):
    cam.location = loc; cd.lens = lens
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(HERE, name + ".png"); bpy.ops.render.render(write_still=True)
shot("a07_n_island_tele", (-1.0, 7.0, 6.0), (1.32, 2.2, 3.55), 85)
shot("a08_ridge_end_tele", (-3.0, 4.0, 6.5), (0.8, 0.0, 5.45), 85)
print("DONE")
