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


EYEBROW = dict(x=0.0, side=1, d=1.5, width=2.0, height=0.75, flat=0.70, plateau=0.18, fade=1.20, lip=0.20,
               set_back=0.04, window=dict(width=0.56, height=0.36, sill=0.05), min_front=0.14, seed=0,
               tilt=False, span_rows=False, eave_inset=0.0, close_ends=False)
"""kit 1.13 (v5 round 5, ref4's eyebrow dormer): one eyebrow bump on a shingle GableRoof, in its local frame --
    x         centre along the ridge (local x)
    side      +1 / -1: the slope (local +y / -y)
    d         plan distance (m) in from the eave lip to the front (snapped so a whole course is the wave's eave)
    width     the wave's length along the eave (m); flat: the part of it at full height (a cosine fall either side)
    height    the lift (m) at the front: the vertical gap the timber front closes
    plateau   plan metres upslope at full height, then fade m: a smooth fall back into the slope (no ridge, no valley)
    lip       plan overhang (m) of the wave's lowest course past the deck front (the little dark eave)
    set_back  the timber front's face is this far out from the deck front (m; its backing covers the deck front)
    window    the kit window (components.openings.window keys, timber family; clear width / height / sill above
              the front's sill beam); None = a blind board front
    min_front the front is built where the gap is at least this tall (beyond it the deck front closes the gap)
kit 1.14 (v5 round 6; every default = the round-5 build, bit-identical):
    tilt       True: each lifted shingle's thickness is laid along the BUMP's own surface normal (the bell's slope
               along the eave and the fade's slope up the roof), not sheared vertically -- no thin slivers on the
               flanks (_brow_tilt)
    span_rows  True: the deck's tear rows and fine wave grid are inserted only over the bump's span (a separate
               closed deck patch), not along the whole roof length (fewer hidden deck triangles)
    eave_inset plan m: the lifted eave board under the wave's lowest course starts this far behind the course's butt
               line, so it hides in the eave's shadow instead of showing as a pale strip
    close_ends True: a closing board runs on past each end post, clamped under the wave's eave, down to where the gap
               is under 2 cm (no dark slot between the post and the wave's flank)"""


def eyebrow(x, side=1, **kw):
    """kit 1.13: an eyebrow-dormer spec for GableRoof(eyebrows=[...]) (see EYEBROW)."""
    return dict(x=float(x), side=side, **kw)


