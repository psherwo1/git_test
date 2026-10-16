"""components.raking_props -- raking timber props shoring a tower (kit 1.2.0): bowed knotted poles, head
cleats, collar lugs and through-bolts, bedded split-stone pads with sunk hewn chocks and iron dogs, cross brace.

Public component: raking_props(g, props, seed).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (TZ, face_axes, face_map, lean)  # noqa: F401
from ..split_stones import (stone_local)  # noqa: F401
from ..tmplmesh import (D2R, PI, R_UPRIGHT, T_PAD, add_caps, add_grid, bolt_heads, circle_prof, facet_shave,
    frame_mats, hewn_beam, lathe, log, member, orient, rect_prof, rotm, sweep, tmpl_rings, unit, xform)  # noqa: F401


def prop_foot(P_a, rng, bot, hz, Zf, idx, pole_at, heel=0.10):
    """Raking-prop foot (kit component, round 5): a split-stone pad bedded in the soil with only its domed,
    irregular top showing (3-6 cm on the high side, 0-2 cm on the low side, no vertical side over 4 cm); a
    hewn chock with planar adze facets sunk >= 40 % of its height into a notch cut in the pad, a bird's-mouth
    step receiving the axe-cut pole foot, two iron dogs; a concave soil fillet that runs out tangentially, and
    3-5 split pebbles buried 40-60 %. hz: horizontal direction pole-top -> foot; seat at Zf, heel `heel` higher."""
    Z3 = np.array([0, 0, 1.0])
    sv = unit(np.cross(Z3, hz))
    Rg = frame_mats(hz[None], sv[None], Z3[None])[0]
    base = bot * np.array([1, 1, 0])

    def place(P, along, lat, z):
        return xform(P, Rg, base + hz * along + sv * lat + np.array([0, 0, z]))
    # ---- pad: bedded split stone, domed top, tilted 3-4 deg, highest point 4.5-5.5 cm ----
    Lpad, Wpad, Hpad = rng.uniform(0.64, 0.74), rng.uniform(0.56, 0.64), 0.20
    Pst, Tst = stone_local(rng, [Lpad], [Wpad], [Hpad], "ground", rot_deg=(0, 0, 0), T=T_PAD)
    uu = Pst[0, :, 0] / (Lpad / 2)
    ww = Pst[0, :, 2] / (Wpad / 2)
    up_w = np.clip((Pst[0, :, 1] + Hpad) / Hpad, 0, 1)
    Pst[0, :, 1] += rng.uniform(0.016, 0.022) * np.clip(1 - uu ** 2, 0, 1) * np.clip(1 - ww ** 2, 0, 1) * up_w
    Wp = xform(Pst, Rg @ R_UPRIGHT @ rotm([0, 1, 0], [rng.uniform(-0.15, 0.15)])[0], base - hz * 0.10)
    td = rng.uniform(0, 2 * PI)
    tdir = np.array([math.cos(td), math.sin(td), 0.0])
    Wp[0, :, 2] += math.tan(rng.uniform(3.0, 4.0) * D2R) * ((Wp[0] - base) @ tdir)
    Wp[0, :, 2] += rng.uniform(0.045, 0.055) - Wp[0, :, 2].max()
    # notch for the chock: chock footprint (+1 cm) pressed down to the notch floor
    al0, al1, hwc = -0.34, 0.15, 0.13
    d = Wp[0] - base
    al, lt = d @ hz, d @ sv
    # round 6: the notch is cut to the chock's footprint +3 mm (gap <= 5 mm), packed with soil below
    inn = (al > al0 - 0.003) & (al < al1 + 0.003) & (np.abs(lt) < hwc + 0.003)
    z_pad_c = float(np.max(np.where(inn, Wp[0, :, 2], -1)))
    z_n = -0.045
    Wp[0, :, 2] = np.where(inn, np.minimum(Wp[0, :, 2], z_n), Wp[0, :, 2])
    P_a.add(Wp, Tst, Pl=Pst, mat="M_stone", smooth="all", wear=0.7)
    # ---- chock: hewn block with planar adze facets, bird's-mouth step at along = 0 ----
    Lc = al1 - al0
    Hc = Zf + heel - z_n
    Pc, Tc = hewn_beam(rng, Lc, 2 * hwc, Hc, nx=18, chamfer=(0.007, 0.013), adze=(0.002, 0.004), checks=(1, 1),
                       check_len=(0.15, 0.3), end_split=1, drop=((2, 0),))
    # round 6 (director r5 #4): an irregular hewn WEDGE - the top 2-3 cm narrower than the base, the heel end
    # tapering 3-5 cm toward the top, and adze facets 6-12 mm deep that read from 2 m
    zr_ = np.clip((Pc[0, :, 2] + Hc / 2) / Hc, 0, 1)
    nw_ = rng.uniform(0.010, 0.015)
    Pc[0, :, 1] -= np.sign(Pc[0, :, 1]) * nw_ * zr_ * np.clip(np.abs(Pc[0, :, 1]) / hwc, 0, 1)
    et_ = rng.uniform(0.03, 0.05)
    Pc[0, :, 0] -= et_ * zr_ * np.clip((Pc[0, :, 0] + 0.02) / (Lc / 2), 0, 1)
    Pc[0, :, 1] += rng.uniform(-0.006, 0.006) * zr_ * np.sign(Pc[0, :, 1])  # the two cheeks not parallel
    Pc[0] = facet_shave(Pc[0], rng, ((1, 1), (1, -1), (2, 1), (0, 1), (0, -1)), n=(2, 3), dep=(0.006, 0.012),
                        tilt=0.18)
    xs_ = Pc[0, :, 0] + (al0 + al1) / 2                       # along
    zl = Pc[0, :, 2] + Hc / 2                                  # 0 .. Hc above the notch floor
    seat = xs_ < -0.003
    Pc[0, :, 2] = np.where(seat, -Hc / 2 + zl * (Zf - z_n) / Hc, Pc[0, :, 2])
    P_a.add(place(Pc, (al0 + al1) / 2, 0.0, z_n + Hc / 2), Tc, Pl=Pc[0], mat="M_timber_weathered", smooth="bevel",
            wear=0.75)
    sunk = (z_pad_c - z_n) / Hc
    # soil / chinking packed into the notch round the chock: a band from 1 cm down the chock's cheeks out over
    # the notch rim, tucked under the pad's top surface (no dark slot)
    zrel_rim = (z_pad_c - z_n) / Hc
    hw_rim = hwc - nw_ * zrel_rim
    perim = []
    for (a0_, a1_, l0_, l1_) in ((al0, al1, -hw_rim, -hw_rim), (al1 - et_ * zrel_rim, al1 - et_ * zrel_rim, -hw_rim, hw_rim),
                                 (al1, al0, hw_rim, hw_rim), (al0, al0, hw_rim, -hw_rim)):
        for u_ in np.linspace(0, 1, 9)[:-1]:
            perim.append((a0_ + (a1_ - a0_) * u_, l0_ + (l1_ - l0_) * u_))
    perim = np.array(perim)
    cc_ = perim.mean(0)
    dir_ = perim - cc_
    dir_ /= np.linalg.norm(dir_, axis=1, keepdims=True)
    padxy = Wp[0, :, :2]
    padz = Wp[0, :, 2]
    rows = []
    for f_, (off_, dz_) in enumerate(((-0.004, -0.010), (0.006, -0.004), (0.02, None), (0.035, None))):
        q_ = perim + dir_ * off_
        wq = base[None, :2] + hz[None, :2] * q_[:, :1] + sv[None, :2] * q_[:, 1:2]
        if dz_ is None:
            dd_ = np.linalg.norm(padxy[None] - wq[:, None], axis=2)
            near_ = np.argsort(dd_, axis=1)[:, :4]
            zq = padz[near_].max(1) - (0.002 if f_ == 2 else 0.006)
        else:
            zq = np.full(len(wq), z_pad_c + dz_)
        rows.append(np.concatenate([wq, zq[:, None]], 1))
    G = np.stack(rows, 1)
    nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
    add_grid(P_a, "M_earth", G, wrap=True, flip=bool(nrm_[2] < 0))
    # iron dogs (round 6): a flat bar driven into the chock's top, bent, and lying FLAT on the pole's side
    # (gap <= 2 mm) for 14-18 cm, spike heads at both ends
    for sg in (-1, 1):
        za_, zb_ = Zf - 0.07, Zf - 0.012
        hwa = hwc - nw_ * (za_ - z_n) / Hc + 0.0035
        hwb = hwc - nw_ * (zb_ - z_n) / Hc + 0.0035
        a_ = place(np.zeros((1, 1, 3)), -0.12, sg * hwa, za_)[0, 0]
        a2_ = place(np.zeros((1, 1, 3)), -0.12, sg * hwb, zb_)[0, 0]
        z1_ = Zf + 0.11
        pc1, pr1 = pole_at(z1_)
        pc2, pr2 = pole_at(z1_ + rng.uniform(0.12, 0.16))
        b1_ = pc1 + sv * sg * (pr1 + 0.0035)
        b2_ = pc2 + sv * sg * (pr2 + 0.0035)
        member(P_a, "M_iron", a_[None], a2_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        member(P_a, "M_iron", a2_[None], b1_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        member(P_a, "M_iron", b1_[None], b2_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        bolt_heads(P_a, np.stack([a_ + sv * sg * 0.004, b2_ + sv * sg * 0.004]),
                   np.stack([sv * sg, sv * sg]), rad=0.011, hgt=0.006, sides=8)
    log("prop foot %d: pad top %.3f m, chock %.0f%% sunk into the notch (height %.3f), seat %.2f, heel %.2f"
        % (idx, float(Wp[0, :, 2].max()), 100 * sunk, Hc, Zf, Zf + heel))


def raking_prop(g, parts, top, bot, k, zatt, idx=0, rng=None, Zf=0.08, seed=None):
    """Raking timber prop (kit component): a bowed, checked, knotted pole from its head `top` (on tower face k at
    height zatt, carried by a cleat, collar lugs and a through-bolt) down to the ground anchor at `bot`, ending in
    prop_foot() (bedded pad, sunk chock, soil fillet). Writes <PREFIX>_props / _prop_anchors / _prop_iron."""
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = g.RNG("prop_%s" % seed) if rng is None else rng
    nn_, tt_ = face_axes(k)
    nn_ = g.LEAN_R @ nn_
    axis = bot - top
    Lp = np.linalg.norm(axis)
    ax = axis / Lp
    hz = unit(np.array([axis[0], axis[1], 0]))
    side = unit(np.cross(axis, [0, 0, 1.0]))
    upv = np.cross(side, ax)
    # ---- pole: 24 sides (+ check lips), rings every ~6.5 cm (1.5 cm over the foot), dia 0.15 -> 0.20,
    # 6-12 cm bow; 2-3 real V checks, 2 adze flats + a bark-strip remnant, 4-6 knots with branch stubs ----
    dt = 0.045 / Lp
    t_main = np.arange(-0.02, 1.0 - 0.5 / Lp, dt)
    t_foot = np.arange(t_main[-1] + 0.012 / Lp, 1.06, 0.012 / Lp)
    t = np.concatenate([t_main, t_foot])
    n = len(t)
    bow = rng.uniform(0.08, 0.12) * rng.choice([-1, 1])
    sag = rng.uniform(0.0, 0.03)
    cen = top + axis * t[:, None] + side * (bow * np.sin(np.clip(t, 0, 1) * PI))[:, None] \
        - upv * (sag * np.sin(np.clip(t, 0, 1) * PI))[:, None]
    rad = 0.075 + 0.025 * np.clip(t, 0, 1) + 0.003 * np.sin(t * 13 + idx) + 0.002 * np.sin(t * 31 + 2 * idx)
    nck = int(rng.integers(2, 4))
    # first check on the face seen from the front / hero cameras (-side), the second on the upper face
    ck_a = np.array([PI + rng.uniform(-0.4, 0.4), PI / 2 + rng.uniform(-0.4, 0.4),
                     rng.uniform(-PI / 2, 0.2)])[:nck]
    # round 5: two more checks in the bottom 1.2 m of the pole (actor distance), on faces the cameras see
    jit_ = rng.uniform(-0.08, 0.08)
    for off_ in (0.55, -0.6, 1.0, -1.1, 2.4, -2.5, 3.14):
        cand_ = ck_a[0] + off_ + jit_
        if len(ck_a) < nck + 2 and np.min(np.abs((ck_a - cand_ + PI) % (2 * PI) - PI)) > 0.4:
            ck_a = np.append(ck_a, cand_)
    base_a = np.linspace(0, 2 * PI, 32, endpoint=False)
    extra = np.concatenate([[a - 0.115, a, a + 0.115] for a in ck_a]) % (2 * PI)
    keep_b = np.array([np.min(np.abs((b - extra + PI) % (2 * PI) - PI)) > 0.06 for b in base_a])
    ang = np.sort(np.concatenate([base_a[keep_b], extra]))
    m = len(ang)
    ell = 1 + rng.uniform(-0.04, 0.04) * np.cos(2 * ang + rng.uniform(0, PI))
    R = rad[:, None] * ell[None, :]
    sdist = (1 - t) * Lp                                    # distance from the foot (m)
    # low-frequency undulation of the trunk (+-3 mm)
    R += 0.003 * np.sin(sdist[:, None] * rng.uniform(2, 4) + ang[None, :] * 2 + rng.uniform(0, 6)) * \
        np.sin(sdist[:, None] * rng.uniform(0.7, 1.4) + rng.uniform(0, 6))
    # adze flats (+-1 cm) and a bark-strip remnant (proud 7 mm, ragged edges)
    for q in range(4):
        af = (PI + rng.uniform(-0.5, 0.5)) if q == 0 else rng.uniform(0, 2 * PI)
        lf = rng.uniform(0.8, 1.6) if q < 3 else rng.uniform(0.6, 0.9)
        s0 = rng.uniform(0.6, 3.5) if q == 0 else (rng.uniform(1.0, Lp - lf - 0.5) if q < 3 else
                                                     rng.uniform(0.12, 0.28))   # q 3: adze flat at the foot
        win = np.clip(np.minimum(sdist - s0, s0 + lf - sdist) / 0.15, 0, 1)
        da = (ang[None, :] - af + PI) % (2 * PI) - PI
        dep = rng.uniform(0.010, 0.014) * win
        flat = (rad[:, None] - dep[:, None]) / np.maximum(np.cos(da), 0.3)
        R = np.where(np.abs(da) < 1.2, np.minimum(R, flat), R)
    ab = rng.uniform(0, 2 * PI)
    lb = rng.uniform(0.5, 0.9)
    s0 = rng.uniform(2.0, Lp - lb - 1.0)
    inb = (sdist > s0) & (sdist < s0 + lb)
    hw_b = 0.3 + 0.08 * np.sin(sdist * 17 + idx) + 0.05 * np.sin(sdist * 41)
    da = np.abs((ang[None, :] - ab + PI) % (2 * PI) - PI)
    R += 0.010 * (inb[:, None] & (da < hw_b[:, None]))
    # V checks (round 6, director r5 #4): each check is a tapering split - width 0 -> 1.5-2.5 cm -> 0 and depth
    # 0 -> 1.2-2.2 cm -> 0 along its 0.3-0.8 m length (no two the same length), drifting +-5 deg off the grain
    # (the V's bottom slides across the three check columns), plus one radial end-grain split at the butt
    checks = []
    used_l = []
    for ci, a in enumerate(ck_a):
        jc = int(np.argmin(np.abs((ang - a % (2 * PI) + PI) % (2 * PI) - PI)))
        jl, jr = (jc - 1) % m, (jc + 1) % m
        for _t in range(20):
            lc = rng.uniform(0.3, 0.8)
            if all(abs(lc - q) > 0.06 for q in used_l):
                break
        used_l.append(lc)
        if len(checks) >= nck:              # foot checks: within the bottom 1.2 m
            s0 = rng.uniform(0.15, 1.2 - lc)
        else:
            s0 = rng.uniform(1.3, Lp - lc - 0.8)
        u = np.clip((sdist - s0) / lc, 0, 1)
        env = np.sin(u * PI) ** 1.3 * (1 + 0.15 * np.sin(u * 11 + ci))
        dep = rng.uniform(0.012, 0.022) * env
        drift = rng.uniform(-1.4, 1.4)          # ~ +-5 deg over the check's length (column units)
        sl = np.clip(0.5 * drift * (2 * u - 1), -0.8, 0.8) * (u > 0) * (u < 1)
        wfac = np.clip(env * rng.uniform(1.1, 1.4), 0, 1)                             # width taper
        R[:, jc] -= dep * (1 - np.abs(sl))
        R[:, jl] -= dep * np.clip(-sl, 0, 1) * wfac
        R[:, jr] -= dep * np.clip(sl, 0, 1) * wfac
        # narrow the open V toward its ends: the lip columns sag in only where the check is wide
        R[:, jl] -= 0.002 * wfac * (u > 0) * (u < 1)
        R[:, jr] -= 0.002 * wfac * (u > 0) * (u < 1)
        checks.append((round(s0, 2), round(lc, 2)))
    # end-grain split at the butt: deepest (2.5-3.5 cm) at the foot cut, closing 0.15-0.25 m up the pole
    jb = int(np.argmin(np.abs((ang - (ck_a[0] + PI * 0.55) % (2 * PI) + PI) % (2 * PI) - PI)))
    lsp = rng.uniform(0.15, 0.25)
    usp = np.clip(1 - sdist / lsp, 0, 1)
    R[:, jb] -= rng.uniform(0.025, 0.035) * usp ** 0.7
    checks.append(("butt", round(lsp, 2)))
    # knots: 4-6, at least 2 within 2.5 m of the foot
    nk = int(rng.integers(4, 7))
    kd = np.concatenate([rng.uniform(0.7, 2.4, 2), rng.uniform(3.0, Lp - 1.0, nk - 2)])
    knots = []
    for ik, sk in enumerate(kd):
        tk = 1 - sk / Lp
        ak = rng.uniform(0, 2 * PI)
        dk = rng.uniform(0.05, 0.07) if ik < 2 else rng.uniform(0.04, 0.07)   # the two lower knots 5-7 cm
        knots.append((tk, ak, dk))
        dda = np.abs((ang - ak + PI) % (2 * PI) - PI)
        R += 0.016 * np.exp(-(dda / 0.5) ** 2)[None, :] * np.exp(-((sdist - sk) / 0.09) ** 2)[:, None]
    ex = side
    ey = upv
    prof = np.stack([R * np.cos(ang)[None], R * np.sin(ang)[None]], -1)
    Pp = cen[:, None, :] + prof[..., 0:1] * ex + prof[..., 1:2] * ey
    # head: cut flush against the collar strap / boards (plane parallel to the face)
    face_pt = lean(g, face_map(g, k, np.array([0.0]), np.array([zatt]), np.array([0.064])))[0]
    dpl = (Pp - face_pt) @ nn_
    Pp -= np.clip(-dpl, 0, None)[..., None] * nn_
    # foot: three crisp axe-cut planes - heel cut bearing on the heel block, level seat on the sole,
    # and a 45 deg bevel taking off the heel's top corner
    stop = bot.copy()
    d1 = (Pp - stop) @ hz
    Pp -= np.clip(d1, 0, None)[..., None] * hz
    Pp[..., 2] = np.maximum(Pp[..., 2], Zf)
    n_up = unit(np.array([0, 0, 1.0]) - ax[2] * ax)          # the pole's upper surface normal
    n3 = unit(hz + n_up)
    p3 = stop + np.array([0, 0, Zf + 0.115 - stop[2]])
    d3 = (Pp - p3) @ n3
    Pp -= np.clip(d3, 0, None)[..., None] * n3
    Pp = Pp.reshape(1, -1, 3)
    T = tmpl_rings(n, m, cap0=True, cap1=True)
    Pp = add_caps(Pp, T)
    T = orient(T, Pp[0])
    P_p.add(Pp, T, mat="M_timber_weathered", smooth="all")
    # branch stubs (dia 4-7 cm, 2-4 cm proud, axe-trimmed flat ends), angled toward the tree top
    for tk, ak, dk in knots:
        jt = np.argmin(np.abs(t - tk))
        dirr = math.cos(ak) * ex + math.sin(ak) * ey
        base = cen[jt] + dirr * (rad[jt] - 0.01)
        out = unit(dirr * 0.85 - ax * 0.35)
        ln = 0.012 + rng.uniform(0.02, 0.04) / max(out @ dirr, 0.5)
        path = base + out * np.array([0.0, 0.25, 0.55, 0.85, 1.0])[:, None] * ln
        # flared boss -> broken stub with a ragged, slightly domed end
        rag = 1 + rng.uniform(-0.12, 0.12, 12)
        prof_k = np.array([circle_prof(dk / 2 * f, 12) * (rag[:, None] if f < 1.0 else 1.0)
                           for f in (1.7, 1.25, 1.02, 0.95, 0.75)])
        Pk, Tk = sweep(path[None], prof_k[None], up=ax)
        P_p.add(Pk, Tk, mat="M_timber_weathered", smooth="all")
    nknot_foot = int(sum(1 for sk in kd if sk <= 2.5))
    log("prop %d: %d rings x %d sides (ring spacing %.3f m), checks %s, knots %d (%d within 2.5 m of the foot)"
        % (idx, n, m, dt * Lp, checks, nk, nknot_foot))
    # ---- head: timber cleat under the pole, collar lugs (clevis ears) and a through-bolt ----
    Lt = g.LEAN_R @ tt_
    latc = float((top - lean(g, face_map(g, k, np.array([0.0]), np.array([zatt]), np.array([0.0])))[0]) @ Lt)
    cle = lean(g, face_map(g, k, np.array([latc]), np.array([zatt - 0.23]), np.array([0.095])))[0]
    member(P_p, 0, (cle - g.LEAN_R @ np.array([0, 0, 0.13]))[None], (cle + g.LEAN_R @ np.array([0, 0, 0.13]))[None],
           0.18, 0.09, up=nn_, c=0.015, rng=rng, bow=0.004)
    prof_b = np.array([(0.0, 0.0), (0.02, 0.0), (0.02, 0.009), (0.013, 0.014), (0.0, 0.015)])
    zear = (g.Z_COLLAR - 0.03 + zatt - 0.16) / 2
    hear = (g.Z_COLLAR - 0.03) - (zatt - 0.16)
    for sg in (-1, 1):
        lq = latc + sg * 0.092
        # lug plate lying on the collar strap, bolted through it
        a_ = lean(g, face_map(g, k, np.array([lq]), np.array([g.Z_COLLAR + 0.03]), np.array([0.068])))[0]
        b_ = lean(g, face_map(g, k, np.array([lq]), np.array([g.Z_COLLAR - 0.03]), np.array([0.068])))[0]
        member(P_i, "M_iron", a_[None], b_[None], 0.07, 0.010, up=nn_, c=0.002)
        bh = lean(g, face_map(g, k, np.array([lq]), np.array([g.Z_COLLAR + 0.005]), np.array([0.073])))
        Pb, Tb = lathe(prof_b[None], 6, open_base=True)
        Rb = frame_mats(Lt[None], np.cross(nn_, Lt)[None], nn_[None])
        P_i.add(xform(Pb, Rb, bh), Tb, mat="M_iron", smooth="none")
        # ear standing out from the face on each side of the pole head
        a_ = lean(g, face_map(g, k, np.array([lq]), np.array([zear]), np.array([0.058])))[0]
        b_ = lean(g, face_map(g, k, np.array([lq]), np.array([zear]), np.array([0.26])))[0]
        member(P_i, "M_iron", a_[None], b_[None], hear, 0.010, up=Lt, c=0.003)
    # through-bolt across the ears and the pole head, nuts outside
    ybolt = 0.175
    pa = lean(g, face_map(g, k, np.array([latc - 0.115]), np.array([zatt - 0.08]), np.array([ybolt])))[0]
    pb = lean(g, face_map(g, k, np.array([latc + 0.115]), np.array([zatt - 0.08]), np.array([ybolt])))[0]
    Pbt, Tbt = sweep(np.stack([pa, pb])[None], circle_prof(0.011, 8), up=nn_)
    P_i.add(Pbt, Tbt, mat="M_iron", smooth="all")
    for sg, pq in ((-1, pa), (1, pb)):
        Pb, Tb = lathe(prof_b[None], 6, open_base=True)
        Rb = frame_mats(nn_[None], np.cross(Lt * sg, nn_)[None], (Lt * sg)[None])
        P_i.add(xform(Pb, Rb, (pq - Lt * sg * 0.018)[None]), Tb, mat="M_iron", smooth="none")
    # strap band around the pole below the head
    for o in (0.32,):
        c = top + ax * o
        a = np.linspace(0, 2 * PI, 21)[:-1]
        rr = 0.077 + 0.025 * o / Lp + 0.006
        ring = c + rr * (np.cos(a)[:, None] * ex + np.sin(a)[:, None] * ey)
        Pr, Tr = sweep(ring[None], rect_prof(0.006, 0.045, 0.002), up=ax, closed=True)
        P_i.add(Pr, Tr, mat="M_iron", smooth="bevel")
    # ---- ground (round 4): one hewn chock seated in a notch cut into a rough split-stone pad, iron dogs
    # from the chock onto the pole, and a soil mound round the pad with a few embedded pebbles ----
    def pole_at(z, top=top, axis=axis, side=side, bow=bow):
        tq = (top[2] - z) / (top[2] - bot[2])
        return top + axis * tq + side * bow * math.sin(min(tq, 1.0) * PI), 0.075 + 0.025 * min(tq, 1.0)
    prop_foot(P_a, rng, bot, hz, Zf, idx, pole_at)
    return top, bot


def build_props(g, parts, props=None):
    """The mill's prop set: `props` = [(tower face k, lateral offset, attach z, foot (x, y)), ...]; default: two
    near-parallel long props from just under the collar on the -X face and a shorter one on the -X/-Y face."""
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = g.RNG("props")
    defs = []
    zc = g.Z_COLLAR - 0.11
    if props is None:
        props = ((6, 0.36, zc, (-6.3, -1.2)), (6, -0.36, zc, (-6.0, 0.9)), (6, 0.62, float(TZ(g, 7.30)), (-6.0, -3.1)))
    for (k, lat, z, gnd) in props:
        top = face_map(g, k, np.array([lat]), np.array([z]), np.array([0.14]))[0]
        defs.append((lean(g, top[None])[0], np.array([gnd[0], gnd[1], 0.19]), k, z))
    Zf = 0.08                                   # round 5: seat of the sunk chock (pad top ~5 cm)
    for idx, (top, bot, k, zatt) in enumerate(defs):
        raking_prop(g, parts, top, bot, k, zatt, idx, rng, Zf)
    # cross brace between the two long props at ~3 m with bolts
    def at_z(top, bot, z):
        tt = (top[2] - z) / (top[2] - bot[2])
        return top + (bot - top) * tt
    a = at_z(defs[0][0], defs[0][1], 3.1)
    b = at_z(defs[1][0], defs[1][1], 3.3)
    member(P_p, 0, a[None], b[None], 0.11, 0.09, up=(0, 0, 1), c=0.015, rng=rng, bow=0.02)
    return defs


def raking_props(g, props=None, seed=None):
    """Raking timber props (kit component): `props` = [(tower face k, lateral offset, attach z, foot (x, y)), ...]
    (default: two near-parallel long props from under the collar on the -X face and a shorter one on the -X/-Y
    face, as in ref1) -- bowed knotted poles with cleats, collar lugs and through-bolts, bedded pads with sunk
    chocks and iron dogs, and a bolted cross brace (<PREFIX>_props / _prop_anchors / _prop_iron)."""
    with g.seeded(seed):
        return build_props(g, g.parts, props)
