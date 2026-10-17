"""components.drum_frame -- the frame `g` of a stone-drum tower (the tower windmill and its kit variants).

DrumFrame holds every dimension of one drum tower -- the battered rubble drum (radius, batter, door, slit windows,
balustrade band, blind arcade, cornice), the shake apron, the octagonal smock tower (taper, lean), the hipped cap
(footprint, bell-cast profile, hood, yaw), the rotor frame (hub, shaft tilt, wheel rings, blades), the tail boom and
vane -- plus the state the components publish to each other while the building is built (named BatchAcc parts,
the rubble-wall rasters, the pooled bolt / baluster / corbel placements).

Every component is a plain function `component(g, ..., seed=...)`; its optional dimension parameters are written
to the frame with g.set(**kw), which re-derives every dependent dimension (openings, cap profile and valley
tables, rotor frame, curb, collar and tail heights), so a component called with other numbers builds a
consistent other tower.  The geometry helpers below (R_out, face_map, cap_z, capw, rotw, lean ...) all take the
frame as their first argument: nothing reads a module global, so several towers can be built in one session.

Frames: x along, y out, z up; azimuth az from -Y toward +X (the entrance faces -Y); cap-local x' = shaft heading.
"""
import math
from contextlib import contextmanager
from functools import partial
import zlib

import numpy as np

from ..assembly import Building
from ..core import DetailRule, log
from ..tmplmesh import BatchAcc, D2R, PI, fill_acc, rotm, smoothstep, unit


