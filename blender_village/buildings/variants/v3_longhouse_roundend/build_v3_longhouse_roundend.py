"""v3_longhouse_roundend (LONG) -- ref1 (lower middle): a long, low stone longhouse under a layered thatch roof, ending
in a round stone house under a mossy conical shingle roof with a stone ball finial.  A declarative RECIPE: every
piece is a village_kit module, the building is only dimensions + the order of the steps.

Run:  python build_v3_longhouse_roundend.py   -> v3_longhouse_roundend.blend + decal_anchors.json (next to this file)
      LONG_FAST=1 skips the hidden-geometry ray test (quick looks only); LONG_OUT=<path.blend> writes elsewhere.

Plan (built with the round end's centre at the origin, then recentred on the plan bounding box):
  round end   RoundFrame cone 48 deg, eave radius 4.22 m, on a battered round rubble body (face r 3.64 m) with a
              pegged wall plate, an eave fill, a boarded soffit under the overhang and two deep-set windows; stone
              ball finial over a 44 deg lead hat with an apex blocker
  body        rubble walls 13.0 x 5.2 m (outer faces) from the gable to the round end, dressed corner quoins, the
              principal door (-Y) and three windows; a 40 deg thatch gable roof (continuous layered courses, D eave
              roll, closed verge faces) with ridge roll and shake comb, eave lip >= 2.30 m over the door
  junctions   body walls run into the round wall (clipped inside it), the round wall is dropped inside the body,
              the thatch runs under the cone (dropped inside the round wall head; under the cone's eave overhang it
              dies into the round wall), a lead flashing closes the slopes + ridge and a lead end-apron is folded
              over each eave roll under the cone's starter course
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.round_wall import wall_plate  # noqa: E402
from village_kit.components.rubble_walls import path_stone_wall, round_stone_body  # noqa: E402
from village_kit.components.wall_openings import door_spec, window_spec  # noqa: E402
from village_kit.components.linear_roof import GableRoof, linear_roof  # noqa: E402
from village_kit.components.roof_junction import cone_abutment, round_eave_fill  # noqa: E402
from village_kit.components.ball_finial import ball_finial  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull, cone_roof, inside_box,  # noqa: E402
                                              inside_round, recenter, set_entrance)

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v3_longhouse_roundend"

# ---- the round end: a RoundFrame (plate centre line radius, eave, cone) ----------------------------------------
KIT = KitParams(radius=3.50, eave_z=2.30, overhang=0.72, pitch_deg=48.0, collar_r=0.62,
                cone_age=age_defaults(**AGE_R10), detail_rule=True)
R_FACE, BATTER = 3.64, 2.5                     # round rubble face radius at the ground, batter (deg)

# ---- the body: plan, walls, roof ---------------------------------------------------------------------------------
X_GABLE, HALF, WALL_Z = -13.0, 2.6, 2.75       # gable outer face, half width at the outer faces, deck at the faces
ROOF = GableRoof(x0=X_GABLE, x1=-0.6, half=HALF, wall_z=WALL_Z, pitch_deg=40.0, overhang=0.45, verge=(0.40, 0.0),
                 thick=0.30, step=0.10, exposure=0.30, name="body_roof")
X_END = -2.0                                   # the body walls run 0.3 m into the round wall (clipped there)
BODY_PATH = [(X_END, HALF), (X_GABLE, HALF), (X_GABLE, -HALF), (X_END, -HALF)]   # interior on the left
north = lambda x: X_END - x                                   # noqa: E731  path distance of x on the north wall
south = lambda x: (X_END - X_GABLE) + 2 * HALF + (x - X_GABLE)  # noqa: E731  ... on the south (entrance) wall
DOOR_X = -7.0
BODY_OPENINGS = [(north(-6.2), window_spec(sill=1.25)),
                 (north(-10.4), window_spec(sill=1.30, width=0.45)),
                 (south(-10.6), window_spec(sill=1.30, width=0.45)),
                 (south(DOOR_X), door_spec(width=1.0, height=2.10)),
                 (south(-4.3), window_spec(sill=1.25))]
ROUND_OPENINGS = [(38.0, window_spec(sill=1.20, width=0.45, height=0.50)),
                  (128.0, window_spec(sill=1.25, width=0.45, height=0.50))]


def body_top(x, y):
    """wall heads tuck 2 cm into the roof deck (the gable follows the rake)."""
    return float(ROOF.under_z(ROOF.to_local([[x, y, 0.0]])[0][1])) + 0.02


def steps():
    in_body = inside_box(X_GABLE, -0.3, -HALF + 0.15, HALF - 0.15)          # interior of the body (round wall drop)
    in_round = inside_round((0.0, 0.0), R_FACE, depth=0.12, batter_deg=BATTER)
    return [
        (set_entrance, dict(xy=(DOOR_X, -HALF))),
        (round_stone_body, dict(name="round_wall", r_base=R_FACE, batter_deg=BATTER, openings=ROUND_OPENINGS,
                                clip=in_body, seed=41)),
        (wall_plate, dict(seed=303)),
        (path_stone_wall, dict(name="body_wall", path=BODY_PATH, top_fn=body_top, openings=BODY_OPENINGS,
                               clip=in_round, hero_s=(south(DOOR_X - 3.0), south(DOOR_X + 3.0)), seed=31)),
        (cone_roof, dict(seed=606, soffit_skip=in_body)),
        (ball_finial, dict(seed=5)),
        (round_eave_fill, dict(skip=in_body)),
        (linear_roof, dict(roof=ROOF, covering="thatch", abut_cone=(0.0, 0.0), seed=71)),
        (cone_abutment, dict(roof=ROOF, center=(0.0, 0.0))),
    ] + ([] if os.environ.get("LONG_FAST") else [composite_hidden_cull]) + [recenter]


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15,
                      exclude_objects=("_deck", "_blockers", "_reveals", "_roof_blocker", "_eave_fill",
                                       "_roof_underlap", "_apex_blocker"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("LONG_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="LONG", collection="LONG", building_id=BID,
        frame=RoundFrame, params=KIT,
        steps=steps(),
        decals=composite_decals,
        decal_validate=DECAL_VALIDATE,
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items() if k != "cone_age"},
                        body=dict(x_gable=X_GABLE, half=HALF, wall_z=WALL_Z, pitch_deg=40.0)),
    ))


if __name__ == "__main__":
    main()
