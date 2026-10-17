"""v1_stone_watchtower -- a round stone lookout tower, assembled purely from the shared village kit (phase 2 variant).

Run:  python build_v1_stone_watchtower.py  -> v1_stone_watchtower.blend + decal_anchors.json (next to this script)
      WATCH_OUT=<path.blend>  writes elsewhere (scratch);  WATCH_FAST=1  skips the hidden-geometry cull (look-dev only)

Recipe (top to bottom = build order; every line is a kit module, numbers live in KIT):
  drum family   round_stone_drum     5.0 m battered coursed-rubble drum, 8.7 m to the cornice top, NO arcade, a plain
                                     dressed string course at the first floor (zones string=), arched door, three
                                     0.18 x 0.95 m stair lights rising round the shaft (window_size, window_z),
                                     dentil-corbelled cornice
                drum_wall_core       continuous wall core behind all masonry (note 6)
                entrance_step        built-in door step (note 10)
                drum_ceiling         ceiling over the ground floor seen through the door           (tower_roof)
  crown         square_cabin         5.4 m square timber watch cabin perched on the drum: bearers and joists
                                     on the wall head, knee struts on corbel pads, framed plank walls with two
                                     lookout openings per side, 48 deg square-pyramid shingle roof, hip boards,
                                     lead apex cap, turned finial                                  (NEW, square_cabin)
  finishing     drum_finish          parts -> objects, pooled corbels / pegs as linked duplicates
                tower_hidden_cull    note 6: analytic pre-cull, drum rays on unblocked views only     (tower_roof)
  anchors       round_tower_decals_gated   note 11, snapped / validated / audited                  (NEW, tower_decals)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.drum_frame import DrumFrame, drum_finish  # noqa: E402
from village_kit.components.drum_wall import drum_wall_core, round_stone_drum  # noqa: E402
from village_kit.components.drum_door import entrance_step  # noqa: E402
from village_kit.components.square_cabin import square_cabin  # noqa: E402
from village_kit.components.tower_roof import TOWER_CULL_TARGETS, drum_ceiling, tower_hidden_cull  # noqa: E402
from village_kit.components.tower_decals import round_tower_decals_gated  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BIG_RUBBLE = dict(hr=(0.10, 0.22), lr=(0.20, 0.70))          # larger, rougher coursing than the mill's drum

FRAME = dict(detail_rule=True, rubble=dict(plain=BIG_RUBBLE, spandrel=dict(BIG_RUBBLE, hbig=0.27, p_big=0.2)))
KIT = KitParams(
    drum=dict(r_base=2.48, r_top=2.18, height=8.70, batter_top="full",       # 2.1 deg batter, 4.96 m at the foot
              zones=dict(string=(5.35, 5.60)),                     # plain dressed string course at the first floor
              door=dict(width=1.05, spring=1.65, reveal=0.30),
              arcade=dict(n=0),                                    # no arcade
              windows=(60, -60, 180), window_z=(2.50, 3.95, 6.10),         # stair lights rising clockwise
              window_size=(0.18, 0.95),                                    # 0.18 x 0.95 m slits
              seed="watch"),
    core=dict(),
    step=dict(),
    ceiling=dict(z=3.45),
    cabin=dict(side=5.4, height=2.30, n_open=2, open_w=1.10, open_sill=0.95, open_h=1.10,   # timber watch cabin
               pitch_deg=48.0, eave_out=0.50, seed="watch"),
    finish=dict(checks=False),                                            # no rotor: skip the rotor clearances
    cull=dict(procs=2, targets=TOWER_CULL_TARGETS + ("cabin_shingles",)),  # shared machine: 2 cull workers
)


def main():
    out = os.environ.get("WATCH_OUT", os.path.join(HERE, "v1_stone_watchtower.blend"))
    steps = [(round_stone_drum, KIT["drum"]),
             (drum_wall_core, KIT["core"]),
             (entrance_step, KIT["step"]),
             (drum_ceiling, KIT["ceiling"]),
             (square_cabin, KIT["cabin"]),
             (drum_finish, KIT["finish"]),
             (tower_hidden_cull, KIT["cull"])]
    if os.environ.get("WATCH_FAST"):
        steps = steps[:-1]
    build_building(dict(
        prefix="WATCH", collection="WATCH", building_id="v1_stone_watchtower",
        frame=DrumFrame, params=FRAME, steps=steps,
        decals=round_tower_decals_gated,
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items()}),
    ))


if __name__ == "__main__":
    main()
