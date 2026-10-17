"""components.linear_roof -- a straight two-slope (gable) roof over a rectangular body (kit, variant v3_longhouse_roundend).

A linear roof is described by ONE spec object, GableRoof, in its own local frame (x along the ridge, y across, z up)
placed in the building by `origin` and `yaw`; every other module (walls, junctions, decals) reads its geometry from
that object, so a building recipe states the roof once:

    roof = GableRoof(x0=-11.0, x1=-0.5, half=2.6, wall_z=2.75, pitch_deg=40, overhang=0.45, verge=(0.40, 0.0))
    linear_roof(g, roof, covering="thatch", clip=inside_cone(g), seed=71)

Geometry of the spec (local frame):
    half        half width of the body at the OUTER wall faces (m); the eave lip is at half + overhang
    wall_z      height of the roof reference surface (= top of the deck = underside of the covering) at the wall faces
    pitch_deg   slope pitch; overhang = horizontal eave overhang beyond the wall faces
    x0, x1      the gable wall outer faces (or the end of the run where the roof dies into another body)
    verge       (v0, v1) verge overhang beyond x0 / x1; 0 = that end abuts another body (no verge finish)
    covering    "thatch" (stepped layered clumps, eave nose, ridge roll + shake comb) or "shingle" (the kit's chunky
                shingles from shingles.SIZE_TABLE, doubled starter, ridge comb)

linear_roof(g, roof, ...) builds  <P>_<name>_deck (sarking slab: the continuous backing under the covering, note 6),
<P>_<name>_rafters (rafter tails under the eave overhang + verge rafters), <P>_<name>_covering (thatch clumps or
shingles, one Mask piece per clump / shingle), <P>_<name>_ridge (ridge roll, thatch only) and <P>_<name>_comb (ridge
comb of riven shakes, SIZE_TABLE 'comb_shake').  `clip(P) -> bool` drops faces wholly inside another body (e.g. the
cone of a round end: components.roof_junction.inside_cone); the junction itself is closed by
components.roof_junction.cone_abutment.
"""
import math

import numpy as np

from ..core import log, n2
from ..geom import Acc, beam, finalize, sweep
from ..shingles import SH_VARIANTS, SIZE_TABLE, shake_mesh, shingle_mesh


