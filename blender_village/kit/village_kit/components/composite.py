"""components.composite -- assembly helpers for buildings combined from several kit bodies (a round end + a linear
body, a tower + an annex ...) (kit, variant v3_longhouse_roundend).

    cone_roof(g, seed, structure_seeds)   KIT COMPONENT: the round frame's conical shingle roof (rafters + hub,
                                          purlin / batten rings, doubled starter + chunky shingle courses, blocker;
                                          components.conical_roof) WITHOUT the hut's daub eave closure, for a round
                                          body whose eave is closed by its own wall head (roof_junction.round_eave_fill)
    set_entrance(g, xy)                   producer note 11: the 1 cm entrance zone at the building's real entrance
    footprint_views(g, ...)               actor / crane viewpoints round the true (elongated) footprint
    composite_hidden_cull(g, ...)         KIT COMPONENT (post step): core.visibility_cull on every non-backing mesh
    recenter(g)                           KIT COMPONENT (last step): moves the whole building so its plan bounding
                                          box is centred on the origin (art bible 8), recording g.SHIFT
    composite_decals(g, seed)             producer note 11 anchors for rubble walls (straight and round), openings,
                                          thatch / shingle roofs and the round end's cone
    roof_cut_field(roofs, lift, off, rake_deg)        round 5: a yielding body's cut surface against GableRoof(s)
    trim_units_field(ob, mark, field, removed, min_keep)  round 5: cut units on a curved surface, capped
    footprint_field(g, field, margin)     round 6: a cone covering's footprint cut (every course ends on one line)
    drop_slivers(ob, field, mark, h)      round 6: drop thin cut remnants lying on the cut surface
    soaker_support(g, roofs)              round 6: (carry, seat) -- where a soaker / saddle is carried
"""
import math

import numpy as np

from ..core import DetailRule, log, review_cameras, ring_views, visibility_cull

BACKING = ("_deck", "_blocker", "_underlap", "_mortar", "_eave_fill", "_reveals", "_roof_blocker", "_abutment", "_finial",
           "_cap_collar")
"""object-name fragments that are never culled: backing surfaces (deck, blockers, mortar bodies, eave fill,
reveals) and small closed hero pieces."""


def cone_roof(g, seed=606, structure_seeds=(404, 505), soffit=True, soffit_skip=None, abut_roof=None,
              abut_lift=0.02, abut_rule="tuck", abut_tuck=0.15, abut_trim=False, soffit_cut=False,
              abut_soakers=False, abut_top_trim=False, abut_rake_deg=None, abut_min_keep=0.2, abut=None):
    """soffit=True (round 2 default): cone_soffit under the whole eave overhang (soffit_skip(P) -> bool drops the
    part inside an attached body).  abut_roof (round 3): a GableRoof (or a list of them) this cone meets -- the
    cone yields to it (cone_keep_out): every covering unit inside / under that roof's solid or less than abut_lift
    over its top is dropped, with the battens, and the rafter and soffit faces there (the mirror of
    linear_roof(abut_cone=...)).
    round 4: abut_trim=True -- an EVEN cut line: covering units and rafters that cross the roof solid's eave plane
    are cut on it and capped (trim_units) instead of dropped whole, so every course ends on one regular line;
    soffit_cut=True -- the soffit slab is built already cut by the roof keep-out (whole azimuth columns, closed end
    faces on the keep-out boundary; cone_soffit(cut=...)), so no soffit sheet reaches into the roof's zone;
    abut_soakers=True -- one lead soaker sheet under every unit dropped near the roof (cone_soakers), so no dropped
    unit leaves a dark void beside the flashing.
    round 5: abut_top_trim=True -- the eave-band covering units are cut on the roof's top surface and eave plane
    (cone_keep_out(top_trim=True)): every oversailing course ends on one line along the eave roll, and the removed
    parts get soakers too; abut_rake_deg (with abut_top_trim): past the roll's crest the cut runs down-and-out at
    this angle (cone_keep_out(top_rake_deg=...)); the soaker lies over the whole cut region (lead saddle) and the
    battens / soffit / rafters under it stay; abut_min_keep: the smallest share of a unit's vertices above the cut
    for it to be cut rather than dropped whole (cone_keep_out(top_min_keep=...)).
    round 6: abut (dict, optional): further cone_keep_out keywords (top_sliver, soaker_carry, soaker_smooth, ...),
    merged over the flat abut_* ones -- new keep-out options go through this sub-spec, not new flat keywords."""
    from .conical_roof import build_purlins_battens, build_rafters, build_roof_blocker, build_shingles
    build_rafters(g, g.coll, seed=structure_seeds[0])
    build_purlins_battens(g, g.coll, seed=structure_seeds[1])
    build_shingles(g, g.coll, seed=seed)
    build_roof_blocker(g, g.coll)
    roofs = None if abut_roof is None else (abut_roof if isinstance(abut_roof, (list, tuple)) else [abut_roof])
    if soffit:
        cut = None
        if soffit_cut and roofs:
            def cut(P):
                m = np.zeros(len(P), bool)
                for r in roofs:
                    m |= r.keep_out(P, lift=abut_lift)
                return m
        cone_soffit(g, skip=soffit_skip, cut=cut)
    if roofs:
        kw = dict(lift=abut_lift, rule=abut_rule, tuck=abut_tuck, trim=abut_trim,
                  soffit_cut=bool(soffit and soffit_cut), soakers=abut_soakers, top_trim=abut_top_trim,
                  top_rake_deg=abut_rake_deg, top_min_keep=abut_min_keep)
        kw.update(abut or {})
        cone_keep_out(g, roofs, **kw)


# =================================================================================================================
# round 3: unit-level keep-outs (a body yields to another body it meets)
# =================================================================================================================
def mesh_islands(me):
    """connected components of a mesh (each shingle / batten / board a kit unit): vertex label array."""
    nv = len(me.vertices)
    lab = np.arange(nv)
    if not len(me.edges):
        return lab
    E = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    while True:
        m = np.minimum(lab[E[:, 0]], lab[E[:, 1]])
        new = lab.copy()
        np.minimum.at(new, E[:, 0], m)
        np.minimum.at(new, E[:, 1], m)
        new = new[new]
        if np.array_equal(new, lab):
            return lab
        lab = new


