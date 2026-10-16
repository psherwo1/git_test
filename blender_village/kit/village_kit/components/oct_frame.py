"""components.oct_frame -- the frame `g` of a tiered octagonal hall building (the hilltop keep and its kin):

    octagonal battered rubble hall (apothem A0, wall WALL_H) with engaged corner posts and an eave plate
    -> tier 1: bell-cast octagonal skirt roof (SKIRT, an OctRoof) -> tier 2: shake collar (COLLAR_*)
    -> tier 3: concave stone cone (CONE_Z / CONE_R, top CONE_TOP) -> lantern belt (LANT_*) -> tier 4: bell cap (CAP)
    -> turned finial; a rectangular annex (wing: WX_W..WX_E x WY_S..WY_N, wall W_WALL_H) under a hipped thatch roof
    (W_PITCH, W_OVH, CORE_T) and an engaged round side turret (TUR_C, TUR_SCALE) with a corbelled cushion (CUSH),
    a board drum and its own bell cap (TUR_CAP).

OctFrame(prefix, **params) holds the building's ONE dimension table (PARAMS documents every key and its default)
and everything derived from it (derive()).  The components of this family (oct_hall, oct_roof, stone_cone, annex,
thatch, turret, plank_doors, windows, oct_decals) are functions component(g, ...); they read the frame's dimensions
and the envelope functions below (apo, hall_map, fmap, wing_map, tur_dist, skirt_z_at, q_rr, wing_under, ...)
through the module proxy FR, which always points at the frame being built (activate()).  One frame is active at a
time (a build is one process); the dimension table itself is the frame object, not module globals.

Surface conventions: facets k = 0..7 of the hall run CCW from NW (0 NW, 1 W, 2 SW, 3 S = door, 4 SE, 5 E, 6 NE,
7 N); fmap(k, x, z, w) is the plumb facet frame (x along the facet CCW, z up, w out of the plane at A_REF).
"""
import math

import numpy as np

from ..assembly import Building
from ..core import DetailRule
from ..geom import CLIP_Z, TAN22, fbm90, n1, vnoise90  # noqa: F401

FPHI = [math.radians(135 + 45 * k) for k in range(8)]
FN = [np.array([math.cos(p), math.sin(p)]) for p in FPHI]
FT = [np.array([-math.sin(p), math.cos(p)]) for p in FPHI]

# turret body profile (z, r) at TUR_SCALE 1 (ref1, director round 3): flank leans ~24 deg where it leaves the wing
# eave, easing to ~8 deg under the cushion; below the eave a D 4.7 base bulging out of the wing's N and W walls
_TPZ = np.array([-0.3, 0.0, 1.3, 2.6, 3.5, 4.5, 5.4, 5.9, 6.1])
_TPR = np.array([2.385, 2.38, 2.365, 2.35, 1.95, 1.55, 1.32, 1.25, 1.24])
# concave stone cone profile (z, r) from the skirt to the lantern sole at CONE_TOP = 9.6
_CONE_Z = np.array([4.4, 5.2, 6.0, 6.6, 7.35, 8.2, 9.0, 9.6])
_CONE_R = np.array([3.12, 2.92, 2.68, 2.30, 1.90, 1.56, 1.36, 1.25])

PARAMS = dict(
    # hall
    A0=4.0,                  # outer apothem at ground (8.0 m across the flats)
    WALL_H=3.45,             # wall top / eave plate seat
    BATTER_DEG=2.0,          # wall batter
    BULGE=0.04,              # convex bulge of each facet
    OPENINGS=None,           # hall openings (None: the keep's door, SW window, W slit, E / NE windows)
    # tiers
    CONE_TOP=9.6,            # top of the stone cone = lantern sole (the cone profile above the collar stretches)
    LANT_H=0.95,             # lantern belt height
    # west wing (annex) and its thatch
    WX_W=-10.0, WX_E=-1.3, WY_S=0.4, WY_N=4.6,
    W_WALL_H=2.55, W_PITCH_DEG=47.0, W_OVH=0.55, CORE_T=0.30,
    WDOOR=None, WWIN=None,   # annex door / window specs (plank_doors.door_spec / windows.window_spec)
    # side turret
    TUR_C=(-8.55, 2.70), TUR_SCALE=1.0, TUR_Z_TOP=5.92,
    # producer note 11
    detail_rule=True,
    seed_offset=0,           # added to the masonry layout seeds (a variant gets its own stones)
)

