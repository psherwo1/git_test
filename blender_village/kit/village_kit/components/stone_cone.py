"""components.stone_cone -- the stacked tiers above a polygonal hall: shake collar, concave stone cone tower, lantern
belt and bell cap with a turned finial (kit 1.1.0, from the hilltop keep; art bible 1.3, the signature tiers).

Public components (g = OctFrame; the cone profile g.CONE_Z / CONE_R stretches to g.CONE_TOP):
    shake_collar(g, seed=505)   tier 2: two layers of radiating riven shakes (shingles.riven_shakes, SIZE_TABLE
                                'collar_shake') from the skirt to a jagged comb, split shakes opening at the top, a
                                backing frustum and cope slabs on the ledge -> <P>_roof_collar_shakes, _cone_ledge_slabs
    stone_cone(g, seed=404)     tier 3: rough small coursed rubble on the concave "candle-snuffer" (stone_wall layout,
                                pinned voids) over a mortar body -> <P>_cone_stones, _cone_mortar
    lantern(g, seed=606)        octagonal lantern belt: sole / head rings, corner posts, vertical boards (SIZE_TABLE
                                'board'), two framed openings with a dark backing, a hinged hatch propped open on the SW
                                face -> <P>_lantern_boards, _lantern_frame
    cone_cap(g, seed=707)       tier 4: bell cap (oct_roof.build_cap, chunky shingles), lead hat fitted over the
                                shingles, turned finial (finial.turned_finial) -> <P>_cap_*, <P>_finial_main
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, TAN22, beam, fbm90, finalize, inst_faces, lathe_rz, obox, prof_circle, sweep
from ..shingles import SIZE_TABLE, riven_shakes
from .finial import lead_hat, turned_finial
from .oct_frame import FR, oct_corner, skirt_z_at, thatch_low
from .oct_roof import build_cap
from .stone_wall import cat_stones, fill_voids, filt, lay_stones, layout_wall


def _lay(*a, **k):
    return lay_stones(*a, relief=FR.min_relief, **k)


def build_cone(coll, seed=404):
    rng = np.random.default_rng(seed)
    acc = Acc(FR.prefix + "_cone_stones")
    m0 = float(np.interp(6.03, FR.CONE_ZF, FR.CONE_MF))       # below this the collar hides the cone
    m1 = float(np.interp(FR.CONE_TOP - 0.015, FR.CONE_ZF, FR.CONE_MF))
    cfg = dict(seed=11 + (seed - 404), footing=None, ch=(0.07, 0.13), p_tall=0.04, len=(0.12, 0.34), foot_len=(0.3, 0.5),
               joint=(0.006, 0.011), front=(0.008, 0.042), foot_proj=(0, 0), bevel=(0.005, 0.025),
               pillow=(0.004, 0.014), tilt=0.009, rot=0.02, p_double=0.05, p_long=0.02, back=0.08, bed_amp=0.018)
    srange = lambda mm: [(0.0, 2 * math.pi * float(np.interp(np.interp(mm, FR.CONE_MF, FR.CONE_ZF), FR.CONE_ZF, FR.CONE_RF)))]
    S = layout_wall(rng, srange, m0, m1, lambda a, b, c: [], cfg)
    pins, _, _ = fill_voids(S, srange, lambda a, b, c: [], m0, m1, rng, cfg, label="cone")
    S = cat_stones(S, pins)
    log("  cone stones:", len(S["sc"]))
    small = (S["hx"] < 0.045) & (S["hy"] < 0.045)
    # budget: one side segment + chamfer band (the cone is never seen closer than ~6 m)
    # round 5: tight joints and a less nibbled outline (visible mortar <= 15 %); 7x7 face grids only on the larger
    # stones, 5x5 on the rest (cone <= 150k tris)
    big = (S["hx"] > 0.13) & ~small
    _lay(acc, filt(S, big), cone_map_factory(), "M_stone", rng, rough=1.0, noise_amp=0.009, nz2=True, nxy=7,
                 side_depth=0.022)
    _lay(acc, filt(S, ~big & ~small), cone_map_factory(), "M_stone", rng, rough=1.0, noise_amp=0.008,
                 nz2=True, nxy=5, side_depth=0.022)
    _lay(acc, filt(S, small), cone_map_factory(), "M_stone", rng, rough=0.9, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=0.022)
    finalize(acc, coll, smooth_deg=28.0)
    # mortar body (lathe) with noise
    accm = Acc(FR.prefix + "_cone_mortar")
    zs = np.linspace(5.95, FR.CONE_TOP + 0.02, 24)
    seg = 72
    rr = np.interp(zs, FR.CONE_ZF, FR.CONE_RF) - 0.004
    V, F = lathe_rz(np.stack([rr, zs], 1), seg, cap_top=False, cap_bottom=False)
    th = np.arctan2(V[:, 1], V[:, 0])
    nz_ = 0.006 * fbm90(np.stack([np.cos(th) * 8, np.sin(th) * 8, V[:, 2] * 4], -1), 2)
    rad = np.hypot(V[:, 0], V[:, 1]) + nz_
    V[:, 0] = rad * np.cos(th)
    V[:, 1] = rad * np.sin(th)
    accm.add(V, F, "M_mortar")
    finalize(accm, coll)


def build_collar(coll, seed=505):
    rng = np.random.default_rng(seed)
    acc = Acc(FR.prefix + "_roof_collar_shakes")
    recs = []
    for layer in (0, 1):
        th = rng.uniform(0, 0.05)
        while th < 2 * math.pi - 0.02:
            w = rng.uniform(*SIZE_TABLE["collar_shake"]["width"])
            # butt radius: octagonal foot line at apothem FR.COLLAR_P on the skirt
            kf = int(np.round(th / (math.pi / 4))) % 8
            delta = th - kf * math.pi / 4
            delta = (delta + math.pi) % (2 * math.pi) - math.pi
            rb = FR.COLLAR_P / math.cos(delta)
            dth = w / rb
            thc = th + dth / 2
            recs.append((layer, thc, w, rb, rng.uniform(0.03, 0.045), float(np.clip(rng.normal(0, 0.035), -0.06, 0.06)),
                         rng.uniform(0.05, 0.25) * (1.0 if layer else 0.75), rng.integers(0, 4), rng.normal(0, 0.008)))
            th += dth * (1.0 if layer else 0.97) + rng.uniform(0.0, 0.004)
    R = np.array(recs, float)
    M = len(R)
    layer, thc, w, rb, tb, butt, tip, kind, twist = [R[:, i] for i in range(9)]
    kind = kind.astype(int)
    xb, yb = rb * np.cos(thc), rb * np.sin(thc)
    zsk, _ = skirt_z_at(xb, yb)
    zb = zsk + 0.13 + butt + layer * 0.035
    B = np.stack([xb, yb, zb], 1)
    rt = FR.COLLAR_TOP_R + layer * 0.03
    T = np.stack([rt * np.cos(thc), rt * np.sin(thc), np.full(M, FR.COLLAR_TOP_Z)], 1)
    D = T - B
    Lb = np.linalg.norm(D, axis=1)
    D /= Lb[:, None]
    L = Lb + tip
    # shakes whose upper half lies under the wing thatch are buried there -> dropped (partly buried ones stay, scribed)
    mid = B + D * (Lb * 0.6)[:, None]
    fpw = (mid[:, 0] > FR.WX_W - FR.W_OVH) & (mid[:, 0] < FR.WX_E + FR.W_OVH) & (mid[:, 1] > FR.WY_S - FR.W_OVH) & (mid[:, 1] < FR.WY_N + FR.W_OVH)
    buried = fpw & (mid[:, 2] < thatch_low(mid[:, 0], mid[:, 1]))
    keep = ~buried
    layer, thc, w, rb, tb, butt, tip, kind, twist = [v[keep] for v in (layer, thc, w, rb, tb, butt, tip, kind, twist)]
    B, T, D, Lb, L = B[keep], T[keep], D[keep], Lb[keep], L[keep]
    M = len(thc)
    E = np.stack([-np.sin(thc), np.cos(thc), np.zeros(M)], 1)
    N = np.cross(E, D)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    rs = np.random.default_rng(5051)
    cang = np.radians(rs.uniform(20, 40, M)) * np.where(rs.uniform(0, 1, M) < 0.5, -1, 1)
    notch = rs.uniform(0.03, 0.07, M)
    taper = rs.uniform(0.10, 0.20, M)
    tb = rs.uniform(0.037, 0.044, M)
    # riven faces: 2-4 longitudinal ridges / hollows of 2-5 mm, drifting a little along the shake
    nrid = rs.integers(2, 5, M)
    rc = rs.uniform(-0.8, 0.8, (M, 4))
    ra = rs.uniform(0.002, 0.005, (M, 4)) * np.where(rs.uniform(0, 1, (M, 4)) < 0.3, -1, 1)
    rsig = rs.uniform(0.12, 0.25, (M, 4))
    # 5-8 % of the shakes are split down 20-40 % of their length (built as two halves that open at the top)
    split = (rs.uniform(0, 1, M) < 0.065) & (layer > 0.5)
    sl = rs.uniform(0.2, 0.4, M)

    Sh = dict(w=w, L=L, tb=tb, taper=taper, kind=kind, cang=cang, notch=notch, twist=twist, sl=sl, phase=thc,
              nrid=nrid, rc=rc, ra=ra, rsig=rsig)
    thr = float(FR.min_relief(np.array([[0.0, 0.0, 5.6]]))[0])

    def build(sel, ncol, halves=0):
        idx = np.flatnonzero(sel)
        if len(idx) == 0:
            return 0
        Mi = len(idx)
        P, quads = riven_shakes(Sh, idx, ncol, halves, min_relief=thr)
        x, u, h = P[..., 0], P[..., 1], P[..., 2]
        Wv = B[idx][:, None, :] + u[..., None] * D[idx][:, None, :] + x[..., None] * E[idx][:, None, :] + \
            h[..., None] * N[idx][:, None, :]
        acc.add(Wv.reshape(-1, 3), inst_faces(quads, Mi, P.shape[1]), "M_roof_shake",
                uv=np.stack([x, u], -1).reshape(-1, 2))
        return Mi
    build((layer > 0.5) & ~split, 11)
    build(layer < 0.5, 7)
    build(split, 7, halves=-1)
    build(split, 7, halves=1)
    log(f"  collar shakes split: {int(split.sum())}")
    log("  collar shakes", M)
    # backing frustum + ledge to the cone
    prof = [(FR.COLLAR_P - 0.06, 4.70), (FR.COLLAR_TOP_R - 0.05, FR.COLLAR_TOP_Z - 0.02), (FR.COLLAR_TOP_R - 0.12, FR.COLLAR_TOP_Z + 0.02),
            (float(np.interp(FR.COLLAR_TOP_Z + 0.08, FR.CONE_ZF, FR.CONE_RF)) - 0.01, FR.COLLAR_TOP_Z + 0.08)]
    V, F = lathe_rz(prof, 64, cap_top=False, cap_bottom=False)
    acc.add(V, F, "M_roof_shake")
    finalize(acc, coll)
    # cope slabs on the ledge between the comb and the cone (shed water off the ledge)
    accl = Acc(FR.prefix + "_cone_ledge_slabs")
    zl = FR.COLLAR_TOP_Z + 0.06
    rin = float(np.interp(zl + 0.06, FR.CONE_ZF, FR.CONE_RF)) - 0.05
    th = rng.uniform(0, 0.1)
    while th < 2 * math.pi - 0.05:
        wd = rng.uniform(0.24, 0.40)
        dth = wd / 2.85
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0.0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0.0])
        tilt = math.radians(rng.uniform(8, 16))
        ex = n3 * math.cos(tilt) - np.array([0, 0, 1.0]) * math.sin(tilt)
        ez = np.cross(ex, t3)
        if ez[2] < 0:
            ez = -ez
        o = n3 * rin + np.array([0, 0, zl + 0.07 + rng.uniform(-0.01, 0.01)])
        L = FR.COLLAR_TOP_R - 0.06 - rin + rng.uniform(-0.03, 0.03)
        hh = rng.uniform(0.05, 0.08)
        seed = rng.uniform(0, 100)

        def dfm(P, seed=seed):
            P = P.copy()
            P[..., 2] += 0.008 * fbm90(P * 9 + seed, 2) * (0.008 >= thr)
            P[..., 1] *= 1 - 0.12 * (P[..., 0] / max(L, 0.1))
            return P
        obox(accl, o[None], ex, t3, ez, L, wd - rng.uniform(0.01, 0.025), hh, 0.015, "M_stone", nx=5, ny=5, nz=4,
             deform=dfm)
        th += dth
    finalize(accl, coll)


def build_lantern(coll, seed=606):
    rng = np.random.default_rng(seed)
    bwr = SIZE_TABLE["board"]["width"] if FR.units == "kit" else (0.14, 0.24)
    accb = Acc(FR.prefix + "_lantern_boards")
    accf = Acc(FR.prefix + "_lantern_frame")
    up = np.array([0, 0, 1.0])
    # sole ring on the cone top, head ring, corner posts
    for k in range(8):
        phi = math.radians(45 * k)
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        for apo_, z, sz in ((1.24, FR.LANT_Z0 + 0.1, 0.2), (1.27, FR.LANT_Z1 - 0.075, 0.15)):
            a = np.array([*oct_corner(apo_, k, -1), z])
            b = np.array([*oct_corner(apo_, k, 1), z])
            beam(accf, a - t3 * 0.08, b + t3 * 0.08, sz, sz, 0.02, "M_timber", up=up, nx=6)
        c = oct_corner(1.27, k, 1)
        cd = c / np.linalg.norm(c)
        cp = np.array([*(c - cd * 0.0), FR.LANT_Z0 + 0.2])
        beam(accf, cp, cp + np.array([0, 0, FR.LANT_Z1 - FR.LANT_Z0 - 0.35]), 0.14, 0.14, 0.02, "M_timber",
             up=np.array([cd[0], cd[1], 0]), nx=4)
    # vertical boards (with openings on facet 6 (-Y) and 5 (SW))
    opening = {6: (0.05, 10.0, 0.35, 0.45), 5: (-0.1, 10.0, 0.35, 0.45)}
    for k in range(8):
        phi = math.radians(45 * k)
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        half = FR.LANT_APO * TAN22
        x = -half + 0.03
        while x < half - 0.06:
            wd = min(rng.uniform(*bwr), half - 0.03 - x)
            if wd < 0.07:
                break
            zb = FR.LANT_Z0 - 0.08 + rng.uniform(-0.02, 0.02)
            zt = FR.LANT_Z1 + 0.02
            segs = [(zb, zt)]
            if k in opening:
                ox, oz, ow, oh = opening[k]
                if x + wd > ox - ow / 2 and x < ox + ow / 2:
                    segs = [(zb, oz - oh / 2 - 0.004), (oz + oh / 2 + 0.004, zt)]
            ask = rng.normal(0, 0.012) if rng.uniform() < 0.25 else rng.normal(0, 0.003)
            for za, zb2 in segs:
                o = n3 * (FR.LANT_APO - 0.015) + t3 * (x + wd / 2) + np.array([0, 0, za])
                ex = np.array([0, 0, 1.0]) + t3 * ask
                ex /= np.linalg.norm(ex)
                obox(accb, o[None], ex, t3, n3, zb2 - za, wd - 0.012, 0.03, 0.006, "M_timber_weathered",
                     nx=5, ny=4, nz=3, skip_back=k not in opening)
            x += wd
        # corner battens
        c = oct_corner(FR.LANT_APO + 0.02, k, 1)
        cd = np.array([c[0], c[1], 0]) / np.linalg.norm(c)
        ct = np.array([-cd[1], cd[0], 0])
        obox(accb, np.array([[c[0], c[1], FR.LANT_Z0 - 0.09]]), up, ct, cd, FR.LANT_Z1 - FR.LANT_Z0 + 0.1, 0.10, 0.035, 0.008,
             "M_timber_weathered", nx=4, ny=4, nz=3)
        if k in opening:
            ox, oz, ow, oh = opening[k]
            # opening frame
            for (a, b) in (((ox - ow / 2, oz - oh / 2), (ox + ow / 2, oz - oh / 2)), ((ox - ow / 2, oz + oh / 2), (ox + ow / 2, oz + oh / 2))):
                pa = n3 * (FR.LANT_APO + 0.02) + t3 * (a[0] - 0.05) + np.array([0, 0, a[1]])
                pb = n3 * (FR.LANT_APO + 0.02) + t3 * (b[0] + 0.05) + np.array([0, 0, b[1]])
                beam(accf, pa, pb, 0.06, 0.05, 0.01, "M_timber", up=n3)
            for xx in (ox - ow / 2 - 0.025, ox + ow / 2 + 0.025):
                pa = n3 * (FR.LANT_APO + 0.02) + t3 * xx + np.array([0, 0, oz - oh / 2 - 0.03])
                beam(accf, pa, pa + np.array([0, 0, oh + 0.06]), 0.05, 0.06, 0.01, "M_timber", up=n3)
            # dark interior backing behind the opening
            pa = n3 * (FR.LANT_APO - 0.6) + t3 * ox + np.array([0, 0, oz - oh / 2 - 0.1])
            obox(accb, pa[None], up, t3, n3, oh + 0.2, ow + 0.3, 0.05, 0.005, "M_timber", nx=4)
            if k == 5:
                # hinged hatch propped open (hinge at top, swung out ~40 deg)
                hz = oz + oh / 2 + 0.03
                ang = math.radians(38)
                hdir = -np.array([0, 0, 1.0]) * math.cos(ang) + n3 * math.sin(ang)
                base = n3 * (FR.LANT_APO + 0.05) + t3 * ox + np.array([0, 0, hz])
                for i, bw in enumerate((0.15, 0.14, 0.15)):
                    xo = ox - 0.22 + 0.075 + i * 0.147
                    o = n3 * (FR.LANT_APO + 0.05) + t3 * xo + np.array([0, 0, hz])
                    obox(accb, o[None], hdir, t3, np.cross(hdir, t3), 0.55, bw - 0.01, 0.028, 0.006, "M_timber_weathered",
                         nx=4, ny=4, nz=3)
                for zz in (0.12, 0.42):
                    o = base + hdir * zz - np.cross(hdir, t3) * 0.025 - t3 * 0.21
                    beam(accb, o, o + t3 * 0.42, 0.05, 0.025, 0.006, "M_timber_weathered", up=-np.cross(hdir, t3))
                # prop stick
                tip = base + hdir * 0.5
                foot = n3 * (FR.LANT_APO + 0.03) + t3 * (ox + 0.12) + np.array([0, 0, oz - oh / 2 - 0.02])
                V, F = sweep(np.array([foot, tip]), n3, prof_circle(0.018, 8))
                accb.add(V, F, "M_timber")
                # strap hinges
                for xo in (-0.12, 0.12):
                    o = base + t3 * (ox + xo - ox) * 1 - np.cross(hdir, t3) * 0.0 + n3 * 0.0
                    beam(accf, base + t3 * xo + hdir * 0.0 + np.cross(hdir, t3) * 0.018,
                         base + t3 * xo + hdir * 0.32 + np.cross(hdir, t3) * 0.018, 0.035, 0.006, 0.002, "M_iron",
                         up=np.cross(hdir, t3))
    # lantern floor & ceiling closure
    ang = np.radians(np.arange(8) * 45 + 22.5)
    r = 1.30 / math.cos(math.radians(22.5))
    for z, fl in ((FR.LANT_Z0 + 0.2, False), (FR.LANT_Z1, True)):
        V = np.stack([r * np.cos(ang), r * np.sin(ang), np.full(8, z)], 1)
        f = np.arange(8)[None]
        accf.add(V, f[:, ::-1] if fl else f, "M_timber")
    finalize(accb, coll)
    finalize(accf, coll)


def build_main_cap_and_finial(coll, seed=707, saddles=False, cap_exposure=None, saddle_taper=None):
    rng = np.random.default_rng(seed)
    chunky = FR.units == "kit"
    Vsh = build_cap(coll, FR.CAP, FR.prefix + "_cap", rng, p_wall=FR.LANT_APO, z_plate=FR.LANT_Z1, n_raft=4,
                    p_top=0.30 if chunky else 0.14, chunky=chunky,
                    expo=0.15, W=0.34, t=0.024, lens=(0.12, 0.18), bracket_z0=FR.LANT_Z1 - 0.45,
                    saddles=saddles, cap_exposure=cap_exposure, saddle_taper=saddle_taper)
    acc = Acc(FR.prefix + "_finial_main")
    apex = float(FR.CAP.zb(0.02))
    if chunky:
        z_top = lead_hat(acc, 0, 0, apex, 0.42, 0.60, cover=Vsh)
        turned_finial(acc, (0, 0, z_top - 0.01), 1.0, 1.0, (0.6, -0.8))
    else:
        lead_hat(acc, 0, 0, apex, 0.24, 0.20)
        turned_finial(acc, (0, 0, apex + 0.04), 1.0, 1.0, (0.6, -0.8))
    finalize(acc, coll)
    return apex


def cone_map_factory(z_base_m=0.0):
    def mapfn(s, m, w, mc):
        z = np.interp(m, FR.CONE_MF, FR.CONE_ZF)
        zc = np.interp(mc, FR.CONE_MF, FR.CONE_ZF)
        r = np.interp(z, FR.CONE_ZF, FR.CONE_RF)
        rc = np.interp(zc, FR.CONE_ZF, FR.CONE_RF)
        th = s / rc
        drdz = np.interp(z, FR.CONE_ZF, FR.CONE_DRDZ)
        nr = 1 / np.sqrt(1 + drdz ** 2)
        nzz = -drdz * nr
        R = r + w * nr
        return np.stack([R * np.cos(th), R * np.sin(th), z + w * nzz], -1)
    return mapfn



def shake_collar(g, seed=505):
    """KIT COMPONENT: tier 2 shake collar with its jagged comb."""
    build_collar(g.sub("tower"), seed=seed)


def stone_cone(g, seed=404):
    """KIT COMPONENT: tier 3 concave rubble cone."""
    build_cone(g.sub("tower"), seed=seed)


def lantern(g, seed=606):
    """KIT COMPONENT: the lantern belt on the cone top."""
    build_lantern(g.sub("tower"), seed=seed)


def cone_cap(g, seed=707, saddles=False, cap_exposure=None, saddle_taper=None):
    """KIT COMPONENT: tier 4 bell cap with lead hat and turned finial.  kit 1.3.0: saddles=True -> one flat saddle
    pair per hip (oct_roof.hip_saddles); cap_exposure=(lo, hi) -> the cap's shingle course exposure."""
    return build_main_cap_and_finial(g.sub("tower"), seed=seed, saddles=saddles, cap_exposure=cap_exposure,
                                     saddle_taper=saddle_taper)   # kit 1.5.0: tapered saddles (oct_roof.build_cap)
