"""components.shake_apron -- the conical split-shake apron between a stone drum and its timber tower (kit 1.2.0).

Public component: shake_apron(g, r_eave, z_eave, r_top, z_top, courses, seed).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (TZ, face_axes, tw_a)  # noqa: F401
from ..tmplmesh import (D2R, PI, T_BRD, T_SHK, T_SHK2, T_SHK2_O, add_grid, cone_frame, log, member, orient, rbox,
    rotm, xform)  # noqa: F401


def shingle_local(rng, L, W, tb, tt, jag=0.012, curl=0.012, cup=0.004, comb=0.0, T=T_SHK):
    """Shingle: x = length (butt at -L/2), y = thickness from 0 (bed) up, z = width."""
    N = len(L)
    h = np.stack([L / 2, np.full(N, 0.01), W / 2], 1)
    P = rbox(T, h, np.stack([np.full(N, 0.006), np.full(N, 0.004), np.full(N, 0.006)], 1))
    u = P[:, :, 0] / h[:, None, 0]
    vz = P[:, :, 2] / h[:, None, 2]
    th = tb[:, None] + (tt - tb)[:, None] * (u + 1) / 2
    P[:, :, 1] = (P[:, :, 1] / 0.01 + 1) / 2 * th
    bw = (1 - u) / 2
    a1 = rng.uniform(-jag, jag, N)[:, None]
    a2 = rng.uniform(-jag, jag, N)[:, None]
    f2 = rng.uniform(1.5, 4.0, N)[:, None]
    P[:, :, 0] += (a1 * vz + a2 * np.sin(vz * f2 + a1 * 50)) * bw ** 3
    if comb > 0:
        P[:, :, 0] += rng.uniform(-comb, comb * 0.4, N)[:, None] * ((u + 1) / 2) ** 3 \
                      + rng.uniform(-comb, comb, N)[:, None] * 0.4 * vz * ((u + 1) / 2) ** 3
    P[:, :, 1] += rng.uniform(0, curl, N)[:, None] * bw ** 2 + rng.uniform(-cup, cup, N)[:, None] * vz ** 2
    return P


def shake_local(rng, L, W, tb=(0.025, 0.035), tt=0.008, comb=0.0, T=None):
    """Split shake (T_SHK2): x = length (butt at -L/2), y = thickness from the bed up, z = width.
    Thickness tapers from a 2.5-3.5 cm butt to a 0.8 cm head; split, tapered outline (each long edge
    wanders +-2 cm and the head is narrower); slight cup or crown; ragged, uneven butt."""
    N = len(L)
    T = T_SHK2 if T is None else T
    h = np.stack([L / 2, np.full(N, 0.01), W / 2], 1)
    P = rbox(T, h, np.stack([np.full(N, 0.005), np.full(N, 0.003), np.full(N, 0.005)], 1))
    u = P[:, :, 0] / h[:, None, 0]               # -1 butt .. +1 head
    s = (u + 1) / 2                               # 0 butt .. 1 head
    vz = P[:, :, 2] / h[:, None, 2]               # -1 .. 1 across
    tbv = rng.uniform(*tb, N)
    th = tbv[:, None] + (tt - tbv)[:, None] * s
    P[:, :, 1] = (P[:, :, 1] / 0.01 + 1) / 2 * th
    # outline: head narrower, each edge wanders independently (split timber)
    taper = rng.uniform(0.0, 0.16, N)[:, None]
    e1 = rng.uniform(-0.02, 0.02, (N, 3))
    e2 = rng.uniform(-0.02, 0.02, (N, 3))
    def edge(e):
        return e[:, 0:1] * s + e[:, 1:2] * np.sin(s * PI) + e[:, 2:3] * np.sin(s * 2 * PI) * 0.5
    side = np.where(vz > 0, 1.0, -1.0)
    wid = (1 - taper * s) * np.abs(P[:, :, 2])
    # edges only ever wander inward (split timber never grows into its neighbour -> no interpenetration;
    # the widened gaps show the offset under-layer)
    off = -np.abs(np.where(vz > 0, edge(e1), edge(e2))) * np.clip(np.abs(vz), 0, 1)
    P[:, :, 2] = side * (wid + off)
    # ragged butt: piecewise steps across the width
    k = rng.uniform(-0.025, 0.02, (N, 4))
    zi = np.clip(((vz + 1) / 2 * 3.999).astype(int), 0, 3)
    jag = np.take_along_axis(k, zi, 1)
    P[:, :, 0] += jag * np.clip(1 - s * 2.5, 0, 1)
    if comb > 0:
        P[:, :, 0] += rng.uniform(-comb, comb * 0.4, N)[:, None] * s ** 3
    # cup / crown and a slight curl at the butt
    P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (vz ** 2 - 0.33) + \
        rng.uniform(0, 0.01, N)[:, None] * np.clip(1 - s * 3, 0, 1) ** 2
    return P


def apron_wave(phi):
    """Eave line wanders +-3 cm (low frequency) and the skirt sags ~1.5 cm between the 32 rafters."""
    phi = np.asarray(phi, float)
    return 0.018 * np.sin(2 * phi + 0.7) + 0.012 * np.sin(5 * phi + 2.1) - 0.015 * np.sin(16 * phi) ** 2


def eave_fascia(part, rng, r_out, z_top, n=16, t=0.03, H=(0.14, 0.18), wave_fn=None):
    """Polygonal eave fascia (kit component): n straight boards (0.9-1.3 m chords), 2.5-3.5 cm thick, 14-18 cm
    deep, butt joints with 3-6 mm gaps and ends cut to the polygon; +-5 mm height and +-3 mm out-of-plane per
    board, worn lower arris, following the low-frequency eave wave. r_out: outer-face radius at the polygon
    vertices; z_top: top edge height. Returns the vertex angles and the inner-face radius per vertex (the
    sarking edge)."""
    wave_fn = apron_wave if wave_fn is None else wave_fn
    base = rng.uniform(0, 2 * PI / n)
    w_ = rng.uniform(0.8, 1.2, n)
    ang = base + np.concatenate([[0], np.cumsum(w_)[:-1]]) / w_.sum() * 2 * PI
    nxt = np.append(ang[1:], ang[0] + 2 * PI)
    Z3 = np.array([0, 0, 1.0])
    d_in = np.zeros(n)
    for k in range(n):
        a0, a1 = ang[k], nxt[k]
        half = (a1 - a0) / 2
        am = (a0 + a1) / 2
        nrm = np.array([math.sin(am), -math.cos(am), 0.0])
        tan = np.cross(nrm, Z3)
        tk = rng.uniform(0.025, 0.035)
        Hk = rng.uniform(*H)
        d_out = r_out * math.cos(half)
        L = 2 * r_out * math.sin(half) - rng.uniform(0.003, 0.006)
        h = np.array([[L / 2, tk / 2, Hk / 2]])
        P = rbox(T_BRD, h, np.array([[0.004, 0.004, 0.004]]))
        yl = P[0, :, 1].copy()
        # worn lower outer arris (8-14 mm), varying along the board
        wr = rng.uniform(0.008, 0.014) * (1 + 0.3 * np.sin(P[0, :, 0] * 7 + k))
        on_face = yl > tk / 2 - 1e-6
        on_bot = P[0, :, 2] < -Hk / 2 + 1e-6
        low = P[0, :, 2] < -(Hk / 2 - 0.004) + 1e-6
        outr = yl > tk / 2 - 0.004 - 1e-6
        P[0, :, 2] = np.where(on_face & low, np.maximum(P[0, :, 2], -(Hk / 2 - wr)), P[0, :, 2])
        P[0, :, 1] = np.where(on_bot & outr, np.minimum(P[0, :, 1], tk / 2 - wr * 0.8), P[0, :, 1])
        # ends cut to the polygon (mitre along the radial bisector): the inner face is shorter
        P[0, :, 0] += np.sign(P[0, :, 0]) * (P[0, :, 1] - tk / 2) * math.tan(half)
        # out of plane +-3 mm, height +-5 mm, eave wave (linear between the board's end vertices)
        u = P[0, :, 0] / (L / 2)
        P[0, :, 1] += rng.uniform(-0.003, 0.003) + rng.uniform(-0.002, 0.002) * u
        zw = (wave_fn(a0) * (1 - u) + wave_fn(a1) * (1 + u)) / 2 * 0.97
        ctr = nrm * (d_out - tk / 2) + np.array([0, 0, z_top - Hk / 2 + rng.uniform(-0.005, 0.005)])
        W = P[0] @ np.stack([tan, nrm, Z3], 1).T + ctr
        W[:, 2] += zw
        part.add(W[None], T_BRD, Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.6)
        d_in[k] = d_out - tk - 0.004

    def r_edge(phi):
        """radius of the fascia's inner face (polygon) at azimuth phi -> the sarking edge"""
        phi = np.asarray(phi, float)
        k = (np.searchsorted(ang, (phi - ang[0]) % (2 * PI) + ang[0], side="right") - 1) % n
        am = (ang[k] + nxt[k]) / 2
        return d_in[k] / np.cos(((phi - am + PI) % (2 * PI)) - PI)
    return ang[0], r_edge


