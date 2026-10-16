"""components.drum_wall -- the stone drum of a tower: coursed rubble with a balustrade band, a blind arcade and a
corbelled cornice (kit 1.2.0, from the signed-off tower windmill).

Public components (frame g = components.drum_frame.DrumFrame):
    round_stone_drum(g, r_base, r_top, height, zones, door, arcade, windows, seed)
    blind_arcade(g, n, clear_w, clear_h, z_sill, az0, seed)
The rubble is laid by coursing() in wall coordinates (u along the wall, z up) and mapped onto the battered drum;
every wall is rasterised (Wall) so voids get pinning stones, joints a concave mortar strike, and the mortar skin
behind full stone cover is not modelled (producer note 6).  Stones come from village_kit.split_stones.
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_band import (baluster_row, dentil_corbels)  # noqa: F401
from .drum_door import (arched_door)  # noqa: F401
from .drum_frame import (relief_door, relief_far, relief_min, FOOT_PIN_Z, MORTAR_RECESS, R_out, arcade_params, arch_set, cyl_place, door_params,
    drum_mortar_d, drum_to_wall, drum_to_world, free_fn_drum, free_on_circle, inside_clear, kpart, open_place,
    wall_relief)  # noqa: F401
from ..split_stones import (STYLE, conchoidal, stone_local)  # noqa: F401
from ..tmplmesh import (D2R, EYE_SOFFIT, PI, RING2, T_PIN, T_PIN_NB, T_RUB3, T_RUB3_HI, T_RUB3_HI_NB, T_RUB3_NB,
    T_RUB3_XHI, T_RUB3_XHI_NB, add_caps, add_grid, chamfer_dt, hull2d, log, noise_field, orient, perm_tmpl,
    profile_block, rbox, rotm, smoothstep, tmpl_rings, xform)  # noqa: F401


EYE_XHI = 2.6


EYE_HI = 4.3                 # the whole drum is the hero surface (every view): dense faces up to the cornice


def wall_stone_tmpl(zc, H, base_T):
    """Per-stone template: open back always; no soffit below eye height; denser face in the eye-level zone."""
    if base_T is not T_RUB3:
        return [base_T] * len(zc)
    out = []
    for z, hh in zip(zc, H):
        low = z - hh / 2 + 0.01 < EYE_SOFFIT
        hi = z < EYE_HI
        if z < EYE_XHI:
            out.append(T_RUB3_XHI_NB if low else T_RUB3_XHI)
        else:
            out.append((T_RUB3_HI_NB if low else T_RUB3_HI) if hi else (T_RUB3_NB if low else T_RUB3))
    return out


def stones_by_tmpl(rng, L, H, D, style, tmpls, min_relief=0.0, roll=0.8):
    """stone_local for groups of stones sharing a template. Returns list of (index array, P, T).
    min_relief: scalar or per stone (producer note 11)."""
    mr = np.broadcast_to(np.asarray(min_relief, float), (len(L),))
    groups = []
    ids = {}
    for i, T in enumerate(tmpls):
        ids.setdefault(id(T), (T, []))[1].append(i)
    for key in sorted(ids, key=lambda k: ids[k][1][0]):
        T, ix = ids[key]
        ix = np.array(ix)
        P, _ = stone_local(rng, L[ix], H[ix], D[ix], style, T=T, min_relief=mr[ix], rot_deg=(2.0, roll, 1.1))
        groups.append((ix, P, T))
    return groups


def coursing(rng, z0, z1, free_fn, hr=(0.10, 0.16), hbig=0.24, p_big=0.12, lr=(0.22, 0.62), joint=(0.006, 0.013),
             wob=0.018, p_tall=0.05, p_pin=0.12, fix_ends=True, Dr=(0.18, 0.30), lmin=0.12, wob_cap=0.28, wob2=0.0,
             pinch=0.0, pinch_w=(0.45, 1.0), h_min=0.0, p_long=0.15):
    """Generic coursed walling in (u, z). free_fn(zb, zt) -> list of (ua, ub) free spans.
    Returns dict of arrays uc, zc, L, H, D for each stone, plus sb / st: the slopes du/dz of its bottom and top bed
    at its centre (emit_drum_stones shears each stone to follow them).

    Ensemble review (kit 1.2.0) -- rough rubble rather than near-ashlar:
      wob, wob_cap, wob2  bed lines wander (a low sine of up to wob, capped at wob_cap x the adjacent course height,
                          plus a second shorter wave of amplitude wob2): courses visibly undulate +-2-4 cm
      pinch               chance per course of a PINCH-OUT: over a 0.9-2 m window the course thins to nothing (its
                          top bed sinks onto its bottom bed); the course above thickens to fill and stones thinner
                          than h_min are not laid
      p_tall, p_long      through-stones spanning two courses; long stones up to 1.45 x lr[1]
    Defaults reproduce the phase-1 layout (no pinch, no second wave)."""
    zs = [z0]
    while zs[-1] < z1 - 1e-6:
        zs.append(zs[-1] + (rng.uniform(*hr) if rng.random() > p_big else rng.uniform(hr[1], hbig)))
    zs = np.array(zs)
    if len(zs) > 2 and (zs[-1] - z1) > 0.5 * (zs[-1] - zs[-2]):
        zs = zs[:-1]
    zs = z0 + (zs - z0) * (z1 - z0) / (zs[-1] - z0)
    nb = len(zs)
    ch = np.diff(zs)
    wa = np.zeros(nb)
    for k in range(1, nb - 1):
        wa[k] = rng.uniform(0.3, 1.0) * min(wob, wob_cap * min(ch[k - 1], ch[k]))
    if not fix_ends:
        wa[0] = wa[-1] = 0
    wf = rng.uniform(0.25, 0.9, nb)
    wp = rng.uniform(0, 2 * PI, nb)
    if wob2 > 0:
        wa2 = np.array([0.0] + [rng.uniform(0.3, 1.0) * min(wob2, 0.15 * min(ch[k - 1], ch[k]))
                                for k in range(1, nb - 1)] + [0.0])
        wf2 = rng.uniform(1.8, 4.0, nb)
        wp2 = rng.uniform(0, 2 * PI, nb)
    else:
        wa2 = np.zeros(nb)
        wf2 = wp2 = np.zeros(nb)
    pinches = {k: [] for k in range(nb)}          # bed line -> [(u centre, half width, depth)]

    def B(k, u):
        z = zs[k] + wa[k] * np.sin(u * wf[k] + wp[k]) + wa2[k] * np.sin(u * wf2[k] + wp2[k])
        for (uc_, hw_, dp_) in pinches[k]:
            x_ = np.clip(np.abs(u - uc_) / hw_, 0, 1)
            z = z - dp_ * (0.5 + 0.5 * np.cos(PI * x_))
        return z

    def dB(k, u):
        return (B(k, u + 0.01) - B(k, u - 0.01)) / 0.02

    out = {k: [] for k in ("uc", "zc", "L", "H", "D", "sb", "st")}
    carry = []  # spans blocked by tall stones for the next course
    n_pinch = 0
    for k in range(nb - 1):
        spans = free_fn(zs[k], zs[k + 1])
        new_carry = []
        # subtract carried tall-stone spans
        sp2 = []
        for a, b in spans:
            cuts = sorted([c for c in carry if c[1] > a and c[0] < b])
            cur = a
            for ca, cb in cuts:
                if ca > cur:
                    sp2.append((cur, ca))
                cur = max(cur, cb)
            if b > cur:
                sp2.append((cur, b))
        if pinch > 0 and 0 < k < nb - 2 and sp2 and rng.random() < pinch:
            a_, b_ = max(sp2, key=lambda ab: ab[1] - ab[0])
            hw_ = rng.uniform(*pinch_w)
            if b_ - a_ > 2.2 * hw_:
                u_c = rng.uniform(a_ + hw_, b_ - hw_)
                pinches[k + 1].append((u_c, hw_, (zs[k + 1] - zs[k]) * rng.uniform(0.92, 1.0)))
                n_pinch += 1
        for a, b in sp2:
            S = b - a
            if S < 0.06:
                continue
            Ls, Js = [], []
            tot = 0.0
            while tot < S:
                Lr = rng.uniform(*lr) if rng.random() > p_long else rng.uniform(lr[1], lr[1] * 1.45)
                j = rng.uniform(*joint)
                Ls.append(Lr)
                Js.append(j)
                tot += Lr + j
            if len(Ls) > 1 and tot - S > 0.5 * Ls[-1]:
                tot -= Ls[-1] + Js[-1]
                Ls.pop()
                Js.pop()
            f = S / tot
            pos = a
            for Lr, j in zip(Ls, Js):
                Lr *= f
                j *= f
                uc = pos + j / 2 + Lr / 2
                pos += Lr + j
                tall = (rng.random() < p_tall) and (k + 2 < nb) and Lr < 0.7
                kt = k + 2 if tall else k + 1
                zb, zt = B(k, uc), B(kt, uc)
                jv = rng.uniform(*joint)
                Hs = (zt - zb) - jv - rng.uniform(0, 0.003)
                zc = (zb + zt) / 2 + rng.uniform(-0.004, 0.004)
                Ds = rng.uniform(*Dr)
                sb, st = dB(k, uc), dB(kt, uc)
                if Hs < h_min:
                    continue                    # pinched out: the course above fills the space
                if tall:
                    new_carry.append((uc - Lr / 2 - j / 2, uc + Lr / 2 + j / 2))
                if (not tall) and rng.random() < p_pin and Hs > 0.13 and Lr > 0.25:
                    # main stone + small pinning stones in a strip above or below
                    frac = rng.uniform(0.62, 0.75)
                    top = rng.random() < 0.5
                    Hm = Hs * frac
                    Hp = max(Hs - Hm - jv * 0.6, 0.03)
                    Hm = Hs - Hp - jv * 0.6
                    zm = zc - Hs / 2 + Hm / 2 if not top else zc + Hs / 2 - Hm / 2
                    zp = zc + Hs / 2 - Hp / 2 if not top else zc - Hs / 2 + Hp / 2
                    for kk, v in zip(("uc", "zc", "L", "H", "D", "sb", "st"), (uc, zm, Lr, Hm, Ds, sb, st)):
                        out[kk].append(v)
                    # 1-2 pinning stones of different sizes, never a row of equal chips (director r5 #2)
                    npin = 1 if Lr < 0.5 else 1 + int(rng.random() < 0.6)
                    seg = Lr / npin
                    for q in range(npin):
                        lp = seg * rng.uniform(0.45, 0.9)
                        up = uc - Lr / 2 + seg * (q + 0.5) + rng.uniform(-0.04, 0.04)
                        Hq = Hp * rng.uniform(0.6, 1.0)
                        zq = zp + rng.uniform(-0.3, 0.3) * (Hp - Hq)
                        for kk, v in zip(("uc", "zc", "L", "H", "D", "sb", "st"), (up, zq, lp, Hq, Ds * 0.7, st, st)):
                            out[kk].append(v)
                    continue
                for kk, v in zip(("uc", "zc", "L", "H", "D", "sb", "st"), (uc, zc, Lr, Hs, Ds, sb, st)):
                    out[kk].append(v)
        carry = new_carry
    res = {k: np.array(v) for k, v in out.items()}
    res["n_pinch"] = n_pinch
    return res


def follow_beds(P, S, ix, k=1.0):
    """shear / taper local stones (x along the wall, z up) so their bottom and top follow the wandering bed lines
    (slopes S['sb'] / S['st'] at each centre): a stone in a sloping or pinching course becomes a wedge."""
    if "sb" not in S or k == 0:
        return P
    sb = np.clip(S["sb"][ix], -0.45, 0.45)[:, None] * k
    st = np.clip(S["st"][ix], -0.45, 0.45)[:, None] * k
    H = np.maximum(S["H"][ix], 0.02)[:, None]
    x, z = P[:, :, 0], P[:, :, 2]
    P = P.copy()
    P[:, :, 2] = z * (1 + (st - sb) * x / H) + 0.5 * (sb + st) * x
    return P


_TPB = {}


def wall_cut_prof(prof, depth=0.012):
    """Profile (y outward, z) cut 1.2 cm behind the wall face: vertices are inserted where the outline crosses
    the wall plane (y = 0) so the faces inside the wall can be dropped."""
    out = []
    n = len(prof)
    for j in range(n):
        a, b = np.asarray(prof[j], float), np.asarray(prof[(j + 1) % n], float)
        out.append((max(a[0], -depth), a[1]))
        if (a[0] < 0) != (b[0] < 0) and abs(b[0] - a[0]) > 1e-9:
            t = -a[0] / (b[0] - a[0])
            out.append((0.0, a[1] + t * (b[1] - a[1])))
    return out


def profile_course(g, part, mat, rng, z0, prof, seg=(0.6, 0.95), skip=(), Rfun=None, joint=0.01, jit=0.004, top_back=0.0):
    """Ring course of dressed profile blocks around the drum (cyl mapped). skip: list of (th_c, half_arc_m).
    Faces inside the wall (behind y = 0) are not modelled, except (top_back > 0) the top bed, which runs
    `top_back` m back into the wall core so no slot opens between the course and the walling above."""
    Rfun = partial(R_out, g) if Rfun is None else Rfun
    prof = wall_cut_prof(prof, depth=max(0.012, top_back))
    ztop_p = max(p_[1] for p_ in prof)
    inwall = np.array([p_[0] <= 0.0005 and not (top_back > 0 and p_[1] >= ztop_p - 1e-6) for p_ in prof])
    Rm = float(Rfun(z0))
    C = 2 * PI * Rm
    if skip:
        spans = free_on_circle(Rm, [(t * Rm, hw) for t, hw in skip])
    else:
        u0 = rng.uniform(0, C)
        spans = [(u0, u0 + C)]
    for a, b in spans:
        S = b - a
        n = max(1, int(round(S / rng.uniform(*seg))))
        cuts = np.sort(np.concatenate([[0, S], rng.uniform(0.15, 0.85, n - 1) * 0 + (np.arange(1, n) + rng.uniform(-0.25, 0.25, n - 1)) * S / n]))
        for i in range(n):
            L = cuts[i + 1] - cuts[i] - joint
            uc = a + (cuts[i] + cuts[i + 1]) / 2
            nseg = max(3, int(L / 0.1))
            P, nr = profile_block(prof, L, nseg)
            key = (nr, len(prof), tuple(inwall))
            if key not in _TPB:
                T = tmpl_rings(nr, len(prof), cap0=True, cap1=True)
                T = dict(orient(T, add_caps(P[None], T)[0]))
                m_ = len(prof)
                jq = np.arange(len(T["quads"])) % m_
                keep_q = ~(inwall[jq] & inwall[(jq + 1) % m_])
                T["quads"], T["qflat"] = T["quads"][keep_q], T["qflat"][keep_q]
                _TPB[key] = T
            T = _TPB[key]
            P = add_caps(P[None], T)
            # tiny irregularity: settle / roll / out-of-line
            P[:, :, 2] += rng.uniform(-jit, jit) + P[:, :, 0] * rng.uniform(-0.006, 0.006)
            P[:, :, 1] += rng.uniform(-jit, jit)
            W = cyl_place(g, P, np.array([uc / Rm]), np.array([z0]), np.array([0.0]), Rfun)
            part.add(W, T, Pl=P, mat=mat, smooth="bevel")


class Wall:
    registry = []

    def __init__(self, name, to_world, to_wall, mortar_d, u0, u1, z0, z1, blocked, period=None, metric_z=None,
                 cell=0.01, flip=False, registry=None, min_relief=0.0):
        self.name, self.to_world, self.to_wall, self.mortar_d = name, to_world, to_wall, mortar_d
        self.min_relief = min_relief            # producer note 11: skin of the pinning stones
        self.u0, self.z0, self.cell, self.period = u0, z0, cell, period
        self.nu = int(math.ceil((u1 - u0) / cell))
        self.nz = int(math.ceil((z1 - z0) / cell))
        uc = u0 + (np.arange(self.nu) + 0.5) * cell
        zc = z0 + (np.arange(self.nz) + 0.5) * cell
        self.U, self.Z = np.meshgrid(uc, zc, indexing="ij")
        self.block = blocked(self.U, self.Z)
        self.cov = np.zeros((self.nu, self.nz), bool)
        self.metric_z = metric_z
        self.stones = []
        self.flip = flip
        if registry is not None:
            registry.append(self)

    def tw(self, T):
        return perm_tmpl(T, self.flip)

    def unwrap(self, u, ref):
        if self.period is None:
            return u
        C = self.period
        return ((u - ref + C / 2) % C) - C / 2 + ref

    def add(self, W, T):
        self.stones.append((np.asarray(W), T))
        self.raster(W, T)

    def raster(self, W, T):
        r2, _ = RING2[id(T)]
        R = W[:, r2]
        u, z, d = self.to_wall(R.reshape(-1, 3))
        u = u.reshape(R.shape[:2])
        z = z.reshape(R.shape[:2])
        c = self.cell
        for s in range(len(R)):
            us = self.unwrap(u[s], u[s, 0])
            h = hull2d(np.stack([us, z[s]], 1))
            if len(h) < 3:
                continue
            i0 = int(math.floor((h[:, 0].min() - self.u0) / c))
            i1 = int(math.ceil((h[:, 0].max() - self.u0) / c))
            k0 = max(int(math.floor((h[:, 1].min() - self.z0) / c)), 0)
            k1 = min(int(math.ceil((h[:, 1].max() - self.z0) / c)), self.nz)
            if k1 <= k0 or i1 <= i0:
                continue
            ii = np.arange(i0, i1)
            kk = np.arange(k0, k1)
            pu = self.u0 + (ii + 0.5) * c
            pz = self.z0 + (kk + 0.5) * c
            PU, PZ = np.meshgrid(pu, pz, indexing="ij")
            a = h
            b = np.roll(h, -1, 0)
            cr = (b[:, 0, None, None] - a[:, 0, None, None]) * (PZ[None] - a[:, 1, None, None]) - \
                (b[:, 1, None, None] - a[:, 1, None, None]) * (PU[None] - a[:, 0, None, None])
            ins = (cr >= 0).all(0)
            if self.period is not None:
                iw = ii % self.nu
            else:
                ok = (ii >= 0) & (ii < self.nu)
                ins = ins[ok]
                iw = ii[ok]
            self.cov[iw[:, None], kk[None, :]] |= ins

    def covered_rect(self, ua, ub, za, zb, dil=1):
        """True where the wall rectangle [ua,ub]x[za,zb] is entirely stone-covered (stone outlines dilated by the
        skirt width) or dressed / blocked work."""
        cov = self.cov.copy()
        for _ in range(dil):
            g_ = cov.copy()
            g_[1:] |= cov[:-1]
            g_[:-1] |= cov[1:]
            g_[:, 1:] |= cov[:, :-1]
            g_[:, :-1] |= cov[:, 1:]
            cov = g_
        unc = (~cov).astype(np.int32)       # dressed / blocked work does not count: its joints need the skin
        S = np.zeros((self.nu + 1, self.nz + 1), np.int64)
        S[1:, 1:] = unc.cumsum(0).cumsum(1)
        ua, ub, za, zb = np.broadcast_arrays(ua, ub, za, zb)
        i0 = np.clip(np.floor((ua - self.u0) / self.cell).astype(int), 0, self.nu)
        i1 = np.clip(np.ceil((ub - self.u0) / self.cell).astype(int), 0, self.nu)
        k0 = np.clip(np.floor((za - self.z0) / self.cell).astype(int), 0, self.nz)
        k1 = np.clip(np.ceil((zb - self.z0) / self.cell).astype(int), 0, self.nz)
        cnt = S[i1, k1] - S[i0, k1] - S[i1, k0] + S[i0, k0]
        inside = (i1 > i0) & (k1 > k0)
        return inside & (cnt == 0)

    def mortar_fraction(self, zlo=None, zhi=None):
        m = ~self.block
        if zlo is not None:
            m &= (self.Z >= zlo) & (self.Z <= zhi)
        n = m.sum()
        return float((~self.cov & m).sum()) / max(n, 1), int(n)

    def max_void(self, where=False):
        D = chamfer_dt(self.cov | self.block, self.cell)
        D[:, :5] = 0                     # ignore the raster's ground / top boundary rows
        D[:, -5:] = 0
        # a gap of n free cells has its centre (n+1)/2 cells from the nearest stone cell centre -> width 2D - c
        if where:
            i, k = np.unravel_index(np.argmax(D), D.shape)
            return 2 * float(D.max()) - self.cell, self.U[i, k], self.Z[i, k]
        return 2 * float(D.max()) - self.cell

    def fill_pins(self, part, rng, yo=(0.012, 0.024), erode=0.0055, hw=(7, 6)):
        """Fill every mortar void wider than 3 cm with pinning stones shaped to the void: the free region
        around the widest point (eroded by the joint width, limited to ~15 x 13 cm) is flood-filled, its convex
        hull becomes the pin's outline (a box template mapped radially onto the polygon)."""
        c = self.cell
        npins = 0
        handled = np.zeros_like(self.cov)       # void regions already given a pin (never re-seeded)
        for it in range(14):
            occ = self.cov | self.block
            D = chamfer_dt(occ, c)
            cand = np.argwhere((D > 0.0155) & ~handled)
            if len(cand) == 0:
                break
            order = np.argsort(-D[cand[:, 0], cand[:, 1]], kind="stable")
            supp = np.zeros_like(occ)
            new = []
            seeds = []
            foot = []
            for q in order:
                i, k = cand[q]
                if supp[i, k]:
                    continue
                ii = np.arange(i - hw[0], i + hw[0] + 1)
                if self.period is not None:
                    ii = ii % self.nu
                else:
                    ii = ii[(ii >= 0) & (ii < self.nu)]
                kk = np.arange(max(k - hw[1], 0), min(k + hw[1] + 1, self.nz))
                free = (D[np.ix_(ii, kk)] >= erode) & ~supp[np.ix_(ii, kk)]
                si = int(np.nonzero(ii == i)[0][0])
                sk = int(np.nonzero(kk == k)[0][0])
                comp = np.zeros_like(free)
                comp[si, sk] = True
                for _ in range(40):
                    g_ = comp.copy()
                    g_[1:] |= comp[:-1]
                    g_[:-1] |= comp[1:]
                    g_[:, 1:] |= comp[:, :-1]
                    g_[:, :-1] |= comp[:, 1:]
                    g_ &= free
                    if (g_ == comp).all():
                        break
                    comp = g_
                supp[np.ix_(ii, kk)] |= comp
                supp[i, k] = True
                cells = np.argwhere(comp)
                if len(cells) < 4:
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    continue
                pu = self.u0 + (i + (cells[:, 0] - si) + 0.5) * c
                pz = self.z0 + (kk[cells[:, 1]] + 0.5) * c
                pts = np.stack([pu, pz], 1)
                h = hull2d(pts)
                if len(h) < 3:
                    continue
                ext = np.ptp(h, 0)
                if ext.min() < 0.008 or ext.max() < 0.02:
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    continue
                if self.name == "drum" and pz.mean() < FOOT_PIN_Z:
                    # round 6: footing bed joints take only sparse irregular wedge pinners (below); the rest of
                    # the joint stays open mortar - never a row of chips
                    sub_ = handled[np.ix_(ii, kk)] | comp
                    handled[np.ix_(ii, kk)] = sub_
                    handled[i, k] = True
                    foot.append(h)
                    continue
                new.append(h)
                seeds.append((i, k))
            npins += self.footing_wedges(part, rng, foot)
            if not new:
                if foot:
                    continue
                break
            W_all, P_all = [], []
            for h in new:
                cen = h.mean(0)
                hp = cen + (h - cen) * 0.97
                ext = np.ptp(hp, 0)
                yo_pin = rng.uniform(*yo)
                dep = yo_pin + 0.008
                hh = np.array([[ext[0] / 2, dep / 2, ext[1] / 2]])
                r = np.array([[min(0.006, ext[0] * 0.2), 0.005, min(0.006, ext[1] * 0.2)]])
                P = rbox(T_PIN, hh, r)[0]
                bc = (hp.min(0) + hp.max(0)) / 2
                x, z = P[:, 0], P[:, 2]
                # radial map of the box outline onto the polygon (about the bbox centre)
                cen2 = bc if all(((hp[(j + 1) % len(hp)] - hp[j])[0] * (bc[1] - hp[j][1]) -
                                  (hp[(j + 1) % len(hp)] - hp[j])[1] * (bc[0] - hp[j][0])) >= 0
                                 for j in range(len(hp))) else cen
                vx, vz = x + bc[0] - cen2[0], z + bc[1] - cen2[1]
                ang = np.arctan2(vz, vx)
                dx, dz = np.cos(ang), np.sin(ang)
                # box radius in that direction (about cen2) and polygon radius
                def ray_poly(poly):
                    a = poly - cen2
                    b = np.roll(poly, -1, 0) - cen2
                    e = b - a
                    den = dx[:, None] * e[None, :, 1] - dz[:, None] * e[None, :, 0]
                    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
                    t = (a[None, :, 0] * e[None, :, 1] - a[None, :, 1] * e[None, :, 0]) / den
                    s_ = (a[None, :, 0] * dz[:, None] - a[None, :, 1] * dx[:, None]) / den
                    t = np.where((s_ >= -1e-9) & (s_ <= 1 + 1e-9) & (t > 0), t, np.inf)
                    return t.min(1)
                box = np.array([[-hh[0, 0], -hh[0, 2]], [hh[0, 0], -hh[0, 2]], [hh[0, 0], hh[0, 2]],
                                [-hh[0, 0], hh[0, 2]]]) + bc
                Rb = ray_poly(box)
                Rp = ray_poly(hp)
                f = np.where(np.isfinite(Rb) & np.isfinite(Rp), Rp / np.maximum(Rb, 1e-6), 1.0)
                nu_ = cen2[0] + vx * f
                nz_ = cen2[1] + vz * f
                u_ = np.stack([P[:, 0] / hh[0, 0], P[:, 1] / hh[0, 1], P[:, 2] / hh[0, 2]], 1)[None]
                y = P[:, 1] - hh[0, 1] + 0.003 * noise_field(u_ * 1.5, rng, fmin=1.5, fmax=3.0)[0] * \
                    np.clip(u_[0, :, 1], 0, 1)
                d = self.mortar_d(np.array([cen2[0]]), np.array([cen2[1]]))[0] + yo_pin
                W_all.append(self.to_world(nu_, nz_, d + y))
                P_all.append(np.stack([nu_ - cen2[0], y, nz_ - cen2[1]], 1))
            W = np.array(W_all)
            lowp = np.array([float(h_[:, 1].min()) + 0.01 < EYE_SOFFIT for h_ in new]) & (self.name != "arch")
            for sel_, Tq in ((lowp, T_PIN_NB), (~lowp, T_PIN)):
                if sel_.any():
                    part.add(W[sel_], self.tw(Tq), Pl=np.array(P_all)[sel_], mat="M_stone", smooth="all")
                    self.add(W[sel_], self.tw(Tq))
            npins += len(W)
            fb = []
            occ2 = self.cov | self.block
            for (i, k) in seeds:            # a pin that did not cover its own seed is never re-seeded there
                if self.z0 + (k + 0.5) * c < FOOT_PIN_Z and self.name == "drum":
                    continue
                if not self.cov[i, k]:
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    # fallback: a small squared pin centred in the free row / column runs through the seed
                    row, col = occ2[:, k], occ2[i, :]
                    il = i
                    while il > 0 and not row[il - 1] and i - il < 6:
                        il -= 1
                    ir = i
                    while ir < self.nu - 1 and not row[ir + 1] and ir - i < 6:
                        ir += 1
                    kl = k
                    while kl > 0 and not col[kl - 1] and k - kl < 5:
                        kl -= 1
                    kr = k
                    while kr < self.nz - 1 and not col[kr + 1] and kr - k < 5:
                        kr += 1
                    Lu = (ir - il + 1) * c - 0.012
                    Lz = (kr - kl + 1) * c - 0.012
                    if min(Lu, Lz) >= 0.018:
                        fb.append((self.u0 + (il + ir + 1) / 2 * c, self.z0 + (kl + kr + 1) / 2 * c,
                                   min(Lu, 0.07), min(Lz, 0.06)))
            if fb:
                fb = np.array(fb)
                Nf = len(fb)
                yq = rng.uniform(*yo, Nf)
                Pq, Tq = stone_local(rng, fb[:, 2], fb[:, 3], yq + 0.008, "pin", rot_deg=(1, 1, 3),
                                     min_relief=self.min_relief)
                yo_ = self.mortar_d(fb[:, 0], fb[:, 1]) + yq
                Wq = self.to_world(fb[:, 0, None] + Pq[:, :, 0], fb[:, 1, None] + Pq[:, :, 2],
                                   yo_[:, None] + Pq[:, :, 1])
                part.add(Wq, self.tw(Tq), Pl=Pq, mat="M_stone", smooth="all")
                self.add(Wq, self.tw(Tq))
                npins += Nf
            self.iters = getattr(self, "iters", []) + [len(W)]
        self.rejected = 0
        return npins

    def footing_wedges(self, part, rng, voids):
        """Round 6 (director r5 #2): 0-2 irregular wedge pinning stones per footing bed joint, 3-8 cm long,
        rotated +-20 deg, every one a different size and shape, never more than 2 in a row along a joint."""
        if not voids:
            return 0
        acc = getattr(self, "_foot_acc", [])
        n = 0
        for h in voids:
            cen = h.mean(0)
            ext = np.ptp(h, 0)
            if ext[1] < 0.012 or ext[0] < 0.03:
                continue
            near = [a for a in acc if abs(self.unwrap(np.array([a[0]]), cen[0])[0] - cen[0]) < 0.55 and abs(a[1] - cen[1]) < 0.05]
            close = [a for a in near if abs(self.unwrap(np.array([a[0]]), cen[0])[0] - cen[0]) < 0.16]
            if len(near) >= 2 or close or rng.random() < 0.35:
                continue
            L = float(np.clip(ext[0] * rng.uniform(0.55, 0.9), 0.03, 0.08))
            Hh = float(np.clip(ext[1] * rng.uniform(0.75, 1.05), 0.012, 0.045))
            yq = rng.uniform(0.010, 0.022)
            P, T = stone_local(rng, [L], [Hh], [yq + 0.012], "pin", rot_deg=(1.5, 1.5, 0.0), min_relief=self.min_relief)
            x, z = P[0, :, 0].copy(), P[0, :, 2].copy()
            # wedge: one end 35-60 % thinner, the thin edge slightly skewed
            tw = rng.uniform(0.35, 0.6) * rng.choice([-1, 1])
            z *= 1 - tw * np.clip(x / L + 0.5, 0, 1) if tw > 0 else 1 + tw * np.clip(0.5 - x / L, 0, 1)
            a = rng.uniform(-20, 20) * D2R
            xr, zr = x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a)
            cu, cz = cen[0] + rng.uniform(-0.2, 0.2) * ext[0] * 0.3, cen[1]
            d = self.mortar_d(np.array([cu]), np.array([cz]))[0] + yq
            W = self.to_world(cu + xr, cz + zr, d + P[0, :, 1])[None]
            Tq = self.tw(T_PIN_NB if T is T_PIN else T)
            if Tq["nv"] != W.shape[1]:
                Tq = self.tw(T)
            part.add(W, Tq, Pl=P, mat="M_stone", smooth="all", wear=0.5)
            self.add(W, Tq)
            acc.append((cu, cz))
            n += 1
        self._foot_acc = acc
        return n

    def skirts(self, part, w_out=(0.010, 0.015), climb=0.007):
        """Concave mortar strike: a fillet strip around each stone from ~7 mm up its side down to the mortar."""
        for W, T in self.stones:
            r2, r1 = RING2[id(T)]
            sub = slice(0, None, 2)
            A = W[:, r2[sub]]
            B = W[:, r1[sub]]
            N, m = A.shape[:2]
            ua, za, da = (x.reshape(N, m) for x in self.to_wall(A.reshape(-1, 3)))
            ub, zb, db = (x.reshape(N, m) for x in self.to_wall(B.reshape(-1, 3)))
            ua = self.unwrap(ua, ua[:, :1])
            ub = self.unwrap(ub, ua[:, :1])
            dm = self.mortar_d(ua, za)
            # skip stones whose sides are not exposed, or that sit on a mortar-depth step (footing ledge)
            dmo = self.mortar_d(ua, za - 0.03)
            okst = (np.median(da - dm, 1) > 0.001) & (np.abs(dmo - dm).max(1) < 0.01) & \
                (np.abs(self.mortar_d(ua, za + 0.03) - dm).max(1) < 0.01)
            if not okst.any():
                continue
            sel = np.nonzero(okst)[0]
            ua, za, da, ub, zb, db, dm = ua[sel], za[sel], da[sel], ub[sel], zb[sel], db[sel], dm[sel]
            N = len(sel)
            tgt = dm + climb
            t = np.clip((da - tgt) / np.maximum(da - db, 1e-6), 0, 1)
            ui, zi, di = ua + t * (ub - ua), za + t * (zb - za), da + t * (db - da)
            di = np.maximum(di, dm + 0.001)
            cu, cz = ui.mean(1, keepdims=True), zi.mean(1, keepdims=True)
            du, dz = ui - cu, zi - cz
            nr = np.sqrt(du ** 2 + dz ** 2) + 1e-9
            wo = np.random.default_rng(len(self.stones) + N).uniform(*w_out, (N, 1))
            uo, zo = ui + du / nr * wo, zi + dz / nr * wo
            do = np.minimum(self.mortar_d(uo, zi) - 0.0015, di - 0.002)
            Pin = self.to_world(ui, zi, di)
            Pout = self.to_world(uo, zo, do)
            V = np.concatenate([Pin, Pout], 1)                # (N, 2m, 3)
            j = np.arange(m)
            q = np.stack([j, (j + 1) % m, m + (j + 1) % m, m + j], 1)
            # winding: outward normal must point away from the wall
            a, b_, c_ = V[0, q[0, 0]], V[0, q[0, 1]], V[0, q[0, 2]]
            nrm = np.cross(b_ - a, c_ - a)
            out = self.to_world(np.array([ui[0, 0]]), np.array([zi[0, 0]]), np.array([di[0, 0] + 0.05]))[0] - a
            if np.dot(nrm, out) < 0:
                q = q[:, ::-1].copy()
            # drop skirt quads that dive under a neighbouring stone (both outer corners under stone cover)
            ii = np.clip(((uo - self.u0) / self.cell).astype(int), -self.nu, 2 * self.nu)
            ii = ii % self.nu if self.period is not None else np.clip(ii, 0, self.nu - 1)
            kk = np.clip(((zo - self.z0) / self.cell).astype(int), 0, self.nz - 1)
            under = self.cov[ii, kk]                            # (N, m)
            # round 4: a skirt quad whose two outer corners both lie under a neighbouring stone can never be seen
            qk = ~(under & np.roll(under, -1, axis=1))
            qq = (q[None] + (np.arange(N) * 2 * m)[:, None, None])[qk]
            if len(qq) == 0:
                continue
            T2 = dict(quads=qq, tris=np.zeros((0, 3), np.int64), qflat=np.zeros(len(qq), bool),
                      tflat=np.zeros(0, bool), nv=N * 2 * m)
            part.add(V.reshape(1, -1, 3), T2, mat="M_mortar", smooth="all")

    def report(self, label):
        f_all, n = self.mortar_fraction()
        msg = "WALL %-18s visible mortar %.1f%% (%d cells)" % (label, 100 * f_all, n)
        if self.metric_z is not None:
            f, n2 = self.mortar_fraction(*self.metric_z)
            msg += ", plain zone %.1f%%" % (100 * f)
        mv = self.max_void(True)
        msg += ", widest void %.3f m at u %.2f z %.2f, stones %d" % (mv + (sum(len(W) for W, _ in self.stones),))
        log(msg)


