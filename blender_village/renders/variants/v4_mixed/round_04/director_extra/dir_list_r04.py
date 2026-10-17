import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
names = sorted(o.name for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(("V4M_pool", "V4H_pool")))
print("MESHES", len(names))
print(" | ".join(n for n in names if "_kit_" not in n)[:6000])
