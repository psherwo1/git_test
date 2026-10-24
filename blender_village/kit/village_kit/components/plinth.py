"""components.plinth -- dry-stone plinth ring (art bible section 3): one course of slabs / blocks / boulders
(never two of a kind in a row), ~20 % two-high, overlapping rounded ends, pooled flat-wedge chinking ray-tested into
open joints.  Publishes g.PL_TOP (BVH stone-top sampler) for everything that bears on the stones."""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import az_pt, log

from ..core import frame_wall, rotx, roty, rotz, xf
from ..stones import chink_stone, plinth_kind_stone
from .frame import cull_below_ground, plinth_face_r


def plinth_stone(rng, L, z_bot, z_top, depth, fracture, kind="block", upper=False, min_relief=0.0, scar_keep=None,
                 split=False, scar_keep_ent=None, dense=1.0):
    """one plinth stone (local frame, see plinth_kind_stone()); bottom at z_bot, high point ~z_top.
    kit 1.6.0 (optional): split (planar split-facet scars, no skin lumps), scar_keep_ent, dense (mesh density factor
    -- crisp facet creases need vertices on them)."""
    c = max(0.05, (z_top - z_bot) / 2)
    b = depth / 2
    V, F = plinth_kind_stone(kind, (L / 2, b, c), rng, fracture=fracture,
                             n_front=int(round((72 if not upper else 56) * dense)),
                             n_up=int(round((30 if not upper else 24) * dense)),
                             min_relief=min_relief, scar_keep=scar_keep, split=split, scar_keep_ent=scar_keep_ent)
    V[:, 2] += z_bot - V[:, 2].min()
    return V, F


