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


def board_belt(g, name, below=None, seed=606, head_ring=True, ring_h=0.11):
    """KIT COMPONENT: see the module doc."""
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
