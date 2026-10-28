"""round 5: which object / face a review-shot pixel hits, and whether it is a back face.
python -I pick_r05.py <blend> sx,sy  locx,locy,locz  tx,ty,tz  lens  px,py [px,py ...]   (plan coords + shift)"""
import sys

import bpy
from mathutils import Vector

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=argv[0])
    sx, sy = (float(v) for v in argv[1].split(","))
    loc = Vector([float(v) for v in argv[2].split(",")]) + Vector((sx, sy, 0))
    tgt = Vector([float(v) for v in argv[3].split(",")]) + Vector((sx, sy, 0))
    lens = float(argv[4])
    scn = bpy.context.scene
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    scn.render.resolution_x, scn.render.resolution_y = 1280, 720
    bpy.context.view_layer.update()
    fr = cam.data.view_frame(scene=scn)          # tr, br, bl, tl (camera space)
    tr, br, bl, tl = fr
    M = cam.matrix_world
    dg = bpy.context.evaluated_depsgraph_get()
    for pp in argv[5:]:
        px, py = (float(v) for v in pp.split(","))
        u, v = px / 1280.0, py / 720.0
        top = tl.lerp(tr, u)
        bot = bl.lerp(br, u)
        p = top.lerp(bot, v)
        d = (M.to_3x3() @ p).normalized()
        hit, co, n, idx, ob, _ = scn.ray_cast(dg, M.translation, d)
        if not hit:
            print("PICK", pp, "miss")
            continue
        back = n.dot(d) > 0
        print(f"PICK {pp} {ob.name} face {idx} at {tuple(round(c - s, 3) for c, s in zip(co, (sx, sy, 0)))} "
              f"{'BACK' if back else 'front'}")
