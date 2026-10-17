"""Read-only: which object / material is seen at given pixels of a lookdev shot.
Usage: python.exe -I pick_pixel.py <lookdev.blend> <CAM_name> x,y [x,y ...]   (x right, y down, 1920x1080 pixels)"""
import sys

import bpy
from mathutils import Vector

path, cam_name = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=path)
sc = bpy.context.scene
cam = sc.objects[cam_name]
dg = bpy.context.evaluated_depsgraph_get()
W, H = 1920, 1080
cd = cam.data
half_w = cd.sensor_width / 2 / cd.lens
for xy in sys.argv[3:]:
    x, y = map(float, xy.split(","))
    nx = (x + 0.5) / W * 2 - 1
    ny = 1 - (y + 0.5) / H * 2
    d_cam = Vector((nx * half_w, ny * half_w * H / W, -1.0))
    d = (cam.matrix_world.to_3x3() @ d_cam).normalized()
    hit, loc, nrm, fi, ob, _ = sc.ray_cast(dg, cam.matrix_world.translation, d)
    if not hit:
        print("PICK", xy, "sky")
        continue
    me = ob.data
    mat = "-"
    if fi < len(me.polygons):
        mi = me.polygons[fi].material_index
        mat = me.materials[mi].name if mi < len(me.materials) and me.materials[mi] else "-"
    print("PICK", xy, ob.name, mat, tuple(round(v, 2) for v in loc), "n", tuple(round(v, 2) for v in nrm))
