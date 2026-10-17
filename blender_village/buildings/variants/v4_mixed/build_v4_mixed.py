"""v4_mixed -- the MILL-HOUSE: a miller's daub roundhouse built against a small stone tower mill (kit variant 4).

A building type the village does not have yet, assembled only from kit modules of all three hero families:
  * HOUSE wing  (hut family, RoundFrame):  dry-stone plinth, wattle-and-daub wall, pegged wall plate, 51 deg
    chunky-shingle cone, framed door with step, interior -- crowned with the KEEP family's turned finial over a
    fitted lead hat (components.round_apex)
  * MILL wing   (drum family, DrumFrame):  a slender battered rubble drum (balustrade band and a 6-bay blind arcade
    lifted clear of the house roof, arched door and step, two slits), shake apron, boarded smock tower, hipped cap,
    12-blade fan wheel, tail vane on a rear boom
  * JUNCTIONS   (components.junctions):  the house cone runs into the drum -> traced roof / drum line closed by the
    KEEP family's flaunching (mortar fillet + stepped lead flashing) with lead end-aprons over the cut eave lips;
    the daub wall runs into the drum -> keep-family hewn abutment posts let into the masonry, mortar pointing
Assembly: village_kit.compound (several frames in one building, one hidden-geometry cull, decal anchors audited on
the whole building).  Producer notes 1-12; deterministic (every seed fixed).

Run:  python build_v4_mixed.py          -> v4_mixed.blend + decal_anchors.json next to this script
      V4_OUT=<path.blend>                build elsewhere (scratch);  V4_FAST=1  skip the cull (look-dev only)
"""
import os
import sys
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.compound import Wing, build_compound, configure, patches_by_azimuth  # noqa: E402
from village_kit.components.frame import RoundFrame, HIDDEN_CULL_TARGETS  # noqa: E402
from village_kit.components.plinth import drystone_plinth  # noqa: E402
from village_kit.components.daub import round_daub_wall  # noqa: E402
from village_kit.components.round_wall import wall_plate  # noqa: E402
from village_kit.components.conical_roof import conical_roof  # noqa: E402
from village_kit.components.cone import age_defaults  # noqa: E402
from village_kit.components.round_apex import turned_apex  # noqa: E402
from village_kit.components.doors import door_step, framed_door  # noqa: E402
from village_kit.components.interior import interior  # noqa: E402
from village_kit.components.round_decals import round_building_decals  # noqa: E402
from village_kit.components.drum_frame import DrumFrame, DRUM_CULL_TARGETS, drum_finish  # noqa: E402
from village_kit.components.drum_wall import drum_wall_core, round_stone_drum  # noqa: E402
from village_kit.components.drum_door import entrance_step  # noqa: E402
from village_kit.components.smock_tower import smock_tower  # noqa: E402
from village_kit.components.shake_apron import shake_apron  # noqa: E402
from village_kit.components.mill_cap import mill_cap  # noqa: E402
from village_kit.components.fan_wheel import fan_wheel  # noqa: E402
from village_kit.components.tail_vane import rear_tail_vane  # noqa: E402
from village_kit.components.drum_decals import drum_tower_decals_gated  # noqa: E402
from village_kit.components.junctions import roof_tower_flashing, wall_tower_abutment  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the plan: house centre and drum centre 4.68 m apart on a 15 deg line, so the 2.85 m daub wall runs 0.12 m
# into the 1.95 m drum and the house cone (eave 3.40 m) meets the drum between z 2.45 and ~3.3, under the band
HOUSE_AT, MILL_AT = (-1.70, 0.15), (2.82, 1.36)

HOUSE = dict(radius=2.85, eave_z=2.45, overhang=0.55, pitch_deg=51.0, cone_age=age_defaults(), detail_rule=True)
# exposed-wattle patches away from the drum side (house azimuth ~105 deg)
HOUSE_PATCHES = [(185.0, "low", 0.55, 0.45, 0.18, 9320), (250.0, "hole", 1.30, 0.42, 0.28, 9310),
                 (318.0, "hole", 1.70, 0.38, 0.26, 9330)]