class GableRoof:
    """the dimension table of one straight gable roof (see module doc).  Pure geometry, no meshes."""

    def __init__(self, x0, x1, half, wall_z, pitch_deg=40.0, overhang=0.45, verge=(0.40, 0.40), origin=(0.0, 0.0),
                 yaw_deg=0.0, deck_t=0.035, thick=0.30, step=0.10, exposure=0.30, ridge_roll=(0.36, 0.20),
                 name="roof", ridge_sag=0.0, eave_sag=0.0, eave_sweep=0.0, sweep_len=1.0, verge_flare=0.0,
                 flare_len=1.6, wave=0.0, wave_seed=33, eyebrows=()):
        """kit 1.12 (v5 round 2, note 17 "soft, organic lines"; all 0 = the straight roof, bit-identical):
        ridge_sag      m the ridge drops at mid-length (parabolic, 0 at the covering's ends), fading to eave_sag at the lip
        eave_sag       m the eave lines drop at mid-length
        eave_sweep     m the eave lip is lifted (bell-cast / swept eave), fading quadratically over sweep_len m (plan)
                       in from the lip -- the slope flattens toward the eave
        verge_flare    m a FREE verge (overhang > 0) is lifted at the apex, fading over flare_len m along the ridge and
                       toward the eave: the verge / bargeboard line curves up to the apex (ref4)
        wave           m low-frequency +-wave out-of-true over the whole roof (art bible 6: ridges / eaves +-2-5 cm)
        The softness is ONE vertical warp field dz(x, y) applied by to_world (and removed by to_local), so every part
        linear_roof builds and every query (keep_out, top_depth, under_soffit, under_z_world) follows it.
        kit 1.13 (v5 round 5; () = no eyebrow, bit-identical): eyebrows=[eyebrow(...), ...] -- eyebrow dormers, a
        local bump in the same warp field (see eyebrow() / EYEBROW): the shingle courses swell over a small window in
        one smooth wave, the deck tears into a vertical front there (framed opening at the window), and linear_roof
        builds the short timber front with a kit window under the wave's little eave (_eyebrow_fronts)."""
        self.name = name
        self.ridge_sag, self.eave_sag = float(ridge_sag), float(eave_sag)
        self.eave_sweep, self.sweep_len = float(eave_sweep), float(sweep_len)
        self.verge_flare, self.flare_len = float(verge_flare), float(flare_len)
        self.wave, self.wave_seed = float(wave), int(wave_seed)
        self.warped = any(abs(v) > 0 for v in (self.ridge_sag, self.eave_sag, self.eave_sweep, self.verge_flare,
                                                self.wave)) or bool(eyebrows)
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
        self.BROWS = [self._resolve_brow(b) for b in (eyebrows or ())]

    # ---- kit 1.13 (v5 round 5): eyebrow dormers ---------------------------------------------------------------------
    def _resolve_brow(self, b):
        """an eyebrow() dict -> the resolved bump (slope coordinates u from the lip; the front snapped to the shingle
        course grid so one whole course forms the wave's little eave)."""
        B = dict(EYEBROW)
        B.update(b)
        unknown = set(b) - set(EYEBROW)
        if unknown:
            raise KeyError(f"eyebrow: unknown option(s) {sorted(unknown)}; known {sorted(EYEBROW)}")
        cp = math.cos(self.p)
        e = 0.5 * sum(SIZE_TABLE["shingle"]["exposure"])
        lip_u = B["lip"] / cp
        k_lip = max(2, int(round((B["d"] / cp - lip_u) / e)))
        B.update(sg=1 if B["side"] > 0 else -1, hw=0.5 * B["width"], pw=0.5 * min(B["flat"], 0.95 * B["width"]),
                 k_lip=k_lip, u_lip=k_lip * e, lip_u=lip_u, u_t=k_lip * e + lip_u,
                 plat_u=B["plateau"] / cp, fade_u=B["fade"] / cp)
        B["d_t"] = B["u_t"] * cp
        if B["u_t"] + B["plat_u"] + B["fade_u"] > self.U - 0.30:
            raise ValueError(f"eyebrow at x {B['x']:.2f}: its wave runs into the ridge; lower d, plateau or fade")
        return B

    def brow_bell(self, B, x):
        """the eyebrow's profile along the ridge: 1 over its flat top (+-flat / 2), a cosine fall to 0 at
        +-width / 2."""
        ax = np.abs(np.asarray(x, float) - B["x"])
        t = np.clip((ax - B["pw"]) / max(B["hw"] - B["pw"], 1e-6), 0.0, 1.0)
        return 0.5 * (1.0 + np.cos(np.pi * t))

    def _brow_dz(self, x, y, brow=None):
        """the eyebrow bumps' share of warp_z.  The bump is a STEP at the front u_t (below it the roof runs on
        untouched, above it it is lifted by height x bell(x)), fading smoothly to 0 upslope over `fade`.  brow:
        None -> each point is on the lifted side if its own slope distance is >= u_t (queries, walls); a number /
        array (all bumps) or {bump index: number / array} -> 1 lifted / 0 not (a part laid by piece: a whole shingle
        course, a deck row, the eave strip)."""
        dz = np.zeros(x.shape)
        cp = math.cos(self.p)
        u = (self.Y - np.abs(y)) / cp
        for i, B in enumerate(self.BROWS):
            side = (y * B["sg"]) > 0
            if isinstance(brow, dict):
                s = brow.get(i)
            else:
                s = brow
            s = (u >= B["u_t"] - 1e-9).astype(float) if s is None else np.broadcast_to(np.asarray(s, float), x.shape)
            tt = np.clip((u - B["u_t"] - B["plat_u"]) / max(B["fade_u"], 1e-6), 0.0, 1.0)
            f = 1.0 - tt * tt * (3.0 - 2.0 * tt)
            dz = dz + B["height"] * self.brow_bell(B, x) * f * s * side
        return dz

    # ---- frames ------------------------------------------------------------------------------------------------
    def to_world(self, P, brow=None):
        """local -> world (warp included).  brow (kit 1.13, eyebrow roofs only): see _brow_dz."""
        P = np.asarray(P, float)
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        out = P.copy()
        out[..., 0] = self.origin[0] + c * P[..., 0] - s * P[..., 1]
        out[..., 1] = self.origin[1] + s * P[..., 0] + c * P[..., 1]
        if getattr(self, "warped", False) and P.shape[-1] >= 3:
            out[..., 2] = P[..., 2] + self.warp_z(P[..., 0], P[..., 1], brow=brow)
        return out

    def to_local(self, P, brow=None):
        P = np.asarray(P, float)
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        dx, dy = P[..., 0] - self.origin[0], P[..., 1] - self.origin[1]
        out = P.copy()
        out[..., 0] = c * dx + s * dy
        out[..., 1] = -s * dx + c * dy
        if getattr(self, "warped", False) and P.shape[-1] >= 3:
            out[..., 2] = P[..., 2] - self.warp_z(out[..., 0], out[..., 1], brow=brow)
        return out

    # ---- kit 1.12 (v5 round 2): the soft-line warp field ----------------------------------------------------------
    def warp_z(self, x, y, brow=None):
        """vertical offset (m) of the warped roof at local (x, y); 0 for a straight roof (see __init__).
        kit 1.13: plus the eyebrow bumps (brow: see _brow_dz; ignored without eyebrows)."""
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        dz = np.zeros(x.shape)
        if not getattr(self, "warped", False):
            return dz
        if getattr(self, "BROWS", None):
            dz = dz + self._brow_dz(x, y, brow)
        ay = np.abs(y)
        f_y = np.clip(1.0 - ay / self.Y, 0.0, 1.0)                    # 1 at the ridge, 0 at the lip
        if self.ridge_sag or self.eave_sag:
            hl = max(0.5 * (self.xb - self.xa), 1e-6)
            t = np.clip((x - 0.5 * (self.xa + self.xb)) / hl, -1.0, 1.0)
            dz -= (1.0 - t * t) * (self.ridge_sag * f_y + self.eave_sag * (1.0 - f_y))
        if self.eave_sweep:
            k = np.clip(1.0 - np.clip(self.Y - ay, 0.0, None) / max(self.sweep_len, 1e-6), 0.0, 1.0)
            dz += self.eave_sweep * k * k
        if self.verge_flare:
            for xe, free in ((self.xa, self.v0 > 0), (self.xb, self.v1 > 0)):
                if free:
                    k = np.clip(1.0 - np.abs(x - xe) / max(self.flare_len, 1e-6), 0.0, 1.0)
                    dz += self.verge_flare * k * k * f_y ** 1.5
        if self.wave:
            dz += self.wave * n2(x * 0.35, y * 0.30, self.wave_seed)
        return dz

    def under_z_world(self, P):
        """kit 1.12: deck underside height (WORLD z, warp included) over world plan points P (n, 2|3) -- what a wall
        under this roof stops at (the warped version of under_z(to_local(P)[:, 1]))."""
        P = np.atleast_2d(np.asarray(P, float))
        Q = np.zeros((len(P), 3))
        Q[:, :2] = P[:, :2]
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        dx, dy = Q[:, 0] - self.origin[0], Q[:, 1] - self.origin[1]
        xl, yl = c * dx + s * dy, -s * dx + c * dy
        return self.under_z(yl) + self.warp_z(xl, yl)

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

    # ---- round 3: the covering as a solid (keep-outs for the bodies it meets) ----------------------------------------
    def section_loop(self, n_arc=19):
        """closed (u, o) outline of one slope's whole roof section (deck underside, eave roll or plain eave edge, course
        envelope up to the ridge roll), lip -> ridge along the top, ridge -> lip along the deck underside."""
        T = self.T0 + 0.45 * self.step
        R = getattr(self, "ROLL", None)
        if R is not None:
            a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, n_arc)
            front = np.stack([R["u_c"] - R["Ru"] * np.cos(a), R["o_m"] + R["hh"] * np.sin(a)], 1)
            ut = np.linspace(R["u_c"], self.U, 40)[1:]
            ot = np.maximum(np.nan_to_num(self.roll_top_o(ut), nan=-1.0), T)
            top = np.concatenate([front, np.stack([ut, ot], 1)])
            bot = np.array([[self.U, -self.deck_t], [R["u_c"] + 0.07, -self.deck_t - 0.008]])
        else:
            top = np.array([[0.0, -self.deck_t], [0.0, T], [self.U, T]])
            bot = np.array([[self.U, -self.deck_t]])
        return np.concatenate([top, bot])

    def section_columns(self, dy=0.004):
        """vertical columns of the section (both slopes are mirror images): returns (ya, z_top, z_bot) over |y| = ya,
        the highest / lowest point of the roof solid (deck + covering + eave roll + ridge roll) in each column;
        -inf / +inf outside it.  Cached."""
        key = ("_cols", dy, tuple(sorted((getattr(self, "ROLL", None) or {}).items())), self.T0, self.step)
        if getattr(self, "_cols_key", None) == key:
            return self._cols
        L = self.section_loop()
        cp, sp = math.cos(self.p), math.sin(self.p)
        Y = self.Y - L[:, 0] * cp + L[:, 1] * sp
        Z = self.z_lip + L[:, 0] * sp + L[:, 1] * cp
        Y = np.maximum(Y, 0.0)
        ya = np.arange(0.0, float(Y.max()) + dy, dy)
        zt = np.full(len(ya), -np.inf)
        zb = np.full(len(ya), np.inf)
        n = len(Y)
        for i in range(n):
            y0, z0, y1, z1 = Y[i], Z[i], Y[(i + 1) % n], Z[(i + 1) % n]
            lo, hi = min(y0, y1), max(y0, y1)
            m = (ya >= lo) & (ya <= hi)
            if not m.any():
                continue
            t = (ya[m] - y0) / (y1 - y0) if abs(y1 - y0) > 1e-9 else np.zeros(int(m.sum()))
            z = z0 + (z1 - z0) * t
            zt[m] = np.maximum(zt[m], z)
            zb[m] = np.minimum(zb[m], z)
        zt = np.maximum(zt, np.where(np.isfinite(zt), self.top_z(ya), -np.inf))   # ridge roll
        self._cols_key, self._cols = key, (ya, zt, zb)
        return self._cols

    def keep_out(self, P, lift=0.02, x_pad=0.06, under=True):
        """round 3: P (n, 3) world -> bool per point: inside the roof solid or within `lift` m over its top, or (under=
        True) anywhere under it (the soffit, the eaves, the body below), in a vertical column of the roof's plan
        (x from xa - x_pad to xb + x_pad).  The keep-out a body meeting this roof (a cone, a turret) drops its
        units with (components.composite.cone_roof(abut_roof=...))."""
        L = self.to_local(np.asarray(P, float))
        ya, zt, zb = self.section_columns()
        ay = np.abs(L[:, 1])
        top = np.interp(ay, ya, zt, right=-np.inf)
        m = (L[:, 0] > self.xa - x_pad) & (L[:, 0] < self.xb + x_pad) & np.isfinite(top) & (L[:, 2] < top + lift)
        if not under:
            m &= L[:, 2] > np.interp(ay, ya, np.where(np.isfinite(zb), zb, 1e9))
        return m

    def top_depth(self, P, x_pad=0.06):
        """round 3: P world -> how far each point lies under the roof solid's top (m; negative above it, -inf outside
        the roof's plan columns)."""
        L = self.to_local(np.asarray(P, float))
        ya, zt, zb = self.section_columns()
        top = np.interp(np.abs(L[:, 1]), ya, zt, right=-np.inf)
        d = top - L[:, 2]
        inx = (L[:, 0] > self.xa - x_pad) & (L[:, 0] < self.xb + x_pad) & np.isfinite(top)
        return np.where(inx, d, -np.inf)

    def eave_zone(self, P):
        """round 3: P world -> bool: over the eave band (the eave roll and its buried tail, or the first 0.6 m of a
        plain covering), where a unit tucked into the covering would show through the eave's thin edge."""
        R = getattr(self, "ROLL", None)
        w = (R["u_c"] + R["L"]) if R is not None else 0.6
        L = self.to_local(np.asarray(P, float))
        return np.abs(L[:, 1]) > self.Y - w * math.cos(self.p)

    def under_soffit(self, P, x_pad=0.06, below=0.0):
        """round 3: P world -> bool: under the roof solid's lower outline (deck underside / eave-roll belly) by more
        than `below` m -- seen from below at the eaves."""
        L = self.to_local(np.asarray(P, float))
        ya, zt, zb = self.section_columns()
        ay = np.abs(L[:, 1])
        bot = np.interp(ay, ya, np.where(np.isfinite(zb), zb, -1e9), right=-1e9)
        return (L[:, 0] > self.xa - x_pad) & (L[:, 0] < self.xb + x_pad) & (L[:, 2] < bot - below)


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


