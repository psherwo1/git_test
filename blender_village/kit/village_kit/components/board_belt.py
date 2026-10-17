"""components.board_belt -- a vertical-board BELT on a round body (kit 1.7.0, v2_tiered_hall).

    board_belt(g, name, below=None, seed=606, head_ring=True)   KIT COMPONENT
        the lantern belt / turret drum of art bible section 1.3: SIZE_TABLE 'board' units (16-30 cm, 2.5-4 cm thick,
        0.5-1.5 cm gaps) standing round the declared round body `name`, a closed dark backing drum behind them (a
        gap shows timber, never a void; never a cull target), a top closure, and a 16-piece hewn head ring the next
        tier's ring beam bears on.  below=<tier name>: the belt rises through that roof tier -- each board starts
        just under the covering (roof_flashing closes the joint) and nothing is modelled deeper.
        Objects <P>_<name>_boards, <P>_<name>_backing, <P>_<name>_ring.
"""
import math

import numpy as np

from ..geom import Acc, finalize, obox
from ..shingles import SIZE_TABLE
from .tier_frame import roof_z


class _BeltBody:
    """kit 1.12 (v5 round 2): a plain round body for board_belt(body=...) on frames without declared tier bodies."""

    def __init__(self, center, r, z0, z1):
        self.c = np.asarray(center, float)[:2]
        self.apothem = float(r)
        self.z0, self.z1 = float(z0), float(z1)


def board_belt(g, name, below=None, seed=606, head_ring=True, ring_h=0.11, body=None, gaps=(), foot_ring=False,
               openings=()):
    """KIT COMPONENT: see the module doc.
    kit 1.12 (v5 round 2; defaults = old): body=dict(center, r, z0, z1) -- the belt stands on a plain round body
    (e.g. the timber top storey of a rubble_walls.round_stone_body tower on a RoundFrame / PlanFrame: no TierFrame
    body / roof tier needed); gaps=[(az_deg, width, z0, z1), ...] -- window gaps: a board whose centre lies within
    width / 2 (arc) of the gap's azimuth (from -Y toward +X) is cut into a piece under z0 and one over z1 (the opening
    itself comes from wall_openings.build_opening(host=...)); foot_ring=True -- a second hewn ring (the timber sill
    band) round the belt's foot, over its joint with the stone head."""
    if body is not None:
        return _board_belt_plain(g, name, body, seed, head_ring, ring_h, gaps, foot_ring, openings)
    body = g.body(name)
    rng = np.random.default_rng(int(seed) + g.seed_offset)
    roof = g.roofs[below]["roof"] if below else None
    r = float(body.apothem)
    c = body.c
    T = SIZE_TABLE["board"]
    z_top = body.z1
    accb = Acc(g.name(name) + "_boards")
    th = rng.uniform(0, 0.1)
    z_feet = []
    while th < 2 * math.pi - 0.06:
        wd = rng.uniform(*T["width"])
        if 2 * math.pi - th - wd / r < 0.12:
            wd = (2 * math.pi - th) * r - rng.uniform(*T["gap"])
        dth = wd / r
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0.0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0.0])
        tk = rng.uniform(*T["thick"])
        foot = np.array([c[0], c[1], 0.0]) + n3 * (r + tk / 2)
        z0 = body.z0
        if roof is not None:
            zr = float(roof_z(roof, foot[0], foot[1]))
            if np.isfinite(zr):
                z0 = max(z0, zr - 0.10)
        z_feet.append(z0)
        z1 = z_top + rng.uniform(-0.012, 0.006)
        ask = rng.normal(0, 0.004)
        ex = np.array([0, 0, 1.0]) + t3 * ask
        obox(accb, (foot + np.array([0, 0, z0]))[None], ex / np.linalg.norm(ex), t3, n3, z1 - z0,
             wd - rng.uniform(*T["gap"]), tk, 0.006, "M_timber_weathered", nx=4, ny=4, nz=3, skip_back=True)
        th += dth
    coll = g.sub(name)
    finalize(accb, coll)
    # closed backing drum + top closure (never a cull target)
    nb = 64
    a = np.linspace(0, 2 * np.pi, nb, endpoint=False)
    rb = r - 0.02
    ring = np.stack([c[0] + rb * np.cos(a), c[1] + rb * np.sin(a)], 1)
    zb0 = min(z_feet) - 0.05
    V = np.concatenate([np.column_stack([ring, np.full(nb, zb0)]), np.column_stack([ring, np.full(nb, z_top + 0.01)]),
                        np.array([[c[0], c[1], z_top + 0.01]])])
    i = np.arange(nb)
    F = [np.stack([i, (i + 1) % nb, (i + 1) % nb + nb, i + nb], 1),
         np.stack([i + nb, (i + 1) % nb + nb, np.full(nb, 2 * nb)], 1)]
    acck = Acc(g.name(name) + "_backing")
    acck.add(V, F, "M_timber_weathered")
    finalize(acck, coll)
    if head_ring:
        accr = Acc(g.name(name) + "_ring")
        n_seg = 16
        ap = (r + 0.04) + ring_h * 0.5
        half = ap * math.tan(math.pi / n_seg)
        ph0 = rng.uniform(0, 2 * math.pi / n_seg)
        for k in range(n_seg):
            phi = ph0 + 2 * math.pi * k / n_seg
            n3 = np.array([math.cos(phi), math.sin(phi), 0.0])
            t3 = np.array([-math.sin(phi), math.cos(phi), 0.0])
            O = np.array([c[0], c[1], z_top - ring_h * 0.5 + rng.uniform(-0.006, 0.006)]) + n3 * ap - t3 * (half + 0.01)
            obox(accr, O[None], t3, n3, np.array([0, 0, 1.0]), 2 * half + 0.02, ring_h, ring_h, 0.014, "M_timber",
                 nx=4, ny=4, nz=4)
        finalize(accr, coll)
    g.belts[name] = dict(center=c, r=r, z0=min(z_feet), z1=z_top)


