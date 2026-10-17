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
              abut_soakers=False, abut_top_trim=False, abut_rake_deg=None, abut_min_keep=0.2):
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
    for it to be cut rather than dropped whole (cone_keep_out(top_min_keep=...))."""
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
        cone_keep_out(g, roofs, lift=abut_lift, rule=abut_rule, tuck=abut_tuck, trim=abut_trim,
                      soffit_cut=bool(soffit and soffit_cut), soakers=abut_soakers, top_trim=abut_top_trim,
                      top_rake_deg=abut_rake_deg, top_min_keep=abut_min_keep)


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


def cone_soakers(g, units_V, roofs, reach=0.30, lap=0.035, cell=0.02, z0=0.002, t=0.006, mat="M_lead",
                 name="cone_soakers", always=()):
    """KIT COMPONENT (round 4, part of cone_keep_out(soakers=True)): ONE continuous lead soaker sheet on a RoundFrame
    cone's reference surface under every covering unit the keep-out dropped within `reach` m of the roof it meets
    (|GableRoof.top_depth| <= reach), each footprint grown by `lap` so the sheet runs under the neighbouring kept
    units and under the thatch.  Where both roofs yield (the thatch clipped under the cone, the cone units dropped
    inside the thatch solid) the pit shows lead, never a dark void.  The footprints are rasterised on a (azimuth,
    slope) grid of `cell` m and the sheet is a closed slab (top, underside, side faces on its outline).
    units_V: list of (n, 3) world vertex arrays of the dropped units.  -> <P>_cone_soakers (or None)
    round 5: always -- vertex arrays laid under whatever their distance to the roof (the removed parts of units cut
    by cone_keep_out(top_trim=True), including those in front of the roof's eave roll, outside its columns)."""
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
    if not M.any():
        return None
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


def cone_keep_out(g, roofs, lift=0.02, rule="tuck", tuck=0.15, trim=False, soffit_cut=False, soakers=False,
                  soaker_reach=0.30, top_trim=False, top_min_keep=0.2, top_rake_deg=None):
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
    roll, not in a vertical stack of cut plates."""
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
    field = roof_cut_field(roofs, lift=lift + 0.003, rake_deg=top_rake_deg) if top_trim else None
    rake = field is not None and top_rake_deg is not None

    def rake_mark(V):
        m = np.zeros(len(V), bool)
        for r in roofs:
            m |= r.eave_zone(V)
        return m & (field(V) < 0)
    for nm in COVER_UNITS + STRUCT_FACES:
        ob = bpy.data.objects.get(f"{g.prefix}_{nm}")
        if ob is None or ob.type != "MESH":
            continue
        if nm == "roof_soffit_deck" and soffit_cut:
            continue                                   # built already cut (cone_soffit(cut=...)), end faces closed
        if field is not None and nm in COVER_UNITS:
            # round 5: cut on the roof's top / eave plane in the eave band (one line along the roll), then the rest
            rm = [] if (soakers and nm in ("roof_shingles", "roof_starter")) else None
            if rake and rm is not None:                # the whole footprint of every unit the rake touches
                rm += _island_vertex_sets(ob, rake_mark)
            cut_info[nm] = trim_units_field(ob, rake_mark if rake else eave_mark, field, removed=rm,
                                            min_keep=top_min_keep)
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
    if soakers and removed:
        log(f"  cut units: {len(removed)} removed parts are soaker footprints too")
    if soakers and (drop_sets or removed):
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
def composite_decals(g, seed=1201, door_lichen="jamb", south_moss=False, walk_gate=True):
    """anchors on the composite's surfaces, all ray-snapped onto the built meshes (decals.SurfaceProbe), physically
    placed: damp_rise / moss at the wall feet (more and likelier on north faces), lichen on footing tops, quoins and
    weather (W / N) faces, water_streak under sills and the cone eave drip, soot over the door and windows, rust under
    the door straps, cracks at opening corners and lintel ends, grime beside the door, repair patches on the walls,
    moss on the north roof slopes and the cone's north shingle butts.  The kit gate (anchor_validate, the building
    spec's decal_validate) then snaps / drops them.
    round 4: door_lichen="jamb" (the footing stones beside the jambs; "threshold": the round 1-3 walked top),
    south_moss=False (thatch moss on the north slope only), walk_gate=True: each door's trodden zone
    (decal_gate.door_walk_zone) is published on da.walk_zones for anchor_validate(walk_zones="da")."""
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
                    da.add("moss", hit["pos"], hit["normal"], (rng.uniform(0.5, 0.9), rng.uniform(0.4, 0.7)),
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
