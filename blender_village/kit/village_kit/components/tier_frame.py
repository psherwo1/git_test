"""components.tier_frame -- the frame of a building assembled from FREE TIER MODULES (kit 1.7.0, v2_tiered_hall).

The keep family (oct_frame) hard-codes one building's tier stack.  This frame holds no building at all: a recipe
declares its BODIES (vertical prisms: round or regular-polygon plan, battered, any centre, any height) and then
stacks modules on them by name:

    declare_bodies(g, dict(hall=dict(sides=8, apothem=5.0, z0=-0.05, z1=3.5, batter_deg=2.0),
                           drum=dict(sides=0, apothem=3.0, z0=5.0, z1=8.1), ...))
    stone_body(g, "hall", openings=[...], clip_by=("tur_e",))          # components.stone_body
    bell_tier(g, "skirt1", on="hall", overhang=1.25, profile="skirt", through=("drum", "tur_e"))
    roof_flashing(g, "skirt1", "drum")                                  # components.tier_roof (the junction)
    board_belt(g, "lantern", ...), tier_finial(g, "cap", ...)           # components.board_belt / tier_roof

Every module reads geometry ONLY through the registry, so any two modules that meet can find each other: a body
culls its stones inside another body (clip_by), a roof drops its units inside the bodies that rise through it
(through), a flashing follows the true roof / body intersection.  That is the junction API.

TierFrame also makes the kit's octagonal-roof machinery (oct_roof.build_cap, hewn members, pooled pegs) usable
outside the keep: it activates itself as the oct_frame proxy FR and provides what those helpers read
(min_relief, dropped_checks, pools, units).

Conventions: plan angles `th` are math angles (x = cos, y = sin) in radians unless a parameter says _deg; a
polygon's facet k has its outward normal at rot + 360 k / sides deg.
"""
import math

import numpy as np

from ..assembly import Building
from ..core import DetailRule
from . import oct_frame


class Body:
    """a vertical prism registered on the frame: round (sides < 3) or a regular polygon (sides >= 3, slightly
    rounded corners), apothem / radius `apothem` at z = 0 battered by batter_deg, from z0 to z1."""

    def __init__(self, name, center=(0.0, 0.0), sides=0, apothem=3.0, z0=0.0, z1=3.0, batter_deg=0.0,
                 rot_deg=0.0, corner_p=40.0, kind="stone"):
        self.name = name
        self.c = np.asarray(center, float)
        self.sides = int(sides)
        self.apothem = float(apothem)
        self.z0, self.z1 = float(z0), float(z1)
        self.bat = math.tan(math.radians(batter_deg))
        self.rot = math.radians(rot_deg)
        self.pn = float(corner_p)
        self.kind = kind

    @property
    def round(self):
        return self.sides < 3

    def r_nom(self, z):
        """nominal radius / apothem at height z (batter)."""
        return self.apothem - np.asarray(z, float) * self.bat

    def shape(self, th):
        """r_eff / r_nom in plan direction th: 1 for a round body; a rounded regular polygon (p-norm of the facet
        cosines, corner rounding ~1.8 % of the apothem at p = 40) otherwise."""
        th = np.asarray(th, float)
        if self.round:
            return np.ones_like(th)
        phis = self.rot + 2 * np.pi * np.arange(self.sides) / self.sides
        c = np.clip(np.cos(th[..., None] - phis), 0.0, None)
        return 1.0 / np.sum(c ** self.pn, -1) ** (1.0 / self.pn)

    def r_eff(self, th, z):
        return self.r_nom(z) * self.shape(th)

    def facet_normal(self, th):
        """outward plan normal angle of the face in direction th (the facet normal; th itself when round)."""
        if self.round:
            return float(th)
        step = 2 * math.pi / self.sides
        k = round((th - self.rot) / step)
        return self.rot + k * step

    def point(self, th, z, d=0.0):
        """world point on the face (nominal, no stone relief) in direction th at height z, d out along the radial."""
        r = self.r_eff(th, z) + d
        return np.stack([self.c[0] + r * np.cos(th), self.c[1] + r * np.sin(th), np.broadcast_to(z, np.shape(r))], -1)

    def dist(self, P):
        """signed horizontal distance of world points from the face (+ outside)."""
        P = np.asarray(P, float)
        x, y = P[..., 0] - self.c[0], P[..., 1] - self.c[1]
        return np.hypot(x, y) - self.r_eff(np.arctan2(y, x), P[..., 2])

    def inside(self, P, margin=0.0, zpad=0.0):
        """points inside the body (deeper than margin behind the face, within z0 - zpad .. z1 + zpad)."""
        P = np.asarray(P, float)
        return (self.dist(P) < -margin) & (P[..., 2] > self.z0 - zpad) & (P[..., 2] < self.z1 + zpad)

    def extent(self):
        """largest plan distance of the face from the world origin (for view rings)."""
        return float(np.hypot(*self.c) + self.apothem / math.cos(math.pi / max(self.sides, 8)))


