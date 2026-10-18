import os
import bpy
from mathutils import Vector

ROOT = r"C:\GitHubDesktop\git_test\blender_village\lookdev\village_r2\work"
for bid in ["hilltop_keep", "v4_mixed", "v5_harbour_house"]:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, bid + "_lookdev.blend"))
    scn = bpy.context.scene
    em = [o for o in scn.objects if o.type == "EMPTY"]
    print("EMPTIES", bid, len(em), [(o.name, o.instance_type, o.instance_collection.name if o.instance_collection else None, o.hide_render) for o in em[:8]], flush=True)
    print("SCENECOLS", bid, [(c.name, c.hide_render, len(c.objects)) for c in scn.collection.children_recursive][:20], flush=True)
    doors = [o for o in scn.objects if o.type == "MESH" and "door" in o.name.lower() and not o.hide_render]
    for o in doors[:12]:
        p = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print("DOOR", bid, o.name, [round(sum(q[i] for q in p) / 8, 2) for i in range(3)], flush=True)
    hid = [o.name for o in scn.objects if o.type == "MESH" and o.hide_render and not o.name.startswith("DA_")]
    print("HIDDENMESH", bid, hid[:20], flush=True)
