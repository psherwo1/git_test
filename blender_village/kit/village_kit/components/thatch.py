"""components.thatch -- a hipped thatch wing roof with rounded hips, an eave roll, a ridge comb and the junctions to
masonry (kit 1.1.0, from the hilltop keep's west wing; ref1).

The roof covers the annex of an OctFrame (WX_W..WX_E x WY_S..WY_N, pitch W_PITCH, overhang W_OVH, core CORE_T) and
dies into the hall's skirt roof (east) and the side turret (west).  The surface is a family of rounded-rectangle
contours (oct_frame.q_rr) so the hips are swells of the courses themselves.

    thatch_wing_roof(g, seed=3, rng_seed=1313)   stepped thatch courses run continuously round the N side, both
        rounded hips and the W end and S side, with drifting course lines, pinch-outs, crowned exposures, end feathers
        (no cut stubs), discrete clumps (producer note 11: no straw striation), a closed core body kept only where it
        shows, one continuous D-section eave roll with tapered ends and a hanging tuft fringe
        -> <P>_wing_roof_thatch_courses, <P>_wing_roof_thatch
    ridge_comb(g, seed=1414)      ridge dome, a ridge-rider log with pegs, and a comb of crossed riven shakes in V / X
        tufts (pooled SIZE_TABLE 'comb_shake' variants) -> <P>_wing_roof_rolls, <P>_wing_ridge_comb
    thatch_junctions(g, seed=1515)   rafter-pole ends in the eave gap, a lime-mortar fillet / stepped lead flashing
        along the true thatch-stone intersection round the turret and the hall, a lead valley apron dressed over the
        course steps under the skirt roof, lead flashing into the shake collar
        -> <P>_wing_roof_structure, <P>_wing_flashing, <P>_wing_fillet
Helpers: d_roll (D-section roll sweeps), tuft_fringe, mortar_fillet, stepped_flashing, flaunch_loop, thatch_cull.
"""
import math

import bpy
import numpy as np

from ..core import log
from ..geom import (Acc, TAN22, ax4, axn, catmull_closed, finalize, frame_matrix, fbm90, n1, prof_circle, rbox_v,
                    runs_of, runs_of_list, smooth_wave, sweep)
from ..shingles import SIZE_TABLE
from .hewn import peg
from .oct_frame import (FR, apo, eave_q, get_pool, hall_L, hall_map, hip_swell, oct_pp, place, q_rr, skirt_z_at,
                        thatch_low, thatch_swell, tur_dist, tur_reff, turret_outer, wing_top, wing_under)


def planes():
    """the wing roof's three plane slopes (S, N, W): origin(a, m) along the eave / up the slope, normal, a-range."""
    SP_, CP_ = FR.SP_, FR.CP_
    WX_W, WX_E, WY_S, WY_N, W_OVH = FR.WX_W, FR.WX_E, FR.WY_S, FR.WY_N, FR.W_OVH
    return {
        "S": dict(o=lambda a, m: np.stack([a, (WY_S - W_OVH) + m * CP_, 2.40 + m * SP_], -1),
                  n=np.array([0, -SP_, CP_]), a_rng=(WX_W - W_OVH - 0.3, WX_E + W_OVH)),
        "N": dict(o=lambda a, m: np.stack([a, (WY_N + W_OVH) - m * CP_, 2.40 + m * SP_], -1),
                  n=np.array([0, SP_, CP_]), a_rng=(WX_W - W_OVH - 0.3, WX_E + W_OVH)),
        "W": dict(o=lambda a, m: np.stack([(WX_W - W_OVH) + m * CP_, a, 2.40 + m * SP_], -1),
                  n=np.array([-SP_, 0, CP_]), a_rng=(WY_S - W_OVH - 0.3, WY_N + W_OVH + 0.3)),
    }


_ROLL_CTRL = np.array([
    (0.45, 1.025), (0.36, 0.929), (0.25, 0.8106), (0.08, 0.616), (0.0, 0.517),
    (-0.06, 0.428), (-0.11, 0.330), (-0.135, 0.220), (-0.126, 0.118), (-0.088, 0.044), (-0.025, 0.008),
    (0.07, 0.0), (0.20, 0.012), (0.31, 0.055), (0.375, 0.15), (0.41, 0.30), (0.43, 0.44),
    (0.47, 0.62), (0.47, 0.90)])
# round 5: the bolster is slimmed from ~0.5 to ~0.35 m (lower part compressed, the buried tail kept)
_ROLL_CTRL[:, 1] = np.where(_ROLL_CTRL[:, 1] <= 0.6, _ROLL_CTRL[:, 1] * 0.7,
                            _ROLL_CTRL[:, 1] - 0.18 * np.clip((0.95 - _ROLL_CTRL[:, 1]) / 0.35, 0, 1))
# visible weight per control point (ribs / bulges are only applied where the roll can be seen)
_ROLL_VIS = np.array([0, 0.3, 0.3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.8, 0.3, 0, 0], float)


HIP_DOME = np.array([(-0.27, -0.17), (-0.235, -0.06), (-0.19, 0.035), (-0.12, 0.105), (-0.035, 0.14), (0.05, 0.138),
                     (0.13, 0.10), (0.20, 0.03), (0.24, -0.06), (0.27, -0.17), (0.0, -0.22)])
HIP_VIS = np.array([0.2, 1, 1, 1, 1, 1, 1, 1, 1, 0.2, 0.0])
RIDGE_DOME = np.array([(-0.31, -0.40), (-0.30, -0.30), (-0.265, -0.15), (-0.205, -0.02), (-0.12, 0.075),
                       (-0.02, 0.115), (0.08, 0.10), (0.17, 0.035), (0.24, -0.07), (0.29, -0.22), (0.31, -0.40),
                       (0.0, -0.50)])
RIDGE_VIS = np.array([0.2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.2, 0.0])

COMB_LEN = np.array(SIZE_TABLE["comb_shake"]["lengths"])


def plane_under(name, x, y):
    if name == "S":
        return FR.W_RAFT + (y - FR.WY_S) * FR.W_TAN
    if name == "N":
        return FR.W_RAFT + (FR.WY_N - y) * FR.W_TAN
    return FR.W_RAFT + (x - FR.WX_W) * FR.W_TAN


def thatch_cull(C, tol_skirt=True):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    bad = tur_dist(x, y, z) < -0.06
    ang = np.arctan2(y, x)
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = x * np.cos(kk * np.pi / 4) + y * np.sin(kk * np.pi / 4)
    zs = FR.SKIRT.zb(pp)
    # inside the hall's plan: only what lies below the skirt sheathing (walls, plates, rafters) is culled; thatch
    # above the skirt runs on over it until it meets the collar / cone
    bad |= (pp < apo(np.clip(z, 0, FR.WALL_H)) + 0.02) & (z < np.maximum(zs - 0.02, FR.RAFTER_SEAT + 0.1))
    if tol_skirt:
        wt = wing_top(x, y)
        bad |= (pp < FR.SKIRT.p_lip + 0.08) & (wt < zs + 0.07) & (z > zs - 0.27)
    r = np.hypot(x, y)
    bad |= (r < np.interp(z, FR.CONE_ZF, FR.CONE_RF) + 0.12) & (z > 4.4)
    # under the shake collar: the thatch runs on under the collar shakes (shakes buried in the thatch are dropped);
    # only cull what would pass through the collar backing frustum
    bad |= (z > 4.5) & (z < FR.COLLAR_TOP_Z + 0.1) & (r < np.interp(z, [4.6, FR.COLLAR_TOP_Z], [3.5, 2.95]) - 0.10)
    return bad


