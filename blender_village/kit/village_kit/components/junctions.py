"""components.junctions -- junction pieces between bodies of DIFFERENT module families (kit 1.7.0 candidate, v4_mixed).

They run as compound junction steps fn(c, ...) (village_kit.compound) after every wing is placed, read the placed
geometry / frames of the wings they join and build their own objects <junction prefix>_<part> in world coordinates.
The body descriptions are generic -- a round TOWER is (centre, outer face radius R(z)), a ROOF is a set of placed
roof objects ray-cast from above, a round WALL is (centre, face radius) -- so the same pieces close a hut cone
against a mill drum, a drum against an octagonal hall's turret, a cone against a keep cone, etc.  Adapters read
them from the family frames (tower_of / round_wall_of).

    roof_tower_flashing(c, roof, tower, ...)   where a roof runs INTO a round masonry tower: the true roof-top /
        tower-face intersection is traced by ray casts on the built roofing and closed with the keep family's
        flaunching language (components.thatch.flaunch_loop: a lime-mortar fillet where the line is flatter than
        `steep_deg`, stepped lead flashing tucked into the bed joints where it is steeper); the run's ends are
        dressed down over the cut eave lip with a lead end-apron so no shingle edge shows against the stone
        -> <P>_<name>_fillet (M_mortar / M_lead)
    wall_tower_abutment(c, wall, tower, ...)   where a round post-and-infill wall runs into a round masonry tower: a
        hewn abutment post (components.hewn.hewn_square, the keep family's square timber) on each side, its drum
        half let into the masonry, covering the daub / stone seam from the plinth to the wall plate, with a mortar
        bead pointing the post / stone seam -> <P>_<name>_posts (M_timber), <P>_<name>_pointing (M_mortar)

Decal anchors (producer note 11) for the junction: moss in the roof valley against the tower (debris collects
there) and damp rising at the abutment-post feet -- added to c.decals and audited with the whole building.
"""
import math

import numpy as np

from ..core import log


# =================================================================================================================
# body adapters (family frame -> generic description in world coordinates)
# =================================================================================================================
def tower_of(c, name):
    """a placed DrumFrame wing as a round tower: centre (x, y) and the outer face radius R(z) (battered drum)."""
    from .drum_frame import R_out
    w = c.wing(name)
    g = w.g
    return dict(center=w.center[:2], R=lambda z, g=g: np.asarray(R_out(g, np.asarray(z, float)), float),
                z_top=float(g.Z_CORN0), name=name)


def round_wall_of(c, name):
    """a placed RoundFrame wing as a round post-and-infill wall: centre, wattle line, coat face, plinth top, plate."""
    w = c.wing(name)
    g = w.g
    return dict(center=w.center[:2], r_line=float(g.R_WALL), r_coat=float(g.R_WALL + g.COAT_R_NOM),
                z0=float(g.PLINTH_TOP), z_plate=float(g.PLATE_BOT), z_plate_top=float(g.PLATE_TOP), name=name)


def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    V, T, nv = [], [], 0
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", lt)
        V.append(co)
        T.append(lt.reshape(-1, 3) + nv)
        nv += len(co)
    V = np.concatenate(V)
    T = np.concatenate(T)
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)


def _down(bvh, x, y, z_from=40.0):
    from mathutils import Vector
    hit = bvh.ray_cast(Vector((float(x), float(y), z_from)), Vector((0.0, 0.0, -1.0)), z_from + 1.0)
    return None if hit[0] is None else float(hit[0][2])


