"""components.tier_cull -- a hidden-geometry cull with a work budget for tier-module buildings (kit 1.10.2 proposal,
v2_tiered_hall round 5).  NEW module: tier_finish.tier_hidden_cull is unchanged.

    tier_hidden_cull_lean(g, max_views=40, ...)    KIT COMPONENT (run after every module; <PREFIX>_FAST=1 skips the
        ray test).  The same targets, building viewpoints and per-object facing selection as
        tier_finish.tier_hidden_cull, but the WORK is cut, not only spread over more workers (art bible 8: a build
        under about 10 minutes on 4 shared cores):
          * every object is tested against at most `max_views` building viewpoints (plus the review tool's own
            viewpoints, which core.visibility_cull always adds): the door close-up viewpoints are always kept, the
            rest is a deterministic farthest-point subset of the views that face the object, so the kept views
            still surround it at every height (eye-level rings, the under-eave ring, crane rings).  The cost of a
            hidden polygon is proportional to the views it is tested against; on v2 the big wrapped objects (hall
            stones, skirt shingles and structure, drum stones) drop from 109 + 77 to 40 + 77 views;
          * `skip`: objects (name substrings) that are not ray-tested at all.
        Then, as tier_hidden_cull: zero-face objects are dropped and the see-through check
        (seal_probe.through_seal_probe) runs on the shipped geometry, also in FAST builds.
"""
import os
import time

import numpy as np

from ..core import log, visibility_cull
from .tier_finish import _facing_views, _targets, cull_procs, tier_views


def _door_views(g, P, reach=1.6, z_max=2.4):
    """mask of viewpoints that belong to a door close-up (within `reach` of a door origin, below z_max)."""
    keep = np.zeros(len(P), bool)
    for o in g.openings:
        if o["kind"] != "door":
            continue
        d = np.linalg.norm(P[:, :2] - np.asarray(o["origin"], float)[:2], axis=1)
        keep |= (d < reach) & (P[:, 2] < z_max)
    return keep


def cap_views(P, n, must=None):
    """KIT HELPER: at most n of the viewpoints P -- every `must` view, then a deterministic farthest-point fill
    (starting from the lowest, then the farthest from all chosen), returned in their original order."""
    P = np.asarray(P, float)
    if len(P) <= n:
        return P
    must = np.zeros(len(P), bool) if must is None else np.asarray(must, bool)
    chosen = list(np.flatnonzero(must))
    if not chosen:
        chosen = [int(np.lexsort((P[:, 0], P[:, 1], P[:, 2]))[0])]
    dmin = np.min(np.linalg.norm(P[:, None, :] - P[None, chosen, :], axis=2), axis=1)
    while len(chosen) < n:
        k = int(np.argmax(dmin))
        if dmin[k] <= 0:
            break
        chosen.append(k)
        dmin = np.minimum(dmin, np.linalg.norm(P - P[k], axis=1))
    return P[np.sort(np.array(chosen))]


def tier_hidden_cull_lean(g, max_views=40, skip=(), extra_targets=(), procs=None, seal=True, seal_kw=None):
    """KIT COMPONENT: see the module doc."""
    import bpy
    if os.environ.get(f"{g.prefix}_FAST"):
        log("  (hidden-geometry cull skipped: FAST build)")
        n = 0
    else:
        t0 = time.time()
        targets = [nm for nm in _targets(g) + list(extra_targets) if not any(s in nm for s in skip)]
        P = tier_views(g)
        doors = _door_views(g, P)
        by = {}
        for nm in targets:
            Pf = _facing_views(g, bpy.data.objects[nm], P)
            by[nm] = cap_views(Pf, max_views, must=_door_views(g, Pf))
        np_ = cull_procs(procs)
        log(f"  hidden-geometry cull (lean): {len(P)} building views ({int(doors.sum())} door), per object "
            f"{min(len(v) for v in by.values())}-{max(len(v) for v in by.values())} (cap {max_views}) + the review "
            f"views, {len(targets)} targets, skip {list(skip)}, {np_} workers")
        n = visibility_cull(targets, extra_views=(), extra_by_target=by, procs=np_)
        log(f"  hidden-geometry cull: -{n} polygons on {len(targets)} objects in {time.time() - t0:.0f} s")
        from .tier_roof import drop_empty_meshes
        drop_empty_meshes([bpy.data.objects[nm] for nm in targets if nm in bpy.data.objects])
    if seal:
        from .seal_probe import through_seal_probe
        through_seal_probe(g, **(seal_kw or {}))
    return n