def thatch_roll(acc, path, r0, seed, flat=0.8, seg=12, mat="M_thatch", bind=0.16, stri=0.0, step=0.05):
    """lumpy bound thatch roll along a path (constrictions every ~0.34 m, irregular section).
    stri > 0: strand striations wrapping the roll (grooves every 1.5-3 cm along the path, depth = stri)."""
    path = np.asarray(path, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    if d[-1] < 0.1:
        return
    n = max(4, int(d[-1] / step))
    ds = np.linspace(0, d[-1], n)
    P = np.stack([np.interp(ds, d, path[:, i]) for i in range(3)], 1)
    bnd = (1 - bind) + bind * np.clip(np.abs(np.sin(np.pi * ds / 0.34 + seed)) * 2.2, 0, 1)
    rr = r0 * bnd * (1 + 0.12 * n1(ds * 1.3, seed))
    # ends taper and round off (rolls die into the neighbouring roll / surface instead of ending as flat caps)
    te = min(0.3, d[-1] * 0.3)
    endf = np.minimum(np.clip(ds / te, 0, 1), np.clip((d[-1] - ds) / te, 0, 1))
    rr = rr * (0.45 + 0.55 * np.sqrt(np.clip(1 - (1 - endf) ** 2, 0, 1)))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    profs = []
    for i in range(n):
        lump = 1 + 0.10 * fbm90(np.stack([np.cos(a) * 1.7 + ds[i] * 4.0, np.sin(a) * 1.7, np.full(seg, seed * 3.3)], -1), 2)
        if stri > 0:
            ph = ds[i] / 0.022 + 2.5 * n1(np.full(seg, ds[i]) * 2.0 + a * 0.4, seed + 5)
            lump = lump - (stri / r0) * np.clip(np.cos(np.pi * ph) * 1.6 - 0.6, 0, 1) * (0.6 + 0.4 * np.sin(a) ** 2)
        profs.append(np.stack([rr[i] * np.cos(a) * lump, rr[i] * flat * np.sin(a) * lump], 1))
    V, F = sweep(P, (0, 0, 1), np.stack(profs))
    acc.add(V, F, mat)


def roll_profile():
    nper = np.array([1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1])
    P, sid = catmull_closed(_ROLL_CTRL, nper)
    vis = np.interp(sid, np.arange(len(_ROLL_CTRL) + 1), np.concatenate([_ROLL_VIS, _ROLL_VIS[:1]]))
    return P, vis


def roll_top_mh(CP_, SP_):
    """roll upper surface in plane coords (m, h) for a roof of pitch cos CP_ / sin SP_: used to seat the first
    course into the roll."""
    up = ROLL_P[:np.argmin(ROLL_P[:, 0]) + 1]            # tail -> nose (upper surface)
    q, v = up[:, 0], up[:, 1]
    m = q * CP_ + v * SP_
    h = -q * SP_ + v * CP_
    o = np.argsort(m)
    return m[o], h[o]


def roll_top_v(q):
    """vertical height (above the 2.40 lip) of the roll's upper surface at inward distance q; -inf beyond the nose."""
    up = ROLL_P[:np.argmin(ROLL_P[:, 0]) + 1]
    o = np.argsort(up[:, 0])
    q = np.asarray(q, float)
    v = np.interp(q, up[o, 0], up[o, 1])
    return np.where(q < up[:, 0].min(), -1e9, v)


def prof_normals(P):
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    N = np.stack([T[:, 1], -T[:, 0]], 1)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    c = P.mean(0)
    sgn = np.sign(np.sum((P - c) * N, 1, keepdims=True))
    sgn[sgn == 0] = 1
    return N * np.where(np.median(sgn) < 0, -1.0, 1.0)


def rib_stations(L, rng, sp=(0.01, 0.04), dep=(0.003, 0.015)):
    """irregular strand ribs along a roll: groove centres at 1-4 cm spacing, 0.3-1.5 cm deep; returns station
    positions and the groove depth at each station (midpoints between grooves carry 0)."""
    g = [rng.uniform(0, sp[1])]
    while g[-1] < L:
        g.append(g[-1] + rng.uniform(*sp))
    g = np.array(g[:-1])
    d = dep[0] + (dep[1] - dep[0]) * rng.uniform(0, 1, len(g)) ** 1.2
    mids = 0.5 * (g[1:] + g[:-1])
    st = np.concatenate([[0.0], g, mids, [L]])
    dd = np.concatenate([[0.0], d, np.zeros(len(mids)), [0.0]])
    o = np.argsort(st)
    st, dd = st[o], dd[o]
    keep = np.concatenate([[True], np.diff(st) > 0.002])
    return st[keep], dd[keep]


def d_roll(acc, path, prof, vis, seed, rng, up=(0.0, 0.0, 1.0), var=0.03, sp=(0.01, 0.04), dep=(0.003, 0.015),
           taper=(0.0, 0.0), mat="M_thatch", z_wave=0.012, tmin=(0.45, 0.45), drop_hidden=False, keep_back_fn=None,
           ribs=True, step=0.05):
    """sweep a (D / dome) section along a path with irregular strand ribs (no regular binding), +-var section
    swelling over 0.5-1 m, and optional rounded tapers at the ends (taper lengths in m).  ribs=False (producer
    note 11: the 0.3-1.5 cm strand ribs are straw striation, a material job): no ribs, stations every `step` m."""
    path = np.asarray(path, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    L = d[-1]
    if L < 0.08:
        return
    if ribs:
        st, dd = rib_stations(L, rng, sp, dep)
    else:
        st = np.linspace(0, L, max(int(math.ceil(L / step)), 2) + 1)
        dd = np.zeros(len(st))
    P = np.stack([np.interp(st, d, path[:, i]) for i in range(3)], 1)
    P[:, 2] += z_wave * n1(st * 0.9, seed + 1)
    ups = np.asarray(up, float)
    if ups.ndim == 2:
        ups = np.stack([np.interp(st, d, ups[:, i]) for i in range(3)], 1)
    N2 = prof_normals(prof)
    cen = prof[vis > 0.5].mean(0) if (vis > 0.5).any() else prof.mean(0)
    pidx = np.arange(len(prof))
    profs = []
    for i, s in enumerate(st):
        sw = var * (0.65 * n1(np.full(len(prof), s / 0.75), seed) + 0.35 * n1(np.full(len(prof), s / 0.45), seed + 7))
        sw = sw * (0.75 + 0.25 * np.cos(pidx * 0.7 + s * 3.0))
        gr = dd[i] * (0.55 + 0.45 * n1(pidx * 0.45 + s * 5.0, seed + 3))
        pr = prof + N2 * ((sw - gr) * vis)[:, None]
        tf = 1.0
        if taper[0] > 0 and s < taper[0]:
            tf = tmin[0] + (1 - tmin[0]) * math.sqrt(max(0.0, 1 - (1 - s / taper[0]) ** 2))
        if taper[1] > 0 and L - s < taper[1]:
            tf = min(tf, tmin[1] + (1 - tmin[1]) * math.sqrt(max(0.0, 1 - (1 - (L - s) / taper[1]) ** 2)))
        if tf < 1.0:
            pr = cen + (pr - cen) * tf
        profs.append(pr)
    V, F = sweep(P, ups, np.stack(profs))
    if drop_hidden:
        # the tail of the section buried in the thatch body is not modelled (no caps: the ends sit in stone / thatch)
        m_ = len(prof)
        jj = np.tile(np.arange(m_), len(st) - 1)
        hid = (vis[jj] < 0.5) & (vis[(jj + 1) % m_] < 0.5)
        if keep_back_fn is not None:
            # round 6: keep the roll's back where nothing else closes it (e.g. at the turret, where the core and
            # the turret stones are both cut away): no view into the open roll section
            kb = np.asarray(keep_back_fn(P), bool)
            hid &= ~np.repeat(kb[:-1] | kb[1:], m_)
        F = [F[0][~hid]] + list(F[1:])
    acc.add(V, F, mat)
    return P


def eave_path():
    """plan path of the eave line N -> W -> S with rounded hipped corners (radius FR.EAVE_RC), at the 2.40 lip."""
    yS, yN, xW = FR.WY_S - FR.W_OVH, FR.WY_N + FR.W_OVH, FR.WX_W - FR.W_OVH
    xe = 0.4
    rc = FR.EAVE_RC
    pts = []
    # NE return: the N eave turns the wing's NE corner under the hall skirt and runs south into the hall's N wall
    xr_ = FR.WX_E + FR.W_OVH
    for y in np.arange(3.5, yN - rc, 0.02):
        pts.append((xr_, y))
    for a in np.linspace(0.0, np.pi / 2, 12)[1:-1]:
        pts.append((xr_ - rc + rc * np.cos(a), yN - rc + rc * np.sin(a)))
    for x in np.arange(xr_ - rc, xW + rc, -0.02):
        pts.append((x, yN))
    for a in np.linspace(np.pi / 2, np.pi, 12)[1:-1]:
        pts.append((xW + rc + rc * np.cos(a), yN - rc + rc * np.sin(a)))
    for y in np.arange(yN - rc, yS + rc, -0.02):
        pts.append((xW, y))
    for a in np.linspace(np.pi, 1.5 * np.pi, 12)[1:-1]:
        pts.append((xW + rc + rc * np.cos(a), yS + rc + rc * np.sin(a)))
    for x in np.arange(xW + rc, xe + 1e-6, 0.02):
        pts.append((x, yS))
    P = np.array(pts)
    return np.column_stack([P, np.full(len(P), 2.40)])


def thatch_top_z(x, y):
    """approximate outer thatch surface (course tops near the mean, roll top near the eaves)."""
    zt = wing_under(x, y) + (FR.TH_BASE + 0.045) / FR.CP_
    q = eave_q(x, y)
    zr = 2.40 + roll_top_v(q) + 0.0 * q
    return np.where(q < -0.135, -1e9, np.where(q < 0.4, zr, zt))


def contour_polyline(d, x_east, step=0.01, rc=None):
    """plan polyline of the roof contour at inset d: N eave side (east -> west), NW hip arc, W side, SW hip arc,
    S side (west -> east). Returns arc length, points, inward normals."""
    rc = FR.HIP_RC if rc is None else rc
    xW = FR.WX_W - FR.W_OVH + d
    yS = FR.WY_S - FR.W_OVH + d
    yN = FR.WY_N + FR.W_OVH - d
    P, N = [], []
    xs = np.arange(x_east, xW + rc, -step)
    P.append(np.stack([xs, np.full_like(xs, yN)], 1))
    N.append(np.tile([0.0, -1.0], (len(xs), 1)))
    na = max(int(0.5 * np.pi * rc / step), 4)
    for a0, cy_ in ((0.5 * np.pi, yN - rc), (np.pi, yS + rc)):
        a = np.linspace(a0, a0 + 0.5 * np.pi, na, endpoint=False)
        u = np.stack([np.cos(a), np.sin(a)], 1)
        P.append(np.array([xW + rc, cy_]) + rc * u)
        N.append(-u)
        if a0 < 3:
            ys = np.arange(yN - rc, yS + rc, -step)
            P.append(np.stack([np.full_like(ys, xW), ys], 1))
            N.append(np.tile([1.0, 0.0], (len(ys), 1)))
    xs = np.arange(xW + rc, x_east + 1e-9, step)
    P.append(np.stack([xs, np.full_like(xs, yS)], 1))
    N.append(np.tile([0.0, 1.0], (len(xs), 1)))
    P = np.concatenate(P)
    N = np.concatenate(N)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    keep = np.concatenate([[True], seg > 1e-7])
    P, N = P[keep], N[keep]
    S = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return S, P, N


def deck_point(Q):
    """thatch underside point and unit deck normal at plan points Q (n,2)."""
    e = 1e-3
    x, y = Q[..., 0], Q[..., 1]
    gx = (q_rr(x + e, y) - q_rr(x - e, y)) / (2 * e)
    gy = (q_rr(x, y + e) - q_rr(x, y - e)) / (2 * e)
    z = 2.40 + FR.W_TAN * q_rr(x, y)
    n = np.stack([-FR.W_TAN * gx, -FR.W_TAN * gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.stack([x, y, z], -1), n


def _interp_rows(mq, M5, H5):
    n = len(mq)
    ar = np.arange(n)
    idx = np.clip((mq[:, None] >= M5).sum(1) - 1, 0, M5.shape[1] - 2)
    m0, m1 = M5[ar, idx], M5[ar, idx + 1]
    h0, h1 = H5[ar, idx], H5[ar, idx + 1]
    t = np.clip((mq - m0) / np.maximum(m1 - m0, 1e-6), 0, 1)
    return h0 + (h1 - h0) * t


def thatch_courses(acc, rng, seed, lobe_w=(0.025, 0.045), clump_w=(0.04, 0.12), m0=0.64, m_max=3.95,
                   drift=(0.085, 0.055), expo_lim=(0.24, 0.36), straw_pitch=(0.015, 0.03), straw_depth=(0.005, 0.015),
                   straw_patch=(0.2, 0.5), straw_skew_deg=5.0, end_feather=0.4, relief_min=0.0,
                   clump_cols=(0.07, 0.15)):
    """Kit component: stepped thatch courses laid as continuous strips round the whole hipped roof (N side, rounded
    NW hip, W end, rounded SW hip, S side), so the hips are a swell of the courses themselves.
    Round 5:
      * course lines drift: a shared low-frequency drift (drift[0], in slope metres) plus an independent per-course
        drift (drift[1]) over 2-4 m wavelengths; the exposure stays inside expo_lim along the whole run, so
        neighbouring butt lines visibly converge and diverge;
      * straw relief on the S slope, both hips and the W end: fall-line ridges straw_depth deep at straw_pitch,
        broken into straw_patch long patches whose direction is skewed +-straw_skew_deg; the N side keeps the
        grouped lobes;
      * every course end (valley under the hall skirt, turret flanks) feathers to nothing over end_feather metres:
        the step, crown and straw relief die out and the course sinks under the course below (no cut stubs);
      * the exposed course top carries an extra crowned row (soft, lumpy, not a flat slab).
    Producer note 11 (relief_min > straw_depth): the straw ridges are not modelled (striation is a material job);
    the courses are laid as discrete thatch CLUMPS instead -- one column pair per clump (clump_cols wide), each clump
    crowned 0.8-1.6 cm and standing +-2-3 cm proud of its neighbours with a 1.2-2 cm crease between them, so the
    bundles read at actor and crane distance with a fraction of the straw's triangles."""
    from mathutils.kdtree import KDTree
    straw_on = straw_depth[1] >= relief_min
    ms = []
    m = m0
    while m < m_max:
        E = rng.uniform(0.27, 0.33)
        ms.append((m, E))
        m += E
    nC = len(ms)
    pinch_ids = set(int(v) for v in rng.choice(np.arange(2, nC - 2), 2, replace=False))
    x_east = FR.WX_E + FR.W_OVH
    m_ridge = 0.5 * ((FR.WY_N + FR.W_OVH) - (FR.WY_S - FR.W_OVH)) / FR.CP_
    rng_sh = np.random.default_rng(seed * 7 + 1)
    sh_l = [rng_sh.uniform(2.0, 4.0) for _ in range(3)]
    sh_p = [rng_sh.uniform(0, 2 * np.pi) for _ in range(3)]
    sh_w = np.array([0.45, 0.35, 0.2])

    def shared(Aq):
        return sum(w_ * np.sin(2 * np.pi * Aq / l_ + p_) for w_, l_, p_ in zip(sh_w, sh_l, sh_p))
    prev = None
    prev_line = None
    nq_tot = 0
    for ci, (m_i, E) in enumerate(ms):
        d_i = m_i * FR.CP_
        Sx, Px, Nx = contour_polyline(d_i, x_east)
        Lc = Sx[-1]
        # end of the N side straight on this contour: straw relief on the hips, W end and S side only
        xW_c = FR.WX_W - FR.W_OVH + d_i
        A_n = x_east - (xW_c + FR.HIP_RC)
        def in_straw(Aq):
            return np.clip((np.asarray(Aq) - (A_n - 0.4)) / 0.4, 0, 1)
        # columns: grouped lobes on the N side, straw ridges (crest + trough per ridge) elsewhere
        lb = [-rng.uniform(0.0, 0.03)]
        flags = [True]
        nxt = lb[0] + rng.uniform(*clump_w)
        while lb[-1] < Lc + 0.02:
            if not straw_on:
                nb = lb[-1] + rng.uniform(*clump_cols)             # one column pair per thatch clump
            elif in_straw(lb[-1]) > 0.5:
                nb = lb[-1] + rng.uniform(*straw_pitch)
            else:
                nb = lb[-1] + rng.uniform(0.028, 0.042)      # N side: coarser, shallower straw
            fl = (nb >= nxt - 0.008) or not straw_on
            if fl:
                nxt = nb + rng.uniform(*clump_w)
            lb.append(nb)
            flags.append(fl)
        lb = np.array(lb)
        flags = np.array(flags)
        nl = len(lb) - 1
        clump_of_b = np.cumsum(flags) - 1
        lobe_clump = clump_of_b[:-1]
        A = np.empty(2 * nl + 1)
        A[0::2] = lb
        A[1::2] = lb[:-1] + np.diff(lb) * rng.uniform(0.38, 0.62, nl)
        ncol = len(A)
        isb = np.zeros(ncol, bool)
        isb[0::2] = True
        lid = np.minimum(np.arange(ncol) // 2, nl - 1)
        lprev = np.maximum(lid - 1, 0)
        ncl = int(lobe_clump.max()) + 1
        prot_c = np.clip(0.012 * n1(np.arange(ncl) * 0.35, seed * 31 + ci) + rng.normal(0, 0.004, ncl), -0.018, 0.018)
        prot_l = prot_c[lobe_clump] + rng.normal(0, 0.002, nl)
        crown = rng.uniform(0.002, 0.004, nl)
        bflag = np.zeros(ncol, bool)
        bflag[0::2] = flags
        crease = np.where(bflag, rng.uniform(0.0015, 0.002, ncol), rng.uniform(0.0005, 0.001, ncol))
        if not straw_on:
            prot_l = prot_l * 1.6
            crown = crown * 4.0
            crease = crease * 10.0
        p_col = np.where(isb, np.minimum(prot_l[lprev], prot_l[lid]) - 0.002, prot_l[lid])
        cr_ = np.where(isb, -crease, crown[lid])
        # straw relief: patches of 0.2-0.5 m with their own depth and skew
        wst = 0.55 + 0.45 * in_straw(A)
        pb_ = [A[0] - 0.01]
        while pb_[-1] < A[-1] + 0.01:
            pb_.append(pb_[-1] + rng.uniform(*straw_patch))
        pb_ = np.array(pb_)
        npch = len(pb_) - 1
        pch = np.clip(np.searchsorted(pb_, A) - 1, 0, npch - 1)
        pdep = rng.uniform(*straw_depth, npch)
        pskw = np.radians(rng.uniform(-straw_skew_deg, straw_skew_deg, npch))
        # blend patch values over ~4 cm at the patch boundaries (no tearing between patches)
        k_ = np.exp(-0.5 * ((A[:, None] - 0.5 * (pb_[:-1] + pb_[1:])[None]) /
                            (0.25 * np.diff(pb_)[None] + 0.02)) ** 2)
        k_ /= k_.sum(1, keepdims=True)
        skew = k_ @ pskw
        rdep = (k_ @ pdep) * rng.uniform(0.6, 1.0, ncol)
        rd = np.where(isb, -0.5, 0.5) * rdep * wst * (1.0 if straw_on else 0.0)
        # the straw replaces the soft lobes on the straw zone
        if straw_on:
            p_col = p_col * 0.25
            cr_ = cr_ * 0.25
        pinch = np.ones(ncol)
        if ci in pinch_ids:
            for _ in range(2):
                ac = rng.uniform(1.0, Lc - 1.0)
                wpi = rng.uniform(0.9, 1.6)
                pinch *= 1 - 0.8 * 0.5 * (1 + np.cos(np.pi * np.clip((A - ac) / (0.5 * wpi), -1, 1)))

        def frame(Aq):
            Pq = np.stack([np.interp(Aq, Sx, Px[:, 0]), np.interp(Aq, Sx, Px[:, 1])], -1)
            Nq = np.stack([np.interp(Aq, Sx, Nx[:, 0]), np.interp(Aq, Sx, Nx[:, 1])], -1)
            return Pq, Nq / np.linalg.norm(Nq, axis=-1, keepdims=True)
        Pc, Nc = frame(A)
        # course line: shared drift + independent drift (2-4 m), exposure clamped to expo_lim against the course
        # below
        # A on a common reference contour (the inner contours are shorter by 2*inset round the W end)
        arc_ = 0.5 * np.pi * FR.HIP_RC
        A_ref = A + 2 * (d_i - m0 * FR.CP_) * np.clip((A - A_n) / arc_, 0, 1)
        indep = smooth_wave(A_ref, rng, (2.0, 4.0), 3)
        mi = m_i + drift[0] * shared(A_ref) + drift[1] * indep
        if prev_line is not None:
            mprev = np.interp(A_ref, prev_line[0], prev_line[1])
            mi = np.clip(mi, mprev + expo_lim[0], mprev + expo_lim[1])
        stp0 = (0.05 + 0.02 * n1(A / 0.7, seed * 100 + ci + 50)) * pinch
        # valley fade toward the hall skirt (the steps die out; the courses sweep into a rounded valley)
        Pb = Pc + Nc * ((mi - m_i) * FR.CP_)[:, None]
        Db, _ = deck_point(Pb)
        zs_b, pp_b = skirt_z_at(Pb[:, 0], Pb[:, 1])
        ztop_nom = Db[:, 2] + (FR.TH_BASE + thatch_swell(Pb[:, 0], Pb[:, 1])) / FR.CP_
        g = ztop_nom - (zs_b + 0.07)
        infoot = pp_b < FR.SKIRT.p_lip + 0.35
        fade = np.where(infoot, np.clip(g / 0.45, 0, 1), 1.0)
        fade = fade * fade * (3 - 2 * fade)
        F = 0.10 + 0.05 * (0.5 + 0.5 * n1(A / 0.9, seed + ci * 7))
        beta = np.radians(rng.uniform(32.0, 40.0))
        bump = 0.004 + 0.006 * (0.5 + 0.5 * n1(A / 0.33, seed * 13 + ci))       # crowned exposure, 0.4-1 cm
        fe = np.ones(ncol)                                                      # end feather (pass 2)

        for pass_ in (0, 1):
            ff = fade * fe
            stp = stp0 * ff
            crr = cr_ * ff
            rdd = rd * fe
            mb = mi - p_col * ff
            m_far = mi + E + 0.07

            def plan(mrow, Ash=None):
                mrow = np.minimum(mrow, m_ridge)
                if Ash is None:
                    return Pc + Nc * ((mrow - m_i) * FR.CP_)[:, None]
                Pq, Nq = frame(A + Ash)
                return Pq + Nq * ((mrow - m_i) * FR.CP_)[:, None]

            def low_at(mrow):
                Q = plan(mrow)
                mg = q_rr(Q[:, 0], Q[:, 1]) / FR.CP_
                if prev is None:
                    return np.interp(mg, FR.ROLL_TOP_M, FR.ROLL_TOP_H)
                kd, pM, pH = prev
                idx = np.array([kd.find((float(q_[0]), float(q_[1]), 0.0))[1] for q_ in Q])
                return _interp_rows(mg, pM[idx], pH[idx])
            Qb = plan(mb)
            sw_b = thatch_swell(Qb[:, 0], Qb[:, 1]) + hip_swell(Qb[:, 0], Qb[:, 1])
            top = FR.TH_BASE + stp + sw_b + np.where(isb, 0.45, 1.0) * crr
            low_b = low_at(mb)
            dh = np.maximum(top - low_b, 0.012) * fe - 0.008 * (1 - fe)
            run = np.maximum(np.abs(dh), 0.004) / np.tan(beta)
            m_mid = mb + run + 0.5 * np.maximum(m_far - mb - run, 0.02)
            rows_m = np.stack([mb - F, mb - 0.45 * F, mb - 0.12 * F, mb - 0.01, mb + run, m_mid, m_far], 1)
            Qf = plan(m_far)
            h_far = FR.TH_BASE - 0.004 + thatch_swell(Qf[:, 0], Qf[:, 1]) + hip_swell(Qf[:, 0], Qf[:, 1]) + 0.3 * crr
            h_top = low_b + dh
            rows_h = np.stack([low_at(mb - F) - 0.004, low_at(mb - 0.45 * F) + 0.05 * dh,
                               low_at(mb - 0.12 * F) + 0.22 * dh, low_b + 0.72 * dh, h_top,
                               0.5 * (h_top + h_far) + bump * ff, h_far], 1)
            # straw ridges (fall-line), all exposed rows; skewed per patch
            rows_h = rows_h + rdd[:, None] * np.array([0.3, 0.6, 0.9, 1.0, 1.0, 1.0, 0.7])[None]
            NR = rows_m.shape[1]
            Am = np.repeat(A[:, None], NR, 1)
            sk = np.tan(skew) * wst
            Q = np.stack([plan(rows_m[:, j], sk * (rows_m[:, j] - mb) * FR.CP_) for j in range(NR)], 1)
            D, Nd = deck_point(Q)
            W = D + rows_h[..., None] * Nd
            # under the hall skirt eave: soft clamp below the skirt sheathing near the valley line
            zs_, pp_ = skirt_z_at(W[..., 0], W[..., 1])
            g_v = wing_top(W[..., 0], W[..., 1]) - (zs_ + 0.07)
            wv = np.clip(0.5 - g_v / 0.2, 0, 1) * (pp_ < FR.SKIRT.p_lip + 0.06)
            wv = wv * wv * (3 - 2 * wv)
            zl = zs_ - 0.05
            zc_ = zl - 0.05 * np.logaddexp(0.0, (zl - W[..., 2]) / 0.05)
            W[..., 2] = W[..., 2] * (1 - wv) + np.minimum(zc_, W[..., 2]) * wv
            idx = np.arange(ncol * NR).reshape(ncol, NR)
            q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
            Wf = W.reshape(-1, 3)
            n0 = np.cross(Wf[q[:, 1]] - Wf[q[:, 0]], Wf[q[:, 3]] - Wf[q[:, 0]])
            if np.median(n0[:, 2]) < 0:
                q = q[:, ::-1]
            C = Wf[q].mean(1)
            x_, y_ = C[:, 0], C[:, 1]
            bad = thatch_cull(C, tol_skirt=False)
            bad |= ~((x_ > FR.WX_W - FR.W_OVH - 0.12) & (x_ < FR.WX_E + FR.W_OVH + 0.04) & (y_ > FR.WY_S - FR.W_OVH - 0.12) &
                     (y_ < FR.WY_N + FR.W_OVH + 0.12))
            bad |= eave_q(x_, y_) < 0.08
            # course tails buried under the ridge dome (within 0.2 m of the ridge line, east of the W hip apex)
            Wq = Wf[q]
            bad |= (np.abs(Wq[..., 1] - FR.WY_R) < 0.2).all(1) & (Wq[..., 0] > FR.WX_W + (FR.WY_R - FR.WY_S) - 0.4).all(1)
            zsq, ppq = skirt_z_at(Wf[q][..., 0], Wf[q][..., 1])
            bad |= ((ppq < FR.SKIRT.p_lip - 0.35) & (Wf[q][..., 2] < zsq - 0.04)).all(1)
            if pass_ == 0:
                # columns whose butt quads survive; feather every course end over end_feather metres
                badc = bad.reshape(ncol - 1, NR - 1)[:, 2:5].any(1)
                dead = np.concatenate([badc, badc[-1:]])
                if dead.any() and not dead.all():
                    di = np.flatnonzero(dead)
                    dd = np.abs(A[:, None] - A[di][None]).min(1)
                    t_ = np.clip(dd / end_feather, 0, 1)
                    fe = t_ * t_ * (3 - 2 * t_)
                    # the run's outer ends (contour ends) are not course ends
                    continue
                break
        q = q[~bad]
        if len(q):
            used = np.unique(q)
            remap = -np.ones(ncol * NR, np.int64)
            remap[used] = np.arange(len(used))
            acc.add(Wf[used], remap[q], "M_thatch", uv=np.stack([Am.ravel(), rows_m.ravel()], -1)[used])
            nq_tot += len(q)
        kd = KDTree(ncol)
        for i_, p_ in enumerate(plan(mb)):
            kd.insert((float(p_[0]), float(p_[1]), 0.0), i_)
        kd.balance()
        prev = (kd, rows_m, rows_h)
        prev_line = (A_ref, mi)
    return nC, nq_tot


def build_wing_roof(coll, seed=3, rng_seed=1313):
    rng = np.random.default_rng(rng_seed)
    thr = float(FR.min_relief(np.array([[FR.WX_W, FR.WY_S, 3.0]]))[0])
    ribs = 0.015 >= thr
    acc = Acc(FR.prefix + "_wing_roof_thatch")
    # --- continuous stepped courses round the rounded hips (built first: the core is trimmed under them)
    accc = Acc(FR.prefix + "_wing_roof_thatch_courses")
    n_c, n_q = thatch_courses(accc, rng, seed, relief_min=thr)
    log(f"  thatch: {n_c} courses, {n_q} quads")
    ob_c = finalize(accc, coll, smooth_deg=60.0, recalc=False)
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bvh_c = BVHTree.FromObject(ob_c, bpy.context.evaluated_depsgraph_get())
    # --- thatch core body (height field): kept only where it can be seen (verges, holes in the course cover,
    # the eave overhang underside); thinned toward the eaves so its edge is buried inside the eave roll
    xs = np.arange(FR.WX_W - FR.W_OVH, FR.WX_E + FR.W_OVH + 1e-6, 0.09)
    ys = np.linspace(FR.WY_S - FR.W_OVH, FR.WY_N + FR.W_OVH, 60)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zu = wing_under(X, Y)
    Zt = Zu + (FR.CORE_T + thatch_swell(X, Y) + hip_swell(X, Y)) / FR.CP_
    qe = eave_q(X, Y)
    Zt = Zt - 0.22 * np.clip(1 - qe / 0.6, 0, 1)
    zsk, ppk = skirt_z_at(X, Y)
    under = (ppk < FR.SKIRT.p_lip + 0.1) & (wing_top(X, Y) < zsk + 0.07)
    Zt = np.where(under, np.minimum(Zt, zsk - 0.24), Zt)
    Zu = np.minimum(Zu, Zt - 0.06)
    nx_, ny_ = X.shape
    idx = np.arange(nx_ * ny_).reshape(nx_, ny_)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    xm, ym = 0.5 * (X[:-1, :-1] + X[1:, 1:]), 0.5 * (Y[:-1, :-1] + Y[1:, 1:])
    ztm = 0.25 * (Zt[:-1, :-1] + Zt[1:, :-1] + Zt[1:, 1:] + Zt[:-1, 1:])
    keep = ~thatch_cull(np.stack([xm, ym, ztm], -1), tol_skirt=False)
    keep &= ~(tur_dist(xm, ym, ztm) < -0.05)
    keep &= eave_q(xm, ym) > -0.01
    # top: drop cells under the course cover (probe the 4 corners and the centre)
    covered = np.ones(xm.shape, bool)
    for fx, fy in ((0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)):
        px = X[:-1, :-1] + (X[1:, 1:] - X[:-1, :-1]) * fx
        py = Y[:-1, :-1] + (Y[1:, 1:] - Y[:-1, :-1]) * fy
        pz = Zt[:-1, :-1] * (1 - fx) * (1 - fy) + Zt[1:, :-1] * fx * (1 - fy) + Zt[:-1, 1:] * (1 - fx) * fy + \
            Zt[1:, 1:] * fx * fy
        hit = np.array([bvh_c.ray_cast(Vector((float(a_), float(b_), float(c_) - 0.01)), Vector((0, 0, 1.0)), 0.6)[0]
                        is not None for a_, b_, c_ in zip(px.ravel(), py.ravel(), pz.ravel())]).reshape(xm.shape)
        covered &= hit
    # keep the core skin wherever the courses thin out or end (hips, the turret flanks, the eave): a grazing view
    # there must meet thatch, never the back of the core
    covered &= (eave_q(xm, ym) > 0.3) & (tur_dist(xm, ym, ztm) > 1.1)
    inside = (xm > FR.WX_W + 0.05) & (xm < FR.WX_E - 0.05) & (ym > FR.WY_S + 0.05) & (ym < FR.WY_N - 0.05)
    Vt = np.stack([X, Y, Zt], -1).reshape(-1, 3)
    Vb = np.stack([X, Y, Zu], -1).reshape(-1, 3)
    acc.add(Vt, quads[(keep & ~covered).ravel()], "M_thatch")
    acc.add(Vb, quads[(keep & ~inside).ravel()][:, ::-1], "M_thatch")
    # close the core's cut edges (turret, hips, eave): a side wall on every boundary edge of the kept region, so a
    # grazing view past a course end or the roll end meets thatch, never the inside of the core
    nv_ = nx_ * ny_
    Vs_ = np.concatenate([Vt, Vb])
    side = []
    K = np.pad(keep, 1, constant_values=False)
    for di, dj, e0, e1 in ((1, 0, (1, 0), (1, 1)), (-1, 0, (0, 1), (0, 0)), (0, 1, (1, 1), (0, 1)),
                           (0, -1, (0, 0), (1, 0))):
        nb = K[1 + di:K.shape[0] - 1 + di, 1 + dj:K.shape[1] - 1 + dj]
        ii, jj = np.nonzero(keep & ~nb)
        a_ = idx[ii + e0[0], jj + e0[1]]
        b_ = idx[ii + e1[0], jj + e1[1]]
        side.append(np.stack([a_, b_, b_ + nv_, a_ + nv_], 1))
    side = np.concatenate(side)
    acc.add(Vs_, side, "M_thatch")
    log(f"  thatch core: top cells {int((keep & ~covered).sum())}/{int(keep.sum())}, "
        f"underside {int((keep & ~inside).sum())}")
    # east verge closing strip (under the hall skirt)
    yv = ys
    xe = np.full_like(yv, xs[-1])
    V = np.concatenate([np.stack([xe, yv, Zu[-1]], 1), np.stack([xe, yv, Zt[-1]], 1)])
    n = len(yv)
    q = np.array([(i, i + 1, n + i + 1, n + i) for i in range(n - 1)])
    cv = np.stack([xe, yv, Zu[-1] + 0.1], 1)
    acc.add(V, q[~thatch_cull(cv[:-1], tol_skirt=False)], "M_thatch")
    # --- eave roll: one continuous D-section roll N -> W -> S round the hipped corners
    path = eave_path()
    # cut where the whole section is buried in the turret stone (W eave) or inside the hall walls (E ends)
    T = np.gradient(path, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Rv = np.cross(np.array([0, 0, 1.0]), T)
    probes = [(-0.135, 0.22), (-0.06, 0.43), (0.0, 0.52), (0.43, 0.44), (0.07, 0.0), (0.25, 0.81)]
    inside_all = np.ones(len(path), bool)
    hall_all = np.ones(len(path), bool)
    for qq, vv in probes:
        Pp = path + Rv * qq + np.array([0, 0, vv])
        inside_all &= tur_dist(Pp[:, 0], Pp[:, 1], Pp[:, 2]) < -0.03
        hall_all &= oct_pp(Pp[:, 0], Pp[:, 1]) < apo(Pp[:, 2]) - 0.05
    # the N eave passes outside the hall's N face: it ends under the skirt with a rounded, tucked-up taper
    ok = ~hall_all & ~inside_all
    FR.EAVE_RUNS = []
    for r_ in runs_of(path, ok, min_len=4):
        # round 6: a run end that dies into the turret tapers (rounded, 0.45 m) instead of stopping as a cut section
        r_a = np.asarray(r_, float)
        near_t = tur_dist(r_a[[0, -1], 0], r_a[[0, -1], 1], r_a[[0, -1], 2] + 0.3) < 0.6
        tp = (0.45 if near_t[0] else 0.0, 0.45 if near_t[1] else 0.0)
        FR.EAVE_RUNS.append(d_roll(acc, r_, ROLL_P, ROLL_VIS, 5 + len(r_), rng, var=0.03, taper=tp, tmin=(0.3, 0.3),
                                drop_hidden=True, sp=(0.022, 0.05), ribs=ribs,
                                keep_back_fn=lambda P_: tur_dist(P_[:, 0], P_[:, 1], P_[:, 2]) < 1.3))
    nt = 0
    for P in FR.EAVE_RUNS:
        if P is not None:
            nt += tuft_fringe(acc, P, np.random.default_rng(4040 + len(P)))
    log(f"  eave fringe tufts {nt}")
    finalize(acc, coll, smooth_deg=70.0)


def tuft_fringe(acc, P, rng, q_rng=(-0.07, 0.0), L_rng=(0.02, 0.06), sp=(0.004, 0.009), mat="M_thatch"):
    """Kit component: irregular hanging straw fringe along the lower edge of an eave roll swept along path P
    (section ROLL_P): tapered tufts 2-6 cm long (lengths clumped, not a regular zigzag), 1-3 cm wide, staggered
    in depth, splayed outward, with gaps; the tuft roots are buried 1.5 cm in the roll."""
    P = np.asarray(P, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    if d[-1] < 0.3:
        return 0
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Rv = np.cross(np.array([0, 0, 1.0]), T)
    Rv /= np.linalg.norm(Rv, axis=1, keepdims=True) + 1e-9
    low = ROLL_P[ROLL_P[:, 1] < 0.2]
    o = np.argsort(low[:, 0])
    s_ = rng.uniform(0, 0.02)
    recs = []
    clump = smooth_wave(np.array([0.0]), rng)  # advance rng deterministically
    Lw = smooth_wave(d, rng, (0.15, 0.6), 3)
    while s_ < d[-1] - 0.02:
        if rng.uniform() < 0.08:                    # small gaps in the fringe
            s_ += rng.uniform(0.02, 0.06)
            continue
        i = int(np.searchsorted(d, s_))
        i = min(max(i, 0), len(P) - 1)
        q = rng.uniform(*q_rng)
        v = float(np.interp(q, low[o, 0], low[o, 1]))
        lf = float(np.interp(s_, d, Lw))
        L = np.clip(0.5 * (L_rng[0] + L_rng[1]) + 0.5 * (L_rng[1] - L_rng[0]) * (0.6 * lf + 0.4 * rng.uniform(-1, 1)),
                    L_rng[0], L_rng[1])
        recs.append((s_, i, q, v, L, rng.uniform(0.006, 0.013), rng.uniform(0.003, 0.006), rng.uniform(0.0, 0.12),
                     rng.normal(0, 0.25)))
        s_ += rng.uniform(*sp)
    V, F = [], []
    nb = 0
    for (s_, i, q, v, L, w, t, splay, twist) in recs:
        base = np.interp(s_, d, P[:, 0]), np.interp(s_, d, P[:, 1]), np.interp(s_, d, P[:, 2])
        base = np.array(base) + Rv[i] * q + np.array([0, 0, v + 0.015])
        if tur_dist(base[0], base[1], base[2]) < 0.03 or oct_pp(base[0], base[1]) < apo(base[2]) + 0.05:
            continue
        dn = np.array([0, 0, -1.0]) - Rv[i] * splay
        dn /= np.linalg.norm(dn)
        ax = T[i] * math.cos(twist) + Rv[i] * math.sin(twist) * 0.3
        ax -= dn * (ax @ dn)
        ax /= np.linalg.norm(ax)
        bx = np.cross(dn, ax)
        rings = []
        for f_, sc in ((0.0, 1.0), (1.0, rng.uniform(0.1, 0.25))):
            c = base + dn * (L + 0.015) * f_ + bx * 0.004 * f_ * f_
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                rings.append(c + ax * sx * w * 0.5 * sc + bx * sy * t * 0.5 * sc)
        V.append(np.array(rings))
        q4 = []
        for j in range(4):
            a_, b_ = j, (j + 1) % 4
            q4.append((a_ + nb, b_ + nb, b_ + 4 + nb, a_ + 4 + nb))
        q4.append((4 + nb, 5 + nb, 6 + nb, 7 + nb))
        F.append(np.array(q4))
        nb += 8
    if V:
        acc.add(np.concatenate(V), [np.concatenate(F)], mat)
    return len(V)


def ridge_dome_top(lat):
    """height of the ridge dome's upper surface above the ridge apex at lateral offset lat."""
    P = RIDGE_DOME[:-1]
    return np.interp(lat, P[:, 0], P[:, 1])


def comb_shake(acc, i):
    """riven ridge-comb shake variant i (local: x across, y along the shake from the butt, z thickness)."""
    rr = np.random.default_rng(7100 + i)
    L = float(COMB_LEN[i])
    wd = rr.uniform(*SIZE_TABLE["comb_shake"]["width"])
    th = rr.uniform(*SIZE_TABLE["comb_shake"]["thick"])      # wedge-thick riven shakes (3-5 cm at the butt)
    r_ = 0.006
    X = axn(np.array([-wd / 2]), np.array([wd / 2]), np.array([r_]), 6)
    Y = axn(np.array([0.0]), np.array([L]), np.array([r_]), 8)
    Z = ax4(np.array([th / 2]), np.array([r_]))
    P, qd = rbox_v(X, Y, Z, np.array([r_]))
    P = P[0]
    x_, u, h = P[:, 0], P[:, 1], P[:, 2]
    xn = x_ / (wd / 2)
    tip = np.clip((u - (L - 0.08)) / 0.08, 0, 1)
    kind = i % 3
    cang = math.radians(rr.uniform(20, 40)) * rr.choice([-1, 1])
    if kind == 1:
        u = u - math.tan(abs(cang)) * (0.5 + 0.5 * math.copysign(1, cang) * xn) * wd * tip * 0.6
    elif kind == 2:
        u = u - np.where(np.abs(xn) < 0.3, rr.uniform(0.02, 0.045) * tip, 0.0)
    u = u - 0.008 * tip * np.abs(np.sin(xn * 4.0 + L * 37.0))
    k_ = 1.0 if FR.units == "phase1" else 0.0          # 2-4 mm riving wobble: producer note 11 (materials)
    h = h * (1 - 0.3 * u / L) + k_ * 0.002 * np.cos(xn * np.pi * 1.5 + L * 11) * (h > 0)
    x_ = x_ * (1 - 0.12 * u / L) + k_ * 0.004 * np.sin(u * 9 + i)
    acc.add(np.stack([x_, u, h], 1), qd, "M_roof_shake", uv=np.stack([x_, u], 1))


def build_wing_ridge(coll, seed=1414):
    rng = np.random.default_rng(seed)
    thr = float(FR.min_relief(np.array([[FR.WX_W, FR.WY_R, 5.0]]))[0])
    acc = Acc(FR.prefix + "_wing_ridge_comb")
    acct = Acc(FR.prefix + "_wing_roof_rolls")
    x_apex = FR.WX_W + (FR.WY_R - FR.WY_S)
    z_apex = FR.W_RAFT + (FR.WY_R - FR.WY_S) * FR.W_TAN + (FR.TH_BASE + 0.045) / FR.CP_
    xs = np.arange(x_apex - 0.6, FR.WX_E - 0.2, 0.03)
    path = np.stack([xs, np.full_like(xs, FR.WY_R), np.full_like(xs, z_apex)], 1)
    path[:, 2] += 0.03 * n1(xs * 0.5, 31) - 0.03 * np.sin(np.pi * np.clip((xs - x_apex) / (FR.WX_E - x_apex), 0, 1))
    path[:, 2] += thatch_swell(path[:, 0], path[:, 1]) / FR.CP_          # rides the swelling thatch mass
    ok = ~thatch_cull(path + np.array([0, 0, -0.3]), tol_skirt=False)
    # west end: the dome dies into the turret body / under the drooping cushion (whole section inside)
    ok &= turret_outer(path[:, 0], path[:, 1] - 0.0, path[:, 2] - 0.2) > -0.25
    best, cur = (0, 0), 0
    for i, o_ in enumerate(list(ok) + [False]):
        if o_:
            cur += 1
        else:
            if cur > best[1] - best[0]:
                best = (i - cur, i)
            cur = 0
    path = path[best[0]:best[1]]
    FR.RIDGE_PATH = path
    d_roll(acct, path, RIDGE_DOME, RIDGE_VIS, 71, rng, var=0.02, sp=(0.012, 0.04), dep=(0.003, 0.012), drop_hidden=True,
           ribs=0.012 >= thr)
    # ridge-rider log, seated 3 cm into the dome; starts clear of the cushion
    lp = path + np.array([0, 0, 0.115 + 0.07 - 0.03])
    okl = turret_outer(lp[:, 0], lp[:, 1], lp[:, 2]) > -0.08
    lp = lp[np.argmax(okl):]
    LOG_R = 0.07
    V, F = sweep(lp, (0, 0, 1), prof_circle(LOG_R, 12))
    acc.add(V, F, "M_timber_weathered")
    # comb: short, stubby, dense crossed split shakes (V/X pairs) pinned by the log (ref1: a crest 0.15-0.30 m
    # tall); the shakes are a pool of 10 riven variants placed as linked duplicates, butts buried in the dome
    get_pool("comb", comb_shake, len(COMB_LEN))
    x = lp[0, 0] + rng.uniform(0.08, 0.14)
    x_end = lp[-1, 0] - 0.06
    ncomb = 0
    while x < x_end:
        psi = math.radians(rng.choice([-1, 1]) * rng.uniform(10, 36))
        hdir = np.array([math.sin(psi), math.cos(psi), 0.0])
        zl = float(np.interp(x, lp[:, 0], lp[:, 2]))
        zc = zl + LOG_R + 0.03
        u = rng.uniform()
        sides = (-1, 1) if u > 0.12 else ((rng.choice([-1, 1]),))
        for side in sides:
            lean = math.radians(rng.uniform(18, 34))
            D = side * math.sin(lean) * hdir + math.cos(lean) * np.array([0, 0, 1.0])
            D += np.array([rng.normal(0, 0.06), 0, 0])
            D /= np.linalg.norm(D)
            Lup = rng.uniform(0.07, 0.20) if rng.uniform() < 0.8 else rng.uniform(0.18, 0.25)
            cross = np.array([x + rng.normal(0, 0.012), FR.WY_R + rng.normal(0, 0.01), zc + rng.normal(0, 0.01)])
            # pick the shortest variant that still buries its butt >= 4.5 cm in the dome (or in the rider log)
            Ldn = 0.06
            while Ldn < 0.32:
                pb = cross - D * Ldn
                lat = pb[1] - FR.WY_R
                zd = float(np.interp(pb[0], path[:, 0], path[:, 2])) + float(ridge_dome_top(lat)) - 0.015
                if pb[2] < zd - 0.045 or math.hypot(lat, pb[2] - zl) < LOG_R - 0.025:
                    break
                Ldn += 0.01
            need = Lup + Ldn
            vi = int(np.argmin(np.where(COMB_LEN >= need, COMB_LEN, 9.0)))
            if COMB_LEN[vi] < need:
                vi = int(np.argmax(COMB_LEN))
            base = cross + D * Lup - D * COMB_LEN[vi]
            E = np.cross(D, np.array([0, 0, 1.0]))
            E = E / np.linalg.norm(E) if np.linalg.norm(E) > 1e-3 else np.array([1.0, 0, 0])
            roll = rng.normal(0, 0.25)
            Nn = np.cross(E, D)
            E2 = E * math.cos(roll) + Nn * math.sin(roll)
            place("comb", vi, frame_matrix(base, E2, D, np.cross(E2, D)), "ridge_comb_shake")
            ncomb += 1
        # V tufts clustered in groups of 2-3 with gaps between the clusters
        x += rng.uniform(0.05, 0.09) if rng.uniform() < 0.62 else rng.uniform(0.16, 0.26)
    log("  ridge comb shakes", ncomb)
    for xx in np.arange(lp[0, 0] + 0.3, lp[-1, 0], 0.9):
        zz = np.interp(xx, lp[:, 0], lp[:, 2])
        peg(FR, np.array([xx, FR.WY_R, zz + LOG_R]), np.array([0, 0, 1.0]), rad=0.016, proud=0.03)
    # (round 4) the west hips are no longer separate roll tubes: the thatch courses themselves swell round the
    # hips (see thatch_courses), dying into the turret on the fillet
    FR.HIP_ENDS = []
    finalize(acc, coll)
    finalize(acct, coll, smooth_deg=70.0)


def _wall_frame(r_, nr_):
    """tangent T, up-the-wall U (perpendicular to T in the wall plane) for a polyline on a wall with normals nr_."""
    T_ = np.gradient(r_, axis=0)
    T_ /= np.linalg.norm(T_, axis=1, keepdims=True) + 1e-12
    zz_ = np.array([0, 0, 1.0])
    U_ = zz_[None, :] - (T_ @ zz_)[:, None] * T_ - (nr_ @ zz_)[:, None] * nr_
    un_ = np.linalg.norm(U_, axis=1)
    U_ /= un_[:, None] + 1e-9
    good = un_ > 0.2
    if good.any():
        gi = np.flatnonzero(good)
        for i_ in np.flatnonzero(~good):
            U_[i_] = U_[gi[np.argmin(np.abs(gi - i_))]]
    for _ in range(3):
        U_[1:-1] = U_[:-2] + 2 * U_[1:-1] + U_[2:]
        U_ -= (U_ * T_).sum(1, keepdims=True) * T_
        U_ -= (U_ * nr_).sum(1, keepdims=True) * nr_
        U_ /= np.linalg.norm(U_, axis=1, keepdims=True) + 1e-9
    return T_, U_


def _resample(pts, out_n, step):
    r_ = np.asarray(pts, float)
    dd_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(r_, axis=0), axis=1))])
    ss_ = np.linspace(0, dd_[-1], max(int(dd_[-1] / step) + 1, 2))
    r_ = np.stack([np.interp(ss_, dd_, r_[:, i]) for i in range(3)], 1)
    nr_ = np.stack([np.interp(ss_, dd_, np.asarray(out_n, float)[:, i]) for i in range(3)], 1)
    nr_[:, 2] = 0.0
    nr_ /= np.linalg.norm(nr_, axis=1, keepdims=True) + 1e-9
    return ss_, r_, nr_


def _sweep_wall(acc, r_, U_, nr_, profs, mat):
    n_, npf = profs.shape[:2]
    V = r_[:, None, :] + profs[..., 0:1] * U_[:, None, :] + profs[..., 1:2] * nr_[:, None, :]
    ii = np.arange(n_ - 1)[:, None]
    jj = np.arange(npf)[None, :]
    a_ = ii * npf + jj
    b_ = ii * npf + (jj + 1) % npf
    quads = np.stack([a_, b_, b_ + npf, a_ + npf], -1).reshape(-1, 4)
    caps = [np.arange(npf)[::-1][None, :], ((n_ - 1) * npf + np.arange(npf))[None, :]]
    acc.add(V.reshape(-1, 3), [quads] + caps, mat)


def mortar_fillet(acc, pts, out_n, seed, h_up=0.052, out=0.055, taper=(0.3, 0.3), smooth=True):
    """Kit component: lime-mortar flaunching where a thatch / shingle surface meets masonry (round 5 section):
    a hard top crease feathered 4 mm proud into the stone, one planar ~43 deg face standing <= 5.5 cm proud, the
    toe tucked 3 cm down under the course butts, and the back buried in the wall. The line wanders only at low
    frequency (+-1.5 cm, wavelength >= 1.3 m). Both ends taper to nothing over taper metres (no square cut ends).
    Built with split normals at the crease and the toe (finalize the receiving object with a low smoothing angle)."""
    ss_, r_, nr_ = _resample(pts, out_n, 0.04)
    if ss_[-1] < 0.05 or len(r_) < 2:
        return
    if smooth:
        for _ in range(4):
            r_[1:-1] = 0.25 * r_[:-2] + 0.5 * r_[1:-1] + 0.25 * r_[2:]
    r_[:, 2] += 0.015 * n1(ss_ / 1.3, seed)
    T_, U_ = _wall_frame(r_, nr_)
    L = ss_[-1]
    tf = np.ones(len(ss_))
    if taper[0] > 0:
        tf = np.minimum(tf, np.clip(ss_ / taper[0], 0, 1))
    if taper[1] > 0:
        tf = np.minimum(tf, np.clip((L - ss_) / taper[1], 0, 1))
    tf = np.sqrt(tf * (2 - tf))
    sc_h = (1 + 0.10 * n1(ss_ / 1.6, seed + 1)) * (0.15 + 0.85 * tf)
    sc_o = (1 + 0.10 * n1(ss_ / 1.9, seed + 2)) * (0.1 + 0.9 * tf)
    prof = np.zeros((len(ss_), 6, 2))
    h = h_up * sc_h
    o = out * sc_o
    prof[:, 0] = np.stack([h + 0.012, np.full_like(h, -0.012)], 1)          # buried in the bed joint above
    prof[:, 1] = np.stack([h, np.full_like(h, 0.004)], 1)                   # hard top crease, 4 mm proud
    prof[:, 2] = np.stack([np.zeros_like(h), o], 1)                         # toe on the thatch (planar face)
    prof[:, 3] = np.stack([np.full_like(h, -0.03), o + 0.006], 1)           # toe tucked 3 cm under the butts
    prof[:, 4] = np.stack([np.full_like(h, -0.05), 0.35 * o], 1)
    prof[:, 5] = np.stack([np.full_like(h, -0.05), np.full_like(h, -0.012)], 1)
    _sweep_wall(acc, r_, U_, nr_, prof, "M_mortar")


def stepped_flashing(acc, pts, out_n, seed, step_h=0.16, w=(0.035, 0.20), turn=0.08):
    """Kit component: stepped lead flashing where a roof edge runs steeply (> 50 deg) down a masonry face: the
    lead lies on the stone with its upper edge in level steps (each step tucked into a bed joint every step_h),
    and turns out 'turn' metres over the thatch below; 2 mm proud, 3 mm thick."""
    ss_, r_, nr_ = _resample(pts, out_n, 0.02)
    if ss_[-1] < 0.1 or len(r_) < 3:
        return
    T_, U_ = _wall_frame(r_, nr_)
    z0 = r_[:, 2].min() + 0.03 * n1(np.array([seed * 1.0]), seed)[0]
    ztop = z0 + step_h * np.ceil((r_[:, 2] + 0.05 - z0) / step_h)
    uz = np.maximum(U_[:, 2], 0.25)
    wd = np.clip((ztop - r_[:, 2]) / uz, w[0], w[1])
    prof = np.zeros((len(ss_), 6, 2))
    prof[:, 0] = np.stack([wd + 0.012, np.full_like(wd, -0.010)], 1)
    prof[:, 1] = np.stack([wd, np.full_like(wd, 0.004)], 1)
    prof[:, 2] = np.stack([np.full_like(wd, 0.0), np.full_like(wd, 0.006)], 1)
    prof[:, 3] = np.stack([np.full_like(wd, -0.02), np.full_like(wd, turn)], 1)
    prof[:, 4] = np.stack([np.full_like(wd, -0.03), np.full_like(wd, turn - 0.004)], 1)
    prof[:, 5] = np.stack([np.full_like(wd, -0.012), np.full_like(wd, -0.006)], 1)
    _sweep_wall(acc, r_, U_, nr_, prof, "M_lead")


def flaunch_loop(acc, pts, center, seed, steep_deg=50.0):
    """split a (closed or open) thatch/stone intersection into one continuous run: mortar fillet where the line is
    flatter than steep_deg, stepped lead flashing where steeper; the two overlap by a few cm at every change."""
    P = np.asarray(pts, float)
    if len(P) < 4:
        return
    dxy = np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1)
    dz = np.abs(np.diff(P[:, 2]))
    ang = np.degrees(np.arctan2(dz, dxy + 1e-9))
    # 3-sample running mean with hysteresis-free majority
    ang = np.convolve(np.concatenate([ang[:1], ang, ang[-1:]]), np.ones(3) / 3, "valid")
    st = np.concatenate([ang > steep_deg, [ang[-1] > steep_deg]])
    nrm = np.column_stack([P[:, 0] - center[0], P[:, 1] - center[1], np.zeros(len(P))])
    i0 = 0
    for i in range(1, len(P) + 1):
        if i == len(P) or st[i] != st[i0]:
            a_, b_ = max(i0 - 1, 0), min(i + 1, len(P))
            seg = P[a_:b_]
            if len(seg) >= 2:
                first, last = i0 == 0, i == len(P)
                if st[i0]:
                    stepped_flashing(acc, seg, nrm[a_:b_], seed + i0)
                else:
                    mortar_fillet(acc, seg, nrm[a_:b_], seed + i0, taper=(0.3 if first else 0.0,
                                                                           0.3 if last else 0.0), smooth=False)
            i0 = i


def build_wing_structure(coll, seed=1515):
    """wall plates, rafter poles and battens visible in the eave gap; thatch/stone fillets."""
    rng = np.random.default_rng(seed)
    PLANES = planes()
    thr = float(FR.min_relief(np.array([[FR.WX_W, FR.WY_S, 2.4]]))[0])
    acc = Acc(FR.prefix + "_wing_roof_structure")
    accf = Acc(FR.prefix + "_wing_flashing")
    accm = Acc(FR.prefix + "_wing_fillet")
    # (round 4) wall plates and battens are buried in the thatch: only the rafter-pole ends that show in the eave
    # gap behind the roll are modelled
    # rafter poles every ~0.6 m with battens across; the pole feet sit on the wall plate and project 2-5 cm past
    # its face into the eave gap behind the roll: chamfered / axe-cut ends, some checked
    prng = np.random.default_rng(seed + 2)
    for name in ("S", "N"):
        pl = PLANES[name]
        m_wall = FR.W_OVH / FR.CP_
        for xr in np.arange(FR.WX_W + 0.35, FR.WX_E + 0.3, 0.62):
            xr2 = xr + rng.normal(0, 0.03)
            proj = prng.uniform(0.02, 0.05)
            m0 = m_wall - (proj + 0.01) / FR.CP_
            ms = np.array([m0, m0 + 0.012, m0 + 0.03, m0 + 0.06, m0 + 0.1, m0 + 0.2, m0 + 0.32])
            path = pl["o"](np.full_like(ms, xr2), ms) - pl["n"] * 0.12
            path[:, 2] -= 0.004 * np.sin(np.linspace(0, 3, len(ms)))
            if thatch_cull(path.mean(0)[None], tol_skirt=False)[0]:
                continue
            if tur_dist(path[:, 0], path[:, 1], path[:, 2]).min() < 0.15:
                continue
            zs_, pp_ = skirt_z_at(path[:, 0], path[:, 1])
            if (pp_ < FR.SKIRT.p_lip + 0.4).any():
                continue
            rr0 = 0.058 + prng.uniform(-0.007, 0.007)
            npf = 12
            ang = np.linspace(0, 2 * np.pi, npf, endpoint=False)
            kch = int(prng.integers(0, npf)) if prng.uniform() < 0.6 else -1
            chd = prng.uniform(0.012, 0.02)
            if chd < thr:
                kch = -1                    # producer note 11: the 1.2-2 cm end check is a decal / material job
            dcut = (ms - m0) * FR.CP_
            profs = []
            for i_, d_ in enumerate(dcut):
                rad = rr0 * (0.78 if i_ == 0 else (0.94 if i_ == 1 else 1.0))
                pr = np.stack([rad * np.cos(ang), rad * np.sin(ang)], 1) * (1 + 0.04 * np.sin(ang * 2 + xr))[:, None]
                if kch >= 0 and d_ < 0.09:
                    f_ = (1 - d_ / 0.09)
                    pr[kch] *= 1 - chd / rad * f_
                    pr[(kch + 6) % npf] *= 1 - 0.5 * chd / rad * f_ * (prng.uniform() < 0.5)
                profs.append(pr)
            V, F = sweep(path, pl["n"], np.stack(profs))
            # axe-cut end: the end ring is skewed +-12 deg
            tilt = math.tan(math.radians(prng.uniform(-12, 12)))
            ax_ = path[1] - path[0]
            ax_ /= np.linalg.norm(ax_)
            V[:npf] += ax_ * (tilt * (V[:npf] - path[0]) @ np.cross(ax_, pl["n"]))[:, None]
            acc.add(V, F, "M_timber_weathered")
    finalize(acc, coll)
    # lime-mortar fillet where the thatch meets the turret stone (S, W and N): a triangular flaunching, 6-10 cm up
    # the stone with a flat ~42 deg face, wandering only at low frequency; the course butts run straight into it
    frng = np.random.default_rng(seed + 1)
    ell = np.stack([np.cos(np.linspace(0, 2 * np.pi, 12, endpoint=False)),
                    np.sin(np.linspace(0, 2 * np.pi, 12, endpoint=False))], 1)

    def mortar_tube(pts, ups, rx, ry, seed):
        pts = np.asarray(pts, float)
        if len(pts) < 3:
            return
        prof = ell * np.array([rx, ry])
        d_roll(accf, pts, prof, np.ones(len(prof)), seed, frng, up=ups, var=0.007, sp=(0.06, 0.12),
               dep=(0.0, 0.0015), taper=(0.04, 0.04), mat="M_mortar", z_wave=0.0)
    # find the real outer thatch surface next to the stone by ray-casting down onto the built thatch meshes
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(bpy.data.objects[nm], dg) for nm in
             (FR.name("wing_roof_thatch_courses"), FR.name("wing_roof_thatch"), FR.name("wing_roof_rolls")) if nm in bpy.data.objects]
    pts = []
    for th in np.linspace(0, 2 * np.pi, 720, endpoint=False):
        best = None
        for zz in np.arange(6.4, 2.3, -0.04):
            r = float(tur_reff(th, zz)) + 0.035
            x, y = FR.TUR_C[0] + r * math.cos(th), FR.TUR_C[1] + r * math.sin(th)
            zh = None
            for tr in trees:
                hit = tr.ray_cast(Vector((x, y, zz + 0.04)), Vector((0, 0, -1.0)), 0.08)
                if hit[0] is not None and (zh is None or hit[0].z > zh):
                    zh = hit[0].z
            if zh is not None:
                best = (x, y, zh)
                break
        if best is None:
            pts.append(None)
            continue
        x, y, zh = best
        zsk, ppk = skirt_z_at(np.array([x]), np.array([y]))
        if x > FR.WX_E - 0.3 or float(ppk[0]) < FR.SKIRT.p_lip + 0.1:
            pts.append(None)
            continue
        r = float(tur_reff(th, zh))
        pts.append(np.array([FR.TUR_C[0] + r * math.cos(th), FR.TUR_C[1] + r * math.sin(th), zh + 0.01]))
    # heavy smoothing round the loop (wavelength >= 1 m), bounded to +-2.5 cm of the real thatch surface
    n_all = len(pts)
    zraw = np.array([p_[2] if p_ is not None else np.nan for p_ in pts])
    zs2 = zraw.copy()
    for i_ in range(n_all):
        if pts[i_] is None:
            continue
        ww, vv = 0.0, 0.0
        for k_ in range(-45, 46, 3):
            z_ = zraw[(i_ + k_) % n_all]
            if not np.isnan(z_):
                g_ = math.exp(-(k_ / 22.0) ** 2)
                ww += g_
                vv += g_ * z_
        zs2[i_] = float(np.clip(vv / ww, zraw[i_] - 0.025, zraw[i_] + 0.02))
    for i_ in range(n_all):
        if pts[i_] is not None:
            pts[i_] = pts[i_].copy()
            pts[i_][2] = zs2[i_]
    # one continuous run along the true intersection: mortar flaunching where it is flatter than 50 deg, stepped
    # lead where steeper; the open ends (where the thatch leaves the stone) taper to nothing
    first_none = next((i for i, p_ in enumerate(pts) if p_ is None), 0)
    pts = pts[first_none:] + pts[:first_none]
    for r_ in runs_of_list(pts, 4):
        flaunch_loop(accm, r_, FR.TUR_C, 400 + len(r_))
    # fillet where thatch meets the hall wall (W facet / N facet)
    pts = []
    for t in np.linspace(0.05, 1.0 - 0.07, 220):
        s = t * hall_L(3.0)
        lo, hi = 2.0, FR.WALL_H
        P = hall_map(np.array([s]), np.array([hi]), np.array([0.0]), np.array([3.0]))[0]
        if not ((P[0] < FR.WX_E + 0.3) and (P[1] > FR.WY_S - 0.6) and (P[1] < FR.WY_N + 0.6)):
            continue
        def g(z):
            Q = hall_map(np.array([s]), np.array([z]), np.array([0.0]), np.array([3.0]))[0]
            return z - float(wing_top(Q[0], Q[1])), Q
        if g(lo)[0] > 0 or g(hi)[0] < 0:
            continue
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if g(mid)[0] > 0:
                hi = mid
            else:
                lo = mid
        pts.append(g(lo)[1])
    if len(pts) > 3:
        pts = np.array(pts)
        nrm_ = np.column_stack([pts[:, 0], pts[:, 1], np.zeros(len(pts))])
        kk_ = np.round(np.arctan2(pts[:, 1], pts[:, 0]) / (np.pi / 4)) % 8
        nrm_ = np.column_stack([np.cos(kk_ * np.pi / 4), np.sin(kk_ * np.pi / 4), np.zeros(len(pts))])
        mortar_fillet(accm, pts - np.array([0, 0, 0.01]), nrm_, 53)
    # lead valley apron where the hall skirt roof and the wing thatch meet: a 0.32 m lead sheet dressed over the
    # real course steps (ray-cast onto the built thatch) and tucked under the skirt boards
    def thatch_z(x, y, z0):
        best = None
        for tr in trees:
            hit = tr.ray_cast(Vector((float(x), float(y), float(z0))), Vector((0, 0, -1.0)), 1.5)
            if hit[0] is not None and (best is None or hit[0].z > best):
                best = hit[0].z
        return best
    for k in range(1, 8):
        # d(x, p) = skirt sheathing top - thatch reference on a grid over the facet; the apron follows d = 0
        xg = np.linspace(-FR.SKIRT.p_lip * TAN22, FR.SKIRT.p_lip * TAN22, 140)
        pg = np.linspace(FR.SKIRT.p_lip + 0.02, 3.4, 110)
        XG, PG = np.meshgrid(xg, pg, indexing="ij")
        Sg = FR.SKIRT.surf(np.full(XG.shape, k), XG, PG)
        xx, yy = Sg[..., 0], Sg[..., 1]
        inside = (xx > FR.WX_W - FR.W_OVH + 0.05) & (xx < FR.WX_E + FR.W_OVH) & (yy > FR.WY_S - FR.W_OVH + 0.05) & \
            (yy < FR.WY_N + FR.W_OVH - 0.05) & (np.abs(XG) < PG * TAN22 - 0.02)
        dG = Sg[..., 2] + FR.SKIRT_SHEATH - (thatch_low(xx, yy) + 0.03)
        dG = np.where(inside, dG, np.nan)
        pts_ = []
        for i_ in range(len(xg)):
            for j_ in range(len(pg)):
                for di, dj in ((1, 0), (0, 1)):
                    if i_ + di >= len(xg) or j_ + dj >= len(pg):
                        continue
                    a_, b_ = dG[i_, j_], dG[i_ + di, j_ + dj]
                    if np.isnan(a_) or np.isnan(b_) or (a_ > 0) == (b_ > 0):
                        continue
                    f_ = a_ / (a_ - b_)
                    pts_.append((xg[i_] + di * f_ * (xg[1] - xg[0]), pg[j_] + dj * f_ * (pg[1] - pg[0])))
        if len(pts_) < 6:
            continue
        pts_ = np.array(pts_)
        # chain the crossing points by nearest-neighbour walking, splitting at jumps
        used = np.zeros(len(pts_), bool)
        chains = []
        while not used.all():
            i_ = int(np.flatnonzero(~used)[np.argmin(pts_[~used, 1])])
            ch = [i_]
            used[i_] = True
            while True:
                dd = np.hypot(pts_[:, 0] - pts_[ch[-1], 0], pts_[:, 1] - pts_[ch[-1], 1])
                dd[used] = 1e9
                j_ = int(np.argmin(dd))
                if dd[j_] > 0.12:
                    break
                ch.append(j_)
                used[j_] = True
            if len(ch) >= 6:
                chains.append(pts_[ch])
        for C in chains:
            # resample evenly and smooth
            dl = np.concatenate([[0], np.cumsum(np.hypot(np.diff(C[:, 0]), np.diff(C[:, 1])))])
            ss = np.arange(0, dl[-1], 0.05)
            if len(ss) < 4:
                continue
            C = np.stack([np.interp(ss, dl, C[:, 0]), np.interp(ss, dl, C[:, 1])], 1)
            for _ in range(4):
                C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
            # cross direction: toward the skirt-on-top side (d > 0)
            Tn = np.gradient(C, axis=0)
            Tn /= np.linalg.norm(Tn, axis=1, keepdims=True) + 1e-9
            Nn = np.stack([-Tn[:, 1], Tn[:, 0]], 1)
            probe = C + Nn * 0.1
            Sp_ = FR.SKIRT.surf(np.full(len(C), k), probe[:, 0], probe[:, 1])
            dp_ = Sp_[:, 2] + FR.SKIRT_SHEATH - (thatch_low(Sp_[:, 0], Sp_[:, 1]) + 0.03)
            Nn = Nn * np.where(np.median(dp_) > 0, 1.0, -1.0)
            offs = np.array([0.17, 0.09, 0.02, -0.06, -0.15])
            n_ = len(C)
            G = np.zeros((n_, len(offs), 3))
            for i_ in range(n_):
                for j_, o_ in enumerate(offs):
                    q_ = C[i_] + Nn[i_] * o_
                    S3 = FR.SKIRT.surf(np.array([k]), np.array([q_[0]]), np.array([q_[1]]))[0]
                    zt_ = thatch_z(S3[0], S3[1], S3[2] + 0.6)
                    if zt_ is None:
                        zt_ = S3[2] - 0.05
                    z_ = zt_ + 0.012
                    if o_ > 0:
                        z_ = min(z_, S3[2] - 0.012)
                    G[i_, j_] = (S3[0], S3[1], z_)
            G[1:-1] = 0.25 * G[:-2] + 0.5 * G[1:-1] + 0.25 * G[2:]
            Gb = G - np.array([0, 0, 0.009])
            nc_ = len(offs)
            V = np.concatenate([G.reshape(-1, 3), Gb.reshape(-1, 3)])
            off_b = n_ * nc_
            F = []
            for i_ in range(n_ - 1):
                for j_ in range(nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, a_ + 1, a_ + nc_ + 1, a_ + nc_))
                    F.append((off_b + a_, off_b + a_ + nc_, off_b + a_ + nc_ + 1, off_b + a_ + 1))
                for j_ in (0, nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, a_ + nc_, off_b + a_ + nc_, off_b + a_))
            for i_ in (0, n_ - 1):
                for j_ in range(nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, off_b + a_, off_b + a_ + 1, a_ + 1))
            accf.add(V, np.array(F), "M_lead")
            log(f"  valley apron facet {k}: {n_} stations")
    # lead flashing where the wing thatch dies into the shake collar (collar surface line butt -> top)
    P_ = []
    for th in np.linspace(0, 2 * np.pi, 720, endpoint=False):
        kf = int(np.round(th / (math.pi / 4))) % 8
        delta = (th - kf * math.pi / 4 + math.pi) % (2 * math.pi) - math.pi
        rb = FR.COLLAR_P / math.cos(delta) + 0.06
        zb = float(skirt_z_at(np.array([rb * math.cos(th)]), np.array([rb * math.sin(th)]))[0][0]) + 0.13
        t = np.linspace(0, 1, 80)
        rr_ = rb + (FR.COLLAR_TOP_R + 0.07 - rb) * t
        zz_ = zb + (FR.COLLAR_TOP_Z - zb) * t
        xx, yy = rr_ * math.cos(th), rr_ * math.sin(th)
        inside = (xx > FR.WX_W - FR.W_OVH) & (xx < FR.WX_E + FR.W_OVH) & (yy > FR.WY_S - FR.W_OVH) & (yy < FR.WY_N + FR.W_OVH)
        d = zz_ - np.where(inside, thatch_low(xx, yy) + 0.04, -10.0)
        hit = np.flatnonzero((d[:-1] < 0) & (d[1:] >= 0))
        if len(hit) == 0 or not inside[hit[0]]:
            P_.append(None)
            continue
        i = hit[0]
        f = -d[i] / (d[i + 1] - d[i])
        P_.append(np.array([xx[i] + (xx[i + 1] - xx[i]) * f, yy[i] + (yy[i + 1] - yy[i]) * f, zz_[i] + (zz_[i + 1] - zz_[i]) * f]))
    runs, cur = [], []
    for q in P_ + [None]:
        if q is None:
            if len(cur) > 4:
                runs.append(np.array(cur))
            cur = []
        else:
            cur.append(q)
    for r_ in runs:
        thatch_roll(accf, r_, 0.12, 97, flat=0.35, seg=10, mat="M_lead", bind=0.0)
    finalize(accf, coll)
    finalize(accm, coll, smooth_deg=25.0)





ROLL_P, ROLL_VIS = roll_profile()


def thatch_wing_roof(g, seed=3, rng_seed=1313):
    """KIT COMPONENT: the wing's thatch courses, core and eave roll (see the module doc)."""
    build_wing_roof(g.sub("wing"), seed=seed, rng_seed=rng_seed)


def ridge_comb(g, seed=1414):
    """KIT COMPONENT: ridge dome, rider log and the crossed-shake comb."""
    build_wing_ridge(g.sub("wing"), seed=seed)


def thatch_junctions(g, seed=1515):
    """KIT COMPONENT: eave poles, fillets, flashings and the valley apron (run after the thatch, turret and skirt)."""
    build_wing_structure(g.sub("wing"), seed=seed)
