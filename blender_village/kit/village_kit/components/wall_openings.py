"""components.wall_openings -- doors and windows for ANY masonry wall, placed by a local frame (kit, variant
v3_longhouse_roundend).

An opening is placed by a frame (O, t, n): O = the point on the wall face at the opening's centre line, at Z = 0
(ground); t = the horizontal direction along the wall; n = the horizontal outward normal.  The wall builders
(components.rubble_walls: straight / polyline walls and round bodies) compute that frame and call these; the same
calls work on any wall a later module lays out.  Local coordinates: x along t, z up, w out along n.

    door_spec(width=1.0, height=2.10, ...)      a timber-framed plank door: dressed threshold slab, two hewn posts
                                                and a lintel bearing 0.25 m into the masonry, a closed vertical-plank
                                                leaf (components.plank_doors.plank_leaf) with forged straps
    window_spec(width=0.50, height=0.55, sill=1.25, ...)   a small deep-set window: projecting dressed stone sill with a
                                                drip, heavy timber frame with a cross mullion, timber lintel, mortar
                                                reveal and a dark blocker room behind (note 6)
    opening_rects(sp)                           the (x0, x1, z0, z1) rectangles the masonry must leave free
    opening_cut(sp)                             the (x0, x1, z0, z1) rectangle the mortar body must leave open
    build_opening(g, sp, O, t, n, accs, rng)    build one opening into the accumulators accs = dict(timber, dressed,
                                                iron, mortar, blocker); records it on g.OPENINGS (for decal anchors)
    opening_accs(g, name) / finish_accs(g, accs)   the per-wall accumulators -> <P>_<name>_frames, _dressed,
                                                _ironwork, _reveals, _blockers
"""
import math

import numpy as np

from ..geom import Acc, finalize, obox, prof_rect, sweep


def door_spec(width=1.0, height=2.10, threshold=0.12, post=(0.20, 0.24), lintel=0.24, bearing=0.25, leaf_set=0.07,
              planks=6):
    """a timber-framed plank door (clear width / height, threshold top above ground, post section (face, depth),
    lintel height, lintel bearing into the masonry each side, leaf set back behind the frame face).
    kit 1.8.0: a thin wrapper of components.openings (family "wall", openings.door)."""
    from .openings import wall_door
    return wall_door(width=width, height=height, threshold=threshold, post=post, lintel=lintel, bearing=bearing,
                     leaf_set=leaf_set, planks=planks)


def window_spec(width=0.50, height=0.55, sill=1.25, frame=0.08, depth=0.22, lintel=0.16, room=1.3):
    """a small deep-set window (clear width / height, clear sill height, frame member size, reveal depth to the
    frame, lintel height, blocker-room depth).
    kit 1.8.0: a thin wrapper of components.openings (family "wall", openings.window)."""
    from .openings import wall_window
    return wall_window(width=width, height=height, sill=sill, frame=frame, depth=depth, lintel=lintel, room=room)


def opening_rects(sp):
    """rectangles (x0, x1, z0, z1) in the wall's local (x along, z up) that the masonry must leave free."""
    from .openings import resolve
    sp = resolve(sp, "wall")
    hw = sp["width"] / 2
    if sp["kind"] == "door":
        pw = sp["post"][0]
        z1 = sp["threshold"] + sp["height"]
        return [(-hw - pw - 0.012, hw + pw + 0.012, -0.30, z1 + 0.012),
                (-hw - pw - sp["bearing"], hw + pw + sp["bearing"], z1 - 0.005, z1 + sp["lintel"] + 0.012),
                (-hw - pw - 0.16, hw + pw + 0.16, -0.30, sp["threshold"] + 0.01)]
    f = sp["frame"]
    z0, z1 = sp["sill"], sp["sill"] + sp["height"]
    return [(-hw - f - 0.012, hw + f + 0.012, z0 - f - 0.012, z1 + f + 0.012),
            (-hw - f - 0.13, hw + f + 0.13, z0 - f - 0.10, z0 - f + 0.005),
            (-hw - f - 0.20, hw + f + 0.20, z1 + f - 0.005, z1 + f + sp["lintel"] + 0.012)]


