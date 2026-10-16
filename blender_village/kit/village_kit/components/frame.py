"""components.frame -- the round-building frame `g` shared by the round components (plinth, posts, wattle/daub
wall, plate, conical roof, collar/finial, framed door, interior).

RoundFrame(spec) holds every dimension of one round building (wall radius, post ring, wall plate, eave, roof
pitch, door opening, plinth...) and the state the components publish to each other while the building is built
(plinth stone-top sampler PL_TOP, post profiles, daub fields, rod store, shingle vertices...).  Components are
plain functions `component(g, ...)`; they never read module globals, so several buildings can be built in one
session, each with its own frame.
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import DetailRule, fbm, ring_noise, smoothstep


def post_azimuths(g):
    rng = np.random.RandomState(101)
    a0 = g.WALL_POST_AZ_DOOR
    span = 2 * math.pi - 2 * a0
    az = [a0]
    for k in range(1, g.N_POSTS - 1):
        az.append(a0 + k * span / (g.N_POSTS - 1) + math.radians(rng.uniform(-1.2, 1.2)))
    az.append(2 * math.pi - a0)
    return np.array(az)


def bay_s(g, i):
    a0 = g.POST_AZ[i]
    a1 = g.POST_AZ[i + 1]
    return a0 * g.R_WALL, a1 * g.R_WALL


def interior_visible(az, half_width=math.radians(110.0)):
    """roof structure on this azimuth can be seen from outside through the doorway (back arc)."""
    return abs(float(np.angle(np.exp(1j * (az - math.pi))))) < half_width


def floor_z(g, X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    R_ = np.hypot(X, Y)
    z = (g.SILL_TOP - 0.004 + 0.008 * fbm(np.stack([X * 1.2, Y * 1.2, np.zeros_like(X)], -1), 3)
         - 0.015 * np.exp(-(R_ / 0.9) ** 2))
    # trodden hollow just inside the sill: the floor steps down ~2.5 cm from the sill top
    door = np.exp(-(X / 0.9) ** 2) * (1 - smoothstep(-(g.R_WALL - 0.05), -(g.R_WALL - 1.1), Y))
    return z - 0.024 * door


def earth_base(X, Y):
    """producer note 10: no apron / mound / path -- the terrain is built separately in Unreal; the
    building stands on a flat Z = 0 datum and its own footing carries a <= 4 cm buried skirt."""
    X = np.asarray(X, float)
    return np.zeros(np.shape(X))


def ground_z(g, X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    r = np.hypot(X, Y)
    return np.where(r < g.R_FLOOR_EDGE, floor_z(g, X, Y), earth_base(X, Y))


def cull_below_ground(g, V):
    """vertex is never visible: deeper than the buried skirt outside (flat Z = 0 datum), or more than
    1.2 cm under the interior earth floor."""
    hid = np.zeros(len(V), bool)
    low = V[:, 2] < 0.26
    if low.any():
        X, Y = V[low, 0], V[low, 1]
        inside = np.hypot(X, Y) < g.R_FLOOR_EDGE
        gz = np.where(inside, floor_z(g, X, Y) - 0.012, earth_base(X, Y) - g.GROUND_SKIRT)
        hid[low] = V[low, 2] < gz
    return hid


def stone_top(g, x, y, default=None):
    """height of the plinth stone surface under (x, y) (vertical ray-cast); default where no stone."""
    from mathutils import Vector
    if default is None:
        default = g.PLINTH_TOP
    bvh = g.PL_TOP.get("bvh")
    out = []
    for xx, yy in zip(np.atleast_1d(x), np.atleast_1d(y)):
        hit = None if bvh is None else bvh.ray_cast(Vector((float(xx), float(yy), 1.5)), Vector((0, 0, -1.0)), 2.0)
        out.append(default if hit is None or hit[0] is None else float(hit[0][2]))
    return np.array(out)


def wall_floor(g, s):
    """plinth stone top under the wattle line at arc length s (R_WALL), for weave bedding."""
    return np.interp(np.mod(np.asarray(s, float) / g.R_WALL, 2 * np.pi), g.PL_TOP["az"], g.PL_TOP["z"])


def plinth_face_r(g, az):
    return g.R_PL_FACE + 0.018 * ring_noise(np.asarray(az, float), 9091, 6, 1.0)


# =================================================================================================================
# the frame
# =================================================================================================================
from ..assembly import Building  # noqa: E402
from .cone import build_profile, s_at_r, rafter_underside_z_at_r  # noqa: E402

# the signed-off phase-1 hut (round 7) is the reference size; derived defaults scale from it
R_REF = 3.50
# client correction (mostly intact daub): 3 small fallen-out patches + the ref2 band left of the door
#   (azimuth deg, kind, centre z, half width, half height, seed)
DEFAULT_PATCHES_AZ = [
    (81.67, "hole", 1.30, 0.47, 0.30, 9310),     # +X side, mid height (side view)
    (154.92, "low", 0.55, 0.50, 0.18, 9320),     # back right, broken out above the plinth (back view)
    (275.51, "hole", 1.86, 0.42, 0.28, 9330),    # back left, under the eave (hero / aerial)
]


class RoundFrame(Building):
    """dimension table + shared state of a round post-and-infill building under a conical roof.

    Main parameters (metres / degrees):
      radius        wattle / post centre-line radius                          (hut 3.50)
      eave_z        roof reference surface height at the eave lip             (hut 2.395 -> eave lip 2.38-2.45)
      overhang      eave radius beyond the wall line                          (hut 0.63 -> eave dia 8.26)
      pitch_deg     cone pitch                                                (hut 51)
      n_posts       wall posts (default: ~1.57 m spacing)                     (hut 14)
      n_raft        pole rafters (default: ~0.93 m at the eave, even)         (hut 28)
      door_post_az_deg  azimuth of the two wall posts that flank the projecting door frame (default: the frame's
                    fixed 2.5 m width at this radius)                         (hut 21)
      finial_tip    height of the spike tip; None -> spindle top + 0.95 m      (hut 8.60)
      collar_r, collar_pitch_deg   apex lead-hat drip radius and pitch       (hut 0.745, 53)
      plinth_top    nominal plinth stone top                                  (hut 0.33)
      cone_age      dict for the low-frequency cone age pass (components.cone.age_defaults), {} = off
      detail_rule   producer note 11 detail-scale rule (core.DetailRule, entrance at the door frame); False =
                    phase-1 behaviour (all sub-2 cm relief modelled)
      hygiene       Nanite clean-up (core.nanite_clean) on every mesh
    Everything else (front plane of the door frame, plinth face, floor edge, eave shadow heights, the doorway
    window of full-length shingles...) is derived from these, so a different radius / wall height builds a
    consistent hut.  The derived values reproduce the signed-off hut exactly at radius 3.50, eave_z 2.395.
    """

    def __init__(self, prefix="HUT", radius=3.50, eave_z=2.395, overhang=0.63, pitch_deg=51.0, n_posts=None,
                 n_raft=None, door_post_az_deg=None, finial_tip=None, collar_r=0.745, collar_pitch_deg=53.0,
                 plinth_top=0.33, n_courses=None, sh_expose=0.318, daub_patches=None, cone_age=None,
                 detail_rule=True, hygiene=True):
        super().__init__(prefix)
        R = float(radius)
        self.k_r = R / R_REF
        self.Z_MIN = -0.045                   # lowest point (buried footing skirt); nothing deeper than 5 cm
        self.GROUND_SKIRT = 0.04              # buried skirt kept on the footing (producer note 10: <= 5 cm)
        self.z_clamp = self.Z_MIN + 0.004
        self.R_WALL = R
        self.N_POSTS = int(n_posts) if n_posts is not None else max(8, int(round(2 * math.pi * R / 1.5708)))
        if door_post_az_deg is not None:
            self.WALL_POST_AZ_DOOR = math.radians(door_post_az_deg)
        elif self.k_r == 1.0:
            self.WALL_POST_AZ_DOOR = math.radians(21.0)
        else:                                 # the projecting door frame is 2.5 m wide whatever the radius
            self.WALL_POST_AZ_DOOR = math.asin(min(0.9, R_REF * math.sin(math.radians(21.0)) / R))
        self.Z_WATTLE0 = 0.345
        self.PITCH = math.radians(pitch_deg)
        self.R_EAVE = R + overhang
        self.Z_EAVE = float(eave_z)
        self.N_RAFT = int(n_raft) if n_raft is not None else 2 * max(8, int(round(14 * self.k_r)))
        self.RAFT_R = 0.055
        self.BATTEN_T = 0.03
        self.SH_EXPOSE = sh_expose
        self.SH_LEN = 0.72
        self.COLLAR_R = collar_r              # lead-hat drip radius (dia 1.49)
        self.COLLAR_PITCH = math.radians(collar_pitch_deg)
        self.FINIAL_TIP = finial_tip          # None: spindle top + 0.95 m
        self.DOOR_W = 1.00
        self.SILL_TOP = 0.20
        self.HEAD_Z = self.SILL_TOP + 2.08    # 2.28: 2.08 m clear opening
        self.FRONT_Y = -(R + 0.22)            # front plane of the projecting door frame
        self.RAFT_AZ0 = math.pi / self.N_RAFT  # no rafter on the door axis
        self.cone_age = dict(cone_age or {})  # optional low-frequency age pass (components.cone)
        # roof reference surface
        self.PS, self.PR, self.PZ, self.PA = build_profile(self)
        self.WAVE_Z = None
        self.S_END = s_at_r(self, 0.42)       # shingles terminate under the collar here
        self.N_COURSES = int(n_courses) if n_courses is not None else int((self.S_END - 0.18) / self.SH_EXPOSE)
        self.PLATE_TOP = float(rafter_underside_z_at_r(self, self.R_WALL + 0.09)) + 0.03
        self.PLATE_H = 0.20
        self.PLATE_BOT = self.PLATE_TOP - self.PLATE_H
        self.WATTLE_TOP = self.PLATE_BOT
        # wall
        self.POST_AZ = post_azimuths(self)
        self.POST_OUT = 0.02                  # wall posts stand 2 cm outside the wattle line
        self.PLATE_OUT = 0.01
        self.EAVE_SHADOW_Z = self.Z_EAVE - 0.035      # above this the wall is in the deep eave shadow
        self.ROD_SHADOW_Z = self.Z_EAVE - 0.115
        self.DAUB_KEEP_UNDER = 0.05           # wattle kept only in the exposed patches + ~7-10 cm under their edges
        self.ROD_ROW_P = 0.036                # nominal rod row pitch: patch margins break along the rows
        self.COAT_R_NOM = 0.062               # mean coat face 6.2 cm outside the wattle centre line
        self.INNER_SKIN_D = 0.17              # inner daub skin face behind the wattle centre line
        # exposed-wattle patches: (bay, kind, centre fraction along the bay, centre z, half w, half h, seed); the
        # defaults are given by azimuth (phase-1 hut: bays 2 / 5 / 10) so any post count places them sensibly
        self._patches_arg = daub_patches
        # roof
        # roof
        self.FULL_WIN_DEG = 66.0              # back-arc window seen through the doorway: full-length shingles
        self.FULL_WIN_Z = self.Z_EAVE + 1.605
        # plinth / ground
        self.R_PL_FACE = R + 0.26             # plinth outer face line
        self.PLINTH_TOP = plinth_top
        self.PAD_TOP = 0.225                  # door-post pad stones: bearing bed height
        self.STEP_C = (0.04, self.FRONT_Y - 0.58)
        self.R_FLOOR_EDGE = R - 0.14          # inside this radius the ground is the interior earth floor
        # shared state published by the components while the building is built
        self.PL_TOP = {}
        self.POST_RAD = []
        self.POST_PROF = []
        self.COVER_FOOT = {}
        self.ROD_STORE = {}
        self.DAUB_BAYS = {}
        self.DAUB_COVER = {}
        self.DAUB_HIDE = {}
        self.DAUB_PARTS = {}
        self._EDGE_CURVE = {}
        self.FOOT = {}
        self.SHINGLE_TOP = {}
        self.FLAGS = []
        self.pools.moss = {"chink": 0.6}
        self.hygiene = bool(hygiene)
        self.pools.hygiene = bool(hygiene)
        self.detail = DetailRule(entrance=(0.0, self.FRONT_Y)) if detail_rule else DetailRule.off()
        self.DAUB_CRACKS = []                 # shrinkage-crack polylines (s, z) -> decal anchors (note 11)
        if self._patches_arg is not None:
            self.DAUB_PATCHES = list(self._patches_arg)
        else:
            self.DAUB_PATCHES = [self.patch_at(*p_) for p_ in DEFAULT_PATCHES_AZ]
        self._ground_cull = partial(cull_below_ground, self)

    # convenience
    def bay_of(self, az):
        """index of the wall bay containing azimuth az (radians, from -Y toward +X)."""
        a = float(np.mod(az, 2 * math.pi))
        for i in range(len(self.POST_AZ) - 1):
            if self.POST_AZ[i] <= a < self.POST_AZ[i + 1]:
                return i
        return len(self.POST_AZ) - 2

    def patch_at(self, az_deg, kind, cz, hs, hz, seed):
        """a DAUB_PATCHES entry from an azimuth (degrees) instead of a bay index."""
        az = math.radians(az_deg) % (2 * math.pi)
        b = self.bay_of(az)
        if b == len(self.POST_AZ) - 2:                   # never in the door bay (it has the ref2 band)
            b -= 1
        a0, a1 = self.POST_AZ[b], self.POST_AZ[b + 1]
        L = (a1 - a0) * self.R_WALL
        m = min(0.5, (hs + 0.12) / L)                     # keep the patch inside its bay, clear of the posts
        f = float(np.clip((az - a0) / (a1 - a0), m, 1 - m))
        hs = min(hs, 0.5 * L - 0.12)
        cz = min(cz, self.PLATE_BOT - hz - 0.3)
        return (b, kind, f, cz, hs, hz, seed)


# =================================================================================================================
# producer note 6: hidden-geometry removal for a round building
# =================================================================================================================
HIDDEN_CULL_TARGETS = ("plinth_stones", "wattle_rods", "posts", "door_frame", "threshold", "roof_shingles",
                       "roof_starter", "wall_plate", "rafters", "purlin_rings", "daub")


def actor_views(g):
    """actor- and crane-scale viewpoints round a round building: rings just outside the eave / plinth at knee,
    waist, eye and raised-hand height, a crane ring, close views in front of the door (0.5-2 m, knee to above
    head height) and the six review cameras.  Used so a visibility cull never opens anything a camera could
    plausibly see."""
    from ..core import ring_views, review_cameras
    import bpy
    V = [ring_views((0, 0), [g.R_EAVE + 0.4, g.R_EAVE + 1.5, g.R_EAVE + 3.5], [0.3, 1.0, 1.65, 2.3], n=24),
         ring_views((0, 0), [g.R_EAVE + 6.0], [5.0, 9.0], n=16, phase=0.11)]
    door = [(x, g.FRONT_Y - d, z) for d in (0.5, 1.0, 2.0) for z in (0.4, 1.1, 1.7, 2.3) for x in (-0.9, 0.0, 0.9)]
    V.append(np.array(door))
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    lo = np.min([np.min(np.array([o.matrix_world @ v.co for v in o.data.vertices[:1]] or [[0, 0, 0]]), 0)
                 for o in obs], 0)
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in obs])
    lo, hi = co.min(0), co.max(0)
    V.append(review_cameras(lo, hi))
    return np.concatenate(V)


def round_hidden_cull(g, targets=HIDDEN_CULL_TARGETS, procs=4):
    """KIT COMPONENT (post step): delete the faces of the named objects that no review / actor / crane viewpoint
    can see (core.visibility_cull).  Backing surfaces (inner skin, blocker, eave closure, panel backing, floor) are
    never culled, so nothing culled can open a see-through hole.  Run it after every mesh is built."""
    from ..core import visibility_cull, log
    names = [f"{g.prefix}_{t}" for t in targets]
    n = visibility_cull(names, extra_views=actor_views(g), procs=procs)
    log(f"hidden-geometry cull: -{n} polygons")
    return n