class GableRoof:
    """the dimension table of one straight gable roof (see module doc).  Pure geometry, no meshes."""

    def __init__(self, x0, x1, half, wall_z, pitch_deg=40.0, overhang=0.45, verge=(0.40, 0.40), origin=(0.0, 0.0),
                 yaw_deg=0.0, deck_t=0.035, thick=0.30, step=0.10, exposure=0.30, ridge_roll=(0.36, 0.20),
                 name="roof"):
        self.name = name
        self.x0, self.x1 = float(x0), float(x1)
        self.half = float(half)
        self.wall_z = float(wall_z)
        self.p = math.radians(pitch_deg)
        self.ovh = float(overhang)
        self.v0, self.v1 = float(verge[0]), float(verge[1])
        self.origin = np.array([float(origin[0]), float(origin[1])])
        self.yaw = math.radians(yaw_deg)
        self.deck_t = float(deck_t)
        self.T0 = float(thick)              # covering thickness above the deck between the course butts (thatch)
        self.step = float(step)             # extra thickness at each course butt (the stepped layers)
        self.exposure = float(exposure)
        self.roll_w, self.roll_h = ridge_roll
        self.Y = self.half + self.ovh                   # lip half width
        self.U = self.Y / math.cos(self.p)              # slope length lip -> ridge
        self.z_lip = self.wall_z - self.ovh * math.tan(self.p)
        self.z_ridge = self.wall_z + self.half * math.tan(self.p)
        self.xa = self.x0 - self.v0                     # covering extent along the ridge
        self.xb = self.x1 + self.v1

    # ---- frames ------------------------------------------------------------------------------------------------
    def to_world(self, P):
        P = np.asarray(P, float)
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        out = P.copy()
        out[..., 0] = self.origin[0] + c * P[..., 0] - s * P[..., 1]
        out[..., 1] = self.origin[1] + s * P[..., 0] + c * P[..., 1]
        return out

    def to_local(self, P):
        P = np.asarray(P, float)
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        dx, dy = P[..., 0] - self.origin[0], P[..., 1] - self.origin[1]
        out = P.copy()
        out[..., 0] = c * dx + s * dy
        out[..., 1] = -s * dx + c * dy
        return out

    def dir_world(self, d):
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        d = np.asarray(d, float)
        return np.stack([c * d[..., 0] - s * d[..., 1], s * d[..., 0] + c * d[..., 1], d[..., 2]], -1)

    # ---- surfaces (local) --------------------------------------------------------------------------------------
    def normal(self, sg):
        return np.array([0.0, sg * math.sin(self.p), math.cos(self.p)])

    def surf(self, x, u, sg, off=0.0):
        """local point on side sg (-1: -y slope, +1: +y slope) at ridge coordinate x, slope distance u from the lip,
        `off` metres out of the reference surface along the slope normal."""
        x, u, off = np.broadcast_arrays(np.asarray(x, float), np.asarray(u, float), np.asarray(off, float))
        y = sg * (self.Y - u * math.cos(self.p)) + off * sg * math.sin(self.p)
        z = self.z_lip + u * math.sin(self.p) + off * math.cos(self.p)
        return np.stack([x, y, z], -1)

    def ref_z(self, y):
        """reference surface (deck top) height at local y."""
        return self.z_lip + (self.Y - np.abs(np.asarray(y, float))) * math.tan(self.p)

    def under_z(self, y):
        """deck underside height at local y (walls stop here)."""
        return self.ref_z(y) - self.deck_t / math.cos(self.p)

    def top_z(self, y):
        """smoothed top of the covering (mid-step envelope incl. the ridge roll and, when built, the eave roll),
        local y -> z."""
        y = np.asarray(y, float)
        z = self.ref_z(y) + (self.T0 + 0.45 * self.step) / math.cos(self.p)
        if getattr(self, "ROLL", None) is not None:
            ro = self.roll_top_o((self.Y - np.abs(y)) / math.cos(self.p))
            z = np.where(np.isnan(ro), z, np.maximum(z, self.ref_z(y) + np.nan_to_num(ro) / math.cos(self.p)))
        zc, wr, hr = self.roll_centre_z(), self.roll_w, self.roll_h
        roll = zc + hr * np.sqrt(np.clip(1 - (y / wr) ** 2, 0, 1)) + 0.03
        return np.where(np.abs(y) < wr, np.maximum(z, roll), z)

    def roll_centre_z(self):
        return self.ref_z(0.0) + self.T0 / math.cos(self.p) - 0.04

    # ---- the eave roll (thatch, style "courses"; round 2) ---------------------------------------------------------
    def eave_roll(self, front=0.06, radius=0.16, proud=0.06, drop=0.035, tail=0.55):
        """the D-section eave roll of a layered thatch covering (thatch.py's eave-roll language), in slope
        coordinates (u from the lip, o off the reference surface): a half-round nose `front` m beyond the deck edge,
        its underside `drop` m under the deck, its crest `proud` m over the course butts, and a tail `tail` m long
        buried under the first course.  Stored on the spec as self.ROLL (other modules read it: junctions, verge)."""
        u_c = -front + radius
        o_bot = -self.deck_t - drop
        H = self.T0 + self.step + proud
        self.ROLL = dict(u_f=-front, u_c=u_c, Ru=radius, o_bot=o_bot, H=H, L=tail,
                         o_m=0.5 * (o_bot + H), hh=0.5 * (H - o_bot), o_end=self.T0 - 0.03)
        return self.ROLL

    def roll_top_o(self, u):
        """offset of the eave roll's upper surface at slope distance u (nan outside the roll's top)."""
        R = getattr(self, "ROLL", None)
        u = np.asarray(u, float)
        if R is None:
            return np.full(u.shape, np.nan)
        out = np.full(u.shape, np.nan)
        m = (u >= R["u_f"]) & (u <= R["u_c"])
        out[m] = R["o_m"] + R["hh"] * np.sqrt(np.clip(1 - ((R["u_c"] - u[m]) / R["Ru"]) ** 2, 0, 1))
        m = (u > R["u_c"]) & (u <= R["u_c"] + R["L"])
        t = (u[m] - R["u_c"]) / R["L"]
        out[m] = R["o_end"] + (R["H"] - R["o_end"]) * (1 - t) ** 1.5
        return out

    def roll_section(self, n_front=13):
        """closed (u, o) loop of the eave roll section (nose bottom -> front -> crest -> tail -> back -> underside)
        and per-point visibility weights (for thatch.d_roll)."""
        R = self.ROLL
        a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, n_front)
        front = np.stack([R["u_c"] - R["Ru"] * np.cos(a), R["o_m"] + R["hh"] * np.sin(a)], 1)
        t = np.linspace(0, 1, 8)[1:]
        tail = np.stack([R["u_c"] + R["L"] * t, R["o_end"] + (R["H"] - R["o_end"]) * (1 - t) ** 1.5], 1)
        back = np.array([[R["u_c"] + R["L"], 0.004], [R["u_c"] + 0.16, 0.004],
                         [R["u_c"] + 0.07, -self.deck_t - 0.008]])
        uo = np.concatenate([front, tail, back])
        vis = np.concatenate([np.ones(n_front), [1, 1, 1, 0.6, 0.2, 0, 0], [0, 0, 0.6]])
        return uo, vis

    def wall_top_fn(self, x_or_y="y"):
        """for a wall laid along the gable (local y run): s -> deck underside + 2 cm (stones tuck under the deck)."""
        return lambda y: float(self.under_z(y)) + 0.02


# =================================================================================================================
def _clumps_along(rng, a, b, w_rng):
    """split [a, b] into clump / unit widths (log-uniform in w_rng), last one stretched to close the run."""
    xs = [a]
    while b - xs[-1] > w_rng[0] * 1.2:
        w = math.exp(rng.uniform(math.log(w_rng[0]), math.log(w_rng[1])))
        if b - (xs[-1] + w) < w_rng[0] * 0.8:
            w = b - xs[-1]
        xs.append(min(xs[-1] + w, b))
    if xs[-1] < b:
        xs[-1] = b
    return np.array(xs)