def drop_units(ob, inside, rule="any", frac=0.5):
    """KIT HELPER (round 3): delete from mesh object `ob` the units (connected islands; rule "any" / "frac" / "all")
    or the single faces (rule "faces": every vertex inside) that a keep-out marks.  inside(V world) -> bool per
    vertex (object transforms are identity in the kit).  Returns the number of polygons removed."""
    import bmesh
    me = ob.data
    nv = len(me.vertices)
    if not nv:
        return 0
    V = np.zeros(nv * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    ins = np.asarray(inside(V), bool)
    if not ins.any():
        return 0
    loops = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    starts = np.zeros(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", starts)
    pv0 = loops[starts]                                     # one vertex of each polygon (its island)
    if rule == "faces":
        tot = np.zeros(len(me.polygons))
        cnt = np.zeros(len(me.polygons))
        pid = np.repeat(np.arange(len(me.polygons)), np.diff(np.append(starts, len(loops))))
        np.add.at(tot, pid, ins[loops].astype(float))
        np.add.at(cnt, pid, 1.0)
        kill = tot >= cnt
    else:
        lab = mesh_islands(me)
        n_in = np.bincount(lab, weights=ins.astype(float), minlength=nv)
        n_all = np.bincount(lab, minlength=nv).astype(float)
        if rule == "any":
            bad = n_in > 0
        elif rule == "all":
            bad = (n_in >= n_all) & (n_all > 0)
        else:
            bad = n_in >= frac * np.maximum(n_all, 1)
        kill = bad[lab[pv0]]
    if not kill.any():
        return 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.flatnonzero(kill)], context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return int(kill.sum())


COVER_UNITS = ("roof_shingles", "roof_starter", "roof_underlap", "battens")
STRUCT_FACES = ("rafters", "purlin_rings", "roof_soffit_deck")


def roof_eave_planes(roof, off=0.004):
    """round 4: the two vertical planes that bound a GableRoof's solid at its eaves (|local y| = the outermost column
    of linear_roof.GableRoof.section_columns, + `off`), as world (point, outward normal) pairs -- the cut line of a
    body that yields to the roof (trim_units)."""
    ya, zt, _zb = roof.section_columns()
    ym = float(ya[np.isfinite(zt)].max()) + off
    out = []
    for sg in (-1.0, 1.0):
        p = roof.to_world(np.array([0.5 * (roof.xa + roof.xb), sg * ym, 0.0]))
        n = roof.dir_world(np.array([0.0, sg, 0.0]))
        out.append((p, n / np.linalg.norm(n)))
    return out


def _face_groups(faces):
    """edge-connected groups of a list of BMFaces (round 5: the removed part of each cut unit)."""
    fs = set(faces)
    seen, out = set(), []
    for f0 in faces:
        if f0 in seen:
            continue
        grp, stack = [], [f0]
        seen.add(f0)
        while stack:
            f = stack.pop()
            grp.append(f)
            for e in f.edges:
                for lf in e.link_faces:
                    if lf in fs and lf not in seen:
                        seen.add(lf)
                        stack.append(lf)
        out.append(grp)
    return out


def trim_units(ob, mark, planes, whole=True, mark_face=None, removed=None):
    """KIT HELPER (round 4): an EVEN cut line instead of a ragged one.  Every unit (connected island) of mesh object
    `ob` that has a vertex marked by mark(V) -> bool AND a vertex on the outer side of one of `planes` [(point,
    outward normal)] is cut on that plane (bmesh.bisect_plane); the part on the inner side is deleted (whole=True:
    all of it -- small units such as shingles; whole=False: only the faces whose centre mark_face(C) marks -- long
    members such as rafters) and every opening the cut leaves is closed with a flat cap (holes_fill, custom data
    copied from the unit), so the kept units of every course end on one regular line.  Returns (units cut, caps).
    round 5: removed (a list, optional) collects the world vertex array of every deleted part (cone_soakers lays lead
    under them too)."""
    import bmesh
    me = ob.data
    nv = len(me.vertices)
    if not nv or not planes:
        return 0, 0
    V = np.zeros(nv * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    mk = np.asarray(mark(V), bool)
    if not mk.any():
        return 0, 0
    lab = mesh_islands(me)
    has_mark = np.bincount(lab, weights=mk.astype(float), minlength=nv) > 0
    unit_plane = np.full(nv, -1, np.int64)                  # per island label: the plane that cuts it
    for k, (p, nrm) in enumerate(planes):
        side = (V - np.asarray(p, float)) @ np.asarray(nrm, float)
        out_lab = np.bincount(lab, weights=(side > 0.002).astype(float), minlength=nv) > 0
        unit_plane[has_mark & out_lab & (unit_plane < 0)] = k
    if not (unit_plane >= 0).any():
        return 0, 0
    loops = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", loops)
    starts = np.zeros(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", starts)
    f_plane = unit_plane[lab[loops[starts]]]
    bm = bmesh.new()
    bm.from_mesh(me)
    fl = bm.faces.layers.int.new("_trim_plane")
    bm.faces.ensure_lookup_table()
    for f, k in zip(bm.faces, f_plane):
        f[fl] = int(k)
    n_units = int((unit_plane >= 0).sum())
    n_caps = 0
    for k, (p, nrm) in enumerate(planes):
        p = np.asarray(p, float)
        nrm = np.asarray(nrm, float)
        faces = [f for f in bm.faces if f[fl] == k]
        if not faces:
            continue
        edges = {e for f in faces for e in f.edges}
        verts = {v for f in faces for v in f.verts}
        bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + faces, dist=1e-5,
                               plane_co=tuple(p), plane_no=tuple(nrm), clear_inner=False, clear_outer=False)
        kill = []
        for f in [f for f in bm.faces if f[fl] == k]:
            c = np.array(f.calc_center_median()[:])
            if float((c - p) @ nrm) >= 0:
                continue
            if whole or mark_face is None or bool(mark_face(c[None])[0]):
                kill.append(f)
        if not kill:
            continue
        if removed is not None:
            for grp in _face_groups(kill):
                removed.append(np.array([v.co[:] for f in grp for v in f.verts]))
        kill_set = set(kill)
        rim = {e for f in kill for e in f.edges if any(lf not in kill_set for lf in e.link_faces)}
        bmesh.ops.delete(bm, geom=kill, context="FACES_ONLY")
        loose_e = [e for e in bm.edges if e.is_valid and not e.link_faces]
        if loose_e:
            bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
        loose_v = [v for v in bm.verts if v.is_valid and not v.link_faces]
        if loose_v:
            bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
        rim = [e for e in rim if e.is_valid and e.is_boundary]
        if rim:
            r = bmesh.ops.holes_fill(bm, edges=rim, sides=0)
            for f in r["faces"]:
                nb = [lf for e in f.edges for lf in e.link_faces if lf is not f]
                if nb:
                    f.material_index = nb[0].material_index
                    f.smooth = nb[0].smooth
            n_caps += len(r["faces"])
            if r["faces"]:
                for f in r["faces"]:
                    f[fl] = -2
                    f.normal_update()
                    # the cap faces the cut plane's inner side (away from the kept unit)
                    if float(np.dot(np.array(f.normal[:]), nrm)) > 0:
                        f.normal_flip()
    bm.faces.layers.int.remove(fl)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n_units, n_caps


def roof_cut_field(roofs, lift=0.02, off=0.004, rake_deg=None):
    """round 5: the cut surface of a body that yields to GableRoof(s), as a continuous scalar field P world -> f
    (f > 0: keep side).  Per roof f = max(z - (top + lift), |local y| - y_eave): the keep side is everything over the
    roof solid's top (linear_roof.GableRoof.section_columns, the eave roll and ridge roll included) by more than
    `lift`, OR outside its eave plane (roof_eave_planes, + `off`), OR beyond its ends along the ridge; with several
    roofs the minimum.  Units cut on it (trim_units_field) end ON the roof's top along the eave roll and on the eave
    plane past the lip -- one line, not a stack of whole-unit ends.
    rake_deg (optional): past the eave roll's crest the cut surface runs on outward and DOWN at this angle (the
    roll's top continued as a raking verge line) instead of dropping vertically at the eave plane, so the yielding
    body's eave courses that hang in front of the roll end on one raking line resting on the roll, not as a
    vertical stack of cut plates beside its nose."""
    roofs = roofs if isinstance(roofs, (list, tuple)) else [roofs]
    tr = math.tan(math.radians(rake_deg)) if rake_deg is not None else None

    def field(P):
        P = np.asarray(P, float)
        f = np.full(len(P), np.inf)
        for r in roofs:
            ya, zt, _zb = r.section_columns()
            ok = np.isfinite(zt)
            ym = float(ya[ok].max())
            L = r.to_local(P)
            ay = np.abs(L[:, 1])
            top = np.interp(np.minimum(ay, ym), ya[ok], zt[ok])
            if tr is None:
                fr = np.maximum(L[:, 2] - top - lift, ay - (ym + off))
            else:
                yo, zo = ya[ok], zt[ok]
                band = yo > yo.max() - 0.45
                y_c = float(yo[band][np.argmax(zo[band])])
                z_c = float(zo[band].max())
                zcut = np.where(ay <= ym, top, -np.inf)
                zcut = np.maximum(zcut, np.where(ay > y_c, z_c - (ay - y_c) * tr, -np.inf))
                fr = L[:, 2] - zcut - lift
            fr = np.maximum(fr, np.maximum(r.xa - 0.06 - L[:, 0], L[:, 0] - (r.xb + 0.06)))
            f = np.minimum(f, fr)
        return f
    return field


def _copy_corner_data(bm, faces):
    """round 5: corner data (Mask colour, UVs) of new cap faces copied from another loop on the same vertex."""
    fs = set(faces)
    cols = list(bm.loops.layers.color.values()) + list(bm.loops.layers.float_color.values())
    uvs = list(bm.loops.layers.uv.values())
    if not cols and not uvs:
        return
    for f in faces:
        for lp in f.loops:
            src = next((ol for ol in lp.vert.link_loops if ol.face not in fs), None)
            if src is None:
                continue
            for ly in cols:
                lp[ly] = src[ly]
            for ly in uvs:
                lp[ly].uv = src[ly].uv


def trim_units_field(ob, mark, field, removed=None, min_keep=0.2, grad_h=0.01):
    """KIT HELPER (round 5): trim_units on a CURVED cut surface.  Every unit (connected island) of mesh object `ob`
    with a vertex marked by mark(V) -> bool that the scalar field(V) (> 0: keep) crosses is clipped to field >= 0:
    crossing edges are split where the field (linearly interpolated) is zero, faces are split along those points,
    the part on the negative side is deleted and the opening is closed with a cap (holes_fill; material, smoothing,
    Mask colour and UVs copied from the unit; the cap faces down the field's gradient).  A unit with fewer than
    `min_keep` of its vertices on the keep side is left alone (the caller drops it whole: no slivers).
    removed (a list, optional) collects the world vertex array of every deleted part.  Returns (units cut, caps)."""
    import bmesh
    me = ob.data
    nv = len(me.vertices)
    if not nv:
        return 0, 0
    V = np.zeros(nv * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    mk = np.asarray(mark(V), bool)
    if not mk.any():
        return 0, 0
    f = np.asarray(field(V), float)
    f = np.where(np.abs(f) < 1e-6, -1e-6, f)
    lab = mesh_islands(me)
    has_mark = np.bincount(lab, weights=mk.astype(float), minlength=nv) > 0
    n_pos = np.bincount(lab, weights=(f > 0).astype(float), minlength=nv)
    n_all = np.bincount(lab, minlength=nv).astype(float)
    sel = has_mark & (n_pos > 0) & (n_pos < n_all) & (n_pos >= min_keep * np.maximum(n_all, 1))
    vsel = sel[lab]
    if not vsel.any():
        return 0, 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    val = {bm.verts[i]: float(f[i]) for i in np.flatnonzero(vsel)}
    # 1) split every crossing edge at the field's zero
    cross = [e for e in bm.edges if e.verts[0] in val and e.verts[1] in val
             and (val[e.verts[0]] > 0) != (val[e.verts[1]] > 0)]
    on = []
    for e in cross:
        a, b = e.verts
        fa, fb = val[a], val[b]
        t = min(max(fa / (fa - fb), 1e-4), 1 - 1e-4)
        co = a.co.lerp(b.co, t)
        _ne, nvt = bmesh.utils.edge_split(e, a, t)
        nvt.co = co
        val[nvt] = 0.0
        on.append(nvt)
    if not on:
        bm.free()
        return 0, 0
    # 2) split the faces through those points
    bmesh.ops.connect_verts(bm, verts=on, check_degenerate=False)
    # 3) delete the negative side of the selected units
    kill = [fc for fc in bm.faces if all(v in val for v in fc.verts) and max(val[v] for v in fc.verts) <= 0.0
            and min(val[v] for v in fc.verts) < 0.0]
    if removed is not None:
        for grp in _face_groups(kill):
            removed.append(np.array([v.co[:] for fc in grp for v in fc.verts]))
    kill_set = set(kill)
    rim = {e for fc in kill for e in fc.edges if any(lf not in kill_set for lf in e.link_faces)}
    bmesh.ops.delete(bm, geom=kill, context="FACES_ONLY")
    loose_e = [e for e in bm.edges if e.is_valid and not e.link_faces]
    if loose_e:
        bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
    loose_v = [v for v in bm.verts if v.is_valid and not v.link_faces]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    rim = [e for e in rim if e.is_valid and e.is_boundary]
    n_caps = 0
    if rim:
        r = bmesh.ops.holes_fill(bm, edges=rim, sides=0)
        caps = r["faces"]
        for fc in caps:
            nb = [lf for e in fc.edges for lf in e.link_faces if lf is not fc]
            if nb:
                fc.material_index = nb[0].material_index
                fc.smooth = nb[0].smooth
            fc.normal_update()
            c = np.array(fc.calc_center_median()[:])
            gr = np.array([(field((c + d)[None])[0] - field((c - d)[None])[0]) for d in np.eye(3) * grad_h])
            if float(np.dot(np.array(fc.normal[:]), gr)) > 0:      # the cap faces the cut side (down the field)
                fc.normal_flip()
        _copy_corner_data(bm, caps)
        n_caps = len(caps)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    bm.to_mesh(me)
    bm.free()
    me.update()
    return int(sel.sum()), n_caps


def _outline_smooth(M, AA, SS, r_ref, iters):
    """round 6: Laplacian smoothing of a raster footprint's OUTLINE in (azimuth m, slope m) node space -- the 2 cm
    stair corners of the cell mask become a clean traced line (interior nodes stay on the grid).  Returns AA, SS."""
    na, ns = M.shape
    Mp = np.zeros((na + 2, ns + 2), bool)
    Mp[1:-1, 1:-1] = M
    edges = []
    # edges along azimuth between nodes (i, j) - (i+1, j): cells (i, j-1) | (i, j)
    I, J = np.meshgrid(np.arange(na), np.arange(ns + 1), indexing="ij")
    b = Mp[I + 1, J] != Mp[I + 1, J + 1]
    edges.append(np.stack([I[b] * (ns + 1) + J[b], (I[b] + 1) * (ns + 1) + J[b]], 1))
    # edges along the slope between nodes (i, j) - (i, j+1): cells (i-1, j) | (i, j)
    I, J = np.meshgrid(np.arange(na + 1), np.arange(ns), indexing="ij")
    b = Mp[I, J + 1] != Mp[I + 1, J + 1]
    edges.append(np.stack([I[b] * (ns + 1) + J[b], I[b] * (ns + 1) + J[b] + 1], 1))
    E = np.concatenate(edges)
    if not len(E):
        return AA, SS
    X = np.stack([AA.ravel() * r_ref, SS.ravel()], 1)
    nb = np.unique(E)
    for _ in range(iters):
        acc = np.zeros_like(X)
        cnt = np.zeros(len(X))
        np.add.at(acc, E[:, 0], X[E[:, 1]])
        np.add.at(acc, E[:, 1], X[E[:, 0]])
        np.add.at(cnt, E[:, 0], 1.0)
        np.add.at(cnt, E[:, 1], 1.0)
        X[nb] = 0.5 * X[nb] + 0.5 * acc[nb] / np.maximum(cnt[nb], 1.0)[:, None]
    return (X[:, 0] / r_ref).reshape(AA.shape), X[:, 1].reshape(SS.shape)


def cone_soakers(g, units_V, roofs, reach=0.30, lap=0.035, cell=0.02, z0=0.002, t=0.006, mat="M_lead",
                 name="cone_soakers", always=(), carry=None, seat=None, smooth=0, covered=None, keep_lap=0.06):
    """KIT COMPONENT (round 4, part of cone_keep_out(soakers=True)): ONE continuous lead soaker sheet on a RoundFrame
    cone's reference surface under every covering unit the keep-out dropped within `reach` m of the roof it meets
    (|GableRoof.top_depth| <= reach), each footprint grown by `lap` so the sheet runs under the neighbouring kept
    units and under the thatch.  Where both roofs yield (the thatch clipped under the cone, the cone units dropped
    inside the thatch solid) the pit shows lead, never a dark void.  The footprints are rasterised on a (azimuth,
    slope) grid of `cell` m and the sheet is a closed slab (top, underside, side faces on its outline).
    units_V: list of (n, 3) world vertex arrays of the dropped units.  -> <P>_cone_soakers (or None)
    round 5: always -- vertex arrays laid under whatever their distance to the roof (the removed parts of units cut
    by cone_keep_out(top_trim=True), including those in front of the roof's eave roll, outside its columns).
    round 6 (all default off = round 5):
      carry(P, s) -> bool per cell (P: the cell centre on the cone's reference surface, s: its slope distance): the
        sheet is kept only where something carries it (cone_keep_out(soaker_carry=True): over the kept soffit /
        wall head, or on / in the other roof's solid -- never hanging under its eave roll or deck);
      seat(P, s) -> depth (m) per node of the carrying surface under the reference surface (nan: none): there the
        sheet turns down (ramped over ~4 cells) and lies on it, so its free lower edge is a closed edge resting on
        the soffit boarding;
      smooth: outline smoothing iterations (_outline_smooth) -- the raster footprint's stair corners are traced
        into a clean line and the sheet is built as one quad per cell (no long run quads, no T-junctions).
    round 7 (default off = round 6):
      covered(P, n) -> bool per cell: something lies over the cell (e.g. _covered_fn: a ray along the normal meets a
        kept unit or the other roof's covering); cells covered AND more than `keep_lap` m from every uncovered cell
        are not built -- they are never seen (in round 6 the visibility cull removed 87 % of the saddle, 1,110 s
        single-process), so the visible sheet is unchanged."""
    from ..geom import Acc, finalize
    from .cone import az2th, s_at_r, surf_frame
    near = [np.asarray(V, float) for V in always if len(V)]
    for V in units_V:
        c = V.mean(0)[None]
        d = np.full(1, np.inf)
        for r in roofs:
            td = r.top_depth(c)
            d = np.minimum(d, np.abs(td))
        if np.isfinite(d[0]) and d[0] <= reach:
            near.append(V)
    if not near:
        return None
    r_ref = float(np.mean([g.R_WALL]))                         # metres per radian at the eave zone
    boxes = []
    for V in near:
        az = np.unwrap(np.arctan2(V[:, 0], -V[:, 1]))          # kit azimuth: (sin az, -cos az) = plan direction
        rr = np.hypot(V[:, 0], V[:, 1])
        s = np.array([s_at_r(g, float(x)) for x in rr])
        r_m = float(rr.mean())
        boxes.append((az.min() - lap / r_m, az.max() + lap / r_m, s.min() - lap, s.max() + lap, r_m))
    a0 = min(b[0] for b in boxes)
    a1 = max(b[1] for b in boxes)
    s0 = max(0.0, min(b[2] for b in boxes))
    s1 = max(b[3] for b in boxes)
    da = cell / r_ref
    na, ns = int(np.ceil((a1 - a0) / da)) + 1, int(np.ceil((s1 - s0) / cell)) + 1
    if na * ns > 400000:
        return None
    A = a0 + np.arange(na + 1) * da
    S = s0 + np.arange(ns + 1) * cell
    ac, sc = 0.5 * (A[:-1] + A[1:]), 0.5 * (S[:-1] + S[1:])
    M = np.zeros((na, ns), bool)
    for b in boxes:
        M |= ((ac >= b[0]) & (ac <= b[1]))[:, None] & ((sc >= b[2]) & (sc <= b[3]))[None, :]
    if carry is not None and M.any():
        ci, cj = np.nonzero(M)
        Pc, _ts, _tt, nc = surf_frame(g, az2th(np.mod(ac[ci], 2 * np.pi)), sc[cj])
        ok = np.asarray(carry(Pc, sc[cj], nc), bool)
        n_cut = int((~ok).sum())
        M[ci[~ok], cj[~ok]] = False
        log(f"  cone soakers: {n_cut} of {len(ci)} cells carried by nothing, clipped")
    if covered is not None and M.any():                # round 7: cells under kept covering, beyond keep_lap
        ci, cj = np.nonzero(M)
        Pc, _ts, _tt, nc = surf_frame(g, az2th(np.mod(ac[ci], 2 * np.pi)), sc[cj])
        cov = np.zeros(M.shape, bool)
        cov[ci, cj] = np.asarray(covered(Pc + nc * (z0 + t + 0.002), nc), bool)
        near_open = M & ~cov
        k = max(1, int(np.ceil(keep_lap / cell)))
        for _ in range(k):                             # grow the uncovered cells by keep_lap (8-neighbour)
            p = np.pad(near_open, 1)
            near_open = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
                         | p[:-2, :-2] | p[2:, 2:] | p[:-2, 2:] | p[2:, :-2])
        n0 = int(M.sum())
        M &= near_open
        log(f"  cone soakers: {n0 - int(M.sum())} of {n0} cells under kept covering (beyond {keep_lap:.2f} m), "
            "not built")
    if not M.any():
        return None
    if carry is not None or seat is not None or smooth:
        return _soaker_cells(g, M, A, S, r_ref, z0, t, mat, name, seat, smooth, len(near))
    AA, SS = np.meshgrid(A, S, indexing="ij")
    P, ts, tt, n = surf_frame(g, az2th(np.mod(AA, 2 * np.pi)).ravel(), SS.ravel())
    top = P + n * (z0 + t)
    bot = P + n * z0
    nv = len(P)
    V = np.concatenate([top, bot])
    idx = lambda i, j: i * (ns + 1) + j                       # noqa: E731
    F = []
    for i in range(na):                                        # one quad per run of cells along the slope line
        d = np.diff(np.concatenate([[0], M[i].astype(int), [0]]))
        for j0, j1 in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            q = [idx(i, j0), idx(i + 1, j0), idx(i + 1, j1), idx(i, j1)]
            F.append(q)
            F.append([x + nv for x in q[::-1]])
            F.append([idx(i, j0), idx(i, j0) + nv, idx(i + 1, j0) + nv, idx(i + 1, j0)][::-1])   # lower end
            F.append([idx(i, j1), idx(i + 1, j1), idx(i + 1, j1) + nv, idx(i, j1) + nv][::-1])   # upper end
            for i2, a_col, sgn in ((i - 1, i, -1), (i + 1, i + 1, 1)):                          # azimuth sides
                nb = M[i2] if 0 <= i2 < na else np.zeros(ns, bool)
                open_ = ~nb[j0:j1]
                dd = np.diff(np.concatenate([[0], open_.astype(int), [0]]))
                for k0, k1 in zip(np.flatnonzero(dd == 1), np.flatnonzero(dd == -1)):
                    a, b = idx(a_col, j0 + k0), idx(a_col, j0 + k1)
                    F.append([a, b, b + nv, a + nv] if sgn > 0 else [b, a, a + nv, b + nv])
    F = np.array(F)
    q = V[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0:
        F = F[:, ::-1]
    acc = Acc(f"{g.prefix}_{name}", 30)
    acc.add(V, F, mat, wear=0.4)
    log(f"  cone soakers: {len(near)} dropped units within {reach:.2f} m of the roof, {int(M.sum())} cells")
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=True)


def _soaker_cells(g, M, A, S, r_ref, z0, t, mat, name, seat, smooth, n_units):
    """round 6: the soaker slab of cone_soakers(carry / seat / smooth) -- one quad per cell on top and underneath,
    side faces on the (smoothed) outline, the underside dropped onto `seat` where it has one."""
    from ..geom import Acc, finalize
    from .cone import az2th, surf_frame
    na, ns = M.shape
    AA, SS = np.meshgrid(A, S, indexing="ij")
    if smooth:
        AA, SS = _outline_smooth(M, AA, SS, r_ref, int(smooth))
    P, ts, tt, n = surf_frame(g, az2th(np.mod(AA, 2 * np.pi)).ravel(), SS.ravel())
    lo = np.full(len(P), z0)
    n_seat = 0
    if seat is not None:
        d = np.asarray(seat(P, SS.ravel()), float)
        m = np.isfinite(d) & (d > z0)
        n_seat = int(m.sum())
        D0 = np.where(m, d - 0.002 + z0, 0.0).reshape(na + 1, ns + 1)   # rests 2 mm over the carrying surface
        D = D0.copy()
        for _ in range(4):                              # ramped, so the underside never steps (no saw teeth)
            Dp = np.pad(D, 1, mode="edge")
            D = np.maximum(D0, (Dp[:-2, 1:-1] + Dp[2:, 1:-1] + Dp[1:-1, :-2] + Dp[1:-1, 2:] + D) / 5.0)
        lo = z0 - D.ravel()
    top = P + n * (lo + t)[:, None]                     # seated: the whole sheet lies on the soffit boarding
    bot = P + n * lo[:, None]
    nv = len(P)
    ci, cj = np.nonzero(M)
    q = np.stack([ci * (ns + 1) + cj, (ci + 1) * (ns + 1) + cj, (ci + 1) * (ns + 1) + cj + 1, ci * (ns + 1) + cj + 1], 1)
    t0 = top[q[0]]
    if float(np.dot(np.cross(t0[1] - t0[0], t0[3] - t0[0]), n[q[0, 0]])) < 0:
        q = q[:, ::-1]
    Mp = np.zeros((na + 2, ns + 2), bool)
    Mp[1:-1, 1:-1] = M
    F = [q, q[:, ::-1] + nv]
    I, J = np.meshgrid(np.arange(na), np.arange(ns + 1), indexing="ij")
    b = Mp[I + 1, J] != Mp[I + 1, J + 1]
    a_, b_ = I[b] * (ns + 1) + J[b], (I[b] + 1) * (ns + 1) + J[b]
    F.append(np.stack([a_, b_, b_ + nv, a_ + nv], 1))
    I, J = np.meshgrid(np.arange(na + 1), np.arange(ns), indexing="ij")
    b = Mp[I, J + 1] != Mp[I + 1, J + 1]
    a_, b_ = I[b] * (ns + 1) + J[b], I[b] * (ns + 1) + J[b] + 1
    F.append(np.stack([a_, b_, b_ + nv, a_ + nv], 1))
    V = np.concatenate([top, bot])
    F = np.concatenate(F)
    used = np.unique(F)
    remap = np.full(len(V), -1)
    remap[used] = np.arange(len(used))
    acc = Acc(f"{g.prefix}_{name}", 30)
    acc.add(V[used], remap[F], mat, wear=0.4)
    log(f"  cone soakers: {n_units} units, {len(ci)} cells (outline smoothed x{int(smooth)}, {n_seat} nodes seated)")
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=True)


def drop_slivers(ob, field, mark, h=0.03, on=0.002, removed=None):
    """KIT HELPER (round 6): after trim_units_field, delete every unit (island) of `ob` that the cut left as a thin
    sliver lying on the cut surface: it has a marked vertex, a vertex ON the cut (|field| < `on`: its cap) and no
    vertex more than `h` m over the cut -- the triangular tabs and tilted wedges that otherwise stand on the soaker
    at the cut line.  removed (list) collects their world vertex arrays (soaker footprints).  -> polygons removed."""
    me = ob.data
    nv = len(me.vertices)
    if not nv:
        return 0
    V = np.zeros(nv * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    mk = np.asarray(mark(V), bool)
    if not mk.any():
        return 0
    f = np.asarray(field(V), float)
    lab = mesh_islands(me)
    has_mark = np.bincount(lab, weights=mk.astype(float), minlength=nv) > 0
    has_on = np.bincount(lab, weights=(np.abs(f) < on).astype(float), minlength=nv) > 0
    fmax = np.full(nv, -np.inf)
    np.maximum.at(fmax, lab, f)
    bad = has_mark & has_on & (fmax < h)
    if not bad.any():
        return 0
    if removed is not None:
        order = np.argsort(lab, kind="stable")
        labs = lab[order]
        for grp in np.split(order, np.flatnonzero(np.diff(labs)) + 1):
            if bad[lab[grp[0]]]:
                removed.append(V[grp])
    return drop_units(ob, lambda P, _b=bad[lab]: _b if len(P) == nv else np.zeros(len(P), bool), rule="any")


def _island_vertex_sets(ob, mask_fn):
    """world vertex arrays of the islands of `ob` that drop_units(ob, mask_fn, rule='any') would remove."""
    me = ob.data
    nv = len(me.vertices)
    if not nv:
        return []
    V = np.zeros(nv * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    ins = np.asarray(mask_fn(V), bool)
    if not ins.any():
        return []
    lab = mesh_islands(me)
    bad = np.bincount(lab, weights=ins.astype(float), minlength=nv) > 0
    out = []
    order = np.argsort(lab, kind="stable")
    labs = lab[order]
    cuts = np.flatnonzero(np.diff(labs)) + 1
    for grp in np.split(order, cuts):
        if bad[lab[grp[0]]]:
            out.append(V[grp])
    return out


def soaker_support(g, roofs, eave_s=0.10, margin=0.04, gap=0.006, clear=0.005):
    """round 6: (carry, seat) for cone_soakers on a RoundFrame cone that yields to GableRoof(s) -- where the lead
    is CARRIED: on / in a roof's solid (never under its lower outline: the eave-roll belly or the deck underside, by
    `clear`), or, outside every roof's plan columns, over the cone's kept soffit (cone_soffit(eave_s=...), slope
    distance >= eave_s + margin) or the wall head; seat: the soffit's top (BATTEN_T + gap under the reference
    surface) there, so the sheet's free lower edge turns down onto the soffit."""
    from .cone import s_at_r
    s_lo = eave_s + margin
    s_in = s_at_r(g, g.R_WALL - 0.075)
    d_seat = g.BATTEN_T + gap

    def cols(P):
        inc = np.zeros(len(P), bool)
        hang = np.zeros(len(P), bool)
        for r in roofs:
            L = r.to_local(np.asarray(P, float))
            ya, zt, zb = r.section_columns()
            ay = np.abs(L[:, 1])
            top = np.interp(ay, ya, zt, right=-np.inf)
            bot = np.interp(ay, ya, np.where(np.isfinite(zb), zb, 1e9), right=1e9)
            m = (L[:, 0] > r.xa - 0.06) & (L[:, 0] < r.xb + 0.06) & np.isfinite(top)
            inc |= m
            hang |= m & (L[:, 2] < bot + clear)
        return inc, hang

    def carry(P, s, n=None):
        inc, hang = cols(P)
        out_ok = np.asarray(s) >= s_lo
        if n is not None:                              # the soffit under the point is outside the roof's columns too
            inc2, _h2 = cols(np.asarray(P) - np.asarray(n) * (d_seat + 0.012))
            out_ok &= ~inc2
        return ~hang & (inc | out_ok)

    def seat(P, s):
        inc, _h = cols(P)
        s = np.asarray(s, float)
        return np.where(~inc & (s >= s_lo - margin) & (s <= s_in), d_seat, np.nan)
    return carry, seat


def footprint_field(g, field, margin=0.01, iters=2):
    """round 6: a RoundFrame cone covering's FOOTPRINT cut -- P world -> field(foot(P)) - margin, where foot(P) is
    P's foot on the cone's reference surface (along the surface normal).  Units cut on it end on one surface
    standing square to the cone along the line where the reference surface crosses `field` (e.g. roof_cut_field):
    every course, whatever its height over the surface, stops on the same line (a flush, sawn verge), instead of
    each layer ending where its own height meets the cut."""
    def fp(P):
        S0, _n, _o = _cone_foot(g, P, iters)
        return np.asarray(field(S0), float) - margin
    return fp


def _cone_foot(g, P, iters=2):
    """round 6: foot of world points on a RoundFrame cone's reference surface -> (foot, normal there, height over)."""
    from .cone import az2th, surf_frame
    P = np.asarray(P, float)
    az = np.mod(np.arctan2(P[:, 0], -P[:, 1]), 2 * np.pi)
    PR, PS = -np.asarray(g.PR, float), np.asarray(g.PS, float)
    rf = np.hypot(P[:, 0], P[:, 1])
    for _ in range(iters):
        S0, _ts, _tt, n = surf_frame(g, az2th(az), np.interp(-rf, PR, PS))
        o = ((P - S0) * n).sum(1)
        rf = np.hypot(*(P - n * o[:, None])[:, :2].T)
    S0, _ts, _tt, n = surf_frame(g, az2th(az), np.interp(-rf, PR, PS))
    return S0, n, ((P - S0) * n).sum(1)


# =================================================================================================================
# round 7: support pass, lean saddle, and the closed cover over a cut course section
# =================================================================================================================
def _mesh_world(ob):
    """round 7: (world vertices, loop-triangle vertex indices) of a mesh object."""
    me = ob.data
    me.calc_loop_triangles()
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", lt)
    return co, lt.reshape(-1, 3)


def region_soup(obs, lo, hi, labels=None):
    """KIT HELPER (round 7): the triangles of mesh objects `obs` whose bounding box meets the box [lo, hi], as a
    BVH -> (bvh, owner object index per triangle, island id per triangle).  labels {object name: per-vertex island
    label} gives the island ids of those objects (unique over the soup: object offset + label, offsets recorded in
    the dict `base` when given); every other object is one id."""
    from mathutils.bvhtree import BVHTree
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    Vs, Ts, own, isl = [], [], [], []
    nv, nid = 0, 0
    base = labels.setdefault("__base__", {}) if labels is not None else {}
    for k, ob in enumerate(obs):
        co, lt = _mesh_world(ob)
        if not len(lt):
            continue
        c = co[lt]
        m = (c.min(1) <= hi).all(1) & (c.max(1) >= lo).all(1)
        if not m.any():
            continue
        lt = lt[m]
        if labels is not None and ob.name in labels:
            lab = np.asarray(labels[ob.name])
            ids = lab[lt[:, 0]] + nid
            base[ob.name] = nid
            nid += int(lab.max()) + 1
        else:
            ids = np.full(len(lt), nid)
            nid += 1
        Vs.append(co)
        Ts.append(lt + nv)
        own.append(np.full(len(lt), k))
        isl.append(ids)
        nv += len(co)
    if not Ts:
        return None, np.zeros(0, np.int64), np.zeros(0, np.int64)
    V, T = np.concatenate(Vs), np.concatenate(Ts)
    return (BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True, epsilon=0.0),
            np.concatenate(own), np.concatenate(isl))


def _covered_fn(obs, reach=0.12, pad=0.3):
    """round 7: covered(P, n) -> bool per point: a ray from P along n meets one of `obs` within `reach` m (a kept
    unit lies over the point).  The BVH is built on the first call, cropped to the queried points."""
    from mathutils import Vector
    st = {}

    def covered(P, n):
        P, n = np.asarray(P, float), np.asarray(n, float)
        if not len(P):
            return np.zeros(0, bool)
        if "bvh" not in st:
            st["bvh"] = region_soup(obs, P.min(0) - pad, P.max(0) + pad)[0]
        bvh = st["bvh"]
        if bvh is None:
            return np.zeros(len(P), bool)
        return np.array([bvh.ray_cast(Vector(p), Vector(d), reach)[0] is not None for p, d in zip(P, n)], bool)
    return covered


def drop_unsupported(obs, mark, tol=0.005, support=None, passes=3, pad=0.10):
    """KIT HELPER (round 7): delete every unit (connected island) of the mesh objects `obs` that has a vertex marked
    by mark(V world) -> bool and NO vertex within `tol` m of any other geometry (another island of the same object,
    or any object in `support`; default every mesh in the scene) -- a unit left floating once what carried it was
    cut, dropped or clipped.  Repeated (`passes`) so a unit carried only by a dropped one goes too.
    -> {object name: polygons removed}; the centre and gap of each dropped unit are logged."""
    import bpy
    from mathutils import Vector
    obs = [o for o in obs if o is not None and o.type == "MESH" and len(o.data.vertices)]
    support = support if support is not None else [o for o in bpy.context.scene.objects if o.type == "MESH"]
    out = {}
    for _ in range(passes):
        cand, labels = {}, {}
        lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
        for ob in obs:
            co, _lt = _mesh_world(ob)
            mk = np.asarray(mark(co), bool)
            if not mk.any():
                continue
            lab = mesh_islands(ob.data)
            labels[ob.name] = lab
            hit = np.unique(lab[mk])
            cand[ob.name] = (co, lab, hit)
            sel = np.isin(lab, hit)
            lo, hi = np.minimum(lo, co[sel].min(0)), np.maximum(hi, co[sel].max(0))
        if not cand:
            break
        sup = list(dict.fromkeys(list(support) + obs))
        bvh, _own, isl = region_soup(sup, lo - pad, hi + pad, labels=labels)
        if bvh is None:
            break
        base = labels["__base__"]                       # the id offsets region_soup gave each object
        n_drop = 0
        for name, (co, lab, hit) in cand.items():
            order = np.argsort(lab, kind="stable")
            groups = np.split(order, np.flatnonzero(np.diff(lab[order])) + 1)
            bad = np.zeros(len(co), bool)
            hit_set = set(int(x) for x in hit)
            for grp in groups:
                L = int(lab[grp[0]])
                if L not in hit_set or name not in base:
                    continue
                me_id = base[name] + L
                ok = False
                for v in co[grp]:
                    for _loc, _nr, idx, _d in bvh.find_nearest_range(Vector(v), tol):
                        if idx is not None and int(isl[idx]) != me_id:
                            ok = True
                            break
                    if ok:
                        break
                if not ok:
                    bad[grp] = True
                    c = co[grp].mean(0)
                    log(f"  unsupported: {name} unit at ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f}) dropped")
            if bad.any():
                k = drop_units(bpy.data.objects[name], lambda P, _b=bad: _b if len(P) == len(_b) else
                               np.zeros(len(P), bool), rule="any")
                out[name] = out.get(name, 0) + k
                n_drop += k
        if not n_drop:
            break
    return out


def _filter_max(h, k=1):
    """running max over +-k along axis 0."""
    out = h.copy()
    for s in range(1, k + 1):
        out[s:] = np.maximum(out[s:], h[:-s])
        out[:-s] = np.maximum(out[:-s], h[s:])
    return out


def _cut_chains(g, surface, zone, s_range=(-0.15, 2.5), ds=0.01, n_az=2400, link=0.08):
    """round 7: the cut line of a RoundFrame cone covering on its reference surface, inside `zone`: per slope row
    the zero crossings of surface(P) in azimuth (bisection-refined), linked row to row into polylines.
    -> [array (n, 3) world points ordered up the slope]."""
    from .cone import az2th, surf
    ss = np.arange(s_range[0], s_range[1], ds)
    az = np.linspace(0.0, 2 * np.pi, n_az, endpoint=False)
    AZ, SS = np.meshgrid(az, ss, indexing="ij")
    P = surf(g, az2th(AZ).ravel(), SS.ravel())
    F = np.asarray(surface(P), float).reshape(AZ.shape)
    Z = np.asarray(zone(P), bool).reshape(AZ.shape)
    F2 = np.roll(F, -1, 0)
    cr = (np.sign(F) != np.sign(F2)) & (Z | np.roll(Z, -1, 0)) & np.isfinite(F) & np.isfinite(F2)
    ii, jj = np.nonzero(cr)
    if not len(ii):
        return []
    a_lo, a_hi = az[ii].copy(), az[ii] + 2 * np.pi / n_az
    f_lo = F[ii, jj].copy()
    s_ = ss[jj]
    for _ in range(22):
        am = 0.5 * (a_lo + a_hi)
        fm = np.asarray(surface(surf(g, az2th(am), s_)), float)
        same = np.sign(fm) == np.sign(f_lo)
        a_lo, f_lo, a_hi = np.where(same, am, a_lo), np.where(same, fm, f_lo), np.where(same, a_hi, am)
    Pc = surf(g, az2th(0.5 * (a_lo + a_hi)), s_)
    order = np.lexsort((ii, jj))
    chains, open_ = [], []                              # open_: (chain index, last point, last row)
    for k in order:
        j, p = int(jj[k]), Pc[k]
        best, bd = None, link
        for ci, (last, row) in enumerate(open_):
            if last is None or row != j - 1:
                continue
            d = float(np.linalg.norm(p - last))
            if d < bd:
                best, bd = ci, d
        if best is None:
            chains.append([p])
            open_.append((p, j))
        else:
            chains[best].append(p)
            open_[best] = (p, j)
    return [np.array(c) for c in chains if len(c) >= 4]


def _resample(C, step):
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    n = max(2, int(round(d[-1] / step)) + 1)
    u = np.linspace(0.0, d[-1], n)
    return np.stack([np.interp(u, d, C[:, k]) for k in range(3)], 1)


def cone_cut_cover(g, mat="M_lead", t=0.012, lap=0.06, step=0.025, gap=0.003, drop_max=0.12, foot=0.03,
                   e_max=0.08, drop_free=0.005, min_len=0.10, band_u=0.30, reach=0.40, name="cone_cut_cover"):
    """KIT COMPONENT (round 7, post step after cone_roof(abut_top_trim=True) / cone_abutment): ONE closed lead
    cover (a capping) over the cut section of a RoundFrame cone's eave courses where they yield to a GableRoof --
    the layered shingle / starter / batten / rafter ends that the footprint cut (g.CONE_CUT) leaves standing on the
    eave roll.  Generic over any cone and GableRoof:
      line: driven from the cut FIELD, not from kept-unit adjacency -- the zero line of g.CONE_CUT's surface field
        on the cone's reference surface, within `band_u` slope m of the roof's eave (the roll), traced row by row
        (_cut_chains) and joined into runs; at each station (every `step` m) the kept stack's outer edge is found
        by rays along the surface normal searched up to `reach` m into the kept side (units dropped whole end short
        of the field's line), and the line is moved onto the outermost edge in a +-2 station window;
      section (BVH rays): a flat top at the stack's highest point in the window (+ gap) from `lap` m up-slope of
        the edge, its upper edge dressed down onto the courses; down across the cut face, clear of whatever still
        stands past it (up to e_max); then onto the roof / roll / apron / saddle below with a `foot` m turn-out, or,
        where nothing lies within `drop_max` m under the stack, turned under the stack's lowest layer;
      closed slab of thickness t, closed end faces.
    drop_free (m, > 0): first drop_unsupported() over the cone's covering, structure and saddle near the cut in the
    roof's eave band (units left floating once the lead or units under them were clipped).
    -> <P>_cone_cut_cover (or None)"""
    import bpy
    from mathutils import Vector
    from ..geom import Acc, finalize
    cut = getattr(g, "CONE_CUT", None)
    if cut is None:
        log("  cone cut cover: no g.CONE_CUT (cone_keep_out(top_trim=True) not run), skipped")
        return None
    roofs = cut["roofs"]
    obj = lambda nm: bpy.data.objects.get(f"{g.prefix}_{nm}")    # noqa: E731
    layers = [obj(nm) for nm in COVER_UNITS + STRUCT_FACES]
    layers = [o for o in layers if o is not None and o.type == "MESH"]

    def band(V, u_w=None):
        V = np.asarray(V, float)
        m = np.zeros(len(V), bool)
        for r in roofs:
            L = r.to_local(V)
            zb = r.eave_zone(V) if u_w is None else np.abs(L[:, 1]) > r.Y - u_w * math.cos(r.p)
            m |= zb & (L[:, 0] > r.xa - 0.06) & (L[:, 0] < r.xb + 0.06) & (L[:, 2] < r.z_ridge)
        return m
    if drop_free:
        near_cut = lambda V: band(V) & (np.asarray(cut["field"](V), float) < 0.15)   # noqa: E731
        dropped = drop_unsupported(layers + [obj("cone_soakers")], near_cut, tol=float(drop_free))
        if dropped:
            log("  cone cut cover: unsupported units dropped: " + ", ".join(f"{k} {v}" for k, v in dropped.items()))
    chains = _cut_chains(g, cut["surface"], lambda P: band(P, band_u) & np.asarray(cut["zone"](P), bool))
    chains = _join_chains(chains, 0.08)
    if not chains:
        log("  cone cut cover: no cut line in the eave band")
        return None
    allP = np.concatenate(chains)
    scene = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.name.endswith(name)]
    bvh, own, _isl = region_soup(scene, allP.min(0) - 0.8, allP.max(0) + 0.8)
    lay_idx = {k for k, o in enumerate(scene) if o in layers}
    LV = []
    for o in layers:
        co, _lt = _mesh_world(o)
        m = ((co > allP.min(0) - 0.6) & (co < allP.max(0) + 0.6)).all(1)
        LV.append(co[m])
    LV = np.concatenate(LV) if LV else np.zeros((0, 3))

    def ray(o, d, dist, layers_only=False):
        loc, _nr, idx, dd = bvh.ray_cast(Vector(o), Vector(d), dist)
        if loc is None:
            return None
        if layers_only and int(own[idx]) not in lay_idx:
            return None
        return dd
    acc = Acc(f"{g.prefix}_{name}", 30)
    n_runs, n_st, n_land, n_capped = 0, 0, 0, 0
    W_s = np.arange(-0.06, reach + 1e-9, 0.01)
    W_top = np.linspace(0.0, lap, 4)
    for C in chains:
        C = _resample(C, step)
        for _ in range(2):                              # light smoothing of the traced line
            C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
        S, n, _o = _cone_foot(g, C)
        T = np.gradient(S, axis=0)
        T -= n * (T * n).sum(1)[:, None]
        T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
        b = np.cross(n, T)
        sgn = np.sign(np.sum(np.asarray(cut["surface"](S + 0.02 * b), float)
                             - np.asarray(cut["surface"](S - 0.02 * b), float)))
        b = b * (sgn if sgn != 0 else 1.0)              # b points to the kept side
        N = len(S)
        # the kept stack's outer edge at each station (first layer hit searching into the kept side)
        w_e = np.full(N, np.nan)
        for i in range(N):
            for w in W_s:
                if ray(S[i] + b[i] * w + n[i] * 0.6, -n[i], 1.2, layers_only=True) is not None:
                    w_e[i] = w
                    break
        kept = np.isfinite(w_e)
        w_l = np.where(kept, w_e, np.inf)
        w_line = w_l.copy()
        for s_ in (1, 2):                               # outermost edge in a +-2 station window
            w_line[s_:] = np.minimum(w_line[s_:], w_l[:-s_])
            w_line[:-s_] = np.minimum(w_line[:-s_], w_l[s_:])
        w_line = np.where(np.isfinite(w_line), w_line, 0.0)
        S2 = S + b * w_line[:, None]
        Htop = np.zeros((N, len(W_top)))
        h_lapend = np.zeros(N)
        for i in range(N):
            for k, w in enumerate(W_top):
                dd = ray(S2[i] + b[i] * w + n[i] * 0.6, -n[i], 1.2)
                Htop[i, k] = 0.6 - dd if dd is not None else -1.0
            dd = ray(S2[i] + b[i] * (lap + 0.015) + n[i] * 0.6, -n[i], 1.2)
            h_lapend[i] = 0.6 - dd if dd is not None else Htop[i, -1]
        h_cap = _filter_max(np.where(kept, Htop.max(1), -1.0), 2) + gap
        h_cap = np.where(h_cap < -0.5, Htop.max(1) + gap, h_cap)
        prof = np.zeros((N, 5, 2))
        for i in range(N):
            Q = LV - S2[i]
            u, w, h = Q @ T[i], Q @ b[i], Q @ n[i]
            near = np.abs(u) < 0.6 * step + 0.01
            st = near & (w >= 0.0) & (w < 0.04) & (h < h_cap[i])
            h_sb = float(h[st].min()) if st.any() else h_cap[i] - 0.03
            dd = ray(S2[i] + b[i] * 0.01 - n[i] * 0.4, n[i], 0.4 + h_cap[i], layers_only=True)
            if dd is not None:                          # the stack's lowest layer seen from below
                h_sb = min(h_sb, dd - 0.4)
            e = gap
            lower = ("wrap", h_sb)
            for _ in range(3):
                dd = ray(S2[i] - b[i] * (e + t + 0.003) + n[i] * h_cap[i], -n[i], h_cap[i] - (h_sb - drop_max))
                lower = (("land", min(h_cap[i] - dd, h_cap[i] - 0.02)) if dd is not None else ("wrap", h_sb))
                pr = near & (w < -e + 0.001) & (w > -0.15) & (h > lower[1] + 0.003) & (h < h_cap[i])
                if not pr.any():
                    break
                e_new = float(-w[pr].min()) + gap
                if e_new > e_max:
                    n_capped += 1
                    e_new = e_max
                if e_new <= e + 1e-4:
                    break
                e = e_new
            prof[i, 0] = (lap + 0.015, min(h_lapend[i] + gap, h_cap[i] - 0.004))
            prof[i, 1] = (lap, h_cap[i])
            prof[i, 2] = (-e, h_cap[i])
            if lower[0] == "land":
                n_land += kept[i]
                dd2 = ray(S2[i] - b[i] * (e + t + foot) + n[i] * (lower[1] + 0.03), -n[i], 0.08)
                h2 = lower[1] + 0.03 - dd2 if dd2 is not None else lower[1]
                prof[i, 3] = (-e, lower[1] + gap)
                prof[i, 4] = (-e - foot, min(h2, lower[1] + 0.01) + gap)
            else:
                prof[i, 3] = (-e, lower[1] - gap)
                prof[i, 4] = (0.02, lower[1] - gap)
        log(f"  cut line: {N} stations {S[0].round(2)} -> {S[-1].round(2)}, stack edge (cm) "
            + " ".join(f"{100 * x:.0f}" if np.isfinite(x) else "-" for x in w_e))
        d = np.diff(np.concatenate([[0], kept.astype(int), [0]]))
        for i0, i1 in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            if (i1 - i0 - 1) * step < min_len:
                continue
            Vr, Fr = _cover_sweep(S2[i0:i1], b[i0:i1], n[i0:i1], prof[i0:i1], t)
            acc.add(Vr, Fr, mat, wear=0.4)
            n_runs += 1
            n_st += i1 - i0
    if not n_runs:
        log("  cone cut cover: no kept course section over the cut line")
        return None
    log(f"  cone cut cover: {n_runs} run(s), {n_st} stations ({n_land} landing on the roof / roll / lead, "
        f"{n_st - n_land} turned under), {n_capped} stations with something standing > {e_max:.2f} m past the cut")
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=True)