APEX = dict(hat_pitch_deg=48.0, scale=0.85)
HOUSE_DECAL_GATE = dict(reach=0.05, min_sep=0.25, clear=0.15,
                        exclude_objects=("_daub_interior", "_roof_blocker", "_eave_closure", "_roof_underlap",
                                         "_door_panel_backing", "_floor"),
                        strict_types=("plaster_patch", "repair_patch"), normal_fp_dot=0.9, fp_ntol=0.10,
                        fp_skip_need=7, no_tops={"lichen": ("_step_stone",), "moss": ("_step_stone",)})

MILL = dict(
    drum=dict(r_base=1.95, r_top=1.82, height=5.30, zones=dict(band=(3.62, 3.72, 3.89, 3.99)), windows=(92, 160),
              door=dict(width=1.0, spring=1.62, reveal=0.30),
              arcade=dict(n=6, clear_w=0.48, clear_h=0.70, z_sill=3.99, az0=15.0), seed="v4"),
    tower=dict(af_bottom=2.60, af_top=1.85, z0=6.35, z1=10.05, seed="v4"),
    apron=dict(r_eave=2.45, z_eave=5.30, r_top=1.37, z_top=6.40, courses=3, seed="v4"),
    cap=dict(length=2.55, width=2.35, rise=1.05, ridge_len=0.9, yaw=25.0, seed="v4"),
    wheel=dict(r_in=1.10, r_rim=2.50, r_tip=3.05, n_blades=12, pitch=14.0, hub_d=1.80, seed="v4"),
    tail=dict(boom_end=-4.9, vane_s0=2.9, vane_length=1.8, seed="v4"),
)
# the drum's plain rubble a little larger than the hero's (art bible 3: courses 9.5-20 cm, 17-66 cm long): budget
MILL_RUBBLE = dict(plain=dict(hr=(0.095, 0.20), lr=(0.17, 0.66)))


def wings():
    house = Wing("house", RoundFrame, "V4H", params=HOUSE, at=HOUSE_AT,
                 steps=[(patches_by_azimuth, dict(patches=HOUSE_PATCHES)), drystone_plinth, round_daub_wall,
                        wall_plate, conical_roof, (turned_apex, APEX), door_step, framed_door, interior],
                 decals=partial(round_building_decals, layout=2), decal_validate=HOUSE_DECAL_GATE,
                 cull_targets=HIDDEN_CULL_TARGETS, reach=3.40, door=(0.0, -3.07), solid=(3.15, 2.5), ring_n=24)
    mill = Wing("mill", DrumFrame, "V4M", params=dict(detail_rule=True, rubble=MILL_RUBBLE), at=MILL_AT,
                steps=[(configure, dict(ENTRANCE_R8=True)), (round_stone_drum, MILL["drum"]), drum_wall_core,
                       entrance_step, (smock_tower, MILL["tower"]), (shake_apron, MILL["apron"]),
                       (mill_cap, MILL["cap"]), (fan_wheel, MILL["wheel"]), (rear_tail_vane, MILL["tail"]),
                       drum_finish],
                decals=drum_tower_decals_gated,
                cull_targets=DRUM_CULL_TARGETS + ("base_stones",), reach=2.45, door=(0.0, -1.92),
                view_heights=(0.4, 1.65, 3.4, 6.0), crane_heights=(6.0, 11.0, 16.0), solid=(2.0, 5.2), ring_n=16)
    return [house, mill]


# one continuous lime-mortar flaunching band (the keep's r7 choice) riding 2.5 cm over the chunky shingle tops
JUNCTIONS = [(roof_tower_flashing, dict(roof="house", tower="mill", mortar_only=True, lift=0.025)),
             (wall_tower_abutment, dict(wall="house", tower="mill"))]


def main():
    out = os.environ.get("V4_OUT", os.path.join(HERE, "v4_mixed.blend"))
    build_compound(dict(
        collection="V4", building_id="v4_mixed", wings=wings(), junctions=JUNCTIONS,
        cull=not os.environ.get("V4_FAST"), cull_procs=3, decal_max=120,
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(recipe="buildings/variants/v4_mixed/build_v4_mixed.py",
                        kit_params=dict(house=dict(HOUSE, cone_age="age_defaults()"), mill=MILL,
                                        house_at=HOUSE_AT, mill_at=MILL_AT)),
    ))


if __name__ == "__main__":
    main()
