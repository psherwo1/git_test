"""components.daub -- the wattle-and-daub infill of a round wall (client correction: MOSTLY INTACT DAUB).

make_daub_fields(g)  per bay coat field (s, z) -> distance inside the intact coat; negative in exposed patches.
                     Door bay: the ref2 eroded lower band (stepped fracture line); other bays: a bedded foot with
                     splash bites and the fallen-out patches listed in g.DAUB_PATCHES.
build_wattle(g, coll)      weave only where it shows (patches + under their margins, foot bites, door rope panels)
build_daub(g, coll)        the coat sheet per bay (+ clinging flakes)
build_inner_skin(g, coll)  interior daub face (dark backing behind the weave, the wall seen through the door)
plinth_under_coat(g, V)    cull predicate for plinth tops hidden behind the bedded coat foot
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import log

from ..core import _poly_area, _runs, _seg_dist, az_pt, fbm, grid_quads, n2, poly_sdf, smoothstep
from .frame import bay_s, wall_floor
from .wattle import arc_path, line_path, rope_panel, weave_panel


WALL_FINISH_R9 = dict(
    daub_relief=True,         # note 11 per vertex (DetailRule.min_at_v): entrance-zone hand relief >= 1 cm kept
    grid=(0.025, 0.016),      # intact-coat grid (m): outside / inside the entrance zone
    ent_dents=(0.010, 0.015),  # entrance zone: the r7 palm-press dents (same places), lifted to 1.0-1.5 cm deep
    ent_dabs=(0.010, 0.013),  # entrance zone: every `ent_dab_keep`-th r7 hand dab (same places), 1.0-1.3 cm proud
    ent_dab_keep=3,
    ent_soft=0.25,            # the entrance relief fades out over this distance (m) inside the zone boundary
    lumps_per_m2=(2.0, 3.0),  # every bay: sparse hand-applied lumps of 2.0-2.5 cm (>= 2 cm: kept anywhere)
    lump_amp=(0.020, 0.025), lump_sigma=(0.045, 0.08),
    sag=(0.011, 0.004),       # sag belly 1.1-1.5 cm
    flakes=False,             # director r7 #2 / r8 #5: clinging flakes read as leaves -> deleted
    foot_bites=6,             # director r7 #3 / r8 #6: at most 6 splash bites round the hut, 0-1 per bay, not adjacent
    bite_len=(0.20, 0.40), bite_h=(0.02, 0.04),
)
"""kit 1.3.0: the wall-finish switches (RoundFrame(wall_finish=...)); an empty dict keeps the 1.0.0 coat."""


def wall_finish_r9(**kw):
    d = dict(WALL_FINISH_R9)
    d.update(kw)
    return d


def _wf(g):
    return getattr(g, "wall_finish", None) or {}


WALL_FINISH_R10 = dict(
    WALL_FINISH_R9,
    patch_style="r10",        # director r9 #1 / audit r9: leaning chamfered spalled outlines (fracture_patch_r10)
    edge_w=(0.015, 0.050),    # visible fracture-face width varies 1.5-5 cm (no constant bevel ring)
    spall_w=0.055,            # ... and opens to ~5.5 cm at the spall scallops
    rag=0.005,                # +-5 mm mid-frequency raggedness (~11 cm wavelength) along every patch margin
    clumps=True,              # client correction: a few clinging clumps (>= 2 cm proud of the rods) at each break
    clump_n=(2, 3),           # per fallen-out patch / in the door-bay band
    clump_proud=(0.022, 0.034), clump_w=(0.06, 0.11), clump_h=(0.05, 0.085),
    stone_scars=0.008,        # plinth (components.plinth): scars >= 8 mm kept as spalls deepened to the note-11 threshold
)
"""kit 1.5.0 (hut round 10): WALL_FINISH_R9 + the ragged patch outlines and the clinging clumps (opt-in)."""


def wall_finish_r10(**kw):
    d = dict(WALL_FINISH_R10)
    d.update(kw)
    return d


WALL_FINISH_R11 = dict(
    WALL_FINISH_R10,
    door_break="r11",         # audit r10: the door-bay break rebuilt with _ragged_margin (straight 8-25 cm runs <= 12 deg,
                              # 1-2 row DIAGONAL steps, no U notch), a vertical-offset field (crisp tab corners) and a
                              # steep THICK edge face (coat >= 7.4 cm at the arris, face 1.5-3 cm tall, no feathering)
    door_edge_w=(0.030, 0.030), door_edge_T=0.074,   # the face ends ON the snapped -3 cm contour: no saw teeth
    clump_style="slab",       # audit r10: clumps are flat-fronted broken slabs hugging the rods (w:depth 1.6-2.4),
                              # at most one at a patch corner, the rest under a top margin
    ent_gate="feature",       # audit r10 (4): entrance-zone dents / dabs gated PER FEATURE by g.detail.min_at(centre):
                              # kept whole (>= 1 cm) or not at all -- no 0-1 cm fade band
    gate_fine=True,           # audit r10 (1-3): chinking / cheek-spall lumps + pits and the 9 mm step dish gated by
                              # g.detail.min_at
    stone_style="split",      # audit r10: plinth scars kept as PLANAR split facets (crisp creases, no soft dish, no
                              # widening), no 1 cm skin lumps, entrance stones meshed denser, flat bed / skirt <= 1 cm
    stone_scars_ent=0.006,    # entrance zone: scars >= 6 mm become >= 1 cm split facets
)
"""kit 1.6.0 (hut round 11): WALL_FINISH_R10 + the crisp door-bay break, slab clumps, per-feature entrance gating,
fine-relief gates and split-facet plinth stones (opt-in)."""


def wall_finish_r11(**kw):
    d = dict(WALL_FINISH_R11)
    d.update(kw)
    return d


def door_break_r11(g):
    """kit 1.6.0 (audit r10 / director r10 #1): the door-bay fracture line (s, z) as a function of s -- the patches'
    _ragged_margin language: straight runs of 8-25 cm sloping <= 12 deg, stepping 1-2 rod rows on 2-5.5 cm diagonal
    breaks (no U notch, no vertical merlon), an up- and a down-step never within 12 cm, the whole line tilted 1.5-3.5
    deg (no level sill), +-5 mm kinks.  z ~ 0.80 (ref2: the band left of the door, post to post)."""
    if "door_line_r11" not in g._EDGE_CURVE:
        sb0, sb1 = bay_s(g, len(g.POST_AZ) - 2)
        rs = np.random.RandomState(9017)
        line = _ragged_margin(g, rs, sb0 - 0.30, sb1 + 0.30, 0.80, levels=(-1, 1), run=(0.08, 0.25), min_pair=0.12,
                              jog=(0.02, 0.055), slope=0.2)
        tilt = rs.choice([-1, 1]) * math.tan(math.radians(rs.uniform(1.5, 3.5)))
        line[:, 1] += tilt * (line[:, 0] - 0.5 * (sb0 + sb1))
        # short straight kinks inside each run (a run is not a ruler), +-4 mm
        out = [line[0]]
        for i in range(1, len(line)):
            a, b = line[i - 1], line[i]
            if b[0] - a[0] > 0.10:
                t = rs.uniform(0.35, 0.65)
                out.append(a + (b - a) * t + np.array([0.0, rs.uniform(-0.004, 0.004)]))
            out.append(b)
        g._EDGE_CURVE["door_line_r11"] = np.array(out, float)
    return g._EDGE_CURVE["door_line_r11"]


def _ragged_margin(g, rs, xa, xb, z0, levels=(-1, 1), run=(0.05, 0.30), min_pair=0.12, jog=(0.02, 0.055),
                   slope=0.22):
    """kit 1.5.0: a patch margin from xa to xb along the rod rows -- runs of 5-30 cm, each sloping up to ~12 deg
    (no ruler), stepping 1 or 2 rod rows (at random) on a 2-5.5 cm DIAGONAL break (30-60 deg, never a vertical
    merlon side); an up-step and a down-step are never closer than min_pair.  Returns (k, 2) points (s, z)."""
    zc = z0 + rs.uniform(-0.006, 0.006)
    pts = [(xa, zc)]
    x = xa
    lv = 0
    last_dir, last_x = 0, -9.0
    while True:
        L = rs.uniform(*run)
        if x + L > xb - 0.05:
            break
        x += L
        zc = float(np.clip(zc + rs.uniform(-slope, slope) * L, z0 + lv * g.ROD_ROW_P - 0.02,
                           z0 + lv * g.ROD_ROW_P + 0.02))
        pts.append((x, zc))
        d = int(rs.choice([-1, 1]))
        if last_dir and d != last_dir and x - last_x < min_pair:
            d = last_dir
        step = d * int(rs.choice([1, 1, 2]))
        nl = int(np.clip(lv + step, levels[0], levels[1]))
        if nl == lv:
            nl = int(np.clip(lv - step, levels[0], levels[1]))
            d = -d
        jg = rs.uniform(*jog)
        zc = zc + (nl - lv) * g.ROD_ROW_P + rs.uniform(-0.006, 0.006)
        x += jg
        pts.append((x, zc))
        lv = nl
        last_dir, last_x = d, x
    zc = float(np.clip(zc + rs.uniform(-slope, slope) * (xb - x), z0 + lv * g.ROD_ROW_P - 0.02,
                       z0 + lv * g.ROD_ROW_P + 0.02))
    pts.append((xb, zc))
    return np.array(pts, float)


def _poly_angles(P):
    """interior angle (deg) at every vertex of a CCW polygon."""
    a = np.roll(P, 1, 0) - P
    c = np.roll(P, -1, 0) - P
    # CCW polygon: the interior angle runs counter-clockwise from the next edge to the previous one
    ang = np.degrees(np.arctan2(c[:, 0] * a[:, 1] - c[:, 1] * a[:, 0], (a * c).sum(1)))
    return np.mod(ang, 360.0)


def fracture_patch_r10(g, c_s, c_z, h_s, h_z, seed, open_below=False):
    """kit 1.5.0 (director r7 #1 / r9 #1): outline of a fallen-out daub patch that reads as a ragged BREAK, not a
    vent or grille.
      * the two sides lean 8-25 deg off vertical in opposite senses, each broken into 2-3 segments (+-9 deg);
      * top / bottom margins: sloping runs of 5-30 cm stepping 1-2 rod rows on diagonal breaks, no up / down pair
        closer than 12 cm (_ragged_margin);
      * the principal corners under 100 deg are chamfered (5-10 cm legs), >= 2 chamfers per patch, so at most one
        corner is near 90 deg;
      * 2-3 spall scallops 6-12 cm wide, 1.5-3 cm deep into the coat, on 15-25 % of the perimeter.
    open_below: a 'low' patch -- the bottom margin is dropped and the sides run straight down 1 m (the field then
    stops it at the stone tops).  Returns (CCW polygon (k, 2) in (s, z), spalls [(s, z, radius)])."""
    rs = np.random.RandomState(seed + 1000)
    zb, zt = c_z - h_z, c_z + h_z
    H = zt - zb
    # opposite senses, mostly converging upward (the chunk broke out wider at the bottom: no basket / vent), and
    # never mirror-symmetric: one side 8-14 deg, the other 16-25 deg
    sgn = 1 if rs.rand() < 0.8 else -1
    la_, lb_ = math.radians(rs.uniform(8, 14)), math.radians(rs.uniform(16, 25))
    if rs.rand() < 0.5:
        la_, lb_ = lb_, la_
    lean_l = la_ * sgn
    lean_r = -lb_ * sgn
    xl0 = c_s - h_s * rs.uniform(0.9, 1.04)
    xr0 = c_s + h_s * rs.uniform(0.9, 1.04)

    def side(x_mid, lean):
        n = int(rs.randint(2, 4))
        zs = np.r_[zb, zb + H * np.sort(rs.uniform(0.22, 0.78, n - 1)), zt]
        xs = [0.0]
        for k in range(n):
            a = lean + math.radians(rs.uniform(-9, 9))
            xs.append(xs[-1] + math.tan(a) * (zs[k + 1] - zs[k]))
        xs = np.array(xs)
        xs = xs - xs.mean() + x_mid
        return np.stack([xs, zs], -1)                 # bottom -> top
    Ls = side(xl0, lean_l)
    Rs = side(xr0, lean_r)
    top = _ragged_margin(g, rs, Ls[-1, 0], Rs[-1, 0], zt)
    top[:, 1] = zt - (top[:, 1] - zt)                       # mirrored: its steps go up into the coat
    tmax = 0.15 * H / max(h_s, 0.1)                         # the margins as a whole tilt 4-9 deg (no level sill)
    top[:, 1] += rs.choice([-1, 1]) * min(rs.uniform(0.07, 0.16), tmax) * (top[:, 0] - c_s)
    if open_below:
        low = zb - 1.0
        bot = np.array([[Ls[0, 0] + rs.uniform(-0.02, 0.02), low], [Rs[0, 0] + rs.uniform(-0.02, 0.02), low]])
    else:
        bot = _ragged_margin(g, rs, Ls[0, 0], Rs[0, 0], zb)
        bot[:, 1] = zb - (bot[:, 1] - zb)                   # steps go down into the coat
        bot[:, 1] += rs.choice([-1, 1]) * min(rs.uniform(0.07, 0.16), tmax) * (bot[:, 0] - c_s)
    # CCW: bottom (L->R), right side up, top (R->L), left side down
    if open_below:
        P = np.vstack([bot, Rs[:-1], top[::-1], Ls[::-1][1:]])
    else:
        P = np.vstack([bot, Rs[1:-1], top[::-1], Ls[::-1][1:-1]])
    keep = np.r_[True, np.hypot(*(np.diff(P, axis=0).T)) > 1e-4]
    P = P[keep]
    if _poly_area(P) < 0:
        P = P[::-1]
    # principal corners = the 4 sharpest; chamfer those under 100 deg (>= 2 chamfers)
    ang = _poly_angles(P)
    order = np.argsort(np.abs(ang - 90.0))
    lowz = P[:, 1] < zb - 0.5                                # open-below corners stay (buried under the stones)
    princ = [int(i) for i in order if not lowz[i]][:4]
    cut = [i for i in princ if ang[i] < 100.0]
    rest = [i for i in princ if i not in cut]
    while len(cut) < 2 and rest:
        cut.append(rest.pop(int(rs.randint(len(rest)))))
    for i in sorted(cut, reverse=True):
        n = len(P)
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        u = (a - b) / max(np.linalg.norm(a - b), 1e-9)
        v = (c - b) / max(np.linalg.norm(c - b), 1e-9)
        leg = rs.uniform(0.05, 0.10)
        la = min(leg, 0.45 * np.linalg.norm(a - b))
        lc = min(leg, 0.45 * np.linalg.norm(c - b))
        mid = b + 0.5 * (u * la + v * lc) + rs.uniform(-0.006, 0.006, 2)      # a broken chamfer, not a ruler cut
        P = np.vstack([P[:i], [b + u * la, mid, b + v * lc], P[i + 1:]])
    # spall scallops: 2-3 windows 6-12 cm wide, 15-25 % of the perimeter, bulging 1.5-3 cm into the coat
    Pc = np.vstack([P, P[:1]])
    seg = np.hypot(*(np.diff(Pc, axis=0).T))
    cum = np.r_[0.0, np.cumsum(seg)]
    per = cum[-1]
    ns = int(rs.randint(2, 4))
    widths = rs.uniform(0.06, 0.12, ns)
    widths *= np.clip(rs.uniform(0.15, 0.25) * per / widths.sum(), 0.6, 1.5)
    widths = np.clip(widths, 0.06, 0.16)
    starts = []
    for w_ in widths:
        for _ in range(40):
            t0 = rs.uniform(0, per - w_)
            mid_ = np.interp(t0 + w_ / 2, cum, np.r_[Pc[:, 1]])
            if open_below and mid_ < zb - 0.05:
                continue
            if all(t0 > s_ + ww_ + 0.06 or t0 + w_ < s_ - 0.06 for (s_, ww_) in starts):
                starts.append((t0, w_))
                break
    spalls = []
    if starts:
        dense_t = np.unique(np.r_[cum[:-1], np.concatenate([np.linspace(t0, t0 + w_, 9) for (t0, w_) in starts])])
        Q = np.stack([np.interp(dense_t, cum, Pc[:, 0]), np.interp(dense_t, cum, Pc[:, 1])], -1)
        Tn = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
        Tn /= np.maximum(np.linalg.norm(Tn, axis=1, keepdims=True), 1e-9)
        Nout = np.stack([Tn[:, 1], -Tn[:, 0]], -1)             # CCW polygon: outward (into the coat)
        disp = np.zeros(len(Q))
        for (t0, w_) in starts:
            dp = rs.uniform(0.015, 0.03)
            u = np.clip((dense_t - t0) / w_, 0, 1)
            sk = rs.uniform(0.35, 0.65)                          # the deepest point off-centre (conchoidal)
            prof = np.where(u < sk, u / sk, (1 - u) / (1 - sk))
            disp = np.maximum(disp, dp * np.clip(prof, 0, 1) ** 0.6 * ((dense_t >= t0) & (dense_t <= t0 + w_)))
            cq = Q[np.argmin(np.abs(dense_t - (t0 + sk * w_)))]
            spalls.append((float(cq[0]), float(cq[1]), float(0.5 * w_ + dp)))
        P = Q + Nout * disp[:, None]
    keep = np.r_[True, np.hypot(*(np.diff(P, axis=0).T)) > 1e-4]
    P = P[keep]
    return (P if _poly_area(P) > 0 else P[::-1]), spalls


def CLUMP_BAYS(g):
    """bays with exposed wattle (clinging daub clumps wrap their rods)."""
    return sorted({len(g.POST_AZ) - 2} | {p[0] for p in g.DAUB_PATCHES})


def stepped_break(g, seed, s_lo, s_hi, z0, rows=(0, 3), run=(0.08, 0.25), notch_c=(), notch_rows=(2, 3),
                  notch_w=(0.10, 0.17), min_tooth=0.13, max_row=6, jog=(0.0, 0.03)):
    """director r6 #1: a FRACTURE line across a daub coat -- straight runs of 8-25 cm, each 1-2 whole rod
    rows (ROD_ROW_P) above / below its neighbour, joined by short vertical or diagonal breaks (sharp
    corners), plus flat-floored notches stepped UP by 2-3 rows where a chunk fell.  No downward tooth
    (a run lower than both neighbours) narrower than min_tooth.  Returns the polyline (k, 2) in (s, z)."""
    rs = np.random.RandomState(seed)
    k = rs.randint(rows[0], rows[1] + 1)
    runs = []                                   # [x0, x1, level, is_notch]
    x = s_lo - 0.35
    notch_c = sorted(notch_c)
    ni = 0
    while x < s_hi + 0.35:
        L = rs.uniform(*run)
        if ni < len(notch_c) and x + L > notch_c[ni] - 0.06:
            # finish the run at the notch, then the notch itself (flat floor, stepped up)
            xn = max(x + 0.03, notch_c[ni] - 0.06)
            runs.append([x, xn, k, False])
            wn = rs.uniform(*notch_w)
            runs.append([xn, xn + wn, None, True])
            x = xn + wn
            ni += 1
            continue
        runs.append([x, x + L, k, False])
        x += L
        dk = rs.choice([-2, -1, -1, 1, 1, 2])
        k2 = int(np.clip(k + dk, rows[0], rows[1]))
        if k2 == k:
            k2 = int(np.clip(k - dk, rows[0], rows[1]))
        k = k2
    # merge consecutive non-notch runs that share a level
    out = []
    for r_ in runs:
        if out and not r_[3] and not out[-1][3] and out[-1][2] == r_[2]:
            out[-1][1] = r_[1]
        else:
            out.append(r_)
    runs = out
    for i, r_ in enumerate(runs):              # notch levels: 2-3 rows above the higher neighbour
        if r_[3]:
            nb_ = [runs[j][2] for j in (i - 1, i + 1) if 0 <= j < len(runs) and runs[j][2] is not None]
            r_[2] = int(min(max(nb_ + [0]) + rs.randint(notch_rows[0], notch_rows[1] + 1), max_row))
    # no narrow downward teeth: a short run below both neighbours is raised to the lower neighbour
    for _ in range(4):
        for i in range(1, len(runs) - 1):
            a_, b_, c_ = runs[i - 1][2], runs[i][2], runs[i + 1][2]
            if b_ < a_ and b_ < c_ and runs[i][1] - runs[i][0] < min_tooth:
                runs[i][2] = min(a_, c_)
    # breaks between runs: short vertical / diagonal jogs; every notch gets one clearly diagonal side
    # (a chunk fell along a crack, not a cut-out battlement)
    J = rs.uniform(*jog, len(runs) + 1)
    for i, r_ in enumerate(runs):
        if r_[3]:
            J[i + rs.randint(2)] = rs.uniform(0.03, 0.065)
    pts = []
    for i, (x0, x1, lv, _) in enumerate(runs):
        z = z0 + lv * g.ROD_ROW_P
        jl = J[i] * 0.5 if i > 0 else 0.0
        jr = J[i + 1] * 0.5 if i < len(runs) - 1 else 0.0
        xa, xb = x0 + jl, x1 - jr
        # a straight run is not a ruler: 1-2 interior kinks of +-3-6 mm
        nk = 1 + int(xb - xa > 0.16)
        xs = np.linspace(xa, xb, nk + 2)
        zz = z + np.r_[0.0, rs.uniform(-0.006, 0.006, nk), 0.0] + rs.uniform(-0.004, 0.004)
        pts.extend(zip(xs, zz))
    P = np.array(pts)
    keep = np.r_[True, np.hypot(*(np.diff(P, axis=0).T)) > 1e-4]
    return P[keep]


def daub_edge_door_bay(g):
    """coat polygon (s, z) of the big bay left of the door: everything ABOVE the stepped fracture line
    (z 0.72-0.95, director r6 #1) is coat; below it the wattle is exposed post to post (ref2)."""
    if "door" not in g._EDGE_CURVE:
        sb0, sb1 = bay_s(g, len(g.POST_AZ) - 2)
        rs = np.random.RandomState(9013)
        cs_ = sb0 + 0.12 + (sb1 - sb0 - 0.24) * (np.arange(3) + 0.5 + rs.uniform(-0.25, 0.25, 3)) / 3
        line = stepped_break(g, 9011, sb0, sb1, 0.72, rows=(0, 3), notch_c=cs_)
        g._EDGE_CURVE["door_line"] = line
        poly = np.vstack([line, [[line[-1, 0], 6.0], [line[0, 0], 6.0]]])
        g._EDGE_CURVE["door"] = poly[::-1] if _poly_area(poly) < 0 else poly
    return g._EDGE_CURVE["door"]


def fracture_patch(g, c_s, c_z, h_s, h_z, seed):
    """director r6 #3: outline of a fallen-out daub patch -- a broken irregular quadrilateral / pentagon
    (4-6 principal breaks, width:height = h_s:h_z), top and bottom margins near horizontal along the rod
    rows (stepped one row over 8-25 cm runs), sides vertical (along a stake) or one corner cut off on a
    30-60 deg diagonal; no notch, no convex corner sharper than ~80 deg.  Returns a CCW polygon (s, z)."""
    rs = np.random.RandomState(seed)
    xl = c_s - h_s * rs.uniform(0.92, 1.05)
    xr = c_s + h_s * rs.uniform(0.92, 1.05)
    zb = c_z - h_z
    zt = c_z + h_z
    H = zt - zb
    lean_l = rs.uniform(-0.02, 0.02)
    lean_r = rs.uniform(-0.02, 0.02)
    # one or two corners cut on a diagonal (pentagon / hexagon)
    c0 = int(rs.randint(4))
    corners = [c0] + ([(c0 + 2) % 4] if rs.rand() < 0.35 else [])      # a second cut only diagonally opposite
    cut = {}
    for c_ in corners:
        ang = math.radians(rs.uniform(35, 55))
        dz_ = H * rs.uniform(0.28, 0.45)
        cut[int(c_)] = (dz_ / math.tan(ang), dz_)          # (horizontal, vertical) legs

    def edge(xa, xb, z, sd):
        P = stepped_break(g, sd, xa + 0.36, xb - 0.36, z, rows=(-1, 0), run=(0.08, 0.25), jog=(0.0, 0.015),
                          max_row=1)
        P = P[(P[:, 0] > xa) & (P[:, 0] < xb)]
        return P
    # corners: 0 = BL, 1 = BR, 2 = TR, 3 = TL
    bl = (xl - lean_l, zb)
    br = (xr - lean_r, zb)
    tr = (xr + lean_r, zt)
    tl = (xl + lean_l, zt)
    pts = []
    # bottom edge, left -> right
    x0 = bl[0] + (cut[0][0] if 0 in cut else 0.0)
    x1 = br[0] - (cut[1][0] if 1 in cut else 0.0)
    if 0 in cut:
        pts.append((bl[0], bl[1] + cut[0][1]))
    pts.append((x0, zb))
    pts.extend(edge(x0, x1, zb, seed + 11)[:, :].tolist())
    pts.append((x1, zb))
    if 1 in cut:
        pts.append((br[0], br[1] + cut[1][1]))
    # right side up, top edge right -> left
    x2 = tr[0] - (cut[2][0] if 2 in cut else 0.0)
    x3 = tl[0] + (cut[3][0] if 3 in cut else 0.0)
    if 2 in cut:
        pts.append((tr[0], tr[1] - cut[2][1]))
    pts.append((x2, zt))
    top = edge(x3, x2, zt, seed + 13)
    top[:, 1] = zt - (top[:, 1] - zt)          # steps of the top margin go up into the coat
    pts.extend(top[::-1].tolist())
    pts.append((x3, zt))
    if 3 in cut:
        pts.append((tl[0], tl[1] - cut[3][1]))
    P = np.array(pts, float)
    keep = np.r_[True, np.hypot(*(np.diff(P, axis=0).T)) > 1e-4]
    P = P[keep]
    return P if _poly_area(P) > 0 else P[::-1]


def stepped_curve(g, seed_, lo_s, hi_s, lo, hi, run=(0.06, 0.22), soft=0.008):
    """piecewise-constant offsets (in rod rows, lo..hi) with 6-22 cm runs, softened by ~1 cm: a daub
    margin that breaks along the rod rows, with no grid comb."""
    rs = np.random.RandomState(seed_)
    ks = [lo_s - 0.3]
    while ks[-1] < hi_s + 0.3:
        ks.append(ks[-1] + rs.uniform(*run))
    lv = rs.randint(lo, hi + 1, len(ks)) * g.ROD_ROW_P
    fine = np.linspace(ks[0], ks[-1], 1500)
    v = lv[np.clip(np.searchsorted(ks, fine) - 1, 0, len(ks) - 1)].astype(float)
    sig = soft / (fine[1] - fine[0])
    kk = np.arange(-int(3 * sig), int(3 * sig) + 1)
    ker = np.exp(-0.5 * (kk / sig) ** 2)
    ker /= ker.sum()
    v = np.convolve(np.pad(v, len(kk) // 2, mode="edge"), ker, mode="valid")
    return fine, v


def daub_hole(g, c_s, c_z, h_s, h_z, seed, floor=None):
    """field of one exposed-wattle patch: NEGATIVE inside the hole (~ -distance to its broken margin),
    positive in the intact coat.  The outline is a FRACTURE polygon (9-14 straight-ish breaks meeting
    at sharp corners, 2-3 deep re-entrant notches where a chunk fell), never a rounded blob; its top and
    bottom margins are shifted in 6-22 cm runs by whole rod rows (the coat breaks along the rows); fine
    ragged noise.
    floor(s): a "low" patch is open down to the stone tops (the coat broken away above the plinth)."""
    st_top = stepped_curve(g, seed + 1, c_s - h_s, c_s + h_s, 0, 1)
    st_bot = stepped_curve(g, seed + 2, c_s - h_s, c_s + h_s, 0, 1)
    rs = np.random.RandomState(seed + 3)
    nk = rs.randint(9, 15)
    th = np.sort(rs.uniform(0, 2 * np.pi, nk) * 0.0 + (np.arange(nk) + rs.uniform(-0.3, 0.3, nk)) * 2 * np.pi / nk)
    th = th + rs.uniform(0, 2 * np.pi)
    rr = rs.uniform(0.72, 1.12, nk)
    notch = rs.choice(nk, rs.randint(2, 4), replace=False)
    rr[notch] *= rs.uniform(0.55, 0.75, len(notch))
    P = np.stack([c_s + h_s * rr * np.cos(th), c_z + h_z * rr * np.sin(th)], -1)
    if floor is not None:                                      # open to the stones: drop the lower half
        P = P[P[:, 1] >= c_z - 0.2 * h_z]
        P = P[np.argsort(np.arctan2(P[:, 1] - c_z, P[:, 0] - c_s))]
        lo_s, hi_s = P[:, 0].min(), P[:, 0].max()
        P = np.vstack([[[hi_s + rs.uniform(-0.03, 0.03), c_z - 1.0]], P, [[lo_s + rs.uniform(-0.03, 0.03), c_z - 1.0]]])
        P = P[np.argsort(np.arctan2(P[:, 1] - c_z, P[:, 0] - c_s))]

    def f(s, z):
        s = np.asarray(s, float)
        z = np.asarray(z, float)
        ze = z - np.where(z > c_z, -np.interp(s, *st_top), np.interp(s, *st_bot))
        inside = poly_sdf(s, ze, P)
        if floor is not None:
            inside = np.minimum(inside, z - (floor(s) - 0.06))
        # (the clinging daub is modelled as torn sleeves wrapped round the exposed rods, see build_daub)
        return -inside + 0.005 * n2(s * 18.0, z * 18.0, seed + 6)
    return f


def coat_floor(g, s):
    """stone top under the daub coat face (r = R_WALL + COAT_R_NOM) at arc length s: the coat foot is
    bedded onto it (director r6 #5).  Sampled once from the plinth BVH."""
    if "s" not in g.FOOT:
        from mathutils import Vector
        bvh = g.PL_TOP["bvh"]
        sg = np.arange(0.0, 2 * np.pi * g.R_WALL + 0.005, 0.005)
        zs = np.full(len(sg), np.nan)
        for i, s_ in enumerate(sg):
            a_ = s_ / g.R_WALL
            best = None
            for rr_ in (g.R_WALL + g.COAT_R_NOM - 0.012, g.R_WALL + g.COAT_R_NOM + 0.006):
                hit = bvh.ray_cast(Vector((math.sin(a_) * rr_, -math.cos(a_) * rr_, 1.5)), Vector((0, 0, -1.0)), 2.0)
                if hit[0] is not None:
                    best = hit[0][2] if best is None else max(best, hit[0][2])
            if best is not None:
                zs[i] = best
        wf = wall_floor(g, sg)
        zs = np.where(np.isnan(zs), wf - 0.03, zs)
        zs = np.clip(zs, wf - 0.07, wf + 0.03)
        g.FOOT["s"], g.FOOT["z"] = sg, zs
    return np.interp(np.mod(np.asarray(s, float), 2 * np.pi * g.R_WALL), g.FOOT["s"], g.FOOT["z"])


def low_margin(g, bay, seed, n_bites=(1, 2), bite_len=(0.10, 0.26), bite_h=(0.03, 0.065), bed=0.03, shoulder=6):
    """director r6 #5: the coat foot is BEDDED onto the stone tops (it runs `bed` into the stone, pressed
    into the joints) along >= 70 % of the bay; the bottom rod row shows only in 1-2 splash-eroded bites,
    each 10-26 cm long and 3-6.5 cm tall (flat-ish crown, ragged), placed at random along the bay (no
    rhythm with the posts).  Returns e(s): the coat's lower margin."""
    bs0, bs1 = bay_s(g, bay)
    rs = np.random.RandomState(seed)
    nb_ = n_bites[0] + int(rs.rand() < 0.45) * (n_bites[1] - n_bites[0])
    Ls = rs.uniform(*bite_len, nb_)
    if nb_ > 0:
        Ls *= min(1.0, 0.27 * (bs1 - bs0 - 0.2) / Ls.sum())    # bedded along >= ~70 % of the bay
    bites = []
    for k in range(nb_):
        L = max(Ls[k], bite_len[0])
        for _ in range(30):
            c_ = rs.uniform(bs0 + 0.15 + L / 2, bs1 - 0.15 - L / 2)
            if all(abs(c_ - b_[0]) > 0.3 for b_ in bites):
                break
        bites.append((c_, L, rs.uniform(*bite_h), rs.uniform(0.25, 0.45)))

    def e(s):
        s = np.asarray(s, float)
        fl = coat_floor(g, s)
        out = fl - bed + 0.006 * n2(s * 23.0, 4.1, seed + 2)
        for (c_, L, h_, sk) in bites:
            u = (s - c_) / (L / 2)
            # flat-ish crown with ragged, steep-ish shoulders (splash-eroded scallop), slightly skewed
            u = np.where(u > 0, u * (1 + sk), u * (1 - sk * 0.5))
            prof = np.clip(1 - np.abs(u) ** shoulder, 0, 1) ** 0.3
            hh = h_ * prof * (1 + 0.15 * n2(s * 40.0, c_, seed + 3)) + 0.003 * n2(s * 70.0, c_, seed + 4)
            out = np.where(prof > 0.02, np.maximum(out, fl + hh), out)
        return out
    e.bites = bites
    return e


def make_daub_fields(g):
    """every bay is daubed (client r6); field(s, z) ~ distance inside the intact coat (m), negative in the
    exposed patches.  Door bay: the ref2 eroded lower band (post to post), now a stepped fracture line
    (director r6 #1).  Other bays: a bedded foot with a few splash bites (r6 #5) and the fallen-out
    patches (fracture polygons, r6 #3)."""
    nb = len(g.POST_AZ) - 1
    door_bay = nb - 1                      # between POST_AZ[-2] and POST_AZ[-1] (az -45..-21)
    if _wf(g).get("door_break") == "r11":
        # kit 1.6.0: VERTICAL offset from the ragged break line -- its iso-contours are translated copies of the
        # line, so the fracture face keeps crisp tab corners (a Euclidean distance rounds every convex corner by
        # the face width)
        dl_ = door_break_r11(g)
        # slope-normalised (each segment's perpendicular distance, mitred at the corners): the fracture face has the
        # same width on the steep diagonal steps as on the runs, so the arris snap catches every step
        sf_ = np.arange(dl_[0, 0], dl_[-1, 0], 0.002)
        seg_ = np.clip(np.searchsorted(dl_[:, 0], sf_, side="right") - 1, 0, len(dl_) - 2)
        m_ = (dl_[seg_ + 1, 1] - dl_[seg_, 1]) / np.maximum(dl_[seg_ + 1, 0] - dl_[seg_, 0], 1e-6)
        K_ = np.sqrt(1 + m_ * m_)
        K_ = np.convolve(np.pad(K_, 3, mode="edge"), np.ones(7) / 7.0, mode="valid")

        def door_field(s, z):
            s = np.asarray(s, float)
            z = np.asarray(z, float)
            f = (z - np.interp(s, dl_[:, 0], dl_[:, 1])) / np.interp(s, sf_, K_) + 0.0015 * n2(s * 30.0, z * 30.0, 905)
            return np.minimum(f, 1.0)
    else:
        door_poly = daub_edge_door_bay(g)

        def door_field(s, z):
            s = np.asarray(s, float)
            z = np.asarray(z, float)
            f = poly_sdf(s, z, door_poly) + 0.003 * n2(s * 30.0, z * 30.0, 905)
            return np.minimum(f, 1.0)

    patches = {}
    r10 = _wf(g).get("patch_style") == "r10"
    if r10:
        g.PATCH_POLYS = {}
        g.PATCH_SPALLS = {}
    for (bay, kind, cf, cz, hs, hz, seed) in g.DAUB_PATCHES:
        s0, s1 = bay_s(g, bay)
        cs = s0 + cf * (s1 - s0)
        if r10:
            # kit 1.5.0 (director r9 #1): ragged leaning / chamfered / spalled outline, +-5 mm mid-frequency rag
            P, sp = fracture_patch_r10(g, cs, cz, hs, hz, seed, open_below=(kind == "low"))
            g.PATCH_POLYS.setdefault(bay, []).append((kind, P))
            g.PATCH_SPALLS.setdefault(bay, []).extend(sp)
            rag = float(_wf(g).get("rag", 0.005))
            flo = partial(wall_floor, g) if kind == "low" else None

            def hf10(s, z, _P=P, _sd=seed, _fl=flo, _rag=rag):
                s = np.asarray(s, float)
                z = np.asarray(z, float)
                inside = poly_sdf(s, z, _P)
                if _fl is not None:
                    inside = np.minimum(inside, z - (_fl(s) - 0.06))
                return -inside + 0.003 * n2(s * 30.0, z * 30.0, _sd + 6) + _rag * n2(s * 9.0, z * 9.0, _sd + 7)
            patches.setdefault(bay, []).append(hf10)
            continue
        if kind == "low":
            patches.setdefault(bay, []).append(daub_hole(g, cs, cz, hs, hz, seed, floor=partial(wall_floor, g)))
        else:
            P = fracture_patch(g, cs, cz, hs, hz, seed)

            def hf(s, z, _P=P, _sd=seed):
                s = np.asarray(s, float)
                z = np.asarray(z, float)
                return -poly_sdf(s, z, _P) + 0.003 * n2(s * 30.0, z * 30.0, _sd + 6)
            patches.setdefault(bay, []).append(hf)
    wf = _wf(g)
    bite_bays = None
    if wf.get("foot_bites") is not None:
        # kit 1.3.0 (director r7 #3): at most N splash bites round the hut, 0-1 per bay, never in adjacent bays
        rsb = np.random.RandomState(9590)
        cand = [b for b in range(nb) if b != door_bay and not any(p[0] == b and p[1] == "low" for p in g.DAUB_PATCHES)]
        bite_bays = set()
        for b in rsb.permutation(cand):
            if len(bite_bays) >= int(wf["foot_bites"]):
                break
            if (b - 1) % nb in bite_bays or (b + 1) % nb in bite_bays:
                continue
            bite_bays.add(int(b))
        g.BITE_BAYS = sorted(bite_bays)
    for bay in range(nb):
        if bay == door_bay:
            g.DAUB_BAYS[bay] = door_field
            g.DAUB_PARTS[bay] = (None, door_field)
            continue
        if bite_bays is None:
            lm = low_margin(g, bay, 9500 + 13 * bay)
        else:
            nbt = 1 if bay in bite_bays else 0
            lm = low_margin(g, bay, 9500 + 13 * bay, n_bites=(nbt, nbt), bite_len=wf.get("bite_len", (0.20, 0.40)),
                            bite_h=wf.get("bite_h", (0.02, 0.04)), shoulder=12)
        holes = patches.get(bay, [])

        def pfield(s, z, _holes=holes):
            f = np.ones(np.broadcast(np.asarray(s, float), np.asarray(z, float)).shape)
            for h_ in _holes:
                f = np.minimum(f, h_(s, z))
            return f

        def field(s, z, _lm=lm, _pf=pfield):
            f = np.asarray(z, float) - _lm(s)
            return np.minimum(np.minimum(f, _pf(s, z)), 1.0)

        def hide(s, z, _lm=lm, _holes=holes):
            # rods buried in the intact coat are not modelled: kept ~7 cm under a patch margin, and only
            # ~3.5 cm (the bottom row) over a splash bite in the foot
            hb = (np.asarray(z, float) - _lm(s)) > 0.035
            for h_ in _holes:
                hb &= h_(s, z) > g.DAUB_KEEP_UNDER
            return hb
        g.DAUB_BAYS[bay] = field
        g.DAUB_HIDE[bay] = hide
        g.DAUB_PARTS[bay] = (lm, pfield if holes else None)
    for bay in g.DAUB_BAYS:
        g.DAUB_COVER[bay] = g.DAUB_KEEP_UNDER


def daub_hides(g, bay):
    f = g.DAUB_BAYS.get(bay)
    if f is None:
        return None
    if bay in g.DAUB_HIDE:
        return g.DAUB_HIDE[bay]

    thr = g.DAUB_COVER.get(bay, g.DAUB_KEEP_UNDER)

    def hide(s, z):
        # the daub stops >= 4 cm under the plate: the top rods stay, tucking under the plate
        return f(s, z) > thr
    return hide


def build_wattle(g, coll):
    make_daub_fields(g)
    rods = g.acc("wattle_rods", 60)
    stakes = g.acc("wattle_stakes", 60)
    backing = g.acc("door_panel_backing", 40)
    pathf = arc_path(g.R_WALL)
    nb = len(g.POST_AZ) - 1
    nr = 0
    for bay in CLUMP_BAYS(g):
        g.ROD_STORE[1000 + bay * 17] = []
    for i in range(nb):
        s0, s1 = bay_s(g, i)
        z0 = max(0.22, float(wall_floor(g, np.linspace(s0, s1, 60)).min()) - 0.01)
        nr += weave_panel(g, rods, stakes, pathf, s0, s1, z0, g.WATTLE_TOP, 1000 + i * 17, hide=daub_hides(g, i),
                          trim=(0.075, 0.075), floor=partial(wall_floor, g), knots=0.0 if g.detail.active else 1.0)
    # door side panels (front plane, jamb face -> door post face) and cheek panels (door post -> wall
    # post): twisted-rope weave, every rod end buried in the timber (director r3 #2)
    yc = g.FRONT_Y + 0.11
    for side in (-1, 1):
        x0, x1 = 0.70, 0.90
        f = line_path((side * x0, yc), (side * x1, yc), (0, -1))
        nr += rope_panel(rods, stakes, backing, f, x1 - x0, 0.405, g.HEAD_Z, 3000 + side, slant=0.85 * side,
                         embed=(0.035, 0.035, 0.03, 0.03), rod_r=(0.012, 0.015), gap=(0.002, 0.005))
        pa = np.array([side * 1.02, g.FRONT_Y + 0.17])
        wp = az_pt(g.WALL_POST_AZ_DOOR * side, g.R_WALL)[:2]
        L = float(np.linalg.norm(wp - pa))
        d = (wp - pa) / L
        nout = np.array([d[1], -d[0]])
        if nout[0] * side < 0:
            nout = -nout
        sa, sb = 0.085, L - 0.095
        f2 = line_path(pa + d * sa, wp, nout)
        nr += rope_panel(rods, stakes, backing, f2, sb - sa, 0.405, g.HEAD_Z, 3100 + side, slant=-0.6 * side,
                         embed=(0.05, 0.05, 0.03, 0.03), rod_r=(0.012, 0.015), gap=(0.002, 0.005))
    log("rods:", nr)
    rods.build(coll)
    stakes.build(coll)
    backing.build(coll)


def build_daub(g, coll):
    """front daub coat on every bay (client r6, director r6): mean face 6.2 cm outside the wattle line
    (2-4 cm over the rod fronts) with lumps <= +-1.5 cm, hand-applied dabs, a <= 1.5 cm sag belly, palm
    dents, 2-4 shrinkage cracks per bay; a 1-2 cm shrinkage-slit dip within 8-12 cm of every post so the
    posts stand 5-8 cm proud; a foot bedded onto the stone tops with 1-3 splash bites; crisp stepped
    fracture margins round the exposed patches and the door-bay break; flat torn flakes clinging to the
    exposed rods.  Every boundary tucks behind the wattle / into the posts / into the plate / into the
    stones, so no clean cut edge is exposed."""
    acc = g.acc("daub", 70)
    h = 0.0075                     # fine grid: patch margins, cracks, the weathered foot
    H_S, H_Z = 0.016, 0.013        # intact coat away from them (hand-applied dabs and bulges)
    H_CR = 0.0105                  # crack boxes and the weathered foot
    # producer note 11: the sub-2 cm relief of the coat (shrinkage cracks, dabs, palm dents, fine noise, foot
    # pitting, fracture-face grit) is not modelled -- cracks become decal anchors (g.DAUB_CRACKS) and the intact
    # coat, whose remaining relief is the low-frequency bulge / sag (>= 0.5 m wavelength), takes a 3 cm grid.
    # The crisp fracture margins (2.5-4 cm coat edge), the post slits and the bedded foot keep the fine grid.
    rule = g.detail.active
    k_fine = 0.0 if rule else 1.0
    if rule:
        H_S, H_Z, H_CR = 0.03, 0.03, 0.02
    # kit 1.7 r4 (v4_mixed, producer note 15): optional frame attribute DAUB_GRID = (H_S, H_Z, H_CR[, h_fine]) -- a
    # coarser coat grid under the note-11 rule (the coat keeps only >= 0.5 m bulge / sag relief); absent = unchanged
    dgrid = getattr(g, "DAUB_GRID", None)
    if rule and dgrid:
        H_S, H_Z, H_CR = (float(v) for v in dgrid[:3])
        if len(dgrid) > 3:
            h = float(dgrid[3])
    # kit 1.3.0 (wall_finish daub_relief, director r8 #1): the note-11 entrance exception is applied PER VERTEX
    # (g.detail.min_at_v): inside the entrance zone the r7 hand relief comes back (palm dents and a third of the
    # hand dabs, same places as r7, lifted to >= 1 cm so the rule keeps them); every bay gets sparse 2-2.5 cm
    # hand-applied lumps (>= 2 cm: kept anywhere), so no bay reads as a flat board.  Cracks stay decals.
    wf = _wf(g)
    relief9 = bool(rule and wf.get("daub_relief"))
    n_cr = 0
    n_fl = 0
    stat_T = []
    for bay, field in g.DAUB_BAYS.items():
        rng = np.random.RandomState(4400 + bay)
        sb0, sb1 = bay_s(g, bay)
        s0, s1 = sb0 + 0.04, sb1 - 0.04
        zlo = min(0.30, float(coat_floor(g, np.linspace(s0, s1, 200)).min()) - 0.045)
        zhi = g.PLATE_BOT + 0.012                     # client r6: the intact coat runs up INTO the plate (no gap)
        # crop to where the daub exists
        Sc, Zc = np.meshgrid(np.linspace(s0, s1, 120), np.linspace(zlo, zhi, 160), indexing="ij")
        fc = field(Sc, Zc)
        live = fc > -0.07
        ss_live = Sc[live]
        zz_live = Zc[live]
        cs0, cs1 = max(s0, ss_live.min() - 0.03), min(s1, ss_live.max() + 0.03)
        cz0, cz1 = max(zlo, zz_live.min() - 0.03), min(zhi, zz_live.max() + 0.03)
        if relief9:
            # grid: finer where the entrance zone keeps the 7-12 cm palm dents
            ssb = np.linspace(cs0, cs1, 9)
            rc_ = g.R_WALL + g.COAT_R_NOM
            Pb = np.stack([np.sin(ssb / g.R_WALL) * rc_, -np.cos(ssb / g.R_WALL) * rc_, np.full(ssb.shape, 1.2)], -1)
            ent_bay = bool((g.detail.min_at_v(Pb) < g.detail.min_relief - 1e-9).any())
            H_S = H_Z = wf.get("grid", (0.025, 0.016))[1 if ent_bay else 0]
        # ---- shrinkage cracks first (their boxes are refined): random-walk polylines in intact coat
        cracks = []
        ncr = rng.randint(2, 5)
        tries = 0
        while len(cracks) < ncr and tries < 200:
            tries += 1
            ps = rng.uniform(cs0 + 0.12, cs1 - 0.12)
            pz = rng.uniform(cz0 + 0.18, cz1 - 0.12)
            if field(np.array([ps]), np.array([pz]))[0] < 0.15:
                continue
            Lc = rng.uniform(0.12, 0.35)
            ang = rng.choice([rng.uniform(-0.5, 0.5) + np.pi / 2, rng.uniform(-1.2, 1.2)])
            pts = [(ps, pz)]
            l = 0.0
            while l < Lc:
                st_ = rng.uniform(0.035, 0.06)
                ang += rng.uniform(-0.45, 0.45)
                ps += math.cos(ang) * st_
                pz += math.sin(ang) * st_
                pts.append((ps, pz))
                l += st_
            cracks.append((pts, rng.uniform(0.004, 0.008), rng.uniform(0.008, 0.014)))
            if rng.rand() < 0.4:        # short branch
                kb = rng.randint(1, len(pts) - 1)
                bs, bz = pts[kb]
                ang2 = ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
                bp = [(bs, bz)]
                for _ in range(rng.randint(3, 6)):
                    ang2 += rng.uniform(-0.4, 0.4)
                    bs += math.cos(ang2) * 0.04
                    bz += math.sin(ang2) * 0.04
                    bp.append((bs, bz))
                cracks.append((bp, rng.uniform(0.004, 0.007), rng.uniform(0.01, 0.015)))
        # ---- graded tensor grid: fine (7.5 mm) rows / columns through the patch margins, the cracks and
        # the weathered foot; 1.3-1.6 cm over the intact coat
        fine_s, fine_z = [], [(zlo, float(wall_floor(g, np.linspace(sb0, sb1, 40)).max()) + 0.22, H_CR)]
        edge_m = (fc > -0.06) & (fc < 0.12)
        if edge_m.any():
            # rows / columns that cross a patch margin (not the lower margin, which is z-refined above)
            em = edge_m & (Zc > fine_z[0][1] - 0.05)
            if em.any():
                cols = np.where(em.any(axis=1))[0]
                rows = np.where(em.any(axis=0))[0]
                for (a_, b_) in _runs(np.isin(np.arange(Sc.shape[0]), cols)):
                    fine_s.append((Sc[a_, 0] - 0.03, Sc[b_ - 1, 0] + 0.03, h))
                for (a_, b_) in _runs(np.isin(np.arange(Zc.shape[1]), rows)):
                    fine_z.append((Zc[0, a_] - 0.03, Zc[0, b_ - 1] + 0.03, h))
        for (pts, wd, dp) in (cracks if not rule else ()):
            pa = np.asarray(pts)
            fine_s.append((pa[:, 0].min() - 0.03, pa[:, 0].max() + 0.03, h))
            fine_z.append((pa[:, 1].min() - 0.03, pa[:, 1].max() + 0.03, h))

        def graded(lo, hi, hc, rngs):
            xs = [lo]
            while xs[-1] < hi - 1e-6:
                x = xs[-1]
                hh = min([hr for (a, b, hr) in rngs if a <= x + 0.5 * hr and x - 0.5 * hr <= b] + [hc])
                xs.append(min(hi, x + hh))
            if len(xs) > 2 and xs[-1] - xs[-2] < 0.3 * h:
                xs.pop(-2)
            return np.array(xs)
        su = graded(cs0, cs1, H_S, fine_s)
        zt_ = min(cz1, g.EAVE_SHADOW_Z - 0.06)
        zr = graded(cz0, zt_, H_Z, fine_z)
        if cz1 > zt_ + 0.005:
            zr = np.concatenate([zr, np.linspace(zr[-1], cz1, int((cz1 - zr[-1]) / 0.02) + 2)[1:]])
        nu, nv = len(su), len(zr)
        log(f"  daub bay {bay}: grid {nu} x {nv}, cracks {len(cracks)}")
        S, Z = np.meshgrid(su, zr, indexing="ij")
        dsu = np.gradient(su) if nu > 1 else np.full(nu, H_S)
        dzr = np.gradient(zr) if nv > 1 else np.full(nv, H_Z)
        HL = np.maximum(dsu[:, None], dzr[None, :])         # local grid spacing per vertex
        crack_d = np.zeros(S.shape)
        if rule:
            g.DAUB_CRACKS.extend((bay, np.asarray(pts, float), wd) for (pts, wd, dp) in cracks)
        for (pts, wd, dp) in (cracks if not rule else ()):
            dist, cs_, cz_, ct = _seg_dist(S, Z, pts)
            prof = np.sin(np.pi * np.clip(ct, 0, 1)) ** 0.5
            ww = wd * 0.5 * (0.3 + 0.7 * prof)
            core = dist < 0.55 * HL
            band = (dist >= 0.55 * HL) & (dist < 1.8 * HL)
            # core vertices snap onto the crack centre line (groove bottom)
            S = np.where(core, cs_, S)
            Z = np.where(core, cz_, Z)
            # neighbours are pulled in to the crack lip (narrow 0.5-1 cm crack)
            with np.errstate(invalid="ignore", divide="ignore"):
                ux = (S - cs_) / np.maximum(dist, 1e-9)
                uz = (Z - cz_) / np.maximum(dist, 1e-9)
            dn = ww + (dist - 0.55 * HL) * (1.8 * HL - ww) / (1.25 * HL)
            S = np.where(band, cs_ + ux * dn, S)
            Z = np.where(band, cz_ + uz * dn, Z)
            crack_d = np.minimum(crack_d, np.where(core, -dp * (0.2 + 0.8 * prof), 0.0))
            n_cr += 1
        lm_, pf_ = g.DAUB_PARTS[bay]

        def f_low(S_, Z_):
            return (np.asarray(Z_, float) - lm_(S_)) if lm_ is not None else np.ones(np.shape(S_))

        def f_pat(S_, Z_):
            return pf_(S_, Z_) if pf_ is not None else np.ones(np.shape(S_))
        # wall posts as built (lean / bow / radius): distance from the nearer post's flank, its front
        zs_l, sc_l, rf_l = g.POST_PROF[bay]
        zs_r, sc_r, rf_r = g.POST_PROF[bay + 1]

        def post_d(S_, Z_):
            dl = S_ - np.interp(Z_, zs_l, sc_l) - g.POST_RAD[bay]
            dr = np.interp(Z_, zs_r, sc_r) - S_ - g.POST_RAD[bay + 1]
            left = dl < dr
            rf = np.where(left, np.interp(Z_, zs_l, rf_l), np.interp(Z_, zs_r, rf_r)) - g.R_WALL
            return np.minimum(dl, dr), rf, np.where(left, 0.0, 1.0)
        f = field(S, Z)
        dfl0, _, _ = post_d(S, Z)
        # director r4 #5c: the sheet's cut boundary (where it is dropped behind the rods) is snapped onto
        # the smooth field contour -- no grid stair-steps along any daub margin
        F_all = grid_quads(nu, nv)
        hv0 = ((f < -0.03) | (dfl0 < -0.03)).ravel()
        F_keep = F_all[~hv0[F_all].all(axis=1)]
        used = np.zeros(S.size, bool)
        used[F_keep.ravel()] = True

        def snap(fn, sel, off, it=5):
            ps, pz = S[sel].copy(), Z[sel].copy()
            hm = HL[sel]
            for _ in range(it):
                e_ = 1e-3
                f0 = fn(ps, pz) + off
                gs = (fn(ps + e_, pz) - fn(ps - e_, pz)) / (2 * e_)
                gz = (fn(ps, pz + e_) - fn(ps, pz - e_)) / (2 * e_)
                g2 = np.maximum(gs * gs + gz * gz, 0.05)
                ps = ps + np.clip(-f0 * gs / g2, -hm, hm)
                pz = pz + np.clip(-f0 * gz / g2, -hm, hm)
            return ps, pz
        mv = (used & (f.ravel() < -0.03) & (dfl0.ravel() >= -0.03)).reshape(S.shape)
        if mv.any():
            S = S.copy()
            Z = Z.copy()
            S[mv], Z[mv] = snap(field, mv, 0.03, 4)
        # director r6 #1/#3: a CRISP outer arris on every fracture margin -- the grid vertices nearest the
        # patch / break contour are snapped onto it, so the coat face turns into the fracture face on an
        # edge loop (no 1-cell soft chamfer, no pillowed lip)
        fp = f_pat(S, Z)
        if pf_ is not None:
            ar = (np.abs(fp) < 0.42 * HL) & (f_low(S, Z) > 0.03) & (dfl0 > 0.0)
            if ar.any():
                S = S.copy()
                Z = Z.copy()
                S[ar], Z[ar] = snap(f_pat, ar, 0.0, 5)
        f = field(S, Z)
        fp = f_pat(S, Z)
        fl_ = f_low(S, Z)
        dfl, RF, side_ = post_d(S, Z)
        P3 = np.stack([S * 1.7, Z * 1.7, np.full(S.shape, bay * 1.31)], -1)
        # ---- soft bulges (director r6 #4: lumps <= +-1.5 cm about the mean face)
        bul = fbm(P3, 2, gain=0.45)
        bul = (bul - bul.mean()) / max(bul.std(), 1e-6)
        bulge = 0.0062 * np.clip(bul, -2.2, 2.2) + k_fine * 0.0025 * n2(S * 7.0, Z * 7.0, 4490 + bay)
        # ---- feathering: along ~30 % of each fracture margin the coat thins over the rods (ridged) in
        # a softer lip; elsewhere the break is a crisp step (director r6 #1)
        Fm = smoothstep(0.18, 0.42, n2(S * 3.2, Z * 3.2, 4560 + bay))
        drift = 0.006 * n2(S * 1.1, np.full(S.shape, 3.3), 4500 + bay)
        pitch = g.ROD_ROW_P
        rid = np.cos(2 * np.pi * (Z + drift) / pitch)
        ridge = 0.0 * rid               # r7: no rod ridging (it read as corrugation); feathering is in the edge profile
        # ---- client r6: hand-applied dabs over the intact coat (handful pats 6-11 cm, 2-5 mm proud, a
        # slightly sharper lower lip where each was pushed upward)
        dabs = np.zeros(S.shape)
        dabs_e = np.zeros(S.shape)          # kit 1.3.0: entrance-zone hand dabs (>= 1 cm, gated per vertex)
        smear_e = np.zeros(S.shape)         # kit 1.3.0: entrance-zone palm dents (>= 1 cm, gated per vertex)
        zone_any = False
        if relief9:
            rc_ = g.R_WALL + g.COAT_R_NOM
            Pw = np.stack([np.sin(S / g.R_WALL) * rc_, -np.cos(S / g.R_WALL) * rc_, Z], -1)
            minv = g.detail.min_at_v(Pw)                      # note 11 threshold per vertex
            ex_, ey_ = g.detail.entrance
            inside_ = np.minimum(g.detail.entrance_r - np.hypot(Pw[..., 0] - ex_, Pw[..., 1] - ey_),
                                 g.detail.entrance_h - Z)
            soft_ = smoothstep(0.0, wf.get("ent_soft", 0.25), inside_)
            zone_any = bool((minv < g.detail.min_relief - 1e-9).any())

            def keep_w(A_, _minv=minv, _soft=soft_):
                """per-vertex weight of a relief feature of depth A_: DetailRule keeps it where A_ >= the local
                threshold; sub-2 cm features fade out over the last `ent_soft` metres inside the zone boundary."""
                k = (A_ >= _minv - 1e-9).astype(float)
                return k if A_ >= g.detail.min_relief - 1e-9 else k * _soft

            if wf.get("ent_gate") == "feature":
                rc_f = rc_

                def keep_w(A_, c_s=None, c_z=None, _minv=minv):    # noqa: F811
                    """kit 1.6.0 (audit r10 (4)): a sub-2 cm feature is kept WHOLE where its centre's note-11
                    threshold allows it (entrance zone: >= 1 cm), else not at all -- no 0-1 cm fade band."""
                    if A_ >= g.detail.min_relief - 1e-9 or c_s is None:
                        return (A_ >= _minv - 1e-9).astype(float)
                    a_c = c_s / g.R_WALL
                    pc = (math.sin(a_c) * rc_f, -math.cos(a_c) * rc_f, c_z)
                    return 1.0 if A_ >= g.detail.min_at(pc) - 1e-9 else 0.0
        n_dab = 0
        for _ in range(int((cs1 - cs0) * (cz1 - cz0) * 30)):
            c_s = rng.uniform(cs0, cs1)
            c_z = rng.uniform(cz0, cz1)
            R_ = rng.uniform(0.06, 0.11)
            ds_ = (S - c_s) / (R_ * rng.uniform(0.9, 1.4))
            dz_ = (Z - c_z) / R_
            r2 = ds_ ** 2 + dz_ ** 2
            m = r2 < 4.0
            if not m.any():
                continue
            lip = np.where(dz_ < 0, np.exp(-r2 * 2.2), np.exp(-r2 * 1.1))
            A_d = rng.uniform(0.002, 0.005)
            dabs += A_d * lip * m
            if zone_any:
                n_dab += 1
                if n_dab % int(wf.get("ent_dab_keep", 3)) == 0:
                    lo_, hi_ = wf.get("ent_dabs", (0.010, 0.013))
                    Ae = lo_ + (A_d - 0.002) / 0.003 * (hi_ - lo_)
                    dabs_e += Ae * lip * m * (keep_w(Ae, c_s, c_z) if wf.get("ent_gate") == "feature" else keep_w(Ae))
        dabs -= 0.003
        dabs *= k_fine
        # ---- palm-press dents (director r3 #5c): round 7-12 cm dents 0.8-1.8 cm deep with a slight
        # squeezed-up rim; they break the long undulations (no strokes, no folds)
        smear = np.zeros(S.shape)
        area = (cs1 - cs0) * (cz1 - cz0)
        for _ in range(int(area * 7)):
            c_s = rng.uniform(cs0, cs1)
            c_z = rng.uniform(cz0, cz1)
            R_ = rng.uniform(0.05, 0.08)
            el = rng.uniform(0.8, 1.25)
            r2 = ((S - c_s) / (R_ * el)) ** 2 + ((Z - c_z) * el / R_) ** 2
            m = r2 < 6.0
            if not m.any():
                continue
            A_ = rng.uniform(0.006, 0.012)
            rr_ = np.sqrt(r2)
            smear += k_fine * A_ * (-np.exp(-r2 * 1.3) + 0.12 * np.exp(-((rr_ - 1.1) / 0.35) ** 2)) * m
            if zone_any:
                lo_, hi_ = wf.get("ent_dents", (0.010, 0.015))
                Ae = lo_ + (A_ - 0.006) / 0.006 * (hi_ - lo_)
                smear_e += Ae * (-np.exp(-r2 * 1.3) + 0.15 * np.exp(-((rr_ - 1.1) / 0.35) ** 2)) * m * (
                    keep_w(Ae, c_s, c_z) if wf.get("ent_gate") == "feature" else keep_w(Ae))
        fine = k_fine * (0.0035 * n2(S * 9, Z * 9, bay + 40) + 0.0012 * n2(S * 30, Z * 30, bay + 41)
                + 0.0005 * n2(S * 80, Z * 80, bay + 42))
        # ---- kit 1.3.0: sparse hand-applied lumps of 2.0-2.5 cm on every bay (own seed: no r7 draw changes)
        lumps = np.zeros(S.shape)
        if relief9:
            rl = np.random.RandomState(7700 + bay)
            for _ in range(int(round(area * rl.uniform(*wf.get("lumps_per_m2", (2.0, 3.0)))))):
                c_s = rl.uniform(cs0, cs1)
                c_z = rl.uniform(cz0 + 0.1, cz1 - 0.1)
                sg_ = rl.uniform(*wf.get("lump_sigma", (0.045, 0.08)))
                el = rl.uniform(1.0, 1.6)                       # pressed on wider than tall
                A_ = rl.uniform(*wf.get("lump_amp", (0.020, 0.025)))
                ds_ = (S - c_s) / (sg_ * el)
                dz_ = (Z - c_z) / sg_
                r2 = ds_ ** 2 + dz_ ** 2
                m = r2 < 9.0
                if not m.any():
                    continue
                # a slightly sharper lower lip where the handful was pushed upward
                lumps += A_ * np.where(dz_ < 0, np.exp(-0.75 * r2), np.exp(-0.5 * r2)) * m * keep_w(A_)
        # ---- slight sag (a soft belly where the wet coat slumped, 0.5-1.0 m up; director r6 #4: <= 1.5 cm)
        z_sag = 0.62 + 0.3 * ((bay * 0.618) % 1.0)
        sa0, sa1 = wf.get("sag", (0.008, 0.004)) if relief9 else (0.008, 0.004)
        sag = (sa0 + sa1 * n2(S * 1.3, np.full(S.shape, 0.5), 4540 + bay)) * np.exp(-((Z - z_sag) / 0.28) ** 2)
        sag = sag * (1 - smoothstep(0.42, 0.62, np.abs(Z - z_sag) / 0.6))
        # ---- weathered foot: splash-pitted over the bottom ~25 cm; where it is bedded on the stones a
        # rough fillet squeezed out onto the stone tops and into the joints (director r6 #5)
        zfl = coat_floor(g, S)
        foot = 1 - smoothstep(0.0, 0.26, Z - zfl)
        foot_n = np.clip(n2(S * 14.0, Z * 30.0, 4541 + bay) * 1.4 + 0.3, 0, 1)
        bedded = smoothstep(0.012, 0.028, fl_ - (Z - zfl))        # the foot here reaches the stone
        fillet = (0.009 + 0.004 * n2(S * 25.0, np.full(S.shape, 1.7), 4544 + bay)) * (1 - smoothstep(-0.01, 0.045, Z - zfl)) * bedded
        if relief9:      # lumps / entrance relief fade into the post slits and toward the fracture margins
            fade_ = smoothstep(0.03, 0.14, dfl) * smoothstep(0.04, 0.14, fp) * smoothstep(0.03, 0.12, fl_)
            smear = smear + (smear_e + dabs_e + lumps) * fade_
        T_full = (g.COAT_R_NOM + bulge * (0.3 + 0.7 * smoothstep(-0.02, 0.16, dfl)) + ridge + smear + fine + dabs + sag
                  - k_fine * foot * (0.004 + 0.006 * foot_n)
                  + k_fine * foot * (0.004 * n2(S * 22.0, Z * 45.0, 4542 + bay) - 0.004 * np.clip(n2(S * 35, Z * 55, 4543 + bay) * 2 - 0.6, 0, 1))
                  + fillet)
        # ---- director r6 #1: the coat at a fracture margin stands 2.5-4 cm over the rod fronts
        door_r11 = wf.get("door_break") == "r11" and bay == len(g.POST_AZ) - 2
        T_edge = float(wf.get("door_edge_T", 0.068)) if door_r11 else 0.068
        T_full = T_full + np.clip(T_edge - T_full, 0, None) * (1 - smoothstep(0.04, 0.12, fp))
        # ---- director r6 #4: posts stand 5-8 cm proud.  Within 8-12 cm of each post the coat dips a
        # further 1-2 cm into the shrinkage slit (a broken step, not a fillet), and never comes within
        # 5.5 cm of the post's (as-built) front face
        slit_w = 0.08 + 0.04 * np.clip(0.5 + 0.6 * n2(Z * 2.2, side_ * 7.0 + bay, 4520), 0, 1) + 0.004 * n2(Z * 14.0, side_ + bay, 4524)
        zone = 1 - smoothstep(slit_w - 0.012, slit_w + 0.004, dfl)
        dip = (0.012 + 0.008 * np.clip(0.5 + 0.6 * n2(Z * 4.0, side_ * 3.0 + bay, 4521), 0, 1)) * zone
        T_full = T_full - dip
        cap = RF - 0.058 + 0.004 * n2(S * 12.0, Z * 12.0, 4523 + bay)
        T_full = np.minimum(T_full, cap + (1 - zone) * 0.2)
        # rods stay covered wherever they are still modelled (patch margins, foot bites)
        rods_behind = (fp < g.DAUB_KEEP_UNDER + 0.03) | (fl_ < 0.07)
        T_full = np.maximum(T_full, np.where(rods_behind, 0.050, 0.034))
        # ---- edge profiles.  Foot bites: a rounded splash-eroded edge.  Fracture margins (door-bay
        # break, patches): a crisp arris, then a near-normal broken face (2.4 cm run for a ~10 cm drop,
        # <= 15 deg off the wall normal) with 3-6 mm grit; softer where feathered
        e_low = smoothstep(-0.004, 0.02, fl_) if lm_ is not None else np.ones(S.shape)
        grit = k_fine * (0.005 * n2(S * 70.0, Z * 70.0, 4570 + bay) + 0.002 * n2(S * 160.0, Z * 160.0, 4571 + bay))
        fpg = fp + grit * np.clip(-fp / 0.006, 0, 1)
        w_e = 0.024 + 0.02 * Fm
        if wf.get("patch_style") == "r10" and bay in getattr(g, "PATCH_POLYS", {}):
            # kit 1.5.0 (director r9 #1): the visible fracture face varies 1.5-5 cm round each patch (no constant
            # bevel ring) and opens into a shallow conchoidal spall at each scallop
            ew0, ew1 = wf.get("edge_w", (0.015, 0.050))
            w_e = ew0 + (ew1 - ew0) * smoothstep(-0.55, 0.55, n2(S * 4.5, Z * 4.5, 4580 + bay))
            for (sc_, zc_, rr_) in g.PATCH_SPALLS.get(bay, ()):
                sp_ = np.exp(-((S - sc_) ** 2 + (Z - zc_) ** 2) / (rr_ * rr_))
                w_e = w_e * (1 - sp_) + float(wf.get("spall_w", 0.055)) * sp_
            Fm = Fm * 0.5
        if door_r11:
            # kit 1.6.0 (audit r10): a steep, THICK broken face -- 1.5-3 cm tall (vertical offset), no feathered lip,
            # so the full coat thickness shows as an edge face and the tab corners stay crisp
            dw0, dw1 = wf.get("door_edge_w", (0.015, 0.030))
            w_e = dw0 + (dw1 - dw0) * smoothstep(-0.55, 0.55, n2(S * 4.5, Z * 4.5, 4581 + bay))
            Fm = Fm * 0.0
            grit = grit * 0.0
            fpg = fp
        tpe = np.clip(1 + fpg / w_e, 0, 1)
        e_pat = (1 - Fm) * tpe + Fm * smoothstep(0.0, 1.0, tpe)
        edge = np.minimum(e_low, e_pat)
        pit = k_fine * 0.004 * np.clip(n2(S * 25, Z * 25, bay + 77), 0, 1) * (1 - smoothstep(0.04, 0.16, f))
        T = -0.036 + (T_full + 0.036 - pit) * edge + crack_d * edge
        # tuck into the posts at the very ends of the sheet, and back under the plate at the top
        T = T - 0.04 * (1 - smoothstep(-0.05, -0.012, dfl)) * edge
        T = T - 0.032 * smoothstep(zhi - 0.09, zhi, Z)
        a = S / g.R_WALL
        rad = g.R_WALL + T
        P = np.stack([np.sin(a) * rad, -np.cos(a) * rad, Z], -1)
        Vv = P.reshape(-1, 3)
        # drop the parts never seen: sheet tucked behind the rods below the break, inside the posts, and
        # the bedded foot inside the stones
        buried = (Z < zfl - 0.004).ravel()
        F_keep = F_keep[~buried[F_keep].all(axis=1)]
        acc.add(Vv, F_keep, "M_daub")
        stat_T.append(T_full[(fp > 0.15) & (fl_ > 0.3) & (dfl > 0.12)])
        # ---- director r6 #2: clinging daub = flat torn FLAKES of coat lying on the rods' front face
        # (8-15 x 5-10 cm, 1-2 cm thick, 4-7 straight breaks), within 8 cm of the main break
        if 1000 + bay * 17 in g.ROD_STORE and wf.get("flakes", True):
            n_fl += daub_flakes(g, acc, bay, field, g.ROD_STORE[1000 + bay * 17], rng, s0, s1,
                                3 if bay == len(g.POST_AZ) - 2 else 2)
        if 1000 + bay * 17 in g.ROD_STORE and wf.get("clumps"):
            n_fl += daub_clumps(g, acc, bay, field, g.ROD_STORE[1000 + bay * 17], s0, s1, wf)
    tt = np.concatenate(stat_T)
    log("daub cracks:", n_cr, "flakes:", n_fl, "intact coat T mean %.4f p5 %.4f p95 %.4f" % (tt.mean(), np.percentile(tt, 5), np.percentile(tt, 95)))
    acc.build(coll)


def flake_mesh(rng, w, h, thick, ch=0.0025):
    """one torn flake of daub: an irregular 5-7 sided polygon of straight breaks (no rectangle, no lens),
    a flat dabbed front, broken sides at varying slopes with a small arris; local x across, y up, z out of
    the wall (back face at z = 0)."""
    m = rng.randint(5, 8)
    gaps = rng.dirichlet(np.full(m, 2.2)) * 2 * np.pi          # uneven breaks: some long, some short
    gaps = np.clip(gaps, 0.35, None)
    gaps *= 2 * np.pi / gaps.sum()
    ang = np.cumsum(gaps) + rng.uniform(0, 2 * np.pi)
    rr = rng.uniform(0.62, 1.0, m)
    o = np.stack([np.cos(ang) * rr * w / 2, np.sin(ang) * rr * h / 2], -1)
    o = o - o.mean(0)
    c = np.zeros(2)
    sc = 1 - ch / max(np.linalg.norm(o, axis=1).mean(), 1e-3)
    back = rng.uniform(0.82, 1.02, m)[:, None]               # break faces lean in / out per edge
    zt = thick + 0.003 * rng.uniform(-1, 1, m)
    V = np.concatenate([
        np.c_[o * back, np.zeros(m)],
        np.c_[o, zt - ch],
        np.c_[o * sc, zt],
        np.c_[o * rng.uniform(0.45, 0.6), thick + 0.002 * rng.uniform(-1, 1, m)],
        [[c[0], c[1], thick + 0.0015 * rng.uniform(-1, 1)]],
    ])
    j = np.arange(m)
    j1 = (j + 1) % m
    F = [
        np.stack([j, j1, m + j1, m + j], -1),
        np.stack([m + j, m + j1, 2 * m + j1, 2 * m + j], -1),
        np.stack([2 * m + j, 2 * m + j1, 3 * m + j1, 3 * m + j], -1),
        np.stack([3 * m + j, 3 * m + j1, np.full(m, 4 * m)], -1),
        j[::-1][None, :],
    ]
    return V, F


def daub_flakes(g, acc, bay, field, store, rng, s0, s1, n_max):
    """director r6 #2: flat torn flakes of coat still clinging to the exposed rods just below / beside a
    break (never a sleeve round one rod).  Each bridges 2-3 rod rows on their front face."""
    allS = np.concatenate([st[0] for st in store])
    allP = np.concatenate([st[1] for st in store])
    allR = np.concatenate([st[2] for st in store])
    front = np.hypot(allP[:, 0], allP[:, 1]) + allR
    cs = rng.uniform(s0 + 0.16, s1 - 0.16, 500)
    cz = rng.uniform(0.40, g.PLATE_BOT - 0.25, 500)
    fc = field(cs, cz)
    ok = (fc > -0.085) & (fc < -0.045) & (cz > coat_floor(g, cs) + 0.10)
    picks = []
    for i in np.where(ok)[0]:
        if len(picks) >= n_max:
            break
        if any(abs(cs[i] - q[0]) < 0.25 for q in picks):
            continue
        w = rng.uniform(0.09, 0.15)
        h = min(0.10, max(0.05, w * rng.uniform(0.5, 0.72)))
        th = rng.uniform(-0.35, 0.35)
        cr = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]])
        cr = cr @ np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
        if (field(cs[i] + cr[:, 0], cz[i] + cr[:, 1]) > 0.01).any():
            continue
        m = (np.abs(allS - cs[i]) < w / 2) & (np.abs(allP[:, 2] - cz[i]) < h / 2)
        if m.sum() < 6 or np.ptp(allP[m, 2]) < 0.03:
            continue                                    # needs rods under it, >= 2 rows
        r_back = float(np.percentile(front[m], 90)) - 0.005
        V, F = flake_mesh(rng, w, h, rng.uniform(0.011, 0.018))
        # into the wall frame: x along the wall, y up, z outward; in-plane rotation, bottom peeled out
        tilt = rng.uniform(0.0, 0.12)
        Rl = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        V = V @ Rl.T
        V[:, 2] += (-V[:, 1]) * tilt * (V[:, 1] < 0)
        a_ = cs[i] / g.R_WALL
        t_ = np.array([math.cos(a_), math.sin(a_), 0.0])
        n_ = np.array([math.sin(a_), -math.cos(a_), 0.0])
        W = n_[None, :] * r_back + V[:, 0:1] * t_[None, :] + V[:, 2:3] * n_[None, :]
        W[:, 2] = cz[i] + V[:, 1]
        acc.add(W, F, "M_daub", wear=0.85)
        picks.append((cs[i], cz[i]))
    return len(picks)


def clump_mesh(rs, w, h, depth, style=None):
    """kit 1.5.0: one broken CLUMP of daub still clinging to the rods (not a flake, not a bead): the convex hull of
    a broad base ring (7-9 points, 0-25 % of the depth), a mid ring (5-7, 45-75 %) and a small crown (3-5, 85-100 %)
    -> a chunky lump of 20-40 flat broken facets, bottom-heavy (the lower half slumps out further).  Local x across,
    y up, z out of the wall; back bed at z ~ 0.  Returns V (k, 3), F (m, 3)."""
    import bmesh
    pts = []
    rings = ((rs.randint(7, 10), (0.82, 1.0), (0.0, 0.25)), (rs.randint(5, 8), (0.55, 0.88), (0.45, 0.75)),
             (rs.randint(3, 6), (0.0, 0.5), (0.85, 1.0)))
    if style == "slab":
        # kit 1.6.0 (audit r10): a flat-fronted broken SLAB of coat, not a bead -- an irregular base (5-8 corners,
        # radii 0.65-1.0) and a broad front plateau (6-8 points at 0.6-0.92 of the base, on one plane tilted
        # 4-12 deg, +-6 % of the depth) -> steep broken sides and a planar front face
        rings = ((rs.randint(5, 9), (0.65, 1.0), (0.0, 0.12)), (rs.randint(6, 9), (0.6, 0.92), None))
        tdir = rs.uniform(0, 2 * np.pi)
        tk = math.tan(math.radians(rs.uniform(4, 12)))
    for (m_, rr, zz) in rings:
        if zz is None:
            ang = np.sort(rs.uniform(0, 2 * np.pi, m_))
            r_ = rs.uniform(*rr, m_)
            x = np.cos(ang) * r_ * w / 2
            y = np.sin(ang) * r_ * h / 2
            z = depth * (0.94 + rs.uniform(-0.06, 0.06, m_)) + tk * (x * math.cos(tdir) + y * math.sin(tdir))
            z = np.clip(z, 0.55 * depth, 1.1 * depth)
            pts.append(np.stack([x, y, z], -1))
            continue
        ang = np.sort(rs.uniform(0, 2 * np.pi, m_))
        r_ = rs.uniform(*rr, m_)
        x = np.cos(ang) * r_ * w / 2
        y = np.sin(ang) * r_ * h / 2
        z = rs.uniform(*zz, m_) * depth
        z = z * np.where(y < 0, rs.uniform(1.05, 1.2), 1.0)
        pts.append(np.stack([x, y, z], -1))
    pts = np.concatenate(pts)
    pts[:, 2] = np.clip(pts[:, 2], 0.0, depth * 1.15)
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(tuple(map(float, p)))
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bm.verts.index_update()
    V = np.array([v.co[:] for v in bm.verts], float)
    F = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    used = np.unique(np.concatenate([np.asarray(f) for f in F]))
    remap = -np.ones(len(V), np.int64)
    remap[used] = np.arange(len(used))
    return V[used], [remap[np.asarray(f)].tolist() for f in F]


def daub_clumps(g, acc, bay, field, store, s0, s1, wf):
    """kit 1.5.0 (client correction: 'a few clinging clumps'; director audit r9): 2-3 clumps per break, each a
    chunky broken lump (clump_mesh) 6-11 x 5-8.5 cm standing 2.2-3.4 cm proud of the rod fronts, its back bedded
    at the rod centre line so the rods run INTO it (it hugs them), centred 3-7 cm inside the fracture contour so
    its rim meets the broken edge (preferably hanging under the top margin, where a slumped clump stays).
    Own random stream: no other draw changes."""
    rs = np.random.RandomState(8800 + bay)
    allS = np.concatenate([st[0] for st in store])
    allP = np.concatenate([st[1] for st in store])
    allR = np.concatenate([st[2] for st in store])
    rc_ = np.hypot(allP[:, 0], allP[:, 1])
    front = rc_ + allR
    door_bay = bay == len(g.POST_AZ) - 2
    lo_n, hi_n = wf.get("clump_n", (2, 3))
    n_max = hi_n if door_bay else lo_n
    cs = rs.uniform(s0 + 0.14, s1 - 0.14, 900)
    cz = rs.uniform(0.40, g.PLATE_BOT - 0.12, 900)
    fc = field(cs, cz)
    e_ = 0.01
    gz = (field(cs, cz + e_) - field(cs, cz - e_)) / (2 * e_)
    gs = (field(cs + e_, cz) - field(cs - e_, cz)) / (2 * e_)
    gn = gz / np.maximum(np.hypot(gs, gz), 1e-6)
    ok = (fc > -0.075) & (fc < -0.03) & (cz > coat_floor(g, cs) + 0.09)
    order = [i for i in np.argsort(-(gn + rs.uniform(0, 0.9, len(cs)))) if ok[i]]
    picks = []
    slab = wf.get("clump_style") == "slab"
    n_corner = 0
    for i in order:
        if len(picks) >= n_max:
            break
        if any(math.hypot(cs[i] - q[0], cz[i] - q[1]) < 0.2 for q in picks):
            continue
        if slab:
            # kit 1.6.0 (audit r10): under a TOP margin (the field rises straight up: coat above) -- at most one
            # clump per break where the margin turns (a corner / side)
            if gn[i] < 0.85:
                if n_corner >= 1:
                    continue
                n_corner += 1
        w = rs.uniform(*wf.get("clump_w", (0.06, 0.11)))
        h = rs.uniform(*wf.get("clump_h", (0.05, 0.085)))
        th = rs.uniform(-0.3, 0.3)
        cr = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2], [0, -h / 2], [0, h / 2]])
        cr = cr @ np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
        fcr = field(cs[i] + cr[:, 0], cz[i] + cr[:, 1])
        if (fcr > 0.03).any() or (fcr > -0.005).sum() < 1:
            continue                                    # mostly over the exposed rods, its rim at the broken edge
        m = (np.abs(allS - cs[i]) < w / 2) & (np.abs(allP[:, 2] - cz[i]) < h / 2)
        if m.sum() < 6 or np.ptp(allP[m, 2]) < 0.025:
            continue                                    # needs rods under it, >= 2 rows
        r_back = float(np.median(rc_[m])) - 0.003
        r_front = float(np.percentile(front[m], 90))
        proud = rs.uniform(*wf.get("clump_proud", (0.022, 0.034)))
        depth = r_front + proud - r_back
        if slab:
            # width : depth 1.6-2.4 (flake-like lump hugging the rod front), height 0.55-0.8 of the width
            w = float(np.clip(w, 1.6 * depth, 2.4 * depth))
            h = float(np.clip(h, 0.55 * w, 0.8 * w))
        V, F = clump_mesh(rs, w, h, depth, style="slab" if slab else None)
        tilt = rs.uniform(0.0, 0.1)                     # the lower edge peeled out a little
        Rl = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        V = V @ Rl.T
        V[:, 2] += (-V[:, 1]) * tilt * (V[:, 1] < 0)
        a_ = cs[i] / g.R_WALL
        t_ = np.array([math.cos(a_), math.sin(a_), 0.0])
        n_ = np.array([math.sin(a_), -math.cos(a_), 0.0])
        W = n_[None, :] * r_back + V[:, 0:1] * t_[None, :] + V[:, 2:3] * n_[None, :]
        W[:, 2] = cz[i] + V[:, 1]
        acc.add(W, F, "M_daub", smooth=False, wear=0.85)
        picks.append((cs[i], cz[i], w, h, proud))
    g.DAUB_CLUMPS = getattr(g, "DAUB_CLUMPS", []) + [(bay,) + p for p in picks]
    log(f"  daub bay {bay}: clumps {len(picks)}")
    return len(picks)