DEFAULT_OPENINGS = [
    dict(name="door", k=3, xc=0.35, kind="arch", hw=0.525, z0=0.12, zs=1.77, depth=0.30),
    dict(name="win_sw", k=2, xc=0.0, kind="rect", hw=0.47, z0=1.24, z1=2.38, depth=0.09, frame=True, surround="timber"),
    dict(name="slit_w", k=1, xc=0.62, kind="rect", hw=0.09, z0=1.45, z1=2.05, depth=0.30, frame=False),
    dict(name="win_e", k=5, xc=-0.25, kind="rect", hw=0.25, z0=1.42, z1=2.02, depth=0.30, frame=True),
    dict(name="win_ne", k=6, xc=0.2, kind="rect", hw=0.25, z0=1.42, z1=2.02, depth=0.30, frame=True),
]

CUSH0 = dict(r_body=1.25, z_base=5.92, r_drum=1.15, z_top_drum=6.575, droop_dir=math.radians(-25.0), droop=0.12,
             proj_lo=(0.12, 0.23), proj_up=(0.15, 0.43), h_lo=(0.25, 0.29), stone_len=(0.35, 0.70), joint=0.025,
             weather_deg=10.0, lip_droop=0.15, seed=2323)
TURCAP0 = dict(p_lip=1.65, z_lip=7.10, d_pts=[0, 0.25, 0.45, 1.65], a_pts=[22, 32, 46, 47], p_min=0.02, kick=0.03,
               kick_len=0.45, wave=0.008, sag=0.012, seed=13, rot_deg=8.0)


# =================================================================================================================
# the active-frame proxy
# =================================================================================================================
_CUR = [None]


class _Proxy:
    """FR.<name> reads / writes the attribute of the frame being built."""

    def __getattr__(self, k):
        g = _CUR[0]
        if g is None:
            raise RuntimeError("no OctFrame is active")
        return getattr(g, k)

    def __setattr__(self, k, v):
        setattr(_CUR[0], k, v)


FR = _Proxy()


def activate(g):
    _CUR[0] = g
    return g


class OctRoof:
    """octagonal bell-cast roof surface about (cx, cy): eave lip at apothem p_lip / height z_lip, pitch profile
    a_pts (deg) at the distances d_pts in from the lip, up to p_min; kick (upturn at the hip corners over kick_len),
    low-frequency eave wave, sag between the hips, rot_deg plan rotation.  Facet k's outward normal is at
    rot + 45 k deg; surf(k, x, p) / world(k, x, p, h) map facet coordinates (x along the facet, p apothem, h along
    the surface normal) to world."""

    def __init__(self, cx, cy, p_lip, z_lip, d_pts, a_pts, p_min, kick=0.0, kick_len=1.0, wave=0.0,
                 sag=0.0, seed=1, rot_deg=0.0):
        self.c = np.array([cx, cy], float)
        self.p_lip = p_lip
        d = np.linspace(0, p_lip - p_min, 600)
        th = np.radians(np.interp(d, d_pts, a_pts))
        tz = np.tan(th)
        z = z_lip + np.concatenate([[0], np.cumsum(0.5 * (tz[1:] + tz[:-1]) * np.diff(d))])
        m = np.concatenate([[0], np.cumsum(np.sqrt(1 + (0.5 * (tz[1:] + tz[:-1])) ** 2) * np.diff(d))])
        self.Pp, self.Zp, self.Mp = p_lip - d, z, m
        self.kick, self.kick_len, self.wave, self.sag, self.seed = kick, kick_len, wave, sag, seed
        self.D = p_lip - p_min
        self.rot = math.radians(rot_deg)
        self.phi = [self.rot + math.radians(45 * k) for k in range(8)]

    def zb(self, p):
        return np.interp(-np.asarray(p, float), -self.Pp, self.Zp)

    def p_of_m(self, m):
        return np.interp(m, self.Mp, self.Pp)

    def m_of_p(self, p):
        return np.interp(-np.asarray(p, float), -self.Pp, self.Mp)

    def surf(self, k, x, p):
        k = np.asarray(k).astype(np.int64)
        x = np.asarray(x, float)
        p = np.asarray(p, float)
        phi = np.asarray(self.phi)[k]
        nx_, ny_ = np.cos(phi), np.sin(phi)
        X = self.c[0] + p * nx_ - x * ny_
        Y = self.c[1] + p * ny_ + x * nx_
        d = self.p_lip - p
        xr = np.clip(np.abs(x) / np.maximum(p * TAN22, 1e-3), 0, 1)
        z = self.zb(p)
        z = z + self.kick * xr ** 3 * np.clip(1 - d / self.kick_len, 0, 1) ** 2
        ang = phi + np.arctan2(x, np.maximum(p, 1e-3))
        z = z + self.wave * n1(ang * 2.2, self.seed) * np.clip(1 - d / (0.8 * self.D), 0.2, 1)
        z = z - self.sag * (1 - xr ** 2) * np.sin(np.pi * np.clip(d / self.D, 0, 1))
        return np.stack([X, Y, z], -1)

    def world(self, k, x, p, h):
        e = 1e-3
        S0 = self.surf(k, x, p)
        dx = self.surf(k, np.asarray(x) + e, p) - S0
        dp = self.surf(k, x, np.asarray(p) - e) - S0      # upslope
        N = np.cross(dx, dp)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        return S0 + np.asarray(h, float)[..., None] * N