def _join_chains(chains, tol):
    """round 7: join traced polylines end to start (either direction) where their ends lie within tol m."""
    chains = [np.asarray(c, float) for c in chains]
    joined = True
    while joined and len(chains) > 1:
        joined = False
        for a in range(len(chains)):
            for b_ in range(len(chains)):
                if a == b_:
                    continue
                A, B = chains[a], chains[b_]
                for A2, B2 in ((A, B), (A, B[::-1]), (A[::-1], B)):
                    if np.linalg.norm(A2[-1] - B2[0]) < tol:
                        chains[a] = np.concatenate([A2, B2])
                        del chains[b_]
                        joined = True
                        break
                if joined:
                    break
            if joined:
                break
    return chains


def _cover_sweep(S, b, n, prof, t):
    """round 7: a closed slab swept along stations S with per-station section `prof` (K, 2) in (b, n) -- the
    inner (contact) line -- offset by t to its outer side (left of the travel direction).  -> (V, faces)"""
    N, K, _ = prof.shape
    outer = np.zeros_like(prof)
    for i in range(N):
        p = prof[i]
        dseg = np.diff(p, axis=0)
        dseg /= np.maximum(np.linalg.norm(dseg, axis=1), 1e-9)[:, None]
        nseg = np.stack([dseg[:, 1], -dseg[:, 0]], 1)       # rotate -90 deg: the outer side
        nv = np.zeros((K, 2))
        nv[0], nv[-1] = nseg[0], nseg[-1]
        nv[1:-1] = nseg[:-1] + nseg[1:]
        nv /= np.maximum(np.linalg.norm(nv, axis=1), 1e-9)[:, None]
        cosv = np.ones(K)
        cosv[1:-1] = np.maximum((nv[1:-1] * nseg[:-1]).sum(1), 0.5)
        outer[i] = p + nv * (t / cosv)[:, None]
    loop = np.concatenate([prof, outer[:, ::-1]], 1)         # (N, 2K)
    V = (S[:, None, :] + b[:, None, :] * loop[:, :, :1] + n[:, None, :] * loop[:, :, 1:]).reshape(-1, 3)
    L = 2 * K
    F = []
    for i in range(N - 1):
        for k in range(L):
            F.append([i * L + k, i * L + (k + 1) % L, (i + 1) * L + (k + 1) % L, (i + 1) * L + k])
    F = [np.array(F)]
    F.append(np.arange(L)[::-1])
    F.append(np.arange(L) + (N - 1) * L)
    return V, F