def _ridge_cover_top(roof, T, x_v, inset=0.012, side=0.0):
    """round 5: the verge face's top polyline T [(y, z) eave -> ridge -> eave] raised to the ridge roll's section at
    the face plane x_v (the roll's FULL section, which the capped roll reaches just behind the face; its top `inset`
    inside the roll's outline, its sides `side` past the roll's flanks), so the face covers the roll's underside and
    no slot is left between the courses and the roll's side lip."""
    yc, zc = (float(v[0]) for v in _ridge_centre(roof, np.array([x_v])))
    fr, fh = roof.roll_w, roof.roll_h - inset
    fw = fr + side
    mid = np.flatnonzero((np.abs(T[:, 0] - yc) < fw + 0.03) & (np.abs(T[:, 0]) < 0.5 * roof.Y))
    if not len(mid) or fw <= 0:
        return T
    i0, i1 = int(mid[0]), int(mid[-1])
    seg = T[i0:i1 + 1]
    ys_seg, iu = np.unique(seg[:, 0], return_index=True)
    zs_seg = seg[iu, 1]
    ang = np.linspace(np.pi, 0.0, 19)
    ya = np.concatenate([[yc - fw], yc + fr * np.cos(ang), [yc + fw]])
    ys = np.unique(np.concatenate([ys_seg, ya]))
    ys = ys[(ys >= ys_seg[0]) & (ys <= ys_seg[-1])]
    z = np.interp(ys, ys_seg, zs_seg)
    inn = np.abs(ys - yc) <= fw                          # the roll's section, then a flat shoulder at its flanks
    za = zc + fh * np.sqrt(np.clip(1 - ((ys - yc) / fr) ** 2, 0, 1))
    z = np.where(inn, np.maximum(z, za), z)
    return np.concatenate([T[:i0], np.stack([ys, z], 1), T[i1 + 1:]])


def _verge_faces(roof, acc, verge, x_v, end, x_deck, roll_cover=0.012, ridge_cover=False):
    """one continuous, closed verge face per gable (round 2, director: no slots between the courses): a single
    polygon in the gable plane x = x_v from the deck underside up to the upper envelope of the eave roll and every
    course's end section, across both rakes and the ridge, plus a strip closing its foot back under the deck end
    (x_deck).  Faces outward (-x at end 0, +x at end 1).  roll_cover (round 3; None = round 2): the face's eave end
    also covers the eave roll's whole D section (inset this much inside the roll's outline), so the roll end and
    the verge face meet with no slot.  ridge_cover (round 5; with _ridge_roll(end_caps=...)): the face's ridge
    part also covers the capped ridge roll's section at the face plane (_ridge_cover_top)."""
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
        if roll_cover is not None:                         # the roll's D section: belly -> nose -> crest
            a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, 15)[:-1]
            us = np.concatenate([R["u_c"] - (R["Ru"] - roll_cover) * np.cos(a), us])
            env = np.concatenate([R["o_m"] + (R["hh"] - roll_cover) * np.sin(a), env])
        Pt = roof.surf(np.full(len(us), x_v), us, sg, env)
        tops[sg] = Pt[:, 1:]                               # (y, z) eave -> ridge
        yb0 = float(roof.surf(x_v, u_a, sg, o_b)[1])
        yb = np.linspace(yb0, 0.0, 24)
        bots[sg] = np.stack([yb, roof.ref_z(yb) + o_b / math.cos(p)], 1)   # eave -> ridge
        if roll_cover is not None:
            bots[sg] = np.concatenate([tops[sg][:1], bots[sg]])
    T = np.concatenate([tops[-1], tops[1][::-1]])
    if ridge_cover:
        T = _ridge_cover_top(roof, T, x_v)
    loop = np.concatenate([T, bots[1], bots[-1][::-1]])
    keep = np.concatenate([[True], np.linalg.norm(np.diff(loop, axis=0), axis=1) > 1e-4])
    loop = loop[keep]
    if np.linalg.norm(loop[-1] - loop[0]) < 1e-4:
        loop = loop[:-1]
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


def _eave_rolls(roof, acc, rng, x_lo, x_hi, seed=0, ends=None, bundles=None, end_caps=True):
    """the eave roll on both eaves: thatch.d_roll (the keep wing's D-roll sweep: +-1 cm swelling over 0.5-1 m, no
    pillows; bundles=thatch.d_roll bundles tuple binds it into long bundles at 4x the cost) along the lip with the
    GableRoof.eave_roll section, the buried back not modelled (drop_hidden).  ends[sg] = (x_from, x_to) local
    overrides (a roll that dies into another body stops where that body takes over); the free ends run 5 cm past
    the verge with a short round taper.  end_caps=True (round 3): the back is kept over the last 0.15 m of each free
    end, so the roll end is a closed rounded cap (no view into the open section past the verge face)."""
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
        kb = None
        if end_caps:
            lo_free = not (ends and sg in ends and ends[sg][0] is not None)
            hi_free = not (ends and sg in ends and ends[sg][1] is not None)

            def kb(Pw, lo_free=lo_free, hi_free=hi_free):
                x_ = roof.to_local(np.asarray(Pw, float))[:, 0]
                return (lo_free & (x_ < x_lo + 0.10)) | (hi_free & (x_ > x_hi - 0.10))
        P = d_roll(acc, path, prof, vis, seed + 11 * sg, rng, up=(0.0, 0.0, 1.0), var=0.010, taper=(ta, tb),
                   tmin=(0.75, 0.75), ribs=False, step=0.06, z_wave=0.008, drop_hidden=True,
                   bundles=bundles, calm_taper=True, round_end=True, keep_back_fn=kb)
        out[sg] = P
    return out