class OctFrame(Building):
    """the frame of a tiered octagonal hall building (see the module doc and PARAMS)."""

    def __init__(self, prefix="KEEP", **params):
        super().__init__(prefix)
        unknown = set(params) - set(PARAMS)
        if unknown:
            raise KeyError(f"unknown OctFrame parameters {sorted(unknown)}")
        p = dict(PARAMS)
        p.update(params)
        for k, v in p.items():
            setattr(self, k, v)
        self.TUR_C = np.asarray(self.TUR_C, float)
        self.OPENINGS = [dict(o) for o in (self.OPENINGS or DEFAULT_OPENINGS)]
        self.WDOOR = dict(self.WDOOR or dict(xc=-5.05, hw=0.50, z0=0.10, z1=2.20, fw=0.18, depth=0.20))
        self.WWIN = dict(self.WWIN or dict(xc=-7.4, hw=0.225, z0=1.30, z1=1.85, depth=0.16, fw=0.07))
        self.CUSH = dict(CUSH0)
        self.hygiene = False
        self.subs = {}
        # state the components publish to each other while the building is built
        self.DRESSED_POLYS = {k: [] for k in range(8)}
        self.JOINT_ACC = None
        self.EAVE_RUNS = []
        self.RIDGE_PATH = None
        self.HIP_ENDS = []
        self.POOL_SPECS = {}
        self.dropped_checks = []          # note 11: timber checks no longer modelled -> crack anchors
        activate(self)
        self.derive()

    # -------------------------------------------------------------------------------------------------------------
    def derive(self):
        """(re)derive every table that depends on the parameters (kit_set convention: call after any change)."""
        activate(self)
        from .thatch import roll_top_mh
        g = self
        g.BAT = math.tan(math.radians(g.BATTER_DEG))
        g.A_REF = g.A0 - 0.01                  # plumb reference plane for joinery in openings
        g.INNER_APO = g.A0 - 0.70              # inner wall face (0.7 m wall)
        # hall timber frame
        g.R_POST = g.A0 + 0.30
        g.PLATE_APO = g.A0 - 0.07
        g.PLATE_W, g.PLATE_H = 0.25, 0.30
        g.PLATE_TOP = g.WALL_H + g.PLATE_H
        g.RPLATE_H = 0.20
        g.RAFTER_SEAT = g.PLATE_TOP + g.RPLATE_H
        g.OT, g.OP, g.ON, g.OB, g.L1 = build_outline(g.A0)
        # tier 1 skirt (eave lip 1.25 m beyond the wall face) and tier 2 collar
        g.SKIRT = OctRoof(0.0, 0.0, p_lip=g.A0 + 1.25, z_lip=g.WALL_H + 0.285, d_pts=[0, 0.4, 0.8, 1.2, 3.25],
                          a_pts=[25, 31, 37, 38, 39], p_min=2.0, kick=0.022, kick_len=0.8, wave=0.022, sag=0.03,
                          seed=3)
        g.SKIRT_SHEATH = 0.025
        g.COLLAR_P = 3.62
        g.COLLAR_TOP_Z, g.COLLAR_TOP_R = 6.02, 3.02
        # tier 3 cone: the profile above z 6.0 stretches to CONE_TOP
        s = (g.CONE_TOP - 6.0) / (9.6 - 6.0)
        g.CONE_Z = np.where(_CONE_Z > 6.0, 6.0 + (_CONE_Z - 6.0) * s, _CONE_Z)
        g.CONE_R = _CONE_R.copy()
        zf = np.linspace(g.CONE_Z[0], g.CONE_Z[-1], 400)
        rf = np.interp(zf, g.CONE_Z, g.CONE_R)
        for _ in range(40):
            rf[1:-1] = 0.25 * rf[:-2] + 0.5 * rf[1:-1] + 0.25 * rf[2:]
        g.CONE_ZF, g.CONE_RF = zf, rf
        g.CONE_MF = np.concatenate([[0], np.cumsum(np.sqrt(np.diff(zf) ** 2 + np.diff(rf) ** 2))])
        g.CONE_DRDZ = np.gradient(rf, zf)
        # lantern and tier 4 cap
        g.LANT_APO = 1.375
        g.LANT_Z0, g.LANT_Z1 = g.CONE_TOP, g.CONE_TOP + g.LANT_H
        g.CAP = OctRoof(0.0, 0.0, p_lip=1.95, z_lip=g.LANT_Z1 + 0.02, d_pts=[0, 0.3, 0.6, 1.95], a_pts=[22, 32, 48, 50],
                        p_min=0.02, kick=0.035, kick_len=0.5, wave=0.008, sag=0.012, seed=8)
        # wing + thatch
        g.WY_R = 0.5 * (g.WY_S + g.WY_N)
        g.W_PITCH = math.radians(g.W_PITCH_DEG)
        g.W_TAN = math.tan(g.W_PITCH)
        g.W_RAFT = 2.40 + g.W_OVH * g.W_TAN          # thatch underside at the outer wall line (eave lip at 2.40)
        g.TH_V = (g.CORE_T + 0.06) / math.cos(g.W_PITCH)
        g.TH_V_MIN = (g.CORE_T + 0.01) / math.cos(g.W_PITCH)
        g.TH_BASE = g.CORE_T + 0.02
        g.SP_, g.CP_ = math.sin(g.W_PITCH), math.cos(g.W_PITCH)
        g.HIP_RC = 0.55
        g.EAVE_RC = g.HIP_RC
        g.ROLL_TOP_M, g.ROLL_TOP_H = roll_top_mh(g.CP_, g.SP_)
        # turret
        g.TUR_ZF, g.TUR_RF = _tur_table(g.TUR_SCALE)
        g.TUR_CLIP_Y = 0.42
        g.TOOTH = _tooth_specs()
        ts = g.TUR_SCALE
        g.CUSH.update(r_body=CUSH0["r_body"] * ts, r_drum=CUSH0["r_drum"] * ts,
                      proj_lo=tuple(v * ts for v in CUSH0["proj_lo"]), proj_up=tuple(v * ts for v in CUSH0["proj_up"]),
                      stone_len=tuple(v * max(ts, 0.85) for v in CUSH0["stone_len"]))
        g.TUR_R_TOP = 1.25 * ts
        tc = dict(TURCAP0)
        tc["p_lip"] = TURCAP0["p_lip"] * ts
        tc["d_pts"] = [d * ts for d in TURCAP0["d_pts"]]
        g.TUR_CAP = OctRoof(g.TUR_C[0], g.TUR_C[1], **tc)
        # wing wall path
        g.WS, g.WP, g.WN = build_wing_path()
        g.WING_LEN = g.WS[-1]
        g.S_SOUTH0 = wing_s_of(g.WX_W, g.WY_S)
        # producer note 11: the entrance zone is round the principal (arched) door
        door = next((o for o in g.OPENINGS if o["kind"] == "arch"), g.OPENINGS[0])
        dp = fmap(door["k"], np.array([door["xc"]]), np.array([0.0]), np.array([0.0]))[0]
        g.DOOR_P = dp
        g.detail = (DetailRule(entrance=(float(dp[0]), float(dp[1]))) if g.detail_rule is True
                    else (g.detail_rule if isinstance(g.detail_rule, DetailRule) else DetailRule.off()))
        return g

    def set(self, **kw):
        """kit_set for a live frame: change parameters and re-derive."""
        for k, v in kw.items():
            if k not in PARAMS:
                raise KeyError(f"unknown OctFrame parameter {k!r}")
            setattr(self, k, np.asarray(v, float) if k == "TUR_C" else v)
        return self.derive()

    def sub(self, name):
        """sub-collection <PREFIX>_<name> of the building collection (created on first use)."""
        from ..core import new_collection
        if name not in self.subs:
            self.subs[name] = new_collection(f"{self.prefix}_{name}", self.coll)
        return self.subs[name]

    def name(self, part):
        return f"{self.prefix}_{part}"

    def min_relief(self, P):
        """note-11 relief threshold (m) at world points P (..., 3): entrance_relief in the entrance zone."""
        P = np.asarray(P, float)
        r = self.detail
        if not r.active:
            return np.zeros(P.shape[:-1])
        d = np.hypot(P[..., 0] - r.entrance[0], P[..., 1] - r.entrance[1])
        ent = (d <= r.entrance_r) & (P[..., 2] >= -0.05) & (P[..., 2] <= r.entrance_h)
        return np.where(ent, r.entrance_relief, r.min_relief)


