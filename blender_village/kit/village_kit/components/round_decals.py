"""components.round_decals -- producer note 11 decal anchors for a round wattle-and-daub building.

round_building_decals(g) places ~80-120 anchors on the built meshes of frame g with the village_kit.decals rules:
    damp_rise   coat foot all round (north faces more likely)          moss   plinth faces at the ground, north roof
    lichen      plinth stone tops, step and threshold tops             water_streak  below the collar drip, lintel ends
    soot        above the door head and round the smoke outlet under the apex collar
    rust_stain  under the strap hinges, pintles, nails and ring pull   grime  hand height at the door
    crack       the daub shrinkage cracks dropped from the geometry (same places), the corners of the exposed
                patches and of the door bay, settlement cracks under the plate beside the posts
    plaster_patch / repair_patch   scattered over the intact daub
"""
import math

import numpy as np

from ..core import log
from .. import decals as D


def _wall_point(g, s, z, r_extra=0.0):
    a = s / g.R_WALL
    r = g.R_WALL + g.COAT_R_NOM + r_extra
    return np.array([math.sin(a) * r, -math.cos(a) * r, z]), np.array([math.sin(a), -math.cos(a), 0.0])


def round_building_decals(g, seed=8800, max_cracks=22):
    import bpy
    rng = np.random.RandomState(seed)
    da = g.decals
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    probe = D.SurfaceProbe(obs)
    n0 = len(da)
    door = g.WALL_POST_AZ_DOOR
    R_out = g.R_EAVE + 1.0
    # ---- damp_rise on the coat foot, moss on the plinth faces at the ground (north faces more likely)
    az_w = [a for a in np.linspace(0, 2 * math.pi, 15, endpoint=False) + 0.2 if door + 0.12 < a < 2 * math.pi - door - 0.12]
    D.base_ring(da, probe, (0, 0), R_out, az_w, lambda a: g.PLINTH_TOP + 0.14, "damp_rise", (0.9, 0.45),
                surfaces={"M_daub"}, rng=rng, up_shift=0.18)
    az_p = np.linspace(0, 2 * math.pi, 10, endpoint=False) + 0.31
    az_p = [a for a in az_p if abs(math.atan2(math.sin(a), math.cos(a))) > door + 0.1]
    D.base_ring(da, probe, (0, 0), R_out, az_p, 0.10, "moss", (0.55, 0.25), surfaces={"M_stone"}, rng=rng,
                up_shift=0.06)
    # ---- lichen on stone tops (plinth, step, threshold)
    az_t = rng.uniform(0, 2 * math.pi, 16)
    pts = [(math.sin(a) * (g.R_PL_FACE - 0.07), -math.cos(a) * (g.R_PL_FACE - 0.07), 0.6) for a in az_t
           if abs(math.atan2(math.sin(a), math.cos(a))) > door + 0.08]
    D.tops(da, probe, pts[:10], "lichen", (0.25, 0.2), surfaces={"M_stone"}, rng=rng)
    D.tops(da, probe, [(g.STEP_C[0] + 0.2, g.STEP_C[1], 0.5), (-0.62, g.FRONT_Y - 0.03, 0.5)], "lichen",
           (0.22, 0.18), surfaces={"M_stone"}, rng=rng)
    # ---- roof: moss on the north (+Y) shingle butts near the eave and mid-slope
    for az in rng.uniform(math.pi * 0.7, math.pi * 1.3, 6):
        for r in ((g.R_EAVE - 0.35) if rng.rand() < 0.6 else (g.R_EAVE - 1.6),):
            hit = probe.cast((math.sin(az) * r, -math.cos(az) * r, 12.0), (0, 0, -1), 14.0)
            da.add_hit("moss", hit, (0.7, 0.5), probability=0.65, seed=int(rng.randint(1 << 30)),
                       surfaces={"M_roof_shingle"})
    # ---- water streaks below the collar drip, soot round the smoke outlet under the collar
    zc = None
    for o in obs:
        if o.name == f"{g.prefix}_cap_collar":
            zc = min(v.co.z for v in o.data.vertices)
    zc = zc if zc is not None else 6.7
    for k, az in enumerate(np.linspace(0, 2 * math.pi, 6, endpoint=False) + 0.4):
        r = g.COLLAR_R + 0.25
        hit = probe.cast((math.sin(az) * r, -math.cos(az) * r, zc + 1.0), (0, 0, -1), 3.0)
        da.add_hit("water_streak", hit, (0.22, 0.7), seed=int(rng.randint(1 << 30)), surfaces={"M_roof_shingle"},
                   shift_down=0.2)
    for az in np.linspace(0, 2 * math.pi, 4, endpoint=False) + 1.1:
        r = g.COLLAR_R + 0.08
        hit = probe.cast((math.sin(az) * r, -math.cos(az) * r, zc + 1.0), (0, 0, -1), 3.0)
        da.add_hit("soot", hit, (0.5, 0.4), probability=0.6, seed=int(rng.randint(1 << 30)),
                   surfaces={"M_roof_shingle"})
    # ---- door: soot over the head, streaks below the lintel ends, grime at hand height, rust under ironwork
    D.above_opening(da, probe, (0.0, g.FRONT_Y), (0, -1, 0), 1.1, g.HEAD_Z, "soot", (1.0, 0.35),
                    surfaces={"M_timber", "M_timber_weathered"}, rng=rng)
    D.below_points(da, probe, [(-1.05, g.FRONT_Y, g.HEAD_Z + 0.02), (1.05, g.FRONT_Y, g.HEAD_Z + 0.02)],
                   [(0, -1, 0)] * 2, "water_streak", (0.12, 0.8), surfaces={"M_timber"}, rng=rng)
    D.opening_corners(da, probe, [(-0.62, g.FRONT_Y + 0.05, 1.05), (0.62, g.FRONT_Y + 0.05, 1.05),
                                  (-1.0, g.FRONT_Y + 0.05, 1.15), (1.0, g.FRONT_Y + 0.05, 1.0)], (0, -1, 0),
                      "grime", (0.18, 0.45), surfaces={"M_timber"}, rng=rng)
    iron_pts, iron_dirs = [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.name.startswith(g.prefix):
            continue
        M = np.array(o.matrix_world)
        if "_door_hinge_strap_" in o.name:
            iron_pts.append(M[:3, :3] @ np.array([-0.35, 0.0, -0.035]) + M[:3, 3])
            iron_dirs.append(M[:3, :3] @ np.array([0.0, -1.0, 0.0]))
        elif "_door_hinge_pintle_" in o.name:
            iron_pts.append(M[:3, 3] + np.array([0.0, 0.0, -0.06]))
            iron_dirs.append(np.array([0.0, -1.0, 0.0]))
    D.below_points(da, probe, iron_pts, iron_dirs, "rust_stain", (0.08, 0.3), surfaces={"M_timber"}, rng=rng,
                   reach=0.15)
    for o in obs:
        if o.name == f"{g.prefix}_door_ironwork":
            co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
            c = co.mean(0)
            leaf_out = (math.sin(math.radians(-75.0)), -math.cos(math.radians(-75.0)), 0.0)   # leaf open 75 deg
            D.below_points(da, probe, [c + np.array([0, 0, -0.05])], [leaf_out], "rust_stain", (0.07, 0.25),
                           surfaces={"M_timber"}, rng=rng, reach=0.12)
    # ---- cracks: the shrinkage cracks dropped from the daub geometry (longest first), patch corners, settlement
    cr = sorted(g.DAUB_CRACKS, key=lambda c: -float(np.sum(np.linalg.norm(np.diff(c[1], axis=0), axis=1))))
    n_cr = 0
    for (bay, pts, wd) in cr:
        if n_cr >= max_cracks:
            break
        L = float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
        if L < 0.1:
            continue
        c = pts.mean(0)
        d = pts[-1] - pts[0]
        p, u = _wall_point(g, c[0], c[1], 0.15)
        hit = probe.cast(p, -u, 0.4)
        if hit is None or hit["surface"] != "M_daub":
            continue
        a = c[0] / g.R_WALL
        t3 = np.array([math.cos(a), math.sin(a), 0.0])
        up = t3 * d[0] + np.array([0, 0, 1.0]) * d[1]
        da.add("crack", hit["pos"], hit["normal"], (max(0.08, 0.35 * L), max(0.15, L)), "M_daub", 0.6,
               int(rng.randint(1 << 30)), up=up if np.linalg.norm(up) > 1e-6 else (0, 0, 1))
        n_cr += 1
    for (bay, kind, cf, cz, hs, hz, sd) in g.DAUB_PATCHES:
        a0, a1 = g.POST_AZ[bay], g.POST_AZ[bay + 1]
        s_c = (a0 + cf * (a1 - a0)) * g.R_WALL
        for (ds, dz) in ((-hs, hz), (hs, hz), (-hs, -hz), (hs, -hz))[: (4 if kind == "hole" else 2)]:
            p, u = _wall_point(g, s_c + ds * 1.08, cz + dz * 1.12, 0.15)
            da.add_hit("crack", probe.cast(p, -u, 0.4), (0.18, 0.3), seed=int(rng.randint(1 << 30)),
                       surfaces={"M_daub"})
    for k in range(1, len(g.POST_AZ) - 1, 3):
        p, u = _wall_point(g, g.POST_AZ[k] * g.R_WALL + 0.16 * (1 if k % 2 else -1), g.PLATE_BOT - 0.2, 0.15)
        da.add_hit("crack", probe.cast(p, -u, 0.4), (0.2, 0.4), seed=int(rng.randint(1 << 30)), surfaces={"M_daub"})
    # ---- plaster / repair patches over the intact coat
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), R_out, 8, (0.7, g.PLATE_BOT - 0.35), "plaster_patch", ((0.35, 0.7), (0.3, 0.6)),
                   surfaces={"M_daub"}, rng=rng, az_range=(door + 0.15, 2 * math.pi - door - 0.15), avoid=avoid,
                   min_sep=0.55)
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), R_out, 5, (0.5, g.PLATE_BOT - 0.3), "repair_patch", ((0.25, 0.5), (0.25, 0.45)),
                   surfaces={"M_daub"}, rng=rng, az_range=(door + 0.15, 2 * math.pi - door - 0.15), avoid=avoid,
                   min_sep=0.5)
    log(f"decal anchors placed: {len(da) - n0}  {da.counts()}")
    return len(da) - n0
