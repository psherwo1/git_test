"""a1_longhouse_addons -- the WALL add-ons (kit 1.19: components.lean_to, components.porch) proved on a DEMO COPY of
the accepted v3 longhouse.  v3's recipe is IMPORTED unchanged (its plan, walls, thatch, round end, cone and finial);
this recipe only adds steps, plus the host settings the add-ons need:

  host eave   the thatch eave is lifted in one soft arch over the front door (GableRoof(eave_lifts=[eave_lift(...)]),
              the barn's "eyelid", kit 1.16) and a second over the lean-to on the back; the walls' heads follow the
              warped deck (under_z_world) and the rafter tails under the arches are dropped (rafter_lift_max, kit 1.17)
  round 3     the lean-to's roof is ROUNDED (CLIENT DIRECTION 00:22, producer note 19): lean_to(roof_ends="round"),
              a softly convex thatch slope whose free ends curve round as rounded hips over the square shed (the
              shingle / verge description below is round 2's); the lean-to is 2.0 m deep; the front arch 7.0 m wide;
              the host's wall heads are bedded to the warped deck (seal_wall_head) and its stones face out
              (orient_stones)
  round 4     the rounded roof in the village coat (0.22 + 0.08 m, 0.30 m courses) on the village eave roll
              (round_kw eave_roll={}), with moss anchors (decals=True); the back wall-head bedding runs to the NW
              gable corner; the porch's slim bargeboards rise 2.5 cm over the covering (no verge slot)
  lean-to     4.0 x 1.9 m on the back (north) long wall, taking in the east window: an open-fronted store in the
              village shingle (16 deg, its wall line arching up under the host's arch: ridge_sag < 0, swept eave,
              flared verges, slim 0.12 m bargeboards), its own small eave arch (0.18 m) so the plate and the eave
              curve together, rubble end walls with quoined fronts, the arched hewn plate on a middle post (dressed
              pad, short curved knee braces), ledger + common rafters, lime flaunching and lead verge aprons against
              the stone; guarded: plate >= 2.10 m, braces >= 1.95 m, eave lip over the opening >= 2.30 m (round 2),
              under the host's eave and its thatch roll's belly
  porch       over the front door: an ARCHED, bell-cast shingle hood (its own eave_lift + eave_sweep, flared verges,
              slim bargeboards cut to the covering line) on two curved brackets (the barn's hoist-beam arm + curved
              knee brace), an arched front beam >= 2.32 m (art bible 7), ledger, rafters, flaunching and aprons;
              guarded >= 0.25 m under the lifted thatch roll's belly (round 2)
Run:  python -I build_a1_longhouse_addons.py   -> a1_longhouse_addons.blend + decal_anchors.json (next to this file)
      A1_FAST=1 skips the hidden-geometry ray test (quick looks only); A1_OUT=<path.blend> writes elsewhere.
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "kit"))

from village_kit.assembly import build_building  # noqa: E402
from village_kit.components.composite import composite_decals, composite_hidden_cull, recenter  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.lean_to import lean_to, plane_wall  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, linear_roof  # noqa: E402
from village_kit.components.porch import porch  # noqa: E402
from village_kit.components.rubble_walls import orient_stones  # noqa: E402

BID = "a1_longhouse_addons"
_spec = importlib.util.spec_from_file_location(
    "v3_recipe", os.path.join(ROOT, "buildings", "variants", "v3_longhouse_roundend", "build_v3_longhouse_roundend.py"))
V3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V3)                     # the accepted recipe, read only (its main() is never called)

# ---- host settings: the thatch eave lifted in one soft arch over the porch (front) and over the lean-to (back) ------
# round 2: front 1.2 -> 1.4 m (the thatch roll's belly >= 0.25 m over the hood, verges included); back 1.2 m / 8 m ->
# 1.5 m / 9.5 m with a longer fade (the lean-to rises for its 2.10 m plate / 2.30 m lip and still dies in under it),
# centred on the east north window so the arch stays clear of the round end (x -2)
# round 3: the front arch 6.0 -> 7.0 m wide (gentler), so the roll also clears the hood's verge corners SIDEWAYS
# by >= 0.25 m (mono_roof's new lateral roll guard: 0.216 m at the E verge with 6.0 m)
LIFT = eave_lift(V3.DOOR_X, side=-1, width=7.0, height=1.4, fade=2.5)          # front: over the door hood
LEAN_X = -6.2                                   # the lean-to's centre on the back wall (it takes in the east window)
LIFT_N = eave_lift(LEAN_X, side=1, width=9.5, height=1.5, fade=2.8)           # back: the lean-to dies in under it
ROOF = GableRoof(x0=V3.X_GABLE, x1=-0.6, half=V3.HALF, wall_z=V3.WALL_Z, pitch_deg=40.0, overhang=0.45,
                 verge=(0.40, 0.0), thick=0.30, step=0.10, exposure=0.30, name="body_roof", eave_lifts=[LIFT, LIFT_N])
LIFT_MAX = 0.08                                   # no host rafter tails where the arch lifts the eave more than this

def body_top(x, y):
    """v3's wall head (2 cm into the deck), on the WARPED deck: the front wall rises under the lifted eave."""
    return float(ROOF.under_z_world(np.array([[x, y]]))[0]) + 0.02


