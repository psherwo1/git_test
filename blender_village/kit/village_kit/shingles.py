"""village_kit.shingles -- ONE shingle / shake / board generator and the village-wide SIZE TABLE.

Ensemble review 1: one roofing scale for the whole village.  The shared scale is the CHUNKY shingle of the
signed-off hut cone (art bible section 1.6): 0.35-0.55 m wide, 3.4-4.2 cm butts, read clearly from 30 m.

SIZE_TABLE (metres) -- every kit roof draws its unit sizes from here:
  shingle        chunky hand-split shingle (hut cone, keep turret / lantern caps, mill cap): width 0.35-0.55
                 (course target 0.44, +-24 %), exposure 0.30-0.40 along the slope, full length 0.72, butt 3.4-4.2
                 cm tapering to 1 cm.
  shingle_apex   the last <= 3 courses under an apex collar: target width 0.40 (circumference forces it; widths
                 still >= 0.30).  DELIBERATE EXCEPTION, documented here: on a cone the course circumference shrinks
                 to ~2.5 m under a 1.45 m collar, so 0.44 m units would leave 5-6 shingles per course.
  shake          long split shake (keep collar, mill apron): 0.9-1.2 m long, 0.16-0.30 wide, 2.5-3.5 cm butt
                 tapering to 0.8 cm, ragged butt +-2.5 cm, jagged comb head.  Not a shingle: a different unit.
  board          vertical lantern / gable board: 0.16-0.30 wide, 25-40 mm thick, 0.5-1.5 cm gaps.
  starter        doubled eave starter course: 0.46 long, same widths as `shingle`.
Any building that needs a unit outside these ranges must add a named row here with the reason (kit edit rule).

Mesh conventions (shingle_mesh / shake_mesh / board_mesh): local x across (width), y from the butt (0) toward the
head (+L), z up out of the roof (0 = bed).  Placement bends them onto the roof surface (see
components.conical_roof).  Variants are pooled (producer note 3): SHINGLE_VARIANTS holds 16 hand-split base shapes.
"""
import math

import numpy as np

from .core import smoothstep

SIZE_TABLE = {
    "shingle": dict(width=(0.35, 0.55), target_w=0.44, w_jitter=(0.76, 1.24), exposure=(0.30, 0.40),
                    length=0.72, butt=(0.034, 0.042), head=0.010, gap=(0.006, 0.016)),
    "shingle_apex": dict(width=(0.30, 0.50), target_w=0.40, w_jitter=(0.76, 1.24), courses_below_collar=3),
    "starter": dict(length=0.46, target_w=0.44, w_jitter=(0.75, 1.25), butt=0.034, gap=(0.005, 0.012)),
    "shake": dict(length=(0.9, 1.2), width=(0.16, 0.30), butt=(0.025, 0.035), head=0.008, ragged=0.025),
    "board": dict(width=(0.16, 0.30), thick=(0.025, 0.040), gap=(0.005, 0.015)),
}

SH_LOOP_X = np.array([-0.97, -0.6, -0.2, 0.2, 0.6, 0.97, 1.0, 0.97, -0.97, -1.0])   # x / (W/2)
SH_LOOP_Z = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.5])            # z / thickness
SH_TOP = np.arange(6)


def shingle_variant(k, seed_base=6060):
    """pool of 16 hand-split shingle base shapes (producer note 3): ragged butt notches, corner
    rounding, cup, curl, butt thickness.  Placement only scales / bends them onto the cone."""
    rs = np.random.RandomState(seed_base + k)
    offs = rs.uniform(-0.012, 0.012, 10)
    offs[[0, 5, 6, 7, 8, 9]] *= 0.4
    for c_ in rs.choice([1, 2, 3, 4], rs.randint(2, 4), replace=False):
        offs[c_] += rs.uniform(0.012, 0.022)
    offs += SH_LOOP_X * rs.uniform(-0.012, 0.012)
    offs[[7, 8]] = offs[[5, 0]]
    offs[[6, 9]] = offs[[5, 0]]
    return dict(offs=offs, rc=rs.uniform(0.03, 0.07), cup=rs.uniform(0.002, 0.008), Tb=rs.uniform(0.034, 0.042),
                curl=rs.uniform(0.0, 0.005), curl_eave=rs.uniform(0.006, 0.016))