def build_inner_skin(g, coll):
    """inner daub skin 17 cm behind the rod centre line: the dark back of the open weave (gaps read dark,
    rod backs are never visible) and the inner wall face seen through the doorway.  A single lumpy sheet
    (both faces are seen: the outer through the weave gaps, the inner through the door) with a folded
    top lip under the plate, continuous all the way round from door cheek to door cheek."""
    acc = g.acc("daub_interior", 70)
    a0, a1 = g.WALL_POST_AZ_DOOR, 2 * math.pi - g.WALL_POST_AZ_DOOR
    nu = max(8, int((a1 - a0) * g.R_WALL / 0.08))
    zt = g.PLATE_BOT + 0.02
    zz = np.concatenate([np.linspace(0.15, zt, 30), [zt + 0.002]])
    A, Z = np.meshgrid(np.linspace(a0, a1, nu), zz, indexing="ij")
    lump = 0.012 * fbm(np.stack([A * 4, Z * 2.5, np.zeros(A.shape)], -1), 3)
    ro = g.R_WALL - g.INNER_SKIN_D + lump
    ro[:, -1] = g.R_WALL - 0.115                                # top lip folded back toward the wattle
    P = np.stack([np.sin(A) * ro, -np.cos(A) * ro, Z], -1)
    F = grid_quads(nu, len(zz))[:, ::-1]                     # normals face the hut interior
    # director r4 #3a: the skin is kept over the FULL circumference (also behind the daubed bays, whose
    # posts and rods are open-backed): no ray through the doorway can leave the hut through the wall
    acc.add(P.reshape(-1, 3), F, "M_daub")
    acc.build(coll)