# =================================================================================================================
# hall envelope
# =================================================================================================================
def apo(z):
    return FR.A0 - np.asarray(z, float) * FR.BAT


def build_outline(A0):
    """the hall's rounded octagon (unit apothem, corner radius 0.08 m at A0): perimeter fraction, points, normals,
    facet bulge weight, length."""
    rc = 0.08 / A0
    half = TAN22 - rc * TAN22
    pts, nrm, bul = [], [], []

    def straight(k, x0, x1):
        n, t = FN[k], FT[k]
        for x in np.arange(x0, x1, 0.004):
            pts.append(n + t * x)
            nrm.append(n)
            bul.append(math.sin(math.pi * (x + half) / (2 * half)))

    def arc(k):
        phi = FPHI[k]
        cang = phi + math.radians(22.5)
        cen = (1 - rc) / math.cos(math.radians(22.5)) * np.array([math.cos(cang), math.sin(cang)])
        for a in np.linspace(phi, phi + math.radians(45), 6)[:-1]:
            d = np.array([math.cos(a), math.sin(a)])
            pts.append(cen + rc * d)
            nrm.append(d)
            bul.append(0.0)

    straight(0, 0.0, half)
    arc(0)
    for k in range(1, 8):
        straight(k, -half, half)
        arc(k)
    straight(0, -half, 0.0)
    pts.append(pts[0])
    nrm.append(nrm[0])
    bul.append(bul[0])
    P = np.array(pts)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    return L / L[-1], P, np.array(nrm), np.array(bul), L[-1]