def _thatch_courses(roof, acc, rng, clip_local=None, seed=0):
    """stepped, layered thatch courses: each course is a row of clumps (0.25-0.6 m wide), its butt `step` thicker
    than its tail, the next course's butt laid over that tail; the eave course is the thick eave nose (down past the
    deck edge); the verge clumps have their outer side face.  Only the top, butt and verge faces are modelled (the
    underside is the deck, note 6)."""
    p = roof.p
    e = roof.exposure
    K = int(math.ceil((roof.U - 0.12) / e))
    ov = 0.07
    n_piece = 0
    for sg in (-1, 1):
        for k in range(K):
            ub0 = k * e
            u_end = min(ub0 + e + ov, roof.U + 0.02)
            if ub0 >= roof.U - 0.05:
                break
            xs = _clumps_along(rng, roof.xa - 0.04, roof.xb, (0.20, 0.48))
            for i in range(len(xs) - 1):
                xa_, xb_ = xs[i], xs[i + 1]
                jit = rng.uniform(-0.025, 0.025) if k > 0 else rng.uniform(-0.01, 0.01)
                lift = rng.uniform(0.0, 0.02)
                crown = rng.uniform(0.022, 0.038)
                ub = ub0 + jit
                top_b = roof.T0 + roof.step + lift
                # rows along the slope: a ROUNDED butt (bundle ends), then the tapering top under the next course
                if k == 0:
                    # the eave: a thick half-round nose from under the deck edge round to the top
                    base_lo = -roof.deck_t - 0.07
                    H = top_b - base_lo
                    R = 0.11
                    a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, 9)
                    nose_u = list(ub + R - R * np.cos(a))
                    nose_o = list(base_lo + 0.5 * H * (1 + np.sin(a)))
                    nose_u = [ub + R + 0.07] + nose_u
                    nose_o = [-roof.deck_t + 0.004] + nose_o
                    u_top0 = ub + R
                else:
                    base_lo = roof.T0 - 0.035
                    rn = 0.07
                    a = np.linspace(0.0, 0.5 * np.pi, 6)
                    nose_u = list(ub + rn * (1 - np.cos(a)))
                    nose_o = list(base_lo + (top_b - base_lo) * np.sin(a))
                    u_top0 = ub + rn
                n_top = max(2, int((u_end - u_top0 - 0.04) / 0.10) + 1)
                tail_u = np.linspace(u_top0 + 0.04, u_end, n_top)
                tt = np.clip((tail_u - ub) / e, 0, 1)
                tail_o = roof.T0 + lift + roof.step * (1 - tt) ** 1.3
                if u_end >= roof.U:                       # the last course runs under the ridge roll
                    tail_o[-1] = roof.T0 - 0.02
                us = np.array(nose_u + list(tail_u))
                off = np.array(nose_o + list(tail_o))
                n_nose = len(nose_u)
                ncol = 6
                cx = np.linspace(xa_, xb_, ncol)
                tcol = np.linspace(0, 1, ncol)
                X = np.broadcast_to(cx[None, :], (len(us), ncol))
                # a wavy, bundle-by-bundle butt line (+-1.5 cm along each clump)
                wav = 0.015 * n2(cx * 6.0, np.full(ncol, k * 1.7 + sg), seed + 31)
                fade = np.clip(1 - (us - ub) / 0.25, 0, 1)
                U_ = us[:, None] + wav[None, :] * fade[:, None]
                cr = crown * np.sin(np.pi * tcol)[None, :] ** 0.7 * np.clip((off[:, None] - base_lo) / max(top_b - base_lo, 1e-3), 0, 1)
                O = off[:, None] + cr + 0.006 * n2(X * 3.0, U_ * 2.0 + k, seed + sg)
                P = roof.surf(X, U_, sg, O)
                V = P.reshape(-1, 3)
                F = []
                nr = len(us)
                for r in range(nr - 1):
                    for c in range(ncol - 1):
                        a = r * ncol + c
                        F.append((a, a + 1, a + ncol + 1, a + ncol))
                F = np.array(F)
                # verge side faces on the outermost clumps (from the deck underside to the top)
                extra_V, extra_F = [], []
                for side, ci in ((0, 0), (1, ncol - 1)):
                    xe = cx[ci]
                    is_end = (side == 0 and abs(xe - xs[0]) < 1e-9 and roof.v0 > 0) or \
                             (side == 1 and abs(xe - xs[-1]) < 1e-9 and roof.v1 > 0)
                    if not is_end:
                        continue
                    lo = roof.surf(np.full(nr, xe), us, sg, np.full(nr, -roof.deck_t - 0.012))
                    base = len(V) + sum(len(v_) for v_ in extra_V)
                    extra_V.append(lo)
                    for r in range(nr - 1):
                        top0, top1 = r * ncol + ci, (r + 1) * ncol + ci
                        q = (top0, top1, base + r + 1, base + r)
                        extra_F.append(q if side == 0 else q[::-1])
                if extra_V:
                    V = np.concatenate([V] + extra_V)
                    F = np.concatenate([F, np.array(extra_F)])
                # orient: the tail (top) faces outward along the slope normal, the verge sides outward along x
                n_grid = (nr - 1) * (ncol - 1)
                q = V[F[n_grid - 2]]
                nn = np.cross(q[1] - q[0], q[3] - q[0])
                if float(nn @ roof.normal(sg)) < 0:
                    F[:n_grid] = F[:n_grid, ::-1].copy()
                for fi in range(n_grid, len(F)):
                    q = V[F[fi]]
                    nn = np.cross(q[1] - q[0], q[2] - q[0])
                    want = -1.0 if q[:, 0].mean() < 0.5 * (roof.xa + roof.xb) else 1.0
                    if nn[0] * want < 0:
                        F[fi] = F[fi, ::-1].copy()
                acc.add(roof.to_world(V), F, "M_thatch", wear=float(rng.uniform(0.2, 0.6)))
                n_piece += 1
    return n_piece


