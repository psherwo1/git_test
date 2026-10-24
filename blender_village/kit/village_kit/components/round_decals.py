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


def _patch_spans(g, kinds=("low",), pad=0.0):
    """azimuth spans (a0, a1) of the exposed-wattle patches of the given kinds (+ pad metres of wall)."""
    out = []
    for (bay, kind, cf, cz, hs, hz, sd) in g.DAUB_PATCHES:
        if kind not in kinds:
            continue
        a0, a1 = g.POST_AZ[bay], g.POST_AZ[bay + 1]
        ac = a0 + cf * (a1 - a0)
        da_ = (hs + pad) / g.R_WALL
        out.append((ac - da_, ac + da_))
    return out


def _clear_of(az, half, spans):
    """az moved (if needed) so that [az - half, az + half] does not overlap any span."""
    for (s0, s1) in spans:
        if az + half > s0 and az - half < s1:
            az = s0 - half if abs(az - s0) < abs(az - s1) else s1 + half
    return az


def round_building_decals(g, seed=8800, max_cracks=22, layout=1):
    """layout=1: the kit 1.0.0 placement.  layout=2 (kit 1.3.0, director r8 #3): the damp_rise / plinth-moss rings
    jittered (+-8 cm, +-6 deg: no printed ring) and kept clear of the low exposed-wattle patches, the lintel-end
    water streaks on the front faces of the door-frame posts, the threshold lichen on the left door-post pad stone,
    plaster / repair patches balanced between the +X and -X halves.  Use with build_building(decal_validate=...).
    layout=4 (kit 1.6.0, sign-off audit r10): one damp_rise per bay centred between the posts (width capped to the
    span 0.12 m clear of each post flank), the door-head soot on the lintel front clipped above the opening, patch
    corner cracks starting 3 cm out along the corner bisector, settlement cracks ending >= 5 cm under the plate,
    plaster / repair patches only where the whole rectangle is >= 5 cm inside intact coat (daub field) and the
    footprint passes anchor_validate.strict_footprint.  Use with validate_anchors(strict=STRICT_R11)."""
    import bpy
    rng = np.random.RandomState(seed)
    rj = np.random.RandomState(seed + 1)          # layout 2 jitter: its own stream (main draws unchanged)
    da = g.decals
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    probe = D.SurfaceProbe(obs)
    n0 = len(da)
    door = g.WALL_POST_AZ_DOOR
    R_out = g.R_EAVE + 1.0
    # ---- damp_rise on the coat foot, moss on the plinth faces at the ground (north faces more likely)
    az_w = [a for a in np.linspace(0, 2 * math.pi, 15, endpoint=False) + 0.2 if door + 0.12 < a < 2 * math.pi - door - 0.12]
    z_w = lambda a: g.PLINTH_TOP + 0.14  # noqa: E731
    size_w = (0.9, 0.45)
    if layout >= 4:
        # kit 1.6.0 (sign-off audit r10 c): one damp_rise per bay, centred between the posts (+-4 cm), never within
        # 0.12 m of a post flank (its width is capped to the clear span), not on the low exposed-wattle patches
        from .frame import bay_s
        nb_ = len(g.POST_AZ) - 1
        low_bays = {p[0] for p in g.DAUB_PATCHES if p[1] == "low"}
        az_w, w_cap = [], {}
        for b_ in range(nb_ - 1):                         # the last bay is the door bay (its eroded band)
            if b_ in low_bays:
                continue
            s0_, s1_ = bay_s(g, b_)
            clear_ = (s1_ - s0_) - 2 * (max(g.POST_RAD[b_], g.POST_RAD[b_ + 1]) + 0.12)
            if clear_ < 0.45:
                continue
            a_ = (0.5 * (s0_ + s1_) + rj.uniform(-0.04, 0.04)) / g.R_WALL
            az_w.append(a_)
            w_cap[round(a_, 6)] = clear_
        dz_w = {round(a, 6): rj.uniform(-0.08, 0.08) for a in az_w}
        z_w = lambda a: g.PLINTH_TOP + 0.14 + max(dz_w.get(round(a, 6), 0.0), -0.04)  # noqa: E731
        size_w = (min(0.9, min(w_cap.values()) / 1.25), 0.45)
    elif layout >= 2:
        spans = _patch_spans(g, ("low",), pad=0.05)
        az_w = [_clear_of(a + math.radians(rj.uniform(-6, 6)), 0.5 * 0.9 * 1.25 / g.R_WALL, spans) for a in az_w]
        dz_w = {round(a, 6): rj.uniform(-0.08, 0.08) for a in az_w}
        z_w = lambda a: g.PLINTH_TOP + 0.14 + max(dz_w.get(round(a, 6), 0.0), -0.04)  # noqa: E731
    D.base_ring(da, probe, (0, 0), R_out, az_w, z_w, "damp_rise", size_w,
                surfaces={"M_daub"}, rng=rng, up_shift=0.18)
    az_p = np.linspace(0, 2 * math.pi, 10, endpoint=False) + 0.31
    az_p = [a for a in az_p if abs(math.atan2(math.sin(a), math.cos(a))) > door + 0.1]
    if layout >= 2:
        az_p = [a + math.radians(rj.uniform(-6, 6)) for a in az_p]
    D.base_ring(da, probe, (0, 0), R_out, az_p, 0.10, "moss", (0.55, 0.25), surfaces={"M_stone"}, rng=rng,
                up_shift=0.06)
    # ---- lichen on stone tops (plinth, step, threshold)
    az_t = rng.uniform(0, 2 * math.pi, 16)
    pts = [(math.sin(a) * (g.R_PL_FACE - 0.07), -math.cos(a) * (g.R_PL_FACE - 0.07), 0.6) for a in az_t
           if abs(math.atan2(math.sin(a), math.cos(a))) > door + 0.08]
    D.tops(da, probe, pts[:10], "lichen", (0.25, 0.2), surfaces={"M_stone"}, rng=rng)
    thr_pt = (-1.04, g.FRONT_Y + 0.11, 0.5) if layout >= 2 else (-0.62, g.FRONT_Y - 0.03, 0.5)
    step_pt = (g.STEP_C[0] + 0.2, g.STEP_C[1], 0.5)
    if layout >= 3:
        # kit 1.5.0 (director r9 #4b): no lichen on the trodden step -- it goes on the plinth's weather top just
        # right of the door instead (off the walking line)
        a_l = g.WALL_POST_AZ_DOOR + 0.33
        step_pt = (math.sin(a_l) * (g.R_PL_FACE - 0.08), -math.cos(a_l) * (g.R_PL_FACE - 0.08), 0.6)
    D.tops(da, probe, [step_pt, thr_pt], "lichen",
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
        if layout >= 2:      # the streak centre 0.2 m down-slope is found by its own ray (lands ON the shingles)
            r += 0.2 * math.cos(g.PITCH)
        hit = probe.cast((math.sin(az) * r, -math.cos(az) * r, zc + 1.0), (0, 0, -1), 3.0)
        da.add_hit("water_streak", hit, (0.22, 0.7), seed=int(rng.randint(1 << 30)), surfaces={"M_roof_shingle"},
                   shift_down=0.2 if layout < 2 else 0.0)
    for az in np.linspace(0, 2 * math.pi, 4, endpoint=False) + 1.1:
        r = g.COLLAR_R + 0.08
        if layout >= 3:
            # kit 1.5.0 (director r9 #4): the smoke-seep soot takes the cone's MACRO normal at its azimuth (never a
            # shingle side / butt face), its centre 0.15 m below the drip so the footprint stays on the shingles;
            # the first spot (+-4 deg, +-3 cm) whose hit face agrees with that normal (dot >= 0.9) is used
            sd_ = int(rng.randint(1 << 30))
            nm_ = np.array([math.sin(az) * math.sin(g.PITCH), -math.cos(az) * math.sin(g.PITCH), math.cos(g.PITCH)])
            for (daz, dr) in ((0, 0), (0.035, 0.02), (-0.035, -0.02), (0.07, 0.03), (-0.07, 0.0), (0.0, 0.04)):
                a2, r2 = az + daz, g.COLLAR_R + 0.15 + dr
                nm_ = np.array([math.sin(a2) * math.sin(g.PITCH), -math.cos(a2) * math.sin(g.PITCH), math.cos(g.PITCH)])
                hit = probe.cast((math.sin(a2) * r2, -math.cos(a2) * r2, zc + 1.0), (0, 0, -1), 3.0)
                if (hit is not None and hit["surface"] == "M_roof_shingle" and "_roof_underlap" not in hit["object"]
                        and float(np.dot(hit["normal"], nm_)) >= 0.9):
                    da.add("soot", hit["pos"], tuple(nm_), (0.5, 0.4), "M_roof_shingle", 0.6, sd_)
                    break
            continue
        hit = probe.cast((math.sin(az) * r, -math.cos(az) * r, zc + 1.0), (0, 0, -1), 3.0)
        da.add_hit("soot", hit, (0.5, 0.4), probability=0.6, seed=int(rng.randint(1 << 30)),
                   surfaces={"M_roof_shingle"})
    # ---- door: soot over the head, streaks below the lintel ends, grime at hand height, rust under ironwork
    if layout >= 4:
        # kit 1.6.0 (sign-off audit r10 f / director r10 nice-to-have): the door-head soot lies on the LINTEL FRONT,
        # clipped to the lintel face so no footprint row falls into the opening (its lower edge >= 2 cm above the
        # head), centred on the door, normal -Y
        sd_ = int(rng.randint(1 << 30))
        zs_ = np.arange(g.HEAD_Z - 0.02, g.HEAD_Z + 0.40, 0.005)
        face_ = []
        for z_ in zs_:
            hs_ = [probe.cast((x_, g.FRONT_Y - 0.15, z_), (0, 1, 0), 0.4) for x_ in (-0.45, 0.0, 0.45)]
            if all(h_ is not None and h_["surface"] in ("M_timber", "M_timber_weathered") and h_["normal"][1] < -0.8
                   for h_ in hs_):
                face_.append((z_, float(np.mean([h_["pos"][1] for h_ in hs_]))))
        if face_:
            fz = np.array([f_[0] for f_ in face_])
            fy = np.array([f_[1] for f_ in face_])
            # the longest contiguous run of lintel-front samples above the head, its front within 1.5 cm
            ok_ = (fz >= g.HEAD_Z + 0.015) & (np.abs(fy - np.median(fy)) < 0.015)
            runs_, cur_ = [], []
            for i_ in range(len(fz)):
                if ok_[i_] and (not cur_ or fz[i_] - fz[cur_[-1]] < 0.0075):
                    cur_.append(i_)
                else:
                    if cur_:
                        runs_.append(cur_)
                    cur_ = [i_] if ok_[i_] else []
            if cur_:
                runs_.append(cur_)
            if runs_:
                rn_ = max(runs_, key=len)
                z0_, z1_ = fz[rn_[0]] + 0.01, fz[rn_[-1]] - 0.01
                h_s = min(0.20, (z1_ - z0_) / 1.0)
                if h_s >= 0.08:
                    zc_ = z0_ + h_s / 2
                    hit = probe.cast((0.0, g.FRONT_Y - 0.15, zc_), (0, 1, 0), 0.4)
                    if hit is not None:
                        da.add("soot", hit["pos"], (0.0, -1.0, 0.0), (0.9, h_s), hit["surface"], 0.7, sd_)
                        g.DOOR_SOOT = (z0_, z1_, h_s)
    else:
        D.above_opening(da, probe, (0.0, g.FRONT_Y), (0, -1, 0), 1.1, g.HEAD_Z, "soot", (1.0, 0.25),
                        surfaces={"M_timber", "M_timber_weathered"}, rng=rng, reach=0.2)     # from under the eave
    if layout >= 2:
        # director r8 #3: the two streaks below the lintel ends lie on the FRONT faces of the outer frame posts
        # (asked: x = +-0.92 +-2 cm; the post fronts span |x| 0.91-1.13, so the 12 cm streak is centred at +-0.97 to
        # lie wholly on them), top at z 2.20, 0.12 x 0.80, normal -Y, up +Z -- mirrored
        for x_ in (-0.97, 0.97):
            hit = probe.cast((x_, g.FRONT_Y - 0.4, 2.20 - 0.40), (0, 1, 0), 0.8)
            if hit is not None and hit["surface"] in ("M_timber", "M_timber_weathered") and hit["normal"][1] < -0.7:
                da.add("water_streak", hit["pos"], (0.0, -1.0, 0.0), (0.12, 0.80), hit["surface"],
                       seed=int(rng.randint(1 << 30)))
    else:
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
    polys = getattr(g, "PATCH_POLYS", None) if layout >= 3 else None
    for (bay, kind, cf, cz, hs, hz, sd) in g.DAUB_PATCHES:
        a0, a1 = g.POST_AZ[bay], g.POST_AZ[bay + 1]
        s_c = (a0 + cf * (a1 - a0)) * g.R_WALL
        nk = 4 if kind == "hole" else 2
        if polys and polys.get(bay):
            # kit 1.5.0 (director r9 #1): the corner cracks radiate from the sharpest corners of the ACTUAL ragged
            # outline (fracture_patch_r10), 6 cm out along the corner bisector, aligned with it
            P = polys[bay][0][1]
            ok_ = P[:, 1] > cz - hz - 0.25
            u_ = np.roll(P, 1, 0) - P
            v_ = np.roll(P, -1, 0) - P
            u_ /= np.maximum(np.linalg.norm(u_, axis=1, keepdims=True), 1e-9)
            v_ /= np.maximum(np.linalg.norm(v_, axis=1, keepdims=True), 1e-9)
            turn = (u_ * v_).sum(1)                         # cos of the corner angle: high = sharp corner
            convex = (v_[:, 0] * u_[:, 1] - v_[:, 1] * u_[:, 0]) > 0
            cand = [i for i in np.argsort(-turn) if ok_[i] and convex[i]]
            chosen = []
            for i in cand:
                if len(chosen) >= nk:
                    break
                if all(np.hypot(*(P[i] - P[j])) > 0.25 for j in chosen):
                    chosen.append(i)
            for i in chosen:
                bis = -(u_[i] + v_[i])
                bis /= max(float(np.linalg.norm(bis)), 1e-9)
                # kit 1.6.0 (layout 4): the crack STARTS 3 cm out from the corner and runs out along the bisector, so
                # its whole footprint lies on the intact coat (not half over the hole)
                q = P[i] + bis * (0.06 if layout < 4 else 0.03 + 0.5 * 0.26)
                p, u = _wall_point(g, q[0], q[1], 0.15)
                hit = probe.cast(p, -u, 0.4)
                a = q[0] / g.R_WALL
                t3 = np.array([math.cos(a), math.sin(a), 0.0])
                up = t3 * bis[0] + np.array([0, 0, 1.0]) * bis[1]
                sd_ = int(rng.randint(1 << 30))
                if hit is not None and hit["surface"] == "M_daub":
                    da.add("crack", hit["pos"], hit["normal"], (0.14, 0.26), "M_daub", 0.6, sd_, up=up)
            continue
        for (ds, dz) in ((-hs, hz), (hs, hz), (-hs, -hz), (hs, -hz))[:nk]:
            p, u = _wall_point(g, s_c + ds * 1.08, cz + dz * 1.12, 0.15)
            da.add_hit("crack", probe.cast(p, -u, 0.4), (0.18, 0.3), seed=int(rng.randint(1 << 30)),
                       surfaces={"M_daub"})
    for k in range(1, len(g.POST_AZ) - 1, 3):
        off_, dz_ = 0.16, 0.0
        if layout >= 4:      # kit 1.6.0 (audit r10 b): the footprint ends >= 5 cm under the plate; jitter downward only
            off_, dz_ = 0.30, -0.05 - 0.20 + 0.2 - abs(rj.uniform(-0.08, 0.08))
        elif layout >= 3:    # kit 1.5.0 (director r9 nice-to-have): clear of the post flank, z jittered +-8 cm
            off_, dz_ = 0.30, rj.uniform(-0.08, 0.08)
        p, u = _wall_point(g, g.POST_AZ[k] * g.R_WALL + off_ * (1 if k % 2 else -1), g.PLATE_BOT - 0.2 + dz_, 0.15)
        da.add_hit("crack", probe.cast(p, -u, 0.4), (0.2, 0.4), seed=int(rng.randint(1 << 30)), surfaces={"M_daub"})
    # ---- plaster / repair patches over the intact coat
    a_lo, a_hi = door + 0.15, 2 * math.pi - door - 0.15
    halves = [(a_lo, a_hi)] if layout < 2 else [(a_lo, math.pi), (math.pi, a_hi)]     # layout 2: +X / -X balanced
    accept = None
    if layout >= 2:          # layout 2: only spots whose whole footprint lies on intact coat (8 of 9 rays on M_daub)
        from ..anchor_validate import footprint_ok

        def accept(hit, wh):
            return footprint_ok(probe, hit["pos"], hit["normal"], (0, 0, 1), wh, "M_daub", need_mat=8,
                                exclude_objects=("_daub_interior",))
    if layout >= 4:
        # kit 1.6.0 (sign-off audit r10 a): a plaster / repair patch only where its WHOLE rectangle (corners and edge
        # midpoints) lies >= 5 cm inside intact coat by the daub field (clear of the door-bay break and every patch
        # polygon) and its footprint passes the strict gate (>= 8 of 9 within 4 cm, mean normal >= 0.97, flat normal)
        from ..anchor_validate import strict_footprint
        from .frame import bay_s
        L_ = 2 * math.pi * g.R_WALL
        spans_b = [(b_,) + tuple(bay_s(g, b_)) for b_ in range(len(g.POST_AZ) - 1)]

        def field_at(s_, z_):
            s_ = s_ % L_
            for (b_, s0_, s1_) in spans_b:
                for sh_ in (0.0, L_, -L_):
                    if s0_ + 0.02 <= s_ + sh_ <= s1_ - 0.02:
                        return float(g.DAUB_BAYS[b_](np.array([s_ + sh_]), np.array([z_]))[0])
            return -1.0

        def accept(hit, wh):
            p_ = hit["pos"]
            nr_ = np.array([p_[0], p_[1], 0.0])
            nr_ /= max(float(np.linalg.norm(nr_)), 1e-9)
            s_c = math.atan2(p_[0], -p_[1]) * g.R_WALL
            for a_ in (-0.5, 0.0, 0.5):
                for b_ in (-0.5, 0.0, 0.5):
                    if field_at(s_c + a_ * wh[0], p_[2] + b_ * wh[1]) < 0.05:
                        return False
            ok_, mean_, k_ = strict_footprint(probe, p_ + nr_ * 0.004, nr_, (0, 0, 1), wh, "M_daub")
            return ok_ >= 8 and mean_ is not None and float(np.dot(mean_, nr_)) >= 0.975
    for (n_, typ, zr, sz, sep) in ((8, "plaster_patch", (0.7, g.PLATE_BOT - 0.35), ((0.35, 0.7), (0.3, 0.6)), 0.55),
                                   (5, "repair_patch", (0.5, g.PLATE_BOT - 0.3), ((0.25, 0.5), (0.25, 0.45)), 0.5)):
        for hi_, ar in enumerate(halves):
            k_ = n_ if len(halves) == 1 else (n_ + 1 - hi_) // 2
            avoid = [it["pos"] for it in da.items]
            D.wall_scatter(da, probe, (0, 0), R_out, k_, zr, typ, sz, surfaces={"M_daub"}, rng=rng, az_range=ar,
                           avoid=avoid, min_sep=sep, **({"accept": accept} if accept else {}))
    log(f"decal anchors placed: {len(da) - n0}  {da.counts()}")
    return len(da) - n0
