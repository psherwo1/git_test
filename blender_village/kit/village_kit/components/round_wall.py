"""components.round_wall -- the post ring and the wall plate of a round building.

build_posts(g, coll)       round-hewn wall posts on the plinth, culled where buried in the daub coat
post_profiles(g, ob)       as-built post fronts (the daub coat fits to them so posts stand 5-8 cm proud)
build_wall_plate(g, coll)  7 curved scarf-jointed, pegged plate segments on the post heads
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import az_pt, tube
from .frame import cull_below_ground, stone_top
from .timber import peg, round_post


def post_cull(g, V):
    """producer note 6 / client r6: the post flanks buried in the intact daub coat (the coat meets each
    post ~6 cm proud of the wattle line) and the post backs behind the wattle line are never seen.
    Door-side flanks of the two door-bay wall posts stay whole (seen through the doorway)."""
    hid = cull_below_ground(g, V)
    X, Y, Zv = V[:, 0], V[:, 1], V[:, 2]
    az = np.mod(np.arctan2(X, -Y), 2 * np.pi)
    dr = np.hypot(X, Y) - g.R_WALL
    ip = np.argmin(np.abs(np.angle(np.exp(1j * (az[:, None] - g.POST_AZ[None, :])))), axis=1)
    dt = np.angle(np.exp(1j * (az - g.POST_AZ[ip])))
    nb = len(g.POST_AZ) - 1
    bay = np.where(dt > 0, ip, ip - 1)
    door_side = (bay < 0) | (bay >= nb)
    intact = np.zeros(len(V), bool)
    for b in range(nb):
        m = bay == b
        if m.any():
            s_side = (g.POST_AZ[ip[m]] + np.sign(dt[m]) * 0.12 / g.R_WALL) * g.R_WALL
            intact[m] = g.DAUB_BAYS[b](s_side, Zv[m]) > 0.07
    intact &= (Zv > 0.3) & (Zv < g.PLATE_BOT - 0.12)
    thr = np.where(intact, 0.02, -0.015)
    return hid | (~door_side & (Zv > 0.3) & (dr < thr))


def build_posts(g, coll, seed=202):
    acc = g.acc("posts", 15, cull=partial(post_cull, g))   # low angle: adze-flat edges crisp, 48-gon stays smooth
    rng = np.random.RandomState(seed)
    g.POST_RAD.clear()
    for i, az in enumerate(g.POST_AZ):
        # stand on the crowned stone under the post: lowest stone point under the footprint (no float)
        fp = [az_pt(az + da / g.R_WALL, g.R_WALL + dr) for da in (-0.08, 0.0, 0.08) for dr in (-0.07, 0.0, 0.08)]
        zb_ = float(np.min(stone_top(g, [p_[0] for p_ in fp], [p_[1] for p_ in fp])))
        b = az_pt(az, g.R_WALL + g.POST_OUT, zb_ - 0.012)
        tp = az_pt(az, g.R_WALL + g.POST_OUT, g.PLATE_BOT + 0.004)       # head bears on the plate underside
        rad = rng.uniform(0.10, 0.12)
        g.POST_RAD.append(rad)
        round_post(g, acc, b, tp, rad, rng, check=(i % 3 == 1), radial=0.3,
                   min_relief=g.detail.min_at(az_pt(az, g.R_WALL, 1.2)))
    ob = acc.build(coll)
    post_profiles(g, ob)


def post_profiles(g, ob, dz=0.04):
    """front radius and centre (arc length) of every wall post along its height, measured from the built
    mesh (lean, bow, adze flats included): the daub coat is fitted so each post stands 5-8 cm proud."""
    me = ob.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    az = np.mod(np.arctan2(V[:, 0], -V[:, 1]), 2 * np.pi)
    r = np.hypot(V[:, 0], V[:, 1])
    zs = np.arange(0.20, g.PLATE_BOT + 0.05, dz)
    g.POST_PROF.clear()
    for i, a in enumerate(g.POST_AZ):
        d = np.angle(np.exp(1j * (az - a))) * g.R_WALL
        m = (np.abs(d) < 0.2) & (r > g.R_WALL - 0.06)
        dm, rm, zm = d[m], r[m], V[m, 2]
        sc, rf = np.full(len(zs), np.nan), np.full(len(zs), np.nan)
        for k, z in enumerate(zs):
            mk = np.abs(zm - z) < dz * 0.75
            if mk.sum() < 6:
                continue
            j = np.argmax(rm[mk])
            near = mk & (np.abs(dm - dm[mk][j]) < 0.035)
            rf[k] = np.percentile(rm[near], 80)
            top = near & (rm > rf[k] - 0.004)
            sc[k] = np.mean(dm[top]) if top.any() else dm[mk][j]
        ok = ~np.isnan(rf)
        # the post is a smooth leaning / bowed stick: a robust quadratic through the per-height
        # estimates (knot stubs and adze flats are outliers), so the coat fits the true flank
        for _ in range(3):
            cs_ = np.polyfit(zs[ok], sc[ok], 2)
            cr_ = np.polyfit(zs[ok], rf[ok], 2)
            res = np.abs(np.polyval(cs_, zs) - sc) + np.abs(np.polyval(cr_, zs) - rf)
            ok2 = ok & (res < max(0.006, np.nanpercentile(res[ok], 75) * 1.5))
            if ok2.sum() < 8:
                break
            ok = ok2
        sc = np.polyval(cs_, zs) + a * g.R_WALL
        rf = np.polyval(cr_, zs)
        g.POST_PROF.append((zs, sc, rf))


def build_wall_plate(g, coll, seed=303):
    acc = g.acc("wall_plate", 40)
    rng = np.random.RandomState(seed)
    joints = list(g.POST_AZ[::2])                # a scarf joint over every other post (7 on 14 posts)
    nj = len(joints)
    joints.sort()
    hw, hh = 0.09, g.PLATE_H / 2
    ch = 0.022
    prof = np.array([[hw - ch, -hh], [hw, -hh + ch], [hw, hh - ch], [hw - ch, hh],
                     [-hw + ch, hh], [-hw, hh - ch], [-hw, -hh + ch], [-hw + ch, -hh]])
    zc = g.PLATE_BOT + hh
    for k in range(nj):
        a0 = joints[k]
        a1 = joints[(k + 1) % nj] + (2 * math.pi if k == nj - 1 else 0)
        # overlap past the joints (scarf) by ~0.17 m each side
        e0 = a0 - 0.17 / g.R_WALL
        e1 = a1 + 0.17 / g.R_WALL
        n = max(8, int((e1 - e0) * g.R_WALL / 0.12))
        a = np.linspace(e0, e1, n)
        rr = g.R_WALL + g.PLATE_OUT + 0.012 * np.sin(np.pi * (a - e0) / (e1 - e0)) * rng.uniform(-1, 1)
        zz = np.full(n, zc) - 0.012 * np.sin(np.pi * (a - e0) / (e1 - e0)) * rng.uniform(0.3, 1)
        path = np.stack([np.sin(a) * rr, -np.cos(a) * rr, zz], -1)
        pr = np.broadcast_to(prof, (n, 8, 2)).copy()
        # half-lap: the start end keeps only the lower half, the end keeps the upper half (scarf)
        lap0 = (a < a0 + 0.17 / g.R_WALL)
        lap1 = (a > a1 - 0.17 / g.R_WALL)
        pr[lap0, :, 1] = np.where(pr[lap0, :, 1] > 0, pr[lap0, :, 1] * 0.0 - 0.004, pr[lap0, :, 1])
        pr[lap1, :, 1] = np.where(pr[lap1, :, 1] < 0, pr[lap1, :, 1] * 0.0 + 0.004, pr[lap1, :, 1])
        # profile coordinates are (radial-ish N=up-projected?)  -> use frames with up=z: N=z, B=T x z
        prof_xy = np.stack([pr[..., 1], -pr[..., 0]], -1)
        P, F, uv, w = tube(path, 1.0, 8, up=(0, 0, 1), profile=prof_xy)
        acc.add(P, F, "M_timber", uv, w)
        # pegs through the laps, driven in from the outer face (heads proud, seen from under the eave)
        for aj in (a0, a1):
            for d in (-0.07, 0.07):
                az_ = aj + d / g.R_WALL
                u = np.array([math.sin(az_), -math.cos(az_), 0.0])
                p = az_pt(az_, g.R_WALL + g.PLATE_OUT + hw - 0.002, zc + rng.uniform(-0.03, 0.03))
                peg(g, p, u, rng)
    acc.build(coll)


def round_posts(g, seed=202):
    """KIT COMPONENT: g.N_POSTS round-hewn posts on the plinth at g.POST_AZ (2 flanking the door frame), heads
    under the plate; object <PREFIX>_posts.  Needs the plinth (g.PL_TOP) and, for the coat culling, the daub
    fields (round_daub_wall calls it at the right moment)."""
    build_posts(g, g.coll, seed=seed)


def wall_plate(g, seed=303):
    """KIT COMPONENT: curved, scarf-jointed and pegged wall plate ring on the post heads (<PREFIX>_wall_plate)."""
    build_wall_plate(g, g.coll, seed=seed)