def _smooth_steps(xs, edges, levels, blend=0.20):
    """piecewise-constant levels over the runs [edges[i], edges[i+1]] with smoothstep transitions `blend` wide."""
    out = np.full(len(xs), float(levels[0]))
    for i in range(1, len(levels)):
        t = np.clip((xs - edges[i] + 0.5 * blend) / blend, 0, 1)
        out += (levels[i] - levels[i - 1]) * t * t * (3 - 2 * t)
    return out


def _layered_courses(roof, acc, rng, x_lo, x_hi, seed=0, run=(1.0, 2.2), crown=(0.004, 0.009), drift=0.045,
                     col=0.15):
    """round 2 (director: "fewer, wider units"): continuous thatch courses on both slopes, the keep wing's course
    language (thatch.py) on a straight roof.  Each course is ONE sheet along the whole roof: a rounded butt `step`
    thick over the course below, a tapering top running on under the next course; the butt line drifts (+-drift m
    over 2-4 m) and is laid in bundle runs of `run` m (each its own +-1.2 cm set and <= 1.2 cm lift, a soft crown
    <= `crown`).  The first course sits on the eave roll (roof.ROLL).  Returns (n_courses, verge profiles):
    verge[(sg, end)] = list of (u, o) arrays of every course at the x_lo (end 0) / x_hi (end 1) column."""
    p = roof.p
    e = roof.exposure
    R = roof.ROLL
    ov = 0.18                     # tail overlap > the largest butt-line offset between two courses (2 x drift + du)
    rn = 0.06
    n_col = max(2, int(math.ceil((x_hi - x_lo) / col)) + 1)
    xs = np.linspace(x_lo, x_hi, n_col)
    verge = {}
    n_c = 0
    for sg in (-1, 1):
        k = 0
        while True:
            ub0 = R["u_c"] + 0.20 + k * e
            if ub0 >= roof.U - 0.05:
                break
            u_end = min(ub0 + e + ov, roof.U + 0.02)
            ed = _clumps_along(rng, x_lo, x_hi, run)
            nr_ = len(ed) - 1
            du = _smooth_steps(xs, ed, rng.uniform(-0.018, 0.018, nr_))
            lift = _smooth_steps(xs, ed, rng.uniform(0.0, 0.012, nr_))
            cr_ = rng.uniform(*crown, nr_)
            idx = np.clip(np.searchsorted(ed, xs, side="right") - 1, 0, nr_ - 1)
            tr = np.clip((xs - ed[idx]) / np.maximum(ed[idx + 1] - ed[idx], 1e-6), 0, 1)
            crn = cr_[idx] * np.sin(np.pi * tr) ** 0.8
            dr = drift * n2(xs * 0.30, np.full(n_col, k * 1.7 + sg * 5.0), seed + 31) + du
            base_lo = roof.T0 - 0.035
            top_b = roof.T0 + roof.step
            a = np.linspace(0.0, 0.5 * np.pi, 5)
            bu = rn * (1 - np.cos(a))
            bo = base_lo + (top_b - base_lo) * np.sin(a)
            n_t = max(2, int(math.ceil((u_end - ub0 - rn - 0.05) / 0.12)) + 1)
            tu = np.linspace(rn + 0.05, u_end - ub0, n_t)
            tt = np.clip(tu / e, 0, 1)
            to = roof.T0 + roof.step * (1 - tt) ** 1.3
            if u_end >= roof.U:
                to[-1] = roof.T0 - 0.02
            us = np.concatenate([bu, tu])
            off = np.concatenate([bo, to])
            w = np.clip((off - base_lo) / (top_b - base_lo), 0, 1)
            w[len(bu):] = 1.0
            if u_end >= roof.U:
                w[-1] = 0.0
            U_ = ub0 + us[:, None] + dr[None, :]
            X = np.broadcast_to(xs[None, :], U_.shape)
            O = off[:, None] + (lift[None, :] + crn[None, :]) * w[:, None] + \
                0.004 * w[:, None] * n2(X * 1.5, U_ * 2.0 + k, seed + sg)
            P = roof.surf(X, U_, sg, O)
            nr = len(us)
            ii = np.arange(nr - 1)[:, None] * n_col + np.arange(n_col - 1)[None, :]
            F = np.stack([ii, ii + 1, ii + n_col + 1, ii + n_col], -1).reshape(-1, 4)
            q = P.reshape(-1, 3)[F[len(F) // 2]]
            if float(np.cross(q[1] - q[0], q[3] - q[0]) @ roof.normal(sg)) < 0:
                F = F[:, ::-1]
            acc.add(roof.to_world(P.reshape(-1, 3)), F, "M_thatch", wear=float(rng.uniform(0.2, 0.6)))
            verge.setdefault((sg, 0), []).append((U_[:, 0].copy(), O[:, 0].copy()))
            verge.setdefault((sg, 1), []).append((U_[:, -1].copy(), O[:, -1].copy()))
            k += 1
            n_c += 1
    return n_c, verge


def _envelope(sources, u):
    """upper envelope of several (u, o) polylines (each monotonic in u), sampled at u; nan where none is defined."""
    out = np.full(len(u), -np.inf)
    for su, so in sources:
        o = np.interp(u, su, so, left=-np.inf, right=-np.inf)
        out = np.maximum(out, o)
    return out


def _verge_faces(roof, acc, verge, x_v, end, x_deck):
    """one continuous, closed verge face per gable (round 2, director: no slots between the courses): a single
    polygon in the gable plane x = x_v from the deck underside up to the upper envelope of the eave roll and every
    course's end section, across both rakes and the ridge, plus a strip closing its foot back under the deck end
    (x_deck).  Faces outward (-x at end 0, +x at end 1)."""
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon
    R = roof.ROLL
    p = roof.p
    o_b = -roof.deck_t - 0.012
    u_a = R["u_c"] + 0.04
    tops, bots = {}, {}
    for sg in (-1, 1):
        src = verge[(sg, end)]
        ur = np.linspace(u_a, R["u_c"] + R["L"], 16)
        src = [(ur, roof.roll_top_o(ur))] + list(src)
        u_max = max(float(s[0][-1]) for s in src)
        us = np.unique(np.concatenate([np.arange(u_a, u_max, 0.02), [u_max]] + [s[0] for s in src]))
        us = us[(us >= u_a) & (us <= u_max)]
        env = _envelope(src, us)
        ok = np.isfinite(env)
        us, env = us[ok], env[ok]
        Pt = roof.surf(np.full(len(us), x_v), us, sg, env)
        tops[sg] = Pt[:, 1:]                               # (y, z) eave -> ridge
        yb0 = float(roof.surf(x_v, u_a, sg, o_b)[1])
        yb = np.linspace(yb0, 0.0, 24)
        bots[sg] = np.stack([yb, roof.ref_z(yb) + o_b / math.cos(p)], 1)   # eave -> ridge
    loop = np.concatenate([tops[-1], tops[1][::-1], bots[1], bots[-1][::-1]])
    keep = np.concatenate([[True], np.linalg.norm(np.diff(loop, axis=0), axis=1) > 1e-4])
    loop = loop[keep]
    tris = tessellate_polygon([[Vector((float(a_), float(b_), 0.0)) for a_, b_ in loop]])
    V = np.stack([np.full(len(loop), x_v), loop[:, 0], loop[:, 1]], 1)
    F = np.array([list(t) for t in tris])
    want = -1.0 if end == 0 else 1.0
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])[:, 0]
    F[nrm * want < 0] = F[nrm * want < 0][:, ::-1]
    acc.add(roof.to_world(V), F, "M_thatch", wear=0.4)
    # the foot strip: from the verge face back under the deck end (1.2 cm under the deck underside)
    for sg in (-1, 1):
        B = bots[sg]
        A0 = np.stack([np.full(len(B), x_v), B[:, 0], B[:, 1]], 1)
        A1 = A0.copy()
        A1[:, 0] = x_deck
        Vs = np.concatenate([A0, A1])
        n = len(B)
        Fs = np.array([(i, i + 1, n + i + 1, n + i) for i in range(n - 1)])
        q = Vs[Fs[0]]
        if float(np.cross(q[1] - q[0], q[3] - q[0])[2]) > 0:
            Fs = Fs[:, ::-1]
        acc.add(roof.to_world(Vs), Fs, "M_thatch", wear=0.4)


