"""Village lineup scene for the Art Director's ensemble review.

Run:  /opt/bpyenv/bin/python -I blender_village/scene/assemble_lineup.py
Saves blender_village/scene/village_lineup.blend next to this script.

Appends (never links, never edits) the single top-level collection of each hero
building .blend and stands them side by side with ~8 m clear gaps between their
yawed footprints, composed like the ref2 / ref3 village:

  * the wattle roundhut on the left and forward (ref2 foreground hut),
  * the hilltop keep in the middle, set back a little (ref2 centre),
  * the tower windmill on the right and furthest back (mills stand on the
    village edge in ref2 / ref3).

All doors face roughly -Y toward a shared lane (the review cameras' side), each
building yawed a few degrees toward the middle of the group so the line reads as
a street rather than a catalogue row.

Producer note 10: no ground, path, apron or loose-stone dressing is added here;
only the buildings' own geometry is placed. Ground stays at Z = 0.
Mesh data shared inside each building stays shared (objects are transformed,
data is not copied or applied).
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "village_lineup.blend")

GAP = 8.0  # clear metres between neighbouring footprints along X

# Left -> right. (building id, top-level collection, yaw deg, Y offset m)
LINEUP = [
    ("wattle_roundhut", "HUT", 14.0, -3.0),
    ("hilltop_keep", "KEEP", 4.0, 1.5),
    ("tower_windmill", "MILL", -28.0, 5.0),
]


def append_collection(blend_path, coll_name):
    with bpy.data.libraries.load(blend_path, link=False) as (src, dst):
        if coll_name not in src.collections:
            raise RuntimeError(f"{coll_name} not found in {blend_path}: {list(src.collections)}")
        dst.collections = [coll_name]
    coll = dst.collections[0]
    bpy.context.scene.collection.children.link(coll)
    return coll


def merge_palette_duplicates():
    """Each building carries its own copy of the shared palette; appending makes
    M_daub.001, M_daub.002 ... Remap them onto one material per palette slot so the
    ensemble uses the same <= 15 slots as each building."""
    for mat in list(bpy.data.materials):
        base, dot, suffix = mat.name.rpartition(".")
        if dot and suffix.isdigit() and base in bpy.data.materials:
            mat.user_remap(bpy.data.materials[base])
            bpy.data.materials.remove(mat)


def footprint_x(objs, m):
    """X extent of the objects' bound boxes after transform m (conservative)."""
    lo, hi = 1e9, -1e9
    for o in objs:
        if o.type not in {"MESH", "CURVE"}:
            continue
        for c in o.bound_box:
            x = (m @ o.matrix_world @ Vector(c)).x
            lo, hi = min(lo, x), max(hi, x)
    return lo, hi


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.name = "village_lineup"
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0

    cursor_x = None
    placed = []
    for bid, cname, yaw, y_off in LINEUP:
        path = os.path.join(ROOT, "buildings", bid, f"{bid}.blend")
        coll = append_collection(path, cname)
        objs = list(coll.all_objects)
        rot = Matrix.Rotation(math.radians(yaw), 4, "Z")
        lo, hi = footprint_x(objs, rot)
        x = 0.0 if cursor_x is None else cursor_x + GAP - lo
        m = Matrix.Translation((x, y_off, 0.0)) @ rot
        for o in objs:
            if o.parent is None:  # children follow their parent
                o.matrix_world = m @ o.matrix_world
        cursor_x = x + hi
        placed.append((cname, x, y_off, yaw, len(objs)))

    merge_palette_duplicates()

    # Centre the whole group on the origin in X (ground untouched at Z = 0)
    allobjs = [o for o in scn.objects if o.type in {"MESH", "CURVE"}]
    lo, hi = footprint_x(allobjs, Matrix.Identity(4))
    shift = Matrix.Translation((-(lo + hi) / 2, 0.0, 0.0))
    for o in scn.objects:
        if o.parent is None:
            o.matrix_world = shift @ o.matrix_world

    for cname, x, y, yaw, n in placed:
        print(f"LINEUP {cname}: x={x - (lo + hi) / 2:+.2f} y={y:+.2f} yaw={yaw:+.1f} objects={n}")
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    print("MATERIALS", len(bpy.data.materials), sorted(m.name for m in bpy.data.materials))
    print("SAVED", OUT)


if __name__ == "__main__":
    main()