def cone_keep_out(g, roofs, lift=0.02, rule="tuck", tuck=0.15, trim=False, soffit_cut=False, soakers=False,
                  soaker_reach=0.30, top_trim=False, top_min_keep=0.2, top_rake_deg=None, top_sliver=0.0,
                  soaker_carry=False, soaker_smooth=0, top_drop=(), top_footprint=0.0, soaker_lean=False):
    """KIT COMPONENT (round 3, after cone_roof): the cone yields to the linear roof(s) it meets -- the mirror of
    linear_roof(abut_cone=...).  The keep-out is each GableRoof's solid (deck, courses, eave roll, ridge roll; its
    vertical columns, linear_roof.GableRoof.keep_out) up to `lift` over its top and everything under it.  Covering
    units (shingles, starters, under-laps) and battens are dropped WHOLE (never cut):
      rule "tuck" (default): every unit wholly in the keep-out, and every unit with any vertex under the roof's
        soffit / eave-roll belly, inside the eave band (GableRoof.eave_zone: the roll), or more than `tuck` m under
        the roof's top -- so at the eaves each cone course ends on a whole unit over the roll and its end apron,
        while on the slopes a unit may tuck its corner a little under the thatch beside the flashing;
      rule "any": every unit with any vertex in the keep-out; "frac": half its vertices; "all": wholly inside.
    Rafter, purlin and soffit faces wholly inside it are dropped (their ends stay buried in the roof).  Records
    g.CONE_KEEP_OUT (the keep-out fn) for later steps.  Returns {object: polygons removed}.
    round 5: top_trim=True -- in the roof's eave band the covering units are CUT on the roof's top surface (+ lift)
    and its eave plane (roof_cut_field, trim_units_field) instead of dropped whole or cut on the eave plane only, so
    every oversailing course ends on one line along the eave roll's top with a capped end (units with less than
    top_min_keep of their vertices above it are still dropped whole); with soakers=True the removed part of every
    cut unit is a soaker footprint too (lead under every cut AND every dropped unit).  top_rake_deg (with
    top_trim): past the roll's crest the cut runs on down-and-out at this angle (roof_cut_field(rake_deg=...)) --
    covering units, battens and rafters in front of the roll nose are cut on that raking line (units mostly under
    it are dropped) and the soaker is laid over the whole cut region (a lead saddle in front of the roll nose;
    the battens, soffit and rafters under it stay), so the eave courses end on one raking line resting on the
    roll, not in a vertical stack of cut plates.
    round 6 (defaults = round 5): top_sliver (m, with top_trim): a cut unit left as a thin sliver lying on the cut
    surface (no vertex more than top_sliver over it: drop_slivers) is dropped too, its footprint soaked -- no tabs
    or tilted wedges stand on the saddle at the cut line; soaker_carry=True: the saddle is clipped to where it is
    carried and its free lower edge turned down onto the soffit (soaker_support, cone_soakers(carry, seat));
    soaker_smooth: outline smoothing iterations of the saddle (cone_soakers(smooth=...)); top_drop (object name
    suffixes, e.g. ("roof_underlap",)): hidden-layer units the cut touches are dropped whole instead of cut;
    top_footprint (m, > 0 = on, with
    top_trim): the eave-band units are cut on footprint_field(field, margin=top_footprint) -- square to the cone
    along the line where its reference surface crosses the cut, so every course (whatever its height) ends on the
    same line, and a unit kept whole above the cut can no longer end short of it in a stepped stack.
    round 7 (default = round 6): soaker_lean=True -- the saddle skips the cells that something covers (a ray along
    the cone normal meets a kept unit or the roof's covering within 0.6 m) beyond 6 cm from any exposed cell
    (cone_soakers(covered=...)): the same visible sheet without the buried cells the visibility cull used to remove.
    With top_trim the cut is recorded on g.CONE_CUT (field, surface field, zone, roofs) for the post step
    cone_cut_cover (and its drop_unsupported pass)."""
    import bpy
    roofs = roofs if isinstance(roofs, (list, tuple)) else [roofs]

    def inside(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            m |= r.keep_out(V, lift=lift)
        return m
    def deep(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            d = r.top_depth(V)
            m |= (d > tuck) | r.under_soffit(V) | ((d > -lift) & r.eave_zone(V))
        return m
    def eave_mark(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            d = r.top_depth(V)
            m |= r.eave_zone(V) & np.isfinite(d) & ((d > -lift) | r.under_soffit(V))
        return m
    out = {}
    planes = [pl for r in roofs for pl in roof_eave_planes(r)] if trim else []
    cut_info = {}
    drop_sets = []
    removed = []
    field =roof_cut_field(roofs, lift=lift + 0.003, rake_deg=top_rake_deg) if top_trim else None
    rake = field is not None and top_rake_deg is not None
    surface_field = field
    if field is not None and top_footprint:            # round 6: cut square to the cone on the footprint line
        surface_field = (lambda P, _f=field, _m=float(top_footprint): np.asarray(_f(P), float) - _m)
        field = footprint_field(g, field, margin=float(top_footprint))

    def rake_mark(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            m |= r.eave_zone(V)
        return m & (field(V) < 0)

    def zone_mark(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            m |= r.eave_zone(V)
        return m
    for nm in COVER_UNITS + STRUCT_FACES:
        ob = bpy.data.objects.get(f"{g.prefix}_{nm}")
        if ob is None or ob.type != "MESH":
            continue
        if nm == "roof_soffit_deck" and soffit_cut:
            continue                                   # built already cut (cone_soffit(cut=...)), end faces closed
        if field is not None and nm in top_drop:
            # round 6: a hidden-layer unit (under-lap) the cut touches is dropped WHOLE -- cut, it is left as a bare
            # tab on the saddle once the shingles over it are cut back
            out[nm + " (whole)"] = drop_units(ob, rake_mark if rake else eave_mark, rule="any")
        elif field is not None and nm in COVER_UNITS:
            # round 5: cut on the roof's top / eave plane in the eave band (one line along the roll), then the rest
            rm = [] if (soakers and nm in ("roof_shingles", "roof_starter")) else None
            if rake and rm is not None:                # the whole footprint of every unit the rake touches
                rm += _island_vertex_sets(ob, rake_mark)
            cut_info[nm] = trim_units_field(ob, rake_mark if rake else eave_mark, field, removed=rm,
                                            min_keep=top_min_keep)
            if top_sliver > 0:                         # round 6: thin cut remnants lying on the cut surface
                sl = [] if rm is not None else None
                out[nm + " (sliver)"] = drop_slivers(ob, field, zone_mark, h=top_sliver, on=0.006, removed=sl)
                if sl:
                    removed += sl
            if rm:
                removed += rm
            if rake:                                   # units (mostly) under the raking line: dropped whole
                out[nm + " (rake)"] = drop_units(ob, rake_mark, rule="frac", frac=1.0 - top_min_keep)
        elif planes and nm in COVER_UNITS:
            # round 4 (trim): a unit the tuck rule would drop that crosses the eave plane is cut on it and capped
            cut_info[nm] = trim_units(ob, (lambda V: deep(V)) if rule == "tuck" else inside, planes, whole=True)
        elif planes and nm == "rafters":
            cut_info[nm] = trim_units(ob, inside, planes, whole=False, mark_face=inside)
        if soakers and nm in ("roof_shingles", "roof_starter"):
            sets = _island_vertex_sets(ob, deep if rule == "tuck" else inside)
            if rule == "tuck":
                sets += [Vu for Vu in _island_vertex_sets(ob, inside) if inside(Vu).all()]
            drop_sets += sets
        if nm not in COVER_UNITS:
            out[nm] = drop_units(ob, inside, rule="faces")
        elif rule == "tuck":
            out[nm] = drop_units(ob, inside, rule="all") + drop_units(ob, deep, rule="any")
        else:
            out[nm] = drop_units(ob, inside, rule=rule)
    g.CONE_KEEP_OUT = inside
    if field is not None:                              # round 7: the cut, for cone_cut_cover / drop_unsupported
        g.CONE_CUT = dict(field=field, surface=surface_field, zone=zone_mark, roofs=roofs)
    if soakers and removed:
        log(f"  cut units: {len(removed)} removed parts are soaker footprints too")
    if soakers and (drop_sets or removed):
        if soaker_carry or soaker_smooth or soaker_lean:   # round 6 / 7
            carry, seat = soaker_support(g, roofs) if soaker_carry else (None, None)
            lean = dict(covered=_covered_fn([o for o in bpy.data.objects if o.type == "MESH"], reach=0.6)
                        ) if soaker_lean else {}
            cone_soakers(g, drop_sets, roofs, reach=soaker_reach, always=removed, carry=carry, seat=seat,
                         smooth=soaker_smooth, **lean)
        else:
            cone_soakers(g, drop_sets, roofs, reach=soaker_reach, always=removed)
    log("cone keep-out (" + ", ".join(r.name for r in roofs) + "): -" +
        ", ".join(f"{k} {v}" for k, v in out.items() if v) + " polygons")
    if cut_info:
        log("  even cut line (trim_units): " + ", ".join(f"{k} {u} units / {c} caps" for k, (u, c) in cut_info.items()))
    return out


def _soffit_spans(g, cut, skip, s0, s1, depth, n_ss=5, n_dense=1440):
    """round 4: the kept azimuth spans of a soffit slab cut by keep-out `cut` (and `skip`): per slope row s, the
    azimuth interval ends refined by bisection on the keep-out boundary.  Returns [(az_lo[row], az_hi[row])] with
    ss, or None when nothing is cut / the rows disagree (the caller falls back to whole faces)."""
    from .cone import az2th, surf_frame
    ss = np.linspace(s0, s1, n_ss)

    def drop(az, s):
        az = np.mod(np.asarray(az, float), 2 * np.pi)
        P, ts, tt, n = surf_frame(g, az2th(az), np.full(az.shape, s))
        P = P - n * depth
        m = np.asarray(cut(P), bool)
        if skip is not None:
            m |= np.asarray(skip(P), bool)
        return m
    azd = np.linspace(0, 2 * np.pi, n_dense, endpoint=False)
    ins = np.array([drop(azd, s) for s in ss])
    if not ins.any():
        return None
    allin = np.flatnonzero(ins.all(0))
    if not len(allin):
        return None
    k0 = int(allin[0])
    step = 2 * np.pi / n_dense
    azr = azd[k0] + np.arange(n_dense) * step              # rotated so it starts inside a dropped run
    insr = np.roll(ins, -k0, axis=1)
    runs = []
    for j in range(len(ss)):
        kept = ~insr[j]
        d = np.diff(np.concatenate([[0], kept.astype(int), [0]]))
        st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
        runs.append(list(zip(st, en)))
    if len({len(r) for r in runs}) != 1 or not runs[0]:
        return None

    def refine(a_keep, a_drop, s):
        for _ in range(26):
            m = 0.5 * (a_keep + a_drop)
            if drop(np.array([m]), s)[0]:
                a_drop = m
            else:
                a_keep = m
        return a_keep
    spans = []
    for r in range(len(runs[0])):
        lo = np.array([refine(azr[runs[j][r][0]], azr[runs[j][r][0]] - step, ss[j]) for j in range(len(ss))])
        hi = np.array([refine(azr[runs[j][r][1]], azr[runs[j][r][1]] + step, ss[j]) for j in range(len(ss))])
        spans.append((lo, hi, ss))
    return spans


def _soffit_span_parts(g, spans, d0, t, n_az):
    """round 4: the closed slab of each kept span (top, soffit, eave edge and an end face at each cut end)."""
    from ..core import grid_quads
    from .cone import az2th, surf_frame
    out = []
    for lo, hi, ss in spans:
        m = max(2, int(round(float(np.mean(hi - lo)) / (2 * np.pi / (n_az - 1)))) + 1)
        f = np.linspace(0, 1, m)
        AZ = lo[None, :] + (hi - lo)[None, :] * f[:, None]          # (m, ns)
        SS = np.broadcast_to(ss[None, :], AZ.shape)
        P, ts, tt, n = surf_frame(g, az2th(np.mod(AZ, 2 * np.pi)).ravel(), SS.ravel())
        top, bot = P - n * d0, P - n * (d0 + t)
        ns = len(ss)
        F = grid_quads(m, ns)
        for V, up in ((top, True), (bot, False)):
            q = V[F[0]]
            FF = F[:, ::-1] if (float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0) == up else F
            out.append((V, FF))
        T3, B3 = top.reshape(m, ns, 3), bot.reshape(m, ns, 3)
        E = np.stack([T3[:, 0], B3[:, 0]], 1).reshape(-1, 3)
        FE = grid_quads(m, 2)
        q = E[FE[0]]
        if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), -ts.reshape(m, ns, 3)[0, 0])) < 0:
            FE = FE[:, ::-1]
        out.append((E, FE))
        for i, i2 in ((0, 1), (m - 1, m - 2)):              # the end faces on the keep-out boundary
            V = np.concatenate([T3[i], B3[i]])
            FF = np.array([[j, j + 1, ns + j + 1, ns + j] for j in range(ns - 1)])
            outward = T3[i, ns // 2] - T3[i2, ns // 2]
            q = V[FF[0]]
            if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), outward)) < 0:
                FF = FF[:, ::-1]
            out.append((V, FF))
    return out