class DrumFrame(Building):
    """dimension table + per-build state of a drum tower (see the module doc).  The defaults are the signed-off
    tower windmill; components change them through their parameters (g.set)."""

    LEANED = ("tower_", "cap_", "windshaft", "poll_end", "rotor_iron", "wheel_", "tail_")

    def __init__(self, prefix="MILL", collection=None, detail_rule=True, hygiene=True, entrance_relief=0.01,
                 min_relief=0.02, rubble=None, **unused):
        super().__init__(prefix, collection)
        self.hygiene = hygiene
        # ---- stone drum ----
        self.R_BASE0, self.R_BASE1, self.Z_BATTER = 2.60, 2.45, 4.05
        self.DOOR_CW = 0.525          # clear half width (1.05 m)
        self.Z_TH = 0.14              # threshold top
        self.ZS_DOOR = self.Z_TH + 1.65    # springing
        self.DOOR_JAMBS = {-1: [0.42, 0.30, 0.44, 0.32], 1: [0.31, 0.43, 0.30, 0.42]}
        self.DOOR_JZ = [0.0, 0.44, 0.86, 1.30, self.ZS_DOOR]
        self.DOOR_RING = (0.18, 0.215)
        self.WIN_AZ = [70 * D2R, -130 * D2R]
        self.WIN = dict(cw=0.08, z0=1.30, z1=1.85, jz=[1.30, 1.56, 1.85], fw=[(0.17, 0.21), (0.21, 0.17)])
        self.WIN_DZ = None            # kit changes v1_stone_watchtower (optional): per-window height offsets (m)
        self.BATTER_TOP = 4.6         # kit changes v1_stone_watchtower (optional): the batter stops at this z
        self.WIN_SPEC = None          # v1_stone_watchtower r2 (optional): one window_spec() per WIN_AZ entry
        self.BAND_STYLE = "balustrade"  # v1_stone_watchtower r2 (optional): "plain" = drum_band.string_course
        self.ARCH_AZ = [(18 + 36 * k) * D2R for k in range(10)]
        self.ARCH = dict(cw=0.36, z0=2.92, zs=3.64, ring=(0.15, 0.165), fw=0.17, jz=[2.92, 3.28, 3.64])
        self.Z_BAND0, self.Z_BAL0, self.Z_BAL1, self.Z_BAND1 = 2.55, 2.65, 2.82, 2.92
        self.Z_CORN0 = 4.17
        self.DZ = 0.12
        self.RREF = 2.53
        # ---- shake apron ----
        self.AP_RE = 3.17
        self.AP_ZE = 4.50 + self.DZ
        self.AP_RT = 1.60
        self.AP_ZT = 6.00
        self.AP_COURSES = 3
        # ---- smock tower ----
        self.TW_Z0, self.TW_Z1 = 5.95, 11.45
        self.TW_A0, self.TW_A1 = 1.55, 0.95
        self.LEAN_DIR = unit(np.array([-0.95, 0.31, 0.0]))
        self.LEAN_ANG = 0.55 * D2R
        self.CURB_W, self.CURB_D = 0.22, 0.24
        # ---- cap ----
        self.CAP_AZ = 21 * D2R
        self.CAP_AF, self.CAP_AB, self.CAP_B = 1.28, 1.48, 1.28
        self.RIDGE_L = 1.0
        self.CAP_RISE = 1.18
        self.HUB_D, self.TILT = 1.95, 8 * D2R
        self.HOOD_XF, self.HOOD_YW = 1.15, 0.45
        self.TB_RW, self.TB_RH, self.TB_GAP = 0.10, 0.12, 0.028
        self.TB_X1 = -6.08
        # ---- rotor ----
        self.PHI_A = (135 - 8) * D2R
        self.W_WH = -0.33
        self.RING_IN, self.RING_OUT = 1.35, 3.20
        self.BL_R0, self.BL_R1 = 1.35, 3.90
        self.BL_W0, self.BL_W1 = 0.55, 1.175
        self.BL_PITCH = 13 * D2R
        self.BL_N = 16
        # ---- tail vane ----
        self.TV_S0 = 3.40
        self.TV_LEN = 2.65
        self.TV_H0 = (-0.62, 0.78)
        self.TV_H1 = (-0.98, 1.22)
        # ---- rubble language (ensemble review 1: rough rubble like the keep / hut, not near-ashlar) ----
        self.rubble = dict(
            rough=1.0,
            plain=dict(hr=(0.085, 0.19), hbig=0.27, p_big=0.2, lr=(0.15, 0.62), p_tall=0.12, p_pin=0.2, wob=0.036,
                       wob_cap=0.42, wob2=0.009, pinch=0.3, pinch_w=(0.45, 0.95), h_min=0.035, p_long=0.15),
            spandrel=dict(hr=(0.08, 0.15), hbig=0.2, p_big=0.14, lr=(0.14, 0.55), p_tall=0.06, p_pin=0.16, wob=0.026,
                          wob_cap=0.4, wob2=0.006, pinch=0.25, pinch_w=(0.4, 0.8), h_min=0.035, p_long=0.15),
            emit=dict(p_tilt=0.26, dy=(-0.008, 0.016), follow=1.0, roll=2.0))
        if rubble:
            for k_, v_ in rubble.items():
                if isinstance(v_, dict):
                    self.rubble[k_] = dict(self.rubble[k_], **v_)
                else:
                    self.rubble[k_] = v_
        # ---- per-build state ----
        self.seed_salt = ""
        self.batch = []                 # BatchAcc parts in build order
        self.walls = []                 # rubble-wall rasters (drum, arcade backs)
        self.pool_parts = {}            # pooled variant batches (balusters, corbels, bolts)
        self.placements = []            # (part name, pool key, 4x4 matrix pre-lean, leaned)
        self.rule = (DetailRule(min_relief=min_relief, entrance_relief=entrance_relief,
                                entrance=(0.0, -self.R_BASE0), entrance_r=3.0, entrance_h=2.5)
                     if detail_rule else DetailRule.off())
        self.derive()
        self.RNG_BOLT = self.RNG("bolt_pool")
        self.parts = self.new_parts()

    # -------------------------------------------------------------------------------------------------------
    def RNG(self, name):
        """the seeded numpy Generator of a named generator (crc32 of the name + the component seed salt)."""
        return np.random.default_rng(zlib.crc32((name + self.seed_salt).encode("utf8")))

    @contextmanager
    def seeded(self, seed):
        """salt every generator a component draws from (None / '' keeps the default seeds)."""
        old = self.seed_salt
        self.seed_salt = "" if seed in (None, "") else "|" + str(seed)
        try:
            yield
        finally:
            self.seed_salt = old

    def set(self, **kw):
        """publish component parameters to the frame (unknown names raise) and re-derive the dependents."""
        for k_, v_ in kw.items():
            if not hasattr(self, k_):
                raise KeyError(f"unknown drum-frame parameter {k_!r}")
            setattr(self, k_, v_)
        self.derive()
        return self

    def derive(self):
        self.R_DOOR = float(R_out(self, 1.0))
        self.RREF = self.R_BASE0 - 0.07
        self.DZ = self.Z_CORN0 - 4.05
        self.OPENINGS = ([(0.0, partial(hw_door, self))]
                         + [(a, partial(hw_window, self, dz=dz, w=w)) for a, w, dz in win_list(self)]
                         + [(a, partial(hw_arch, self)) for a in self.ARCH_AZ])
        self.AP_A = math.atan2(self.AP_ZT - self.AP_ZE, self.AP_RE - self.AP_RT)
        self.TW_TAPER = (self.TW_A0 - self.TW_A1) / (self.TW_Z1 - self.TW_Z0)
        self.LEAN_PIVOT = np.array([0, 0, self.TW_Z0 - 0.15])
        self.LEAN_R = rotm(np.cross([0, 0, 1.0], self.LEAN_DIR), [self.LEAN_ANG])[0]
        self.CURB_R = self.TW_A1 + 0.04
        self.ZCT = self.TW_Z1 + 0.01
        self.Z_COLLAR = self.TW_Z1 - 1.15
        self.HDIR = np.array([math.sin(self.CAP_AZ), -math.cos(self.CAP_AZ), 0.0])
        self.YDIR = np.cross([0, 0, 1.0], self.HDIR)
        self.CAP_XC = (self.CAP_AF - self.CAP_AB) / 2
        self.XR0, self.XR1 = self.CAP_XC - self.RIDGE_L / 2, self.CAP_XC + self.RIDGE_L / 2
        self.CAP_EF, self.CAP_EB, self.CAP_SB = self.CAP_AF - self.XR1, self.CAP_AB + self.XR0, self.CAP_B
        self.CAP_ZE = self.ZCT + 0.24
        self.HUB_Z = self.CAP_ZE + 0.66
        self.HOOD_ZE, self.HOOD_ZR = self.CAP_ZE + 0.62 * self.CAP_RISE / 1.18, self.CAP_ZE + self.CAP_RISE - 0.12
        self.TB_X0 = -(self.CAP_AB - 0.35)
        self.SKIRT_R = self.CURB_R + self.CURB_W / 2 + 0.012
        self.TB_Z = self.ZCT + 0.09
        self.TB_YC = self.TB_GAP / 2 + self.TB_RW / 2
        self.CAP_DS, self.CAP_HS, self.CAP_TMAX = _cap_profile(self)
        self.VAL_Y, self.VAL_X = _valley_table(self)
        self.S_AX = math.cos(self.TILT) * self.HDIR + math.sin(self.TILT) * np.array([0, 0, 1.0])
        self.E1 = unit(np.cross(-self.S_AX, [0, 0, 1.0]))
        self.E2 = np.cross(self.E1, -self.S_AX)
        self.HUB = self.HDIR * self.HUB_D + np.array([0, 0, self.HUB_Z])
        self.ARM_R1 = self.RING_OUT + 0.15
        self.W_RING = self.W_WH - 0.058
        self.rule.entrance = (0.0, -self.R_BASE0)

    # -------------------------------------------------------------------------------------------------------
    def part(self, key, mats, **kw):
        """get or create the named object <PREFIX>_<key> (a BatchAcc) of a component."""
        if key not in self.parts:
            self.parts[key] = BatchAcc("%s_%s" % (self.prefix, key), mats, **kw)
            self.batch.append(self.parts[key])
        return self.parts[key]

    def new_parts(self):
        """the drum tower's named objects (components add their own through g.part())."""
        TW = ["M_timber_weathered"]
        spec = [("stones", "base_stones", ["M_stone"], {}), ("mortar", "base_mortar", ["M_mortar"], {}),
                ("dressed", "base_dressed", ["M_stone_dressed"], {}),
                ("interior", "interior", ["M_stone", "M_timber", "M_mortar"], {}),
                ("door", "door_leaf", TW, {}), ("door_iron", "door_iron", ["M_iron"], {}),
                ("step", "door_step", ["M_stone"], dict(moss=0.1)), ("curb", "curb", ["M_timber", "M_mortar"], {}),
                ("apron_frame", "apron_rafters", ["M_timber", "M_timber_weathered"], {}),
                ("apron", "apron_shingles", ["M_roof_shake"], {}), ("tower_boards", "tower_boards", TW, {}),
                ("tower_frame", "tower_frame", ["M_timber", "M_timber_weathered"], {}),
                ("tower_iron", "tower_iron", ["M_iron"], {}),
                ("cap_frame", "cap_frame", ["M_timber", "M_timber_weathered"], {}),
                ("cap_shingles", "cap_shingles", ["M_roof_shingle"], {}),
                ("cap_iron", "cap_iron", ["M_iron", "M_lead"], {}),
                ("windshaft", "windshaft", ["M_timber", "M_iron"], {}), ("poll_end", "poll_end", ["M_iron"], {}),
                ("rotor_iron", "rotor_iron", ["M_iron"], {}), ("wheel_rim", "wheel_rim", ["M_iron"], {}),
                ("wheel_blades", "wheel_blades", ["M_timber"], {}),
                ("wheel_spokes", "wheel_spokes", ["M_iron"], {}), ("props", "props", TW, {}),
                ("prop_anchors", "prop_anchors", ["M_stone", "M_timber_weathered", "M_iron", "M_earth"],
                 dict(moss=0.1)),
                ("prop_iron", "prop_iron", ["M_iron"], {}),
                ("moss", "moss_clumps", ["M_moss"], dict(angle=60.0))]
        self.parts = {}
        for key, name, mats, kw in spec:
            self.parts[key] = BatchAcc("%s_%s" % (self.prefix, name), mats, **kw)
            self.batch.append(self.parts[key])
        for L in "ABCD":
            self.part("wheel_arm_%s" % L, ["M_timber_weathered", "M_iron"])
        self.part("tail_boom", ["M_timber_weathered", "M_timber"])
        self.part("tail_vane", ["M_timber_weathered", "M_timber"], wear=0.55)
        self.part("tail_iron", ["M_iron"])
        return self.parts

    def is_leaned(self, p):
        return p.name.replace(self.prefix + "_", "").startswith(self.LEANED)


