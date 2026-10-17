"""components.tier_finish -- producer notes 6 and 11 for a tier-module building (kit 1.7.0, v2_tiered_hall).

    tier_hidden_cull(g)    KIT COMPONENT (run after every module; <PREFIX>_FAST=1 skips it): core.visibility_cull
        on the building's stones, roofing, structure, boards and frames with the review viewpoints plus actor rings
        round every ground body, under the eaves, door close-ups and crane stations derived from the declared bodies
        (viewpoints inside a body are dropped).  Backings (mortar, decks, belt backings, opening backings, bands,
        flashings) are never targets, so the cull never opens a hole.
    tier_decals(g, seed)   KIT COMPONENT: note-11 anchors placed from what the recipe declared -- damp rise / moss
        at every ground body's foot (more on the north), lichen and repair patches over the stone faces, soot
        over doors, cracks at frame corners, water streaks below sills, under short-overhang eaves on the wall and,
        for deep eaves, where the drip lands on a lower tier's covering (kit 1.7.1), rust under hinges, moss on the
        eave courses (north-weighted).  The kit's anchor gate
        (assembly spec `decal_validate`) then snaps / drops them.
"""
import math
import os

import numpy as np

from ..core import log, ring_views, visibility_cull
from ..decals import (SurfaceProbe, above_opening, base_ring, below_points, opening_corners, tops,
                      wall_scatter)

NEVER = ("mortar", "deck", "backing", "band", "flashing", "finial", "openings_iron", "coping", "closure", "underlap",
         "collar")


def _targets(g):
    out = []
    for ob in g.coll.all_objects:
        if ob.type != "MESH" or ob.name.startswith(g.prefix + "_peg") or ob.name.startswith(g.prefix + "_nail"):
            continue
        if any(s in ob.name for s in NEVER):
            continue
        if ob.users_collection and ob.users_collection[0].name.endswith("_kit_instances"):
            continue
        out.append(ob.name)
    return out


def tier_views(g):
    """kit 1.7.1 (build-time budget, art bible 8): two actor rings per ground body (eye level just outside the
    face, and a knee-to-waist ring further out looking up under the eaves), one crane ring pair for the whole
    building (deduplicated), and per opening 2 distances x 2 heights x 3 offsets.  The review tool's own
    viewpoints are always added by core.visibility_cull."""
    V = []
    ground = [b for b in g.bodies.values() if b.z0 < 0.5]
    for b in ground:
        R = b.apothem / math.cos(math.pi / max(b.sides, 8))
        for d, z, step in ((0.6, 1.65, 2.0), (2.6, 0.9, 2.6)):
            n = int(np.clip(2 * math.pi * (R + d) / step, 10, 20))
            V += list(ring_views(b.c, R + d, z, n=n))
    E = g.extent()
    for r, z in ((E * 2.2, 8.0), (E * 1.6, 15.0)):
        V += list(ring_views((0.0, 0.0), r, z, n=12, phase=0.21))
    for o in g.openings:                 # doors: 2 distances x 2 heights x 3 offsets; windows: one eye-level row
        grid = ((0.6, 1.8), (0.9, 1.7)) if o["kind"] == "door" else ((1.2,), (1.6,))
        for dist in grid[0]:
            for z in grid[1]:
                for x in (-0.8, 0.0, 0.8):
                    V.append(o["origin"] + o["normal"] * (dist + 0.1) + o["tangent"] * x + np.array([0, 0, z]))
    P = np.array(V)
    inside = g.inside_any(P, list(g.bodies), margin=-0.15, zpad=0.2)
    P = P[~inside]
    _, ix = np.unique(np.round(P, 2), axis=0, return_index=True)
    return P[np.sort(ix)]


def _facing_views(g, ob, P, z_high=6.0):
    """the building viewpoints that face object `ob`: an object that sits on one side of the building (its plan
    centroid well off the building centre, e.g. a turret's parts or one opening's frame) is tested only against the
    views on its own side (in front of the plane through the building centre normal to the centroid direction,
    with the object's own half-size as slack) plus every view above z_high (crane views over the roofs); an object
    wrapped round the centre (a ring of stones, a roof) keeps every view."""
    co = np.array([ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box])
    lo, hi = co.min(0), co.max(0)
    cen = 0.5 * (lo[:2] + hi[:2])
    half = 0.5 * float(np.hypot(*(hi[:2] - lo[:2])))
    d = float(np.hypot(*cen))
    if d < max(half, 1.0):
        return P
    u = cen / d
    side = (P[:, :2] @ u) > (d - half - 1.5)
    return P[side | (P[:, 2] > z_high)]


