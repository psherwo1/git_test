import bpy, json, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
J = json.load(open(argv[0]))
names = set(argv[1].split(","))
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
for a in J["anchors"]:
    if a["name"] not in names:
        continue
    p = Vector(a["position"]); n = Vector(a["normal"]).normalized(); up = Vector(a["up"]).normalized()
    rt = up.cross(n).normalized(); w, h = a["size"]
    print("ANCHOR", a["name"], a["surface"], "up", [round(x, 2) for x in up])
    for j in (1, 0, -1):
        row = []
        for i in (-1, 0, 1):
            q = p + rt * (i * 0.45 * w) + up * (j * 0.45 * h)
            hh, ll, nn, ff, oo, _ = scn.ray_cast(dg, q + n * 0.15, -n, distance=0.6)
            if hh:
                s = oo.material_slots[oo.data.polygons[ff].material_index].material.name
                row.append(f"{oo.name[4:]}:{s[2:]}:d{(ll-q).dot(n)*100:+.1f}cm:n{nn.dot(n):.2f}")
            else:
                row.append("MISS")
        print("  ", " | ".join(row))