# =============================================================================================
# pooled variants (producer note 3): balusters, corbels, bolt heads -> village_kit.pools linked duplicates
# =============================================================================================
BOLT_POOL = [(0.016, 0.012), (0.018, 0.013), (0.020, 0.014), (0.020, 0.0145), (0.026, 0.020), (0.026, 0.019)]
POOL_MOSS = {"baluster": 0.35, "corbel": 0.3, "bolt": 0.2}


def pool_part(g, key, mats):
    """the BatchAcc a pooled variant `key` is modelled in (local coordinates); built once."""
    if key not in g.pool_parts:
        p = BatchAcc("%s_pool_%s" % (g.prefix, key), mats, mesh_only=True)
        p.zref = 2.6 if key.startswith("baluster") else (4.3 if key.startswith("corbel") else 11.0)
        g.pool_parts[key] = p
    return g.pool_parts[key]


def place_instance(g, name, key, R, t, leaned=False):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    g.placements.append((name, key, M, leaned))


def bolt_pool(g):
    """Six hex bolt-head / nut variants (radius, height; two chamfer styles), built once."""
    from ..tmplmesh import lathe
    for i, (rad, hgt) in enumerate(BOLT_POOL):
        key = "bolt_hex_%d" % i
        if key in g.pool_parts:
            continue
        p = pool_part(g, key, ["M_iron"])
        ch = 0.75 if i % 2 == 0 else 0.62
        prof = np.array([(0.0, -0.002), (rad, -0.002), (rad, hgt * 0.7), (rad * ch, hgt), (0.0, hgt)])
        P, T = lathe(prof[None], 6, caps=True)
        p.add(P, T, mat="M_iron", smooth="none", wear=0.4)