def _shingle_courses(roof, acc, rng, seed=0):
    """the kit's chunky shingles (SIZE_TABLE 'shingle' / 'starter') laid in straight courses on both slopes."""
    T = SIZE_TABLE["shingle"]
    e = 0.5 * (T["exposure"][0] + T["exposure"][1])
    K = int(math.ceil((roof.U - 0.15) / e))
    n_piece = 0
    for sg in (-1, 1):
        brows = [(bi, B) for bi, B in enumerate(getattr(roof, "BROWS", None) or ()) if B["sg"] == sg]
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
                force, L_i, bottom = None, L, k < 1
                if brows:                      # kit 1.13: a course is wholly on the lifted side of a bump or not
                    force = {}
                    for bi, B in brows:
                        force[bi] = 1.0 if k >= B["k_lip"] else 0.0
                        if xs[i + 1] > B["x"] - B["hw"] and xs[i] < B["x"] + B["hw"]:
                            if k < B["k_lip"] and ub + L_i > B["u_t"] - 0.01:
                                L_i = max(B["u_t"] - 0.01 - ub, 0.10)       # the head stops at the deck front
                            if k == B["k_lip"]:
                                bottom = True                                 # the wave's eave course is seen below
                Pl, F, uv = shingle_mesh(W, L_i, var, curl=var["curl_eave"] if k < 2 else var["curl"],
                                         bottom=bottom, head=True)
                v = np.clip(Pl[:, 1] / 0.72, 0, 1)
                wedge = 0.0 if k < 0 else (0.037 if k == 0 else 0.066)
                off = wedge * (1 - v) + Pl[:, 2] + rng.uniform(0, 0.01) * (1 - v)
                x = 0.5 * (xs[i] + xs[i + 1]) + Pl[:, 0]
                u = ub + Pl[:, 1] + rng.uniform(-0.01, 0.01)
                P = roof.surf(x, u, sg, off)
                Fl = [f[:, ::-1] if sg > 0 else f for f in F]      # the slope map has det = -sg
                Pw = roof.to_world(P) if force is None else roof.to_world(P, brow=force)
                if force is not None:          # kit 1.14: eyebrow(tilt=True) -- thickness along the bump's normal
                    tb = [bi for bi, B in brows if B.get("tilt") and force[bi] > 0
                          and xs[i + 1] > B["x"] - B["hw"] and xs[i] < B["x"] + B["hw"]]
                    if tb:
                        Pw = _brow_tilt(roof, sg, x, u, off, force, tb, Pw)
                acc.add(Pw, Fl, "M_roof_shingle", uv, wear=float(rng.uniform(0.2, 0.6)))
                n_piece += 1
    return n_piece


def _brow_tilt(roof, sg, x, u, off, force, tilt_ids, Pw, eps=0.01):
    """kit 1.14 (eyebrow(tilt=True)): re-lay a lifted shingle's thickness along the bumped surface's normal.  The
    vertical warp shears a piece on the bell's steep flanks (its thickness stays vertical, so it thins into a sliver);
    here each vertex moves by off x (n_bumped - n_unbumped) at its footprint (x, u): the piece keeps its footprint and
    its full thickness normal to the wave.  0 where the bump is flat (the correction vanishes outside the wave)."""
    off = np.asarray(off, float)
    s0 = {bi: (0.0 if bi in tilt_ids else v) for bi, v in force.items()}

    def nrm(s):
        def S(xx, uu):
            return roof.to_world(roof.surf(xx, uu, sg, 0.0), brow=s)
        n = np.cross(S(x + eps, u) - S(x - eps, u), S(x, u + eps) - S(x, u - eps))
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        return n * np.sign(n[..., 2:3])
    return Pw + off[..., None] * (nrm(force) - nrm(s0))


RIDGE_CAP = dict(past=0.045, cap_len=0.09, f_min=0.15)
"""round 5: the ridge roll's rounded free end -- it runs `past` m beyond the verge face and its section closes over
the last `cap_len` m as a quarter ellipse (a bound bundle end), never below f_min of the full section."""


def _ridge_centre(roof, xs):
    """the ridge roll's centre line (local y, z) at ridge coordinates xs (the gentle +-1.2 / 1.5 cm wander)."""
    xs = np.asarray(xs, float)
    return (0.012 * n2(xs * 0.8, np.zeros_like(xs), 77),
            roof.roll_centre_z() + 0.015 * n2(xs * 0.6, np.ones_like(xs), 78))


def _ridge_cap_scale(d, past=0.04, cap_len=0.16, f_min=0.15):
    """section scale of a capped ridge roll at distance d from its free end (quarter ellipse)."""
    t = np.clip(np.asarray(d, float) / cap_len, 0.0, 1.0)
    return np.maximum(f_min, np.sqrt(np.clip(1.0 - (1.0 - t) ** 2, 0.0, 1.0)))


def _ridge_roll(roof, acc, rng, x_from=None, end_caps=None):
    """thatch ridge roll: a rounded bundle along the ridge (closed sweep, ends capped at the verges).
    round 5: end_caps=dict(lo=x_face | None, hi=x_face | None) -- at each FREE end (its verge face plane given) the
    roll runs RIDGE_CAP["past"] m past the face and closes in a rounded end (_ridge_cap_scale) instead of a flat
    faceted disc; None = the old flat-capped sweep."""
    wr, hr = roof.roll_w, roof.roll_h
    a = np.linspace(0, np.pi, 11)
    top = np.stack([wr * np.cos(a), hr * np.sin(a)], 1)                 # right, up (CCW from +y side)
    bury = np.array([[-wr * 0.85, -0.10], [0.0, -0.16], [wr * 0.85, -0.10]])
    prof = np.concatenate([top, bury])
    x0_ = roof.xa - 0.02 if x_from is None else x_from
    x1_ = roof.xb
    if end_caps:
        lo, hi = end_caps.get("lo"), end_caps.get("hi")
        cp = RIDGE_CAP
        if lo is not None:
            x0_ = lo - cp["past"]
        if hi is not None:
            x1_ = hi + cp["past"]
    xs = np.linspace(x0_, x1_, max(4, int((x1_ - x0_) / 0.25) + 1))
    fs = np.ones(len(xs))
    if end_caps:
        extra = []
        if lo is not None:
            extra.append(x0_ + cp["cap_len"] * (1 - np.cos(np.linspace(0, 0.5 * np.pi, 8)[:-1])))
        if hi is not None:
            extra.append(x1_ - cp["cap_len"] * (1 - np.cos(np.linspace(0, 0.5 * np.pi, 8)[:-1])))
        xs = np.unique(np.concatenate([xs] + extra))
        fs = np.ones(len(xs))
        if lo is not None:
            fs = np.minimum(fs, _ridge_cap_scale(xs - x0_, **cp))
        if hi is not None:
            fs = np.minimum(fs, _ridge_cap_scale(x1_ - xs, **cp))
    yc, zc = _ridge_centre(roof, xs)
    path = np.stack([xs, yc, zc], 1)
    # sweep's profile axes: right = U x T, up = U; T = +x, U = +z -> right = -y; mirror the profile for +y
    prof_s = prof * np.array([-1.0, 1.0])
    if end_caps:
        V, F = sweep(path, (0, 0, 1), prof_s[::-1][None, :, :] * fs[:, None, None])
    else:
        V, F = sweep(path, (0, 0, 1), prof_s[::-1].copy())
    acc.add(roof.to_world(V), F, "M_thatch", wear=0.3)
    zc = roof.roll_centre_z()
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
    if getattr(roof, "warped", False):              # kit 1.12: the warp is curved across the slope; follow it
        us = np.unique(np.concatenate([us, np.linspace(0.0, roof.U, 13)]))
        xs = np.unique(np.concatenate([xs, np.linspace(roof.xa, roof.xb, max(2, int((roof.xb - roof.xa) / 0.25) + 1))]))
    xs0, us0 = xs, us
    for sg in (-1, 1):
        brows = [(bi, B) for bi, B in enumerate(getattr(roof, "BROWS", None) or ()) if B["sg"] == sg]
        span = [(bi, B) for bi, B in brows if B.get("span_rows")]
        if not span:
            _deck_slab(roof, acc, sg, xs0, us0, brows)
        else:                              # kit 1.14: eyebrow(span_rows=True) -- a closed patch over each bump only
            rest = [(bi, B) for bi, B in brows if not B.get("span_rows")]
            a = roof.xa
            for c0, c1, bi in sorted((max(B["x"] - B["hw"], roof.xa), min(B["x"] + B["hw"], roof.xb), bi)
                                     for bi, B in span):
                if c0 > a + 1e-6:
                    _deck_slab(roof, acc, sg, xs0, us0, rest, (a, c0))
                _deck_slab(roof, acc, sg, xs0, us0, rest + [(bi, roof.BROWS[bi])], (c0, c1))
                a = c1
            if a < roof.xb - 1e-6:
                _deck_slab(roof, acc, sg, xs0, us0, rest, (a, roof.xb))
        for bi, B in brows:
            _brow_eave_strip(roof, acc, sg, bi, B)


