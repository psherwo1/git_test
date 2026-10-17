"""village_kit.mask -- THE one writer of the mandatory `Mask` colour attribute (producer note 9).

Every mesh of every kit building gets its Mask through write_mask().  Layout:
    R  per-piece random 0-1   constant over one piece (stone, shingle, plank, rod, clump), differs between neighbours
    G  per-piece wear 0-1     high on chipped / split / slipped / weathered / replaced pieces, low on fresh dressed work
    B  moss / dirt / damp 0-1 per vertex: high near the ground and plinths, on up-facing ledges and roof butts, on
                              north (+Y) faces; low on sheltered vertical faces high up
    A  1.0 (reserved)
Domain CORNER, type BYTE_COLOR, set as the active AND the default (render) colour attribute so it exports to Unreal
as vertex colour.  Values are written raw (color_srgb), i.e. the stored byte is round(value * 255): the channels
are data, not colours.

Where the per-piece values come from (in priority order):
  1. explicit arrays r / g (per vertex) passed to write_mask();
  2. the point attributes `_mask_r` / `_mask_g` that core.Acc attaches per add() call (one call = one piece);
     they survive validate() and the Nanite clean-up and are removed after use;
  3. mesh islands (connected components): R = hash(island), G = material wear base + spread * hash(island)
     (the keep's round-4 scheme) -- used for meshes built without an Acc.
"""
import numpy as np

# per-material wear defaults for island-derived G: (base, spread)
WEAR_BY_MAT = {"M_stone_dressed": (0.08, 0.25), "M_iron": (0.25, 0.35), "M_lead": (0.1, 0.2),
               "M_timber": (0.15, 0.4), "M_timber_weathered": (0.35, 0.45), "M_roof_shingle": (0.2, 0.5),
               "M_roof_shake": (0.25, 0.5), "M_thatch": (0.25, 0.45), "M_mortar": (0.2, 0.3)}


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def default_b(V, VN):
    """moss / dirt / damp (B): high near the ground and on the plinth, on up-facing ledges and roof butts, on
    shaded north faces; low on sheltered vertical faces under an eave.  World-space V (metres, ground Z = 0)."""
    from .core import n2
    z = V[:, 2]
    ground = np.clip(1.0 - z / 0.7, 0, 1) ** 1.5
    up = np.clip(VN[:, 2], 0, 1)
    north = np.clip(VN[:, 1], 0, 1) * 0.25
    high = smoothstep(0.9, 2.6, z) * (1 - smoothstep(2.6, 3.2, z))      # sheltered wall under the eave
    b = np.maximum(ground, 0.45 * up) + north - 0.2 * high
    return np.clip(b + 0.06 * n2(V[:, 0] * 2.0, V[:, 1] * 2.0 + z, 77), 0, 1)


def _hash01(x, seed=0.0):
    x = np.asarray(x, np.float64)
    v = np.sin(x * 12.9898 + seed * 78.233 + 0.5) * 43758.5453
    return v - np.floor(v)


def island_labels(nv, edges):
    """connected components of a mesh (label = smallest vertex index of the island)."""
    lab = np.arange(nv, dtype=np.int64)
    if len(edges) == 0:
        return lab
    a, b = edges[:, 0], edges[:, 1]
    for _ in range(400):
        m = np.minimum(lab[a], lab[b])
        new = lab.copy()
        np.minimum.at(new, a, m)
        np.minimum.at(new, b, m)
        for _ in range(6):
            new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def _island_rg(me, seed):
    nv = len(me.vertices)
    ed = np.zeros(len(me.edges) * 2, np.int32)
    me.edges.foreach_get("vertices", ed)
    lab = island_labels(nv, ed.reshape(-1, 2).astype(np.int64))
    r = _hash01(lab, seed)
    wu = _hash01(lab, seed + 3.1)
    # wear base per vertex from the material of any polygon using it
    pm = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", pm)
    lt = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", lv)
    vm = np.zeros(nv, np.int32)
    vm[lv] = np.repeat(pm, lt)
    names = [m.name if m else "" for m in me.materials]
    gb, gs = np.full(nv, 0.15), np.full(nv, 0.45)
    for i, nm in enumerate(names):
        b0, sp = WEAR_BY_MAT.get(nm, (0.15, 0.45))
        sel = vm == i
        gb[sel], gs[sel] = b0, sp
    return r, np.clip(gb + gs * wu ** 1.6, 0, 1)