def opening_cut(sp):
    """the rectangle (x0, x1, z0, z1) the mortar body leaves open (inside the frame / reveal)."""
    from .openings import resolve
    sp = resolve(sp, "wall")
    hw = sp["width"] / 2
    if sp["kind"] == "door":
        pw = sp["post"][0]
        return (-hw - pw + 0.03, hw + pw - 0.03, 0.0, sp["threshold"] + sp["height"] - 0.02)
    f = sp["frame"]
    return (-hw - f + 0.02, hw + f - 0.02, sp["sill"] - f + 0.02, sp["sill"] + sp["height"] + f - 0.02)


def opening_accs(g, name):
    pre = f"{g.prefix}_{name}"
    return dict(timber=Acc(pre + "_frames"), dressed=Acc(pre + "_dressed"), iron=Acc(pre + "_ironwork"),
                mortar=Acc(pre + "_reveals"), blocker=Acc(pre + "_blockers"))


def finish_accs(g, accs):
    for k, a in accs.items():
        if a.n:
            finalize(a, g.coll, smooth_deg=30.0, recalc=(k not in ("mortar", "blocker")))


def _box(acc, lm, t, n, x0, x1, z0, z1, w0, w1, r, mat, nx=4):
    """an axis box in the opening's local frame (x along t, z up, w along n)."""
    ez = np.array([0.0, 0.0, 1.0])
    O = lm(x0, 0.5 * (z0 + z1), 0.5 * (w0 + w1))
    obox(acc, O[None], t, n, ez, x1 - x0, w1 - w0, z1 - z0, r, mat, nx=nx)


def _quad_strip(acc, P, mat, facing):
    """quads through a list of 4-point rings; faces turned toward `facing` (a point)."""
    F = np.array([[0, 1, 2, 3]])
    q = P[F[0]]
    nn = np.cross(q[1] - q[0], q[3] - q[0])
    if float(nn @ (np.asarray(facing) - q.mean(0))) < 0:
        F = F[:, ::-1]
    acc.add(P, F, mat)


def _room(acc, lm, x0, x1, z0, z1, w0, w1, mat):
    """dark blocker room behind an opening: back wall, two sides, floor, ceiling, all facing the opening."""
    c = lm(0.5 * (x0 + x1), 0.5 * (z0 + z1), 0.5 * (w0 + w1))
    corners = lambda xs, zs, ws: np.array([lm(x, z, w) for x, z, w in zip(xs, zs, ws)])  # noqa: E731
    faces = [corners([x0, x1, x1, x0], [z0, z0, z1, z1], [w1] * 4),               # back
             corners([x0, x0, x0, x0], [z0, z1, z1, z0], [w0, w0, w1, w1]),        # left
             corners([x1, x1, x1, x1], [z0, z1, z1, z0], [w0, w0, w1, w1]),        # right
             corners([x0, x1, x1, x0], [z0, z0, z0, z0], [w0, w0, w1, w1]),        # floor
             corners([x0, x1, x1, x0], [z1, z1, z1, z1], [w0, w0, w1, w1])]        # ceiling
    for P in faces:
        _quad_strip(acc, P, mat, c)