def cull_procs(procs=None):
    """kit 1.7.3 (build-time budget, art bible 8): worker processes for the hidden-geometry ray test -- `procs` if
    given, else one per physical core less one for the main process (logical CPUs / 2 - 1), between 3 and 6.  The
    result does not depend on it (every polygon's test is independent)."""
    if procs:
        return int(procs)
    return int(np.clip((os.cpu_count() or 6) // 2 - 1, 3, 6))


def tier_hidden_cull(g, extra_targets=(), procs=None, seal=True, seal_kw=None):
    """KIT COMPONENT: see the module doc.  Each object is tested only against the viewpoints that face it.
    procs (kit 1.7.3): ray-test worker processes (cull_procs).  seal (kit 1.7.3): afterwards run the see-through
    check components.seal_probe.through_seal_probe on every roof / through-body junction (also in FAST builds), so
    neither a module nor the cull can ship a see-through; seal_kw: its keywords."""
    import time
    import bpy
    if os.environ.get(f"{g.prefix}_FAST"):
        log("  (hidden-geometry cull skipped: FAST build)")
        n = 0
    else:
        t0 = time.time()
        targets = _targets(g) + list(extra_targets)
        P = tier_views(g)
        by = {nm: _facing_views(g, bpy.data.objects[nm], P) for nm in targets}
        np_ = cull_procs(procs)
        log(f"  hidden-geometry cull: {len(P)} building views (+ the review views), per object "
            f"{min(len(v) for v in by.values())}-{max(len(v) for v in by.values())}, {np_} workers")
        n = visibility_cull(targets, extra_views=(), extra_by_target=by, procs=np_)
        log(f"  hidden-geometry cull: -{n} polygons on {len(targets)} objects in {time.time() - t0:.0f} s")
        from .tier_roof import drop_empty_meshes                  # kit 1.7.2: a fully culled object is removed
        drop_empty_meshes([bpy.data.objects[nm] for nm in targets if nm in bpy.data.objects])
    if seal:
        from .seal_probe import through_seal_probe
        through_seal_probe(g, **(seal_kw or {}))
    return n


def _az(th):
    """decals.* azimuth (from -Y toward +X) of a math plan angle."""
    return th + math.pi / 2


def tier_decals(g, seed=9900):
    """KIT COMPONENT: see the module doc."""
    rng = np.random.RandomState(seed + g.seed_offset)
    da = g.decals
    probe = SurfaceProbe([o for o in g.coll.all_objects if o.type == "MESH"])
    stone = ("M_stone", "M_stone_dressed", "M_mortar")
    stone_bodies = [b for b in g.bodies.values() if b.kind == "stone"]
    n0 = len(da.items)
    for b in stone_bodies:
        R = b.apothem / math.cos(math.pi / 8) + 0.8
        n_az = max(6, int(2 * math.pi * b.apothem / 2.4))
        az = np.linspace(0, 2 * math.pi, n_az, endpoint=False) + rng.uniform(0, 0.4)
        if b.z0 < 0.5:
            base_ring(da, probe, b.c, R, az, 0.26, "damp_rise", (0.9, 0.42), stone, rng=rng, up_shift=0.0)
            base_ring(da, probe, b.c, R, az[::3] + 0.17, 0.42, "moss", (0.45, 0.22), stone, north_gain=1.0, rng=rng,
                      up_shift=0.0)
            zr = (0.5, min(b.z1 - 0.4, 2.8))
        else:
            zr = (b.z0 + 0.3, b.z1 - 0.3)
        if zr[1] > zr[0]:
            wall_scatter(da, probe, b.c, R, max(2, n_az // 3), zr, "lichen", ((0.25, 0.45), (0.2, 0.4)), stone,
                         rng=rng, min_sep=1.2)
            wall_scatter(da, probe, b.c, R, max(1, n_az // 4), zr, "repair_patch", ((0.3, 0.5), (0.25, 0.45)), stone,
                         rng=rng, min_sep=1.5)
    # openings: soot over doors, cracks at the frame corners, streaks below sills, rust under the hinges
    for o in g.openings:
        nrm, tng, org = o["normal"], o["tangent"], o["origin"]
        hw = o["hw"] + o["jamb"]
        head = o["_ztop"]
        if o["kind"] == "door":
            above_opening(da, probe, org[:2] + nrm[:2] * 0.0, nrm, 2 * hw, head + 0.02, "soot", (1.0, 0.5), stone,
                          rng=rng)
            for zh in (o["z_clear0"] + 0.32, o["head"] - 0.36):
                P = org + tng * (-o["hw"] * 0.2) + np.array([0, 0, zh - 0.03])
                below_points(da, probe, [P], [nrm], "rust_stain", (0.08, 0.3), ("M_timber",), rng=rng, reach=0.5)
        else:
            sill = org + np.array([0, 0, o["_zbot"] - 0.03])
            below_points(da, probe, [sill + tng * x for x in (-0.15, 0.15)], [nrm, nrm], "water_streak",
                         (0.12, 0.55), stone, rng=rng)
        corners = [org + tng * (s * (hw + 0.12)) + np.array([0, 0, z]) for s in (-1, 1) for z in (head + 0.12,)]
        opening_corners(da, probe, corners, nrm, "crack", (0.22, 0.32), stone, rng=rng)
    # eave drip lines (kit 1.7.1, note 11 plausibility): a tier whose lip overhangs its body by <= short_drip
    # streaks the wall under it; a deeper eave throws its drip clear of the wall, so the anchor goes where the drip
    # LANDS -- on the covering of a lower tier (a drip-line streak on the shingles) -- or nowhere (the ground)
    short_drip = 0.30
    for name, t in g.roofs.items():
        roof = t["roof"]
        under = g.body(t["on"])
        over = float(roof.p_lip) - float(t["p_wall"])
        for k in range(8):
            if rng.uniform() > 0.6:
                continue
            ph = roof.rot + math.radians(45 * k + rng.uniform(-12, 12))
            u = np.array([math.cos(ph), math.sin(ph), 0.0])
            if over <= short_drip:
                if under.kind == "stone":
                    P = under.point(np.array(ph), np.array(min(t["z_lip"] - 0.05, under.z1 - 0.2)))
                    below_points(da, probe, [P], [u], "water_streak", (0.14, 0.7), stone, rng=rng)
                continue
            Q = np.array([roof.c[0], roof.c[1], t["z_lip"] - 0.08]) + u * (roof.p_lip + 0.05)
            hit = probe.cast(Q, (0.0, 0.0, -1.0), 30.0)
            if hit is None or hit["surface"] != "M_roof_shingle" or hit["pos"][2] < 0.5 or hit["normal"][2] < 0.3:
                continue
            da.add("water_streak", hit["pos"], hit["normal"], (rng.uniform(0.5, 0.8), 0.3), hit["surface"],
                   seed=int(rng.randint(1 << 30)), up=(0.0, 0.0, 1.0))
        pts = []
        for k in range(8):
            ph = roof.rot + math.radians(45 * k + rng.uniform(-14, 14))
            p = roof.p_lip - 0.35
            pts.append((roof.c[0] + p * math.cos(ph), roof.c[1] + p * math.sin(ph)))
        tops(da, probe, pts, "moss", (0.5, 0.35), ("M_roof_shingle",), north_gain=1.2, rng=rng)
    n_snap = _macro_snap(g, da, probe, n0)
    log(f"  tier decals: {len(da.items) - n0} anchors placed {da.counts()}, {n_snap} wall anchors on macro normals")


def _macro_snap(g, da, probe, start):
    """wall anchors take their body's MACRO normal (facet / radial, not a stone side or chamfer) and are re-cast
    onto the real surface along it, so the anchor gate judges them against the wall plane they decorate."""
    from ..decals import decal_frame
    n_ok = 0
    for it in da.items[start:]:
        if abs(it["normal"][2]) > 0.6:
            continue
        p = np.asarray(it["pos"], float)
        best, bd = None, 0.4
        for b in g.bodies.values():
            if b.kind != "stone" or not (b.z0 - 0.1 < p[2] < b.z1 + 0.1):
                continue
            d = abs(float(b.dist(p[None])[0]))
            if d < bd:
                best, bd = b, d
        if best is None:
            continue
        th = math.atan2(p[1] - best.c[1], p[0] - best.c[0])
        thn = best.facet_normal(th)
        n = np.array([math.cos(thn), math.sin(thn), best.bat])
        n /= np.linalg.norm(n)
        hit = probe.cast(p + n * 0.35, -n, 0.7)
        if hit is None or hit["surface"] not in ("M_stone", "M_stone_dressed", "M_mortar"):
            continue
        r, u, nn = decal_frame(n, (0.0, 0.0, 1.0))
        it.update(pos=hit["pos"] + n * 0.004, normal=nn, up=u, right=r, surface=hit["surface"])
        n_ok += 1
    return n_ok