def build_plinth(g, coll, seed=9191):
    """dry-stone plinth (director r3 #3a): ONE course of rounded / sub-angular field boulders, each a
    superellipsoid body with a crowned top (4-8 cm, high point off-centre), a front bulging 3-6 cm,
    sloping sides and crisp fracture facets on ~35 % of stones only; crown heights alternate so that
    neighbours differ by >= 4 cm (visible 0.18-0.34 m), ~20 % two-high with a smaller upper stone;
    neighbours overlap at their rounded ends so face joints close to <= 3 cm.  Only what is outside
    the wattle line and above ground is modelled.  Flat wedge chinking (pooled) is ray-tested into
    the open V-joints."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    def cull_pl(V):
        return cull_below_ground(g, V) | (np.hypot(V[:, 0], V[:, 1]) < g.R_WALL - 0.035)
    acc = g.acc("plinth_stones", 30, cull=cull_pl)
    rng = np.random.RandomState(seed)
    r_c = g.R_WALL + 0.10
    a_start = math.asin(1.20 / round(g.R_WALL + 0.28, 9))          # runs on under the cheek panels to the door-post pads
    a_end = 2 * math.pi - a_start
    post_az = list(g.POST_AZ)
    a = a_start
    stones = []
    # director r4 #2b: shape mix ~30 % sub-rounded boulders, ~40 % flat slabs, the rest blocky, never two
    # neighbours of the same kind (lengths by kind: slabs long and low, h:L <= 0.45)
    kinds = []
    len_rng = {"slab": (0.62, 0.84), "block": (0.42, 0.62), "boulder": (0.42, 0.58)}
    while a < a_end - 0.02:
        opts = [k_ for k_ in ("slab", "block", "boulder") if not kinds or k_ != kinds[-1]]
        w = np.array([{"slab": 0.46, "block": 0.30, "boulder": 0.24}[k_] for k_ in opts])
        kind = opts[rng.choice(len(opts), p=w / w.sum())]
        L = rng.uniform(*len_rng[kind])
        if a + L / r_c > a_end:
            L = (a_end - a) * r_c
            if L < 0.25:
                stones[-1][1] += L * 0.6
                break
        stones.append([a + (L / 2) / r_c, L])
        kinds.append(kind)
        a += (L - rng.uniform(0.035, 0.06)) / r_c          # rounded ends overlap: tight joints
    n_two = n_fr = 0
    placed = []
    z_prev = None
    ground_face = 0.045
    vis_rng = {"slab": (0.17, 0.22), "block": (0.22, 0.30), "boulder": (0.27, 0.35)}
    n_kind = {"slab": 0, "block": 0, "boulder": 0}
    # kit 1.5.0 (opt-in g.wall_finish["stone_scars"]): the deepest hand-split scars are kept as note-11 spalls
    wf_ = getattr(g, "wall_finish", None) or {}
    sk_ = wf_.get("stone_scars")
    split_ = wf_.get("stone_style") == "split"
    ske_ = wf_.get("stone_scars_ent") if split_ else None

    def flat_feet(Pw, ac_, skirt=0.01):
        """kit 1.6.0 (audit r10): a flat bed at the ground -- below z 0.5 cm no vertex stands more than `skirt`
        proud (radially) of the stone's own face just above the ground (z 0.5-6 cm) at the same arc position."""
        if not split_ or Pw[:, 2].min() > 0.005:
            return Pw
        r_ = np.hypot(Pw[:, 0], Pw[:, 1])
        s_ = np.angle(np.exp(1j * (np.arctan2(Pw[:, 0], -Pw[:, 1]) - ac_))) * r_c
        bw = 0.015
        k_ = np.floor(s_ / bw).astype(int)
        k0 = k_.min()
        k_ -= k0
        ref = (Pw[:, 2] >= 0.005) & (Pw[:, 2] <= 0.06)
        rr = np.full(k_.max() + 1, np.nan)
        for kk in np.unique(k_[ref]):
            rr[kk] = r_[ref & (k_ == kk)].max()
        if np.isnan(rr).all():
            return Pw
        idx = np.arange(len(rr))
        good = ~np.isnan(rr)
        rr = np.interp(idx, idx[good], rr[good])
        low = Pw[:, 2] < 0.005
        lim = rr[k_] + skirt
        sc = np.where(low & (r_ > lim), lim / np.maximum(r_, 1e-9), 1.0)
        Pw = Pw.copy()
        Pw[:, 0] *= sc
        Pw[:, 1] *= sc
        return Pw
    for i, (ac, L) in enumerate(stones):
        kind = kinds[i]
        mr = g.detail.min_at(az_pt(ac, r_c, 0.2))           # producer note 11 (1 cm near the door)
        st_kw = dict(split=split_, scar_keep_ent=ske_, dense=(1.6 if (split_ and mr < 0.015) else 1.0))
        if mr >= 0.015:
            # kit 1.7 r4 (v4_mixed, producer note 15): optional frame attribute PLINTH_DENSE -- mesh-density factor
            # of the plinth stones OUTSIDE the entrance zone (note-11 relief >= 1.5 cm there); absent = unchanged
            st_kw["dense"] *= float(getattr(g, "PLINTH_DENSE", 1.0))
        n_kind[kind] += 1
        near_post = min(abs(np.angle(np.exp(1j * (ac - pa)))) for pa in post_az) * r_c < L / 2 + 0.02
        # visible heights by kind, neighbours >= 4 cm apart
        for _ in range(40):
            zt = ground_face + rng.uniform(*vis_rng[kind])
            if near_post:
                zt = max(zt, ground_face + 0.22)
            if z_prev is None or abs(zt - z_prev) >= 0.04:
                break
        z_prev = zt
        fr_ = rng.rand() < 0.62
        n_fr += fr_
        face = float(plinth_face_r(g, ac)) + rng.uniform(-0.015, 0.02)
        depth = face - (g.R_WALL - 0.10)
        R = frame_wall(ac) @ rotz(rng.uniform(-0.08, 0.08)) @ rotx(rng.uniform(-0.05, 0.03)) @ roty(rng.uniform(-0.05, 0.05))
        two = (not near_post) and kind != "slab" and L > 0.5 and rng.rand() < 0.22
        z_b = -0.06 if kind == "slab" else -0.11
        if not two:
            V, F = plinth_stone(rng, L, z_b, zt, depth, fr_, kind, min_relief=mr, scar_keep=sk_, **st_kw)
            Pw = xf(V, R)
            u = np.array([math.sin(ac), -math.cos(ac), 0.0])
            Pw += u * (face - float((Pw @ u).max()))
            Pw = flat_feet(Pw, ac)
            acc.add(Pw, F, "M_stone", wear=rng.uniform(0.2, 0.5) + 0.3 * fr_)
            placed.append((ac, zt, L))
        else:
            n_two += 1
            lo_top = ground_face + rng.uniform(0.11, 0.15)
            V, F = plinth_stone(rng, L, -0.07, lo_top, depth, fr_, "slab", min_relief=mr, scar_keep=sk_, **st_kw)
            Pw = xf(V, R)
            u = np.array([math.sin(ac), -math.cos(ac), 0.0])
            Pw += u * (face - float((Pw @ u).max()))
            Pw = flat_feet(Pw, ac)
            acc.add(Pw, F, "M_stone", wear=rng.uniform(0.2, 0.5))
            Lu = L * rng.uniform(0.55, 0.72)
            xo = rng.uniform(-0.15, 0.15) * L
            zu = max(zt, lo_top + 0.12)
            Vu, Fu = plinth_stone(rng, Lu, lo_top - 0.03, zu, depth - 0.05, rng.rand() < 0.6, kind, upper=True,
                                  min_relief=mr, scar_keep=sk_, **st_kw)
            acu = ac + xo / r_c
            Ru = frame_wall(acu) @ rotz(rng.uniform(-0.1, 0.1)) @ roty(rng.uniform(-0.06, 0.06))
            Pu = xf(Vu, Ru)
            uu = np.array([math.sin(acu), -math.cos(acu), 0.0])
            Pu += uu * (face - rng.uniform(0.025, 0.05) - float((Pu @ uu).max()))
            acc.add(Pu, Fu, "M_stone", wear=rng.uniform(0.3, 0.6))
            placed.append((ac, zu, L))
    log("plinth kinds:", n_kind)
    log("plinth stones:", len(stones), "two-high:", n_two, f"({100 * n_two / len(stones):.0f} %)",
        "fractured:", n_fr)
    stones_ob = acc.build(coll)
    me = stones_ob.data
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])
    g.PL_TOP["bvh"] = bvh
    az_s = np.linspace(0, 2 * np.pi, 1441)
    zs = []
    for az in az_s:
        best = None
        for rr_ in (g.R_WALL - 0.03, g.R_WALL + 0.03):
            hit = bvh.ray_cast(Vector((math.sin(az) * rr_, -math.cos(az) * rr_, 1.5)), Vector((0, 0, -1.0)), 2.0)
            if hit[0] is not None:
                best = hit[0][2] if best is None else max(best, hit[0][2])
        zs.append(g.PLINTH_TOP if best is None else best)
    g.PL_TOP["az"], g.PL_TOP["z"] = az_s, np.array(zs)

    # ---------------- chinking: pooled FLAT wedges, ray-tested into open joints
    def face_r(az, z):
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        o = u * (g.R_WALL + 1.1) + np.array([0, 0, z])
        hit = bvh.ray_cast(Vector(o), Vector(-u), 2.0)
        if hit[0] is None:
            return None
        return (g.R_WALL + 1.1) - hit[3]

    def make_chink(acc_, k):
        rs = np.random.RandomState(7300 + k)
        # kit 1.6.0 (wall_finish gate_fine): the pooled chinking's 1.5 mm noise / 0.6 mm pits are below every note-11
        # threshold (entrance 1 cm) -> dropped
        V, F = chink_stone(rs, min_relief=(g.detail.entrance_relief if (wf_.get("gate_fine") and g.detail.active)
                                           else 0.0))
        acc_.add(V, F, "M_mortar")            # producer note 7: chinking is on M_mortar

    n_ch = n_try = 0
    ch_rng = np.random.RandomState(9393)
    cands = []
    for i in range(len(placed) - 1):
        ac, zt, L = placed[i]
        ga = ac + (L / 2 - 0.02) / r_c
        zj = min(zt, placed[i + 1][1])
        for zc in (zj - 0.03, zj * 0.65, zj * 0.35):
            cands.append((ga + ch_rng.uniform(-0.003, 0.003), zc + ch_rng.uniform(-0.015, 0.015)))
    for (az, zc) in cands:
        n_try += 1
        rL = face_r(az - 0.05 / g.R_PL_FACE, zc)
        rR = face_r(az + 0.05 / g.R_PL_FACE, zc)
        rC = face_r(az, zc)
        if rL is None or rR is None:
            continue
        front = min(rL, rR) - 0.012 - ch_rng.uniform(0.0, 0.01)
        if rC is not None and rC > front - 0.012:
            continue                     # no open joint here (stones touch)
        k = ch_rng.randint(8)
        mesh = g.pools.mesh("chink", k, make_chink)
        R = frame_wall(az) @ roty(math.pi / 2 + ch_rng.uniform(-0.5, 0.5)) @ rotx(ch_rng.uniform(-0.15, 0.15))
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        g.pools.place(mesh, "plinth_chink", R, u * (front - 0.03) + np.array([0, 0, zc]))
        n_ch += 1
    log("chinking:", n_ch, "of", n_try, "candidate joints")


def drystone_plinth(g, seed=9191):
    """KIT COMPONENT: dry-stone plinth ring under a round wall of radius g.R_WALL (face at g.R_PL_FACE, nominal
    top g.PLINTH_TOP), stopping at the door-post pads; object <PREFIX>_plinth_stones + pooled chinking.
    Publishes g.PL_TOP (stone-top sampler used by the posts, the weave bedding and the coat foot)."""
    build_plinth(g, g.coll, seed=seed)