def _hewn_ring(acc, c, r, z_c, ring_h, rng, n_seg=16):
    """a 16-piece hewn ring (the head-ring language) centred at height z_c round radius r."""
    ap = (r + 0.04) + ring_h * 0.5
    half = ap * math.tan(math.pi / n_seg)
    ph0 = rng.uniform(0, 2 * math.pi / n_seg)
    for k in range(n_seg):
        phi = ph0 + 2 * math.pi * k / n_seg
        n3 = np.array([math.cos(phi), math.sin(phi), 0.0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0.0])
        O = np.array([c[0], c[1], z_c + rng.uniform(-0.006, 0.006)]) + n3 * ap - t3 * (half + 0.01)
        obox(acc, O[None], t3, n3, np.array([0, 0, 1.0]), 2 * half + 0.02, ring_h, ring_h, 0.014, "M_timber",
             nx=4, ny=4, nz=4)


def _board_belt_plain(g, name, body, seed, head_ring, ring_h, gaps, foot_ring, openings=()):
    """board_belt(body=...): the same SIZE_TABLE 'board' belt, backing drum and hewn rings on a plain round body,
    with window gaps (see board_belt).  body["z1"] may be a callable(g) (e.g. the round frame's plate top).
    openings=[(az_deg, spec)]: small cased windows through the belt from the kit's ONE opening builder
    (wall_openings.build_opening, timber host; the spec resolved by timber_walls.resolve_timber), each cutting its
    own gap.  Objects <P>_<name>_boards, _backing, _ring (+ _frames, _ironwork, _blockers).  Publishes
    g.BELTS[name]."""
    z1_ = body["z1"](g) if callable(body["z1"]) else body["z1"]
    B = _BeltBody(body["center"], body["r"], body["z0"], z1_)
    rng = np.random.default_rng(int(seed))
    r, c, z_top = B.apothem, B.c, B.z1
    T = SIZE_TABLE["board"]
    pre = f"{g.prefix}_{name}"
    ops = []
    if openings:
        from .timber_walls import resolve_timber
        for (az, spec) in openings:
            sp = resolve_timber(spec)
            sp["shutters"] = bool(sp.get("shutters")) and False      # lookouts in a drum: no open shutters
            zc0 = B.z0 + sp["sill"]
            ops.append((float(az), sp))
            gaps = list(gaps) + [(float(az), sp["width"] + 2 * sp["jamb"][0] + 0.02, zc0 - sp.get("rail", 0.14),
                                  zc0 + sp["height"] + sp["head"])]
    G = [(math.radians(a) - math.pi / 2, float(w), float(z0), float(z1)) for (a, w, z0, z1) in gaps]
    accb = Acc(pre + "_boards")
    th = rng.uniform(0, 0.1)
    while th < 2 * math.pi - 0.06:
        wd = rng.uniform(*T["width"])
        if 2 * math.pi - th - wd / r < 0.12:
            wd = (2 * math.pi - th) * r - rng.uniform(*T["gap"])
        dth = wd / r
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0.0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0.0])
        tk = rng.uniform(*T["thick"])
        foot = np.array([c[0], c[1], 0.0]) + n3 * (r + tk / 2)
        z1 = z_top + rng.uniform(-0.012, 0.006)
        ask = rng.normal(0, 0.004)
        ex = np.array([0, 0, 1.0]) + t3 * ask
        ex = ex / np.linalg.norm(ex)
        w_ = wd - rng.uniform(*T["gap"])
        spans = [(B.z0, z1)]
        for (tg, wg, za, zb) in G:
            if abs(math.remainder(tc - tg, 2 * math.pi)) * r < 0.5 * wg + 0.5 * wd:
                spans = [(a, b) for (a0, b0) in spans for (a, b) in ((a0, min(b0, za)), (max(a0, zb), b0))
                         if b - a > 0.05]
        for (za, zb) in spans:
            obox(accb, (foot + np.array([0, 0, za]))[None], ex, t3, n3, zb - za, w_, tk, 0.006,
                 "M_timber_weathered", nx=4, ny=4, nz=3, skip_back=True)
        th += dth
    finalize(accb, g.coll)
    nb = 64
    a = np.linspace(0, 2 * np.pi, nb, endpoint=False)
    rb = r - 0.02
    ring = np.stack([c[0] + rb * np.cos(a), c[1] + rb * np.sin(a)], 1)
    zb0 = B.z0 - 0.05
    V = np.concatenate([np.column_stack([ring, np.full(nb, zb0)]), np.column_stack([ring, np.full(nb, z_top + 0.01)]),
                        np.array([[c[0], c[1], z_top + 0.01]])])
    i = np.arange(nb)
    F = [np.stack([i, (i + 1) % nb, (i + 1) % nb + nb, i + nb], 1),
         np.stack([i + nb, (i + 1) % nb + nb, np.full(nb, 2 * nb)], 1)]
    acck = Acc(pre + "_backing")
    acck.add(V, F, "M_timber_weathered")
    finalize(acck, g.coll)
    if head_ring or foot_ring:
        accr = Acc(pre + "_ring")
        if head_ring:
            _hewn_ring(accr, c, r, z_top - ring_h * 0.5, ring_h, rng)
        if foot_ring:
            _hewn_ring(accr, c, r, B.z0 + ring_h * 0.5, ring_h, rng)
        finalize(accr, g.coll)
    if ops:
        from .wall_openings import build_opening, finish_accs, opening_accs
        oaccs = opening_accs(g, name)
        orng = np.random.default_rng(int(seed) + 11)
        for k, (az, sp) in enumerate(ops):
            a_ = math.radians(az)
            nrm = np.array([math.sin(a_), -math.cos(a_), 0.0])
            tng = np.array([math.cos(a_), math.sin(a_), 0.0])
            O = np.array([c[0], c[1], 0.0]) + nrm * (r + 0.005)
            build_opening(g, sp, O, tng, nrm, oaccs, orng, label=f"{name}_{k}",
                          host=dict(face=0.03, floor=B.z0, head_max=z_top - ring_h, ground=0.0, casing=True))
        finish_accs(g, oaccs)
    if not hasattr(g, "BELTS"):
        g.BELTS = {}
    g.BELTS[name] = dict(center=c, r=r, z0=B.z0, z1=z_top)
    return g.BELTS[name]
