"""components.square_cabin -- a SQUARE TIMBER LOOKOUT CABIN perched on a round (or any) wall head, with its own
square-pyramid shingle roof (kit changes v1_stone_watchtower round 2; new module, nothing existing changed).

    square_cabin(g, side=5.4, height=2.30, z_bed=None, bearers=(-1.6, 0.0, 1.6), n_joists=7, struts=True,
                 strut_drop=1.25, n_open=2, open_w=1.10, open_sill=1.00, open_h=0.90, pitch_deg=48.0, eave_out=0.50,
                 exposure=0.34, cap_r=0.62, seed=None)

A gatehouse loft, a harbour look-out or a watchtower cabin from one call.  The cabin's square plan is centred on
the z axis, its sides face -Y / +X / +Y / -X (the entrance side of the building is -Y).  It sits on a wall head at
z_bed (default: the drum family's cornice top, tower_roof.drum_top) whose bed ring is `bed_r` (default the drum's
cornice cap).  Built and carried:

  floor      bearers (along Y) bedded on the wall head, joists (along X) on the bearers, cantilevered out to the
             square, a plank floor deck; a mortar bed disc closes the wall head under the floor
  brackets   a dragon beam out to every corner of the floor, each carried by a raking timber knee strut in the
             diagonal plane, its foot on a dressed stone corbel pad set into the wall face `strut_drop` m below the bed
  walls      a framed wall: sill, corner posts, opening jamb posts, a breast rail with a weathered sill board, a head
             beam and a top plate (half-lapped at the corners: no coplanar faces), vertical plank infill below the
             rail, between the openings and over the heads; `n_open` real lookout openings on EVERY side, open
             through the cabin; a boarded ceiling at the plate (the roof void is closed)
  roof       r4: NOT built here any more -- the kit's components.pyramid_roof.pyramid_roof (sides=4) on the plate,
             parameters `pitch_deg`, `eave_out`, `exposure`, `cap_r`, `finial_scale` plus any `roof=dict(...)`
             overrides (bell_deg / bell_len bell-cast eave, kick, sag, ...); `roof_fn` swaps in another roof module.
             bell_deg=0 (the default) is the round-3 straight pyramid.
  bed fill   r4: `bed_fill=True` closes the floor sandwich over the wall head with a timber rim ring (blocking
             between bearers and joists) from the bed to the deck underside

Objects <P>_cabin_floor / _cabin_struts / _cabin_corbels / _cabin_bed / _cabin_frame / _cabin_boards /
_cabin_ceiling / _cabin_roof_frame / _cabin_roof_deck / _cabin_shingles / _cabin_hips / _cabin_lead / _cabin_finial.
Publishes g.CABIN and g.ROOF (r_eave / z_eave / tip: tower_roof.tower_views and the decal pass read them).
"""
import math
import zlib

import numpy as np

from ..core import log
from ..geom import Acc, beam, finalize, lathe_rz, obox
from ..shingles import SHINGLE_VARIANTS, SIZE_TABLE, shingle_mesh

EZ = np.array([0.0, 0.0, 1.0])
SIDES = [np.array(v, float) for v in ((0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0))]


def _tn(k):
    n = SIDES[k]
    return np.array([-n[1], n[0], 0.0]), n


def _side_box(acc, k, u0, u1, d0, d1, z0, z1, mat, r=0.012, nn=3):
    """an axis-aligned box in side k's frame (u along the side, d out along its normal, z up)."""
    t, n = _tn(k)
    O = t * u0 + n * 0.5 * (d0 + d1) + EZ * 0.5 * (z0 + z1)
    obox(acc, O[None], t, n, EZ, u1 - u0, d1 - d0, z1 - z0, r, mat, nx=nn, ny=nn, nz=nn)


def _slab(acc, B, N, th, mat, th1=None):
    """a closed slab from 4 bottom corners B (4, 3, in order) offset by th along N (th1: thickness at corners 2, 3:
    a wedge)."""
    B = np.asarray(B, float)
    th1 = th if th1 is None else th1
    V = np.concatenate([B, B + N * np.array([th, th, th1, th1])[:, None]])
    F = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    c = V.mean(0)
    for i, f in enumerate(F):                               # orient every face outward
        p = V[f]
        nrm = np.cross(p[1] - p[0], p[3] - p[0])
        if np.dot(nrm, p.mean(0) - c) < 0:
            F[i] = f[::-1]
    acc.add(V, F, mat)


