"""components.doors -- door assemblies.

build_door(g)  projecting flat-fronted framed door of a round wattle building: pad stones, cheek sole rails, door
               posts, jambs, lintel, infill boards, rope side panels (built by components.daub), threshold slabs,
               worn timber sill, ledged and braced plank leaf open inward with strap hinges / pintles / nails, ring
               pull and latch.
build_step(g)  the door step built into the entrance (producer note 10 keeps it)
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import az_pt, frame_R, n2, nrm, prism, rbox, roty, rotz, smoothstep, tube, xf
from ..stones import add_shell, map_uvw, outline_radius, pad_stone, shell_stone, spall_stone
from .cone import rafter_underside_z_at_r
from .frame import cull_below_ground, earth_base, stone_top
from .timber import hewn_member, make_clench, make_nail_head, peg, timber_box


def plan_path(g):
    """the built-in door step only (producer note 10: no path flags / stepping stones)."""
    rng = np.random.RandomState(1414)
    g.FLAGS.append(dict(kind="step", c=(g.STEP_C[0], g.STEP_C[1]), rot=0.05, hu=0.62, hv=0.34, ext=0.7,
                      R=outline_radius(rng, "flag"), top=0.095, th=0.16, seed=77))


def build_step(g, coll):
    """the door step built into the entrance (kept per producer note 10): a flat slightly dished slab
    (1-1.5 cm arris, sloping sides, 1-2 edge chips) bedded to the skirt depth."""
    acc = g.acc("step_stone", 30)
    for fl in g.FLAGS:
        rng = np.random.RandomState(fl["seed"])
        if fl["kind"] == "step":
            # kit 1.6.0 (wall_finish gate_fine, audit r10 (3)): the 9 mm trodden dish is below the 1 cm entrance
            # threshold -> gated by g.detail.min_at (dropped); no draw changes
            dish_ = 0.009
            if (getattr(g, "wall_finish", None) or {}).get("gate_fine") and \
                    dish_ < g.detail.min_at((fl["c"][0], fl["c"][1], 0.1)) - 1e-9:
                dish_ = 0.0
            V, F = shell_stone(fl["hu"], fl["hv"], rng, "flag", fl["th"], rr=(0.006, 0.018), rr_var=0.8, dome=0.0,
                               tilt=0.01, n_frac=0, frac_depth=(0.008, 0.015), frac_k=(0.003, 0.005), n_th=128,
                               noise=0.012, freq=4.5, side_bulge=0.0, side_slope=0.12, thick_var=0.12,
                               dish=dish_, chips=3, chip_w=(0.04, 0.08), chip_d=(0.012, 0.022), Rf=fl["R"],
                               spalls=3, face_fr=tuple(np.linspace(0.0, 0.95, 15)),
                               fine_scale=0.0 if g.detail.active else 1.0, spall_scale=0.0 if g.detail.active else 1.0)
            wear = 0.8
        V[:, 2] += fl["top"] - V[0, 2]
        P, _ = map_uvw(V, "plan")
        acc.add(xf(P, rotz(fl["rot"]), (fl["c"][0], fl["c"][1], 0.0)), F, "M_stone", wear=wear)
    acc.build(coll)


def build_door(g, coll, seed=1212):
    fr = g.acc("door_frame", 28)      # adze ridges / checks read crisp; corner arcs are 18 deg
    leaf = g.acc("door_leaf", 40)
    iron = g.acc("door_ironwork", 50)
    def cull_thr(V):
        # under the sill (the slabs run in beneath it): never visible (producer note 6)
        under_sill = (np.abs(V[:, 0]) < 0.88) & (V[:, 1] > g.FRONT_Y + 0.11 - 0.13 + 0.025) & (V[:, 2] < 0.10)
        return cull_below_ground(g, V) | under_sill
    thr = g.acc("threshold", 30, cull=cull_thr)
    rng = np.random.RandomState(seed)
    # producer note 11: the whole door assembly lies in the entrance zone (relief >= 1 cm stays): hero-face adze
    # strokes 1.0-1.3 cm, no strokes on non-hero faces, no drying / end checks (decals), no sub-cm stone skin
    rule = g.detail.active
    hk = dict(checks=not rule, hero_adze=(0.010, 0.013) if rule else None, adze_nonhero=not rule)
    k_fine = 0.0 if rule else 1.0
    yc = g.FRONT_Y + 0.11                       # frame centre plane
    POST_BASE = g.PAD_TOP
    RV = np.array([[0.0, 1, 0], [0, 0, 1], [1, 0, 0]])        # local X -> world Z (vertical member)
    for side in (-1, 1):
        x = side * 1.02
        # pad stone under each door post (director r4 #2a): low and wide (0.46 x 0.36 plan, ~0.18 visible),
        # irregular 6-9-corner plan, battered planar sides, 2-3 planar split faces, flat bed tilted 1-3 deg
        prs = np.random.RandomState(5150 + side)
        pc = np.array([side * 1.04, round(g.FRONT_Y + 0.11, 9)])
        g_pad = float(earth_base(pc[:1], pc[1:])[0])
        # stands on the flat Z = 0 datum (producer note 10): nearly upright sides, no flared foot
        V, F = pad_stone(prs, plan=(0.23, 0.18), vis_h=POST_BASE - g_pad, bury=0.06, batter=(5, 13),
                         min_relief=g.detail.min_at((pc[0], pc[1], 0.15)))
        V[:, 2] += POST_BASE
        thr.add(xf(V, rotz(side * 0.25 + prs.uniform(-0.1, 0.1)), (pc[0], pc[1], 0.0)), F, "M_stone", wear=0.45)
        # cheek-panel sole rail: door post -> wall post, on the pad and the first plinth stone
        wp0 = az_pt(g.WALL_POST_AZ_DOOR * side, g.R_WALL, 0)
        q0 = np.array([side * 1.02, g.FRONT_Y + 0.17, 0.0])
        Lr = float(np.linalg.norm(wp0[:2] - q0[:2]))
        Rr = frame_R(wp0 - q0, (0, 0, 1))
        z_top_r = 0.405
        z_bot_r = min(max(float(stone_top(g, [wp0[0]], [wp0[1]])[0]) - 0.01, g.PAD_TOP - 0.01), 0.30)
        hw_r = 0.06
        hewn_member(fr, (q0 + wp0) / 2 + np.array([0, 0, (z_top_r + z_bot_r) / 2]),
                    (Lr / 2, hw_r, (z_top_r - z_bot_r) / 2), Rr, rng, ch=0.015, ns=5, nc=4, ds=0.02,
                    end_checks=1, hidden=(2,), **hk)
        # director r4 #3c: packing stones under the cheek sole rail (no black void between the pad and the
        # first plinth stone): two split spalls bedded in the earth, their tops wedged under the rail
        for kf, tf in enumerate((0.28, 0.6)):
            frs = np.random.RandomState(5170 + 10 * side + kf)
            hf = np.array([frs.uniform(0.10, 0.13), frs.uniform(0.08, 0.10), 0.5 * (z_bot_r + 0.03)])
            # kit 1.6.0 (wall_finish gate_fine, audit r10 (2)): 1.2 mm lumps / 0.6 mm pits gated by g.detail.min_at
            mr_f = g.detail.min_at((q0[0], q0[1], 0.1)) if (getattr(g, "wall_finish", None) or {}).get("gate_fine") \
                else 0.0
            Vf, Ff = spall_stone(frs, hf, n_planes=(6, 8), k_round=0.003, lump=0.0012 * (0.0012 >= mr_f),
                                 pit=0.0006 * (0.0006 >= mr_f))
            pf = q0 + (wp0 - q0) * tf + np.array([0, 0, 0]) - np.array([side * 0.0, 0.0, 0.0])
            Vf = xf(Vf, rotz(math.atan2(wp0[1] - q0[1], wp0[0] - q0[0]) + frs.uniform(-0.3, 0.3)), (0, 0, 0))
            Vf[:, 2] += (z_bot_r - 0.004) - Vf[:, 2].max()
            Vf[:, :2] += pf[:2] + nrm(np.array([q0[0], q0[1]])) * frs.uniform(-0.02, 0.03)
            thr.add(Vf, Ff, "M_stone", wear=0.5)
        # door posts (heavier, squared): front & door-side faces are hero faces, back face hidden
        wane_c = (3, 0) if side > 0 else (2, 1)
        inner_f, outer_f = (1, 3) if side > 0 else (3, 1)
        hewn_member(fr, (x, yc, (POST_BASE + g.HEAD_Z) / 2), ((g.HEAD_Z - POST_BASE) / 2, 0.12, 0.11),
                    rotz(side * 0.006) @ RV, rng, ch=0.02, wane=wane_c, n_checks=3,
                    check_faces=(2, 2, outer_f, inner_f), ns=11, nc=6, hero=(2, outer_f), hidden=(0, inner_f),
                    caps=(False, False), ds=0.007, **hk)
        # inner jambs on the sill
        xj = side * 0.60
        hewn_member(fr, (xj, yc, (g.SILL_TOP + g.HEAD_Z) / 2), ((g.HEAD_Z - g.SILL_TOP) / 2, 0.10, 0.11),
                    rotz(side * 0.004) @ roty(side * 0.003) @ RV, rng, ch=0.018, wane=(2 if side > 0 else 3,),
                    n_checks=2, check_faces=(2, inner_f), ns=10, nc=6, hero=(2, inner_f), hidden=(0, outer_f),
                    caps=(False, False), ds=0.007, **hk)
        # sole rail under the side panel, resting on the sill end
        hewn_member(fr, (side * 0.805, yc, (g.SILL_TOP + 0.405) / 2), (0.115, 0.075, (0.405 - g.SILL_TOP) / 2),
                    np.eye(3), rng, ch=0.015, ns=5, nc=4, ds=0.02, hidden=(3,), **hk)
        # return tie beam from the door post to the wall post (top under the roof, inner face hidden)
        wp = az_pt(g.WALL_POST_AZ_DOOR * side, g.R_WALL, 0)
        p0 = np.array([x, yc + 0.05, g.HEAD_Z + 0.11])
        p1 = np.array([wp[0], wp[1], g.HEAD_Z + 0.11])
        L = float(np.linalg.norm(p1 - p0))
        R = frame_R(p1 - p0, (0, 0, 1))
        mid = (p0 + p1) / 2
        inner_side = 3 if float(np.dot(R[:, 1], -mid)) > 0 else 1
        hewn_member(fr, mid, (L / 2 + 0.1, 0.08, 0.10), R, rng, ch=0.02, wane=(0,), end_checks=1,
                    sag=0.004, ns=3, nc=3, ds=0.04, adze=False, hidden=(0, inner_side), **hk)
        for (px, pz, fy) in ((x - side * 0.03, g.HEAD_Z + 0.06, g.FRONT_Y - 0.009), (x + side * 0.045, g.HEAD_Z + 0.15, g.FRONT_Y - 0.009),
                             (xj, g.HEAD_Z + 0.07, g.FRONT_Y - 0.009), (xj - side * 0.03, g.SILL_TOP + 0.05, g.FRONT_Y + 0.004)):
            peg(g, np.array([px, fy, pz]), (0, -1, 0), rng)
        pe = p1 - R[:, 0] * 0.12
        peg(g, pe + R[:, 1] * (0.08 if inner_side == 1 else -0.08) * 1.0, R[:, 1] * (1 if inner_side == 1 else -1), rng)
    # lintel on the door posts (front face proud), slight sag; top + back hidden
    hewn_member(fr, (0.0, yc - 0.008, g.HEAD_Z + 0.11), (1.15, 0.115, 0.11), np.eye(3), rng, ch=0.022,
                wane=(1,), n_checks=2, check_faces=(1,), end_checks=2, sag=0.008, ns=9, nc=6, ds=0.016,
                hero=(1, 2), hidden=(0, 3), **hk)
    # infill above the lintel up to the rafters: short vertical boards
    xx = -1.05
    k = 0
    while xx < 1.05:
        bw = min(rng.uniform(0.16, 0.26), 1.05 - xx)
        if bw < 0.05:
            break
        cx = xx + bw / 2
        r_ = math.hypot(cx, g.FRONT_Y + 0.1)
        top = float(rafter_underside_z_at_r(g, r_)) + 0.02
        h0 = g.HEAD_Z + 0.215
        if top - h0 > 0.04:
            timber_box(fr, (cx, g.FRONT_Y + 0.13, (h0 + top) / 2), (bw / 2 - 0.006, 0.016, (top - h0) / 2),
                       rotz(rng.uniform(-0.01, 0.01)), ch=0.006, segs=(1, 1, 2), seed=40 + k)
        xx += bw
        k += 1
    # threshold (director r3 #3c): three flat slabs under the sill front, front edges wandering, depth
    # 0.22-0.35 m, 1-2 cm steps between the pieces, chipped notches of 3-6 cm
    trs = np.random.RandomState(5300)
    xs_t = [-0.64, 0.0, 0.62]
    tops_t = [0.081, 0.093, 0.074]
    for kt in range(3):
        hu_t = trs.uniform(0.36, 0.39)
        hv_t = trs.uniform(0.13, 0.17)
        # director r4 #2c: tops undulating 0.5-1.5 cm at 15-25 cm, 2-3 shallow spalls, arris 0.5-2.5 cm
        V, F = shell_stone(hu_t, hv_t, trs, "flag", 0.11, rr=(0.006, 0.016), rr_var=0.8, dome=0.004, tilt=0.008,
                           n_frac=0, frac_depth=(0.008, 0.016), frac_k=(0.003, 0.005), n_th=100, noise=0.013,
                           freq=5.0, side_bulge=0.0, side_slope=0.25, sm_scale=0.5, chips=trs.randint(2, 4),
                           chip_w=(0.03, 0.06), chip_d=(0.01, 0.02), spalls=trs.randint(2, 4),
                           face_fr=tuple(np.linspace(0.0, 0.94, 11)), fine_scale=k_fine, spall_scale=k_fine)
        V[:, 2] += tops_t[kt] - V[0, 2]
        yc_t = g.FRONT_Y - 0.03 + trs.uniform(-0.04, 0.03)
        add_shell(thr, V, F, "plan", rotz(trs.uniform(-0.06, 0.06)), (xs_t[kt] + trs.uniform(-0.02, 0.02), yc_t, 0.0),
                  "M_stone")

    # worn timber sill: hewn, with a 2.2 cm trodden dip over the middle 0.6 m, a worn outer arris
    # and end checks; underside (on the stone) and inner face hidden
    sh = (g.SILL_TOP - 0.09) / 2

    def sill_wear(V):
        x = V[:, 0]
        dip = np.exp(-np.abs(x / 0.36) ** 3.2)
        top = smoothstep(-0.2 * sh, sh, V[:, 2])
        V[:, 2] -= 0.022 * dip * top * (0.75 + 0.25 * smoothstep(0.13, -0.13, V[:, 1]))
        front = smoothstep(-0.13 + 0.06, -0.13, V[:, 1]) * smoothstep(sh - 0.05, sh, V[:, 2] + 0.022 * dip)
        V[:, 2] -= 0.012 * (0.4 + 0.6 * dip) * front
        V[:, 1] += 0.008 * (0.4 + 0.6 * dip) * front
        # director r4 #4: irregular wear instead of periodic adze beads -- 1-3 soft lumps / hollows per
        # metre on the front face, varied in size, plus slow undulation
        ff = smoothstep(-0.13 + 0.03, -0.13, V[:, 1])
        for (xc_, wl_, am_) in sill_lumps:
            V[:, 1] -= k_fine * am_ * np.exp(-((x - xc_) / wl_) ** 2) * ff
        V[:, 1] -= k_fine * 0.002 * n2(x * 2.3, V[:, 2] * 3.0, 5333) * ff
        return V
    srs = np.random.RandomState(5331)
    sill_lumps = [(xc_, srs.uniform(0.05, 0.16), srs.choice([-1, 1]) * srs.uniform(0.002, 0.005))
                  for xc_ in np.sort(srs.uniform(-0.85, 0.85, srs.randint(3, 5)))]
    hewn_member(thr, (0.0, yc, (g.SILL_TOP + 0.09) / 2), (0.92, 0.13, sh), np.eye(3), rng, ch=0.015,
                end_checks=2, n_checks=1, check_faces=(0,), ns=8, nc=5, hero=(0, 1), hidden=(2, 3),
                deform=sill_wear, mat="M_timber", wear=0.9, adze=False, **hk)

    # ---------------- door leaf: 6 boards (16-30 cm) + 2 ledges + brace, open 75 deg inward
    LY = 0.024
    pivot = np.array([0.555, -g.R_WALL - 0.0065 + 0.0015, 0.0])
    Rl = rotz(math.radians(-75.0))
    parts = []
    for _ in range(200):
        widths = rng.uniform(0.155, 0.30, 6)
        widths = widths / widths.sum() * (1.06 - 5 * 0.009)
        if widths.min() >= 0.155 and widths.max() <= 0.30:
            break
    x = 0.02
    h0, h1 = g.SILL_TOP + 0.012, g.HEAD_Z + 0.035
    cup_b = set(rng.choice(6, 2, replace=False).tolist())
    edge_fns = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(6)]
    for b in range(6):
        bw = widths[b]
        cx = -(x + bw / 2)
        V, F = rbox((bw / 2, 0.0175, (h1 - h0) / 2), 0.006, (3, 1, 10))
        zl = V[:, 2] / ((h1 - h0) / 2)
        # gaps 0.5-1.5 cm varying along the length: each edge wanders +-3 mm
        ea, eb = edge_fns[b]
        right = V[:, 0] > 0
        wl = 0.003 * n2(zl * 1.6, np.full(len(V), ea), 1500 + b)
        wr = 0.003 * n2(zl * 1.6, np.full(len(V), eb), 1600 + b)
        V[:, 0] += np.where(right, wr, wl) * np.clip(np.abs(V[:, 0]) / (bw / 2), 0, 1)
        # uneven board ends +-1 cm
        top_off = rng.uniform(-0.01, 0.01) + V[:, 0] * rng.uniform(-0.03, 0.03)
        bot_off = rng.uniform(-0.008, 0.004)
        V[:, 2] += np.where(zl > 0, top_off * (zl > 0.9), bot_off * (zl < -0.9))
        if b in cup_b:                      # cupped board: edges lift 3-5 mm on the outer face
            V[:, 1] -= rng.uniform(0.003, 0.005) * (2 * V[:, 0] / bw) ** 2
        V[:, 1] += 0.002 * np.sin(V[:, 2] * 1.7 + b * 2) * (V[:, 0] / bw)
        V = V + [cx, LY, (h0 + h1) / 2]
        parts.append((V, F, "M_timber"))
        x += bw + 0.009
    W = x - 0.009 - 0.02
    clench = []
    for zl_ in (h0 + 0.32, h1 - 0.34):
        V, F = rbox((W / 2 - 0.04, 0.016, 0.075), 0.01, (4, 1, 1))
        parts.append((V + [-0.02 - W / 2, LY + 0.0175 + 0.016, zl_], F, "M_timber"))
        for xn in np.linspace(-0.1, -W + 0.06, 6):
            clench.append(np.array([xn, LY + 0.0175 + 0.032 + 0.003, zl_ + 0.03]))
    za_, zb_ = h0 + 0.32 + 0.06, h1 - 0.34 - 0.06
    p0 = np.array([-0.1, 0.0, za_])
    p1 = np.array([-W + 0.06, 0.0, zb_])
    L = float(np.linalg.norm(p1 - p0))
    Rb = frame_R(p1 - p0, (0, 1, 0))
    V, F = rbox((L / 2 - 0.02, 0.065, 0.016), 0.01, (4, 1, 1))
    V = xf(V, Rb, (p0 + p1) / 2 + [0, LY + 0.0175 + 0.016, 0])
    parts.append((V, F, "M_timber"))
    V, F = rbox((0.24, 0.016, 0.022), 0.006, (3, 1, 1))
    parts.append((V + [-W + 0.10, LY + 0.0175 + 0.05, 1.12], F, "M_timber"))
    V, F = rbox((0.03, 0.014, 0.04), 0.005)
    parts.append((V + [-W + 0.28, LY + 0.0175 + 0.014, 1.12], F, "M_timber"))
    for V, F, m in parts:
        leaf.add(xf(V, Rl, pivot), F, m)
    for c_ in clench:
        g.pools.place(g.pools.mesh("clench_nail", rng.randint(3), make_clench), "door_clench_nail", Rl,
                       pivot + Rl @ c_)
    face_y = LY - 0.0175                 # outer face

    def make_strap(acc_, k):
        Ls = 0.80
        outline = [(0.0, -0.026), (-Ls + 0.10, -0.023), (-Ls + 0.055, -0.038), (-Ls, 0.0),
                   (-Ls + 0.055, 0.038), (-Ls + 0.10, 0.023), (0.0, 0.026)]
        V, faces = prism(outline[::-1], 0.007)
        V = np.stack([V[:, 0], -V[:, 2], V[:, 1]], -1)
        acc_.add(V, faces, "M_iron", smooth=False)

    def make_knuckle(acc_, k):
        Pk, Fk, uvk, wk = tube(np.linspace([0, 0, -0.03], [0, 0, 0.03], 3), 0.014, 12, up=(1, 0, 0))
        acc_.add(Pk, Fk, "M_iron", uvk, wk)

    def make_pintle(acc_, k):
        Pp, Fp, uvp, wpp = tube(np.linspace([0, 0, -0.05], [0, 0, 0.045], 3), 0.0075, 8, up=(1, 0, 0))
        acc_.add(Pp, Fp, "M_iron", uvp, wpp)
        V, F = rbox((0.009, 0.035, 0.009), 0.002)
        acc_.add(V + [0.0, -0.03, -0.05], F, "M_iron")

    for zh in (h0 + 0.30, h1 - 0.30):
        g.pools.place(g.pools.mesh("hinge_strap", 0, make_strap), "door_hinge_strap", Rl, pivot + Rl @ np.array([0, face_y, zh]))
        g.pools.place(g.pools.mesh("hinge_knuckle", 0, make_knuckle), "door_hinge_knuckle", Rl, pivot + Rl @ np.array([0, 0, zh]))
        g.pools.place(g.pools.mesh("hinge_pintle", 0, make_pintle), "door_hinge_pintle", None, pivot + np.array([0, 0, zh]))
        for xn in (-0.07, -0.22, -0.38, -0.54, -0.68):
            Rn = Rl @ np.array([[1.0, 0, 0], [0, -1, 0], [0, 0, -1]])      # head points out of the face (-y)
            g.pools.place(g.pools.mesh("nail_head", rng.randint(3), make_nail_head), "door_nail",
                           Rn @ rotz(0), pivot + Rl @ np.array([xn, face_y - 0.007, zh]))
    # ring pull with rose plate near the free edge
    plate = [(0.035 * math.cos(a), 0.035 * math.sin(a)) for a in np.linspace(0, 2 * np.pi, 13)[:-1]]
    V, faces = prism(plate, 0.005)
    xr = -0.02 - W + 0.13
    V = np.stack([V[:, 0] + xr, face_y - V[:, 2], V[:, 1] + 1.08], -1)
    iron.add(xf(V, Rl, pivot), faces, "M_iron", smooth=False)
    ang = np.linspace(0, 2 * np.pi, 25)[:-1]
    ring = np.stack([np.cos(ang) * 0.045 + xr, np.full_like(ang, face_y - 0.013), np.sin(ang) * 0.045 + 1.08 - 0.04], -1)
    ring = np.concatenate([ring, ring[:1]])
    Pr, Fr, uvr, wr = tube(ring, 0.0065, 8, up=(0, -1, 0), caps=False)
    iron.add(xf(Pr, Rl, pivot), Fr, "M_iron", uvr, wr)
    # keeper for the latch on the -X jamb (inner face)
    timber_box(fr, (-0.56, -g.R_WALL + 0.03, 1.12), (0.03, 0.03, 0.05), ch=0.008, seed=77)
    fr.build(coll)
    leaf.build(coll)
    iron.build(coll)
    thr.build(coll)


def door_step(g):
    """KIT COMPONENT: the flat dished step stone built into the entrance (<PREFIX>_step_stone), 0.58 m in front
    of the door frame."""
    if not g.FLAGS:
        plan_path(g)
    build_step(g, g.coll)


def framed_door(g, seed=1212):
    """KIT COMPONENT: projecting flat-fronted door frame of a round wattle wall, centred on -Y: clear opening
    g.DOOR_W x 2.08 m on a worn sill at g.SILL_TOP, door posts on pad stones, jambs, lintel, infill boards up to the
    rafters, cheek sole rails to the wall posts at +-g.WALL_POST_AZ_DOOR, threshold slabs, a ledged and braced
    plank leaf open 75 deg inward with pooled strap hinges / pintles / nails, ring pull, latch keeper.  Objects
    <PREFIX>_door_frame / _door_leaf / _door_ironwork / _threshold (+ pooled ironwork, pegs)."""
    build_door(g, g.coll, seed=seed)