def hall_L(z):
    return apo(z) * FR.L1


def hall_map(s, z, w, zc):
    """hall wall surface: s = perimeter arc length at the course height zc, z up, w out of the battered face."""
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    OT, OP, ON, OB = FR.OT, FR.OP, FR.ON, FR.OB
    t = np.mod(s / hall_L(zc), 1.0)
    ox, oy = np.interp(t, OT, OP[:, 0]), np.interp(t, OT, OP[:, 1])
    nx, ny = np.interp(t, OT, ON[:, 0]), np.interp(t, OT, ON[:, 1])
    nn = np.sqrt(nx * nx + ny * ny)
    nx, ny = nx / nn, ny / nn
    b = FR.BULGE * np.interp(t, OT, OB)
    a = apo(z)
    BAT = FR.BAT
    k3 = 1.0 / math.sqrt(1 + BAT * BAT)
    return np.stack([a * ox + b * nx + w * nx * k3, a * oy + b * ny + w * ny * k3, z + w * BAT * k3], -1)


def face_apo(k, x, z):
    """apothem of the outer wall face at facet-local x, height z."""
    half = TAN22 * FR.A0
    return apo(z) + FR.BULGE * np.sin(np.pi * np.clip((x + half) / (2 * half), 0, 1))


def fmap(k, x, z, w, a_ref=None):
    """plumb facet-local frame: x along facet (CCW), z up, w outward from the plane at a_ref (default A_REF)."""
    a_ref = FR.A_REF if a_ref is None else a_ref
    x = np.asarray(x, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    n, t = FN[k], FT[k]
    return np.stack([(a_ref + w) * n[0] + x * t[0], (a_ref + w) * n[1] + x * t[1], z], -1)


def facet_s(k, x, zc):
    return (k / 8.0) * hall_L(zc) + np.asarray(x, float)


def oct_pp(x, y):
    """exact octagon support distance of plan points (max over the 8 facet normals at k * 45 deg)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return np.max(np.stack([x * math.cos(k * math.pi / 4) + y * math.sin(k * math.pi / 4) for k in range(8)], 0), 0)


def oct_corner(apo_, k, sgn):
    """corner of an octagon (facet normals at k * 45 deg) at the end sgn of facet k."""
    phi = math.radians(45 * k)
    n = np.array([math.cos(phi), math.sin(phi)])
    t = np.array([-math.sin(phi), math.cos(phi)])
    return n * apo_ + t * apo_ * TAN22 * sgn


def corner_dir(c):
    a = FPHI[c] + math.radians(22.5)        # corner between facet c and c+1
    return np.array([math.cos(a), math.sin(a)]), a


def skirt_z_at(x, y):
    """height of the skirt sheathing surface above plan point (x, y) (approx, no noise) and its apothem."""
    ang = np.arctan2(y, x)
    k = np.round(ang / (np.pi / 4)).astype(int) % 8
    phi = k * np.pi / 4
    p = x * np.cos(phi) + y * np.sin(phi)
    return FR.SKIRT.zb(p), p


def cone_r(z):
    return np.interp(np.asarray(z, float), FR.CONE_ZF, FR.CONE_RF)


# =================================================================================================================
# wing (annex) envelope and its thatch surface
# =================================================================================================================
def q_rr(x, y, rc=None):
    """inward horizontal inset of plan points from the wing's eave outline (W, S, N eaves; the E end dies into the
    hall), measured to the family of rounded-rectangle contours that all keep corner radius rc: the hipped thatch
    surface z = 2.40 + q * tan(pitch) is rounded over the hips at every height."""
    rc = FR.HIP_RC if rc is None else rc
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    dW = x - (FR.WX_W - FR.W_OVH)
    dS = y - (FR.WY_S - FR.W_OVH)
    dN = (FR.WY_N + FR.W_OVH) - y
    q = np.minimum(np.minimum(dW, dS), dN)
    for d2 in (dS, dN):
        a, b = dW - rc, d2 - rc
        dc = 0.5 * ((a + b) + np.sqrt(np.maximum(2 * rc * rc - (a - b) ** 2, 0.0)))
        q = np.where(np.abs(a - b) < rc, np.minimum(q, dc), q)
    return q


def eave_q(x, y):
    return q_rr(x, y, FR.EAVE_RC)


def wing_under(x, y):
    """underside of the wing thatch (rounded-hip deck)."""
    return 2.40 + FR.W_TAN * q_rr(x, y)


def thatch_swell(x, y):
    """coherent low-frequency swelling of the thatch mass (+-5-8 cm over 1.5-3 m), faded in from the eave roll."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    v = 0.09 * vnoise90(np.stack([x / 2.3, y / 2.3, np.full_like(x, 4.11)], -1)) + \
        0.025 * vnoise90(np.stack([x / 1.2 + 5.0, y / 1.2, np.full_like(x, 9.3)], -1))
    return v * np.clip((q_rr(x, y) - 0.45) / 0.6, 0, 1)