def build_opening(g, sp, O, t, n, accs, rng, label="", host=None):
    """build one opening (door / window spec) at frame (O, t, n) into accs (see module doc).  kit 1.8.0: sp may be a
    components.openings spec (resolved to family "wall").
    kit 1.12 (v5 round 2; None = the masonry opening, unchanged): host=dict(...) -- the opening sits in a TIMBER
    wall (components.timber_walls, the cruck infill, a board belt): see TIMBER_HOST and _build_timber_opening.  sp is
    then the timber family's resolved dict (timber_walls.resolve_timber)."""
    if host is not None:
        return _build_timber_opening(g, sp, O, t, n, accs, rng, label, host)
    from .openings import resolve
    sp = resolve(sp, "wall")
    O = np.asarray(O, float)
    t = np.asarray(t, float) / np.linalg.norm(t)
    n = np.asarray(n, float) / np.linalg.norm(n)
    ez = np.array([0.0, 0.0, 1.0])

    def lm(x, z, w):
        return O + x * t + z * ez + w * n

    def mapfn(x, z, w):
        x, z, w = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float), np.asarray(w, float))
        return O[None] + x.ravel()[:, None] * t + z.ravel()[:, None] * ez + w.ravel()[:, None] * n
    hw = sp["width"] / 2
    rec = dict(kind=sp["kind"], label=label, O=O, t=t, n=n, width=sp["width"], height=sp["height"])
    if sp["kind"] == "door":
        pw, pd = sp["post"]
        zt = sp["threshold"]
        z1 = zt + sp["height"]
        # threshold: one dressed slab, projecting 0.26 m, its top 8-15 cm above the ground (art bible 7)
        _box(accs["dressed"], lm, t, n, -hw - pw - 0.14, hw + pw + 0.14, -0.04, zt, -pd - 0.08, 0.26, 0.018,
             "M_stone_dressed", nx=6)
        # hewn posts and the lintel (bearing into the masonry each side), 2 cm proud of the wall face
        for sgn in (-1, 1):
            xa, xb = sorted((sgn * hw, sgn * (hw + pw)))
            _box(accs["timber"], lm, t, n, xa, xb, zt - 0.005, z1 + 0.002, -pd + 0.02, 0.02, 0.02, "M_timber")
        _box(accs["timber"], lm, t, n, -hw - pw - sp["bearing"], hw + pw + sp["bearing"], z1, z1 + sp["lintel"],
             -pd + 0.02, 0.025, 0.022, "M_timber", nx=6)
        # closed plank leaf in the frame rebate
        from .plank_doors import plank_leaf
        widths = rng.uniform(0.75, 1.25, sp["planks"])
        plank_leaf(accs["timber"], mapfn, -hw - 0.012, hw + 0.012, zt + 0.004, lambda x: np.full(np.shape(x), z1 + 0.01),
                   -sp["leaf_set"], 0.045, rng, widths, mat="M_timber_weathered", nv=24, seed=int(rng.integers(1000)))
        # forged straps (spear ends) from the hinge side + a latch bar
        for zs in (zt + 0.32, z1 - 0.34):
            us = np.linspace(0, 1, 14)
            xs = -hw + 0.02 + us * (sp["width"] * 0.72)
            wd = 0.05 - 0.012 * us + 0.03 * np.clip((us - 0.86) / 0.06, 0, 1) * np.clip((1 - us) / 0.08, 0, 1)
            path = mapfn(xs, np.full_like(xs, zs), np.full_like(xs, -sp["leaf_set"] + 0.004))
            V, F = sweep(path, n, np.stack([prof_rect(max(w_, 0.012), 0.007, 0.002) for w_ in wd]))
            accs["iron"].add(V, F, "M_iron")
        _box(accs["iron"], lm, t, n, hw - 0.20, hw - 0.04, zt + 1.00, zt + 1.03, -sp["leaf_set"], -sp["leaf_set"] + 0.018,
             0.004, "M_iron")
        rec.update(z0=zt, z1=z1, head=z1 + sp["lintel"], sill=None, threshold=zt, lintel_w=sp["width"] + 2 * (pw + sp["bearing"]))
    else:
        f = sp["frame"]
        d = sp["depth"]
        z0, z1 = sp["sill"], sp["sill"] + sp["height"]
        # projecting dressed sill with a drip edge (7 cm proud)
        _box(accs["dressed"], lm, t, n, -hw - f - 0.12, hw + f + 0.12, z0 - f - 0.09, z0 - f, -d - 0.02, 0.07, 0.012,
             "M_stone_dressed", nx=5)
        _box(accs["dressed"], lm, t, n, -hw - f - 0.10, hw + f + 0.10, z0 - f - 0.105, z0 - f - 0.085, 0.035, 0.065,
             0.005, "M_stone_dressed", nx=4)
        # mortar reveal round the frame, from the face back to the frame
        xo0, xo1, zo0, zo1 = -hw - f - 0.004, hw + f + 0.004, z0 - f, z1 + f
        for (xa, za, xb, zb) in ((xo0, zo0, xo1, zo0), (xo1, zo0, xo1, zo1), (xo1, zo1, xo0, zo1), (xo0, zo1, xo0, zo0)):
            P = np.array([lm(xa, za, 0.01), lm(xb, zb, 0.01), lm(xb, zb, -d), lm(xa, za, -d)])
            _quad_strip(accs["mortar"], P, "M_mortar", lm(0.0, 0.5 * (z0 + z1), -d * 0.5))
        # heavy frame + cross mullion, deep in the reveal
        wf0, wf1 = -d - 0.12, -d + 0.005
        for (xa, xb, za, zb) in ((-hw - f, -hw, z0 - f, z1 + f), (hw, hw + f, z0 - f, z1 + f),
                                 (-hw, hw, z0 - f, z0), (-hw, hw, z1, z1 + f)):
            _box(accs["timber"], lm, t, n, xa, xb, za, zb, wf0, wf1, 0.012, "M_timber")
        _box(accs["timber"], lm, t, n, -0.025, 0.025, z0, z1, wf0 + 0.02, wf1 - 0.015, 0.008, "M_timber")
        zm = 0.5 * (z0 + z1)
        _box(accs["timber"], lm, t, n, -hw, hw, zm - 0.025, zm + 0.025, wf0 + 0.02, wf1 - 0.015, 0.008, "M_timber")
        # timber lintel bearing into the masonry
        _box(accs["timber"], lm, t, n, -hw - f - 0.20, hw + f + 0.20, z1 + f, z1 + f + sp["lintel"], -d - 0.10, 0.012,
             0.016, "M_timber", nx=5)
        # dark blocker room behind (note 6: interiors only as deep as the opening shows)
        _room(accs["blocker"], lm, -hw - 0.45, hw + 0.45, z0 - 0.75, z1 + 0.35, wf0 + 0.01, -d - sp["room"],
              "M_timber_weathered")
        rec.update(z0=z0, z1=z1, head=z1 + f + sp["lintel"], sill=z0 - f, threshold=None,
                   lintel_w=sp["width"] + 2 * (f + 0.20))
    if not hasattr(g, "OPENINGS"):
        g.OPENINGS = []
    g.OPENINGS.append(rec)
    return rec


