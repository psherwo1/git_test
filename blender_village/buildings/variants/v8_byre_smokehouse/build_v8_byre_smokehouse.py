"""v8_byre_smokehouse (BYRE) -- a long low single-storey rubble byre / smokehouse, ~12 x 5 m, wall 2.4 m.
A declarative RECIPE (template: v7_cottage; add-on: a1 lean-to).  Every piece is a village_kit module.

  main     rubble house 12.0 x 5.0 m (path_stone_wall, RUBBLE_LARGE) under a soft thatch LOAF: GableRoof(hips="both",
           crown=...) a ROUND HIP at both ends ("an oval on the rectangle", note 19); hip-end board gablets as v7
  eyebrow  ONE thatch eyebrow on the FRONT slope over the hay-loft window (note 18)
  hood     a ROUND battered rubble smoke hood / stack rising through the EAST round hip (roof_addons.chimney)
  lean-to  a rounded apsidal lean-to (lean_to roof_ends="round") on the back long wall, under a lifted host eave arch
  doors    a wide plank cart / animal door (no arched head in the kit) + small deep-set windows

Run:  python -I build_v8_byre_smokehouse.py -> v8_byre_smokehouse.blend + decal_anchors.json (next to this file)
      BYRE_FAST=1 skips the hidden-geometry cull (quick looks only); BYRE_OUT=<path.blend> writes elsewhere.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.composite import (composite_decals, inside_box, inside_round, recenter,  # noqa: E402
                                              set_entrance)
from village_kit.components.lean_to import lean_to, plane_wall  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, eyebrow, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.orient_fix import orient_closed_slabs, orient_open_islands  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.roof_addons import (any_clip, chimney, chimney_decals, hidden_cull,  # noqa: E402
                                                reentrant_views, roofs_top_fn, straight_span)
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall  # noqa: E402
from village_kit.components.timber_walls import path_timber_wall  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v8_byre_smokehouse"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
DIM = KitParams(half=2.5, x0=-6.0, x1=6.0, wall_z=2.4, pitch=46.0, crown=0.50, door_x=-2.6, stack_x=6.15,
                stack_r=1.0, stack_batter=3.5, shoulder_z=2.9, brow_x=1.8, lean_x=-1.2, lean_depth=1.8,
                lean_zface=2.44)
HALF, X0, X1 = DIM["half"], DIM["x0"], DIM["x1"]

BROW = eyebrow(DIM["brow_x"], side=-1, grid="thatch", profile="arch", respace=True, d=1.3, width=2.5, height=0.90,
               lip=0.22, plateau=0.15, fade=1.1, window=dict(width=0.60, height=0.45, sill=0.05), close_ends=True,
               span_rows=True, seed=3)
LIFT_N = eave_lift(DIM["lean_x"], side=1, width=7.5, height=1.6, fade=2.4)       # back eave arch over the lean-to
LIFT_S = eave_lift(DIM["door_x"], side=-1, width=4.0, height=0.55, fade=1.4)    # front: lifts the eave over the cart door (lip >= 2.30)
LIFT_MAX = 0.08
MAIN = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.45,
                 verge=(0.0, 0.0), thick=0.28, name="roof", ridge_sag=0.15, eave_sag=0.04, eave_sweep=0.16,
                 sweep_len=1.0, wave=0.02, wave_seed=71, ridge_seat=True, hips="both", hip_seam=(-1, 0.0),
                 crown=DIM["crown"], eyebrows=[BROW], eave_lifts=[LIFT_N, LIFT_S])

PATH = [(X1, 0.0), (X1, HALF), (X0, HALF), (X0, -HALF), (X1, -HALF), (X1, 0.0)]
S_N, S_W, S_F = HALF, HALF + (X1 - X0), HALF + (X1 - X0) + 2 * HALF
WIN = window(width=0.50, height=0.60, sill=1.05)
SMALL = window(width=0.40, height=0.45, sill=1.20)
DOOR_S = S_F + (DIM["door_x"] - X0)
OPENINGS = [(S_N + (X1 - 4.2), SMALL), (S_N + (X1 - 1.0), WIN),                             # back (north)
            (S_W + (HALF - 0.8), SMALL),                                                       # west end
            (DOOR_S, door(width=1.7, height=2.05, threshold=0.14)),                           # the wide cart door
            (S_F + (0.6 - X0), WIN), (S_F + (4.2 - X0), SMALL)]                              # front windows
TOP = roofs_top_fn([MAIN])
Z_CAP = DIM["wall_z"] - 0.30


def _end_span(lim):
    ss = np.linspace(0.0, lim, 400)
    ok = [s for s in ss if TOP(X1, s) >= Z_CAP + 0.35]
    return float(max(ok)) if ok else 0.0


YT = _end_span(HALF)


def stone_top(x, y):
    z = TOP(x, y)
    if (abs(x - X1) < 0.75 or abs(x - X0) < 0.75) and abs(y) < YT:
        return min(z, Z_CAP)
    return z


GABLETS = [("hip_end_W", [(X0, YT), (X0, -YT)], 0.0),
           ("hip_end_E_s", [(X1, -YT), (X1, -0.30)], 0.16), ("hip_end_E_n", [(X1, 0.30), (X1, YT)], 0.16)]
FOOT = [(X0, -HALF), (X1, -HALF), (X1, HALF), (X0, HALF)]

LEAN = dict(name="lean_to", W=plane_wall((DIM["lean_x"], HALF), (0.0, 1.0)), s0=-2.2, s1=2.2,
            depth=DIM["lean_depth"], z_face=DIM["lean_zface"], pitch_deg=13.0, overhang=0.12, verge=(0.18, 0.18),
            covering="shingle", ends="rubble", end_t=0.40, max_span=1.8, brace=(0.36, 0.20), headroom=(1.7, 1.55),
            soft=dict(ridge_sag=-0.15, eave_sweep=0.06, sweep_len=0.6, wave=0.012, verge_flare=0.06, flare_len=0.5),
            below=MAIN, gate=False, below_lift_max=LIFT_MAX, below_clear=0.05, below_roll=0.10, seed=1901,
            roof_ends="round", round_kw=dict(end_over=0.45, hip=0.55, ne=3.0, bulge=0.04, arch_wall=0.15,
                                             arch_eave=0.18, wave=0.012, thatch=(0.22, 0.08), course=0.30,
                                             eave_roll={}, decals=True))


def steps():
    deck = lambda roof: (lambda P: roof.under_z_world(P))  # noqa: E731
    in_house = inside_box(X0 + 0.15, X1 - 0.15, -HALF + 0.15, HALF - 0.15, z_fn=deck(MAIN))
    base = inside_round((DIM["stack_x"], 0.0), DIM["stack_r"], depth=0.12, batter_deg=DIM["stack_batter"])
    upper = inside_round((DIM["stack_x"], 0.0), 0.72, depth=0.12, batter_deg=1.5)

    def in_stack(P, margin=0.0):
        P = np.asarray(P, float)
        return np.where(P[:, 2] < DIM["shoulder_z"], base(P, margin), upper(P, margin))
    return [
        (set_entrance, dict(xy=(DIM["door_x"], -HALF))),
        (path_stone_wall, dict(name="walls", path=PATH, top_fn=stone_top, openings=OPENINGS, clip=in_stack,
                               cfg=RUBBLE_LARGE, hero_s=(DOOR_S - 2.5, DOOR_S + 2.5), seed=31)),
    ] + [(path_timber_wall, dict(name=nm, path=pth, z0=Z_CAP - dz, top=Z_CAP + 0.26, top_fn=TOP, style="post_plank",
                                 gable_style="board_batten", rough=True, seed=331 + k))
         for k, (nm, pth, dz) in enumerate(GABLETS)] + [
        (linear_roof, dict(roof=MAIN, covering="thatch", seed=71, comb=False, rafter_lift_max=LIFT_MAX)),
        (chimney, dict(name="chimney", center=(DIM["stack_x"], 0.0), r_base=DIM["stack_r"],
                       batter_deg=DIM["stack_batter"], roof=MAIN, clip=in_house, crown="pot", over_ridge=0.62, seed=51,
                       shoulder=dict(z=DIM["shoulder_z"], r_base=0.72, batter_deg=1.5, h=0.30),
                       pot=dict(r=0.19, h=0.46), abut=dict(ring_fillet=dict(out=0.22, h_up=0.18, bury=0.06, step_deg=1.5)))),
        (orient_open_islands, dict(parts=("_stones",))),
        (orient_closed_slabs, dict(parts=("_deck",))),
        (lean_to, LEAN),
    ] + ([] if os.environ.get("BYRE_FAST") else
         [(hidden_cull, dict(min_polys=200, extra_views=reentrant_views(FOOT)))]) + [recenter]


def decals(g):
    with straight_span(MAIN):
        composite_decals(g, moss_normal="slope", timber=True, timber_soot=False)
    chimney_decals(g)


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_roof_blocker",
                                       "_cap_collar", "_abutment"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("BYRE_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="BYRE", collection="BYRE", building_id=BID, frame=PlanFrame,
        params=dict(footprint=FOOT, entrance=(DIM["door_x"], -HALF)),
        steps=steps(), decals=decals, decal_validate=DECAL_VALIDATE, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(dims=dict(DIM), datum=dict(ground_z=0.0, note="built on the plan, then recentred"))))


if __name__ == "__main__":
    main()







