"""village_kit.split_stones -- the split-stone language of the tower windmill, vectorised (kit 1.2.0).

One generator, many stones per call: split_batch(rng, L, H, D, style) returns N stones of one template topology at
once (local x = length, y = outward with the front face at y = 0, z = up), so a drum of ~9k rubble stones is laid in
a few numpy calls.  It is registered in village_kit.stones.STYLES under "split_<style>" (make_stone("split_rubble",
rng, half=(a, b, c)) builds a single stone), so the village keeps ONE stone generator entry point.

SPLIT_STYLES (rounding, outline noise, face noise, pillow, taper, shear, cuts / facets / spalls per style):
  rubble    coursed split rubble: angular outline from 2-4 straight fracture cuts across the corners, a flat bed
            face with 1-2 tilted split facets, arrises varying 0.3-1.5 cm per edge with 1-2 crisp broken edges
  footing   larger footing stones split like the rubble (flat beds, straight corner cuts, low-tilt facets)
  pin       pinning / packing stones
  dressed   crisp dressed work (surrounds, string courses, piers): outline noise <= 2 mm, flat faces, 1 cm
            chamfer, wear concentrated in 2-3 conchoidal spalls cut as 3 tilted planes (never pushing outward)
  hero      the actor-zone dressed blocks (door jambs, threshold): denser grids, 2-4 spalls
  ashlar    band / frieze ashlar above the actor zone
  flag      floor flags, ground  bedded pad stones (local y up)

Producer note 11 (min_relief): split facets, spalls and conchoidal scoops shallower than min_relief are not cut
(their random draws are still made, so the layout and the kept shape do not change); pass DetailRule thresholds.
"""
import math

import numpy as np

from .tmplmesh import (D2R, PI, T_DRS3L, T_DRS3X, T_DRSH3X, T_GRUB, T_PIN, T_RUB3, T_RUBF, euler, noise_field,
    rbox, unit, xform)  # noqa: F401


STYLE = {
    # rounding (frac of min dim, min, max), outline noise, face noise (m), pillow range (m), taper, shear
    # cuts = (min, max) straight fracture cuts on the outline; facets = (min, max) tilted face planes;
    # spall = (min, max) edge spalls (dressed work)
    "rubble": dict(avar=(0.003, 0.015, 0.8), rr=(0.08, 0.008, 0.013), ry=0.009, nxz=0.045, ny=0.006, pil=(0.002, 0.009), tap=0.07,
                   shear=0.06, T=T_RUB3, cuts=(2, 4), cutk=(0.8, 0.94), facets=(1, 2), hf=0.003, ftilt=0.25,
                   fshave=(0.008, 0.02)),
    "pin": dict(avar=(0.002, 0.008, 0.8), rr=(0.12, 0.004, 0.008), ry=0.006, nxz=0.05, ny=0.004, pil=(0.0, 0.004), tap=0.12,
                shear=0.08, T=T_PIN, cuts=(1, 3), cutk=(0.8, 0.92), facets=(0, 1), hf=0.0015, ftilt=0.3,
                fshave=(0.003, 0.008)),
    # round 6: footing stones split like the drum rubble (z01): flat beds (low outline noise), straight
    # fracture cuts that only take the corners, 0.3-1.5 cm arris variation with 1-2 crisp broken edges, and
    # low-tilt face facets (no melted, bevelled top arris)
    "footing": dict(avar=(0.003, 0.015, 0.7), rr=(0.09, 0.01, 0.015), ry=0.010, nxz=0.03, ny=0.005, pil=(0.002, 0.008), tap=0.06,
                    shear=0.05, T=T_RUB3, cuts=(2, 4), cutk=(0.82, 0.95), facets=(1, 2), hf=0.0025, ftilt=0.22,
                    fshave=(0.004, 0.012), ncrisp=(1, 2)),
    "boulder": dict(rr=(0.2, 0.012, 0.05), ry=0.2, nxz=0.12, ny=0.012, pil=(0.0, 0.01), tap=0.2,
                    shear=0.15, T=T_RUBF, cuts=(3, 4), facets=(1, 2), hf=0.003),
    # round 5: dressed / hero / ashlar are CRISP: straight edges (outline noise <= 2 mm), flat faces (+-1 mm),
    # a 1 cm chamfer, and the wear concentrated in crisp spalls (sramp = 4 mm ramp at the scar ends)
    "dressed": dict(rr=(0.1, 0.009, 0.010), ry=0.010, nxz=0.003, ny=0.0007, pil=(0.0, 0.0012), tap=0.004,
                    shear=0.004, T=T_DRS3X, spall=(2, 3), sramp=0.004),
    "hero": dict(rr=(0.1, 0.010, 0.010), ry=0.010, nxz=0.002, ny=0.0006, pil=(0.0, 0.001), tap=0.003,
                 shear=0.003, T=T_DRSH3X, spall=(2, 4), sramp=0.004),
    "ashlar": dict(rr=(0.1, 0.008, 0.012), ry=0.010, nxz=0.008, ny=0.0012, pil=(0.0, 0.002), tap=0.01,
                   shear=0.008, T=T_DRS3L, spall=(1, 2), facets=(0, 1), sramp=0.005),
    "flag": dict(rr=(0.2, 0.022, 0.035), ry=0.028, nxz=0.07, ny=0.003, pil=(0.0, 0.004), tap=0.12,
                 shear=0.08, T=T_RUBF, cuts=(2, 3)),
}