def inst_bolts(g, prefix, centers, normals, rad, leaned=True, rng=None):
    """Place pooled hex heads (world centres + outward normals, pre-lean) as linked duplicates."""
    from ..tmplmesh import bolt_frames
    bolt_pool(g)
    centers = np.atleast_2d(centers)
    Rs = bolt_frames(normals)
    cand = [i for i, (r_, _) in enumerate(BOLT_POOL) if abs(r_ - rad) < 0.0025] or [2]
    for j in range(len(centers)):
        r_ = rng if rng is not None else g.RNG_BOLT
        k = cand[int(r_.integers(0, len(cand)))]
        ang = r_.uniform(0, PI / 3)
        place_instance(g, "%s_%03d" % (prefix, len([q for q in g.placements if q[0].startswith(prefix)])),
                       "bolt_hex_%d" % k, Rs[j] @ rotm([0, 0, 1], [ang])[0], centers[j], leaned)


def kpart(g, parts, key, mats, **kw):
    """get or create the named object (BatchAcc) `<PREFIX>_<key>` of a component."""
    return g.part(key, mats, **kw)


from ..split_stones import (stone_local)  # noqa: F401


def R_out(g, z):
    return g.R_BASE0 - (g.R_BASE0 - g.R_BASE1) * np.clip(z, 0, getattr(g, "BATTER_TOP", 4.6)) / g.Z_BATTER


def win_dz(g):
    """kit changes v1_stone_watchtower: the height offset of every slit window (g.WIN_DZ; None = all 0, the mill's
    windows at WIN z0..z1)."""
    dz = getattr(g, "WIN_DZ", None)
    return [0.0] * len(g.WIN_AZ) if dz is None else [float(d) for d in dz]


def win_list(g):
    """v1_stone_watchtower r2: every window of the drum as (azimuth rad, spec dict, dz).  Without g.WIN_SPEC every
    window uses the frame's g.WIN (the mill's slit) shifted by win_dz(); with it, window k uses g.WIN_SPEC[k]
    (absolute heights, dz 0)."""
    spec = getattr(g, "WIN_SPEC", None)
    if spec is None:
        return [(a, g.WIN, dz) for a, dz in zip(g.WIN_AZ, win_dz(g))]
    return [(a, s, 0.0) for a, s in zip(g.WIN_AZ, spec)]


WINDOW_FW = dict(slit=[(0.17, 0.21), (0.21, 0.17)], lookout=[(0.20, 0.26), (0.26, 0.20)])
"""jamb-block face widths (left, right) per jamb course, alternating course by course."""


def window_spec(clear_w=0.16, clear_h=0.55, sill=1.30, kind="slit", fw=None, lintel_h=None, course_h=0.30,
                splay=0.22, room=1.5):
    """KIT (v1_stone_watchtower r2): a drum window of any size, as a dict build_slit_windows / hw_window /
    inside_clear / the wall core read.  clear_w x clear_h is the clear opening, `sill` its bottom (m above ground).
    kind "slit": a splayed embrasure closed 0.62 m in (the mill's slit, `splay` = half width at the back);
    kind "lookout": a straight reveal through the wall and a closed dark room `room` m deep behind the face
    (producer note 6).  The jamb courses (about `course_h` each), the sill / lintel sizes and the rubble keep-out
    bands are derived from the clear size, so a slit, a stair light and a lookout come from one module."""
    cw = clear_w / 2.0
    z0, z1 = float(sill), float(sill) + clear_h
    n = max(2, int(round(clear_h / course_h)))
    jz = [float(z) for z in np.linspace(z0, z1, n + 1)]
    fw = fw or WINDOW_FW["lookout" if kind == "lookout" else "slit"]
    fmax = max(max(p) for p in fw)
    lh = lintel_h if lintel_h is not None else (0.18 if kind == "slit" else 0.24)
    sill_w = 2 * (cw + fmax) + 0.04
    lintel_w = 2 * (cw + fmax) + 0.16
    return dict(kind=kind, cw=cw, z0=z0, z1=z1, jz=jz, fw=fw, splay=splay, room=room, sill_w=sill_w,
                lintel_w=lintel_w, lintel_h=lh, z_sill=z0 - 0.065, z_lintel=z1 + 0.005 + lh / 2,
                zb=z0 - 0.13, zt=z1 + lh + 0.015, hw_sill=sill_w / 2, hw_jamb=cw + fmax + 0.01, hw_lintel=lintel_w / 2)


def cyl_place(g, P, th, zc, yoff, Rfun=None):
    """Map local stone coords onto the drum. x -> arc length, y -> outward, z -> up."""
    Rfun = partial(R_out, g) if Rfun is None else Rfun
    z = zc[:, None] + P[:, :, 2]
    R = Rfun(z)
    r = R + yoff[:, None] + P[:, :, 1]
    thv = th[:, None] + P[:, :, 0] / R
    return np.stack([r * np.sin(thv), -r * np.cos(thv), z], 2)


def open_place(g, P, th0, xc, zc, yoff, Rfun=None):
    """Opening-aligned mapping: parallel reveals (x lateral, straight), front follows the drum."""
    Rfun = partial(R_out, g) if Rfun is None else Rfun
    x = xc[:, None] + P[:, :, 0]
    z = zc[:, None] + P[:, :, 2]
    R = Rfun(z)
    d = np.sqrt(np.maximum(R ** 2 - x ** 2, 0.01)) + yoff[:, None] + P[:, :, 1]
    c, s = np.cos(th0)[:, None], np.sin(th0)[:, None]
    return np.stack([x * c + d * s, x * s - d * c, z], 2)