V3.ROOF = ROOF                                    # v3's steps() / body_top / under_deck read these module globals
V3.body_top = body_top

# ---- the add-ons ----------------------------------------------------------------------------------------------------
# round 2: the bargeboards slimmed to 0.12 m and cut to the covering line (no "ears"); both verges flared (note 17)
SLIM_VERGE = dict(below=0.025, above=0.0)
LEAN = dict(name="lean_to", W=plane_wall((LEAN_X, V3.HALF), (0.0, 1.0)), s0=-2.0, s1=2.0, depth=2.0,
            z_face=3.08, pitch_deg=16.0, overhang=0.22, verge=(0.18, 0.18), covering="shingle", ends="rubble",
            end_t=0.40, max_span=1.8, brace=(0.36, 0.28), headroom=(2.10, 1.95),
            soft=dict(ridge_sag=-0.15, eave_sweep=0.06, sweep_len=0.6, wave=0.012,    # its wall line arches up
                      verge_flare=0.06, flare_len=0.5,                                # flared verges
                      eave_lifts=[eave_lift(0.0, side=1, width=4.6, height=0.18, fade=1.5)]),  # plate + eave arch
            verge_board=SLIM_VERGE,
            below=ROOF, below_lift_max=LIFT_MAX, below_clear=0.08, below_roll=0.10, seed=1901,
            # round 3 (CLIENT DIRECTION 00:22, producer note 19 "an oval on the rectangle"): a softly convex thatch
            # slope whose free ends curve round as rounded hips over the square shed (no verges); the arch along the
            # wall (0.15) and at the eave (0.18) are round 2's ridge_sag / eave_lift
            roof_ends="round", round_kw=dict(end_over=0.45, hip=0.55, ne=3.0, bulge=0.04, arch_wall=0.15,
                                             arch_eave=0.18, wave=0.012,
                                             # round 4 (AD r3 must-fix 1, note 16): the village coat and courses
                                             # (0.22 + 0.08 m = mono_roof's thatch, 0.30 m courses = the host's
                                             # exposure) on the village eave roll (GableRoof.eave_roll defaults =
                                             # the v3 host's); moss anchors on the round roof
                                             thatch=(0.22, 0.08), course=0.30, eave_roll={}, decals=True))
PORCH = dict(name="porch", W=plane_wall((V3.DOOR_X, -V3.HALF), (0.0, -1.0)), width=2.1, depth=1.0, clear=2.32,
             pitch_deg=22.0, overhang=0.25, side=0.20, covering="shingle", brace=(0.65, 0.75),
             soft=dict(eave_sweep=0.08, sweep_len=0.5, wave=0.008,                # bell-cast lip
                       verge_flare=0.05, flare_len=0.45,                          # flared verges
                       eave_lifts=[eave_lift(0.0, side=1, width=2.6, height=0.22, fade=1.0)]),   # arched hood
             # round 4 (AD r3 must-fix 3): the slim board rises 2.5 cm over the covering top (verge slot p01 / p02)
             verge_board=dict(SLIM_VERGE, above=0.025),
             below=ROOF, below_lift_max=LIFT_MAX, below_roll=0.25, seed=1931)

