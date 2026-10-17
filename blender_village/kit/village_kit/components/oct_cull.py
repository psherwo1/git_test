"""components.oct_cull -- producer note 6 for an OctFrame building: delete the polygons no exterior / actor viewpoint
can see (core.visibility_cull with the review viewpoints plus actor rings under and outside the skirt eave, low ground
views, stations along the annex walls and round the turret, close crane views of the upper tiers, off-ring crane
stations and door close-ups).  Backing surfaces (mortar bodies, decks, thatch core / courses / rolls, blockers) are
never targets, so a cull never opens a hole.

oct_hidden_cull(g, targets=None)   KIT COMPONENT (run last, after every component; KEEP_FAST=1 skips it)
"""
import math
import os

import numpy as np

from ..core import log, visibility_cull
from .oct_frame import FR, fmap, oct_pp

# parts whose never-seen faces are deleted (roof level, structure, stone bodies, timber); close-up hero pieces that
# must stay whole (door ironwork, dressed surrounds, eave roll) and every backing surface are left out
CULL_PARTS = ["roof_collar_shakes", "cap_structure", "turret_cap_structure", "turret_drum", "cap_shingles",
              "turret_cap_shingles", "roof_skirt_boards", "roof_skirt_structure", "hall_eave_plate", "cap_hips",
              "turret_cap_hips", "roof_skirt_hips", "lantern_boards", "lantern_frame", "cone_ledge_slabs",
              "wing_roof_structure", "hall_posts", "hall_post_bases", "hall_knee_braces", "door_leaf", "wing_door",
              "wing_window", "threshold", "hall_window_frames", "wing_ridge_comb", "turret_stones", "wing_wall_stones",
              "turret_corbel_collar"]


def door_views():
    """close-up positions in front of both doors (0.5-2 m out, knee to above head height, either side)."""
    V = []
    k = 3
    for dist in (0.5, 1.0, 2.0):
        for z in (0.4, 1.1, 1.7, 2.3):
            for x in (-0.9, 0.0, 0.9):
                V.append(fmap(k, np.array([FR.OPENINGS[0]["xc"] + x]), np.array([z]), np.array([dist]))[0])
                V.append((FR.WDOOR["xc"] + x, FR.WY_S - dist, z))
    return np.array(V)


def near_views():
    """actor-scale viewpoints close to the building (so nothing an actor could see near the walls / under the
    eaves is ever removed): rings round the hall under and outside the skirt eave, low ground views, along the
    wing walls and round the turret, plus close crane views of the upper tiers."""
    V = []
    for r, z, n in ((4.75, 1.65, 28), (6.2, 1.65, 20), (5.0, 0.6, 14), (7.5, 3.0, 14), (6.5, 9.0, 10), (3.5, 13.5, 6)):
        for k in range(n):
            a = 2 * math.pi * (k + 0.37) / n
            V.append((r * math.cos(a), r * math.sin(a), z))
    for x in np.arange(-10.6, -1.2, 1.3):
        for y in (FR.WY_S - 0.35, FR.WY_S - 1.6, FR.WY_N + 0.35, FR.WY_N + 1.6):
            V.append((x, y, 1.65))
    for y in np.arange(-0.8, 6.0, 1.3):
        V += [(FR.WX_W - 0.35, y, 1.65), (FR.WX_W - 1.6, y, 1.65)]
    for k in range(10):
        a = 2 * math.pi * k / 10
        V.append((FR.TUR_C[0] + 3.6 * math.cos(a), FR.TUR_C[1] + 3.6 * math.sin(a), 6.0))
    # off-ring crane stations (elevation 25-40 deg, azimuths between the review stations): the cull must not
    # open anything a camera between the review rings would see
    for k in range(12):
        a = 2 * math.pi * (k + 0.29) / 12
        for r, z in ((15.0, 9.5), (19.0, 16.0)):
            V.append((-2.5 + r * math.cos(a), r * math.sin(a), z))
    P = np.array(V)
    inside = (oct_pp(P[:, 0], P[:, 1]) < FR.A0 + 0.1) | ((P[:, 0] > FR.WX_W - 0.1) & (P[:, 0] < FR.WX_E + 0.1) &
                                                    (P[:, 1] > FR.WY_S - 0.1) & (P[:, 1] < FR.WY_N + 0.1) & (P[:, 2] < 6.5))
    return P[~inside]



def oct_hidden_cull(g, targets=None):
    """KIT COMPONENT: the hidden-geometry cull of an OctFrame building (see the module doc)."""
    if os.environ.get(f"{g.prefix}_FAST"):
        log("  (hidden-geometry cull skipped: FAST build)")
        return 0
    targets = [g.name(p) for p in (targets or CULL_PARTS)]
    dv = door_views()
    extra = {g.name(p): dv for p in ("door_leaf", "wing_door", "threshold", "hall_posts", "hall_post_bases")}
    n = visibility_cull(targets, near_views(), extra_by_target=extra)
    log(f"  hidden-geometry cull: -{n} polygons")
    return n