def rbox_pv(T, h, rv):
    """Rounded box with a PER-VERTEX arris radius rv (N, nv, 3): every edge of a stone can carry its own wear."""
    h = np.asarray(h, float)
    rv = np.minimum(rv, h[:, None, :] * 0.48)
    N = len(h)
    idx = T["idx"]
    P = np.empty((N, T["nv"], 3))
    for a in range(3):
        n = T["n"][a]
        ia = idx[:, a]
        if a == 1 and T.get("yfront"):
            pos = np.where(ia == 0, -h[:, None, 1], np.where(ia == 1, h[:, None, 1] - rv[:, :, 1], h[:, None, 1]))
        else:
            t = -1 + 2 * (ia - 1) / max(n - 3, 1)
            pos = np.where(ia == 0, -h[:, None, a], np.where(ia == n - 1, h[:, None, a],
                                                             t[None] * (h[:, None, a] - rv[:, :, a])))
        P[:, :, a] = pos
    lim = h[:, None, :] - rv
    inner = np.clip(P, -lim, lim)
    d = (P - inner) / rv
    nr = np.linalg.norm(d, axis=2, keepdims=True)
    dn = np.where(nr > 1e-9, d / np.maximum(nr, 1e-9), 0.0)
    return inner + dn * rv


def edge_radii(rng, T, N, rmin, rmax, ry_k, D, ncrisp=(1, 2)):
    """Per-vertex arris radii: each of a stone's four face edges gets its own wear in [rmin, rmax], and 1-2
    edges per stone are crisp broken edges (<= 3 mm)."""
    re = rng.uniform(rmin, rmax, (N, 4))
    nc = rng.integers(ncrisp[0], ncrisp[1] + 1, N)
    for k in range(ncrisp[1]):
        e = rng.integers(0, 4, N)
        sel = k < nc
        re[np.arange(N)[sel], e[sel]] = rng.uniform(0.0015, 0.003, int(sel.sum()))
    idx = T["idx"]
    tx = idx[:, 0] / (T["n"][0] - 1) * 2 - 1
    tz = idx[:, 2] / (T["n"][2] - 1) * 2 - 1
    rx = np.where(tx[None] < 0, re[:, 0:1], re[:, 1:2])
    rz = np.where(tz[None] < 0, re[:, 2:3], re[:, 3:4])
    ry = np.where(np.abs(tx)[None] >= np.abs(tz)[None], rx, rz) * ry_k
    ry = np.minimum(ry, 0.45 * np.asarray(D, float)[:, None])
    return np.stack([rx, ry, rz], 2)


def conchoidal(rng, P, T, frac=0.3, dep=(0.003, 0.008)):
    """Shallow conchoidal scoop (3-8 mm, crisp rim) on the front face of ~30 % of the stones (in place)."""
    N = len(P)
    front = T["idx"][:, 1] == T["n"][1] - 1
    sel = np.nonzero(rng.random(N) < frac)[0]
    for i in sel:
        F = P[i, front]
        lo, hi = F[:, [0, 2]].min(0), F[:, [0, 2]].max(0)
        c = lo + (hi - lo) * rng.uniform(0.2, 0.8, 2)
        R = min(rng.uniform(0.04, 0.10), 0.6 * float((hi - lo).min()))
        rho = np.hypot(F[:, 0] - c[0], F[:, 2] - c[1]) / max(R, 1e-3)
        d = rng.uniform(*dep) * np.clip(1 - rho ** 2, 0, 1)
        P[i, np.nonzero(front)[0], 1] -= d
    return len(sel)