SHINGLE_VARIANTS = [shingle_variant(k) for k in range(16)]
SH_VARIANTS = SHINGLE_VARIANTS            # phase-1 name


def shingle_mesh(W, L, var, Th=0.01, curl=None, ys=None, bottom=True, head=True):
    """one shingle in local coords: x across (W), y from butt (0) to head (L), z up (0..thickness).
    Section loop: 6 top points (cup), rounded side edges, ONE bottom strip (the underside lies on the
    course below and is never seen), n-gon end caps.  Thickness tapers as on a full 0.72 m shingle,
    so a trimmed shingle is the exposed part of a real one."""
    if ys is None:
        base = [0.0, 0.006, 0.018, 0.04, 0.075, 0.13]
        ys = np.array(base + list(np.arange(0.2, L - 0.03, 0.07)) + [L])
    ys = np.asarray(ys, float)
    n, m = len(ys), len(SH_LOOP_X)
    Tb = var["Tb"]
    cup = var["cup"]
    curl = var["curl"] if curl is None else curl
    rc = var["rc"]
    Y = np.broadcast_to(ys[:, None], (n, m)).copy()
    X = np.broadcast_to(SH_LOOP_X[None, :] * W / 2, (n, m)).copy()
    thick = Tb - (Tb - Th) * np.clip(ys / 0.72, 0, 1)
    Z = SH_LOOP_Z[None, :] * thick[:, None]
    # rounded butt corners in plan
    x_edge = W / 2 - rc + np.sqrt(np.clip(rc ** 2 - (rc - np.minimum(ys, rc)) ** 2, 0, None))
    shrink = (W / 2 - x_edge)[:, None] * smoothstep(0.5, 1.0, np.abs(SH_LOOP_X))[None, :]
    X = X - np.sign(X) * shrink
    # ragged hand-split butt on the first rings; arris rounding: ring 0 inset
    Y[:2] += var["offs"][None, :] * np.array([[1.0], [0.85]])
    X[0] *= 1 - 0.008 / max(W, 0.1)
    Z[0] = Z[0] * 0.8 + thick[0] * 0.1
    # cup (edges lift) and curl (butt lifts)
    Z = Z + cup * (2 * X / W) ** 2 + curl * (1 - np.clip(Y / 0.72, 0, 1)) ** 2
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    j1 = (j + 1) % m
    jj = j if bottom else j[:, SH_LOOP_Z[j[0]] + SH_LOOP_Z[j1[0]] > 0]       # drop the underside strip
    jj1 = (jj + 1) % m
    F = [np.stack([i * m + jj, i * m + jj1, (i + 1) * m + jj1, (i + 1) * m + jj], -1).reshape(-1, 4),
         np.arange(m)[::-1][None, :] * 1]
    if head:
        F.append(((n - 1) * m + np.arange(m))[None, :])
    uv = np.stack([V[:, 0] / max(W, 1e-3) + 0.5, V[:, 1]], -1)
    return V, F, uv


def course_widths(rng, circ, n, jitter=(0.76, 1.24), gap=(0.006, 0.016)):
    """n unit widths (+ joint gaps) that exactly close a course of circumference circ (widths +-24 %)."""
    w = rng.uniform(jitter[0], jitter[1], n)
    gaps = rng.uniform(gap[0], gap[1], n)
    w = w / w.sum() * (circ - gaps.sum())
    return w, gaps


def units_per_course(r_mid, kind="shingle"):
    """how many units a ring course of mid radius r_mid takes at the SIZE_TABLE target width (>= 8)."""
    return max(8, int(round(2 * math.pi * r_mid / SIZE_TABLE[kind]["target_w"])))


