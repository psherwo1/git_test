"""components.finial -- apex "lead hat" collar and finials.

build_collar_finial(g)  lead-hat collar (smooth cone with drip fascia, rolled bead, standing seams), bell-cast
                        upper collar, turned spindle and iron spike (style "spike")
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import ccw, lathe, n2, rotx, roty, tube


def collar_drip_z(g, clear=0.02):
    """lowest fascia-bottom height that clears every shingle vertex under the 53 deg collar."""
    V = g.SHINGLE_TOP["V"]
    r = np.hypot(V[:, 0], V[:, 1])
    m = r < g.COLLAR_R + 0.03
    need = V[m, 2] - np.maximum(g.COLLAR_R - r[m], 0.0) * math.tan(g.COLLAR_PITCH) * 0.97
    return float(need.max()) + clear


def build_collar_finial(g, coll):
    """lead-hat collar (smooth 53 deg cone, dia 1.49, 6.5 cm drip fascia standing ~8 cm off the
    shingles, rolled drip bead, 10 folded standing seams), bell-cast upper collar (dia 0.57) with its
    own 4.5 cm drip, turned spindle (bead ring 0.20 / neck 0.10 / bulb 0.18) and a conical spike.
    Upper collar + finial lean 1 deg."""
    acc = g.acc("cap_collar", 50)
    fin = g.acc("finial", 50)
    R = g.COLLAR_R
    tp = math.tan(g.COLLAR_PITCH)
    zf = collar_drip_z(g)                     # fascia bottom (drip line)
    FD = 0.065                               # fascia depth
    zd = zf + FD                             # where the cone surface meets the fascia top
    r_top = 0.25
    z_top = zd + (R - r_top) * tp
    seed = 808

    def dent(th, z):
        # producer note 11: the 3-5 mm dents of the lead are sub-threshold relief (decals / normal maps)
        k_ = 0.0 if g.detail.active else 1.0
        return 1 + k_ * (0.007 * n2(th * 2.2, np.full_like(th, z * 3), seed) + 0.003 * n2(th * 7, np.full_like(th, z * 9), seed + 1))

    # CCW in (r,z): underside (from the axis outward), fascia inner face, drip bead, fascia, cone
    under = [(0.0, zf + 0.70)] + [(r_, zf + 0.012 + (R - r_) * tp * 0.97) for r_ in np.linspace(0.4, R - 0.03, 2)]
    prof = under + [(R - 0.018, zf + 0.04), (R - 0.016, zf + 0.012),
            (R - 0.012, zf + 0.001), (R - 0.002, zf - 0.004), (R + 0.008, zf + 0.0), (R + 0.0135, zf + 0.009),
            (R + 0.012, zf + 0.019), (R + 0.004, zf + 0.026), (R + 0.0015, zf + 0.035), (R + 0.001, zd - 0.012),
            (R - 0.002, zd - 0.003), (R - 0.009, zd + 0.004)]
    for f in np.linspace(0.04, 1.0, 14):
        rr = (R - 0.012) - (R - 0.012 - r_top + 0.0) * f
        prof.append((rr, zd + (R - rr) * tp))
    prof.append((0.2, z_top + 0.01))
    prof.append((0.0, z_top + 0.02))
    V, F, uv, w = lathe(prof, 128, rfunc=dent)
    acc.add(V, F, "M_lead", uv, w)
    # folded standing seams (raised 6-8 mm fins with soft fillets), 10 of them
    fin_prof = ccw([(-0.003, 0.0), (-0.0012, 0.013), (0.0018, 0.0058), (0.0052, 0.0034), (0.0074, 0.0014),
                    (0.0076, -0.0012), (0.0054, -0.0032), (0.002, -0.0056), (-0.0012, -0.013)])
    for k in range(10):
        th = 2 * np.pi * k / 10 + 0.13 + 0.03 * math.sin(k * 2.7)
        rr = np.linspace(R - 0.02, r_top + 0.01, 16)
        zz = zd + (R - rr) * tp
        dd = dent(np.full_like(rr, th), zz)
        path = np.stack([np.cos(th) * rr * dd, np.sin(th) * rr * dd, zz], -1)
        nrmv = np.array([math.cos(th) * math.sin(g.COLLAR_PITCH), math.sin(th) * math.sin(g.COLLAR_PITCH),
                         math.cos(g.COLLAR_PITCH)])
        path = path + nrmv * 0.001
        P, Fp, uvp, wp = tube(path, 1.0, len(fin_prof), up=tuple(nrmv), profile=fin_prof)
        acc.add(P, Fp, "M_lead", uvp, wp)
    # ---- upper collar (bell-cast), leaning 1 deg with the finial
    lean = rotx(math.radians(0.75)) @ roty(math.radians(-0.65))
    piv = np.array([0.0, 0.0, z_top])
    ru = 0.285
    zu0 = z_top - 0.03                       # its drip bottom (4.5 cm fascia)
    zu1 = zu0 + 0.045
    H_u = 0.30
    prof_u = [(0.0, z_top - 0.02), (ru - 0.03, zu0 + 0.012), (ru - 0.014, zu0 + 0.004), (ru - 0.006, zu0 - 0.002),
              (ru + 0.005, zu0 + 0.002), (ru + 0.009, zu0 + 0.01), (ru + 0.006, zu0 + 0.018),
              (ru + 0.001, zu0 + 0.024), (ru, zu1 - 0.006), (ru - 0.005, zu1 + 0.002)]
    for f in np.linspace(0.06, 1.0, 10):           # straight 54 deg cone, r 0.285 -> 0.07 over 0.30 m
        r_ = 0.07 + (ru - 0.012 - 0.07) * (1 - f)
        prof_u.append((r_, zu1 + (H_u - 0.015) * f))
    z_s = zu1 + H_u - 0.015
    prof_u.append((0.0, z_s + 0.004))
    V, F, uv, w = lathe(prof_u, 64, rfunc=lambda th_, z_: 1 + 0.005 * np.sin(2 * th_ + 0.4))
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_lead", uv, w)
    # ---- turned spindle (timber), ref2's stack: bead ring -> tapered spindle -> ring
    sp = [(0.0, z_s - 0.01), (0.068, z_s - 0.01), (0.082, z_s + 0.004),                                # seat
          (0.096, z_s + 0.018), (0.101, z_s + 0.036), (0.097, z_s + 0.054), (0.08, z_s + 0.066),       # bead ring
          (0.066, z_s + 0.076), (0.064, z_s + 0.12), (0.059, z_s + 0.2), (0.053, z_s + 0.28),          # tapered spindle
          (0.052, z_s + 0.3), (0.07, z_s + 0.312), (0.094, z_s + 0.328), (0.1, z_s + 0.346),           # ring
          (0.097, z_s + 0.366), (0.085, z_s + 0.379), (0.0, z_s + 0.385)]
    V, F, uv, w = lathe(sp, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_timber", uv, w)
    # ---- spike (iron): base dia 0.19, knop ring ~0.2 m up, straight taper to a sharp point
    z_k = z_s + 0.383
    tip = max(g.FINIAL_TIP if g.FINIAL_TIP is not None else z_k + 0.95, z_k + 0.6)
    Hs = tip - z_k
    rb_ = 0.095

    def r_sp(h):
        return rb_ * (1 - h / Hs) + 0.0008
    hk = 0.2
    spk = [(0.0, z_k - 0.003), (rb_ - 0.004, z_k - 0.003), (rb_, z_k + 0.004), (r_sp(0.012), z_k + 0.012),
           (r_sp(hk - 0.02), z_k + hk - 0.02), (r_sp(hk - 0.014) + 0.013, z_k + hk - 0.012),
           (r_sp(hk) + 0.015, z_k + hk), (r_sp(hk + 0.014) + 0.013, z_k + hk + 0.012),
           (r_sp(hk + 0.02), z_k + hk + 0.02)]
    for f in np.linspace(0.0, 1.0, 9)[1:]:
        h = hk + 0.02 + (Hs - 0.006 - hk - 0.02) * f
        spk.append((r_sp(h), z_k + h))
    spk += [(0.0, tip)]
    V, F, uv, w = lathe(spk, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_iron", uv, w)
    acc.build(coll)
    fin.build(coll)
    return zf, zd, z_top, z_s, z_k, tip


FINIAL_STYLES = ("spike",)        # extension point: "ball" (stone round ends), "turned" (keep), "vane" ...


def finial(g, style="spike"):
    """KIT COMPONENT: apex collar + finial on the cone of frame g.  style 'spike': lead-hat collar (g.COLLAR_R,
    g.COLLAR_PITCH, drip fascia clearing the top shingles), bell-cast upper collar, turned spindle and iron spike to
    g.FINIAL_TIP (None: spindle + 0.95 m); the upper parts lean ~1 deg.  Objects <PREFIX>_cap_collar / _finial.
    Must run after the shingles (the drip height is fitted to them)."""
    if style not in FINIAL_STYLES:
        raise ValueError(f"finial style {style!r} not in the kit yet ({FINIAL_STYLES})")
    from ..core import log
    zz = build_collar_finial(g, g.coll)
    log("collar drip %.3f fascia top %.3f lower top %.3f upper top %.3f spindle top %.3f tip %.3f" % zz)
    return zz


lead_hat_finial = finial


# ---------------------------------------------------------------------------------------------------------------
# kit 1.1.0 (hilltop keep): the "turned" style -- a turned / forged finial over a lead hat on a bell cap apex
# ---------------------------------------------------------------------------------------------------------------
TURNED_PROFILE = np.array([
    (0.10, 0.0), (0.105, 0.09), (0.128, 0.105), (0.128, 0.14), (0.075, 0.16), (0.08, 0.21), (0.105, 0.26),
    (0.112, 0.31), (0.105, 0.35), (0.06, 0.41), (0.048, 0.43), (0.068, 0.445), (0.068, 0.465), (0.048, 0.48),
    (0.066, 0.495), (0.066, 0.512), (0.042, 0.53), (0.05, 0.57), (0.072, 0.63), (0.076, 0.67), (0.068, 0.72),
    (0.045, 0.79), (0.024, 0.86), (0.021, 0.9), (0.032, 0.915), (0.032, 0.94), (0.019, 0.96), (0.015, 1.05),
    (0.010, 1.2), (0.004, 1.38), (0.0, 1.45)])
"""(r, z) of the keep's main finial at scale 1 (1.45 m): socket collar, ring, bulb, two thin rings, onion /
teardrop, neck, tapering spike."""


def turned_finial(acc, base, scale=1.0, lean_deg=1.0, lean_dir=(0.6, -0.8), seg=28):
    """FINIAL STYLE "turned": the turned / forged finial (TURNED_PROFILE x scale) standing at `base`, leaning
    lean_deg toward lean_dir (a shear proportional to height), M_iron."""
    from ..geom import lathe_rz
    V, F = lathe_rz(TURNED_PROFILE * scale, seg, cap_bottom=True, cap_top=False)
    a = math.radians(lean_deg)
    d = np.array([lean_dir[0], lean_dir[1], 0.0])
    d /= np.linalg.norm(d)
    V = V + d[None] * (V[:, 2:3] * math.tan(a))
    acc.add(V + np.asarray(base, float)[None], F, "M_iron")


def lead_hat(acc, cx, cy, z_apex, r0, h0, seg=28, cover=None, clear=0.02):
    """lead hat over a cap apex: a shallow lead cone of radius r0 with a rolled drip edge h0 below the apex.
    cover: optional (N, 3) vertices of the covering under it (e.g. the chunky cap shingles); the drip edge and the
    cone are then lowered / raised so that every covering vertex inside r0 stays `clear` under the lead (no shingle
    pokes through the hat).  Returns the height of the hat top (where the finial stands)."""
    from ..geom import lathe_rz
    z_top = z_apex + 0.05
    if cover is not None and len(cover):
        r_v = np.hypot(cover[:, 0] - cx, cover[:, 1] - cy)
        m = r_v < r0 + 0.04
        if m.any():
            z_v, r_v = cover[m, 2], r_v[m]
            z_top = max(z_top, float(z_v[r_v < 0.10].max(initial=-1e9)) + clear + 0.03)
            # the cone from (0.09, z_top - 0.03) down to (r0, z_apex - h0 + 0.02) must pass over every vertex
            for _ in range(60):
                zr = z_apex - h0 + 0.02
                t_ = np.clip((r_v - 0.09) / max(r0 - 0.09, 1e-3), 0, 1)
                z_cone = (z_top - 0.03) * (1 - t_) + zr * t_
                need = float((z_v + clear - z_cone).max())
                if need <= 0:
                    break
                h0 = h0 - min(need, 0.02)
    prof = [(r0 + 0.02, -h0 - 0.01), (r0 + 0.025, -h0 + 0.012), (r0, -h0 + 0.02),
            (r0 * 0.55, -h0 * 0.45 + 0.45 * (z_top - z_apex - 0.05)), (0.09, z_top - z_apex - 0.03),
            (0.085, z_top - z_apex), (0.0, z_top - z_apex)]
    V, F = lathe_rz(prof, seg, cx=cx, cy=cy, z0=z_apex, cap_bottom=True, cap_top=False)
    acc.add(V, F, "M_lead")
    return z_top