def depth_tilt_params(rng, N, p_tilt=0.18, dy=(-0.006, 0.012), yaw=(2.0, 4.0)):
    """Per-stone face depth (2 cm range) and a 2-4 deg yaw on ~18% of stones so one end stands proud."""
    tilt = rng.random(N) < p_tilt
    ang = np.where(tilt, rng.uniform(*yaw, N) * rng.choice([-1, 1], N), 0.0) * D2R
    return ang, rng.uniform(*dy, N)


def wall_depth(face_d, mortar_d, L, ang, margin=0.008):
    """Stone depth = its protrusion above the mortar + margin (+ what a yawed end swings back): nothing of the
    stone is modelled deeper than ~2 cm behind the mortar surface."""
    return np.maximum(face_d - mortar_d + margin + np.abs(np.sin(ang)) * L / 2, 0.03)


def apply_tilt(P, ang):
    return xform(P, rotm([0, 0, 1], ang), np.zeros(3))


def emit_drum_stones(g, part, mat, rng, S, style, yoff_base, bulge=True, wall=None, tilt=True, p_tilt=0.18,
                     dy=(-0.006, 0.012), follow=1.0, roll=0.8):
    """Lay the coursed stones S (coursing()) on the drum: per-stone face depth and yaw (one end proud), a
    low-frequency bulge in and out of the wall plane, each stone sheared to follow its wandering / pinching beds
    (follow_beds), an in-plane roll of +-`roll` deg; producer note 11 per stone (relief_min)."""
    if len(S["uc"]) == 0:
        return 0
    zc = S["zc"]
    th = S["uc"] / R_out(g, zc)
    N = len(zc)
    if tilt:
        ang, dy_ = depth_tilt_params(rng, N, p_tilt=p_tilt, dy=dy)
    else:
        ang, dy_ = np.zeros(N), rng.uniform(-0.003, 0.004, N)
    yo = yoff_base + dy_
    D = wall_depth(yo, drum_mortar_d(g, S["uc"], zc), S["L"], ang)
    if bulge:  # stones bulge in and out of the wall plane (low-frequency)
        yo += 0.004 * np.sin(th * 3 + 1.3) * np.sin(zc * 2.1 + 0.4) + 0.003 * np.sin(th * 7 + zc * 3)
    R0 = R_out(g, zc)
    mr = relief_min(g, np.stack([R0 * np.sin(th), -R0 * np.cos(th), zc], 1))
    tm = wall_stone_tmpl(zc, S["H"], STYLE[style]["T"])
    for ix, P, Tq in stones_by_tmpl(rng, S["L"], S["H"], D, style, tm, min_relief=mr, roll=roll):
        low = zc[ix] < 2.2
        if low.any():          # conchoidal scoops on ~30 % of the faces in the bottom 2.2 m (note 11: < 1 cm -> skin)
            Pl_ = P[low]
            conchoidal(rng, Pl_, Tq, min_relief=float(mr[ix][low].max()))
            P[low] = Pl_
        P = follow_beds(P, S, ix, follow)
        P = apply_tilt(P, ang[ix])
        W = cyl_place(g, P, th[ix], zc[ix], yo[ix])
        part.add(W, Tq, Pl=P, mat=mat, smooth="all")
        if wall is not None:
            wall.add(W, Tq)
    return len(zc)


