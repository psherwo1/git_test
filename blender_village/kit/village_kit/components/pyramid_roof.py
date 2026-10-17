"""components.pyramid_roof -- a reusable, bell-cast POLYGONAL PYRAMID shingle roof on any regular-polygon wall head
(kit changes v1_stone_watchtower round 4; new module, extracted from square_cabin's inline straight pyramid).

    pyramid_roof(g, p_wall, z_plate, name="pyramid", sides=4, rot_deg=-90.0, cx=0.0, cy=0.0, pitch_deg=48.0,
                 eave_out=0.50, bell_deg=0.0, bell_len=0.70, kick=0.0, kick_len=0.60, sag=0.0, exposure=0.34,
                 cap_r=0.62, finial_scale=0.80, finial_lean=0.5, rafter_step=0.60, t_deck=0.025, seed=None, rng=None)

The village's cap language (art bible 1.4 and the section-2 cap row) on ANY square, hexagonal or octagonal body:
a pyramid at `pitch_deg` whose last `bell_len` m of slope flatten by `bell_deg` toward the eave (sprocketed, bell-cast
eave; the hip lines come out concave in elevation), optional upturned hip corners (`kick` over `kick_len` in from the
lip) and a dished face between the hips (`sag`).  bell_deg = kick = sag = 0 is the straight pyramid of square_cabin
rounds 2-3, point for point (same deck, same shingles from the same rng).

  surface    PyramidSurface: facet k's outward normal at rot_deg + 360 k / sides (rot -90: facet 0 faces -Y), the
             deck underside passes over the plate top z_plate at the wall line p_wall (apothem), eave lip at
             p_wall + eave_out; under / top / normal(k, u, p) in facet coordinates (u along the facet, p apothem)
  structure  rafter tails bearing on the plate under the overhang and a hip rafter at every hip, all swept along the
             true (curved) roof surface                                                  -> <P>_<name>_roof_frame
  deck       closed sarking deck (top, soffit, eave edge; shared hip / apex points: closed) -> <P>_<name>_roof_deck
  covering   a starter board, then coursed kit shingles (shingles.shingle_mesh, SHINGLE_VARIANTS, SIZE_TABLE)
             bent onto the surface and trimmed at the hips                                 -> <P>_<name>_shingles
  hips       ONE closed saddle (two boards meeting over the hip) per hip, swept along the curved hip line (no open
             V slot between two separate boards)                                            -> <P>_<name>_hips
  apex       a polygonal lead cap lifted clear of every shingle / hip vertex under it, a round lead sleeve seating the
             finial, and the kit's turned finial at `finial_scale` (finial.turned_finial; 0.8 = 1.16 m above the
             cap, art bible 1.5: 0.9-1.3 m)                                       -> <P>_<name>_lead / _finial

Returns a record dict(objs, surface, r_eave, z_eave, z_eave_corner, apex, cap_top, collar_drip, tip, ...); `tip` is
the max z of the BUILT finial mesh (never a formula).  Callers publish it (square_cabin -> g.CABIN / g.ROOF).
"""
import math
import zlib

import numpy as np

from ..core import log
from ..geom import Acc, finalize, lathe_rz, prof_rect, sweep
from ..shingles import SHINGLE_VARIANTS, SIZE_TABLE, shingle_mesh

EZ = np.array([0.0, 0.0, 1.0])
PARTS = ("roof_frame", "roof_deck", "shingles", "hips", "lead", "finial")
"""object suffixes: <prefix>_<name>_<part> (name="cabin" gives square_cabin's round-3 object names)."""