def _eave_rolls(roof, acc, rng, x_lo, x_hi, seed=0, ends=None, bundles=None):
    """the eave roll on both eaves: thatch.d_roll (the keep wing's D-roll sweep: +-1 cm swelling over 0.5-1 m, no
    pillows; bundles=thatch.d_roll bundles tuple binds it into long bundles at 4x the cost) along the lip with the
    GableRoof.eave_roll section, the buried back not modelled (drop_hidden).  ends[sg] = (x_from, x_to) local
    overrides (a roll that dies into another body stops where that body takes over); the free ends run 5 cm past
    the verge with a short round taper."""
    from .thatch import d_roll
    uo, vis = roof.roll_section()
    p = roof.p
    q = uo[:, 0] * math.cos(p) - uo[:, 1] * math.sin(p)          # inward horizontal
    v = uo[:, 0] * math.sin(p) + uo[:, 1] * math.cos(p)          # up
    prof = np.stack([q, v], 1)
    area = 0.5 * float(np.sum(prof[:, 0] * np.roll(prof[:, 1], -1) - np.roll(prof[:, 0], -1) * prof[:, 1]))
    if area < 0:
        prof, vis = prof[::-1].copy(), vis[::-1].copy()
    out = {}
    for sg in (-1, 1):
        a_, b_ = (x_lo - 0.05, x_hi + 0.05)
        ta, tb = 0.12, 0.12
        if ends and sg in ends:
            ea, eb = ends[sg]
            if ea is not None:
                a_, ta = ea, 0.0
            if eb is not None:
                b_, tb = eb, 0.0
        n = max(4, int((b_ - a_) / 0.05) + 1)
        xs = np.linspace(a_, b_, n)
        if sg > 0:
            xs, ta, tb = xs[::-1], tb, ta
        path = roof.to_world(roof.surf(xs, np.zeros(n), sg, np.zeros(n)))
        P = d_roll(acc, path, prof, vis, seed + 11 * sg, rng, up=(0.0, 0.0, 1.0), var=0.010, taper=(ta, tb),
                   tmin=(0.75, 0.75), ribs=False, step=0.06, z_wave=0.008, drop_hidden=True,
                   bundles=bundles, calm_taper=True, round_end=True)
        out[sg] = P
    return out