def stone_local(rng, L, H, D, style, rot_deg=(2.0, 0.8, 1.1), spall=None, T=None):
    """Irregular stone, local x = length, y = outward (front face at y=0), z = up. (N,nv,3).
    Split-stone language: angular outline from straight fracture cuts, a flat bed face with 1-2 tilted
    facets (pillow <= 1 cm), small arris radius. Dressed work: flat faces, 1 cm chamfer, edge spalls."""
    st = STYLE[style]
    T = st["T"] if T is None else T
    L, H, D = (np.asarray(v, float) for v in (L, H, D))
    N = len(L)
    h = np.stack([L / 2, D / 2, H / 2], 1)
    mn = np.minimum(L, H)
    rxz = np.clip(st["rr"][0] * mn, st["rr"][1], st["rr"][2])
    ry = np.minimum(st["ry"], 0.45 * D) if st["ry"] < 0.15 else st["ry"] * np.minimum(mn, D)
    r = np.stack([rxz, np.broadcast_to(ry, (N,)), rxz], 1)
    if st.get("avar"):
        # round 4: the arris varies per edge (0.3-1.5 cm) with 1-2 crisp broken edges per stone
        a0, a1, kry = st["avar"]
        P = rbox_pv(T, h, edge_radii(rng, T, N, a0, a1, kry, D))
    else:
        P = rbox(T, h, r)
    u = P / h[:, None, :]
    tap = rng.uniform(-st["tap"], st["tap"], N)
    sh = rng.uniform(-st["shear"], st["shear"], N)
    P[:, :, 0] *= 1 + tap[:, None] * u[:, :, 2]
    P[:, :, 0] += sh[:, None] * u[:, :, 2] * h[:, None, 2]
    P[:, :, 0] += st["nxz"] * h[:, None, 0] * 0.6 * noise_field(u, rng)
    P[:, :, 2] += st["nxz"] * h[:, None, 2] * noise_field(u, rng)
    front = np.clip(u[:, :, 1], 0, 1)
    P[:, :, 1] += st["ny"] * noise_field(u * 1.6, rng, fmin=1.5, fmax=3.5) * (0.4 + 0.6 * front)
    if st.get("hf", 0):
        P[:, :, 1] += st["hf"] * noise_field(u * 3.0, rng, nterms=4, fmin=2.0, fmax=5.0) * (0.3 + 0.7 * front)
    pil = rng.uniform(*st["pil"], N)
    P[:, :, 1] += pil[:, None] * front * np.clip(1 - u[:, :, 0] ** 2, 0, 1) * np.clip(1 - u[:, :, 2] ** 2, 0, 1)
    if st.get("cuts"):
        # straight fracture cuts across corners of the face outline (exact planes -> straight edges)
        c0, c1 = st["cuts"]
        ncut = rng.integers(c0, c1 + 1, N)
        base_a = rng.uniform(0, 2 * PI, N)
        for k in range(c1):
            a = base_a + k * 2 * PI / c1 + rng.uniform(-0.45, 0.45, N)
            nrm = np.stack([np.cos(a) / h[:, 0], rng.normal(0, 0.12, N) / h[:, 1] * 0.0, np.sin(a) / h[:, 2]], 1)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            proj = np.einsum("nvc,nc->nv", P, nrm)
            o = proj.max(1) * rng.uniform(*st.get("cutk", (0.7, 0.9)), N)
            exc = np.clip(proj - o[:, None], 0, None) * (k < ncut)[:, None]
            P -= exc[:, :, None] * nrm[:, None, :]
    if st.get("facets"):
        # flat bed face + 1-2 tilted split facets shaving part of the face
        f0, f1 = st["facets"]
        nfac = rng.integers(f0, f1 + 1, N)
        for k in range(f1):
            ftl = st.get("ftilt", 0.32)
            nf = unit(np.stack([rng.normal(0, ftl, N), np.ones(N), rng.normal(0, ftl, N)], 1))
            proj = np.einsum("nvc,nc->nv", P, nf)
            o = proj.max(1) - rng.uniform(*st.get("fshave", (0.003, 0.011)), N)
            exc = np.clip(proj - o[:, None], 0, None) * (k < nfac)[:, None]
            P -= exc[:, :, None] * nf[:, None, :]
    sp = spall if spall is not None else st.get("spall")
    if sp:
        # round 6: spalls as the intersection of 3 tilted fracture planes (director r5 #5): two planes meeting
        # along the arris tilt the scar so its depth (1-3 cm at the deepest point) falls linearly to 0 at both
        # ends, a third plane skews it toward the face or the side -> an irregular, tapering, crisp-rimmed
        # chip with no rectangular corner. Each vertex inside all three half-spaces is pushed back along its OWN
        # face normal (front -> -y, side -> into the side; blended on the chamfer) onto the nearest plane, so
        # nothing ever moves outward or folds over its neighbour (no lips, tabs or flaps).
        s0, s1 = sp
        nsp = rng.integers(s0, s1 + 1, N)
        yh = np.array([0, 1.0, 0])
        ar = np.arange(N)
        for k in range(s1):
            side = rng.integers(0, 4, N)            # 0:+x 1:-x 2:+z 3:-z
            dax = np.where(side < 2, 0, 2)
            sgn = np.where(side % 2 == 0, 1.0, -1.0)
            aax = np.where(side < 2, 2, 0)
            dvec = np.zeros((N, 3))
            dvec[ar, dax] = sgn
            avec = np.zeros((N, 3))
            avec[ar, aax] = 1.0
            kk = rng.uniform(0.75, 1.5, N)
            nrm = unit(dvec + yh * kk[:, None])
            bvec = unit(np.cross(nrm, avec))
            ha = h[ar, aax]
            hd = h[ar, dax]
            dep = rng.uniform(0.012, 0.03, N)
            ca_ = rng.uniform(-0.7, 0.7, N) * ha
            hl1 = np.minimum(rng.uniform(0.035, 0.08, N), 0.6 * ha)
            hl2 = np.minimum(hl1 * rng.uniform(0.6, 1.5, N), 0.6 * ha)
            edge = dvec * hd[:, None] + yh * h[:, 1:2]
            c0 = edge + avec * ca_[:, None] - nrm * dep[:, None]
            n1 = unit(nrm + avec * (dep / hl1)[:, None])
            n2 = unit(nrm - avec * (dep / hl2)[:, None])
            n3 = unit(nrm + bvec * rng.uniform(-0.45, 0.45, N)[:, None] + avec * rng.uniform(-0.15, 0.15, N)[:, None])
            c3 = c0 - nrm * (rng.uniform(-0.25, 0.1, N) * dep)[:, None]
            on = (k < nsp)[:, None]
            ds = np.abs(hd[:, None] - sgn[:, None] * np.take_along_axis(P, dax[:, None, None].repeat(P.shape[1], 1), 2)[:, :, 0])
            df = np.abs(h[:, 1:2] - P[:, :, 1])
            ws, wf = 1.0 / (ds + 0.002), 1.0 / (df + 0.002)
            m = unit((ws[:, :, None] * dvec[:, None, :] + wf[:, :, None] * yh) / (ws + wf)[:, :, None])
            fs, ts = [], []
            for nn, cc in ((n1, c0), (n2, c0), (n3, c3)):
                f = np.einsum("nvc,nc->nv", P - cc[:, None, :], nn)
                fs.append(f)
                ts.append(f / np.maximum(np.einsum("nvc,nc->nv", m, nn), 0.2))
            inside = (fs[0] > 0) & (fs[1] > 0) & (fs[2] > 0) & on
            t = np.where(inside, np.minimum(np.minimum(ts[0], ts[1]), ts[2]), 0.0)
            t = np.clip(t, 0, 0.045)
            P -= t[:, :, None] * m
    P[:, :, 1] -= h[:, None, 1]
    rx, ry_, rz = rot_deg
    R = euler(rng.normal(0, rx * D2R, N), rng.normal(0, ry_ * D2R, N), rng.normal(0, rz * D2R, N))
    return xform(P, R, np.zeros(3)), T