def free_on_circle(Rmid, blocks):
    """blocks: list of (u_centre, half_width) in arc length at Rmid -> free spans (cyclic)."""
    C = 2 * PI * Rmid
    if not blocks:
        return None
    iv = sorted(((uc - hw) % C, hw * 2) for uc, hw in blocks)
    # merge on a circle by unrolling from the first block start
    start = iv[0][0]
    segs = sorted(((a - start) % C, (a - start) % C + w) for a, w in iv)
    merged = []
    for a, b in segs:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    free = []
    for i, (a, b) in enumerate(merged):
        nxt = merged[i + 1][0] if i + 1 < len(merged) else C
        if nxt > b:
            free.append((b + start, nxt + start))
    return free


MORTAR_RECESS = 0.014


def hw_door(g, z):
    z = np.asarray(z, float)
    out = np.zeros_like(z)
    for s in (-1, 1):
        pass
    for i in range(4):
        m = (z >= g.DOOR_JZ[i] - 0.01) & (z < g.DOOR_JZ[i + 1])
        out = np.where(m, g.DOOR_CW + max(g.DOOR_JAMBS[-1][i], g.DOOR_JAMBS[1][i]) + 0.012, out)
    ro = g.DOOR_CW + g.DOOR_RING[1] + 0.012
    dz = z - g.ZS_DOOR
    arch = np.sqrt(np.clip(ro ** 2 - dz ** 2, 0, None))
    out = np.where(z >= g.ZS_DOOR, np.where(dz < ro, arch, 0.0), out)
    return out


def hw_window(g, z, dz=0.0, w=None):
    """half width the rubble leaves free round a window at height z (sill band, jambs, lintel band).  w: the
    window's spec (window_spec; None = g.WIN, the mill's slit, whose bands are the literal numbers)."""
    W = g.WIN if w is None else w
    z = np.asarray(z, float) - dz
    out = np.zeros_like(z)
    out = np.where((z >= W.get("zb", 1.17)) & (z < W["z0"]), W.get("hw_sill", 0.31), out)
    out = np.where((z >= W["z0"]) & (z < W["z1"]), W.get("hw_jamb", W["cw"] + 0.22), out)
    out = np.where((z >= W["z1"]) & (z < W.get("zt", 2.04)), W.get("hw_lintel", 0.37), out)
    return out


def hw_arch(g, z):
    z = np.asarray(z, float)
    out = np.where((z >= g.ARCH["z0"] - 0.01) & (z < g.ARCH["zs"]), g.ARCH["cw"] + g.ARCH["fw"] + 0.012, 0.0)
    ro = g.ARCH["cw"] + g.ARCH["ring"][1] + 0.012
    dz = z - g.ARCH["zs"]
    return np.where(z >= g.ARCH["zs"], np.sqrt(np.clip(ro ** 2 - dz ** 2, 0, None)), out)


def free_fn_drum(g, rng, extra_rad=0.0):
    def f(zb, zt):
        zz = np.linspace(zb, zt, 5)
        Rm = float(R_out(g, (zb + zt) / 2)) + extra_rad
        blocks = []
        for th, fn in g.OPENINGS:
            w = fn(zz)
            if w.max() <= 0:
                continue
            hw = 0.5 * (w.max() + w.mean())
            blocks.append((th * Rm, hw))
        if not blocks:
            u0 = rng.uniform(0, 2 * PI * Rm)
            return [(u0, u0 + 2 * PI * Rm)]
        return free_on_circle(Rm, blocks)
    return f


def wall_relief(u, z, k=0.0):
    """Low-frequency +-5 mm relief of the mortar body."""
    return 0.0028 * np.sin(u * 7.1 + z * 3.3 + k) + 0.0022 * np.sin(u * 4.3 - z * 8.9 + 1.7 + k)


FOOT_PIN_Z = 0.47           # round 6: below this the drum's bed joints get sparse wedge pinners only


def drum_to_world(g, u, z, d):
    th = np.asarray(u) / g.RREF
    r = R_out(g, z) + d
    return np.stack([r * np.sin(th), -r * np.cos(th), np.asarray(z, float) + 0 * th], -1)


def drum_to_wall(g, W):
    W = np.asarray(W)
    th = np.arctan2(W[..., 0], -W[..., 1])
    return th * g.RREF, W[..., 2], np.hypot(W[..., 0], W[..., 1]) - R_out(g, W[..., 2])


def drum_mortar_d(g, u, z):
    z = np.asarray(z, float)
    rec = -0.022 - 0.023 * (1 - smoothstep(0.45, 0.68, z))        # raked to 4.5 cm in the bottom 0.6 m
    foot = 0.065 - 0.042                                           # footing course projects 6.5 cm
    d = np.where(z < 0.40, foot, rec)
    band = (z > g.Z_BAND0 + 0.004) & (z < g.Z_BAND1 - 0.004)
    d = np.where(band, -0.085, d)                                  # behind the recessed ashlar of the balustrade band
    return d + (0.0 if g.rule.active else 1.0) * wall_relief(u, z)    # +-5 mm body relief: note 11 -> material