# round 4 (AD r3 must-fix 2, i13): the bedding runs on past the arch's foot to the NW gable corner (min_lift 0:
# x_lim as given; it stops 5 cm inside the gable's outer face, so its end is buried in the corner stones)
HEAD_SEAL = dict(lift=LIFT_N, y_face=V3.HALF, out=1.0, w=(0.035, 0.085), drop=0.30, tuck=0.012, min_lift=0.0,
                 x_lim=(V3.X_GABLE + 0.05, -2.60), name="body_wall_head")          # back (round-2 i06 slits)
HEAD_SEAL_S = dict(HEAD_SEAL, lift=LIFT, y_face=-V3.HALF, out=-1.0, name="body_wall_head_s")   # front, the same


def seal_wall_head(g, lift, y_face, out, w, drop, tuck, min_lift, x_lim, name, step=0.05):
    """a1 round 3: close the host's rubble wall head to the WARPED deck under a lifted eave arch.  On the arch's
    flanks the deck rises along the wall faster than a flat-topped head stone follows it, so 1-2 cm wedge slits
    open between the top course and the deck (i06: daylight into the attic).  A mortar bedding band (M_mortar,
    w[0]..w[1] m behind the outer face, inside the stones' depth) runs from `drop` m under the deck up `tuck` m into
    it, wherever the arch lifts the eave at the face by >= min_lift; the "_mortar" name keeps it out of the cull."""
    from village_kit.geom import Acc, finalize, prof_rect, sweep
    from village_kit.core import log
    x0 = max(lift["x"] - 0.5 * lift["width"], x_lim[0]) if min_lift > 0 else x_lim[0]   # round 4: 0 = x_lim
    x1 = min(lift["x"] + 0.5 * lift["width"], x_lim[1]) if min_lift > 0 else x_lim[1]
    xs = np.arange(x0, x1 + 1e-9, step)
    yc = y_face - out * 0.5 * (w[0] + w[1])
    P = np.column_stack([xs, np.full(len(xs), yc)])
    Q = ROOF.to_local(np.column_stack([xs, np.full(len(xs), y_face), np.zeros(len(xs))]))
    keep = ROOF.lift_z(Q[:, 0], Q[:, 1]) >= min_lift - 1e-9
    if keep.sum() < 2:
        return None
    i0, i1 = np.flatnonzero(keep)[[0, -1]]
    xs, P = xs[i0:i1 + 1], P[i0:i1 + 1]
    zt = ROOF.under_z_world(P) + tuck
    path = np.column_stack([xs, P[:, 1], zt - 0.5 * drop])
    acc = Acc(f"{g.prefix}_{name}_mortar")
    V, F = sweep(path, np.array([0.0, 0.0, 1.0]), prof_rect(w[1] - w[0], drop, 0.01))
    acc.add(V, F, "M_mortar", wear=0.2)
    finalize(acc, g.coll, smooth_deg=35.0)
    log(f"  {g.prefix}_{name}_mortar: wall-head bedding x {xs[0]:.2f}..{xs[-1]:.2f}, {drop:.2f} m deep, "
        f"{tuck * 100:.1f} cm into the deck, {w[0]:.3f}-{w[1]:.3f} m behind the face")


CORNER_SEAL = dict(x_face=V3.X_GABLE, y=(V3.HALF - 0.80, V3.HALF - 0.035), w=(0.035, 0.085), z_lo=2.30, tuck=0.012,
                   name="body_gable_corner_nw")