def plinth_under_coat(g, V):
    """client r6 / director r6 #5: where the bedded daub foot comes down onto the stones, the stone top
    behind the coat (inside the wattle line) is never seen.  Stone tops stay wherever the foot is broken
    (splash bites, patches, the door bay) within 8 cm, so no hole ever opens behind the exposed rods."""
    if "s" not in g.COVER_FOOT:
        sg = np.arange(0.0, 2 * np.pi * g.R_WALL, 0.01)
        cov = np.zeros(len(sg), bool)
        for b in range(len(g.POST_AZ) - 1):
            sb0, sb1 = bay_s(g, b)
            m = (sg > sb0 + 0.10) & (sg < sb1 - 0.10)
            if m.any():
                cov[m] = g.DAUB_BAYS[b](sg[m], wall_floor(g, sg[m]) + 0.005) > 0.005
        k = 8
        bad = ~cov
        dil = bad.copy()
        for d in range(1, k + 1):
            dil |= np.roll(bad, d) | np.roll(bad, -d)
        g.COVER_FOOT["s"], g.COVER_FOOT["c"] = sg, ~dil
    r_ = np.hypot(V[:, 0], V[:, 1])
    cand = (r_ < g.R_WALL + 0.045) & (V[:, 2] > 0.18)          # behind the bedded coat face (r >= 3.55 at the foot)
    hid = np.zeros(len(V), bool)
    if not cand.any():
        return hid
    az = np.mod(np.arctan2(V[cand, 0], -V[cand, 1]), 2 * np.pi)
    i_ = np.clip(np.round(az * g.R_WALL / 0.01).astype(int), 0, len(g.COVER_FOOT["s"]) - 1)
    hid[np.where(cand)[0][g.COVER_FOOT["c"][i_]]] = True
    return hid