def arch_set(g, P_dr, rng, th0, ri, zs, nv, ring, Dv, jambs, Rfun, yfront=0.03, vert=False, style="dressed",
             min_relief=None, jamb_min_relief=None):
    """Dressed voussoir ring + jamb blocks for an arch at azimuth th0.
    jambs: dict side -> list of (z0, z1, face_width).  min_relief (producer note 11) defaults to the frame's
    threshold at the springing (1 cm for the entrance arch, 2 cm elsewhere).  jamb_min_relief (kit 1.4.0,
    optional): a separate threshold for the jamb blocks only (e.g. 0.035 drops their edge spalls -- the mill's
    round-7 'proud tabs' -- with every random draw unchanged); None = min_relief (old behaviour)."""
    if min_relief is None:
        R_ = float(R_out(g, zs))
        min_relief = float(relief_min(g, [R_ * math.sin(th0), -R_ * math.cos(th0), zs])[0])
    jmr = min_relief if jamb_min_relief is None else jamb_min_relief
    # voussoirs: widths vary +-25 %, key stone wider
    w = rng.uniform(0.75, 1.25, nv)
    w[nv // 2] = max(w[nv // 2], 1.0) * 1.15
    edges = np.concatenate([[0], np.cumsum(w)]) / w.sum() * PI
    for i in range(nv):
        a0, a1 = edges[i], edges[i + 1]
        ac = (a0 + a1) / 2
        dep = ring[0] + (ring[1] - ring[0]) * math.sin(ac) + rng.uniform(-0.012, 0.012)
        rm = ri + dep / 2
        L = (a1 - a0) * rm - 0.012
        P, T = stone_local(rng, [L], [dep], [Dv], style, rot_deg=(0.1, 0.1, 0.1), min_relief=min_relief)
        rho = ri + dep / 2 + P[:, :, 2]
        al = ac - P[:, :, 0] / rm
        E = np.stack([rho * np.cos(al), P[:, :, 1], zs + rho * np.sin(al)], 2)
        W = open_place(g, E, np.array([th0]), np.array([0.0]), np.array([0.0]), np.array([yfront]), Rfun)
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # jambs
    for s, blocks in jambs.items():
        for (z0, z1, fw) in blocks:
            H = z1 - z0 - 0.012
            # more wear on the lower jambs (scuffed by carts / feet): 3-4 crisp spalls
            P, T = stone_local(rng, [fw], [H], [Dv], style, rot_deg=(0.1, 0.1, 0.15), min_relief=jmr,
                               spall=(3, 4) if z0 < 1.0 else None)
            W = open_place(g, P, np.array([th0]), np.array([s * (ri + fw / 2)]), np.array([(z0 + z1) / 2]),
                           np.array([yfront]), Rfun)
            P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")


def inside_clear(g, th, z):
    """Is point (azimuth th, height z) on the drum face inside a clear opening?"""
    R = float(R_out(g, z))

    def lat(th0):
        d = (th - th0 + PI) % (2 * PI) - PI
        return R * math.sin(d), abs(d) < PI / 2

    x, ok = lat(0.0)
    if ok and abs(x) < g.DOOR_CW and g.Z_TH - 0.2 <= z <= g.ZS_DOOR + math.sqrt(max(g.DOOR_CW ** 2 - x ** 2, 0)):
        return True
    for a, W, dz in win_list(g):
        x, ok = lat(a)
        if ok and abs(x) < W["cw"] and W["z0"] + dz <= z <= W["z1"] + dz:
            return True
    for a in g.ARCH_AZ:
        x, ok = lat(a)
        if ok and abs(x) < g.ARCH["cw"] and g.ARCH["z0"] <= z <= g.ARCH["zs"] + math.sqrt(max(g.ARCH["cw"] ** 2 - x ** 2, 0)):
            return True
    return False


TAN225 = math.tan(PI / 8)


COS225 = math.cos(PI / 8)


def lean(g, V):
    return (V - g.LEAN_PIVOT) @ g.LEAN_R.T + g.LEAN_PIVOT


def TZ(g, z_old):
    """Map round-1 tower heights (5.40 .. 10.55) onto the taller tower."""
    return g.TW_Z0 + (np.asarray(z_old, float) - 5.40) * (g.TW_Z1 - g.TW_Z0) / (10.55 - 5.40)


def tw_a(g, z):
    return g.TW_A0 - (np.asarray(z, float) - g.TW_Z0) * g.TW_TAPER


def face_axes(k):
    phi = k * PI / 4
    n = np.array([math.sin(phi), -math.cos(phi), 0.0])
    t = np.array([math.cos(phi), math.sin(phi), 0.0])
    return n, t


def face_map(g, k, l, z, y):
    """Point on tower face k: lateral l (scaled with taper about z), height z, outward y from frame line."""
    n, t = face_axes(k)
    a = tw_a(g, z)
    return (a + y)[..., None] * n + l[..., None] * t + z[..., None] * np.array([0, 0, 1.0])


def post_geom(g, z):
    """Corner post centre radius (along the bisector) at height z (posts are 0.2 x 0.2)."""
    return (tw_a(g, z) + 0.03) / COS225 + 0.02 - 0.10


def _cap_profile(g):
    ds = np.linspace(0, g.CAP_SB, 800)

    def h_for(tmax):
        th = (25 + (tmax - 25) * smoothstep(0.0, 0.45, ds)) * D2R
        return np.concatenate([[0], np.cumsum(np.tan(th[1:]) * np.diff(ds))])
    lo, hi = 25.0, 85.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if h_for(mid)[-1] < g.CAP_RISE:
            lo = mid
        else:
            hi = mid
    return ds, h_for(lo), lo


def cap_h(g, t):
    """Height above the eave at normalised hip coordinate t (0 eave .. 1 ridge)."""
    d = np.asarray(t, float) * g.CAP_SB
    return np.where(d < 0, d * math.tan(25 * D2R), np.interp(d, g.CAP_DS, g.CAP_HS))


def cap_dh(g, t):
    """d(height)/dt."""
    t = np.asarray(t, float)
    return (cap_h(g, t + 1e-3) - cap_h(g, t - 1e-3)) / 2e-3


def cap_t(g, x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return np.minimum(np.minimum((g.CAP_B - np.abs(y)) / g.CAP_SB, (g.CAP_AF - x) / g.CAP_EF), (g.CAP_AB + x) / g.CAP_EB)


def cap_z(g, x, y):
    return g.CAP_ZE + cap_h(g, np.minimum(cap_t(g, x, y), 1.0))


def hood_z(g, y):
    return g.HOOD_ZR - (g.HOOD_ZR - g.HOOD_ZE) * np.abs(y) / (g.HOOD_YW + 0.03)


def _valley_table(g):
    ys = np.linspace(0, g.HOOD_YW + 0.06, 40)
    xv = []
    for y in ys:
        lo, hi = g.XR0, g.HOOD_XF + 0.2
        assert cap_z(g, lo, y) > hood_z(g, y) and cap_z(g, hi, y) < hood_z(g, y), "hood does not meet the cap roof"
        for _ in range(50):
            m = (lo + hi) / 2
            if cap_z(g, m, y) > hood_z(g, y):
                lo = m
            else:
                hi = m
        xv.append((lo + hi) / 2)
    return ys, np.array(xv)


def x_valley(g, y):
    return np.interp(np.abs(np.asarray(y, float)), g.VAL_Y, g.VAL_X)


def capw(g, P):
    """cap-local (x', y', z) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return P[..., 0:1] * g.HDIR + P[..., 1:2] * g.YDIR + P[..., 2:3] * np.array([0, 0, 1.0])


def to_cap_local(g, V):
    V = np.asarray(V)
    return np.stack([V @ g.HDIR, V @ g.YDIR, V[:, 2]], 1)


def rotw(g, P):
    """rotor-local (x, y, w) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return g.HUB + P[..., 0:1] * g.E1 + P[..., 1:2] * g.E2 + P[..., 2:3] * g.S_AX


def er_t(phi):
    return np.array([math.cos(phi), math.sin(phi), 0.0]), np.array([-math.sin(phi), math.cos(phi), 0.0])


def stock_w(i):
    return 0.30 if i % 2 == 0 else 0.0


def stock_depth(g, r, i=0):
    return 0.30 - 0.13 * np.clip(r, 0, g.ARM_R1) / g.ARM_R1


def loc3(er, t, r, l, w):
    return np.asarray(r)[..., None] * er + np.asarray(l)[..., None] * t + np.asarray(w)[..., None] * np.array([0, 0, 1.0])


def hex_heads(g, part, centers, normals, rad=0.02, hgt=0.012):
    """Hex bolt heads / nuts (rotor-local centres + normals) -> pooled linked duplicates (producer note 3)."""
    centers = rotw(g, np.atleast_2d(centers))
    normals = rotw(g, np.atleast_2d(normals)) - g.HUB
    inst_bolts(g, g.prefix + "_rotor_bolt", centers, normals, rad, leaned=True, rng=g.RNG_BOLT)


# =============================================================================================
# component parameters -> frame (door / arcade), shared by round_stone_drum, arched_door and blind_arcade
# =============================================================================================
def door_params(g, width=None, spring=None, reveal=None, ring=None):
    """publish arched-door parameters: clear width, springing height above the threshold, voussoir ring depths."""
    kw = {}
    if width is not None:
        kw["DOOR_CW"] = width / 2
    if spring is not None:
        zs = g.Z_TH + spring
        kw["ZS_DOOR"] = zs
        kw["DOOR_JZ"] = [0.0] + [zs * f for f in (0.44 / 1.79, 0.86 / 1.79, 1.30 / 1.79)] + [zs]
    if ring is not None:
        kw["DOOR_RING"] = tuple(ring)
    if kw:
        g.set(**kw)


def arcade_params(g, n=None, clear_w=None, clear_h=None, z_sill=None, az0=18.0, ring=None, pier_fw=None):
    """publish blind-arcade parameters: n bays from azimuth az0 (deg), clear width / height, sill height."""
    a = dict(g.ARCH)
    if clear_w is not None:
        a["cw"] = clear_w / 2
    if z_sill is not None:
        a["z0"] = z_sill
    if clear_h is not None or z_sill is not None or clear_w is not None:
        h = clear_h if clear_h is not None else (g.ARCH["zs"] + g.ARCH["cw"] - g.ARCH["z0"])
        a["zs"] = a["z0"] + h - a["cw"]
        a["jz"] = [a["z0"], 0.5 * (a["z0"] + a["zs"]), a["zs"]]
    if ring is not None:
        a["ring"] = tuple(ring)
    if pier_fw is not None:
        a["fw"] = pier_fw
    kw = dict(ARCH=a)
    if n is not None:
        kw["ARCH_AZ"] = [(az0 + 360.0 / n * k) * D2R for k in range(n)]
    g.set(**kw)


# =============================================================================================
# finishing step: every BatchAcc part -> a mesh object, pooled variants -> linked duplicates
# =============================================================================================
def drum_finish(g, checks=True):
    """Build every component part of the frame into its named mesh object (the leaned parts -- tower, cap, rotor,
    tail -- through the tower lean), the pooled variants (balusters, corbels, bolt heads) through village_kit.pools
    as linked duplicates in <PREFIX>_kit_instances, and run the rotor clearance checks (spec G / I)."""
    import bpy
    from mathutils import Matrix
    if checks:
        from .rotor_checks import rotor_clearance
        rotor_clearance(g)
    for k in ("step", "prop_anchors"):
        if k in g.parts:
            g.parts[k].zmin = -0.005          # bedded pieces feather 5 mm into the ground (no crease)
    total = 0
    for p in g.batch:
        ob = p.build(g.coll, post=partial(lean, g) if g.is_leaned(p) else None, hygiene=g.hygiene)
        if ob is None:
            continue
        g.objects[p.name] = ob
        ntri = sum(len(pp.vertices) - 2 for pp in ob.data.polygons)
        total += ntri
        log("%-28s tris %8d  (degenerate faces removed %d, on-ground faces culled %d, slivers alt<0.1mm %d, "
            "area<1e-8 %d)" % (p.name, ntri, p.n_degenerate, p.n_ground, p.n_alt, p.n_area))
    # pooled variants -> village_kit.pools meshes; placements -> linked duplicates (producer note 3)
    L4 = np.eye(4)
    L4[:3, :3] = g.LEAN_R
    L4[:3, 3] = g.LEAN_PIVOT - g.LEAN_R @ g.LEAN_PIVOT
    used = {}
    for (name, key, M, leaned) in g.placements:
        pp = g.pool_parts[key]
        kind = key.split("_")[0]
        me = g.pools.mesh(key.rsplit("_", 1)[0], int(key.rsplit("_", 1)[1]), lambda acc, k, pp=pp: fill_acc(pp, acc),
                          sharp=pp.angle, moss=POOL_MOSS.get(kind, 0.2))
        Mf = L4 @ M if leaned else M
        part = name.replace(g.prefix + "_", "", 1).rsplit("_", 1)[0]
        g.pools.place(me, part, Mf[:3, :3], Mf[:3, 3])
        used[key] = used.get(key, 0) + 1
    n_obj = len(g.coll.all_objects)
    log("OBJECTS %d (%d linked duplicates of %d pooled variant meshes: %s)"
        % (n_obj, g.pools.n_inst, len(g.pools), ", ".join("%s x%d" % kv for kv in sorted(used.items()))))
    bpy.context.view_layer.update()
    return total


# =============================================================================================
# producer note 11: the modelled-relief threshold at a place on the building
# =============================================================================================
def relief_min(g, P):
    """per-point relief threshold (m) of the frame's DetailRule: 2 cm, 1 cm in the entrance zone (3 m round the
    door, 0-2.5 m high), 0 when the rule is off.  P (N, 3) or (3,) world points."""
    r = g.rule
    P = np.atleast_2d(np.asarray(P, float))
    if not r.active:
        return np.zeros(len(P))
    d = np.hypot(P[:, 0] - r.entrance[0], P[:, 1] - r.entrance[1])
    ent = (d <= r.entrance_r) & (P[:, 2] >= -0.05) & (P[:, 2] <= r.entrance_h)
    return np.where(ent, r.entrance_relief, r.min_relief)


def relief_far(g):
    """the threshold away from the entrance (2 cm; 0 when the rule is off)."""
    return g.rule.min_relief if g.rule.active else 0.0


def relief_door(g):
    """the entrance-zone threshold (1 cm; 0 when the rule is off)."""
    return g.rule.entrance_relief if g.rule.active else 0.0


# =============================================================================================
# producer note 6: hidden-geometry cull (only pieces with a backing surface behind them)
# =============================================================================================
DRUM_CULL_TARGETS = ("arcade_dressed", "arcade_backs", "base_dressed", "cap_shingles")


def drum_views(g):
    """actor / crane viewpoints round a drum tower: rings at knee, waist, eye, raised-hand and first-floor height
    0.5-6 m out from the drum face, a band-level ring (the balustrade / arcade close-ups), crane rings, close views
    in front of the door and the six review cameras -- so the cull never removes what a camera can plausibly see."""
    from ..core import ring_views, review_cameras
    R = g.R_BASE0
    V = [ring_views((0, 0), [R + 0.5, R + 2.0, R + 5.0], [0.4, 1.65, 3.4], n=16),
         ring_views((0, 0), [R + 1.2, R + 2.6], [4.5, 6.0], n=12, phase=0.21),
         ring_views((0, 0), [R + 9.0], [6.0, 11.0, 16.0], n=12, phase=0.11)]
    fy = -g.R_DOOR
    V.append(np.array([(x, fy - d, z) for d in (0.5, 1.0, 2.0) for z in (0.4, 1.1, 1.7, 2.3) for x in (-0.9, 0.0, 0.9)]))
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in g.coll.all_objects if o.type == "MESH"])
    V.append(review_cameras(co.min(0), co.max(0)))
    return np.concatenate(V)


def drum_hidden_cull(g, targets=DRUM_CULL_TARGETS, procs=3):
    """KIT COMPONENT (post step, producer note 6): delete the faces of the named objects that no review / actor /
    crane viewpoint can see (core.visibility_cull).  Only pieces with a continuous backing behind them are
    culled -- the arcade and band dressed work and recess backs (wall-core ring) and the cap shingles (sarking
    deck) -- so no cull can open a see-through hole.  Run after drum_finish."""
    from ..core import visibility_cull
    names = [f"{g.prefix}_{t}" for t in targets]
    n = visibility_cull(names, extra_views=drum_views(g), procs=procs)
    log(f"hidden-geometry cull: -{n} polygons")
    return n
