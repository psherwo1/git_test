"""v3_longhouse_roundend (LONG) -- ref1 (lower middle): a long, low stone longhouse under a layered thatch roof, ending
in a round stone house under a mossy conical shingle roof with a stone ball finial.  A declarative RECIPE: every
piece is a village_kit module, the building is only dimensions + the order of the steps.

Run:  python build_v3_longhouse_roundend.py   -> v3_longhouse_roundend.blend + decal_anchors.json (next to this file)
      LONG_FAST=1 skips the hidden-geometry ray test (quick looks only); LONG_OUT=<path.blend> writes elsewhere.

Plan (built with the round end's centre at the origin, then recentred on the plan bounding box):
  round end   round 8 (client direction 2026-10-17): RAISED -- a battered round rubble body (face r 3.70 m at the
              ground, 1.5 deg batter) rising one storey past the longhouse ridge to a 6.0 m eave, two ground-floor
              and three upper-storey deep-set windows; RoundFrame cone 48 deg (eave radius 4.22 m) on a masonry
              beam-fill on the wall head, boarded soffit under the overhang; stone ball finial over a 44 deg lead hat
  body        rubble walls 13.0 x 5.2 m (outer faces) from the gable to the round end, dressed corner quoins, the
              principal door (-Y) and three windows; a 40 deg thatch gable roof (continuous layered courses, D eave
              roll, closed verge face) with ridge roll and shake comb, eave lip >= 2.30 m over the door
  junction    "gable roof abutting a round wall" (roof_junction.wall_abutment): the thatch, its eave rolls, ridge and
              comb run INTO the drum and are trimmed at its face; a lime-mortar flaunching follows the true
              roof / cylinder intersection and lead end-aprons close each eave against the stone.  The two eaves no
              longer meet (the cone's eave lip is >= 0.25 m over the thatch where it meets the wall, checked)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.rubble_walls import path_stone_wall, round_stone_body  # noqa: E402
from village_kit.components.wall_openings import door_spec, window_spec  # noqa: E402
from village_kit.components.linear_roof import GableRoof, linear_roof  # noqa: E402
from village_kit.components.roof_junction import round_eave_fill, wall_abutment  # noqa: E402
from village_kit.components.ball_finial import ball_finial  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull, cone_roof,  # noqa: E402
                                              inside_box, inside_round, recenter, set_entrance)

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v3_longhouse_roundend"

# ---- the round end: a RoundFrame (plate centre line radius, eave, cone); round 8: the eave raised past the ridge --
KIT = KitParams(radius=3.50, eave_z=6.00, overhang=0.72, pitch_deg=48.0, collar_r=0.62,
                cone_age=age_defaults(**AGE_R10), detail_rule=True)
R_FACE, BATTER = 3.70, 1.5                     # round rubble face radius at the ground, batter (deg): 3.53 m at the head

# ---- the body: plan, walls, roof ---------------------------------------------------------------------------------
# kit 1.9.0 (guard clearance): the deck at the faces is 2.81 m so the rafter feet over the door clear 2.30 m
X_GABLE, HALF, WALL_Z = -13.0, 2.6, 2.81       # gable outer face, half width at the outer faces, deck at the faces
ROOF = GableRoof(x0=X_GABLE, x1=-0.6, half=HALF, wall_z=WALL_Z, pitch_deg=40.0, overhang=0.45, verge=(0.40, 0.0),
                 thick=0.30, step=0.10, exposure=0.30, name="body_roof")
X_END = -2.0                                   # the body walls run into the round wall (clipped there)
BODY_PATH = [(X_END, HALF), (X_GABLE, HALF), (X_GABLE, -HALF), (X_END, -HALF)]   # interior on the left
north = lambda x: X_END - x                                   # noqa: E731  path distance of x on the north wall
south = lambda x: (X_END - X_GABLE) + 2 * HALF + (x - X_GABLE)  # noqa: E731  ... on the south (entrance) wall
DOOR_X = -7.0
BODY_OPENINGS = [(north(-6.2), window_spec(sill=1.25)),
                 (north(-10.4), window_spec(sill=1.30, width=0.45)),
                 (south(-10.6), window_spec(sill=1.30, width=0.45)),
                 (south(DOOR_X), door_spec(width=1.0, height=2.10)),
                 (south(-4.3), window_spec(sill=1.25))]
UPPER = window_spec(sill=3.70, width=0.45, height=0.60)          # round 8: the raised storey's windows
ROUND_OPENINGS = [(38.0, window_spec(sill=1.20, width=0.45, height=0.50)),
                  (128.0, window_spec(sill=1.25, width=0.45, height=0.50)),
                  (8.0, UPPER), (88.0, UPPER), (168.0, UPPER)]


def body_top(x, y):
    """wall heads tuck 2 cm into the roof deck (the gable follows the rake)."""
    return float(ROOF.under_z(ROOF.to_local([[x, y, 0.0]])[0][1])) + 0.02


def under_deck(P):
    """deck underside over each point: the round wall is dropped only inside the body, under its roof."""
    return ROOF.under_z(ROOF.to_local(P)[:, 1])


def steps():
    in_body = inside_box(X_GABLE, -0.3, -HALF + 0.15, HALF - 0.15, z_fn=under_deck)  # body interior, under the deck
    in_round = inside_round((0.0, 0.0), R_FACE, depth=0.12, batter_deg=BATTER)
    at_round = inside_round((0.0, 0.0), R_FACE, depth=-0.10, batter_deg=BATTER)   # within 10 cm of the round face
    in_drum = inside_round((0.0, 0.0), R_FACE, depth=0.10, batter_deg=BATTER)     # roof parts deep in the drum
    return [
        (set_entrance, dict(xy=(DOOR_X, -HALF))),
        (round_stone_body, dict(name="round_wall", r_base=R_FACE, batter_deg=BATTER, openings=ROUND_OPENINGS,
                                clip=in_body, open_z="mid", seed=41)),
        (path_stone_wall, dict(name="body_wall", path=BODY_PATH, top_fn=body_top, openings=BODY_OPENINGS,
                               clip=in_round, hero_s=(south(DOOR_X - 3.0), south(DOOR_X + 3.0)), seed=31)),
        (linear_roof, dict(roof=ROOF, covering="thatch", clip=in_drum, seed=71,
                           rafter_skip=at_round, ridge_caps=True, verge_apex=True)),
        (wall_abutment, dict(roof=ROOF, center=(0.0, 0.0))),      # round 8: gable roof into the round wall
        (cone_roof, dict(seed=606)),                              # the cone sits clear above the thatch
        (ball_finial, dict(seed=5, hat_seg=96, fit=True)),
        (round_eave_fill, dict(z_bot="wall", r_off=-0.03)),       # masonry beam-fill on the wall head
    ] + ([] if os.environ.get("LONG_FAST") else [composite_hidden_cull]) + [recenter]


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15,
                      exclude_objects=("_deck", "_blockers", "_reveals", "_roof_blocker", "_eave_fill",
                                       "_roof_underlap", "_apex_blocker"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"),
                      walk_zones="da")                       # no lichen / moss on a door's trodden tops


def main():
    from functools import partial
    out = os.environ.get("LONG_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="LONG", collection="LONG", building_id=BID,
        frame=RoundFrame, params=KIT,
        steps=steps(),
        decals=partial(composite_decals, moss_normal="slope"),        # moss on the slope normal
        decal_validate=DECAL_VALIDATE,
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items() if k != "cone_age"},
                        body=dict(x_gable=X_GABLE, half=HALF, wall_z=WALL_Z, pitch_deg=40.0)),
    ))


if __name__ == "__main__":
    main()