def seal_gable_corner(g, x_face, y, w, z_lo, tuck, name, step=0.05):
    """a1 round 4 (i15): a mortar core slab inside the host's NW gable corner, w[0]..w[1] m behind the gable's outer
    face, from z_lo up `tuck` m into the deck, along the gable from y[0] to y[1] (5 cm inside the back face): the
    rubble shell there leaves a ray path from the attic out through the corner (2 px in i15, under the wall head)."""
    from village_kit.geom import Acc, finalize
    from village_kit.core import log
    ys = np.arange(y[0], y[1] + 1e-9, step)
    xa, xb = x_face + w[0], x_face + w[1]
    zt = ROOF.under_z_world(np.column_stack([np.full(len(ys), 0.5 * (xa + xb)), ys])) + tuck
    n = len(ys)
    V = np.concatenate([np.column_stack([np.full(n, xa), ys, np.full(n, z_lo)]),
                        np.column_stack([np.full(n, xb), ys, np.full(n, z_lo)]),
                        np.column_stack([np.full(n, xb), ys, zt]),
                        np.column_stack([np.full(n, xa), ys, zt])])
    i = np.arange(n - 1)
    sides = [np.stack([k * n + i, k * n + i + 1, ((k + 1) % 4) * n + i + 1, ((k + 1) % 4) * n + i], 1)
             for k in range(4)]
    caps = [np.array([[3 * n, 2 * n, n, 0]]), np.array([[n - 1, 2 * n - 1, 3 * n - 1, 4 * n - 1]])]
    acc = Acc(f"{g.prefix}_{name}_mortar")
    acc.add(V, sides + caps, "M_mortar", wear=0.2)
    finalize(acc, g.coll, smooth_deg=35.0)
    log(f"  {g.prefix}_{name}_mortar: gable-corner core y {ys[0]:.2f}..{ys[-1]:.2f}, z {z_lo:.2f}..{zt.max():.2f}, "
        f"{w[0]:.3f}-{w[1]:.3f} m behind the gable face")


def orient_host_stones(g):
    """a1 round 3: the host's rubble (laid on the warped head) with every stone facing out (orient_stones)."""
    orient_stones(g, "body_wall")


def steps():
    st = []
    for step in V3.steps():
        fn, kw = step if isinstance(step, tuple) else (step, {})
        if fn is linear_roof:
            kw = dict(kw, rafter_lift_max=LIFT_MAX)
        if fn is composite_hidden_cull or fn is recenter:
            continue
        st.append((fn, kw) if kw or isinstance(step, tuple) else fn)
    st += [orient_host_stones, (seal_wall_head, HEAD_SEAL), (seal_wall_head, HEAD_SEAL_S),
           (seal_gable_corner, CORNER_SEAL)]
    st += [(lean_to, LEAN), (porch, PORCH)]
    return st + ([] if os.environ.get("A1_FAST") else [hidden_cull_host]) + [recenter]


ADDON_PARTS = ("_lean_to", "_porch")


def hidden_cull_host(g):
    """v3's hidden-geometry cull on the host only: the add-ons (open shed, door hood) are seen from under and
    inside, where the cull's viewpoint loops do not reach, and they are trimmed at the wall already."""
    from village_kit.components.composite import BACKING, _meshes
    targets = [o.name for o in _meshes(g) if o.data.users == 1 and not any(b in o.name for b in BACKING)
               and not any(p in o.name for p in ADDON_PARTS)]
    return composite_hidden_cull(g, targets=targets)


def main():
    from functools import partial
    out = os.environ.get("A1_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="A1L", collection="A1L", building_id=BID,
        frame=RoundFrame, params=V3.KIT,
        steps=steps(),
        decals=partial(composite_decals, moss_normal="slope"),
        decal_validate=V3.DECAL_VALIDATE,
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in V3.KIT.items() if k != "cone_age"},
                        host="v3_longhouse_roundend (recipe imported)", host_eave_lift=LIFT,
                        addons=dict(lean_to={k: v for k, v in LEAN.items() if k not in ("W", "below")},
                                    porch={k: v for k, v in PORCH.items() if k not in ("W", "below")})),
    ))


if __name__ == "__main__":
    main()
