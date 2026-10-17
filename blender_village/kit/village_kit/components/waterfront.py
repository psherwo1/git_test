"""components.waterfront -- piles, decks, jetties, a timber crib quay and ladders (kit, variant v5_harbour_house; new
module, no existing building uses it).

Datum convention: the quay / landward ground is Z = 0; the harbour bed is bed_z (about -2.5 m).  Everything here is
below Z = 0 on purpose (piles stand in water), so these parts are finalised with clip_z = bed_z - 0.01 instead of the
kit's -5 cm buried-skirt clip (producer note 10 is about ground contact on land).

    pile(acc, top, bot, r=0.13, rng=None, lean=0.01, sides=10)      one round, tapering, slightly bent timber pile
    pile_deck(g, name, rects, deck_z=0.5, bed_z=-2.5, land=None, pile_rows=1.6, pile_cols=1.8, ...)   KIT COMPONENT
        a plank deck / jetty on timber piles over ANY rectilinear plan given as a union of rectangles
        [(x0, x1, y0, y1), ...]: piles in rows across the plan (rows every <= pile_rows m along Y, piles every
        <= pile_cols m across), a bearer (pile cap) on each row, joists along Y, deck planks along X with 6 mm gaps,
        fascia boards closing every free edge (plank and joist ends), X-bracing on the outer pile lines with a waling,
        mooring posts (piles run up past the deck) at the given corners.  land = "S" / "N" / "E" / "W": the side that
        butts a building or quay -- no fascia and no piles there; the joists bear on a ledger on the quay (land_z).
        -> <P>_<name>_piles, _structure, _planks, _fascia, _ironwork
    stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, ...)   KIT COMPONENT (round 2; the timber crib quay
        is retired): a quay edge of large rubble blocks (rubble_walls.path_stone_wall, QUAY_BLOCKS) whose WATER runs
        stand on the bed; land runs are terrain and are not built.  -> <P>_<name>_<k>_stones, _quoins, _mortar
    ladder(g, name, top, out, z_bot, width=0.46, ...)       KIT COMPONENT: a timber ladder down a quay / deck face
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, obox, sweep
from .timber_walls import wbox

EZ = np.array([0.0, 0.0, 1.0])


def pile(acc, top, bot, r=0.13, rng=None, lean=0.01, sides=10, taper=0.12, mat="M_timber_weathered", cap=True):
    """one round timber pile from bot (x, y, z) up to top: tapering by `taper` toward the foot, a gentle bend,
    `lean` (m per m) off plumb; a closed piece (capped)."""
    rng = rng or np.random.default_rng(0)
    top, bot = np.asarray(top, float), np.asarray(bot, float)
    H = float(top[2] - bot[2])
    n_st = max(4, int(H / 0.9) + 2)
    u = np.linspace(0.0, 1.0, n_st)
    lx, ly = rng.normal(0, lean), rng.normal(0, lean)
    bend = rng.uniform(-0.02, 0.02, 2)
    path = np.stack([bot[0] + (top[0] - bot[0]) * u + lx * H * (1 - u) + bend[0] * np.sin(np.pi * u),
                     bot[1] + (top[1] - bot[1]) * u + ly * H * (1 - u) + bend[1] * np.sin(np.pi * u),
                     bot[2] + H * u], 1)
    a = np.linspace(0, 2 * np.pi, sides, endpoint=False) + rng.uniform(0, 1)
    rr = r * (1.0 - taper * (1 - u))
    prof = np.stack([np.stack([rr_ * np.cos(a), rr_ * np.sin(a)], 1) * (1 + 0.04 * np.sin(3 * a + k))[:, None]
                     for k, rr_ in enumerate(rr)])
    V, F = sweep(path, (1.0, 0.0, 0.0), prof, caps=cap)
    acc.add(V, F, mat, wear=float(rng.uniform(0.3, 0.7)))


def _beam(acc, p0, p1, w, h, mat="M_timber", r=0.012, up=(0, 0, 1), nx=4):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    ex = d / L
    up = np.asarray(up, float)
    ey = np.cross(up, ex)
    if np.linalg.norm(ey) < 1e-6:
        ey = np.cross((1.0, 0, 0), ex)
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    obox(acc, p0[None], ex, ey, ez, L, w, h, r, mat, nx=nx)


class _Plan:
    """a union of axis-aligned rectangles: intervals along a line, membership, outline pieces."""

    def __init__(self, rects):
        self.R = [tuple(float(v) for v in r) for r in rects]
        self.x0 = min(r[0] for r in self.R)
        self.x1 = max(r[1] for r in self.R)
        self.y0 = min(r[2] for r in self.R)
        self.y1 = max(r[3] for r in self.R)

    def inside(self, x, y):
        return any(r[0] <= x <= r[1] and r[2] <= y <= r[3] for r in self.R)

    @staticmethod
    def _merge(iv):
        iv = sorted(iv)
        out = []
        for a, b in iv:
            if out and a <= out[-1][1] + 1e-6:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out

    def x_at(self, y):
        return self._merge([(r[0], r[1]) for r in self.R if r[2] - 1e-6 <= y <= r[3] + 1e-6])

    def y_at(self, x):
        return self._merge([(r[2], r[3]) for r in self.R if r[0] - 1e-6 <= x <= r[1] + 1e-6])

    def edges(self, step=0.05):
        """free outline runs: (p0, p1, outward normal (2,)) for every rectangle edge part not inside another one."""
        out = []
        for r in self.R:
            x0, x1, y0, y1 = r
            for (a, b, nrm) in (((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)),
                                ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))):
                a, b = np.array(a, float), np.array(b, float)
                L = float(np.linalg.norm(b - a))
                ts = np.linspace(0, 1, max(2, int(L / step) + 1))
                mids = 0.5 * (ts[1:] + ts[:-1])
                free = [not self.inside(*(a + (b - a) * m + np.array(nrm) * 0.02)) for m in mids]
                k = 0
                while k < len(mids):
                    if not free[k]:
                        k += 1
                        continue
                    j = k
                    while j + 1 < len(mids) and free[j + 1]:
                        j += 1
                    out.append((a + (b - a) * ts[k], a + (b - a) * ts[j + 1], np.array(nrm, float)))
                    k = j + 1
        return out


def pile_deck(g, name, rects, deck_z=0.5, bed_z=-2.5, land=None, land_z=0.0, pile_rows=1.6, pile_cols=1.8,
              pile_r=0.13, plank=(0.20, 0.30), plank_t=0.05, gap=0.006, joist=(0.10, 0.16), joist_sp=0.55,
              bearer=(0.20, 0.22), fascia=0.24, brace_z=(-1.6, None), moor=(), moor_h=0.75, land_edge=0.25,
              first_row=0.55, seed=611):
    """KIT COMPONENT (see the module doc).  moor: [(x, y), ...] plan points: the pile nearest each runs up `moor_h`
    above the deck as a mooring post (the planks are notched round it)."""
    P = _Plan(rects)
    rng = np.random.default_rng(seed)
    pre = f"{g.prefix}_{name}"
    piles, struct, planks, fasc, iron = (Acc(pre + "_piles"), Acc(pre + "_structure"), Acc(pre + "_planks"),
                                         Acc(pre + "_fascia"), Acc(pre + "_ironwork"))
    z_pl = deck_z - plank_t                               # plank underside = joist top
    z_jb = z_pl - joist[1]                                # joist bottom = bearer top
    z_bb = z_jb - bearer[1]                               # bearer bottom = pile top
    if land not in (None, "S", "N"):
        raise ValueError("pile_deck: land must be None, 'S' (the -Y end) or 'N' (the +Y end)")
    # ---- pile rows (along Y) and the piles of each row
    y_lo = P.y0 + (first_row if land == "S" else 0.25)
    y_hi = P.y1 - (first_row if land == "N" else 0.25)
    nr = max(1, int(math.ceil((y_hi - y_lo) / pile_rows)))
    rows = np.linspace(y_lo, y_hi, nr + 1)
    pile_pts = []
    for y in rows:
        for (a, b) in P.x_at(y):
            npc = max(1, int(math.ceil((b - a - 0.4) / pile_cols)))
            xs = np.linspace(a + 0.2, b - 0.2, npc + 1)
            for x in xs:
                pile_pts.append((float(x), float(y)))
            _beam(struct, (a - 0.05, y, z_bb + bearer[1] / 2), (b + 0.05, y, z_bb + bearer[1] / 2), bearer[0],
                  bearer[1], "M_timber", nx=max(4, int((b - a) / 1.2) + 2))
            # iron dog plates on the outer face of the bearer at each pile (bearer to pile)
            for x in xs:
                wbox(iron, (np.array([x - 0.03, y - bearer[0] / 2, 0.0]), np.array([1.0, 0, 0]),
                            np.array([0, -1.0, 0])), 0.0, 0.06, z_bb - 0.14, z_jb - 0.03, 0.0, 0.008, "M_iron",
                     r=0.002)
    moor_set = set()
    for (mx, my) in moor:
        d = [math.hypot(px - mx, py - my) for (px, py) in pile_pts]
        moor_set.add(int(np.argmin(d)))
    for k, (x, y) in enumerate(pile_pts):
        top_z = (deck_z + moor_h) if k in moor_set else z_bb + 0.01
        pile(piles, (x, y, top_z), (x, y, bed_z), r=pile_r * (1.15 if k in moor_set else 1.0), rng=rng)
    # ---- joists along Y (land end on a ledger on the quay at land_z)
    for (a, b) in [(P.x0, P.x1)]:
        nj = max(2, int(math.ceil((b - a - 0.2) / joist_sp)))
        for x in np.linspace(a + 0.10, b - 0.10, nj + 1):
            for (c, d) in P.y_at(x):
                c_ = c + (0.02 if land == "S" else 0.06)
                d_ = d - (0.02 if land == "N" else 0.06)
                _beam(struct, (x, c_, z_jb + joist[1] / 2), (x, d_, z_jb + joist[1] / 2), joist[0], joist[1],
                      "M_timber", nx=max(4, int((d_ - c_) / 1.2) + 2))
    if land in ("S", "N"):
        yl = P.y0 + land_edge / 2 if land == "S" else P.y1 - land_edge / 2
        for (a, b) in P.x_at(yl):
            # the ledger: one closed beam from the quay top up to the joists
            _beam(struct, (a - 0.02, yl, (land_z + z_jb) / 2), (b + 0.02, yl, (land_z + z_jb) / 2), 0.22,
                  z_jb - land_z, "M_timber", nx=max(4, int((b - a) / 1.2) + 2))
    # ---- deck planks along X, 6 mm gaps, notched round the mooring posts
    y = P.y0 + (0.0 if land == "S" else 0.0)
    ys = [y]
    while P.y1 - ys[-1] > plank[1]:
        ys.append(ys[-1] + rng.uniform(*plank))
    ys.append(P.y1)
    if len(ys) > 2 and ys[-1] - ys[-2] < 0.6 * plank[0]:
        ys.pop(-2)
    moors = [pile_pts[k] for k in sorted(moor_set)]
    n_pl = 0
    for k in range(len(ys) - 1):
        ya, yb = ys[k] + gap / 2, ys[k + 1] - gap / 2
        ym = 0.5 * (ya + yb)
        for (a, b) in P.x_at(ym):
            pieces = [(a, b)]
            for (mx, my) in moors:
                if ya - 0.16 < my < yb + 0.16:
                    nxt = []
                    for (u, v) in pieces:
                        if mx - 0.17 > u:
                            nxt.append((u, min(v, mx - 0.17)))
                        if mx + 0.17 < v:
                            nxt.append((max(u, mx + 0.17), v))
                    pieces = nxt
            for (u, v) in pieces:
                if v - u < 0.08:
                    continue
                F = (np.array([0.0, ya, 0.0]), np.array([1.0, 0, 0]), np.array([0, -1.0, 0]))
                # one board: s along x, w = -y (so w in [-(yb - ya), 0])
                wbox(planks, F, u, v, z_pl + rng.uniform(-0.003, 0.003), deck_z + rng.uniform(-0.003, 0.003),
                     -(yb - ya), 0.0, "M_timber_weathered", r=0.008, ns=max(4, int((v - u) / 1.0) + 3))
                n_pl += 1
    # ---- fascia boards on every free edge (not the land side)
    for (p0, p1, nrm) in P.edges():
        if land == "S" and nrm[1] < -0.5 and abs(p0[1] - P.y0) < 1e-6:
            continue
        if land == "N" and nrm[1] > 0.5 and abs(p0[1] - P.y1) < 1e-6:
            continue
        d = p1 - p0
        L = float(np.linalg.norm(d))
        t = np.array([d[0] / L, d[1] / L, 0.0])
        n = np.array([nrm[0], nrm[1], 0.0])
        F = (np.array([p0[0], p0[1], 0.0]), t, n)
        wbox(fasc, F, -0.035, L + 0.035, deck_z - fascia, deck_z - 0.012, 0.0, 0.035, "M_timber", r=0.008,
             ns=max(4, int(L / 1.2) + 3))
    # ---- bracing: X braces between neighbouring piles on the outer lines, and a waling
    z_b0 = brace_z[0]
    z_b1 = z_bb - 0.10 if brace_z[1] is None else brace_z[1]
    pts = np.array(pile_pts)
    for y in rows:
        row = sorted([p for p in pile_pts if abs(p[1] - y) < 1e-6])
        outer = (abs(y - rows[-1]) < 1e-6) or (abs(y - rows[0]) < 1e-6 and land is None)
        if outer:
            off = (1 if abs(y - rows[-1]) < 1e-6 else -1) * (pile_r + 0.04)
            for (pa, pb) in zip(row[:-1], row[1:]):
                for (za, zb) in ((z_b0, z_b1), (z_b1, z_b0)):
                    _beam(struct, (pa[0], pa[1] + off, za), (pb[0], pb[1] + off, zb), 0.06, 0.16,
                          "M_timber_weathered", up=(0.0, 1.0, 0.0))
                off_ = off + 0.07 * np.sign(off)
            if len(row) > 1:
                _beam(struct, (row[0][0] - 0.15, row[0][1] + off + 0.07 * np.sign(off), -0.55),
                      (row[-1][0] + 0.15, row[-1][1] + off + 0.07 * np.sign(off), -0.55), 0.07, 0.18,
                      "M_timber_weathered", up=(0.0, 1.0, 0.0))
    for side_x in ("lo", "hi"):
        col = []
        for y in rows:
            row = sorted([p for p in pile_pts if abs(p[1] - y) < 1e-6])
            col.append(row[0] if side_x == "lo" else row[-1])
        sg = -1 if side_x == "lo" else 1
        for (pa, pb) in zip(col[:-1], col[1:]):
            if abs(pa[0] - pb[0]) > 0.3:
                continue
            off = sg * (pile_r + 0.04)
            for (za, zb) in ((z_b0, z_b1), (z_b1, z_b0)):
                _beam(struct, (pa[0] + off, pa[1], za), (pb[0] + off, pb[1], zb), 0.06, 0.16, "M_timber_weathered",
                      up=(1.0, 0.0, 0.0))
    _ = pts
    clip = dict(clip_z=bed_z - 0.01)
    for a_ in (piles, struct, planks, fasc, iron):
        if a_.n:
            finalize(a_, g.coll, smooth_deg=30.0, **clip)
    if not hasattr(g, "DECKS"):
        g.DECKS = []
    g.DECKS.append(dict(name=name, plan=P, deck_z=deck_z, bed_z=bed_z, piles=pile_pts, moor=moors, land=land))
    log(f"  {pre}: deck {P.x1 - P.x0:.2f} x {P.y1 - P.y0:.2f} m, {len(pile_pts)} piles, {n_pl} planks")
    return P


QUAY_BLOCKS = dict(ch=(0.28, 0.48), ch_mix=[(0.35, 0.28, 0.34), (0.40, 0.34, 0.41), (0.25, 0.41, 0.48)],
                  len=(0.70, 1.40), foot_len=(0.90, 1.60), p_tall=0.03, p_double=0.0, p_long=0.10)
"""round 2: the quay's LARGE blocks (ref4) -- rubble_walls.path_stone_wall's coursing table with courses of 28-48 cm
and stones 0.70-1.40 m (the bible's through-stone end of the range): fewer, bigger stones (note 15)."""


BLOCK_DEPTH, BLOCK_FACE = 0.30, 0.012
"""the core blocks' bed depth behind the face line and their face set-back (w -0.30 .. -0.012)."""


def _block_courses(rng, z0, z1, ch=(0.42, 0.58)):
    """course boundaries [(za, zb), ...] from z0 to z1 (42-58 cm; the last course takes the remainder >= 20 cm).
    Round 3: drawn ONCE per quay face group, so the runs meeting at a corner share their beds (quoin bond)."""
    out, z = [], z0
    while z < z1 - 0.05:
        h = float(rng.uniform(*ch))
        if z1 - (z + h) < 0.2:
            h = z1 - z
        out.append((z, z + h))
        z += h
    return out


def _core_blocks(acc, F, s0, s1, z0, z1, rng, ch=(0.42, 0.58), ln=(0.85, 1.55), gap=0.022, courses=None,
                 quoin=(None, None)):
    """the submerged core laid as LOW-POLY large blocks (round 2b): courses of 42-58 cm, blocks 0.85-1.55 m, broken
    joints, each block a closed rounded box (~60 tris) a little out of line (+-1.2 cm), on the recessed joint
    backing -- it reads as ref4's big quay blocks from any distance at ~1 % of the rubble's triangles.
    Round 3 (v5-only): courses = the group's shared course list (None: drawn here, the round-2 behaviour).
    quoin = (start, end): None, or the parity p of a CONVEX corner at that end (the run's corner point is s = 0 /
    s = s1 - its e1 extension is ignored there).  On course k the run OWNS the corner when (k + p) is even: its end
    block runs through the corner to the other run's face plane (s = BLOCK_FACE in from the corner), so its end face
    is seen flush on the other face; otherwise it BUTTS that block's back (s = BLOCK_DEPTH + gap / 2 in from the
    corner).  The two runs get opposite parities, so the corner is a long-and-short quoin bond with no straight
    vertical joint; the only joints are the 2.2 cm beds and 1.1 cm butt joints."""
    if courses is None:
        courses = _block_courses(rng, z0, z1, ch)
    for k, (za, zb) in enumerate(courses):
        lo_c, hi_c = quoin
        lo = s0 + gap / 2 if lo_c is None else (BLOCK_FACE if (k + lo_c) % 2 == 0 else BLOCK_DEPTH + gap / 2)
        hi = s1 - gap / 2 if hi_c is None else (s1 - BLOCK_FACE if (k + hi_c) % 2 == 0
                                                else s1 - BLOCK_DEPTH - gap / 2)
        stagger = 0.0 if (k % 2 == 0 or lo_c is not None) else float(rng.uniform(0.3, 0.6))
        s = lo - stagger
        while s < hi - 0.05:
            L = float(rng.uniform(*ln))
            if hi - (s + L) < 0.35:
                L = hi - s
            a = max(s, lo) + (0.0 if s <= lo + 1e-9 else gap / 2)
            b = min(s + L, hi) - (0.0 if s + L >= hi - 1e-9 else gap / 2)
            if b - a > 0.1:
                dw = float(rng.uniform(-0.012, 0.012))
                top = zb - (gap / 2 if zb < z1 - 1e-6 else 0.0)          # the top course: flush coping
                wbox(acc, F, a, b, za + gap / 2, top, -BLOCK_DEPTH, -BLOCK_FACE + dw, "M_stone", r=0.035, ns=2,
                     nz=2, tilt=float(rng.uniform(-0.006, 0.006)))
            s += L


def stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, cfg=None, seed=651, coping=True, detail_z=-0.9,
               core_blocks=False):
    """KIT COMPONENT (round 2; replaces the retired timber crib quay): a harbour quay edge of large rubble blocks
    (rubble_walls.path_stone_wall with QUAY_BLOCKS) along a plan polyline (interior = the land on the LEFT, so each
    face looks out over the water on the right).  water: the runs that are WATER faces -- a list of run indices of
    the path, or None (all): those run from the bed (bed_z) to the quay top; every other run is a LAND face, buried
    by the quay ground at the datum, and is not built (producer note 6: nothing deeper than 5 cm; the land side is
    terrain).  Each water run is laid as its own open stone wall, so its foot is the bed and its corners get quoins.
    coping: the top course is the wall's own top course at top_z (no separate coping object).
    detail_z: the blocks are laid from here (the tidal band, -0.9 m: where the waterline anchors and the camera are)
    up; below it, down to the bed, the wall's submerged CORE is one closed rubble slab per run, set 2 cm behind the
    face line (note 6: under water nothing is seen at close range; None = blocks all the way to the bed).
    core_blocks: round 2b -- the core is laid as low-poly large blocks on a recessed joint backing (_core_blocks), so
    the face below detail_z still reads as ref4's quay blocks (clay / low-water views) at ~60 tris a block; with
    detail_z >= top_z - 0.05 the WHOLE face is that block masonry (no rubble band; the top course is the coping).
    Round 3: the joint backing is its own object <P>_<name>_backing_blocker (never culled: composite.BACKING) and
    every CONVEX corner between two water runs is quoin-bonded (shared courses; alternate courses' end blocks run
    through the corner by the block depth, see _core_blocks).  -> <P>_<name>_core, <P>_<name>_backing_blocker.
    Publishes g.QUAYS (dict(name, water=[PathMap ...], top_z, bed_z)) -- the waterline anchors
    (composite.waterfront_anchors) go only on these water faces, between -0.9 m and the datum."""
    from .rubble_walls import PathMap, path_stone_wall
    A = [tuple(map(float, p)) for p in path]
    runs = list(range(len(A) - 1)) if water is None else sorted(int(i) for i in water)
    groups, cur = [], []
    for i in runs:                                    # consecutive water runs form one open wall (shared corners)
        if cur and i != cur[-1] + 1:
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    blocks_only = bool(core_blocks) and detail_z is not None and float(detail_z) >= top_z - 0.05
    z_b = bed_z if detail_z is None else (top_z if blocks_only else max(bed_z, float(detail_z)))
    cfg_ = dict(QUAY_BLOCKS, footing=z_b + 0.42, **(cfg or {}))     # the footing course sits on the base, not z 0.30
    maps = []
    core = Acc(f"{g.prefix}_{name}_core")
    # round 3: the joint backing is its OWN object, named into composite.BACKING ("_blocker"), so the hidden-geometry
    # cull can never remove it from behind a visible joint (producer note 6)
    back = Acc(f"{g.prefix}_{name}_backing_blocker")
    rng_c = np.random.default_rng(seed + 7)
    n_q = 0
    for k, grp in enumerate(groups):
        pts = [A[grp[0]]] + [A[i + 1] for i in grp]
        if blocks_only:                                  # the whole face is the low-poly block masonry
            pm = PathMap(pts)
        else:
            pm = path_stone_wall(g, f"{name}_{k}", pts, top=top_z, openings=(), seed=seed + 13 * k, cfg=cfg_,
                                 base=z_b, clip_z=bed_z - 0.01)
        maps.append(pm)
        if z_b > bed_z + 0.05:
            z_top = top_z if blocks_only else z_b + 0.10
            courses = _block_courses(rng_c, bed_z, z_top) if core_blocks else None   # shared by the group

            def convex(j):
                if j <= 0 or j >= len(pm.L):
                    return False
                a_, b_ = pm.dir[j - 1], pm.dir[j]
                return a_[0] * b_[1] - a_[1] * b_[0] > 1e-6

            def ext(j):                                          # close the core's corners
                if j <= 0 or j >= len(pm.L):
                    return 0.0
                return 0.02 if convex(j) else 0.12
            for i in range(len(pm.L)):
                O = np.array([pm.A[i][0], pm.A[i][1], 0.0])
                F = (O, np.array([*pm.dir[i], 0.0]), np.array([*pm.nrm[i], 0.0]))
                e0, e1 = ext(i), ext(i + 1)
                Li = float(pm.L[i])
                if core_blocks:                      # the joint backing, recessed behind the blocks
                    # corner c (run c-1 -> run c) has parity c: run c-1 ends with p = c, run c starts with p = c + 1,
                    # so on every course exactly one of the two owns the corner
                    q0 = (i + 1) if convex(i) else None
                    q1 = (i + 1) if convex(i + 1) else None
                    n_q += int(q1 is not None)
                    # the backing stops at the other run's backing face at a convex corner (closed round it,
                    # nothing past either face)
                    b0 = 0.07 if q0 is not None else -e0
                    b1 = Li - 0.07 if q1 is not None else Li + e1
                    wbox(back, F, b0, b1, bed_z, z_top - 0.03, -0.20, -0.07, "M_stone", r=0.03,
                         ns=max(4, int(pm.L[i] / 1.5) + 2), nz=3)
                    _core_blocks(core, F, 0.0 if q0 is not None else -e0, Li if q1 is not None else Li + e1,
                                 bed_z, z_top, rng_c, courses=courses, quoin=(q0, q1))
                else:
                    wbox(core, F, -e0, float(pm.L[i]) + e1, bed_z, z_b + 0.12, -0.12, -0.02, "M_rubble", r=0.03,
                         ns=max(4, int(pm.L[i] / 1.5) + 2), nz=3)
    for a_ in (core, back):
        if a_.n:
            finalize(a_, g.coll, smooth_deg=30.0, clip_z=bed_z - 0.01)
    if n_q:
        log(f"  {g.prefix}_{name}: {n_q} convex corner(s) quoin-bonded (shared courses, alternate overrun "
            f"{BLOCK_DEPTH:.2f} m)")
    if not hasattr(g, "QUAYS"):
        g.QUAYS = []
    g.QUAYS.append(dict(name=name, water=maps, top_z=top_z, bed_z=bed_z))
    log(f"  {g.prefix}_{name}: stone quay, {len(groups)} water face run(s) from the bed {bed_z:.2f} to {top_z:.2f} m; "
        f"{len(A) - 1 - len(runs)} land run(s) left to the terrain")
    return maps