# =================================================================================================================
# kit 1.12 (v5 round 2): the TIMBER host -- the same opening builder for doors, windows and large boat / barn doors
# in a timber wall (it replaces timber_walls' private opening builder: one opening builder in the kit)
# =================================================================================================================
TIMBER_HOST = dict(face=0.0, floor=0.0, head_max=None, plate_top=None, plate_w=None, head_rule="clamp", ground=0.0,
                   casing=False)
"""host keys: face = w of the visible wall face beside the opening (cladding front); floor = absolute z of the
storey floor (sill-beam top); head_max = absolute z of the storey head's underside (the wall plate): no opening member
may cross it; plate_top / plate_w = the plate's top z and (w0, w1) range (for head_rule "trim"); head_rule = what a
door / boat door taller than its storey does: "clamp" (the clear height is clamped so the PLATE is the lintel, the
leaves stop 1 cm under it, no separate head beam) or "trim" (the plate is cut between the jambs and the head beam
replaces it flush, at the plate's own depth and top: rec["plate_cut"]); anything else raises.  ground = the wall's
ground z (a door more than 1.2 m above it is a loading hatch, not an entrance); casing = cased openings (clad
walls)."""


def _pintle(g, acc_fallback, P, ex, k):
    """the kit's forged pintle (plank_doors.make_pintle), pooled (note 3) as a linked duplicate at P: its shank runs
    along ex (into the jamb), the pin vertical."""
    from .plank_doors import make_pintle
    ez = np.array([0.0, 0.0, 1.0])
    ex = np.asarray(ex, float)
    ex = ex - ez * float(ex @ ez)
    ex = ex / np.linalg.norm(ex)
    ey = np.cross(ez, ex)
    pools = getattr(g, "pools", None)
    if pools is None or getattr(pools, "collection", None) is None:
        raise ValueError("timber opening: the pintle pool needs the frame's kit_instances collection")
    me = pools.mesh("pintle", int(k) % 3, make_pintle, sharp=40.0)
    pools.place(me, "pintle", np.stack([ex, ey, ez], 1), P)
    _ = acc_fallback


def _strap(acc, mapfn, n, x_h, x_len, z, w, direction):
    """a forged strap lying flat at w (its back), from the hinge edge x_h along `direction` (+-1), spear end
    (plank_doors.strap_widths), 6 mm thick."""
    from .plank_doors import strap_widths
    us = np.linspace(0, 1, 16)
    xs = x_h + direction * us * x_len
    wd = strap_widths(us, w0=0.045, w1=0.034, spear_w=0.065)
    path = mapfn(xs, np.full_like(xs, z), np.full_like(xs, w + 0.0035))
    V, F = sweep(path, n, np.stack([prof_rect(max(w_, 0.012), 0.007, 0.002) for w_ in wd]))
    acc.add(V, F, "M_iron")