def build_base(g, parts):
    P_st, P_mo, P_dr = parts["stones"], parts["mortar"], parts["dressed"]
    rng = g.RNG("base_rubble")
    n = 0

    def drum_blocked(U, Z):
        b = (Z < 0.0) | (Z > g.Z_CORN0) | ((Z > g.Z_BAND0 - 0.005) & (Z < g.Z_BAND1 + 0.005))
        C = 2 * PI * g.RREF
        for th0, fn in g.OPENINGS:
            du = ((U - th0 * g.RREF + C / 2) % C) - C / 2
            b |= np.abs(du) < fn(Z) * g.RREF / R_out(g, Z)
        return b
    WD = Wall("drum", partial(drum_to_world, g), partial(drum_to_wall, g), partial(drum_mortar_d, g), -PI * g.RREF, PI * g.RREF, 0.0, g.Z_CORN0, drum_blocked,
              period=2 * PI * g.RREF, metric_z=(0.40, g.Z_BAND0), registry=g.walls, min_relief=relief_door(g))
    R = g.rubble
    # 1. footing course (big stones projecting ~7 cm, bottoms cut at the ground)
    S = coursing(rng, -0.04, 0.40, free_fn_drum(g, rng), hr=(0.18, 0.24), hbig=0.26, p_big=0.0, lr=(0.42, 0.85),
                 p_tall=0.0, p_pin=0.0, Dr=(0.3, 0.4), wob=0.015 + 0.01 * R["rough"])
    n += emit_drum_stones(g, P_st, "M_stone", rng, S, "footing", 0.065, wall=WD, roll=0.8 + 0.7 * R["rough"])
    # 2. plain rubble 0.40 - band: ensemble review -> rough rubble like the keep / hut neighbours (wandering beds,
    #    pinch-outs, through-stones, more pinners, a wider spread of lengths and heights, more stones proud)
    S = coursing(rng, 0.40, g.Z_BAND0, free_fn_drum(g, rng), **R["plain"])
    n += emit_drum_stones(g, P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD, **R["emit"])
    log("plain rubble: %d stones, %d pinch-outs" % (len(S["uc"]), S["n_pinch"]))
    # 4. arcade zone: round 6 - the piers are laid by blind_arcade() as coursed long-and-short dressed blocks
    # (arcade_piers); without an arcade the zone is plain coursed ashlar
    if not g.ARCH_AZ:
        S = coursing(rng, g.Z_BAND1, g.ARCH["zs"], free_fn_drum(g, rng), hr=(0.2, 0.25), hbig=0.25, p_big=0.0,
                     lr=(0.24, 0.45), p_tall=0.0, p_pin=0.0, wob=0.0, joint=(0.01, 0.016))
        n += emit_drum_stones(g, P_st, "M_stone", rng, S, "ashlar", 0.012, bulge=False, wall=WD, tilt=False)
    S = coursing(rng, g.ARCH["zs"], g.Z_CORN0, free_fn_drum(g, rng), **R["spandrel"])
    n += emit_drum_stones(g, P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD, **R["emit"])
    log("drum rubble stones", n)

    # ---- door, slit windows and blind arcade (kit components set into this drum) ----
    arched_door(g, _drum_call=True)
    build_slit_windows(g, parts)
    blind_arcade(g, _drum_call=True)
    build_band_cornice_and_finish(g, parts)
    return n