def _deck_slab(roof, acc, sg, xs, us, brows, x_rng=None):
    """one closed deck slab on side sg over the grid xs x us (kit 1.13: plus the tear rows / fine wave grid / framed
    opening of the eyebrows `brows`); kit 1.14: x_rng=(lo, hi) -- only the part of the roof between lo and hi along
    the ridge (its own closed ends), so _deck can build an eyebrow's fine patch separately from the plain deck."""
    t = roof.deck_t
    holes = []
    patch = x_rng is not None and any(B.get("span_rows") for _, B in brows)
    if x_rng is not None:
        lo, hi = x_rng
        inner = xs[(xs > lo + 1e-6) & (xs < hi - 1e-6)]
        xs = np.unique(np.concatenate([[] if patch else inner, [lo, hi]]))   # a patch takes only its own grid
    if brows:                              # kit 1.13: rows at each eyebrow's tear, a fine grid over its wave
        ex, eu = [xs], [us]
        for bi, B in brows:
            fine = bool(B.get("span_rows"))
            n_u = max(14, int((B["plat_u"] + B["fade_u"]) / 0.30) + 1) if fine else 14
            n_x = _brow_cols(B)
            eu.append(np.array([B["u_t"] - 1e-3, B["u_t"]]))
            eu.append(np.linspace(B["u_t"], B["u_t"] + B["plat_u"] + B["fade_u"], n_u))
            ex.append(np.linspace(B["x"] - B["hw"], B["x"] + B["hw"], n_x))
            h = _brow_hole(roof, B)
            if h is not None and (x_rng is None or (h[0] > lo and h[1] < hi)):
                ex.append(np.array(h))
                holes.append((bi, B, h))
        xs, us = np.unique(np.concatenate(ex)), np.unique(np.concatenate(eu))
        if x_rng is not None:
            xs = xs[(xs >= lo - 1e-9) & (xs <= hi + 1e-9)]
    X, Uu = np.meshgrid(xs, us, indexing="ij")
    top = roof.surf(X, Uu, sg, 0.0)
    bot = roof.surf(X, Uu, sg, -t)
    nx_, nu = X.shape
    V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
    off = nx_ * nu
    I = lambda i, j: i * nu + j  # noqa: E731
    skip = set()
    for bi, B, (h0, h1) in holes:      # the framed opening: the deck front is open behind the window
        j = int(np.argmin(np.abs(us - (B["u_t"] - 1e-3))))
        for i in range(nx_ - 1):
            if xs[i] >= h0 - 1e-9 and xs[i + 1] <= h1 + 1e-9:
                skip.add((i, j))
    F = []
    for i in range(nx_ - 1):
        for j in range(nu - 1):
            if (i, j) in skip:
                continue
            F.append((I(i, j), I(i + 1, j), I(i + 1, j + 1), I(i, j + 1)))
            F.append((off + I(i, j), off + I(i, j + 1), off + I(i + 1, j + 1), off + I(i + 1, j)))
        F.append((I(i, 0), off + I(i, 0), off + I(i + 1, 0), I(i + 1, 0)))          # eave edge
    for j in range(nu - 1):
        F.append((I(0, j), I(0, j + 1), off + I(0, j + 1), off + I(0, j)))           # verge ends
        F.append((I(nx_ - 1, j), off + I(nx_ - 1, j), off + I(nx_ - 1, j + 1), I(nx_ - 1, j + 1)))
    for (i, j) in skip:                # the opening's cut edges stay closed (deck thickness)
        if (i - 1, j) not in skip:
            F.append((I(i, j), I(i, j + 1), off + I(i, j + 1), off + I(i, j)))
        if (i + 1, j) not in skip:
            F.append((I(i + 1, j), off + I(i + 1, j), off + I(i + 1, j + 1), I(i + 1, j + 1)))
    F = np.array(F)
    q = V[F[0]]
    if float(np.cross(q[1] - q[0], q[3] - q[0]) @ roof.normal(sg)) < 0:
        F = F[:, ::-1]
    if brows:
        S = {bi: np.tile((Uu >= B["u_t"] - 1e-6).reshape(-1).astype(float), 2) for bi, B in brows}
        acc.add(roof.to_world(V, brow=S), F, "M_timber_weathered", wear=0.4)
    else:
        acc.add(roof.to_world(V), F, "M_timber_weathered", wear=0.4)


def _brow_cols(B):
    """the eyebrow's fine column count along the ridge: 25 (kit 1.13); kit 1.14 span_rows: ~every 0.15 m, >= 25."""
    return max(25, int(B["width"] / 0.15) + 1) if B.get("span_rows") else 25


def _brow_hole(roof, B):
    """kit 1.13: (x0, x1) local of the deck opening behind an eyebrow's window (None: a blind front)."""
    if not B.get("window"):
        return None
    w = float(B["window"].get("width", 0.56))
    return (B["x"] - 0.5 * w - 0.03, B["x"] + 0.5 * w + 0.03)