def shake_mesh(rng, L=None, W=None, butt=None, head=None, ragged=None, comb=0.02, n_len=9):
    """long split shake (SIZE_TABLE['shake']): tapering thickness, split outline (head narrower, each long edge
    wandering inward), ragged stepped butt, jagged comb head, slight cup.  Local x across, y butt -> head, z up.
    Closed solid (bed face included).  Returns V, faces, uv."""
    t = SIZE_TABLE["shake"]
    L = rng.uniform(*t["length"]) if L is None else L
    W = rng.uniform(*t["width"]) if W is None else W
    tb = rng.uniform(*t["butt"]) if butt is None else butt
    th = t["head"] if head is None else head
    rg = t["ragged"] if ragged is None else ragged
    ys = np.linspace(0, 1, n_len)
    xs = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    taper = rng.uniform(0.0, 0.16)
    e1, e2 = rng.uniform(0, 0.02, 2)
    steps = rng.uniform(-rg, rg * 0.8, len(xs))
    comb_v = rng.uniform(-comb, comb * 0.4, len(xs))
    Y = ys[:, None] * L + steps[None, :] * np.clip(1 - ys[:, None] * 4, 0, 1) + comb_v[None, :] * ys[:, None] ** 3
    half = W / 2 * (1 - taper * ys)[:, None]
    X = xs[None, :] * half - np.sign(xs)[None, :] * np.where(xs[None, :] > 0, e1, e2) * np.sin(np.pi * ys)[:, None]
    T = (tb + (th - tb) * ys)[:, None] * np.ones_like(X)
    cup = rng.uniform(-0.004, 0.006) * (xs[None, :] ** 2 - 0.33)
    top = np.stack([X, Y, T + cup], -1)
    bot = np.stack([X, Y, np.zeros_like(X) + cup * 0.5], -1)
    nl, nx = top.shape[:2]
    V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
    off = nl * nx
    I = lambda i, j: i * nx + j  # noqa: E731
    F = []
    for i in range(nl - 1):
        for j in range(nx - 1):
            F.append([I(i, j), I(i, j + 1), I(i + 1, j + 1), I(i + 1, j)])
            F.append([off + I(i, j), off + I(i + 1, j), off + I(i + 1, j + 1), off + I(i, j + 1)])
        F.append([I(i, 0), I(i + 1, 0), off + I(i + 1, 0), off + I(i, 0)])
        F.append([I(i, nx - 1), off + I(i, nx - 1), off + I(i + 1, nx - 1), I(i + 1, nx - 1)])
    for j in range(nx - 1):
        F.append([I(0, j), off + I(0, j), off + I(0, j + 1), I(0, j + 1)])
        F.append([I(nl - 1, j), I(nl - 1, j + 1), off + I(nl - 1, j + 1), off + I(nl - 1, j)])
    uv = np.stack([V[:, 0] / max(W, 1e-3) + 0.5, V[:, 1]], -1)
    return V, [np.array(F)], uv


def board_mesh(rng, W=None, H=1.0, thick=None, chamfer=0.006, segs_h=4):
    """vertical plank / lantern board (SIZE_TABLE['board']): x across, y up the board (0..H), z out of the wall;
    chamfered rounded box with uneven ends (+-1 cm) and a slight cup.  Returns V, faces."""
    from .core import rbox
    t = SIZE_TABLE["board"]
    W = rng.uniform(*t["width"]) if W is None else W
    T = rng.uniform(*t["thick"]) if thick is None else thick
    V, F = rbox((W / 2, H / 2, T / 2), chamfer, (2, segs_h, 1))
    V[:, 1] += H / 2 + np.where(V[:, 1] > 0, rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.0)) * (np.abs(V[:, 1]) > H / 2 - 0.02)
    V[:, 2] += T / 2 - rng.uniform(0.0, 0.004) * (2 * V[:, 0] / W) ** 2
    return V, [F]