def _boards(acc, k, u0, u1, d0, d1, z0, z1, rng, mat="M_timber_weathered"):
    """vertical plank infill between u0 and u1 (widths 0.18-0.28, tight joints with rounded arrises)."""
    if u1 - u0 < 0.03 or z1 - z0 < 0.03:
        return
    n = max(1, int(round((u1 - u0) / rng.uniform(0.20, 0.26))))
    cuts = np.concatenate([[u0], u0 + (np.arange(1, n) + rng.uniform(-0.2, 0.2, n - 1)) * (u1 - u0) / n, [u1]])
    for a, b in zip(cuts[:-1], cuts[1:]):
        dd = rng.uniform(-0.004, 0.004)
        _side_box(acc, k, a + 0.002, b - 0.002, d0 + dd, d1 + dd, z0, z1 + rng.uniform(-0.004, 0.0), mat, r=0.008,
                  nn=2)


def square_cabin(g, side=5.4, height=2.30, z_bed=None, bed_r=None, bearers=None, n_joists=7,
                 struts=True, strut_drop=1.25, n_open=2, open_w=1.10, open_sill=1.00, open_h=0.90, pitch_deg=48.0,
                 eave_out=0.50, exposure=0.34, cap_r=0.62, seed=None, bed_fill=True, finial_scale=0.80, roof=None,
                 roof_fn=None):
    """KIT COMPONENT: square timber lookout cabin with a square-pyramid shingle roof on a wall head (module doc).
    side: outer plan size of the floor (m); height: floor top to the top plate's underside; z_bed / bed_r: the wall
    head (default: the drum's cornice top and cap); bearers: x of the bearers (along Y; r4 default None = 0 and
    +-0.65 bed_r, so any cabin / drum size bears on the wall head); n_joists: joists (along X);
    struts / strut_drop: a dragon beam to every corner, each carried by a raking knee strut in the diagonal plane,
    its foot on a dressed corbel pad this far below the bed; n_open,
    open_w, open_sill, open_h: lookout openings per side (clear width, sill above the floor, clear height);
    pitch_deg / eave_out: roof pitch and eave beyond the wall face; exposure: shingle course exposure; cap_r: plan
    radius (to the hip) of the lead apex cap.
    r4: bed_fill (default True): a closed timber rim ring on the wall head between the bearers and the joists, from
    the bed up to the deck underside just inside bed_r (the floor sandwich over the wall head is closed; open framing
    remains only on the cantilevers outside it); finial_scale: turned-finial scale (0.8 = 1.16 m above the cap);
    roof: overrides for the roof module (e.g. dict(bell_deg=24, bell_len=0.75, kick=0.04)); roof_fn: the roof module,
    called roof_fn(g, p_wall, z_plate, name="cabin", rng=rng, **kw) and returning pyramid_roof's record (default
    components.pyramid_roof.pyramid_roof)."""
    from .drum_frame import R_out
    from .pyramid_roof import pyramid_roof
    from .tower_roof import drum_top
    s0 = 0 if seed in (None, "") else zlib.crc32(str(seed).encode("utf8")) % 100000
    rng = np.random.default_rng(4141 + s0)
    H = float(drum_top(g)) if z_bed is None else float(z_bed)
    Rb = (float(R_out(g, H)) + 0.28) if bed_r is None else float(bed_r)
    if bearers is None:
        xb = round(0.65 * Rb, 2)
        bearers = (-xb, 0.0, xb)
    hs = side / 2.0
    P = g.prefix + "_cabin_"
    A = {k: Acc(P + k) for k in ("floor", "struts", "corbels", "bed", "frame", "boards", "ceiling")}
    # ---------------- floor: bed disc, bearers, joists, deck ----------------
    th = np.linspace(0, 2 * math.pi, 72, endpoint=False)
    rs = np.linspace(0.05, Rb - 0.02, 6)
    V = np.stack([np.outer(rs, np.sin(th)), np.outer(rs, -np.cos(th)), np.full((len(rs), len(th)), H + 0.003)], -1)
    i_, j_ = np.meshgrid(np.arange(len(rs) - 1), np.arange(len(th)), indexing="ij")
    j1 = (j_ + 1) % len(th)
    F = np.stack([i_ * len(th) + j_, (i_ + 1) * len(th) + j_, (i_ + 1) * len(th) + j1, i_ * len(th) + j1], -1)
    F = F.reshape(-1, 4)
    p = V.reshape(-1, 3)[F[0]]
    if np.cross(p[1] - p[0], p[3] - p[0])[2] < 0:
        F = F[:, ::-1]
    A["bed"].add(V.reshape(-1, 3), F, "M_mortar")
    hb, hj, td = 0.24, 0.20, 0.05
    for x in bearers:                                                     # bearers along Y on the wall head
        obox(A["floor"], np.array([[x, -hs, H + hb / 2]]), (0, 1, 0), (-1, 0, 0), (0, 0, 1), side, 0.22, hb, 0.015,
             "M_timber", nx=4, ny=3, nz=3)
    ys = np.linspace(-hs + 0.10, hs - 0.10, n_joists)
    for y in ys:                                                          # joists along X on the bearers
        obox(A["floor"], np.array([[-hs, y, H + hb + hj / 2]]), (1, 0, 0), (0, 1, 0), (0, 0, 1), side, 0.18, hj,
             0.015, "M_timber", nx=4, ny=3, nz=3)
    zd0 = H + hb + hj
    obox(A["floor"], np.array([[-hs, 0.0, zd0 + td / 2]]), (1, 0, 0), (0, 1, 0), (0, 0, 1), side, side, td, 0.01,
         "M_timber_weathered", nx=6, ny=6, nz=2)
    if bed_fill:
        # r4: rim ring (blocking between the bearers and between the joists) bedded 1 cm into the wall head, up to
        # the deck underside, its face 6 cm inside the bed ring: no sky between the cornice cap and the deck
        r1, r0 = Rb - 0.06, Rb - 0.18
        Vr, Fr = lathe_rz([(r0, H - 0.01), (r1, H - 0.01), (r1, zd0 - 0.004), (r0, zd0 - 0.004), (r0, H - 0.01)],
                          32, cap_bottom=False, cap_top=False, phase=math.pi / 32)
        A["floor"].add(Vr, Fr, "M_timber")
    Zf = zd0 + td                                                         # floor top
    # ---------------- knee struts on corbel pads ----------------
    n_str = 0
    pads = []
    if struts:
        zf = H - strut_drop
        Rf = float(R_out(g, zf))
        feet = []
        xo = max(abs(b) for b in bearers)
        for sx in (-1, 1):                    # a dragon beam to every corner (housed against the outer bearer)
            for sy in (-1, 1):
                dg = np.array([sx, sy, 0.0]) / math.sqrt(2.0)
                c0 = np.array([sx * (xo + 0.12), sy * (xo + 0.12), H + hb / 2])
                c1 = np.array([sx * (hs - 0.08), sy * (hs - 0.08), H + hb / 2])
                beam(A["floor"], c0, c1, 0.20, hb, 0.015, "M_timber", up=(0, 0, 1))
                # the knee strut under its outer end, in the diagonal plane, foot on a corbel pad
                feet.append((dg * Rf + EZ * zf, dg * (math.sqrt(2.0) * (hs - 0.20)) + EZ * H, dg))
        for foot, top, out in feet:
            rad = np.array([foot[0], foot[1], 0.0]) / max(math.hypot(foot[0], foot[1]), 1e-6)
            tang = np.cross(EZ, rad)
            pad_o = np.array([foot[0], foot[1], 0.0]) - rad * 0.10 + EZ * (zf - 0.11)
            obox(A["corbels"], pad_o[None], rad, tang, EZ, 0.30, 0.30, 0.22, 0.02, "M_stone_dressed", nx=3, ny=3,
                 nz=3)
            pads.append((float(foot[0]), float(foot[1]), float(zf)))
            p0 = foot + EZ * 0.0 + rad * 0.12                              # foot on the pad
            d = top - p0
            p0 = p0 - d / np.linalg.norm(d) * 0.04
            p1 = top + d / np.linalg.norm(d) * 0.05
            beam(A["struts"], p0, p1, 0.16, 0.16, 0.015, "M_timber_weathered", up=(0, 0, 1))
            n_str += 1
    # ---------------- framed walls with lookout openings ----------------
    do = hs - 0.04                                                        # wall outer face
    fd = 0.18                                                             # frame depth
    zs1 = Zf + 0.18
    zr0 = Zf + open_sill - 0.12
    zh0 = Zf + open_sill + open_h
    Zp = Zf + height
    Zt = Zp + 0.18
    L_in = 2 * (do - 0.20)
    centres = [-L_in / 2 + (j + 0.5) * L_in / n_open for j in range(n_open)]
    jw = 0.13
    bd0, bd1 = do - 0.075, do - 0.035                                     # plank infill plane
    for k in range(4):
        fr, bo = A["frame"], A["boards"]
        _side_box(fr, k, -do, do - fd, do - fd, do, Zf, zs1, "M_timber")                 # sill (half-lapped)
        _side_box(fr, k, -do, do - fd, do - fd, do, Zp, Zt, "M_timber")                  # top plate
        _side_box(fr, k, -do, -do + 0.20, do - 0.20, do, zs1, Zp, "M_timber")            # corner post
        posts = [(-do, -do + 0.20)]
        for c in centres:
            o0, o1 = c - open_w / 2, c + open_w / 2
            for a, b in ((o0 - jw, o0), (o1, o1 + jw)):
                _side_box(fr, k, a, b, do - 0.17, do - 0.01, zs1, Zp, "M_timber")
                posts.append((a, b))
        posts.append((do - 0.20, do))
        posts.sort()
        # head beam (r4: when the plate is under 6 cm above it, it grows into the plate -- no slot, no sliver boards)
        hh = 0.14 if Zp - zh0 - 0.14 >= 0.055 else Zp - zh0 + 0.005
        _side_box(fr, k, -do + 0.20, do - 0.20, do - 0.17, do - 0.02, zh0, zh0 + hh, "M_timber")      # head beam
        _side_box(fr, k, -do + 0.20, do - 0.20, do - 0.17, do - 0.02, zr0, zr0 + 0.12, "M_timber")    # breast rail
        _side_box(fr, k, -do + 0.20, do - 0.20, do - 0.12, do + 0.05, zr0 + 0.12, zr0 + 0.155,
                  "M_timber_weathered")                                                            # sill board
        for (a0, a1), (b0, b1) in zip(posts[:-1], posts[1:]):
            u0, u1 = a1, b0
            if u1 - u0 < 0.02:
                continue
            _boards(bo, k, u0, u1, bd0, bd1, zs1, zr0, rng)
            _boards(bo, k, u0, u1, bd0, bd1, zh0 + hh, Zp, rng)
            opening = any(abs(0.5 * (u0 + u1) - c) < open_w / 2 for c in centres)
            if not opening:
                _boards(bo, k, u0, u1, bd0, bd1, zr0 + 0.12, zh0, rng)
    ci = do - 0.17                                                         # boarded ceiling inside the plate
    obox(A["ceiling"], np.array([[-ci, 0.0, Zt - 0.02]]), (1, 0, 0), (0, 1, 0), (0, 0, 1), 2 * ci, 2 * ci, 0.04,
         0.008, "M_timber", nx=4, ny=4, nz=2)
    # ---------------- roof: the kit's pyramid roof module on the plate (r4: extracted, bell-cast capable) ----------
    rkw = dict(pitch_deg=pitch_deg, eave_out=eave_out, exposure=exposure, cap_r=cap_r, finial_scale=finial_scale)
    rkw.update(roof or {})
    rf = (roof_fn or pyramid_roof)(g, do, Zt, name="cabin", rng=rng, **rkw)
    built = dict(rf["objs"])
    for k_, acc in A.items():
        ob = finalize(acc, g.coll, smooth_deg=35.0, recalc=k_ not in ("bed",))
        if ob is not None:
            built[k_] = ob
    z_eave, tip = rf["z_eave"], rf["tip"]
    g.CABIN = dict(side=side, floor=Zf, plate=Zp, plate_top=Zt, eave=z_eave, apex=float(rf["apex"]), tip=tip,
                   openings=[(k, c, open_w, Zf + open_sill, open_h) for k in range(4) for c in centres],
                   pads=pads, bed=H, bed_r=Rb, bearers=tuple(bearers), roof=rf)
    g.ROOF = dict(frame=None, r_eave=rf["r_eave"], z_eave=z_eave, plate_top=Zt, r_wall=do, pitch=rkw["pitch_deg"],
                  tip=tip, collar_drip=rf["collar_drip"])
    log("square cabin: side %.2f on the bed z %.2f (r %.2f, bearers %s, bed fill %s), floor %.2f, plate %.2f..%.2f, "
        "%d x %d lookout openings %.2f x %.2f (sill %.2f), %d knee struts, roof eave %.2f (r %.2f) apex %.2f tip %.2f"
        % (side, H, Rb, tuple(bearers), bool(bed_fill), Zf, Zp, Zt, 4, n_open, open_w, open_h, Zf + open_sill, n_str,
           z_eave, rf["r_eave"], rf["apex"], tip))
    return built