def _leaf(acc, mapfn, rng, x0, x1, z0, z1, w_front, thick, n_planks, mat="M_timber_weathered"):
    """a vertical-plank leaf / shutter (plank_doors.plank_leaf, the kit's ONE plank leaf)."""
    from .plank_doors import plank_leaf
    widths = rng.uniform(0.75, 1.25, max(1, int(n_planks)))
    plank_leaf(acc, mapfn, x0, x1, z0, lambda x: np.full(np.shape(x), z1), w_front, thick, rng, widths, mat=mat,
               nv=12, seed=int(rng.integers(1000)))


def _build_timber_opening(g, sp, O, t, n, accs, rng, label, host):
    """build_opening(host=...): a door, window (with open plank shutters) or large boat / barn door in a timber wall.
    sp: the timber family's dict (kind "door" / "window" / "boat"; width, height, threshold / sill above the floor,
    jamb (face, depth), head, ... see timber_walls.TIMBER_OPENING).  Every leaf and shutter is the kit's plank leaf,
    every hinge a forged strap ON THE LEAF from its hinge edge, with the kit's pooled pintle in the jamb.
    Returns the record (also appended to g.OPENINGS) with z1 = the EFFECTIVE clear head."""
    h = dict(TIMBER_HOST)
    h.update(host)
    O = np.asarray(O, float)
    t = np.asarray(t, float) / np.linalg.norm(t)
    n = np.asarray(n, float) / np.linalg.norm(n)
    ez = np.array([0.0, 0.0, 1.0])

    def lm(x, z, w):
        return O + x * t + z * ez + w * n

    def mapfn(x, z, w):
        x, z, w = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float), np.asarray(w, float))
        return O[None] + x.ravel()[:, None] * t + z.ravel()[:, None] * ez + w.ravel()[:, None] * n
    kind = sp["kind"]
    hw = sp["width"] / 2
    jw, jd = sp["jamb"]
    face, floor = float(h["face"]), float(h["floor"])
    cased = bool(h["casing"]) or kind == "boat"
    jo = face + (0.02 if cased else 0.0)                        # the jamb's front
    tim, iron, room = accs["timber"], accs["iron"], accs["blocker"]
    rec = dict(kind="door" if kind in ("door", "boat") else "window", label=label, O=O.copy(), t=t, n=n,
               width=sp["width"], height=sp["height"], timber=True, style=kind)
    if kind == "window":
        cz0 = floor + sp["sill"]
        cz1 = cz0 + sp["height"]
        rail, hd = sp.get("rail", 0.14), sp["head"]
        if h["head_max"] is not None and cz1 + hd > float(h["head_max"]) + 1e-6:
            raise ValueError(f"timber window {label}: its head {cz1 + hd:.2f} crosses the storey head "
                             f"{float(h['head_max']):.2f}; lower the sill or the height")
        for a, b in ((-hw - jw, -hw), (hw, hw + jw)):
            _box(tim, lm, t, n, a, b, cz0 - rail, cz1 + hd, -jd, jo, 0.012, "M_timber")
        _box(tim, lm, t, n, -hw - jw - 0.04, hw + jw + 0.04, cz1, cz1 + hd, -jd, jo + 0.012, 0.01, "M_timber", nx=5)
        _box(tim, lm, t, n, -hw - jw - 0.05, hw + jw + 0.05, cz0 - 0.05, cz0, -jd, jo + 0.06, 0.01, "M_timber", nx=5)
        f = sp["frame"]
        wf0, wf1 = -jd + 0.04, -jd + 0.04 + f
        for (xa, xb, za, zb) in ((-hw, -hw + f, cz0, cz1), (hw - f, hw, cz0, cz1), (-hw, hw, cz0, cz0 + f),
                                 (-hw, hw, cz1 - f, cz1)):
            _box(tim, lm, t, n, xa, xb, za, zb, wf0, wf1, 0.006, "M_timber")
        zm = 0.5 * (cz0 + cz1)
        _box(tim, lm, t, n, -0.02, 0.02, cz0 + f, cz1 - f, wf0 + 0.01, wf1 - 0.01, 0.005, "M_timber")
        if sp.get("lights", 4) != 2:                                  # kit 1.14: lights=2 = no transom
            _box(tim, lm, t, n, -hw + f, hw - f, zm - 0.02, zm + 0.02, wf0 + 0.01, wf1 - 0.01, 0.005, "M_timber")
        rec.update(z0=cz0, z1=cz1, head=cz1 + hd, sill=cz0 - 0.05, threshold=None, lintel_w=sp["width"] + 2 * jw)
        if sp.get("shutters"):
            # two open plank shutters lying back on the wall face beside the casing: the hinge is the casing's outer
            # edge, the straps lie ON the shutter ledges running OUTWARD from it, the pintle runs into the jamb
            sw = hw + 0.03
            wb = max(face, jo) + 0.006                         # shutter back on the face
            st = 0.028
            for k, sgn in enumerate((-1, 1)):
                xh = sgn * (hw + jw)
                xa, xb = sorted((xh, xh + sgn * sw))
                _leaf(tim, mapfn, rng, xa, xb, cz0 - 0.03, cz1 + 0.03, wb + st, st, 3)
                for zz in (cz0 + 0.08, cz1 - 0.14):
                    _box(tim, lm, t, n, xa + 0.02, xb - 0.02, zz, zz + 0.07, wb + st, wb + st + 0.022, 0.006,
                         "M_timber_weathered")
                    _strap(iron, mapfn, n, xh, 0.72 * sw, zz + 0.035, wb + st + 0.022, sgn)
                    _pintle(g, iron, lm(xh, zz + 0.035 + 0.045, wb + 0.012), -sgn * t, k)
        px, pb, pt = sp.get("room_pad") or (0.35, 0.6, 0.35)          # kit 1.13 (default = the old margins)
        _room(room, lm, -hw - px, hw + px, cz0 - pb, cz1 + pt, -jd + 0.03, -jd - sp.get("room", 1.0),
              "M_timber_weathered")
    else:
        cz0 = floor + sp["threshold"]
        cz1 = cz0 + sp["height"]
        hd = sp["head"]
        hm = h["head_max"]
        head_beam = True
        if hm is not None and cz1 + hd > float(hm) + 1e-6:
            rule = sp.get("head_rule") or h["head_rule"]
            hm = float(hm)
            if rule == "clamp":
                if hm - cz0 < (1.80 if kind == "boat" else 2.0):
                    raise ValueError(f"timber {kind} {label}: clamped under the storey head it would be only "
                                     f"{hm - cz0:.2f} m tall; raise the storey or use head_rule='trim'")
                cz1, head_beam = hm, False                       # the plate is the lintel
            elif rule == "trim":
                pt, pw_ = h["plate_top"], h["plate_w"]
                if pt is None or pw_ is None or float(pt) - cz1 < 0.15:
                    raise ValueError(f"timber {kind} {label}: head_rule 'trim' needs a head beam >= 0.15 m between "
                                     f"the clear head {cz1:.2f} and the plate top {pt}")
                rec["plate_cut"] = (-hw - jw, hw + jw)
            else:
                raise ValueError(f"timber {kind} {label}: the opening head {cz1 + hd:.2f} m crosses the storey head "
                                 f"{hm:.2f} m (head_rule {rule!r}: 'clamp' or 'trim')")
        jz0 = floor - 0.01
        jz1 = (cz1 + hd) if head_beam else float(hm) - 0.002
        if "plate_cut" in rec:
            jz1 = float(h["plate_top"])
        for a, b in ((-hw - jw, -hw), (hw, hw + jw)):
            _box(tim, lm, t, n, a, b, jz0, jz1, -jd, jo, 0.012, "M_timber")
        if head_beam:
            if "plate_cut" in rec:                      # flush with the plate it replaces: its depth and top
                w0, w1 = h["plate_w"]
                _box(tim, lm, t, n, -hw - jw, hw + jw, cz1, float(h["plate_top"]), w0, w1, 0.014, "M_timber", nx=6)
            else:
                hb = sp.get("bearing", 0.04) if kind == "boat" else 0.04
                _box(tim, lm, t, n, -hw - jw - hb, hw + jw + hb, cz1, cz1 + hd, -jd, jo + 0.012, 0.014, "M_timber",
                     nx=6)
        lt = sp.get("leaf_t", 0.045)
        if kind == "door":
            lw1 = jo - sp.get("leaf_set", 0.06)
            _leaf(tim, mapfn, rng, -hw - 0.012, hw + 0.012, cz0 + 0.004, cz1 + 0.010 - (0.02 if not head_beam else 0),
                  lw1, lt, sp.get("planks", 5))
            for k, zs in enumerate((cz0 + 0.30, cz1 - 0.32)):
                _strap(iron, mapfn, n, -hw + 0.01, sp["width"] * 0.72, zs, lw1, 1)
                _pintle(g, iron, lm(-hw - 0.004, zs + 0.045, lw1 - 0.01), -t, k)
            _box(iron, lm, t, n, hw - 0.20, hw - 0.04, cz0 + 1.00, cz0 + 1.03, lw1, lw1 + 0.018, 0.004, "M_iron")
        else:                                          # boat / barn door: ledged and braced leaves, ledges outside
            nl = int(sp.get("leaves", 2))
            lw1 = jo - 0.05
            top = cz1 + 0.015 if head_beam else cz1 - 0.01
            edges = np.linspace(-hw - 0.015, hw + 0.015, nl + 1)
            for li in range(nl):
                a, b = edges[li] + (0.004 if li else 0.0), edges[li + 1] - (0.004 if li < nl - 1 else 0.0)
                _leaf(tim, mapfn, rng, a, b, cz0 + 0.005, top, lw1, lt, max(3, int(round((b - a) / 0.22))))
                zl = np.linspace(cz0 + 0.22, top - 0.30, int(sp.get("ledges", 3)))
                hinge_left = li == 0 if nl > 1 else True
                for k, zz in enumerate(zl):
                    _box(tim, lm, t, n, a + 0.03, b - 0.03, zz, zz + 0.18, lw1, lw1 + 0.035, 0.008,
                         "M_timber_weathered", nx=5)
                    xh, dr = (a, 1) if hinge_left else (b, -1)
                    _strap(iron, mapfn, n, xh - dr * 0.01, 0.62 * (b - a), zz + 0.09, lw1 + 0.035, dr)
                    _pintle(g, iron, lm(xh - dr * 0.03, zz + 0.09 + 0.045, lw1 + 0.02), -dr * t, k + 3 * li)
                for k in range(len(zl) - 1):              # Z braces rising from the hinge side
                    za, zb = zl[k] + 0.18, zl[k + 1]
                    sa, sb = (a + 0.10, b - 0.10) if hinge_left else (b - 0.10, a + 0.10)
                    p0, p1 = lm(sa, za + 0.02, lw1 + 0.0175), lm(sb, zb - 0.02, lw1 + 0.0175)
                    d = p1 - p0
                    L = float(np.linalg.norm(d))
                    obox(tim, p0[None], d / L, np.cross(n, d / L), n, L, 0.15, 0.035, 0.008, "M_timber_weathered",
                         nx=5)
            _box(iron, lm, t, n, -0.03, 0.03, cz0 + 1.05, cz0 + 1.25, lw1 + 0.035, lw1 + 0.05, 0.004, "M_iron")
        _room(room, lm, -hw - 0.3, hw + 0.3, cz0 - 0.002, cz1 + 0.3, -jd + 0.03, -jd - sp.get("room", 1.4),
              "M_timber_weathered")
        rec.update(z0=cz0, z1=cz1, head=(cz1 + hd) if head_beam else cz1, sill=None, threshold=cz0,
                   lintel_w=sp["width"] + 2 * jw, head_rule=None if head_beam and "plate_cut" not in rec else
                   ("trim" if "plate_cut" in rec else "clamp"))
        if cz0 - float(h["ground"]) > 1.2:
            rec.update(kind="hatch", sill=cz0)
        if sp.get("steps_to") is not None:                 # built-in dressed-stone steps down to the ground
            gz = float(sp["steps_to"])
            nst = int(math.ceil((cz0 - gz - 0.02) / sp.get("rise", 0.17)))
            if nst > 0:
                rise = (cz0 - gz) / nst
                for k in range(nst):
                    ztop = gz + (k + 1) * rise - (0.01 if k == nst - 1 else 0.0)
                    depth = (nst - k) * sp.get("tread", 0.32)
                    _box(accs["dressed"], lm, t, n, -hw - jw - 0.10 + 0.02 * k, hw + jw + 0.10 - 0.02 * k,
                         ztop - rise - 0.04, ztop, -0.06, depth, 0.02, "M_stone_dressed", nx=6)
                rec["steps"] = dict(n=nst, rise=rise, tread=sp.get("tread", 0.32))
        if rec.get("head_rule"):
            from ..core import log
            log(f"  timber {kind} {label}: head rule {rec['head_rule']}: effective clear head {cz1:.3f} m "
                f"(clear height {cz1 - cz0:.3f} m)")
    if not hasattr(g, "OPENINGS"):
        g.OPENINGS = []
    g.OPENINGS.append(rec)
    return rec