def round_daub_wall(g, patches=None, posts_seed=202):
    """KIT COMPONENT: the wattle-and-daub wall of a round building (radius g.R_WALL, wattle up to g.WATTLE_TOP):
    daub fields per bay, woven wattle where it shows, the post ring (round_posts), the plinth tops behind the
    bedded coat culled, the coat sheet with clinging flakes and the interior skin.
    patches: exposed-wattle patches [(bay, kind 'hole'|'low', centre fraction, centre z, half w, half h, seed)]
    (use g.patch_at(az_deg, ...) to give them by azimuth); default g.DAUB_PATCHES.  The bay left of the door
    always carries the ref2 eroded band.  Objects <PREFIX>_wattle_rods / _wattle_stakes / _door_panel_backing /
    _posts / _daub / _daub_interior."""
    import bpy
    from ..core import cull_object, log
    from .round_wall import round_posts
    if patches is not None:
        g.DAUB_PATCHES = list(patches)
    build_wattle(g, g.coll)
    round_posts(g, seed=posts_seed)          # after the daub fields: post flanks buried in the coat are culled
    n = cull_object(bpy.data.objects[f"{g.prefix}_plinth_stones"], partial(plinth_under_coat, g))
    log("plinth tops under the daub foot culled:", n)
    build_daub(g, g.coll)
    build_inner_skin(g, g.coll)