# =================================================================================================================
# roof into a round tower
# =================================================================================================================
def trace_roof_on_tower(bvh, tower, offsets=(0.006, 0.02), step_deg=0.5, z_guess=3.0):
    """the line where the roof top meets the tower face: for every azimuth round the tower centre the highest
    roof-top hit just outside the face (R(z) + offsets), iterated for the batter.  Returns the contiguous runs
    [(theta (n,), P (n, 3))] (theta = math angle about the tower centre)."""
    C = np.asarray(tower["center"], float)
    th = np.radians(np.arange(0.0, 360.0, step_deg))
    Z = np.full(len(th), np.nan)
    for i, t in enumerate(th):
        d = np.array([math.cos(t), math.sin(t)])
        z = z_guess
        zz = None
        for _ in range(3):
            hs = []
            for off in offsets:
                r = float(tower["R"](z)) + off
                h = _down(bvh, C[0] + d[0] * r, C[1] + d[1] * r)
                if h is not None:
                    hs.append(h)
            if not hs:
                zz = None
                break
            zz = max(hs)
            z = zz
        if zz is not None:
            Z[i] = zz
    ok = np.isfinite(Z)
    if not ok.any():
        return []
    # close short misses (a ray slipping through a shingle joint) by interpolation: <= max_gap samples
    max_gap = max(2, int(round(3.0 / step_deg)))
    n_ = len(Z)
    i = 0
    while i < n_:
        if ok[i]:
            i += 1
            continue
        j = i
        while j < n_ and not ok[j]:
            j += 1
        a, b = i - 1, j % n_
        if j - i <= max_gap and ok[a % n_] and ok[b] and (i > 0 or ok[-1]):
            za, zb = Z[a % n_], Z[b]
            for k_ in range(i, j):
                f = (k_ - a) / (j - a)
                Z[k_] = za * (1 - f) + zb * f
        i = j
    ok = np.isfinite(Z)
    if ok.all():
        raise ValueError("roof covers the whole tower: not a roof-into-tower junction")
    # contiguous runs on the circle
    k0 = int(np.flatnonzero(~ok)[0])
    order = np.roll(np.arange(len(th)), -k0)
    runs, cur = [], []
    for i in order:
        if ok[i]:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    out = []
    for r_ in runs:
        if len(r_) < 4:
            continue
        idx = np.array(r_)
        t_ = np.unwrap(th[idx])
        z_ = Z[idx]
        rr = np.array([float(tower["R"](zv)) for zv in z_])
        P = np.stack([C[0] + rr * np.cos(t_), C[1] + rr * np.sin(t_), z_], 1)
        out.append((t_, P))
    return out


def _smooth_up(z, n_max=3, n_avg=4):
    """upper envelope (running max over +-n_max samples) then a light smoothing: the line rides on the shingle tops."""
    z = np.asarray(z, float)
    m = np.array([z[max(0, i - n_max):i + n_max + 1].max() for i in range(len(z))])
    for _ in range(n_avg):
        m[1:-1] = 0.25 * m[:-2] + 0.5 * m[1:-1] + 0.25 * m[2:]
    return np.maximum(m, z)


def end_apron(acc, P_end, out_n, along, drop, w=0.16, t=0.004, proud=0.025, turn=0.05):
    """lead end-apron where a roof's cut eave lip meets a wall: a plate on the wall face from just above the roof
    line down over the lip (`drop`), `w` wide toward the roof, its lower edge turned out `turn` under the lip."""
    n = np.asarray(out_n, float)
    n = n / np.linalg.norm(n)
    a = np.asarray(along, float)
    a = a - n * (a @ n)
    a[2] = 0.0
    a = a / (np.linalg.norm(a) + 1e-9)
    z = np.array([0.0, 0.0, 1.0])
    P = np.asarray(P_end, float)
    # plate: u along a (0..w), v down (0..drop+0.06), thickness t standing proud of the face
    us = np.linspace(-0.03, w, 5)
    vs = np.linspace(-0.06, drop, 6)
    U, Vv = np.meshgrid(us, vs, indexing="ij")
    base = P[None, None] + a[None, None] * U[..., None] - z[None, None] * Vv[..., None]
    F0 = base + n * proud
    F1 = base + n * (proud + t)
    # turned-out lower edge
    nu, nv = U.shape
    from ..core import grid_quads
    Vf = np.concatenate([F1.reshape(-1, 3), F0.reshape(-1, 3)])
    q_out = grid_quads(nu, nv)
    q_in = grid_quads(nu, nv, nu * nv)[:, ::-1]
    # side walls (close the plate)
    ii = np.arange(nu)
    jj = np.arange(nv)
    o = nu * nv
    sides = []
    for j0 in (0, nv - 1):
        for i in range(nu - 1):
            a0, b0 = ii[i] * nv + j0, ii[i + 1] * nv + j0
            sides.append([a0, b0, b0 + o, a0 + o] if j0 == 0 else [b0, a0, a0 + o, b0 + o])
    for i0 in (0, nu - 1):
        for j in range(nv - 1):
            a0, b0 = i0 * nv + jj[j], i0 * nv + jj[j + 1]
            sides.append([b0, a0, a0 + o, b0 + o] if i0 == 0 else [a0, b0, b0 + o, a0 + o])
    acc.add(Vf, [q_out, q_in, np.array(sides)], "M_lead")
    # drip lip: a small rolled bead along the bottom edge, turned out
    bot = base[:, -1] + n * proud
    lip = np.concatenate([bot, bot + n * turn - z * 0.012, bot + n * turn - z * 0.012 - z * t,
                          bot - z * t])
    m_ = len(bot)
    quads = []
    for k in range(3):
        for i in range(m_ - 1):
            quads.append([k * m_ + i, k * m_ + i + 1, (k + 1) * m_ + i + 1, (k + 1) * m_ + i])
    acc.add(lip, [np.array(quads)[:, ::-1]], "M_lead")