def _shingle_courses(roof, acc, rng, seed=0):
    """the kit's chunky shingles (SIZE_TABLE 'shingle' / 'starter') laid in straight courses on both slopes."""
    T = SIZE_TABLE["shingle"]
    e = 0.5 * (T["exposure"][0] + T["exposure"][1])
    K = int(math.ceil((roof.U - 0.15) / e))
    n_piece = 0
    for sg in (-1, 1):
        for k in range(-1, K):
            ub = max(k, 0) * e + (0.012 if k < 0 else 0.0)
            L = SIZE_TABLE["starter"]["length"] if k < 0 else min(T["length"], roof.U - ub + 0.02)
            if L < 0.08:
                break
            xs = _clumps_along(rng, roof.xa - 0.03, roof.xb, (T["width"][0], T["width"][1]))
            for i in range(len(xs) - 1):
                gap = rng.uniform(*T["gap"])
                W = xs[i + 1] - xs[i] - gap
                var = SH_VARIANTS[int(rng.integers(16))]
                Pl, F, uv = shingle_mesh(W, L, var, curl=var["curl_eave"] if k < 2 else var["curl"],
                                         bottom=k < 1, head=True)
                v = np.clip(Pl[:, 1] / 0.72, 0, 1)
                wedge = 0.0 if k < 0 else (0.037 if k == 0 else 0.066)
                off = wedge * (1 - v) + Pl[:, 2] + rng.uniform(0, 0.01) * (1 - v)
                x = 0.5 * (xs[i] + xs[i + 1]) + Pl[:, 0]
                u = ub + Pl[:, 1] + rng.uniform(-0.01, 0.01)
                P = roof.surf(x, u, sg, off)
                Fl = [f[:, ::-1] if sg > 0 else f for f in F]      # the slope map has det = -sg
                acc.add(roof.to_world(P), Fl, "M_roof_shingle", uv, wear=float(rng.uniform(0.2, 0.6)))
                n_piece += 1
    return n_piece


def _ridge_roll(roof, acc, rng, x_from=None):
    """thatch ridge roll: a rounded bundle along the ridge (closed sweep, ends capped at the verges)."""
    wr, hr = roof.roll_w, roof.roll_h
    zc = roof.roll_centre_z()
    a = np.linspace(0, np.pi, 11)
    top = np.stack([wr * np.cos(a), hr * np.sin(a)], 1)                 # right, up (CCW from +y side)
    bury = np.array([[-wr * 0.85, -0.10], [0.0, -0.16], [wr * 0.85, -0.10]])
    prof = np.concatenate([top, bury])
    x0_ = roof.xa - 0.02 if x_from is None else x_from
    xs = np.linspace(x0_, roof.xb, max(4, int((roof.xb - x0_) / 0.25) + 1))
    path = np.stack([xs, 0.012 * n2(xs * 0.8, np.zeros_like(xs), 77), zc + 0.015 * n2(xs * 0.6, np.ones_like(xs), 78)], 1)
    # sweep's profile axes: right = U x T, up = U; T = +x, U = +z -> right = -y; mirror the profile for +y
    prof_s = prof * np.array([-1.0, 1.0])
    V, F = sweep(path, (0, 0, 1), prof_s[::-1].copy())
    acc.add(roof.to_world(V), F, "M_thatch", wear=0.3)
    # binding spars across the roll every ~0.7 m (split hazel, read at mid-shot as the ridge pattern)
    for x in np.arange(roof.xa + 0.35, roof.xb - 0.2, 0.7):
        ang = np.linspace(0.15, np.pi - 0.15, 9)
        pth = np.stack([np.full_like(ang, x), -wr * np.cos(ang) * 1.01, zc + hr * np.sin(ang) * 1.01 + 0.004], 1)
        V, F = sweep(pth, (1, 0, 0), np.array([[0.012, -0.006], [0.012, 0.006], [-0.012, 0.006], [-0.012, -0.006]]))
        acc.add(roof.to_world(V), F, "M_timber_weathered", wear=0.5)