def hip_swell(x, y):
    """the thatch builds up over the rounded hips (rounded swell, ~0.25 m radius section)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    dW = x - (FR.WX_W - FR.W_OVH)
    dS = y - (FR.WY_S - FR.W_OVH)
    dN = (FR.WY_N + FR.W_OVH) - y
    out = np.zeros_like(x)
    for d2, other in ((dS, dN), (dN, dS)):
        dh = np.abs(dW - d2) / math.sqrt(2)
        out = np.maximum(out, 0.05 * np.exp(-(dh / 0.24) ** 2) * (np.minimum(dW, d2) < other))
    return out


def thatch_low(x, y):
    """lowest course surface of the (swelling) thatch above plan point (x, y)."""
    return wing_under(x, y) + FR.TH_V_MIN + thatch_swell(x, y) / math.cos(FR.W_PITCH)


def wing_top(x, y):
    return wing_under(x, y) + FR.TH_V + thatch_swell(x, y) / math.cos(FR.W_PITCH)


def in_wing(P, margin=0.0, zpad=0.03):
    """points inside the wing envelope (under the thatch, within the walls)."""
    P = np.asarray(P, float)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    return (x < FR.WX_E - margin) & (x > FR.WX_W + margin) & (y > FR.WY_S + margin) & (y < FR.WY_N - margin) & \
        (z < wing_under(x, y) - zpad)


def in_wing_fp(x, y, pad=0.0):
    """plan points inside the wing's eave footprint (+ pad)."""
    return (x > FR.WX_W - FR.W_OVH - pad) & (x < FR.WX_E + FR.W_OVH + pad) & (y > FR.WY_S - FR.W_OVH - pad) & \
        (y < FR.WY_N + FR.W_OVH + pad)