def _unit(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


class PyramidSurface:
    """the roof surface of a regular `sides`-gon pyramid (see the module doc).  Profile tables are sampled along the
    plan distance d in from the eave lip (extended `ext` m beyond the lip at the lip pitch)."""

    def __init__(self, p_wall, z_plate, sides=4, rot_deg=-90.0, cx=0.0, cy=0.0, pitch_deg=48.0, eave_out=0.50,
                 bell_deg=0.0, bell_len=0.70, kick=0.0, kick_len=0.60, sag=0.0, t_deck=0.025, ext=0.5, n=4001):
        self.n = int(sides)
        if self.n < 3:
            raise ValueError(f"pyramid_roof: sides={sides} (a pyramid needs >= 3; round roofs: tower_roof)")
        self.tanh = math.tan(math.pi / self.n)          # facet half-width per unit apothem
        self.cosh = math.cos(math.pi / self.n)          # apothem / corner radius
        self.c = np.array([float(cx), float(cy), 0.0])
        self.p_wall = float(p_wall)
        self.p_lip = float(p_wall) + float(eave_out)
        self.rot = math.radians(rot_deg)
        self.pitch = math.radians(pitch_deg)
        self.bell = math.radians(bell_deg)
        self.kick, self.kick_len, self.sag, self.t_deck = float(kick), max(float(kick_len), 1e-3), float(sag), t_deck
        self.curved = bool(bell_deg or kick or sag)
        Lb = max(bell_len * math.cos(self.pitch - 0.5 * self.bell), 1e-3)     # plan length of the bell-cast zone
        d = np.linspace(-ext, self.p_lip, n)
        w = np.where(d <= 0.0, 1.0, np.where(d < Lb, 0.5 * (1.0 + np.cos(np.pi * np.clip(d / Lb, 0.0, 1.0))), 0.0))
        ang = self.pitch - self.bell * w
        tz = np.tan(ang)
        dd = np.diff(d)
        z = np.concatenate([[0.0], np.cumsum(0.5 * (tz[1:] + tz[:-1]) * dd)])
        sl = np.sqrt(1.0 + tz ** 2)
        m = np.concatenate([[0.0], np.cumsum(0.5 * (sl[1:] + sl[:-1]) * dd)])
        P = self.p_lip - d                                                    # decreasing along d
        self.Pi, self.Ai = P[::-1].copy(), ang[::-1].copy()
        z = z[::-1]
        self.Zi = z - np.interp(self.p_wall, self.Pi, z) + float(z_plate)    # underside over the wall line = plate
        m = m - np.interp(self.p_lip, P[::-1], m[::-1])                      # slope distance from the lip (0 there)
        self.Md, self.Pd = m, P                                               # m increasing, p decreasing
        self.Mi = m[::-1].copy()

    # ---- profile -------------------------------------------------------------------------------------------------
    def zu(self, p):
        return np.interp(p, self.Pi, self.Zi)

    def ang(self, p):
        return np.interp(p, self.Pi, self.Ai)

    def m_of_p(self, p):
        return np.interp(p, self.Pi, self.Mi)

    def p_of_m(self, m):
        return np.interp(m, self.Md, self.Pd)

    def frame(self, k):
        phi = self.rot + 2.0 * math.pi * (k % self.n) / self.n
        n = np.array([math.cos(phi), math.sin(phi), 0.0])
        return np.array([-n[1], n[0], 0.0]), n

    # ---- surface (facet k, u along the facet toward facet k+1's hip, p apothem) ------------------------------------
    def under(self, k, u, p):
        t, n = self.frame(k)
        u, p = np.broadcast_arrays(np.asarray(u, float), np.asarray(p, float))
        z = self.zu(p)
        if self.kick or self.sag:
            xr = np.clip(np.abs(u) / np.maximum(p * self.tanh, 1e-3), 0.0, 1.0)
            d = self.p_lip - p
            z = z + self.kick * xr ** 3 * np.clip(1.0 - d / self.kick_len, 0.0, 1.0) ** 2
            z = z - self.sag * (1.0 - xr ** 2) * np.sin(np.pi * np.clip(d / self.p_lip, 0.0, 1.0))
        return self.c + u[..., None] * t + p[..., None] * n + z[..., None] * EZ

    def top(self, k, u, p):
        p = np.asarray(p, float)
        return self.under(k, u, p) + (self.t_deck / np.cos(self.ang(p)))[..., None] * EZ

    def normal(self, k, u, p, e=1e-3):
        u = np.asarray(u, float)
        p = np.asarray(p, float)
        S0 = self.top(k, u, p)
        N = np.cross(self.top(k, u + e, p) - S0, self.top(k, u, p - e) - S0)
        return _unit(N)

    def apothem(self, V):
        """apothem (max over the facets of the outward plan offset) of points V (N, 3)."""
        V = np.asarray(V, float) - self.c
        return np.max(np.stack([V @ self.frame(k)[1] for k in range(self.n)], -1), -1)


def _slab(acc, B, N, th, mat, th1=None):
    """a closed slab from 4 bottom corners B (in order) offset by th along N (th1 at corners 2, 3: a wedge)."""
    B = np.asarray(B, float)
    th1 = th if th1 is None else th1
    V = np.concatenate([B, B + N * np.array([th, th, th1, th1])[:, None]])
    F = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    c = V.mean(0)
    for i, f in enumerate(F):
        p = V[f]
        if np.dot(np.cross(p[1] - p[0], p[3] - p[0]), p.mean(0) - c) < 0:
            F[i] = f[::-1]
    acc.add(V, F, mat)


def _sweep_add(acc, path, ups, prof, mat):
    V, F = sweep(path, ups, prof)
    acc.add(V, F, mat)


def pyramid_roof(g, p_wall, z_plate, name="pyramid", sides=4, rot_deg=-90.0, cx=0.0, cy=0.0, pitch_deg=48.0,
                 eave_out=0.50, bell_deg=0.0, bell_len=0.70, kick=0.0, kick_len=0.60, sag=0.0, exposure=0.34,
                 cap_r=0.62, finial_scale=0.80, finial_lean=0.5, rafter_step=0.60, t_deck=0.025, seed=None,
                 rng=None):
    """KIT COMPONENT: bell-cast polygonal pyramid shingle roof (module doc).
    p_wall: apothem of the wall's outer face (the deck underside passes over z_plate there); z_plate: top of the
    wall plate; sides / rot_deg / cx, cy: plan polygon (facet 0's normal at rot_deg); pitch_deg: main pitch;
    eave_out: plan overhang beyond p_wall; bell_deg / bell_len: flattening at the eave and its slope length (0 =
    straight pyramid); kick / kick_len: upturn of the hip corners at the eave; sag: dish between the hips;
    exposure: shingle course exposure; cap_r: corner radius of the lead apex cap; finial_scale: turned finial scale
    (1.45 m x scale above the cap); rafter_step: rafter tail spacing; rng: a numpy Generator to continue (else one is
    seeded from `seed`)."""
    from .finial import turned_finial
    if rng is None:
        s0 = 0 if seed in (None, "") else zlib.crc32(str(seed).encode("utf8")) % 100000
        rng = np.random.default_rng(5151 + s0)
    S = PyramidSurface(p_wall, z_plate, sides=sides, rot_deg=rot_deg, cx=cx, cy=cy, pitch_deg=pitch_deg,
                       eave_out=eave_out, bell_deg=bell_deg, bell_len=bell_len, kick=kick, kick_len=kick_len, sag=sag,
                       t_deck=t_deck)
    nS, tanh, cosh = S.n, S.tanh, S.cosh
    pre = f"{g.prefix}_{name}_"
    A = {k: Acc(pre + k) for k in PARTS}
    a, do = S.p_lip, S.p_wall
    Ls = float(S.m_of_p(0.0))                               # slope length lip -> apex (facet centre line)
    sh = SIZE_TABLE["shingle"]
    Lsh = exposure + 0.18
    Lb = 0.048
    cap_face = cap_r * cosh
    n_sh = 0
    cover = []
    rows = np.linspace(0, 1, 10)
    if S.curved:                                            # denser deck rows through the bell / kick zone
        reach = min(0.7, 1.6 * max(bell_len, kick_len if kick else 0.0) / a)
        rows = np.unique(np.round(np.concatenate([rows, np.linspace(0, reach, 10)]), 5))
    n_path = 8 if S.curved else 2
    for k in range(nS):
        t, n = S.frame(k)
        # ---- deck: top, soffit, eave edge ----
        ss = np.linspace(0, 1, 9)
        pp = a * (1 - rows)
        PP = np.broadcast_to(pp[None, :], (len(ss), len(pp)))
        Q = S.under(k, (2 * ss[:, None] - 1) * PP * tanh, PP)
        dzq = (S.t_deck / np.cos(S.ang(PP)))[..., None] * EZ
        nu, nv = Q.shape[:2]
        i2, j2 = np.meshgrid(np.arange(nu - 1), np.arange(nv - 1), indexing="ij")
        Fq = np.stack([i2 * nv + j2, (i2 + 1) * nv + j2, (i2 + 1) * nv + j2 + 1, i2 * nv + j2 + 1], -1).reshape(-1, 4)
        top = (Q + dzq).reshape(-1, 3)
        Nc = S.normal(k, 0.0, 0.5 * a)
        f_up = Fq if np.dot(np.cross(top[Fq[0][1]] - top[Fq[0][0]], top[Fq[0][3]] - top[Fq[0][0]]), Nc) > 0 \
            else Fq[:, ::-1]
        A["roof_deck"].add(top, f_up, "M_timber_weathered")
        A["roof_deck"].add(Q.reshape(-1, 3), f_up[:, ::-1], "M_timber_weathered")
        edge = np.concatenate([Q[:, 0], Q[:, 0] + dzq[:, 0]])
        m = len(Q[:, 0])
        Fe = np.stack([np.arange(m - 1), np.arange(1, m), np.arange(1, m) + m, np.arange(m - 1) + m], -1)
        if np.dot(np.cross(edge[Fe[0][1]] - edge[Fe[0][0]], edge[Fe[0][3]] - edge[Fe[0][0]]), n) < 0:
            Fe = Fe[:, ::-1]
        A["roof_deck"].add(edge, Fe, "M_timber_weathered")
        # ---- rafter tails (bearing on the plate, carrying the soffit), swept along the true surface ----
        hw = do * tanh
        for u in np.arange(-hw + 0.35, hw - 0.30, rafter_step):
            ps = np.linspace(do - 0.12, a - 0.03, n_path)
            us = np.full_like(ps, u)
            Ns = S.normal(k, us, ps)
            _sweep_add(A["roof_frame"], S.under(k, us, ps) - Ns * 0.07, Ns, prof_rect(0.10, 0.14, 0.012), "M_timber")
        # ---- hip rafter at the + end hip ----
        ph = np.linspace(do - 0.10, a - 0.04, n_path)
        Ch = S.under(k, ph * tanh, ph) - (0.10 / np.cos(S.ang(ph)))[:, None] * EZ
        _sweep_add(A["roof_frame"], Ch, EZ, prof_rect(0.12, 0.17, 0.012), "M_timber")
        # ---- starter board under the first course ----
        v0, v1 = -0.02, 0.26
        p0_, p1_ = float(S.p_of_m(v0)), float(S.p_of_m(v1))
        Nst = S.normal(k, 0.0, float(S.p_of_m(0.5 * (v0 + v1))))
        _slab(A["shingles"], [S.top(k, -p0_ * tanh + 0.01, p0_), S.top(k, p0_ * tanh - 0.01, p0_),
                              S.top(k, p1_ * tanh - 0.01, p1_), S.top(k, -p1_ * tanh + 0.01, p1_)], Nst, 0.046,
              "M_roof_shingle", th1=0.018)
        # ---- coursed shingles bent onto the surface, trimmed at the hips ----
        i = 0
        while True:
            vb = -0.03 + i * exposure
            pb = float(S.p_of_m(vb))
            if pb < cap_face - 0.05 or vb > Ls:
                break
            L_ = min(Lsh, Ls - vb - 0.05)
            if L_ < 0.12:
                break
            w0 = pb * tanh
            u = -w0 - rng.uniform(0.0, 0.2)
            while u < w0 - 0.04:
                W = float(np.clip(sh["target_w"] * rng.uniform(*sh["w_jitter"]), *sh["width"]))
                gap = rng.uniform(*sh["gap"])
                uc = u + W / 2
                if uc + W / 2 > w0 - 0.05 and w0 - 0.05 - u > 0.12:
                    W = w0 - 0.05 - u + 0.04
                    uc = u + W / 2
                var = SHINGLE_VARIANTS[int(rng.integers(0, len(SHINGLE_VARIANTS)))]
                Vs, Fs, uv = shingle_mesh(W, L_, var, bottom=False, head=False)
                y = Vs[:, 1]
                pv = S.p_of_m(vb + y)
                lim = pv * tanh - 0.012                                    # trim at the hips
                x = np.clip(Vs[:, 0] + uc, -lim, lim)
                lift = Lb * (1 - np.clip(y, 0, None) / Lsh) + 0.002
                Wp = S.top(k, x, pv) + (Vs[:, 2] + lift)[:, None] * S.normal(k, x, pv)
                if np.ptp(x) > 0.05:
                    A["shingles"].add(Wp, Fs, "M_roof_shingle", uv=uv, wear=rng.uniform(0.2, 0.6))
                    n_sh += 1
                    near = np.hypot(Wp[:, 0] - S.c[0], Wp[:, 1] - S.c[1]) < cap_r + 0.1
                    if near.any():
                        cover.append(Wp[near])
                u += W + gap
            i += 1
    # ---------------- hips: one closed saddle per hip, swept along the (concave) hip line ----------------
    lift, th_b, w_b = 0.085, 0.036, 0.13
    hp = np.linspace(a + 0.03, 0.6 * cap_r * cosh, 26 if S.curved else 8)
    for k in range(nS):
        k2 = (k + 1) % nS
        uh = hp * tanh
        H = S.top(k, uh, hp)
        NA = S.normal(k, uh * 0.997, hp)
        NB = S.normal(k2, -uh * 0.997, hp)
        T = np.zeros_like(H)
        T[1:-1] = H[2:] - H[:-2]
        T[0], T[-1] = H[1] - H[0], H[-1] - H[-2]
        T = _unit(T)
        Ub = NA + NB
        U = _unit(Ub - (Ub * T).sum(1, keepdims=True) * T)
        R = np.cross(U, T)
        prof = []
        for j in range(len(hp)):
            sides_ = []
            for tv, sgn, Nx in ((S.frame(k)[0], -1.0, NA[j]), (S.frame(k2)[0], 1.0, NB[j])):
                dX = sgn * tv
                dX = dX - np.dot(dX, T[j]) * T[j]
                dX = _unit(dX - np.dot(dX, Nx) * Nx)
                fb, ft = dX * w_b + Nx * lift, dX * w_b + Nx * (lift + th_b)
                sides_.append(((fb @ R[j], fb @ U[j]), (ft @ R[j], ft @ U[j])))
            cA = max(float(np.dot(NA[j], U[j])), 0.3)
            rb, rt = (0.0, lift / cA), (0.0, (lift + th_b) / cA)
            right, left = (sides_[0], sides_[1]) if sides_[0][0][0] > sides_[1][0][0] else (sides_[1], sides_[0])
            prof.append([right[0], right[1], rt, left[1], left[0], rb])
        _sweep_add(A["hips"], H, U, np.array(prof), "M_timber_weathered")
    # ---------------- lead apex cap, sleeve and finial ----------------
    apex_top = float(S.top(0, 0.0, 0.0)[2])
    zc = apex_top + 0.17
    rc = cap_r                                                             # corner radius of the polygonal cap
    tp = math.tan(S.pitch)
    drop = rc * cosh * tp                                                  # the pyramid falls this much to the cap edge
    prof = [(rc + 0.03, -drop - 0.06), (rc + 0.035, -drop - 0.035), (rc, -drop), (0.06, -0.06 * tp * cosh),
            (0.0, 0.0)]
    Vl, Fl = lathe_rz(prof, nS, cx=S.c[0], cy=S.c[1], z0=zc, cap_bottom=True, cap_top=False,
                      phase=S.rot + math.pi / nS)
    cover += [np.asarray(v_, float) for v_ in A["hips"].V]
    if cover:
        cv = np.concatenate(cover)
        ap = S.apothem(cv)
        m_ = ap < rc * cosh + 0.01
        for _ in range(40):                    # lift the cap until every covered vertex inside it is 2 cm under the lead
            zl = np.interp(ap / cosh, [0.0, rc], [zc, zc - drop])
            need = float((cv[m_, 2] + 0.02 - zl[m_]).max(initial=-1.0))
            if need <= 0:
                break
            zc += need
            Vl[:, 2] += need
    A["lead"].add(Vl, Fl, "M_lead")
    rs_ = 0.07 * finial_scale                  # round lead sleeve dressing the finial's foot into the pointed cap
    Vs_, Fs_ = lathe_rz([(rs_, -(rs_ * tp + 0.04)), (rs_, 0.02), (0.0, 0.02)], 20, cx=S.c[0], cy=S.c[1], z0=zc,
                        cap_bottom=True, cap_top=False)
    A["lead"].add(Vs_, Fs_, "M_lead")
    turned_finial(A["finial"], (S.c[0], S.c[1], zc - 0.02), scale=finial_scale, lean_deg=finial_lean)
    tip = float(np.concatenate(A["finial"].V)[:, 2].max())                 # the BUILT finial's tip
    built = {}
    for k_, acc in A.items():
        ob = finalize(acc, g.coll, smooth_deg=35.0, recalc=k_ not in ("shingles", "roof_deck"))
        if ob is not None:
            built[k_] = ob
    z_eave = float(S.zu(a))
    z_corner = float(S.under(0, a * tanh, a)[2])
    log("pyramid roof %s: %d sides, wall p %.2f plate %.2f, pitch %.0f bell %.0f/%.2f kick %.3f sag %.3f, eave p %.2f "
        "z %.2f (corner %.2f), apex %.2f, cap %.2f, finial x%.2f tip %.2f (%.2f above the cap), %d shingles"
        % (name, nS, do, z_plate, pitch_deg, bell_deg, bell_len, kick, sag, a, z_eave, z_corner, apex_top, zc,
           finial_scale, tip, tip - zc, n_sh))
    return dict(objs=built, surface=S, sides=nS, p_wall=do, z_plate=float(z_plate), r_eave=a, z_eave=z_eave,
                z_eave_corner=z_corner, apex=apex_top, cap_top=zc, collar_drip=zc - drop, tip=tip, pitch=pitch_deg,
                bell_deg=bell_deg, n_shingles=n_sh)