def _ridge_comb(roof, acc, rng, seed=0):
    """ridge comb: short riven shakes (SIZE_TABLE 'comb_shake') crossed over the ridge in a saddle, alternating
    sides, butts down on the slopes or the roll."""
    T = SIZE_TABLE["comb_shake"]
    thatch = roof.T0 > 0.1
    z0 = (roof.roll_centre_z() + roof.roll_h + 0.13) if thatch else roof.ref_z(0.0) + 0.16    # crest stands proud
    x = roof.xa + 0.03
    n = 0
    k = 0
    while x < roof.xb - 0.05:
        w = rng.uniform(*T["width"]) * 1.8
        for sg in (-1, 1):
            L = float(rng.choice(T["lengths"])) + 0.12
            V, F, uv = shake_mesh(rng, L=L, W=w, butt=rng.uniform(*T["thick"]) * 0.8, head=0.012, n_len=5)
            ang = roof.p + math.radians(rng.uniform(16, 28))         # steeper than the slope: the crest stands up
            # local shake: x across (-> ridge x), y butt->head (-> up the slope toward the ridge), z out
            ca, sa = math.cos(ang), math.sin(ang)
            # head at the ridge (yv = 0 -> y ~ 0), butt down the slope on side sg (yv < 0 -> |y| grows)
            yv = V[:, 1] - L
            P = np.stack([x + w / 2 + V[:, 0],
                          sg * (-yv * ca + V[:, 2] * sa) - sg * 0.04,
                          z0 + yv * sa + V[:, 2] * ca + 0.02], 1)
            Fl = [f[:, ::-1] if sg > 0 else f for f in F]      # the comb map has det = -sg
            acc.add(roof.to_world(P), Fl, "M_roof_shake", uv, wear=float(rng.uniform(0.3, 0.7)))
            n += 1
        x += w * 0.92
        k += 1
    return n


def _deck(roof, acc, clip_local=None):
    """the sarking deck: one closed slab per slope (top = reference surface, thickness deck_t), split every ~0.5 m
    along the ridge so a clip can drop the parts inside another body.  It is the continuous backing under the
    covering (note 6) and the soffit seen under the eave and the verge."""
    t = roof.deck_t
    xs = np.linspace(roof.xa, roof.xb, max(2, int((roof.xb - roof.xa) / 0.5) + 1))
    us = np.array([0.0, roof.ovh / math.cos(roof.p), roof.U * 0.5, roof.U])
    for sg in (-1, 1):
        X, Uu = np.meshgrid(xs, us, indexing="ij")
        top = roof.surf(X, Uu, sg, 0.0)
        bot = roof.surf(X, Uu, sg, -t)
        nx_, nu = X.shape
        V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
        off = nx_ * nu
        I = lambda i, j: i * nu + j  # noqa: E731
        F = []
        for i in range(nx_ - 1):
            for j in range(nu - 1):
                F.append((I(i, j), I(i + 1, j), I(i + 1, j + 1), I(i, j + 1)))
                F.append((off + I(i, j), off + I(i, j + 1), off + I(i + 1, j + 1), off + I(i + 1, j)))
            F.append((I(i, 0), off + I(i, 0), off + I(i + 1, 0), I(i + 1, 0)))          # eave edge
        for j in range(nu - 1):
            F.append((I(0, j), I(0, j + 1), off + I(0, j + 1), off + I(0, j)))           # verge ends
            F.append((I(nx_ - 1, j), off + I(nx_ - 1, j), off + I(nx_ - 1, j + 1), I(nx_ - 1, j + 1)))
        F = np.array(F)
        q = V[F[0]]
        if float(np.cross(q[1] - q[0], q[3] - q[0]) @ roof.normal(sg)) < 0:
            F = F[:, ::-1]
        acc.add(roof.to_world(V), F, "M_timber_weathered", wear=0.4)


def _rafters(roof, acc, rng, spacing=0.62):
    """rafter tails under the eave overhang (from 0.25 m inside the wall face to just behind the lip) and a verge
    rafter under each verge (seen from below and from the gable)."""
    t = roof.deck_t
    w, h = 0.11, 0.15
    xs = np.arange(roof.x0 + 0.25, roof.x1 - 0.1, spacing)
    for sg in (-1, 1):
        nrm = roof.normal(sg)
        for x in xs:
            x_ = x + rng.uniform(-0.03, 0.03)
            u0 = 0.03
            u1 = (roof.ovh + 0.25) / math.cos(roof.p)
            p0 = roof.surf(x_, u0, sg, -t - h / 2)
            p1 = roof.surf(x_, u1, sg, -t - h / 2)
            beam(acc, roof.to_world(p0), roof.to_world(p1), w, h, 0.012, "M_timber", up=roof.dir_world(nrm))
        for xe, ve in ((roof.x0, roof.v0), (roof.x1, roof.v1)):
            if ve <= 0:
                continue
            xv = xe - ve + 0.07 if xe == roof.x0 else xe + ve - 0.07
            p0 = roof.surf(xv, 0.0, sg, -t - h / 2)
            p1 = roof.surf(xv, roof.U - 0.05, sg, -t - h / 2)
            beam(acc, roof.to_world(p0), roof.to_world(p1), w, h, 0.012, "M_timber_weathered", up=roof.dir_world(nrm))