def tower_foot_flashing(g, part, rng, bed_fn, z_top=None):
    """One vertical flashing board per octagon face over the tower sill (kit component), its lower edge scribed
    to the shakes, ends lapped over the neighbours (alternate boards stand 2.6 cm further out)."""
    z_sill = float(TZ(g, 5.41))
    z_top = z_sill + 0.165 if z_top is None else z_top
    for k in range(8):
        n_, t_ = face_axes(k)
        d = float(tw_a(g, z_sill)) - 0.03 + 0.12 + 0.006 + (0.026 if k % 2 else 0.0)
        L = 2 * d * math.tan(PI / 8) + (0.09 if k % 2 else 0.02)
        tk = rng.uniform(0.022, 0.028)
        h = np.array([[L / 2, tk / 2, 0.5]])
        P = rbox(T_BRD, h, np.array([[0.004, 0.004, 0.01]]))
        x = P[0, :, 0]
        r = np.hypot(d + tk / 2, x)
        # round 5: STRAIGHT drip edge at the level the shakes reach at the board ends; the top shake course
        # tucks under the board (no scalloped scribed frill seen from above)
        zb = float(bed_fn(r).min()) + 0.03 + rng.uniform(-0.003, 0.003) + 0.002 * x / (L / 2)
        zt = z_top + rng.uniform(-0.006, 0.006) + 0.004 * x / (L / 2)
        zz = zb + (P[0, :, 2] + 0.5) * (zt - zb)
        W = (d + tk / 2 + P[0, :, 1] + rng.uniform(-0.002, 0.002))[:, None] * n_ + x[:, None] * t_ + \
            zz[:, None] * np.array([0, 0, 1.0])
        part.add(W[None], orient(T_BRD, W), Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.55)


