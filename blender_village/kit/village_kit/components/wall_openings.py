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
    opening_rects(spec)                         the (x0, x1, z0, z1) rectangles the masonry must leave free
    opening_cut(spec)                           the (x0, x1, z0, z1) rectangle the mortar body must leave open
    build_opening(g, spec, O, t, n, accs, rng)  build one opening into the accumulators accs = dict(timber, dressed,
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
    lintel height, lintel bearing into the masonry each side, leaf set back behind the frame face)."""
    return dict(kind="door", width=width, height=height, threshold=threshold, post=post, lintel=lintel,
                bearing=bearing, leaf_set=leaf_set, planks=planks)


def window_spec(width=0.50, height=0.55, sill=1.25, frame=0.08, depth=0.22, lintel=0.16, room=1.3):
    """a small deep-set window (clear width / height, clear sill height, frame member size, reveal depth to the
    frame, lintel height, blocker-room depth)."""
    return dict(kind="window", width=width, height=height, sill=sill, frame=frame, depth=depth, lintel=lintel,
                room=room)


def opening_rects(sp):
    """rectangles (x0, x1, z0, z1) in the wall's local (x along, z up) that the masonry must leave free."""
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


def build_opening(g, sp, O, t, n, accs, rng, label=""):
    """build one opening (door / window spec) at frame (O, t, n) into accs (see module doc)."""
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
