"""Ray-trace given pixels of a director shot (same camera as dir_render_r06.py): list every surface the ray crosses.
blender -b --python dir_raypix_r06.py -- <blend> <loc xyz> <tgt xyz> <lens> <px py (from top)> ..."""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
loc = Vector(map(float, a[1:4])); tgt = Vector(map(float, a[4:7])); lens = float(a[7]); pts = list(map(float, a[8:]))
scn = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
rot = (tgt - loc).to_track_quat("-Z", "Y").to_matrix()
W, H, sw = 1280, 720, 36.0
for i in range(0, len(pts), 2):
    px, py = pts[i] + 0.5, pts[i + 1] + 0.5
    x = (px / W - 0.5) * sw; y = (0.5 - py / H) * sw * H / W
    d = (rot @ Vector((x, y, -lens))).normalized()
    o = loc.copy(); hits = []
    for _ in range(8):
        ok, p, n, idx, ob, _m = scn.ray_cast(dg, o, d)
        if not ok:
            hits.append("MISS"); break
        hits.append(f"{ob.name}@({p.x:.3f},{p.y:.3f},{p.z:.3f}) t={(p-loc).length:.3f} {'front' if n.dot(d) < 0 else 'BACK'}")
        o = p + d * 1e-4
    print("PIX", pts[i], pts[i+1], " | ".join(hits))
