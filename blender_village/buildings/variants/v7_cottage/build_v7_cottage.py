"""v7_cottage (COTT) -- a low L-plan village cottage, round 1: the proof of the kit 1.19 ROOF add-ons (plan step 4).
A declarative RECIPE: every piece is a village_kit module; the building is dimensions + the order of the steps.

Run:  python -I build_v7_cottage.py  -> v7_cottage.blend + decal_anchors.json (next to this file)
      COTT_FAST=1 skips the hidden-geometry cull (quick looks only); COTT_OUT=<path.blend> writes elsewhere.

Built on the plan (x along the main ridge, the front long side at y = -HALF, ground Z = 0), then recentred.
  main    a storey-and-a-half rubble house 10.0 x 5.5 m (path_stone_wall, RUBBLE_LARGE) under a steep 52 deg soft
          thatch (GableRoof ridge sag, swept and sagging eaves, flared verges, out-of-true wave, seated ridge roll)
  wing    the cross wing 4.8 x 5.25 m projecting from the front under its own soft 47 deg thatch, which runs into the
          main slope in a ROLLED THATCH VALLEY each side and over its ridge (roof_addons.roof_valley)
  dormer  a GABLED DORMER on the main front slope over the door (roof_addons.gabled_dormer): rough board-and-batten
          front and cheeks with the kit window, its own small soft thatch with a lead hat and turned finial, the
          valley into the main slope and a rolled thatch foot round its walls
  chimney a ROUND battered rubble STACK at the east gable (roof_addons.chimney): the main roof runs into it with the
          v3 / v5 lime-mortar flaunching and lead aprons (wall_abutment), a dressed drip-course cap, and a round
          SMOKE LOUVRE -- dressed posts under a little lead cone with the village's turned finial
  doors   a plank door with a threshold stone under the dormer, small deep-set windows
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull, inside_box,  # noqa: E402
                                              inside_round, recenter, set_entrance)
from village_kit.components.linear_roof import GableRoof, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.roof_addons import (GabledDormer, any_clip, chimney, chimney_decals,  # noqa: E402
                                                deck_clip, gabled_dormer, roof_valley, roofs_top_fn, solid_clip)
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v7_cottage"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
DIM = KitParams(half=2.75, x0=-5.0, x1=5.0, wall_z=2.85, pitch=52.0, wing_x=1.5, wing_half=2.4, wing_y0=-8.0,
                wing_pitch=47.0, door_x=-3.0, stack_x=5.30, stack_r=1.05, stack_batter=3.5, shoulder_z=4.7)
HALF, X0, X1 = DIM["half"], DIM["x0"], DIM["x1"]
WX, WH, WY0 = DIM["wing_x"], DIM["wing_half"], DIM["wing_y0"]
MAIN = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.45,
                 verge=(0.40, 0.40), thick=0.28, name="roof", ridge_sag=0.18, eave_sag=0.04, eave_sweep=0.18,
                 sweep_len=1.0, verge_flare=0.20, flare_len=1.5, wave=0.02, wave_seed=71, ridge_seat=True)
# the cross wing: its ridge runs along world y (yaw 90: local x = world y), its free gable at WY0, its other end
# buried in the main roof at the main ridge line (verge 0 there)
WING = GableRoof(x0=WY0, x1=0.0, half=WH, wall_z=DIM["wall_z"], pitch_deg=DIM["wing_pitch"], overhang=0.45,
                 verge=(0.40, 0.0), origin=(WX, 0.0), yaw_deg=90.0, thick=0.28, name="wing_roof", ridge_sag=0.12,
                 eave_sag=0.03, eave_sweep=0.15, sweep_len=0.9, verge_flare=0.18, flare_len=1.3, wave=0.02,
                 wave_seed=73, ridge_seat=True)
DORMER = GabledDormer(MAIN, x=DIM["door_x"], side=-1, d=0.35, width=1.30, pitch=50.0, overhang=0.22, verge=0.28,
                      window=dict(width=0.55, height=0.45, sill=0.30, lights=2), name="dormer")

# ---- plan: one path round the L from inside the chimney stack and back (interior on the left) -------------------
PATH = [(X1, 0.0), (X1, HALF), (X0, HALF), (X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0),
        (WX + WH, -HALF), (X1, -HALF), (X1, 0.0)]
_S = [0.0]
for _a, _b in zip(PATH[:-1], PATH[1:]):
    _S.append(_S[-1] + abs(_b[0] - _a[0]) + abs(_b[1] - _a[1]))
S_N, S_W, S_F, S_WW, S_WS, S_WE = _S[1], _S[2], _S[3], _S[4], _S[5], _S[6]
WIN = window(width=0.50, height=0.60, sill=1.05)
SMALL = window(width=0.40, height=0.45, sill=1.20)
DOOR_S = S_F + (DIM["door_x"] - X0)
OPENINGS = [(S_N + (X1 - 2.6), WIN), (S_N + (X1 + 1.2), WIN), (S_N + (X1 + 3.6), SMALL),     # back (north)
            (S_W + (HALF - 0.9), SMALL),                                                       # west gable
            (DOOR_S, door(width=1.0, height=1.95, threshold=0.14)),                            # the front door
            (S_F + (WX - WH - 0.75 - X0), SMALL),                                              # front, by the wing
            (S_WW + 2.9, WIN),                                                                 # wing west side
            (S_WS + WH, window(width=0.55, height=0.65, sill=1.05)),                           # wing gable
            (S_WE + 2.5, WIN)]                                                                 # wing east side
TOP = roofs_top_fn([MAIN, WING])


def steps():
    deck = lambda roof: (lambda P: roof.under_z_world(P))  # noqa: E731
    in_house = inside_box(X0 + 0.15, X1 - 0.15, -HALF + 0.15, HALF - 0.15, z_fn=deck(MAIN))
    base = inside_round((DIM["stack_x"], 0.0), DIM["stack_r"], depth=0.12, batter_deg=DIM["stack_batter"])
    upper = inside_round((DIM["stack_x"], 0.0), 0.72, depth=0.12, batter_deg=1.5)

    def in_stack(P, margin=0.0):            # the broad base below the shoulder, the narrower stack above it
        P = np.asarray(P, float)
        return np.where(P[:, 2] < DIM["shoulder_z"], base(P, margin), upper(P, margin))
    return [
        (set_entrance, dict(xy=(DIM["door_x"], -HALF))),
        (path_stone_wall, dict(name="walls", path=PATH, top_fn=TOP, openings=OPENINGS, clip=in_stack, cfg=RUBBLE_LARGE,
                               hero_s=(DOOR_S - 2.5, DOOR_S + 2.5), seed=31)),
        (linear_roof, dict(roof=MAIN, covering="thatch", seed=71, ridge_caps=True, verge_apex=True,
                           clip=any_clip(solid_clip(WING), DORMER.clip_main()),
                           deck_clip=any_clip(deck_clip(WING), DORMER.deck_clip_main()),
                           apex_finial="turned", apex_ends=("lo",), verge_roll=dict(apex_bend=0.22, bend_over=0.12),
                           comb_step=0.75, comb_backing=True)),
        (linear_roof, dict(roof=WING, covering="thatch", seed=72, ridge_caps=True, verge_apex=True,
                           clip=solid_clip(MAIN), deck_clip=deck_clip(MAIN), apex_finial="turned",
                           verge_roll=dict(apex_bend=0.22, bend_over=0.12), comb_step=0.75, comb_backing=True)),
        (roof_valley, dict(main=MAIN, wing=WING, name="wing_valley", seed=5)),
        (gabled_dormer, dict(D=DORMER, seed=81, verge_roll=dict(rc=0.22, apex_bend=0.16, bend_over=0.10))),
        (chimney, dict(name="chimney", center=(DIM["stack_x"], 0.0), r_base=DIM["stack_r"],
                       batter_deg=DIM["stack_batter"], roof=MAIN, clip=in_house, crown="pot", over_ridge=0.62, seed=51,
                       shoulder=dict(z=DIM["shoulder_z"], r_base=0.72, batter_deg=1.5, h=0.30),
                       pot=dict(r=0.19, h=0.46))),
    ] + ([] if os.environ.get("COTT_FAST") else [(composite_hidden_cull, dict(min_polys=200))]) + [recenter]


def decals(g):
    composite_decals(g, moss_normal="slope", timber=True, timber_soot=False)
    chimney_decals(g)


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_roof_blocker",
                                       "_cap_collar", "_abutment"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,      # v3 / v6: stepped thatch courses
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("COTT_OUT", os.path.join(HERE, BID + ".blend"))
    foot = [(X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0), (WX + WH, -HALF), (X1, -HALF), (X1, HALF),
            (X0, HALF)]
    build_building(dict(
        prefix="COTT", collection="COTT", building_id=BID, frame=PlanFrame,
        params=dict(footprint=foot, entrance=(DIM["door_x"], -HALF)),
        steps=steps(), decals=decals, decal_validate=DECAL_VALIDATE, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(dims=dict(DIM), datum=dict(ground_z=0.0, note="built on the plan, then recentred"))))


if __name__ == "__main__":
    main()