def build_slit_windows(g, parts):
    P_dr, P_mo = parts["dressed"], parts["mortar"]
    # ---- dressed: slit windows ----
    rw = g.RNG("windows")
    for k, th in enumerate(g.WIN_AZ):
        fw = g.WIN["fw"][k]
        Rw_ = float(R_out(g, 1.6))
        mrw = float(relief_min(g, [Rw_ * math.sin(th), -Rw_ * math.cos(th), 1.6])[0])     # producer note 11
        jam = {-1: [(g.WIN["jz"][0], g.WIN["jz"][1], fw[0]), (g.WIN["jz"][1], g.WIN["jz"][2], fw[1])],
               1: [(g.WIN["jz"][0], g.WIN["jz"][1], fw[1]), (g.WIN["jz"][1], g.WIN["jz"][2], fw[0])]}
        for s, bl in jam.items():
            for (z0, z1, w) in bl:
                P, T = stone_local(rw, [w], [z1 - z0 - 0.012], [0.32], "dressed", rot_deg=(0.2, 0.2, 0.3), min_relief=mrw)
                W = open_place(g, P, np.array([th]), np.array([s * (g.WIN["cw"] + w / 2)]), np.array([(z0 + z1) / 2]),
                               np.array([0.02]))
                P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        # sill with drip (projects 6 cm) and lintel
        P, T = stone_local(rw, [0.62], [0.12], [0.40], "dressed", rot_deg=(0.2, 0.3, 0.2), min_relief=mrw)
        P[:, :, 2] += np.where(P[:, :, 2] > 0, -0.02 * np.clip(P[:, :, 1] + 0.1, 0, 1) * 6, 0)
        W = open_place(g, P, np.array([th]), np.array([0.0]), np.array([1.235]), np.array([0.06]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        P, T = stone_local(rw, [0.74], [0.18], [0.34], "dressed", rot_deg=(0.2, 0.2, 0.4), min_relief=mrw)
        W = open_place(g, P, np.array([th]), np.array([0.0]), np.array([1.945]), np.array([0.02]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        # splayed embrasure behind the slit (closed, dark): sides, sill, head and back (mortar)
        cth, sth = math.cos(th), math.sin(th)
        Rz = float(R_out(g, 1.575))

        def wpt(x, d, z):
            return [x * cth + (Rz + d) * sth, x * sth - (Rz + d) * cth, z]

        z0, z1 = g.WIN["z0"], g.WIN["z1"]
        cw = g.WIN["cw"]
        for s in (-1, 1):
            G = np.array([[wpt(s * cw, -0.30, z0), wpt(s * cw, -0.30, z1)],
                          [wpt(s * 0.22, -0.62, z0), wpt(s * 0.22, -0.62, z1)]])
            add_grid(P_mo, "M_mortar", G, flip=(s < 0))
        for zz, fl in ((z0, True), (z1 + 0.06, False)):
            G = np.array([[wpt(-cw, -0.30, zz), wpt(-0.22, -0.62, zz)],
                          [wpt(cw, -0.30, zz), wpt(0.22, -0.62, zz)]])
            add_grid(P_mo, "M_mortar", G, flip=fl)
        G = np.array([[wpt(-0.22, -0.62, z0), wpt(-0.22, -0.62, z1 + 0.06)],
                      [wpt(0.22, -0.62, z0), wpt(0.22, -0.62, z1 + 0.06)]])
        add_grid(P_mo, "M_mortar", G, flip=False)


def blind_arcade_build(g, parts):
    """Blind arcade recesses: voussoir rings, dressed jambs and sill slabs (object <PREFIX>_arcade_dressed) and the
    coursed rubble backs (<PREFIX>_arcade_backs; their pins and strike are laid with the drum's walls)."""
    P_dr = kpart(g, parts, "arcade_dressed", ["M_stone_dressed"], wear=0.4, angle=22.0)
    P_st = kpart(g, parts, "arcade_backs", ["M_stone"])
    # ---- dressed: blind arcade ----
    ra = g.RNG("arcade")
    for th in g.ARCH_AZ:
        jam = {s: [(g.ARCH["jz"][0], g.ARCH["jz"][1], g.ARCH["fw"] + ra.uniform(-0.01, 0.01)),
                   (g.ARCH["jz"][1], g.ARCH["jz"][2], g.ARCH["fw"] + ra.uniform(-0.01, 0.01))] for s in (-1, 1)}
        arch_set(g, P_dr, ra, th, g.ARCH["cw"], g.ARCH["zs"], int(ra.choice([9, 11])), g.ARCH["ring"], 0.30, {}, partial(R_out, g),
                 yfront=0.018)
        # round 5: dressed sill slab on the floor of the recess (full 0.25 m recess depth, top 2.92-2.94 m,
        # 1 cm chamfer, 1-2 chips): the recess floor was open into the hollow drum from above
        cw = g.ARCH["cw"]
        zsill = g.ARCH["z0"] + ra.uniform(0.003, 0.016)
        P, T = stone_local(ra, [2 * cw + 0.10], [0.06], [0.275], "dressed", rot_deg=(0.25, 0.15, 0.2), spall=(1, 2),
                           min_relief=relief_far(g))
        W = open_place(g, P, np.array([th]), np.array([ra.uniform(-0.01, 0.01)]), np.array([zsill - 0.03]),
                       np.array([0.006]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.5)

        def ff(zb, zt, cw=cw):
            zm = (zb + zt) / 2
            if zm < g.ARCH["zs"]:
                return [(-cw, cw)]
            dz = zt - g.ARCH["zs"]
            if dz >= cw - 0.05:
                return []
            w = math.sqrt(cw ** 2 - min(dz, cw) ** 2) + 0.03
            return [(-w, w)]

        S = coursing(ra, g.ARCH["z0"], g.ARCH["zs"] + cw, ff, hr=(0.09, 0.14), hbig=0.16, p_big=0.1, lr=(0.16, 0.4),
                     p_tall=0.0, p_pin=0.1, wob=0.01, Dr=(0.15, 0.22))
        cth, sth = math.cos(th), math.sin(th)

        def a_world(u, z, d, cth=cth, sth=sth):
            u = np.asarray(u, float)
            z = np.asarray(z, float) + 0 * u
            al = np.sqrt(np.maximum(R_out(g, z) ** 2 - u ** 2, 0.01)) - 0.25 + d
            return np.stack([u * cth + al * sth, u * sth - al * cth, z], -1)

        def a_wall(W, cth=cth, sth=sth):
            W = np.asarray(W)
            u = W[..., 0] * cth + W[..., 1] * sth
            al = W[..., 0] * sth - W[..., 1] * cth
            z = W[..., 2]
            return u, z, al - np.sqrt(np.maximum(R_out(g, z) ** 2 - u ** 2, 0.01)) + 0.25

        def a_mort(u, z, k=th):
            return -0.022 + (0.0 if g.rule.active else 1.0) * wall_relief(u, z, k)

        def a_block(U, Z, cw=cw):
            top = g.ARCH["zs"] + np.sqrt(np.clip(cw ** 2 - U ** 2, 0, None))
            return (np.abs(U) > cw) | (Z < g.ARCH["z0"]) | (Z > top)
        WA = Wall("arch", a_world, a_wall, a_mort, -cw - 0.05, cw + 0.05, g.ARCH["z0"] - 0.02, g.ARCH["zs"] + cw + 0.05,
                  a_block, registry=g.walls, min_relief=relief_far(g))
        if len(S["uc"]):
            ang, dy = depth_tilt_params(ra, len(S["uc"]))
            P, T = stone_local(ra, S["L"], S["H"], wall_depth(dy, a_mort(S["uc"], S["zc"]), S["L"], ang), "rubble",
                               min_relief=relief_far(g))
            P = apply_tilt(P, ang)
            W = open_place(g, P, np.full(len(S["uc"]), th), S["uc"], S["zc"], -0.25 + dy)
            P_st.add(W, T, Pl=P, mat="M_stone", smooth="all")
            WA.add(W, T)
        # mortar back panel of the recess (low-frequency relief): laid after the pins, behind-stone cells culled
        WA.panel = (a_world, a_mort, cw)
        WA.part = P_st
    arcade_piers(g, P_dr, g.RNG("arcade_piers"))


def pier_courses(rng, H, hr=(0.15, 0.30)):
    """Course heights for one pier: 3-4 courses of 0.15-0.30 m summing to H, a different sequence per pier."""
    nmin, nmax = max(int(math.ceil(H / hr[1] - 1e-6)), 1), max(int(math.floor(H / hr[0] + 1e-6)), 1)
    for _ in range(200):
        n = int(rng.integers(nmin, min(nmax, nmin + 1) + 1))
        h = rng.uniform(0.7, 1.3, n)
        h *= H / h.sum()
        if (h >= hr[0]).all() and (h <= hr[1]).all():
            return h
    return np.full(nmin, H / nmin)


def arcade_piers(g, P_dr, rng, yfront=0.015, depth=0.30):
    """Round 6 (director r5 #6): every pier between two arcade recesses is laid as coursed dressed blocks -
    course heights 0.15-0.30 m (own sequence per pier), long and short blocks of 0.30-0.55 m alternating
    quoin-fashion so the vertical joints break course to course, the first block of each course returning
    into the recess reveal as its jamb. A block's reveal end follows the opening's axis (open mapping) and its
    joint end is radial (drum mapping), so neighbouring blocks close tight with ~1 cm joints, no voids."""
    if not g.ARCH_AZ:
        return 0
    WD = [w for w in g.walls if w.name == "drum"][-1]
    cw, z0, zs = g.ARCH["cw"], g.ARCH["z0"], g.ARCH["zs"]
    azs = sorted(float(a) % (2 * PI) for a in g.ARCH_AZ)
    nb = 0
    for k, a0 in enumerate(azs):
        a1 = azs[(k + 1) % len(azs)] + (2 * PI if k + 1 == len(azs) else 0.0)
        hs = pier_courses(rng, zs - z0 - 0.002)
        zb = z0 + 0.001
        phase = int(rng.integers(0, 2))
        for c, hc in enumerate(hs):
            zc = zb + hc / 2
            R = float(R_out(g, zc))
            th_l = a0 + math.asin(cw / R)          # left reveal edge (right side of arch k)
            th_r = a1 - math.asin(cw / R)          # right reveal edge (left side of arch k+1)
            S = R * (th_r - th_l)
            nblk = max(2, int(round(S / 0.42)))
            lens = []
            for q in range(nblk):
                lng = (q + c + phase) % 2 == 0
                lens.append(rng.uniform(0.44, 0.55) if lng else rng.uniform(0.28, 0.36))
            j = rng.uniform(0.008, 0.012, nblk - 1)
            lens = np.array(lens) * (S - j.sum()) / sum(lens)
            starts = np.concatenate([[0.0], np.cumsum(lens[:-1] + j)])
            H = hc - rng.uniform(0.009, 0.013)
            for q in range(nblk):
                L = float(lens[q])
                P, T = stone_local(rng, [L], [H], [depth], "dressed", rot_deg=(0.1, 0.1, 0.12),
                                   spall=(1, 3) if q in (0, nblk - 1) else (0, 2), min_relief=relief_far(g))
                u = starts[q] + L / 2 + P[0, :, 0]          # arc length from the left reveal edge
                y = P[0, :, 1] + yfront + rng.uniform(-0.003, 0.004)
                z = zc + P[0, :, 2] + rng.uniform(-0.002, 0.002)
                Rz = R_out(g, z)
                phi = th_l + u / Rz
                rr = Rz + y
                Wc = np.stack([rr * np.sin(phi), -rr * np.cos(phi), z], 1)
                # opening-aligned mapping near each reveal: lateral coordinate in that arch's frame
                Wo = Wc.copy()
                wgt = np.ones(len(u))
                for (ath, uref, sg) in ((a0, 0.0, 1.0), (a1, S, -1.0)):
                    dist = sg * (u - uref)
                    near = dist < 0.15
                    if not near.any():
                        continue
                    xo = Rz * np.sin(phi - ath)
                    d = np.sqrt(np.maximum(Rz ** 2 - xo ** 2, 0.01)) + y
                    Wa = np.stack([xo * math.cos(ath) + d * math.sin(ath), xo * math.sin(ath) - d * math.cos(ath), z], 1)
                    wv = smoothstep(0.0, 0.15, dist)
                    Wo = np.where(near[:, None], Wa, Wo)
                    wgt = np.where(near, wv, wgt)
                W = (Wo * (1 - wgt[:, None]) + Wc * wgt[:, None])[None]
                P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.35)
                WD.add(W, T)
                nb += 1
            zb += hc
    log("arcade piers: %d coursed long-and-short dressed blocks in %d piers" % (nb, len(azs)))
    return nb


def build_band_cornice_and_finish(g, parts):
    P_st, P_mo, P_dr = parts["stones"], parts["mortar"], parts["dressed"]

    # ---- band: strings, back panel, balusters ----
    rb = g.RNG("band")
    skip_b = ()
    # profiles stop 5 cm inside the wall face (nothing modelled deeper)
    prof_lo = [(-0.05, 0), (0.10, 0), (0.12, 0.018), (0.12, 0.08), (0.105, 0.097), (-0.05, 0.10)]
    prof_up = [(-0.05, 0), (0.08, 0), (0.10, 0.018), (0.10, 0.082), (0.088, 0.098), (-0.05, 0.10)]
    profile_course(g, P_dr, "M_stone_dressed", rb, g.Z_BAND0, prof_lo, skip=skip_b)
    profile_course(g, P_dr, "M_stone_dressed", rb, g.Z_BAL1, prof_up, skip=skip_b, top_back=0.065)
    Rm = float(R_out(g, g.Z_BAL0))
    u0b = rb.uniform(0, 2 * PI * Rm)
    spans = [(u0b, u0b + 2 * PI * Rm)]
    S = coursing(rb, g.Z_BAL0, g.Z_BAL1, lambda zb, zt: spans, hr=(0.17, 0.17), p_big=0, lr=(0.3, 0.55), p_tall=0,
                 p_pin=0, wob=0, joint=(0.008, 0.014), Dr=(0.05, 0.06))
    th = S["uc"] / R_out(g, S["zc"])
    P, T = stone_local(rb, S["L"], S["H"], S["D"], "ashlar", min_relief=relief_far(g))
    P_dr.add(cyl_place(g, P, th, S["zc"], np.full(len(th), -0.03)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    baluster_row(g, rb, spans, g.Z_BAL0, g.Z_BAL1)

    # ---- cornice (raised: 4.17 - 4.62) ----
    rc = g.RNG("cornice")
    zc0 = g.Z_CORN0
    profile_course(g, P_dr, "M_stone_dressed", rc, zc0, [(-0.05, 0), (0.03, 0), (0.04, 0.01), (0.04, 0.06),
                                                    (0.03, 0.07), (-0.05, 0.07)], seg=(0.5, 0.8))
    # frieze course between corbels
    S = coursing(rc, zc0 + 0.07, zc0 + 0.22, lambda zb, zt: [(0.3, 0.3 + 2 * PI * float(R_out(g, zc0 + 0.15)))],
                 hr=(0.15, 0.15), p_big=0, lr=(0.25, 0.5), p_tall=0, p_pin=0, wob=0, joint=(0.008, 0.012),
                 Dr=(0.05, 0.06))
    th = S["uc"] / R_out(g, S["zc"])
    P, T = stone_local(rc, S["L"], S["H"], S["D"], "ashlar", min_relief=relief_far(g))
    P_dr.add(cyl_place(g, P, th, S["zc"], np.full(len(th), -0.005)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    dentil_corbels(g, rc, zc0 + 0.145, n=int(round(40 * float(R_out(g, zc0)) / 2.446)))
    profile_course(g, P_dr, "M_stone_dressed", rc, zc0 + 0.22, [(-0.05, 0), (0.19, 0), (0.20, 0.01), (0.20, 0.042),
                                                           (0.19, 0.05), (-0.05, 0.05)], seg=(0.6, 0.9))
    cap = [(-0.06, 0), (0.19, 0), (0.235, 0.035), (0.24, 0.042), (0.243, 0.056), (0.252, 0.056), (0.256, 0.046),
           (0.29, 0.058), (0.305, 0.072), (0.305, 0.145), (0.29, 0.16), (0.0, 0.18), (-0.06, 0.18)]
    profile_course(g, P_dr, "M_stone_dressed", rc, zc0 + 0.27, cap, seg=(0.75, 1.05), joint=0.008)

    # ---- pinning stones in every void > 3 cm, concave strike skirts, visible-mortar report ----
    rp = g.RNG("pins")
    for wl in [w for w in g.walls if w.name in ("drum", "arch")]:
        before = wl.mortar_fraction(*wl.metric_z)[0] if wl.metric_z else wl.mortar_fraction()[0]
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_pre.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        npin = wl.fill_pins(getattr(wl, "part", P_st), rp)
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_post.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        if wl.name == "drum":
            log("drum pins %d, rejected %d (plain-zone mortar before pins %.1f%%)" % (npin, wl.rejected, 100 * before))
            wl.report("drum")
            log("  pins per iteration", wl.iters)
        if not os.environ.get("MILL_NOSKIRT"):
            wl.skirts(P_mo)
        if wl.name == "arch":
            a_world, a_mort, cw = wl.panel
            xs = np.linspace(-cw - 0.06, cw + 0.06, 16)
            zz = np.linspace(g.ARCH["z0"] - 0.02, g.ARCH["zs"] + cw + 0.05, 20)
            X, Z = np.meshgrid(xs, zz, indexing="ij")
            hid = wl.covered_rect(X[:-1, :-1], X[1:, :-1], Z[:-1, :-1], Z[:-1, 1:])
            add_grid(P_mo, "M_mortar", a_world(X, Z, a_mort(X, Z)), keep=~hid, flip=False)
    arch_walls = [w for w in g.walls if w.name == "arch"]
    fr = np.mean([w.mortar_fraction()[0] for w in arch_walls])
    log("WALL arcade backs: mean visible mortar %.1f%%, widest void %.3f m" %
        (100 * fr, max(w.max_void() for w in arch_walls)))

    # ---- mortar core (outer skin): recessed 2.2 cm (4.5 cm raked in the bottom 0.6 m), +-5 mm relief ----
    nth = 288
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.concatenate([np.linspace(0.0, 0.40, 6), np.linspace(0.41, 0.70, 5), np.linspace(0.78, g.Z_BAND0, 22),
                         [g.Z_BAND0 + 0.005, g.Z_BAND1 - 0.005], np.linspace(g.Z_BAND1, g.Z_CORN0 + 0.12, 15)])
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    U = np.where(TH > PI, TH - 2 * PI, TH) * g.RREF
    G = drum_to_world(g, U, Z, drum_mortar_d(g, U, Z))
    keep = np.ones((nth, len(zs) - 1), bool)
    # remove cells touching the clear part of door / windows / arcade recesses
    for i in range(nth):
        for j in range(len(zs) - 1):
            th_s = np.array([ths[i], ths[i] + 2 * PI / nth, ths[i] + PI / nth])
            z_s = np.array([zs[j], zs[j + 1], (zs[j] + zs[j + 1]) / 2])
            for tq in th_s:
                for zq in z_s:
                    if inside_clear(g, tq, zq):
                        keep[i, j] = False
    # remove cells hidden behind full stone cover (stone outlines + their 1 cm mortar strike skirts, dressed work)
    WD = [w for w in g.walls if w.name == "drum"][0]
    us0 = np.where(ths > PI, ths - 2 * PI, ths) * g.RREF
    us1 = us0 + 2 * PI / nth * g.RREF
    hid = WD.covered_rect(us0[:, None], us1[:, None], zs[None, :-1], zs[None, 1:])
    band = (zs[None, :-1] > g.Z_BAND0 - 0.01) & (zs[None, 1:] < g.Z_BAND1 + 0.01)
    ledge = (zs[None, 1:] > 0.30) & (zs[None, :-1] < 0.50)      # footing ledge: no skirts there, keep the skin
    ledge |= (zs[None, 1:] > g.Z_BAND1) & (zs[None, :-1] < g.ARCH["zs"])   # pier joints: mortar skin, never the core
    n0 = int(keep.sum())
    keep &= ~(hid & ~band & ~ledge)
    log("drum mortar skin: %d of %d cells hidden behind stone cover -> culled" % (n0 - int(keep.sum()), n0))
    add_grid(P_mo, "M_mortar", G, keep=keep, wrap=True, flip=False)
    wall_core_backing(g, P_mo, g.Z_BAL1 + 0.02, g.Z_CORN0 + 0.28)


def wall_core_backing(g, part, z0, z1, d_out=None, depth=0.30, nth=180, nz=9):
    """Round 5 (producer note 6, 'never open holes when culling'): a cheap closed wall-core ring behind the
    band / arcade / cornice zone at R_out(z) - MORTAR_RECESS - 0.02, holed only at the clear openings (whose
    pockets are closed by the jambs, voussoirs, sill slabs and rubble backs), with top and bottom annuli and an
    inner face behind the recess backs. Culled stone soffits and mortar now show this surface, never a void."""
    d_out = -(MORTAR_RECESS + 0.02) if d_out is None else d_out
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.linspace(z0, z1, nz)
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    Rr = R_out(g, Z) + d_out
    G = np.stack([Rr * np.sin(TH), -Rr * np.cos(TH), Z], -1)
    keep = np.ones((nth, nz - 1), bool)
    for i in range(nth):
        for j in range(nz - 1):
            for tq in (ths[i], ths[i] + PI / nth, ths[i] + 2 * PI / nth):
                for zq in (zs[j], 0.5 * (zs[j] + zs[j + 1]), zs[j + 1]):
                    if inside_clear(g, tq, zq):
                        keep[i, j] = False
    add_grid(part, "M_mortar", G, keep=keep, wrap=True, flip=False)
    Ri = R_out(g, Z) + d_out - depth
    Gi = np.stack([Ri * np.sin(TH), -Ri * np.cos(TH), Z], -1)
    add_grid(part, "M_mortar", Gi[::4], wrap=True, flip=False)
    for j, fl in ((0, True), (nz - 1, False)):          # bottom annulus faces down, top faces up
        A = np.stack([G[::4, j], Gi[::4, j]], 1)
        add_grid(part, "M_mortar", A, wrap=True, flip=fl)
    log("wall-core backing z %.2f..%.2f at d %.3f: %d of %d outer cells kept (openings holed)"
        % (z0, z1, d_out, int(keep.sum()), keep.size))


# =============================================================================================
# public kit components
# =============================================================================================
def round_stone_drum(g, r_base=None, r_top=None, height=None, zones=None, door=None, arcade=None, windows=None,
                     seed=None):
    """Battered round rubble drum with a balustrade band, a blind arcade and a corbelled cornice (kit component).
    Radius r_base at the ground battering to r_top, cornice top at `height`; zones=dict(band=(z0, z_bal0, z_bal1,
    z1)) places the balustrade band (lower string course, baluster row, upper string course); `door` / `arcade` are
    the arched_door() / blind_arcade() parameters; `windows` the slit-window azimuths (deg).  Lays the projecting
    footing course, the coursed rubble (wandering beds, pinch-outs, through-stones, pinning stones in every void,
    concave mortar strike), the dressed work, the mortar skin and the wall-core backing.  Writes <PREFIX>_base_stones
    / _base_mortar / _base_dressed, the door, slit-window and arcade objects and the pooled balusters / corbels."""
    kw = {}
    if r_base is not None:
        kw["R_BASE0"] = r_base
    if r_top is not None:
        kw["R_BASE1"] = r_top
    if height is not None:
        kw["Z_CORN0"] = height - 0.45
        kw["Z_BATTER"] = height - 0.57
    if zones and "band" in zones:
        kw["Z_BAND0"], kw["Z_BAL0"], kw["Z_BAL1"], kw["Z_BAND1"] = zones["band"]
    if windows is not None:
        kw["WIN_AZ"] = [a * D2R for a in windows]
    g.set(**kw)
    if door:
        door_params(g, **door)
    if arcade:
        arcade_params(g, **arcade)
    with g.seeded(seed):
        n = build_base(g, g.parts)
    return n


def blind_arcade(g, n=None, clear_w=None, clear_h=None, z_sill=None, az0=18.0, seed=None, _drum_call=False):
    """Blind arcade of `n` round-headed recesses (clear_w x clear_h, sill at z_sill, first bay at az0 deg) set into
    the drum: 0.25 m deep with coursed rubble backs, 9-11 irregular voussoirs, dressed sill slabs and coursed
    long-and-short dressed piers (<PREFIX>_arcade_dressed, <PREFIX>_arcade_backs)."""
    if n is not None or clear_w is not None or clear_h is not None or z_sill is not None:
        arcade_params(g, n, clear_w, clear_h, z_sill, az0)
    with g.seeded(seed):
        blind_arcade_build(g, g.parts)