def cone_soffit(g, r_in=None, eave_s=0.10, gap=0.006, t=0.012, skip=None, n_az=145, cut=None):
    """KIT COMPONENT (round 2): the boarded soffit slab under a RoundFrame cone's eave overhang -- the closed slab of
    components.tower_roof._roof_deck (v1), limited to the overhang: top face up under the battens, soffit face down,
    edge face at the eave, from eave_s slope metres above the lip to r_in (default 7.5 cm inside the plate line,
    past the start of the roof blocker), so no eye-level ray finds sky between the rafters, plate, battens, under-lap
    and shingles of the overhang.  skip(P) -> bool drops faces inside an attached body.  -> <P>_roof_soffit_deck
    round 4: cut(P) -> bool (a body's keep-out, e.g. GableRoof.keep_out): the slab is built as whole azimuth spans
    that stop ON the keep-out boundary (refined per slope row), each closed with an end face -- no single-sided sheet
    and no board inside the other body's zone (cut=None: the round-2 behaviour)."""
    from ..core import grid_quads
    from ..geom import Acc, finalize
    from .cone import az2th, s_at_r, surf_frame
    r_in = g.R_WALL - 0.075 if r_in is None else r_in
    az = np.linspace(0, 2 * np.pi, n_az)
    th = az2th(az)
    s_in = s_at_r(g, r_in)
    d0 = g.BATTEN_T + gap
    acc = Acc(f"{g.prefix}_roof_soffit_deck", 30)

    def sheet(depth, up, ns=5):
        ss = np.linspace(eave_s, s_in + 0.03, ns)
        TH, SS = np.meshgrid(th, ss, indexing="ij")
        P, ts, tt, n = surf_frame(g, TH.ravel(), SS.ravel())
        P = P - n * depth
        F = grid_quads(len(th), len(ss))
        q = P[F[0]]
        if (float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0) == up:
            F = F[:, ::-1]
        return P, F
    if cut is not None:
        spans = _soffit_spans(g, cut, skip, eave_s, s_in + 0.03, d0 + 0.5 * t, n_ss=5)
        if spans is not None:
            for P, F in _soffit_span_parts(g, spans, d0, t, n_az):
                acc.add(P, F, "M_timber_weathered", wear=0.4)
            log(f"  cone soffit: {len(spans)} spans cut by the keep-out, closed end faces")
            return finalize(acc, g.coll, smooth_deg=30.0, recalc=False)
    parts = [sheet(d0, True), sheet(d0 + t, False)]
    P0, ts, tt, n = surf_frame(g, th, np.full_like(th, eave_s))
    E = np.stack([P0 - n * d0, P0 - n * (d0 + t)], 1).reshape(-1, 3)
    F = grid_quads(len(th), 2)
    q = E[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), -ts[0])) < 0:
        F = F[:, ::-1]
    parts.append((E, F))
    for P, F in parts:
        if skip is not None:
            F = F[~skip(P[F].mean(1))]
        acc.add(P, F, "M_timber_weathered", wear=0.4)
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=False)