def roof_support(roof, x, y):
    """apothem coordinate p of plan points on an oct_frame.OctRoof (the octagon support distance about its centre,
    honouring its plan rotation)."""
    x = np.asarray(x, float) - roof.c[0]
    y = np.asarray(y, float) - roof.c[1]
    if getattr(roof, "is_round", False):          # tier_roof.ConeRoof (a round tier): the plan radius
        return np.hypot(x, y)
    return np.max(np.stack([x * math.cos(p) + y * math.sin(p) for p in roof.phi], 0), 0)


def roof_z(roof, x, y):
    """height of an OctRoof's base surface (no kick / wave / sag) above plan points; p beyond the lip -> -inf."""
    p = roof_support(roof, x, y)
    z = roof.zb(np.clip(p, roof.Pp[-1], roof.p_lip))
    return np.where(p <= roof.p_lip, z, -np.inf)


class TierFrame(Building):
    """frame of a tier-module building (see the module doc).  Parameters: entrance (x, y) of the principal door
    (producer note 11's entrance zone), detail_rule (True / False / a DetailRule), units ('kit' = SIZE_TABLE
    chunky roofing), seed_offset (added to every module seed by the recipe).
    roof_clear (kit 1.7.2): minimum clear height (m) between two tiers on DIFFERENT bodies wherever their plans
    overlap (roof_clearance, run by every tier when it registers); None switches the gate off (diagnostics only)."""

    roof_clear = 0.50
    roof_stack = 0.20

    def __init__(self, prefix="TIER", entrance=(0.0, -5.0), detail_rule=True, units="kit", seed_offset=0):
        super().__init__(prefix)
        from ..geom import pool_hygiene
        self.units = units
        self.seed_offset = int(seed_offset)
        self.hygiene = False
        self.pools.hygiene = pool_hygiene()
        self.subs = {}
        self.bodies = {}          # name -> Body
        self.roofs = {}           # name -> dict(roof=OctRoof, on=body, p_wall, z_plate, objects, through)
        self.openings = []        # framed openings published by stone_body (world frames, for frames / decals / cull)
        self.belts = {}           # name -> dict(center, r, z0, z1)
        self.copings = []         # (body, z) ledges published by stone_body
        self.dropped_checks = []  # note 11: timber checks not modelled -> crack anchors
        self.POOL_SPECS = {}
        ent = (float(entrance[0]), float(entrance[1]))
        self.DOOR_P = np.array(ent)
        self.detail = (DetailRule(entrance=ent) if detail_rule is True
                       else (detail_rule if isinstance(detail_rule, DetailRule) else DetailRule.off()))
        oct_frame.activate(self)          # oct_roof / hewn / peg helpers read the active frame through FR

    # ---------------------------------------------------------------------------------------------------------
    def sub(self, name):
        from ..core import new_collection
        if name not in self.subs:
            self.subs[name] = new_collection(f"{self.prefix}_{name}", self.coll)
        return self.subs[name]

    def name(self, part):
        return f"{self.prefix}_{part}"

    def min_relief(self, P):
        """note-11 relief threshold (m) at world points P: entrance_relief inside the entrance zone."""
        P = np.asarray(P, float)
        r = self.detail
        if not r.active:
            return np.zeros(P.shape[:-1])
        d = np.hypot(P[..., 0] - r.entrance[0], P[..., 1] - r.entrance[1])
        ent = (d <= r.entrance_r) & (P[..., 2] >= -0.05) & (P[..., 2] <= r.entrance_h)
        return np.where(ent, r.entrance_relief, r.min_relief)

    def body(self, name):
        if name not in self.bodies:
            raise KeyError(f"no body {name!r} declared; declared: {sorted(self.bodies)}")
        return self.bodies[name]

    def inside_any(self, P, names, margin=0.0, zpad=0.0):
        P = np.asarray(P, float)
        out = np.zeros(P.shape[:-1], bool)
        for n in names:
            out |= self.body(n).inside(P, margin, zpad)
        return out

    def extent(self):
        return max([b.extent() for b in self.bodies.values()] + [3.0])


def declare_bodies(g, bodies):
    """KIT STEP: register the building's bodies (name -> Body keywords) before any module is built, so modules that
    meet can find each other in any build order."""
    for name, kw in bodies.items():
        g.bodies[name] = Body(name, **kw)
    return g.bodies


# =================================================================================================================
# kit 1.7.2: the roof-to-roof junction rule (two tiers on different bodies)
# =================================================================================================================
class RoofClearanceError(RuntimeError):
    """two roof tiers on different bodies overlap in plan with too little clear height (kit 1.7.2)."""