def ladder(g, name, top, out, z_bot, width=0.46, rung_sp=0.30, rail=(0.07, 0.10), rung_r=0.022, set_off=0.06,
           above=0.55, seed=641):
    """KIT COMPONENT: a timber ladder against a face: top = (x, y, z) of the deck / quay edge at the ladder's centre,
    out = horizontal outward direction of the face; the stiles run `above` m over the edge (hand holds) and down to
    z_bot; rungs every rung_sp."""
    top = np.asarray(top, float)
    o = np.array([out[0], out[1], 0.0], float)
    o /= np.linalg.norm(o)
    t = np.array([-o[1], o[0], 0.0])
    pre = f"{g.prefix}_{name}"
    acc = Acc(pre)
    rng = np.random.default_rng(seed)
    for sg in (-1, 1):
        b = top + t * sg * width / 2 + o * (set_off + rail[1] / 2)
        p0 = np.array([b[0], b[1], z_bot])
        p1 = np.array([b[0], b[1], top[2] + above])
        _beam(acc, p0, p1, rail[0], rail[1], "M_timber_weathered", up=(o[0], o[1], 0.0), nx=6)
    z = top[2] - 0.25
    while z > z_bot + 0.15:
        c = top + o * (set_off + rail[1] / 2)
        p0 = np.array([c[0], c[1], z]) - t * (width / 2 + 0.02)
        p1 = np.array([c[0], c[1], z]) + t * (width / 2 + 0.02)
        path = np.stack([p0, p1])
        a = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        V, F = sweep(path, (0.0, 0.0, 1.0), np.stack([rung_r * np.cos(a), rung_r * np.sin(a)], 1))
        acc.add(V, F, "M_timber", wear=float(rng.uniform(0.2, 0.6)))
        z -= rung_sp
    finalize(acc, g.coll, smooth_deg=30.0, clip_z=z_bot - 0.01)
    if not hasattr(g, "LADDERS"):
        g.LADDERS = []
    g.LADDERS.append(dict(name=name, top=top, out=o, z_bot=z_bot))


__all__ = ["pile", "pile_deck", "stone_quay", "QUAY_BLOCKS", "ladder"]