def _brow_eave_strip(roof, acc, sg, bi, B):
    """kit 1.13: the eyebrow's little eave -- a lifted board strip under its lowest course, from the course's butt
    line back to the deck front (u_lip .. u_t), deck underside up to just under the course butts, so no slot shows
    between the wave's eave and the deck front."""
    xs = np.linspace(B["x"] - B["hw"], B["x"] + B["hw"], _brow_cols(B))
    u0 = B["u_lip"] - 0.01
    if B.get("eave_inset"):                # kit 1.14: the board's front hides behind the wave's eave course
        u0 = min(u0 + float(B["eave_inset"]) / math.cos(roof.p), B["u_t"] - 0.03)
    us = np.array([u0, 0.5 * (u0 + B["u_t"]), B["u_t"]])
    X, Uu = np.meshgrid(xs, us, indexing="ij")
    top = roof.surf(X, Uu, sg, 0.055)
    bot = roof.surf(X, Uu, sg, -roof.deck_t)
    nx_, nu = X.shape
    V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
    off = nx_ * nu
    I = lambda i, j: i * nu + j  # noqa: E731
    F = []
    for i in range(nx_ - 1):
        for j in range(nu - 1):
            F.append((I(i, j), I(i + 1, j), I(i + 1, j + 1), I(i, j + 1)))
            F.append((off + I(i, j), off + I(i, j + 1), off + I(i + 1, j + 1), off + I(i + 1, j)))
        F.append((I(i, 0), off + I(i, 0), off + I(i + 1, 0), I(i + 1, 0)))
        F.append((I(i, nu - 1), I(i + 1, nu - 1), off + I(i + 1, nu - 1), off + I(i, nu - 1)))
    for j in range(nu - 1):
        F.append((I(0, j), I(0, j + 1), off + I(0, j + 1), off + I(0, j)))
        F.append((I(nx_ - 1, j), off + I(nx_ - 1, j), off + I(nx_ - 1, j + 1), I(nx_ - 1, j + 1)))
    F = np.array(F)
    q = V[F[0]]
    if float(np.cross(q[1] - q[0], q[3] - q[0]) @ roof.normal(sg)) < 0:
        F = F[:, ::-1]
    acc.add(roof.to_world(V, brow={bi: 1.0}), F, "M_timber", wear=0.5)


def _rafters(roof, acc, rng, spacing=0.62, skip=None, verge_apex=False):
    """rafter tails under the eave overhang (from 0.25 m inside the wall face to just behind the lip) and a verge
    rafter under each verge (seen from below and from the gable).
    round 5 (defaults = old behaviour): skip(P world) -> bool -- a rafter tail with any corner of its box marked is
    not built (e.g. the face of a round body the roof runs into: composite.inside_round with a negative depth), so no
    tail butts into or through another body's wall; verge_apex=True -- the two verge rafters run on past the ridge
    into a crossed (halved) apex, closing the pocket their short ends left under the deck at the gable apex."""
    t = roof.deck_t
    w, h = 0.11, 0.15
    xs = np.arange(roof.x0 + 0.25, roof.x1 - 0.1, spacing)
    n_skip = 0
    for sg in (-1, 1):
        nrm = roof.normal(sg)
        for x in xs:
            x_ = x + rng.uniform(-0.03, 0.03)
            u0 = 0.03
            u1 = (roof.ovh + 0.25) / math.cos(roof.p)
            p0 = roof.surf(x_, u0, sg, -t - h / 2)
            p1 = roof.surf(x_, u1, sg, -t - h / 2)
            if skip is not None:
                cn = np.array([roof.surf(x_ + dx, uu, sg, -t + dz) for dx in (-w / 2, w / 2) for uu in (u0, u1)
                               for dz in (0.0, -h)])
                if np.asarray(skip(roof.to_world(cn)), bool).any():
                    n_skip += 1
                    continue
            beam(acc, roof.to_world(p0), roof.to_world(p1), w, h, 0.012, "M_timber", up=roof.dir_world(nrm))
        for xe, ve in ((roof.x0, roof.v0), (roof.x1, roof.v1)):
            if ve <= 0:
                continue
            xv = xe - ve + 0.07 if xe == roof.x0 else xe + ve - 0.07
            p0 = roof.surf(xv, 0.0, sg, -t - h / 2)
            p1 = roof.surf(xv, roof.U + (0.03 if verge_apex else -0.05), sg, -t - h / 2)
            beam(acc, roof.to_world(p0), roof.to_world(p1), w, h, 0.012, "M_timber_weathered", up=roof.dir_world(nrm))
    if n_skip:
        log(f"  {roof.name} rafters: {n_skip} tails skipped (they would run into another body)")


VERGE_BOARD = dict(t=0.045, below=0.07, above=0.05, gap=0.005, foot_curl=0.05, n_u=None)
"""kit 1.12 (v5 round 2; folded from the retired timber_roof.verge_boards, WITHOUT its crossed horns): the bargeboard
of a free verge -- thickness t, from `below` m under the deck to `above` m over the covering top, `gap` off the
covering's end, mitred on the ridge plane; foot_curl: its eave foot turns up this much over the last 0.4 m (a soft,
rolled foot, note 17).  It is laid in the roof's local frame, so it follows the roof's warp (sag / sweep / flare)."""


def _verge_boards(roof, acc, rng, ends=None, t=0.045, below=0.07, above=0.05, gap=0.005, foot_curl=0.05, n_u=None):
    """bargeboards on the free verges (see VERGE_BOARD); returns the number of boards."""
    o_bot = -roof.deck_t - below
    o_top = float(getattr(roof, "T0", 0.06)) + above
    cp, sp_ = math.cos(roof.p), math.sin(roof.p)
    ends = ends or tuple(e for e, v in (("lo", roof.v0), ("hi", roof.v1)) if v > 0)
    n = 0
    for end in ends:
        xe = roof.xa if end == "lo" else roof.xb
        sx = -1.0 if end == "lo" else 1.0
        for sg in (-1, 1):
            u_end = lambda o: (roof.Y + o * sp_) / cp  # noqa: E731  the ridge plane (mitre) at offset o
            nu = n_u or max(8, int(roof.U / 0.20) + 2)
            us = np.linspace(-0.03, u_end(o_top) + 0.01, nu)
            ring = []
            for (dx, o) in ((0.0, o_bot), (0.0, o_top), (t, o_top), (t, o_bot)):
                x = xe + sx * (gap + dx)
                uu = np.minimum(us, u_end(o))
                curl = foot_curl * np.clip(1.0 - (uu + 0.03) / 0.40, 0.0, 1.0) ** 2
                ring.append(roof.surf(np.full(nu, x), uu, sg, np.full(nu, o) + curl))
            V = np.stack(ring, 1).reshape(-1, 3)                       # (nu * 4)
            F = []
            for i in range(nu - 1):
                for j in range(4):
                    a, b = i * 4 + j, i * 4 + (j + 1) % 4
                    F.append((a, b, b + 4, a + 4))
            F = [np.array(F), np.array([[3, 2, 1, 0]]), np.array([[(nu - 1) * 4 + j for j in range(4)]])]
            q = V[np.array(F[0][0])]
            ctr = V[:8].mean(0)                                         # the board's centre at its first station
            if float(np.cross(q[1] - q[0], q[3] - q[0]) @ (q.mean(0) - ctr)) < 0:
                F = [f[:, ::-1] for f in F]
            acc.add(roof.to_world(V), F, "M_timber", wear=float(rng.uniform(0.3, 0.6)))
            n += 1
    return n