def wing_roof_zone(C, pad=0.02):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    inside = in_wing_fp(x, y, 0.05)
    zs, pp = skirt_z_at(x, y)
    thatch_on_top = wing_top(x, y) > zs + 0.07
    return inside & (z < wing_top(x, y) + pad) & thatch_on_top


def build_wing_path():
    """the wing wall's plan path (outer face at ground): from the hall's N face along the N wall, W wall, S wall to
    the hall's SW facet, corners rounded r 0.07.  Returns arc length, points, outward normals."""
    pts = [(FR.WX_E, 3.70), (FR.WX_E, FR.WY_N), (FR.WX_W, FR.WY_N), (FR.WX_W, FR.WY_S), (-3.70, FR.WY_S)]
    rc = 0.07
    P, N = [], []
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        n = np.array([d[1], -d[0]])
        sa = rc if i > 0 else 0.0
        sb = rc if i < len(pts) - 2 else 0.0
        for u in np.arange(sa, L - sb, 0.01):
            P.append(a + d * u)
            N.append(n)
        if i < len(pts) - 2:
            c = b
            nb = np.array(pts[i + 2], float)
            d2 = (nb - c) / np.linalg.norm(nb - c)
            n2_ = np.array([d2[1], -d2[0]])
            cen = c - n * rc - n2_ * rc
            for t in np.linspace(0, 1, 7)[:-1]:
                nn = n * (1 - t) + n2_ * t
                nn /= np.linalg.norm(nn)
                P.append(cen + nn * rc)
                N.append(nn)
    P.append(np.array(pts[-1], float))
    N.append(N[-1])
    P = np.array(P)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    S = np.concatenate([[0], np.cumsum(seg)])
    return S, P, np.array(N)


def wing_map(s, z, w, zc):
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    WS, WP, WN = FR.WS, FR.WP, FR.WN
    px, py = np.interp(s, WS, WP[:, 0]), np.interp(s, WS, WP[:, 1])
    nx, ny = np.interp(s, WS, WN[:, 0]), np.interp(s, WS, WN[:, 1])
    nn = np.sqrt(nx * nx + ny * ny)
    nx, ny = nx / nn, ny / nn
    off = w - z * FR.BAT
    return np.stack([px + nx * off, py + ny * off, z + w * FR.BAT], -1)


def wing_s_of(x, y):
    d = np.hypot(FR.WP[:, 0] - x, FR.WP[:, 1] - y)
    return float(FR.WS[np.argmin(d)])


def wing_ztop(s):
    x, y = np.interp(s, FR.WS, FR.WP[:, 0]), np.interp(s, FR.WS, FR.WP[:, 1])
    if x > FR.WX_E - 0.05 and y > 3.6:
        return float(wing_under(x, y)) - 0.02
    return FR.W_WALL_H


# =================================================================================================================
# turret envelope
# =================================================================================================================
def _tur_table(scale):
    zf = np.linspace(_TPZ[0], _TPZ[-1], 641)
    rf = np.interp(zf, _TPZ, _TPR * scale)
    for _ in range(45):
        rf[1:-1] = 0.25 * rf[:-2] + 0.5 * rf[1:-1] + 0.25 * rf[2:]
    return zf, rf


def tur_r(z):
    return np.interp(np.asarray(z, float), FR.TUR_ZF, FR.TUR_RF)