STYLE["ground"] = dict(rr=(0.06, 0.008, 0.015), ry=0.012, nxz=0.05, ny=0.008, pil=(0.0, 0.008), tap=0.15,
                       shear=0.12, T=T_GRUB, cuts=(3, 4), cutk=(0.78, 0.9), facets=(1, 2), hf=0.003, ftilt=0.45,
                       fshave=(0.01, 0.03))
SPLIT_STYLES = STYLE
split_batch = stone_local


def _as_generator(rng):
    if isinstance(rng, np.random.Generator):
        return rng
    return np.random.default_rng(int(rng.randint(0, 2 ** 31 - 1)))


def _single(style):
    def make(half, rng, rot_deg=(2.0, 0.8, 1.1), spall=None, T=None):
        """one split stone (village_kit.stones.make_stone entry): half = (along, out, up) half extents.
        Returns (V, faces) in local coords, x along, y out (face at +y), z up, centred."""
        a, b, c = (float(v) for v in half)
        P, Tq = stone_local(_as_generator(rng), [2 * a], [2 * c], [2 * b], style, rot_deg=rot_deg, spall=spall, T=T)
        V = P[0] + np.array([0.0, b, 0.0])
        faces = [f for f in (Tq["quads"], Tq["tris"]) if len(f)]
        return V, faces
    make.__name__ = "split_" + style
    make.__doc__ = f"split-stone style {style!r} (village_kit.split_stones)"
    return make


split_rubble = _single("rubble")
split_footing = _single("footing")
split_pin = _single("pin")
split_dressed = _single("dressed")
split_hero = _single("hero")
split_ashlar = _single("ashlar")
split_flag = _single("flag")