def linear_roof(g, roof, covering="thatch", clip=None, seed=71, comb=True, abut_cone=None, thatch_style="courses",
                abut_wall_in=0.10):
    """KIT COMPONENT: a straight gable roof from its GableRoof spec (see module doc).  clip(P_world, margin=0) -> bool
    marks vertices inside another body; faces wholly inside are dropped from the covering, ridge, comb and rafters,
    and deck faces more than 10 cm inside it.  abut_cone=(cx, cy): the roof runs into the cone of the round frame g
    centred there: dropped where it is under the cone's covering AND inside the round wall head (g.R_WALL -
    abut_wall_in; None = under the cone only, the round-1 rule), so under the cone's eave overhang the roof runs on
    (deck, eave roll, courses) and dies into the round wall instead of leaving a pocket under the oversailing eave.
    thatch_style: "courses" (round 2 default: continuous layered courses + thatch.d_roll eave roll + one closed
    verge face per gable) or "clumps" (round 1).  Publishes the spec on g.LINEAR_ROOFS[roof.name]."""
    if abut_cone is not None and clip is None:
        from .roof_junction import inside_cone
        cc = inside_cone(g, center=abut_cone)
        if abut_wall_in is None:
            clip = cc
        else:
            r_in = float(g.R_WALL) - float(abut_wall_in)
            c0 = np.array(abut_cone, float)

            def clip(V, margin=0.0):
                V = np.asarray(V, float)
                return cc(V, margin) & (np.hypot(V[:, 0] - c0[0], V[:, 1] - c0[1]) < r_in - margin)
    rng = np.random.default_rng(seed)
    if covering == "thatch" and thatch_style == "courses":
        return _linear_roof_courses(g, roof, clip, rng, seed, comb)
    pre = f"{g.prefix}_{roof.name}"
    if not hasattr(g, "LINEAR_ROOFS"):
        g.LINEAR_ROOFS = {}
    g.LINEAR_ROOFS[roof.name] = roof
    roof.covering = covering
    deck = Acc(pre + "_deck")
    _deck(roof, deck)
    if clip is not None:
        deck.cull = lambda V: clip(V, margin=0.10)
    finalize(deck, g.coll, smooth_deg=30.0)
    raf = Acc(pre + "_rafters")
    _rafters(roof, raf, rng)
    if clip is not None:
        raf.cull = clip
    finalize(raf, g.coll, smooth_deg=30.0)
    cov = Acc(pre + "_covering", 50)
    if covering == "thatch":
        n = _thatch_courses(roof, cov, rng, seed=seed)
    elif covering == "shingle":
        roof.T0, roof.step = 0.06, 0.0
        n = _shingle_courses(roof, cov, rng, seed=seed)
    else:
        raise ValueError(f"unknown covering {covering!r}")
    if clip is not None:
        cov.cull = clip
    finalize(cov, g.coll, smooth_deg=50.0, recalc=False)
    log(f"  {pre}: {n} {covering} pieces")
    if covering == "thatch":
        rid = Acc(pre + "_ridge", 50)
        _ridge_roll(roof, rid, rng)
        if clip is not None:
            rid.cull = clip
        finalize(rid, g.coll, smooth_deg=50.0)
    if comb:
        cb = Acc(pre + "_comb", 40)
        _ridge_comb(roof, cb, rng, seed=seed)
        if clip is not None:
            cb.cull = clip
        finalize(cb, g.coll, smooth_deg=40.0)
    return roof


def _linear_roof_courses(g, roof, clip, rng, seed, comb):
    """linear_roof, thatch_style "courses" (round 2): deck + rafters as before; the eave roll (thatch.d_roll),
    continuous layered courses, a closed verge face per free gable, the ridge roll and the comb."""
    pre = f"{g.prefix}_{roof.name}"
    if not hasattr(g, "LINEAR_ROOFS"):
        g.LINEAR_ROOFS = {}
    g.LINEAR_ROOFS[roof.name] = roof
    roof.covering = "thatch"
    roof.eave_roll()
    deck = Acc(pre + "_deck")
    _deck(roof, deck)
    if clip is not None:
        deck.cull = lambda V: clip(V, margin=0.10)
    finalize(deck, g.coll, smooth_deg=30.0)
    raf = Acc(pre + "_rafters")
    _rafters(roof, raf, rng)
    if clip is not None:
        raf.cull = clip
    finalize(raf, g.coll, smooth_deg=30.0)
    # the covering runs 4 cm past the deck at a free verge (the verge face covers the deck end)
    x_lo = roof.xa - 0.04 if roof.v0 > 0 else roof.xa
    x_hi = roof.xb + 0.04 if roof.v1 > 0 else roof.xb
    cov = Acc(pre + "_covering", 60)
    n_c, verge = _layered_courses(roof, cov, rng, x_lo, x_hi, seed=seed)
    if roof.v0 > 0:
        _verge_faces(roof, cov, verge, x_lo, 0, roof.xa + 0.02)
    if roof.v1 > 0:
        _verge_faces(roof, cov, verge, x_hi, 1, roof.xb - 0.02)
    if clip is not None:
        cov.cull = clip
    finalize(cov, g.coll, smooth_deg=60.0, recalc=False)
    roll = Acc(pre + "_eave_roll", 70)
    ends = {sg: (None if roof.v0 > 0 else x_lo, None if roof.v1 > 0 else x_hi) for sg in (-1, 1)}
    roof.EAVE_ROLLS = _eave_rolls(roof, roll, rng, x_lo, x_hi, seed=seed, ends=ends)
    if clip is not None:
        roll.cull = clip
    finalize(roll, g.coll, smooth_deg=70.0)
    log(f"  {pre}: {n_c} continuous thatch courses + eave rolls + verge faces")
    rid = Acc(pre + "_ridge", 50)
    _ridge_roll(roof, rid, rng, x_from=(x_lo - 0.03) if roof.v0 > 0 else None)
    if clip is not None:
        rid.cull = clip
    finalize(rid, g.coll, smooth_deg=50.0)
    if comb:
        cb = Acc(pre + "_comb", 40)
        _ridge_comb(roof, cb, rng, seed=seed)
        if clip is not None:
            cb.cull = clip
        finalize(cb, g.coll, smooth_deg=40.0)
    return roof