def build_apron(g, parts):
    P_c, P_s, P_r = parts["curb"], parts["apron"], parts["apron_frame"]
    rng = g.RNG("apron")
    ca, sa = math.cos(g.AP_A), math.sin(g.AP_A)
    # stone kerb inside (carries the tower sill; hidden behind rafters)
    # (the stone kerb under the tower sill is fully enclosed by the apron: not modelled)
    # timber curb on the cornice (16 lapped segments, 0.22 x 0.24)
    n = 16
    rc = 2.30
    ph = np.arange(n) * 2 * PI / n + rng.uniform(-0.01, 0.01, n)
    a = np.stack([rc * np.sin(ph - PI / n - 0.05), -rc * np.cos(ph - PI / n - 0.05), np.full(n, 4.62 + g.DZ)], 1)
    b = np.stack([rc * np.sin(ph + PI / n + 0.05), -rc * np.cos(ph + PI / n + 0.05), np.full(n, 4.62 + g.DZ)], 1)
    # (the curb ring is wholly enclosed under the apron: not modelled)
    # rafters (32) from the kerb to past the eave
    nr = 32
    ph = (np.arange(nr) + 0.5) * 2 * PI / nr

    def bed(r):
        return g.AP_ZE + (g.AP_RE - r) * math.tan(g.AP_A)
    rr0, rr1 = g.AP_RE - 0.67, g.AP_RE - 0.05   # rafter feet only: above the cornice they are enclosed by the apron
    off = -0.025 - 0.02 - 0.06  # below batten + sarking, centre of a 0.12 rafter
    er0 = np.stack([np.sin(ph), -np.cos(ph), np.zeros(nr)], 1)
    nn = np.stack([sa * er0[:, 0], sa * er0[:, 1], np.full(nr, ca)], 1)
    a = er0 * rr0 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr0))], 1) + nn * off
    b = er0 * rr1 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr1))], 1) + nn * off
    member(P_r, "M_timber", a, b, 0.08, 0.12, up=(0, 0, 1), c=0.012, rng=rng, bow=0.01)
    # eave fascia (round 4): 16 straight boards on a polygon, butt-jointed, ends cut to the polygon, eave wave
    a_first, r_edge_fn = eave_fascia(P_r, rng, g.AP_RE + 0.0, bed(g.AP_RE) - 0.025, n=16)
    # sarking: a closed board shell (2 cm) from the tower foot out to the fascia's inner face (polygonal edge,
    # following the eave wave) -> no see-through, and its end grain is covered by the fascia
    na = 16 * 9
    aa = np.linspace(0, 2 * PI, na, endpoint=False) + a_first
    r_edge = r_edge_fn(aa)
    fr_ = np.linspace(0, 1, 6)
    R_ = (g.AP_RT - 0.05) + (r_edge[:, None] - (g.AP_RT - 0.05)) * fr_[None]
    wave_ = apron_wave(aa)[:, None] * np.clip(1 - (g.AP_RE - R_) / ca / 2.0, 0, 1)
    Zt = bed(R_) - 0.025 + wave_
    top = np.stack([R_ * np.sin(aa)[:, None], -R_ * np.cos(aa)[:, None], Zt], 2)
    bot = top - np.array([0, 0, 0.022])
    add_grid(P_r, "M_timber", top, wrap=True, flip=True, smooth="none")
    add_grid(P_r, "M_timber", bot, wrap=True, flip=False, smooth="none")
    add_grid(P_r, "M_timber", np.stack([bot[:, -1], top[:, -1]], 1), wrap=True, flip=True, smooth="none")
    # tower-foot flashing: one vertical board per octagon face over the sill, scribed to the shakes, lapped
    tower_foot_flashing(g, P_r, rng, bed)
    # shakes: 3 visible courses, each double layered (offset under-layer), long split shakes.
    # Lift per layer is a fixed offset normal to the bed (no per-shake pitch blow-up), the under-layer is
    # complete, and only isolated top-layer shakes are missing (exposing the under-layer).
    slope_len = (g.AP_RE - g.AP_RT) / ca
    # AP_COURSES visible courses of 0.72-0.84 m shakes (3 over this mill's 2.09 m slope at 41 deg)
    courses = [i * (slope_len - 0.73) / max(g.AP_COURSES - 1, 1) for i in range(g.AP_COURSES)]
    stats = 0
    for ci, sb in enumerate(courses):
        rb_ = g.AP_RE - sb * ca
        C = 2 * PI * rb_
        for layer in (1,):          # single layer (the under-layer was ~all hidden); sarking shows in the gaps
            widths, gaps = [], []
            tot = 0
            while tot < C:
                widths.append(rng.uniform(0.14, 0.22))
                gaps.append(rng.uniform(0.005, 0.015))
                tot += widths[-1] + gaps[-1]
            widths = np.array(widths) * C / tot
            gaps = np.array(gaps) * C / tot
            # centres include every gap -> the ring closes evenly (no leftover hole at azimuth 0)
            phc = (np.cumsum(widths + gaps) - gaps - widths / 2) / C * 2 * PI + \
                (0.5 * widths.mean() / rb_ if layer == 0 else 0) + ci * 0.37
            phc += rng.uniform(-0.004, 0.004, len(phc))
            N = len(phc)
            if ci < 2:
                L = rng.uniform(0.74, 0.84, N)
                comb = 0.0
            else:
                # top course: reach the tower face (octagon) with a ragged comb top
                a_t = g.AP_RT - 0.02
                rel = (phc + PI / 8) % (PI / 4) - PI / 8
                r_face = a_t / np.cos(rel) + 0.012
                L = np.clip((rb_ - r_face) / ca + rng.uniform(-0.01, 0.06, N), 0.3, None)
                comb = 0.04
            sbb = sb - (0.04 if layer == 0 else 0.0) - (0.045 if ci == 0 else 0.0) + rng.uniform(-0.02, 0.02, N)
            W = widths * rng.uniform(0.93, 1.0, N)
            Tsh = T_SHK2_O               # the sarking runs out past every eave butt, so no bed face is ever seen
            P = shake_local(rng, L, W, comb=comb, T=Tsh)
            # a few slipped shakes (2-3 %) hang 4-7 cm low instead of leaving holes
            slip = rng.random(N) < 0.025
            sbb = sbb - np.where(slip, rng.uniform(0.04, 0.07, N), 0.0)
            keep = np.ones(N, bool)
            # lift: courses below (butt) -> straight plane, slight pitch only
            ob = 0.004 + (0.028 if ci > 0 else 0.0)
            ot = 0.002
            beta = np.arctan2(ob - ot, np.maximum(L, 0.6)) + rng.uniform(-0.004, 0.008, N)
            Rf, er, nrm = cone_frame(phc, g.AP_A)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rng.normal(0, 2.0 * D2R, N))
            sc = sbb + L / 2
            wave = apron_wave(phc) * np.clip(1 - sc / 2.0, 0, 1)
            ctr = er * (g.AP_RE - sc * ca)[:, None] + np.stack([0 * sc, 0 * sc, g.AP_ZE + sc * sa + wave], 1) \
                + nrm * ((ob + ot) / 2 + rng.uniform(-0.002, 0.004, N))[:, None]
            Wd = xform(P, Rf @ Rl, ctr)
            P_s.add(Wd[keep], Tsh, Pl=P[keep], mat="M_roof_shake", smooth="bevel")
            stats += keep.sum()
    log("apron shakes", stats)


def shake_apron(g, r_eave=None, z_eave=None, r_top=None, z_top=None, courses=None, seed=None):
    """Conical split-shake apron (kit component) from the cornice eave (r_eave, z_eave) up to the tower foot
    (r_top, z_top) in `courses` courses of long split shakes (village_kit.shingles SIZE_TABLE['shake']), with
    rafter feet, a closed sarking shell, a polygonal eave fascia and the tower-foot flashing boards."""
    kw = {k_: v_ for k_, v_ in (("AP_RE", r_eave), ("AP_ZE", z_eave), ("AP_RT", r_top), ("AP_ZT", z_top),
                                ("AP_COURSES", courses)) if v_ is not None}
    g.set(**kw)
    with g.seeded(seed):
        build_apron(g, g.parts)