def set_entrance(g, xy, radius=3.0, height=2.5):
    g.detail = DetailRule(entrance=tuple(xy), entrance_r=radius, entrance_h=height)
    g.ENTRANCE = tuple(xy)


def inside_box(x0, x1, y0, y1, z1=None):
    """clip(P, margin=0) -> bool: plan point inside the box (e.g. the interior of an attached rectangular body)."""
    def clip(P, margin=0.0):
        P = np.asarray(P, float)
        m = (P[:, 0] > x0 + margin) & (P[:, 0] < x1 - margin) & (P[:, 1] > y0 + margin) & (P[:, 1] < y1 - margin)
        if z1 is not None:
            m &= P[:, 2] < z1
        return m
    return clip


def inside_round(center, r_out, depth=0.12, batter_deg=0.0):
    """clip(P, margin=0) -> bool: plan point more than `depth` inside a round body's face (radius r_out at the
    ground, battered by batter_deg) -- e.g. a straight wall running into a round end."""
    tb = math.tan(math.radians(batter_deg))

    def clip(P, margin=0.0):
        P = np.asarray(P, float)
        r = r_out - np.clip(P[:, 2], 0, None) * tb
        return np.hypot(P[:, 0] - center[0], P[:, 1] - center[1]) < r - depth - margin
    return clip