def write_mask(me, r=None, g=None, b=None, b_fn=None, moss=None, seed=0.0):
    """write the `Mask` attribute on mesh `me` (see module doc).  r, g, b: optional per-vertex arrays; b_fn(V, VN)
    -> per-vertex B; moss: constant B (pooled parts whose world position is not known).  Idempotent: an existing
    Mask is replaced."""
    nv = len(me.vertices)
    nl = len(me.loops)
    if "Mask" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["Mask"])
    if nv == 0 or nl == 0:
        ca = me.color_attributes.new("Mask", "BYTE_COLOR", "CORNER")
        me.color_attributes.active_color_name = "Mask"
        me.color_attributes.default_color_name = "Mask"
        return
    if r is None or g is None:
        if "_mask_r" in me.attributes and "_mask_g" in me.attributes:
            r_ = np.zeros(nv, np.float32)
            g_ = np.zeros(nv, np.float32)
            me.attributes["_mask_r"].data.foreach_get("value", r_)
            me.attributes["_mask_g"].data.foreach_get("value", g_)
        else:
            r_, g_ = _island_rg(me, seed)
        r = r_ if r is None else r
        g = g_ if g is None else g
    for nm_ in ("_mask_r", "_mask_g"):
        if nm_ in me.attributes:
            me.attributes.remove(me.attributes[nm_])
    if b is None:
        if moss is not None:
            b = np.full(nv, float(moss))
        else:
            V = np.zeros(nv * 3, np.float32)
            me.vertices.foreach_get("co", V)
            VN = np.zeros(nv * 3, np.float32)
            me.vertex_normals.foreach_get("vector", VN)
            b = (b_fn or default_b)(V.reshape(-1, 3).astype(float), VN.reshape(-1, 3).astype(float))
    li = np.zeros(nl, np.int32)
    me.loops.foreach_get("vertex_index", li)
    col = np.stack([np.asarray(r)[li], np.asarray(g)[li], np.asarray(b)[li], np.ones(nl)], -1)
    ca = me.color_attributes.new("Mask", "BYTE_COLOR", "CORNER")
    ca.data.foreach_set("color_srgb", np.clip(col, 0, 1).astype(np.float32).ravel())
    me.color_attributes.active_color_name = "Mask"
    me.color_attributes.default_color_name = "Mask"


def has_mask(me):
    return "Mask" in me.color_attributes


# ---- kit 1.10.0: no moss on walked steps (the client-approved queued UV fix, item 3) ---------------------------
WALK_B = 0.04            # stored as byte 10 (0.039): at or under the 0.05 limit after BYTE_COLOR quantisation
WALK_SIDE = 0.10         # the walking zone: clear width + 0.10 m each side ...
WALK_OUT = 1.50          # ... from the wall face to 1.5 m out ...
WALK_IN = 1.00           # ... and back through the opening (threshold / sill inside the reveal) ...
WALK_Z = (-0.30, 0.90)   # ... at foot level (relative to the entrance origin)
WALK_UP = 0.70           # up-facing tops only: n.z above this (step fronts, ends and outer edges keep their B)


def walk_zone_faces(centres, normals, ent):
    """bool per face: an up-facing top inside entrance `ent`'s walking zone (guards entrance dict: origin, out
    (horizontal unit), width = clear width)."""
    O = np.asarray(ent["origin"], float)
    if O.shape == (2,):
        O = np.array([O[0], O[1], 0.0])
    out = np.asarray(ent["out"], float)[:2]
    out = out / max(float(np.linalg.norm(out)), 1e-9)
    t = np.array([-out[1], out[0]])
    d = centres[:, :2] - O[:2]
    a, c = d @ out, d @ t
    dz = centres[:, 2] - O[2]
    return ((np.abs(c) <= ent["width"] / 2 + WALK_SIDE) & (a >= -WALK_IN) & (a <= WALK_OUT) &
            (dz >= WALK_Z[0]) & (dz <= WALK_Z[1]) & (normals[:, 2] > WALK_UP))


def clear_walked_tops(objects, entrances, b_walk=WALK_B, log=None):
    """Mask B <= b_walk on every up-facing top (threshold, step, door sill, the floor through the opening) inside
    each entrance's walking zone, so the moss layer never lands where feet go.  Only those faces' corners change
    (CORNER domain): the step's front, ends and outer edges keep their moss.  Pooled (shared) meshes are skipped
    (their tops are not walked: nails, pegs).  objects: the building's objects (world coordinates); entrances:
    guards entrance dicts in world coordinates.  Returns [(entrance, object, faces)]."""
    done = []
    if not entrances:
        return done
    for o in sorted((o for o in objects if o.type == "MESH"), key=lambda o: o.name):
        me = o.data
        if me.users > 1 or len(me.polygons) == 0 or "Mask" not in me.color_attributes:
            continue
        ca = me.color_attributes["Mask"]
        if ca.domain != "CORNER":
            continue
        npg, nl = len(me.polygons), len(me.loops)
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        Mw = np.array(o.matrix_world)
        co = co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]
        lt = np.empty(npg, np.int64)
        me.polygons.foreach_get("loop_total", lt)
        lv = np.empty(nl, np.int64)
        me.loops.foreach_get("vertex_index", lv)
        lp = np.repeat(np.arange(npg), lt)
        cen = np.zeros((npg, 3))
        np.add.at(cen, lp, co[lv])
        cen /= lt[:, None]
        nrm = np.empty(npg * 3)
        me.polygons.foreach_get("normal", nrm)
        nrm = nrm.reshape(-1, 3) @ Mw[:3, :3].T
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-30)
        hit = np.zeros(npg, bool)
        for e in entrances:
            z = walk_zone_faces(cen, nrm, e)
            if z.any():
                done.append((e["name"], o.name, int(z.sum())))
                hit |= z
        if not hit.any():
            continue
        prop = "color_srgb" if ca.data_type == "BYTE_COLOR" else "color"
        col = np.empty(nl * 4, np.float32)
        ca.data.foreach_get(prop, col)
        col = col.reshape(-1, 4)
        hl = hit[lp]
        col[hl, 2] = np.minimum(col[hl, 2], b_walk)
        ca.data.foreach_set(prop, col.ravel())
    if log:
        for en, on, nf in done:
            log(f"  walked tops (Mask B <= {b_walk}): {en} -> {on}: {nf} faces")
    return done
