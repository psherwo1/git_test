"""components.interior -- the interior depth visible through a doorway: earth floor (tucked under the sill)
and a hearth ring.  Nothing deeper than what the door shows (producer note 1 / 6)."""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..stones import box_stone
from ..core import rotz, xf
from ..stones import box_stone
from .frame import floor_z


def build_interior(g, coll, seed=1313):
    """earthen floor (tucked under the sill: no seam inside the doorway), hearth ring."""
    acc = g.acc("floor", 40)
    rng = np.random.RandomState(seed)
    nr, nt = 18, 96
    T1 = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    dth = np.angle(np.exp(1j * (T1 + np.pi / 2)))
    r_out = g.R_WALL + 0.02 + 0.20 * np.exp(-(dth / 0.22) ** 2)
    f_ = np.linspace(0.0, 1.0, nr)
    R_ = 0.03 + f_[:, None] * (r_out[None, :] - 0.03)
    T_ = np.broadcast_to(T1[None, :], R_.shape)
    X = R_ * np.cos(T_)
    Y = R_ * np.sin(T_)
    Z = floor_z(g, X, Y)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    i = np.arange(nr - 1)[:, None]
    j = np.arange(nt)[None, :]
    j1 = (j + 1) % nt
    F = np.stack([i * nt + j, (i + 1) * nt + j, (i + 1) * nt + j1, i * nt + j1], -1).reshape(-1, 4)
    acc.add(V, [F, np.arange(nt)[None, :]], "M_earth")
    hr = g.acc("hearth", 60)
    for k in range(13):
        a = 2 * math.pi * k / 13 + rng.uniform(-0.08, 0.08)
        half = np.array([rng.uniform(0.11, 0.16), rng.uniform(0.08, 0.11), rng.uniform(0.06, 0.09)])
        P, F = box_stone(half, 0.4, (4, 4, 3), rng, amp=0.012, freq=6)
        c = (math.cos(a) * 0.55, math.sin(a) * 0.55 + 0.4, g.SILL_TOP - 0.02 + half[2] * 0.6)
        hr.add(xf(P, rotz(a + math.pi / 2), c), F, "M_stone")
    acc.build(coll)
    hr.build(coll)


def interior(g, seed=1313):
    """KIT COMPONENT: the earth floor (to the wall line, tucked under the sill) and a hearth ring: the dark depth
    seen through the doorway (<PREFIX>_floor, <PREFIX>_hearth)."""
    build_interior(g, g.coll, seed=seed)