def _apex_finials(g, roof, pre, ends=None, hat_r=0.24, hat_pitch_deg=44.0, scale=0.55, lean_deg=1.0, seed=7):
    """kit 1.12 (v5 round 2, note 16): the village finial on a gable apex -- the keep's turned / spike finial
    (finial.turned_finial) over a fitted lead hat (finial.lead_hat, its drip fitted over the comb / covering / verge
    board vertices under it), at every free verge apex.  -> <P>_<roof>_apex_cap_collar (M_lead), _apex_finial."""
    import bpy
    from .finial import lead_hat, turned_finial
    ends = ends or tuple(e for e, v in (("lo", roof.v0), ("hi", roof.v1)) if v > 0)
    cover = []
    for part in ("covering", "comb", "verge"):
        ob = bpy.data.objects.get(f"{pre}_{part}")
        if ob is not None and ob.type == "MESH" and len(ob.data.vertices):
            co = np.zeros(len(ob.data.vertices) * 3)
            ob.data.vertices.foreach_get("co", co)
            cover.append(co.reshape(-1, 3))
    cover = np.concatenate(cover) if cover else np.zeros((0, 3))
    hat, fin = Acc(pre + "_apex_cap_collar", 50.0), Acc(pre + "_apex_finial", 45.0)
    rng = np.random.default_rng(seed)
    tips = []
    for end in ends:
        xe = roof.xa if end == "lo" else roof.xb
        sx = -1.0 if end == "lo" else 1.0
        x_c = xe + sx * 0.02
        c = roof.to_world(np.array([[x_c, 0.0, roof.ref_z(0.0)]]))[0]
        near = cover[np.hypot(cover[:, 0] - c[0], cover[:, 1] - c[1]) < hat_r + 0.05] if len(cover) else cover
        z_apex = (float(near[:, 2].max()) if len(near) else c[2] + 0.2) + 0.01
        h0 = hat_r * math.tan(math.radians(hat_pitch_deg))
        z_top = lead_hat(hat, c[0], c[1], z_apex, hat_r, h0, seg=28, cover=near if len(near) else None, clear=0.015)
        ld = rng.uniform(0, 2 * math.pi)
        turned_finial(fin, (c[0], c[1], z_top - 0.01), scale=scale, lean_deg=lean_deg,
                      lean_dir=(math.cos(ld), math.sin(ld)), seg=24)
        tips.append(z_top - 0.01 + 1.45 * scale)
    finalize(hat, g.coll, smooth_deg=50.0)
    finalize(fin, g.coll, smooth_deg=45.0)
    log(f"  {pre}: apex finials on {len(ends)} gable(s), tips {', '.join(f'{z:.2f}' for z in tips)}")
    return tips


def _roof_edges(g, roof, pre, rng, clip, verge, apex_finial):
    """kit 1.12: the optional verge board and apex finials of a linear roof (see linear_roof)."""
    if verge == "board":
        acc = Acc(pre + "_verge", 30)
        kw = dict(VERGE_BOARD)
        kw.update(getattr(roof, "verge_kw", None) or {})
        n = _verge_boards(roof, acc, rng, **kw)
        if clip is not None:
            acc.cull = clip
        finalize(acc, g.coll, smooth_deg=30.0)
        log(f"  {pre}: {n} verge boards")
    elif verge is not None:
        raise ValueError(f"linear_roof: verge {verge!r}; None or 'board'")
    if apex_finial == "turned":
        _apex_finials(g, roof, pre)
    elif apex_finial is not None:
        raise ValueError(f"linear_roof: apex_finial {apex_finial!r}; None or 'turned'")


def _eyebrow_fronts(g, roof, pre):
    """kit 1.13: the short timber front of every eyebrow (GableRoof(eyebrows=...)): a sill beam on the slope, rough
    vertical boards with battens rising to the wave's eave strip (clamped to it, so the front is the wave's arch),
    a closed backing over the deck front, end posts, and the kit window (components.openings.window, timber host:
    wall_openings.build_opening) with its dark room sized to stay under the wave.  The timber family's own
    pieces (timber_walls._clad / _sheet / wbox), so it reads as the village's timber."""
    from .openings import window as _window
    from .timber_walls import STYLES, _clad, _opening_layout, _sheet, resolve_timber, rough_opts, wbox
    from .wall_openings import build_opening, finish_accs, opening_accs
    st = STYLES["board_batten"]
    out = []
    for i, B in enumerate(roof.BROWS):
        rng = np.random.default_rng(9100 + 17 * i + int(B["seed"]))
        sg = B["sg"]
        d_f = B["d_t"] - B["set_back"]
        y_f = sg * (roof.Y - d_f)
        uz, rz = float(roof.under_z(y_f)), float(roof.ref_z(y_f))

        def z_up(x, i=i, y_f=y_f, uz=uz):
            return uz + float(roof.warp_z(np.array([x]), np.array([y_f]), brow={i: 1.0})[0]) + 0.02

        def z_dn(x, i=i, y_f=y_f, rz=rz):
            return rz + float(roof.warp_z(np.array([x]), np.array([y_f]), brow={i: 0.0})[0])
        xg = np.linspace(B["x"] - B["hw"], B["x"] + B["hw"], 201)
        zd = np.array([z_dn(x) for x in xg])
        zu = np.array([z_up(x) for x in xg])
        ok = (zu - zd) >= B["min_front"]
        ic = int(np.argmin(np.abs(xg - B["x"])))
        if not ok[ic]:
            raise ValueError(f"eyebrow {i}: no front (height {B['height']:.2f} m is under min_front)")
        a = ic
        while a > 0 and ok[a - 1]:
            a -= 1
        b = ic
        while b < len(xg) - 1 and ok[b + 1]:
            b += 1
        x_lo, x_hi = float(xg[a]), float(xg[b])
        z0 = float(zd[a:b + 1].min()) - 0.02
        floor = z0 + 0.09
        tl = -float(sg)                                   # walk so the front's outside (downslope) is on the right
        x_O = x_hi if tl < 0 else x_lo
        L = x_hi - x_lo
        O = roof.to_world(np.array([[x_O, y_f]]))[0]
        O = np.array([O[0], O[1], 0.0])
        t_w = roof.dir_world(np.array([tl, 0.0, 0.0]))
        n_w = roof.dir_world(np.array([0.0, float(sg), 0.0]))
        F = (O, t_w, n_w)

        def rake(s, x_O=x_O, tl=tl, z_up=z_up):
            return z_up(x_O + tl * s)
        tag = f"{roof.name}_eyebrow{i}"
        accs = dict(frame=Acc(f"{g.prefix}_{tag}_frame"), boards=Acc(f"{g.prefix}_{tag}_boards"),
                    back=Acc(f"{g.prefix}_{tag}_blocker"))
        oaccs = opening_accs(g, tag)
        wbox(accs["frame"], F, 0.0, L, z0, floor, -0.10, 0.0, "M_timber", r=0.012, ns=max(4, int(L / 0.3) + 2))
        for (pa, pb) in ((0.0, 0.08), (L - 0.08, L)):
            zt = max(rake(pa), rake(pb))
            wbox(accs["frame"], F, pa, pb, z0, zt, -0.10, 0.04, "M_timber", r=0.012, nz=6, clamp=rake)
        if B.get("close_ends"):            # kit 1.14: a closing board past each end post, under the wave's flank
            gap = zu - zd
            a2, b2 = a, b
            while a2 > 0 and gap[a2 - 1] >= 0.02:
                a2 -= 1
            while b2 < len(xg) - 1 and gap[b2 + 1] >= 0.02:
                b2 += 1
            for xa_, xb_ in ((float(xg[a2]), x_lo + 0.04), (x_hi - 0.04, float(xg[b2]))):
                if xb_ - xa_ < 0.06:
                    continue
                sa, sb = sorted(((xa_ - x_O) / tl, (xb_ - x_O) / tl))
                zb = float(min(z_dn(xa_), z_dn(xb_))) - 0.03
                zt = max(rake(s) for s in np.linspace(sa, sb, 9))
                wbox(accs["frame"], F, sa, sb, zb, zt, -0.07, 0.02, "M_timber", r=0.008,
                     ns=max(4, int((sb - sa) / 0.04) + 2), nz=4, clamp=lambda s, rake=rake: rake(s) - 0.005)
        blocks, clears = [], []
        s_c = (B["x"] - x_O) / tl
        if B.get("window"):
            wk = dict(shutters=False, jamb=(0.08, 0.14), head=0.08, rail=0.06, frame=0.045, room=0.45,
                      room_pad=(0.05, 0.10, 0.04))
            wk.update(B["window"])
            ww, wh, wsill = wk.pop("width"), wk.pop("height"), wk.pop("sill")
            sp = resolve_timber(_window(width=ww, height=wh, sill=wsill, **wk))
            clear, block = _opening_layout(sp, s_c, floor, st)
            top_min = min(rake(s) for s in np.linspace(block[0], block[1], 9))
            if block[3] > top_min - 0.02:
                raise ValueError(f"eyebrow {i}: the window head {block[3]:.2f} is above the wave's eave "
                                 f"{top_min:.2f}; raise height or lower the window")
            blocks.append(block)
            clears.append(clear)
            build_opening(g, sp, O + s_c * t_w, t_w, n_w, oaccs, rng, label=tag,
                          host=dict(face=st["board"][1], floor=floor, head_max=None, casing=True, ground=0.0))
        z_top = max(rake(s) for s in np.linspace(0.0, L, 41))
        _clad(accs, F, L, floor - 0.04, z_top, st, [(0.0, 0.08), (L - 0.08, L)], blocks, rng, rake,
              rough=rough_opts(True))
        ss = sorted(set([0.0, L] + list(np.arange(0.08, L, 0.08)) + [c for cl in clears for c in (cl[0], cl[1])]))
        zz = sorted(set([floor - 0.03, z_top] + [c for cl in clears for c in (cl[2], cl[3])]))

        def keep(ia, ib, ss=ss, zz=zz, clears=clears):
            sm, zm = 0.5 * (ss[ia] + ss[ia + 1]), 0.5 * (zz[ib] + zz[ib + 1])
            return not any(c[0] < sm < c[1] and c[2] < zm < c[3] for c in clears)
        _sheet(accs["back"], F, np.array(ss), np.array(zz), keep, -0.03, 0.0, "M_timber_weathered",
               clamp=lambda s, rake=rake: rake(s) - 0.01)
        for a_ in accs.values():
            if a_.n:
                finalize(a_, g.coll, smooth_deg=30.0)
        finish_accs(g, oaccs)
        out.append(dict(x=(x_lo, x_hi), z0=z0, top=z_top, d_front=B["d_t"], u_t=B["u_t"]))
        log(f"  {pre}: eyebrow {i} at x {B['x']:.2f} (side {sg:+d}): front {L:.2f} m wide, sill {z0:.2f}, "
            f"eave {z_top:.2f} (world z before recentre), lift {B['height']:.2f} m over {B['width']:.2f} m")
    roof.EYEBROW_FRONTS = out
    return out


