"""v7_cottage (COTT) -- a low L-plan village cottage, round 4: the proof of the kit ROOF add-ons (plan step 4) on
ROUNDED "loaf" roofs (producer note 19: "an oval on the rectangle") with a THATCH EYEBROW (producer note 18).
A declarative RECIPE: every piece is a village_kit module; the building is dimensions + the order of the steps.

Run:  python -I build_v7_cottage.py  -> v7_cottage.blend + decal_anchors.json (next to this file)
      COTT_FAST=1 skips the hidden-geometry cull (quick looks only); COTT_OUT=<path.blend> writes elsewhere.

Built on the plan (x along the main ridge, the front long side at y = -HALF, ground Z = 0), then recentred.
  main    a storey-and-a-half rubble house 11.0 x 5.5 m (path_stone_wall, RUBBLE_LARGE) under a soft thatch LOAF:
          GableRoof(hips="both", crown=...) -- a ROUND HIP (half-cone) at both ends, so the eave runs round the
          house as one oval oversailing the corners, a softly convex section easing into the rolled ridge, which
          rounds over each hip as a dome; ridge sag, swept and sagging eaves, out-of-true wave; no gable, no comb
          A THATCH EYEBROW on the back slope (eyebrow(grid="thatch", profile="arch", respace=True)): the courses roll
          over one continuous arch, the eave roll runs over it as a rolled lip, the kit window in a rough-boarded
          front under it
  wing    the cross wing 4.8 x 5.25 m projecting from the front under its own thatch loaf (a round hip at its free S
          end, no hip at the joined end), which runs into the main slope in a ROLLED THATCH VALLEY each side and
          over its ridge (roof_addons.roof_valley); at each inside corner the eave roll runs round in one swept
          internal-corner roll over a boarded soffit
  dormer  a GABLED DORMER on the main front slope over the door (roof_addons.gabled_dormer): rough board-and-batten
          front and cheeks with the kit window, its own small soft thatch with a lead hat and turned finial, a slim
          rolled hood scaled to the dormer, the valley into the main slope and a rolled thatch foot round its walls
  chimney a ROUND battered rubble STACK at the east end (roof_addons.chimney): a broad battered base against the
          end wall, a rounded dressed-stone weathering at the shoulder, the stack rising THROUGH THE EAST ROUND HIP
          (the hip surrounds it: a closed ring of lime flaunching) to about 0.8 m over the ridge, a dressed drip-course
          cap and a ROUND dressed-stone POT
  doors   a plank door with a threshold stone under the dormer, small deep-set windows
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.composite import (composite_decals, inside_box, inside_round, recenter,  # noqa: E402
                                              set_entrance)
from village_kit.components.linear_roof import GableRoof, eyebrow, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.orient_fix import orient_closed_slabs, orient_open_islands  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.roof_addons import (GabledDormer, any_clip, chimney, chimney_decals,  # noqa: E402
                                                deck_clip, gabled_dormer, hidden_cull, reentrant_views, roof_valley,
                                                roofs_top_fn, solid_clip, straight_span)
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall  # noqa: E402
from village_kit.components.timber_walls import path_timber_wall  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v7_cottage"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
# round 5: main 49 deg (was 47; the bible's 48-52 thatch range) and a lower wing (42 deg, crown 0.12; was 44 / 0.35)
# -- the wing's ridge and its S hip dome sit ~0.55 m further under the main ridge, so nothing of the wing stands
# proud of the main ridge from the north (the round-4 "knob")
DIM = KitParams(half=2.75, x0=-5.5, x1=5.5, wall_z=2.85, pitch=49.0, crown=0.55, wing_x=1.0, wing_half=2.4,
                wing_y0=-8.0, wing_pitch=42.0, wing_crown=0.12, door_x=-3.1, stack_x=5.65, stack_r=1.05,
                stack_batter=3.5, shoulder_z=3.0, brow_x=-0.8)
HALF, X0, X1 = DIM["half"], DIM["x0"], DIM["x1"]
WX, WH, WY0 = DIM["wing_x"], DIM["wing_half"], DIM["wing_y0"]
BROW = eyebrow(DIM["brow_x"], side=1, grid="thatch", profile="arch", respace=True, d=1.3, width=2.5, height=0.90,
               lip=0.22, plateau=0.15, fade=1.1, window=dict(width=0.60, height=0.36, sill=0.05), close_ends=True,
               span_rows=True, seed=3)
MAIN = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.45,
                 verge=(0.0, 0.0), thick=0.28, name="roof", ridge_sag=0.15, eave_sag=0.04, eave_sweep=0.16,
                 sweep_len=1.0, wave=0.02, wave_seed=71, ridge_seat=True, hips="both", hip_seam=(-1, WX),
                 crown=DIM["crown"], eyebrows=[BROW])
# the cross wing: its ridge runs along world y (yaw 90: local x = world y), a round hip at its free S end (WY0),
# its other end buried in the main roof at the main ridge line (no hip there)
WING = GableRoof(x0=WY0, x1=0.0, half=WH, wall_z=DIM["wall_z"], pitch_deg=DIM["wing_pitch"], overhang=0.45,
                 verge=(0.0, 0.0), origin=(WX, 0.0), yaw_deg=90.0, thick=0.28, name="wing_roof", ridge_sag=0.10,
                 eave_sag=0.03, eave_sweep=0.14, sweep_len=0.9, wave=0.02, wave_seed=73, ridge_seat=True,
                 hips=("lo",), crown=DIM["wing_crown"])
DORMER = GabledDormer(MAIN, x=DIM["door_x"], side=-1, d=0.35, width=1.30, pitch=50.0, overhang=0.22, verge=0.28,
                      window=dict(width=0.55, height=0.45, sill=0.30, lights=2), name="dormer")

# ---- plan: one path round the L from inside the chimney stack and back (interior on the left) -------------------
PATH = [(X1, 0.0), (X1, HALF), (X0, HALF), (X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0),
        (WX + WH, -HALF), (X1, -HALF), (X1, 0.0)]
_S = [0.0]
for _a, _b in zip(PATH[:-1], PATH[1:]):
    _S.append(_S[-1] + abs(_b[0] - _a[0]) + abs(_b[1] - _a[1]))
S_N, S_W, S_F, S_WW, S_WS, S_WE, S_FE = _S[1], _S[2], _S[3], _S[4], _S[5], _S[6], _S[7]
WIN = window(width=0.50, height=0.60, sill=1.05)
SMALL = window(width=0.40, height=0.45, sill=1.20)
DOOR_S = S_F + (DIM["door_x"] - X0)
OPENINGS = [(S_N + (X1 - 2.8), WIN), (S_N + (X1 - DIM["brow_x"]), SMALL), (S_N + (X1 + 3.7), WIN),   # back (north)
            (S_W + (HALF - 0.9), SMALL),                                                       # west end
            (DOOR_S, door(width=1.0, height=1.95, threshold=0.14)),                            # the front door
            (S_F + (-2.0 - X0), SMALL),                                                        # front, by the wing
            (S_WW + 2.9, WIN),                                                                 # wing west side
            (S_WS + WH, window(width=0.55, height=0.65, sill=1.05)),                           # wing south end
            (S_WE + 2.5, WIN),                                                                 # wing east side
            (S_FE + (4.6 - (WX + WH)), SMALL)]                                                 # front, east
TOP = roofs_top_fn([MAIN, WING])
# under each ROUND HIP the end wall would rise into the hip's deep, dark oversail (a stone gablet nobody sees): the
# rubble stops at Z_CAP there and a rough board-and-batten HIP-END GABLET (timber_walls.path_timber_wall, the
# village's boards) closes the attic up to the deck -- "rubble with rough timber where it suits" (the Brief)
Z_CAP = DIM["wall_z"] - 0.30


def _end_span(xy_fn, lim):
    """half length of an end wall over which the deck underside stands >= Z_CAP + 0.35 (the gablet's run)."""
    ss = np.linspace(0.0, lim, 400)
    ok = [s for s in ss if TOP(*xy_fn(s)) >= Z_CAP + 0.35]
    return float(max(ok)) if ok else 0.0


YT = _end_span(lambda s: (X1, s), HALF)
YT_W = _end_span(lambda s: (WX + s, WY0), WH)


def stone_top(x, y):
    z = TOP(x, y)
    if ((abs(x - X1) < 0.75 or abs(x - X0) < 0.75) and abs(y) < YT) or (abs(y - WY0) < 0.75 and abs(x - WX) < YT_W):
        return min(z, Z_CAP)
    return z


# (name, path, z0 drop): round 5 -- the E gablets either side of the stack run 0.2 m on INTO the stack and stand
# 0.16 m lower, so their backing closes the stack / gablet / wall-head joint from inside (the i06 pinhole)
GABLETS = [("hip_end_W", [(X0, YT), (X0, -YT)], 0.0),
           ("hip_end_E_s", [(X1, -YT), (X1, -0.30)], 0.16), ("hip_end_E_n", [(X1, 0.30), (X1, YT)], 0.16),
           ("hip_end_S", [(WX - YT_W, WY0), (WX + YT_W, WY0)], 0.0)]
FOOT = [(X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0), (WX + WH, -HALF), (X1, -HALF), (X1, HALF),
        (X0, HALF)]

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
        (path_stone_wall, dict(name="walls", path=PATH, top_fn=stone_top, openings=OPENINGS, clip=in_stack,
                               cfg=RUBBLE_LARGE, hero_s=(DOOR_S - 2.5, DOOR_S + 2.5), seed=31)),
    ] + [(path_timber_wall, dict(name=nm, path=pth, z0=Z_CAP - dz, top=Z_CAP + 0.26, top_fn=TOP, style="post_plank",
                                 gable_style="board_batten", rough=True, seed=331 + k))
         for k, (nm, pth, dz) in enumerate(GABLETS)] + [
        (linear_roof, dict(roof=MAIN, covering="thatch", seed=71, comb=False,
                           clip=any_clip(solid_clip(WING), DORMER.clip_main()),
                           deck_clip=any_clip(deck_clip(WING), DORMER.deck_clip_main()))),
        (linear_roof, dict(roof=WING, covering="thatch", seed=72, comb=False,
                           clip=solid_clip(MAIN), deck_clip=deck_clip(MAIN))),
        # round 5: the wing's ridge roll runs 0.35 m PAST the arch's crest and ends buried in the main thatch (no cut
        # end / pocket under the arch); each internal-corner roll sinks into the straight eave rolls over a long
        # smoothstep overlap (no sleeve band)
        (roof_valley, dict(main=MAIN, wing=WING, name="wing_valley", seed=5, ridge_cut=-0.35, ridge_bury=0.25, ridge_bury_w=0.45,
                           corner_opts=dict(cut=0.08, past=0.02, roll=dict(ext=0.60, blend=0.42, grow=1.08, end_f=0.90)))),
        (gabled_dormer, dict(D=DORMER, seed=81)),                    # the hood: dormer_verge_roll(D.hw)
        (chimney, dict(name="chimney", center=(DIM["stack_x"], 0.0), r_base=DIM["stack_r"],
                       batter_deg=DIM["stack_batter"], roof=MAIN, clip=in_house, crown="pot", over_ridge=0.62, seed=51,
                       shoulder=dict(z=DIM["shoulder_z"], r_base=0.72, batter_deg=1.5, h=0.30),
                       pot=dict(r=0.19, h=0.46), abut=dict(ring_fillet=dict(out=0.22, h_up=0.18, bury=0.06, step_deg=1.5)))),
        # round 5: the r4 "cull holes" at the W inside corner were wall stones finalize had turned to face INTO the
        # wall (present on the uncut FAST build too); every inverted open-backed stone shell is flipped back
        (orient_open_islands, dict(parts=("_stones",))),
        (orient_closed_slabs, dict(parts=("_deck",))),
    ] + ([] if os.environ.get("COTT_FAST") else
         # round 5: the lean cull PLUS eye-level views into both re-entrant corners (the door's inside corner, the
         # valley feet), which the bounding-box loops never see
         [(hidden_cull, dict(min_polys=200, extra_views=reentrant_views(FOOT)))]) + [recenter]


def decals(g):
    with straight_span(MAIN, WING):         # the moss anchors on the straight slopes (not on the folded hips)
        composite_decals(g, moss_normal="slope", timber=True, timber_soot=False)
    chimney_decals(g)


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_roof_blocker",
                                       "_cap_collar", "_abutment"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,      # v3 / v6: stepped thatch courses
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("COTT_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="COTT", collection="COTT", building_id=BID, frame=PlanFrame,
        params=dict(footprint=FOOT, entrance=(DIM["door_x"], -HALF)),
        steps=steps(), decals=decals, decal_validate=DECAL_VALIDATE, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(dims=dict(DIM), datum=dict(ground_z=0.0, note="built on the plan, then recentred"))))


if __name__ == "__main__":
    main()