def _roof_plan_box(roof):
    r = float(roof.p_lip) * (1.0 if getattr(roof, "is_round", False) else 1.0 / math.cos(math.pi / 8))
    return roof.c[0] - r, roof.c[0] + r, roof.c[1] - r, roof.c[1] + r


def _covered(g, t, X, Y):
    """(z of tier t's base surface, mask of plan points its covering really spans): inside the lip, outside the
    p_top opening and outside every body rising through it."""
    roof = t["roof"]
    z = roof_z(roof, X, Y)
    ok = np.isfinite(z)
    p = roof_support(roof, X, Y)
    p_in = t.get("p_top")
    ok &= p >= (float(p_in) if p_in is not None else float(roof.Pp[-1]))
    if t.get("through") and ok.any():
        P = np.stack([X, Y, np.where(ok, z, 0.0)], -1)
        ok &= ~g.inside_any(P, t["through"], margin=0.0, zpad=0.30)
    return z, ok


def roof_clearance(g, name, min_clear=None, stack=None, step=0.05, raise_error=True):
    """KIT CHECK (kit 1.7.2): the roof-to-roof junction rule.  Tier `name` is tested against every registered tier
    on ANOTHER body.  Where the two coverings overlap in plan (both inside their lips, outside their p_top openings
    and outside the bodies rising through them), the clear height between the upper tier's underside and the lower
    tier's covering must be >= min_clear (default g.roof_clear, 0.50 m), else no plan overlap at all.
    Clear height = upper base surface - lower base surface - stack, where stack (default g.roof_stack, 0.20 m)
    allows for the lower covering's shingle stack above its base surface plus the upper tier's deck / soffit / rafter
    feet below its own (checked against a vertical mesh ray probe on v2: the rule agrees with the measured mesh gap
    to within about 0.15 m, e.g. rule / mesh 0.10 / 0.16 m for round 2's clash, 0.61 / 0.56 m for round 3's fix,
    1.86 / 1.88 m tur_e_cap over skirt1, 1.33 / 1.47 m tur_nw_cap over skirt1).  Tiers that cross (one
    eave passes through the other covering) give a negative clear height.
    Raises RoofClearanceError naming both tiers, the worst plan point and the clear height (raise_error=False:
    only logs).  Returns [(other, upper, lower, clear, x, y)] for the overlapping pairs."""
    from ..core import log
    min_clear = getattr(g, "roof_clear", 0.50) if min_clear is None else min_clear
    stack = getattr(g, "roof_stack", 0.20) if stack is None else stack
    t = g.roofs[name]
    out, bad = [], []
    x0, x1, y0, y1 = _roof_plan_box(t["roof"])
    for other, o in g.roofs.items():
        if other == name or o["on"] == t["on"]:
            continue
        a0, a1, b0, b1 = _roof_plan_box(o["roof"])
        lx, hx, ly, hy = max(x0, a0), min(x1, a1), max(y0, b0), min(y1, b1)
        if lx >= hx or ly >= hy:
            continue
        xs = np.arange(lx, hx + step, step)
        ys = np.arange(ly, hy + step, step)
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        X, Y = X.ravel(), Y.ravel()
        za, oka = _covered(g, t, X, Y)
        zb, okb = _covered(g, o, X, Y)
        m = oka & okb
        if not m.any():
            continue
        d = za[m] - zb[m]
        if np.median(d) >= 0:
            upper, lower, gap = name, other, d - stack
        else:
            upper, lower, gap = other, name, -d - stack
        k = int(np.argmin(gap))
        rec = (other, upper, lower, float(gap[k]), float(X[m][k]), float(Y[m][k]))
        out.append(rec)
        log(f"  roof clearance {upper} over {lower}: min clear {rec[3]:.2f} m at ({rec[4]:.2f}, {rec[5]:.2f}) "
            f"over {int(m.sum())} plan samples (rule >= {min_clear:.2f} m)" if min_clear is not None else
            f"  roof clearance {upper} over {lower}: min clear {rec[3]:.2f} m at ({rec[4]:.2f}, {rec[5]:.2f})")
        if min_clear is not None and rec[3] < min_clear:
            bad.append(rec)
    if bad and raise_error:
        msg = "; ".join(f"tier {u!r} (on body {g.roofs[u]['on']!r}) passes over tier {lo!r} (on body "
                        f"{g.roofs[lo]['on']!r}) with {c:.2f} m clear at plan ({x:.2f}, {y:.2f})"
                        for _, u, lo, c, x, y in bad)
        raise RoofClearanceError(f"roof-to-roof clearance < {min_clear:.2f} m: {msg}.  Raise the upper tier's body, "
                                 f"move it out, or cut an overhang until the plans no longer overlap.")
    return out