def roof_tower_flashing(c, roof, tower, roof_parts=("roof_shingles", "roof_starter"), name="roof_tower",
                        steep_deg=50.0, bury=0.035, lift=0.012, mortar_only=False, end_aprons=True, seed=2601,
                        decals=True):
    """JUNCTION: a placed roof (wing `roof`, its roofing objects roof_parts) runs into a placed round masonry tower
    (wing `tower`).  Traces the true roof-top / tower-face line and closes it with the keep family's flaunching
    (thatch.flaunch_loop: mortar fillet where flatter than steep_deg, stepped lead flashing where steeper; the
    fillet's back buried `bury` m in the masonry), lifted `lift` m over the highest shingle at the face; each run
    end gets a lead end-apron over the cut eave lip.  Object <P>_<name>_fillet.  Returns the traced runs."""
    from .thatch import flaunch_loop
    rw = c.wing(roof)
    T = tower_of(c, tower)
    objs = [o for o in rw.meshes() if any(o.name == f"{rw.prefix}_{p}" for p in roof_parts)]
    if not objs:
        raise ValueError(f"no roofing objects {roof_parts} in wing {roof}")
    bvh = _bvh(objs)
    runs = trace_roof_on_tower(bvh, T, z_guess=float(getattr(rw.g, "Z_EAVE", 3.0)) + 0.5)
    acc = c.acc(f"{name}_fillet")
    C = np.asarray(T["center"], float)
    for k, (th, P) in enumerate(runs):
        P = P.copy()
        P[:, 2] = _smooth_up(P[:, 2]) + lift
        log(f"  {name}: run {k}: {len(P)} samples, azimuth {np.degrees(th[0]):.1f}..{np.degrees(th[-1]):.1f} deg, "
            f"z {P[:, 2].min():.2f}..{P[:, 2].max():.2f}")
        flaunch_loop(acc, P, C, seed + 17 * k, steep_deg=steep_deg, mortar_only=mortar_only, bury=bury)
        if end_aprons:
            # at each run end (the cut eave lip against the stone) the apron reaches 16 cm past the lip, 16 cm down
            for i0, i1 in ((0, 1), (-1, -2)):
                n_out = np.array([P[i0, 0] - C[0], P[i0, 1] - C[1], 0.0])
                end_apron(acc, P[i0] + np.array([0, 0, 0.02]), n_out, P[i0] - P[i1], 0.16)
        if decals:
            _roof_junction_decals(c, P, C, seed + k)
    c.finalize(acc, smooth_deg=35.0)
    c.__dict__.setdefault("junction_runs", {})[name] = runs
    return runs


def _roof_junction_decals(c, P, C, seed):
    """moss in the roof valley against the tower (debris collects there), 0.3 m out from the face on the shingles
    -- on the built surfaces (SurfaceProbe), audited later with the building."""
    from ..decals import SurfaceProbe
    probe = getattr(c, "_probe", None)
    if probe is None:
        probe = SurfaceProbe([o for w in c.wings.values() for o in w.meshes()])
        c._probe = probe
    rng = np.random.RandomState(seed)
    n = len(P)
    for f in (0.3, 0.5, 0.7):
        i = int(f * (n - 1))
        d = np.array([P[i, 0] - C[0], P[i, 1] - C[1], 0.0])
        d /= np.linalg.norm(d)
        q = P[i] + d * 0.30
        hit = probe.cast((q[0], q[1], q[2] + 1.5), (0, 0, -1), 3.0)
        c.decals.add_hit("moss", hit, (0.45, 0.35), probability=0.7, seed=int(rng.randint(1 << 30)),
                         surfaces={"M_roof_shingle"}, up=tuple(-d))


# =================================================================================================================
# round wall into a round tower
# =================================================================================================================
def _circle_x(c1, r1, c2, r2):
    """the two intersection points of two circles (plan)."""
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    d = float(np.linalg.norm(c2 - c1))
    if d > r1 + r2 or d < abs(r1 - r2):
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    e = (c2 - c1) / d
    p = c1 + a * e
    nrm = np.array([-e[1], e[0]])
    return [p + h * nrm, p - h * nrm]


