"""Order-independent per-object fingerprint of a kit .blend (verification helper, 4_verify; reads only).

Usage: <bpy-python> canon_hash.py <file.blend> <out.json>

For every rendered mesh object: the ordered geometry hash (same recipe as tools/geom_hash.py) AND a canonical hash
that ignores vertex order and polygon order (each polygon is rotated to start at its lexicographically smallest
vertex, then rows are sorted).  The canonical uv / mask hashes follow the same rotation, so a pure polygon-order
change shows up as: ordered differs, canonical identical.
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


def canon(o):
    me = o.data
    nv, nl, npo = len(me.vertices), len(me.loops), len(me.polygons)
    co = np.zeros(nv * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    co = np.round(co, 5)
    lv = np.zeros(nl, np.int64)
    me.loops.foreach_get("vertex_index", lv)
    ps = np.zeros(npo, np.int64)
    me.polygons.foreach_get("loop_start", ps)
    pt = np.zeros(npo, np.int64)
    me.polygons.foreach_get("loop_total", pt)
    pm = np.zeros(npo, np.int64)
    me.polygons.foreach_get("material_index", pm)
    mats = [m.name if m else "-" for m in me.materials]
    # vertex rank by rounded coordinate (identical coordinates share a rank)
    _, rank = np.unique(co, axis=0, return_inverse=True)
    rank = rank.ravel()
    uv = np.zeros((nl, 2))
    if me.uv_layers.active:
        u = np.zeros(nl * 2)
        me.uv_layers.active.data.foreach_get("uv", u)
        uv = np.round(u.reshape(-1, 2), 5)
    mk = np.zeros((nl, 4))
    ca = me.color_attributes.get("Mask")
    if ca is not None and ca.domain == "CORNER":
        c = np.zeros(len(ca.data) * 4)
        ca.data.foreach_get("color", c)
        mk = np.round(c.reshape(-1, 4), 4)
    geo_rows, uv_rows, mk_rows = [], [], []
    for k in np.unique(pt):
        sel = np.nonzero(pt == k)[0]
        L = ps[sel][:, None] + np.arange(k)[None, :]            # (m, k) loop indices
        R = rank[lv[L]]
        st = np.argmin(R, axis=1)
        rot = (st[:, None] + np.arange(k)[None, :]) % k
        Lr = np.take_along_axis(L, rot, axis=1)
        Rr = rank[lv[Lr]]
        matid = np.array([hash_name(mats[i] if i < len(mats) else "-") for i in pm[sel]], np.int64)
        g = np.column_stack([np.full(len(sel), k), matid, Rr])
        geo_rows.append((k, g, uv[Lr].reshape(len(sel), -1), mk[Lr].reshape(len(sel), -1)))
    # canonical: sort polygons by their geometry row (per size group, groups in size order)
    parts_g, parts_u, parts_m = [], [], []
    for k, g, u, m in geo_rows:
        order = np.lexsort(g.T[::-1])
        parts_g.append(g[order]); parts_u.append(u[order]); parts_m.append(m[order])
    vsorted = co[np.lexsort(co.T[::-1])]
    return dict(geom=_h(vsorted, *parts_g), uv=_h(*parts_u), mask=_h(*parts_m))


_NAMES = {}


def hash_name(s):
    if s not in _NAMES:
        _NAMES[s] = int(hashlib.sha1(s.encode()).hexdigest()[:12], 16)
    return _NAMES[s]


def main(path, out):
    bpy.ops.wm.open_mainfile(filepath=path)
    res = {"file": path, "objects": {}}
    for o in sorted((o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render),
                    key=lambda o: o.name):
        me = o.data
        me.calc_loop_triangles()
        d = canon(o)
        d["tris"] = len(me.loop_triangles)
        d["nv"] = len(me.vertices)
        d["np"] = len(me.polygons)
        res["objects"][o.name] = d
    obj = res["objects"]
    res["triangles"] = int(sum(v["tris"] for v in obj.values()))
    for ch in ("geom", "uv", "mask"):
        res["canon_" + ch] = _h(np.frombuffer("".join(f"{k}:{v[ch]}" for k, v in obj.items()).encode(), np.uint8))
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print("CANON", json.dumps({k: res[k] for k in ("file", "triangles", "canon_geom", "canon_uv", "canon_mask")}))


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(a[0], a[1])