def _meshes(g):
    return [o for o in g.coll.all_objects if o.type == "MESH"]


def _bounds(g):
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in _meshes(g)])
    return co.min(0), co.max(0)


LEAN_VIEWS = dict(dists=(0.8, 3.0), heights=(0.6, 1.65, 2.6), spacing=1.8, crane=(6.0, (7.0,)),
                  door=((0.8, 1.6, 2.4), (0.6, 1.2, 1.8), (-0.6, 0.0, 0.6)))
"""round 2: the lean view set (2 loop distances x 3 heights + 1 crane loop + 27 door views + the review cameras,
~1/3 of the round-1 set) -- keeps a full composite build under the art bible's ~10 min."""
ROOF_VIEWS = dict(dists=(0.8, 3.0), heights=(1.65, 2.6), spacing=1.8, crane=(6.0, (7.0,)), door=((), (), ()))
ROOF_PARTS = ("roof_shingles", "roof_starter", "_covering", "_eave_roll", "_ridge", "_comb")
"""roof coverings: no knee-height loop and no door views (they cannot see more of a roof than head height does)."""


def footprint_views(g, dists=(0.5, 1.5, 3.5), heights=(0.3, 1.0, 1.65, 2.3), spacing=1.2, crane=(6.0, (5.0, 9.0)),
                    door=((0.6, 1.2, 2.0), (0.5, 1.1, 1.7, 2.3), (-0.8, 0.0, 0.8))):
    """viewpoints on loops round the plan bounding box (offset by each distance) at actor heights, a crane loop, the
    review cameras and door views (1-2 m in front of every door, knee to above head height).
    door = (distances, heights, lateral offsets) of the door views."""
    lo, hi = _bounds(g)
    out = []

    def loop(d, z):
        x0, x1, y0, y1 = lo[0] - d, hi[0] + d, lo[1] - d, hi[1] + d
        per = 2 * ((x1 - x0) + (y1 - y0))
        n = max(16, int(per / spacing))
        for k in range(n):
            s = per * k / n
            if s < x1 - x0:
                p = (x0 + s, y0)
            elif s < (x1 - x0) + (y1 - y0):
                p = (x1, y0 + s - (x1 - x0))
            elif s < 2 * (x1 - x0) + (y1 - y0):
                p = (x1 - (s - (x1 - x0) - (y1 - y0)), y1)
            else:
                p = (x0, y1 - (s - 2 * (x1 - x0) - (y1 - y0)))
            out.append((p[0], p[1], z))
    for d in dists:
        for z in heights:
            loop(d, z)
    for z in crane[1]:
        loop(crane[0], z)
    for op in getattr(g, "OPENINGS", []):
        if op["kind"] != "door":
            continue
        for d in door[0]:
            for z in door[1]:
                for x in door[2]:
                    out.append(tuple(op["O"] + op["n"] * d + op["t"] * x + np.array([0, 0, z])))
    V = np.array(out)
    return np.concatenate([V, review_cameras(lo, hi)])


def composite_hidden_cull(g, targets=None, procs=4, views="lean", min_polys=0):
    """KIT COMPONENT (post step): delete the polygons no review / actor / crane / door viewpoint can see on every
    building mesh except the backing surfaces (BACKING) and the pooled instances (producer note 6).
    views: "lean" (round 2 default, LEAN_VIEWS), "full" (the round-1 set) or a footprint_views kwargs dict;
    min_polys: only ray-test objects with at least this many polygons (the small ones cost time, save little)."""
    if targets is None:
        targets = [o.name for o in _meshes(g)
                   if o.data.users == 1 and not any(b in o.name for b in BACKING)
                   and len(o.data.polygons) >= min_polys]
    if views == "lean":
        # roof coverings (ROOF_PARTS) are tested from the actor loops at head / eave height, the crane loop and the
        # review cameras; walls, openings and timbers also from the knee-height loops and the door views
        common = footprint_views(g, **ROOF_VIEWS)
        low = footprint_views(g, **dict(LEAN_VIEWS, heights=(0.6,), crane=(6.0, ())))
        by = {t: low for t in targets if not any(r in t for r in ROOF_PARTS)}
        n = visibility_cull(targets, extra_views=common, extra_by_target=by, procs=procs)
        log(f"hidden-geometry cull: -{n} polygons on {len(targets)} objects")
        return n
    kw = {} if views == "full" else dict(views)
    n = visibility_cull(targets, extra_views=footprint_views(g, **kw), procs=procs)
    log(f"hidden-geometry cull: -{n} polygons on {len(targets)} objects")
    return n


