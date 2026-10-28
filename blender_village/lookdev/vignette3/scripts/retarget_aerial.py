import bpy,sys,math
from mathutils import Vector
bl=r"C:\GitHubDesktop\git_test\blender_village\lookdev\vignette3\vignette3.blend"
bpy.ops.wm.open_mainfile(filepath=bl)
c=bpy.data.objects["CAM_aerial"]
c.location=(48,-100,46); c.rotation_euler=(Vector((-2,175,8))-c.location).to_track_quat("-Z","Y").to_euler(); c.data.lens=26
bpy.ops.wm.save_as_mainfile(filepath=bl)