def tur_reff(th, z):
    """effective radius in plan direction th: the circle, flattened onto the south wall plane below the thatch."""
    r = tur_r(z)
    sn = np.sin(th)
    lim = np.where(sn < -1e-3, (FR.TUR_C[1] - FR.TUR_CLIP_Y) / np.maximum(-sn, 1e-3), 1e9)
    return np.where(np.asarray(z, float) < 3.4, np.minimum(r, lim), r)


def tur_dist(x, y, z):
    """signed horizontal distance of points from the turret stone surface (+ outside)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    th = np.arctan2(y - FR.TUR_C[1], x - FR.TUR_C[0])
    return np.hypot(x - FR.TUR_C[0], y - FR.TUR_C[1]) - tur_reff(th, z)


def junction(name, z):
    """junction point (x, y), turret angle and arc direction sign for the wall 'N' (north wall, east of the turret)
    or 'W' (west wall, south of the turret) at height z."""
    z = np.asarray(z, float)
    r = tur_r(z)
    if name == "N":
        yf = FR.WY_N - z * FR.BAT
        xj = FR.TUR_C[0] + np.sqrt(np.maximum(r * r - (yf - FR.TUR_C[1]) ** 2, 0))
        return xj, yf, np.arctan2(yf - FR.TUR_C[1], xj - FR.TUR_C[0]), 1.0
    xf = FR.WX_W + z * FR.BAT
    yj = FR.TUR_C[1] - np.sqrt(np.maximum(r * r - (xf - FR.TUR_C[0]) ** 2, 0))
    return xf, yj, np.arctan2(yj - FR.TUR_C[1], xf - FR.TUR_C[0]), -1.0


def _tooth_specs():
    rng = np.random.default_rng(1818)
    out = []
    for name in ("N", "W"):
        z = rng.uniform(0.34, 0.45)
        while z < 2.30:
            h = rng.uniform(0.15, 0.23)
            out.append(dict(j=name, z0=z, z1=z + h, Lt=rng.uniform(0.22, 0.36), Lw=rng.uniform(0.26, 0.42),
                            f=rng.uniform(0.032, 0.05), r=rng.uniform(0.012, 0.024)))
            z += h + rng.uniform(0.16, 0.30)        # every 2-3 courses
    return out


def cush_f(th, spec=None):
    """0 on the W / NW side .. 1 toward droop_dir (the lopsided overhang of ref1)."""
    spec = FR.CUSH if spec is None else spec
    return 0.5 * (1 + np.cos(np.asarray(th, float) - spec["droop_dir"]))


def cush_out_r(th):
    """outer radius of the cushion's upper corbel course about the turret axis."""
    f = cush_f(th)
    C = FR.CUSH
    return C["r_body"] + C["proj_up"][0] + (C["proj_up"][1] - C["proj_up"][0]) * f


def cush_lip_z(th):
    """underside of the lower corbel course (droops toward droop_dir)."""
    return FR.CUSH["z_base"] - FR.CUSH["droop"] * cush_f(th)


def turret_outer(x, y, z):
    """signed distance from the turret envelope including the cushion collar (for ridge / comb ends)."""
    th = np.arctan2(np.asarray(y) - FR.TUR_C[1], np.asarray(x) - FR.TUR_C[0])
    r = np.hypot(np.asarray(x) - FR.TUR_C[0], np.asarray(y) - FR.TUR_C[1])
    z = np.asarray(z, float)
    in_c = (z > cush_lip_z(th) - 0.02) & (z < 6.66)
    rr = np.where(in_c, np.maximum(cush_out_r(th) - 0.03, tur_r(z)), tur_r(z))
    return r - rr


# =================================================================================================================
# pooled small parts (producer note 3) through the kit's shared pools
# =================================================================================================================
def get_pool(key, builder, n_var):
    """register a pool of n_var variants built by builder(acc, k) (built on first use)."""
    FR.POOL_SPECS[key] = (builder, n_var)


def place(key, var, M, part):
    """linked duplicate of variant `var` of pool `key` with the 4x4 matrix M; object <PREFIX>_<part>_<nnn>."""
    from ..geom import pool_hygiene
    builder, n = FR.POOL_SPECS[key]
    pools = FR.pools
    if not callable(pools.hygiene):
        pools.hygiene = pool_hygiene()
    me = pools.mesh(key, int(var) % n, builder, sharp=40.0)
    M = np.asarray(M, float)
    return pools.place(me, part, R=M[:3, :3], t=M[:3, 3])