def linear_roof(g, roof, covering="thatch", clip=None, seed=71, comb=True, abut_cone=None, thatch_style="courses",
                abut_wall_in=0.10, rafter_skip=None, ridge_caps=False, verge_apex=False, verge=None,
                apex_finial=None):
    """KIT COMPONENT: a straight gable roof from its GableRoof spec (see module doc).  clip(P_world, margin=0) -> bool
    marks vertices inside another body; faces wholly inside are dropped from the covering, ridge, comb and rafters,
    and deck faces more than 10 cm inside it.  abut_cone=(cx, cy): the roof runs into the cone of the round frame g
    centred there: dropped where it is under the cone's covering AND inside the round wall head (g.R_WALL -
    abut_wall_in; None = under the cone only, the round-1 rule), so under the cone's eave overhang the roof runs on
    (deck, eave roll, courses) and dies into the round wall instead of leaving a pocket under the oversailing eave.
    thatch_style: "courses" (round 2 default: continuous layered courses + thatch.d_roll eave roll + one closed
    verge face per gable) or "clumps" (round 1).  Publishes the spec on g.LINEAR_ROOFS[roof.name].
    round 5 (defaults = round 4): rafter_skip(P world) -> bool -- rafter tails reaching into another body (e.g. the
    round wall a roof runs into: composite.inside_round(..., depth=-0.04)) are not built (_rafters(skip=...));
    ridge_caps=True ("courses" thatch) -- the ridge roll gets a rounded end <= 5 cm past each free verge face and the
    verge face covers the roll's section there (_ridge_roll(end_caps=...), _verge_faces(ridge_cover=True));
    verge_apex=True -- the verge rafters meet in a crossed apex (no pocket under the deck at the gable apex).
    kit 1.12 (v5 round 2; defaults = old): verge="board" -- a bargeboard on every free verge (VERGE_BOARD, folded
    from the retired timber_roof.verge_boards; it follows the roof's warp, so a GableRoof(verge_flare=...) gives the
    curved, apex-flared bargeboard), -> <P>_<roof>_verge; apex_finial="turned" -- the village's turned / spike
    finial over a fitted lead hat on every free gable apex (_apex_finials).  The soft-line options themselves (ridge
    sag, eave sweep / bell-cast, verge flare, out-of-true wave) are GableRoof parameters."""
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
    if getattr(roof, "BROWS", None) and covering != "shingle":
        raise ValueError("linear_roof: GableRoof(eyebrows=...) is built for covering='shingle' only (kit 1.13)")
    if covering == "thatch" and thatch_style == "courses":
        out = _linear_roof_courses(g, roof, clip, rng, seed, comb, rafter_skip=rafter_skip, ridge_caps=ridge_caps,
                                   verge_apex=verge_apex)
        if verge is not None or apex_finial is not None:
            _roof_edges(g, roof, f"{g.prefix}_{roof.name}", rng, clip, verge, apex_finial)
        return out
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
    if rafter_skip is not None or verge_apex:          # kit 1.12: the round-5 options on the plain path too
        _rafters(roof, raf, rng, skip=rafter_skip, verge_apex=verge_apex)
    else:
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
    if verge is not None or apex_finial is not None:
        _roof_edges(g, roof, pre, rng, clip, verge, apex_finial)
    if getattr(roof, "BROWS", None):
        _eyebrow_fronts(g, roof, pre)
    return roof


def _linear_roof_courses(g, roof, clip, rng, seed, comb, rafter_skip=None, ridge_caps=False, verge_apex=False):
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
    _rafters(roof, raf, rng, skip=rafter_skip, verge_apex=verge_apex)
    if clip is not None:
        raf.cull = clip
    finalize(raf, g.coll, smooth_deg=30.0)
    # the covering runs 4 cm past the deck at a free verge (the verge face covers the deck end)
    x_lo = roof.xa - 0.04 if roof.v0 > 0 else roof.xa
    x_hi = roof.xb + 0.04 if roof.v1 > 0 else roof.xb
    cov = Acc(pre + "_covering", 60)
    n_c, verge = _layered_courses(roof, cov, rng, x_lo, x_hi, seed=seed)
    if roof.v0 > 0:
        _verge_faces(roof, cov, verge, x_lo, 0, roof.xa + 0.02, ridge_cover=ridge_caps)
    if roof.v1 > 0:
        _verge_faces(roof, cov, verge, x_hi, 1, roof.xb - 0.02, ridge_cover=ridge_caps)
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
    if ridge_caps:
        _ridge_roll(roof, rid, rng, end_caps=dict(lo=x_lo if roof.v0 > 0 else None,
                                                  hi=x_hi if roof.v1 > 0 else None))
    else:
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
