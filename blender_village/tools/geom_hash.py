"""Geometry fingerprint of a building .blend, to prove a kit refactor is behaviour-preserving.

Usage:
    <python-with-bpy> blender_village/tools/geom_hash.py <file.blend> [<out.json>]

For every rendered mesh object (sorted by name) it hashes, separately:
- geometry: world-space vertex positions rounded to 0.01 mm plus the polygon vertex lists and material names;
- uv: the active UV map, rounded to 1e-5;
- mask: the `Mask` colour attribute, rounded to 1e-4.
It prints one JSON object: total triangles, an overall hash per channel, and per-object entries, so that a
refactor can show "geometry identical" while a UV-only fix shows "geometry identical, uv changed".
"""
import hashlib
import json
import sys

import bpy
import numpy as np


def _h(*arrays):
    m = hashlib.sha1()
    for a in arrays:
        m.update(np.ascontiguousarray(a).tobytes())
    return m.hexdigest()[:16]


def fingerprint(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {"file": path, "objects": {}}
    tris_total = 0
    for o in sorted((o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render),
                    key=lambda o: o.name):
        me = o.data
        me.calc_loop_triangles()
        n_t = len(me.loop_triangles)
        tris_total += n_t
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
        co = np.round(co, 5)
        pv = np.zeros(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", pv)
        ps = np.zeros(len(me.polygons), np.int64)
        me.polygons.foreach_get("loop_start", ps)
        mats = ",".join(m.name if m else "-" for m in me.materials).encode()
        geo = _h(co, pv, ps, np.frombuffer(mats, np.uint8))
        uv_h = "-"
        if me.uv_layers.active:
            uv = np.zeros(len(me.loops) * 2)
            me.uv_layers.active.data.foreach_get("uv", uv)
            uv_h = _h(np.round(uv, 5))
        mask_h = "-"
        ca = me.color_attributes.get("Mask")
        if ca is not None:
            c = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", c)
            mask_h = _h(np.round(c, 4))
        out["objects"][o.name] = {"tris": n_t, "geometry": geo, "uv": uv_h, "mask": mask_h}
    obj = out["objects"]
    out["triangles"] = tris_total
    for ch in ("geometry", "uv", "mask"):
        out[ch] = _h(np.frombuffer("".join(f"{k}:{v[ch]}" for k, v in obj.items()).encode(), np.uint8))
    return out


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    res = fingerprint(args[0])
    if len(args) > 1:
        with open(args[1], "w") as f:
            json.dump(res, f, indent=1)
    print("GEOM_HASH", json.dumps({k: res[k] for k in ("file", "triangles", "geometry", "uv", "mask")}))