def recenter(g):
    """KIT COMPONENT (last geometry step): translate the building so its plan bounding box is centred on the origin
    (ground stays at Z = 0).  Unique meshes are moved in their data (transforms stay identity); pooled linked
    duplicates move by their matrices.  g.SHIFT records the move (later steps and decals add it)."""
    from mathutils import Matrix
    lo, hi = _bounds(g)
    sh = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, 0.0])
    T = Matrix.Translation(tuple(map(float, sh)))
    done = set()
    for o in _meshes(g):
        if o.data.users == 1 and o.matrix_world == Matrix.Identity(4):
            o.data.transform(T)
            o.data.update()
        else:
            o.matrix_world = T @ o.matrix_world
        done.add(o.name)
    g.SHIFT = sh
    log(f"recentred by ({sh[0]:+.3f}, {sh[1]:+.3f}); plan bbox {hi[0] - lo[0]:.2f} x {hi[1] - lo[1]:.2f} m, "
        f"height {hi[2]:.2f} m")
    return sh


# =================================================================================================================
# producer note 11: decal anchors
# =================================================================================================================
def composite_decals(g, seed=1201, door_lichen="jamb", south_moss=False, walk_gate=True, moss_normal="hit"):
    """anchors on the composite's surfaces, all ray-snapped onto the built meshes (decals.SurfaceProbe), physically
    placed: damp_rise / moss at the wall feet (more and likelier on north faces), lichen on footing tops, quoins and
    weather (W / N) faces, water_streak under sills and the cone eave drip, soot over the door and windows, rust under
    the door straps, cracks at opening corners and lintel ends, grime beside the door, repair patches on the walls,
    moss on the north roof slopes and the cone's north shingle butts.  The kit gate (anchor_validate, the building
    spec's decal_validate) then snaps / drops them.
    round 4: door_lichen="jamb" (the footing stones beside the jambs; "threshold": the round 1-3 walked top),
    south_moss=False (thatch moss on the north slope only), walk_gate=True: each door's trodden zone
    (decal_gate.door_walk_zone) is published on da.walk_zones for anchor_validate(walk_zones="da").
    round 6: moss_normal="slope" -- linear-roof moss projects along the roof's slope normal (a ray hit on a course's
    flat top gave a straight-up normal on a 40 deg slope); "hit": the round 1-5 behaviour."""
    from ..decals import SurfaceProbe, above_opening, below_points, opening_corners, tops
    sh = getattr(g, "SHIFT", np.zeros(3))
    da = g.decals
    rng = np.random.RandomState(seed)
    probe = SurfaceProbe(_meshes(g))
    ez = np.array([0.0, 0.0, 1.0])
    STONE = ("M_stone", "M_stone_dressed", "M_mortar")

    def cast_wall(p, n, typ, size, prob=None, surfaces=STONE, up=(0, 0, 1)):
        hit = probe.cast(p + n * 0.6, -n, 1.2)
        if hit is None or hit["surface"] not in surfaces:
            return None
        return da.add(typ, hit["pos"], hit["normal"], size, hit["surface"], prob, seed=int(rng.randint(1 << 30)),
                      up=up)

    ops = getattr(g, "OPENINGS", [])

    def near_opening(p, m=0.5):
        for op in ops:
            d = p - (op["O"] + sh)
            x = float(d @ op["t"])
            if abs(x) < op["width"] / 2 + 0.45 + m and -0.3 < p[2] < op.get("head", 2.5) + m:
                if abs(float(d @ op["n"])) < 1.0:
                    return True
        return False
    # ---- wall feet, weather faces, repairs
    for wf in getattr(g, "WALL_FACES", []):
        if wf["kind"] == "path":
            pm = wf["map"]
            for s in np.arange(0.6, pm.total - 0.4, 1.7):
                O, t, n = pm.frame(s)
                p = O + sh + ez * 0.32
                if wf["clip"] is not None and wf["clip"]((O + ez * 0.3)[None])[0]:
                    continue
                if near_opening(p, 0.2):
                    continue
                north = n[1] > 0.5
                typ = "moss" if (north and rng.uniform() < 0.5) else "damp_rise"
                prob = min(1.0, 0.6 + 0.3 * north)
                cast_wall(p, n, typ, (rng.uniform(0.7, 1.1), rng.uniform(0.35, 0.5)), prob)
            for s in np.arange(1.0, pm.total - 0.5, 3.1):
                O, t, n = pm.frame(s)
                z = rng.uniform(1.3, max(1.4, wf["top"](s) - 0.4))
                p = O + sh + ez * z
                if (wf["clip"] is not None and wf["clip"]((O + ez * z)[None])[0]) or near_opening(p, 0.3):
                    continue
                weather = n[0] < -0.5 or n[1] > 0.5
                typ = "lichen" if weather else "repair_patch"
                cast_wall(p, n, typ, (rng.uniform(0.35, 0.6), rng.uniform(0.3, 0.5)))
        else:
            c = np.array([wf["center"][0], wf["center"][1], 0.0]) + sh
            for az in np.radians(np.arange(8.0, 360.0, 24.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                r = float(wf["radius"](0.3))
                O = c + n * r
                if wf["clip"] is not None and wf["clip"]((O - sh + ez * 0.3)[None])[0]:
                    continue
                if near_opening(O + ez * 0.3, 0.2):
                    continue
                typ = "moss" if (n[1] > 0.4 and rng.uniform() < 0.5) else "damp_rise"
                cast_wall(O + ez * 0.32, n, typ, (rng.uniform(0.7, 1.0), rng.uniform(0.35, 0.5)),
                          min(1.0, 0.6 + 0.3 * (n[1] > 0.4)))
            for az in np.radians(np.arange(20.0, 360.0, 52.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                z = rng.uniform(1.0, wf["top"] - 0.35)
                O = c + n * float(wf["radius"](z)) + ez * z
                if (wf["clip"] is not None and wf["clip"]((O - sh)[None])[0]) or near_opening(O, 0.3):
                    continue
                cast_wall(O, n, "lichen" if n[1] > 0.0 else "repair_patch",
                          (rng.uniform(0.35, 0.55), rng.uniform(0.3, 0.45)))
                # the cone's eave drip streaks the wall head under the plate
            for az in np.radians(np.arange(35.0, 360.0, 60.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                z = wf["top"] - 0.15
                O = c + n * float(wf["radius"](z)) + ez * z
                if (wf["clip"] is not None and wf["clip"]((O - sh)[None])[0]) or near_opening(O, 0.3):
                    continue
                below_points(da, probe, [O], [n], "water_streak", size=(0.14, 0.7), surfaces=STONE, rng=rng)
    # ---- openings
    for op in ops:
        O, t, n = op["O"] + sh, op["t"], op["n"]
        mid = O + ez * 0.5 * (op["z0"] + op["z1"])
        hw = op["width"] / 2
        above_opening(da, probe, O, n, op["width"] + 0.2, op["head"] + 0.02, "soot",
                      size=(op["width"] + 0.3, 0.5), surfaces=STONE, rng=rng)
        cs = [O + t * (op["lintel_w"] / 2 + 0.06) + ez * (op["head"] + 0.1),
              O - t * (op["lintel_w"] / 2 + 0.06) + ez * (op["head"] + 0.1)]
        opening_corners(da, probe, cs, n, "crack", size=(0.22, 0.4), surfaces=STONE, rng=rng)
        if op["kind"] == "window":
            below_points(da, probe, [O + ez * (op["sill"] - 0.12) + n * 0.03], [n], "water_streak",
                         size=(op["width"] * 0.8, 0.7), surfaces=STONE, rng=rng)
            opening_corners(da, probe, [O + t * (hw + 0.25) + ez * (op["sill"] - 0.15)], n, "crack",
                            size=(0.2, 0.32), surfaces=STONE, rng=rng)
        else:
            for zs in (op["z0"] + 0.32, op["z1"] - 0.34):
                below_points(da, probe, [O + t * (-hw + 0.25) + ez * zs - n * 0.06], [n], "rust_stain",
                             size=(0.08, 0.3), surfaces=("M_timber_weathered", "M_timber"), rng=rng, drop=0.04)
            for sgn in (-1, 1):
                cast_wall(O + t * sgn * (hw + 0.55) + ez * 1.0, n, "grime", (0.35, 0.9), 0.7)
            if door_lichen == "threshold":                  # round 1-3 behaviour (the walked top: implausible)
                tops(da, probe, [O + n * 0.2 + t * sgn * (hw + 0.1) for sgn in (-1, 1)], "lichen",
                     size=(0.2, 0.15), surfaces=("M_stone_dressed",), rng=rng)
            elif door_lichen == "jamb":
                # round 4 (note 11): on the footing stones beside the door jambs, never on the trodden threshold
                for sgn in (-1, 1):
                    cast_wall(O + t * sgn * (hw + 0.62) + ez * 0.24, n, "lichen", (0.2, 0.15), 0.6)
            if walk_gate:
                from ..decal_gate import door_walk_zone
                if not hasattr(da, "walk_zones"):
                    da.walk_zones = []
                da.walk_zones.append(door_walk_zone(O, n, t, hw + 0.38, depth=1.5, inset=0.35, z_max=0.6))
    # ---- footing tops and quoins (lichen), roofs (moss)
    lo, hi = _bounds(g)
    for wf in getattr(g, "WALL_FACES", []):
        if wf["kind"] != "path":
            continue
        pm = wf["map"]
        for s in np.arange(1.2, pm.total - 0.5, 2.3):
            O, t, n = pm.frame(s)
            if near_opening(O + sh + ez * 0.3, 0.4):
                continue
            tops(da, probe, [O + sh + n * 0.06 + ez * 0.35], "lichen", size=(0.25, 0.15), surfaces=STONE, rng=rng,
                 h_from=0.25)
    for name, roof in getattr(g, "LINEAR_ROOFS", {}).items():
        mat = "M_thatch" if roof.covering == "thatch" else "M_roof_shingle"
        for x in np.arange(roof.xa + 0.6, roof.xb - 0.4, 1.6):
            for sg in (1, -1):
                for u in (0.5, roof.U * 0.55):
                    P = roof.to_world(roof.surf(x, u, sg, 0.0)) + sh
                    if sg < 0 and (rng.uniform() < 0.6 or not south_moss):
                        continue                         # round 4: moss on the north (+y) slope only (note 11)
                    hit = probe.cast(P + ez * 1.5, -ez, 3.0)
                    if hit is None or hit["surface"] != mat or hit["normal"][2] < 0.5:
                        continue
                    nrm = hit["normal"]
                    if moss_normal == "slope":           # round 6: project along the roof slope, not a facet
                        nrm = roof.dir_world(roof.normal(sg))
                    da.add("moss", hit["pos"], nrm, (rng.uniform(0.5, 0.9), rng.uniform(0.4, 0.7)),
                           mat, 0.75 if sg > 0 else 0.4, seed=int(rng.randint(1 << 30)), up=roof.dir_world(
                               np.array([0.0, -sg * math.cos(roof.p), math.sin(roof.p)])))
    if hasattr(g, "R_EAVE"):
        c = np.array([0.0, 0.0, 0.0]) + sh
        for az in np.radians(np.arange(120.0, 260.0, 22.0)):
            for rr in (g.R_EAVE - 0.5, g.R_EAVE - 1.5):
                p = c + np.array([math.sin(az) * rr, -math.cos(az) * rr, 0.0])
                hit = probe.cast(p + ez * 12.0, -ez, 14.0)
                if hit is None or hit["surface"] != "M_roof_shingle":
                    continue
                da.add("moss", hit["pos"], hit["normal"], (0.6, 0.45), "M_roof_shingle", 0.7,
                       seed=int(rng.randint(1 << 30)), up=(0, 0, 1))
    log(f"composite decals: {len(da.items)} anchors before the gate")
    return da