def wall_tower_abutment(c, wall, tower, name="abutment", post=(0.22, 0.22), into=0.04, z_mid=1.2, seed=2701,
                        pointing=0.032, decals=True):
    """JUNCTION: a placed round post-and-infill wall (wing `wall`, RoundFrame) runs into a placed round masonry tower
    (wing `tower`).  At both plan intersections of the wall's coat face with the tower face (at z_mid) a hewn
    abutment post (post = section along / across the wall, m) stands on the plinth up to the wall plate, slid along
    the wall until its tower-side outer corner is `into` m inside the masonry, so it straddles the seam; a mortar
    bead (radius `pointing`) points the line where the post's outer face leaves the stone.  Objects
    <P>_<name>_posts, <P>_<name>_pointing."""
    from .hewn import hewn_square
    from ..core import tube
    Wl = round_wall_of(c, wall)
    T = tower_of(c, tower)
    H = np.asarray(Wl["center"], float)
    C = np.asarray(T["center"], float)
    Rt = float(T["R"](z_mid))
    pts = _circle_x(H, Wl["r_coat"], C, Rt)
    if not pts:
        log(f"  {name}: wall and tower do not meet")
        return []
    accp = c.acc(f"{name}_posts", 40.0)
    accm = c.acc(f"{name}_pointing", 50.0)
    rng = np.random.default_rng(seed)
    wy, wz = post
    z0, z1 = Wl["z0"] - 0.10, Wl["z_plate"] + 0.01
    r_c = Wl["r_line"] + 0.04               # post centre radius (outer face ~9 cm proud of the coat)
    placed = []
    for k, p in enumerate(pts):
        a0 = math.atan2(p[1] - H[1], p[0] - H[0])
        # which way along the wall is "into the tower"
        sgn = 1.0 if np.linalg.norm(H + Wl["r_coat"] * np.array([math.cos(a0 + 0.01), math.sin(a0 + 0.01)]) - C) \
            < np.linalg.norm(p - C) else -1.0

        def corner_in(a):
            n_ = np.array([math.cos(a), math.sin(a)])
            t_ = np.array([-n_[1], n_[0]]) * sgn
            q = H + n_ * (r_c + wz / 2) + t_ * (wy / 2)             # outer corner on the tower side
            return float(np.linalg.norm(q - C)) - float(T["R"](z_mid))
        lo, hi = a0 - sgn * 0.25, a0 + sgn * 0.25
        # bisection: corner_in(a) decreases moving toward the tower; find corner_in = -into
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            if corner_in(mid) > -into:
                lo = mid
            else:
                hi = mid
        a = 0.5 * (lo + hi)
        n3 = np.array([math.cos(a), math.sin(a), 0.0])
        t3 = np.array([-n3[1], n3[0], 0.0]) * sgn
        O = np.array([H[0] + n3[0] * r_c, H[1] + n3[1] * r_c, z0])
        hewn_square(accp, O, np.array([0, 0, 1.0]), t3, n3, z1 - z0, wy, wz, rng, mat="M_timber", chamfer=0.02,
                    nf=2, st_len=0.08, adze=0.0, wave=0.004, seed=seed + k)
        # the seam on the post's outer face: where that face line leaves the tower face
        def face_pt(s):
            return H + n3[:2] * (r_c + wz / 2) + t3[:2] * s
        s_lo, s_hi = -wy / 2, wy / 2
        for _ in range(40):
            sm = 0.5 * (s_lo + s_hi)
            if np.linalg.norm(face_pt(sm) - C) > float(T["R"](z_mid)):
                s_lo = sm
            else:
                s_hi = sm
        q = face_pt(0.5 * (s_lo + s_hi))
        zz = np.linspace(z0 + 0.06, z1 - 0.02, 24)
        path = []
        for zv in zz:
            # follow the batter: the seam point moves with R(z)
            s_lo, s_hi = -wy / 2, wy / 2
            Rz = float(T["R"](zv))
            for _ in range(30):
                sm = 0.5 * (s_lo + s_hi)
                if np.linalg.norm(face_pt(sm) - C) > Rz:
                    s_lo = sm
                else:
                    s_hi = sm
            qz = face_pt(0.5 * (s_lo + s_hi))
            path.append([qz[0], qz[1], zv])
        path = np.array(path)
        wob = 1.0 + 0.15 * np.sin(zz * 3.1 + k)
        Vt, Ft, uvt, wt = tube(path, pointing * wob, 8, up=tuple(n3))
        accm.add(Vt, Ft, "M_mortar", uvt, wt)
        placed.append(dict(center=O, normal=n3, along=t3))
        if decals:
            _post_decals(c, O, n3, t3, wy, wz, z0, seed + k)
        log(f"  {name}: post {k} at ({O[0]:.2f}, {O[1]:.2f}), seam {q.round(3).tolist()}")
    c.finalize(accp, smooth_deg=40.0)
    c.finalize(accm, smooth_deg=60.0)
    return placed


def _post_decals(c, O, n3, t3, wy, wz, z0, seed):
    """damp rising at the abutment post's foot (rain off the tower runs down the seam)."""
    from ..decals import SurfaceProbe
    probe = getattr(c, "_probe", None)
    if probe is None:
        probe = SurfaceProbe([o for w in c.wings.values() for o in w.meshes()])
        c._probe = probe
    p = np.array([O[0], O[1], 0.62]) - t3 * (wy * 0.15)
    hit = probe.cast(p + n3 * 0.4, -n3, 1.0)
    c.decals.add_hit("damp_rise", hit, (0.12, 0.40), probability=0.7, seed=seed, surfaces={"M_timber"})
