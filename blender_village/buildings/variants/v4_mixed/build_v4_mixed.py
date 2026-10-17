"""v4_mixed -- the MILL-HOUSE: a miller's daub roundhouse built against a small stone tower mill (kit variant 4).

A building type the village does not have yet, assembled only from kit modules of all three hero families:
  * HOUSE wing  (hut family, RoundFrame):  dry-stone plinth, wattle-and-daub wall, pegged wall plate, a steep 58 deg
    chunky-shingle needle cone on a small 2.55 m plan, framed door with step, interior -- crowned with the KEEP
    family's turned finial over a fitted lead hat (components.round_apex)
  * MILL wing   (drum family, DrumFrame):  a tall, strongly battered rubble drum (balustrade band and a 6-bay blind
    arcade lifted clear of the house roof, arched door and step, two slits), shake apron, boarded smock tower, hipped
    cap, 16-blade fan wheel, tail vane on a rear boom
  * JUNCTIONS   (components.junctions):  the house cone runs into the drum -> the roof wing trimmed at the drum
    face, every cut rafter foot outside the wall head on a level KEEP-family hewn pad over a drum corbel (a stepped
    bearing), the traced roof / drum line
    closed by a mortar fillet fitted to the shingles, lead end-aprons over the cut eave lips;
    the daub wall runs into the drum -> keep-family hewn abutment posts let into the masonry, mortar pointing
Assembly: village_kit.compound (several frames in one building, one hidden-geometry cull that keeps every wing's
eye-level rings whole and protects a wall-head band under a low eave lip, decal anchors audited on the whole
building).  Producer notes 1-15 (note 15: <= 1,000,000 triangles, met with kit LOD / density parameters:
village_kit.lod.tmpl_lod and frame attributes); deterministic (every seed fixed).

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
from village_kit.lod import DRUM_LOD_PARTS, tmpl_lod, tmpl_lod_report  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the plan: house centre and drum centre 4.43 m apart on a 15 deg line, so the 2.55 m daub wall runs 0.09 m
# into the drum (R 1.97 m at z 1.2) and the house cone (eave radius 3.15 m) meets the drum between z 2.4 and ~3.5,
# under the band.
# Round 3 (distinctness): both wings are pushed off their hero presets.  The house is a narrow, steep miller's
# cottage -- 5.1 m wall (hut 7.0 / hut variant 5.8), a 58 deg needle cone (heroes 51) on a low 2.40 m eave, eave
# diameter 6.3 m against a finial at ~8.4 m (height / width 1.3; hut 1.0).  The mill is a TALL, strongly battered
# stone tower -- 5.5 m drum tapering 2.05 -> 1.70 m (mill 4.62 m 2.60 -> 2.45; mill variant 4.2 m 2.00 -> 1.88) --
# with a 16-blade fan wheel of the small mill's diameter (ref1).
HOUSE_AT, MILL_AT = (-1.462, 0.214), (2.82, 1.36)

HOUSE = dict(radius=2.55, eave_z=2.40, overhang=0.60, pitch_deg=58.0, cone_age=age_defaults(), detail_rule=True)
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
    drum=dict(r_base=2.05, r_top=1.70, height=5.50, zones=dict(band=(3.80, 3.90, 4.07, 4.17)), windows=(92, 160),
              door=dict(width=1.0, spring=1.62, reveal=0.30),
              arcade=dict(n=6, clear_w=0.48, clear_h=0.70, z_sill=4.17, az0=15.0), seed="v4"),
    tower=dict(af_bottom=2.60, af_top=1.85, z0=6.55, z1=10.25, seed="v4"),
    apron=dict(r_eave=2.45, z_eave=5.50, r_top=1.37, z_top=6.60, courses=3, seed="v4"),
    cap=dict(length=2.55, width=2.35, rise=1.05, ridge_len=0.9, yaw=25.0, seed="v4"),
    wheel=dict(r_in=1.10, r_rim=2.50, r_tip=3.05, n_blades=16, pitch=14.0, hub_d=1.80, seed="v4"),
    tail=dict(boom_end=-4.9, vane_s0=2.9, vane_length=1.8, seed="v4"),
)
# the drum's plain rubble a little larger than the hero's (art bible 3: courses 8-25 cm, mostly 10-15, 20-70 cm
# long): budget
MILL_RUBBLE = dict(plain=dict(hr=(0.10, 0.21), lr=(0.20, 0.68)))
# producer note 15 (<= 1,000,000 triangles), kit parameters only:
#  * the drum family's template pieces (rubble, dressed work, arcade, smock / cap / apron timbers, blades) clear of
#    the footing course (above 0.6 m) and outside the entrance zone on every 2nd grid line (village_kit.lod.tmpl_lod:
#    same outline corners and arrises, a thinner face grid)
#  * the daub coat on a 7-7.5 cm grid (its relief is the >= 0.5 m bulge / sag), 1.25 cm at the fracture margins
#  * plinth boulders outside the entrance zone at 0.55 x the hero's mesh density (~1.5 cm face grid)
#  * cone shingles with a cross-section ring every 21 cm above the butt (the cone is straight along the slope)
MILL_LOD = dict(z=0.6, step=2, bands=[(3.0, 3)],          # every 3rd grid line above 3.0 m (note 15: mid-distance)
                parts=DRUM_LOD_PARTS + ("pool_corbel*",))  # + the pooled cornice corbels (all at 5 m)
HOUSE_BUDGET = dict(DAUB_GRID=(0.075, 0.07, 0.035, 0.0125), PLINTH_DENSE=0.55, SH_RING_STEP=0.21)
# round 4 (director r3 probe): the door-head infill boards run up to the batten deck (laths behind the board gaps)
# -- on the 58 deg cone the rafter-underside top left a ~0.26 m slot between the rafters over the door -- and the
# eave closure runs on behind the infill (the cheek opening beside it looked into the eave void)
HOUSE_OPTS = dict(HOUSE_BUDGET, DOOR_INFILL_DECK=True, EAVE_CLOSURE_DOOR_HALF_DEG=1.0)


def wings():
    house = Wing("house", RoundFrame, "V4H", params=HOUSE, at=HOUSE_AT,
                 steps=[(configure, HOUSE_OPTS),
                        (patches_by_azimuth, dict(patches=HOUSE_PATCHES)), drystone_plinth, round_daub_wall,
                        wall_plate, conical_roof, (turned_apex, APEX), door_step, framed_door, interior],
                 decals=partial(round_building_decals, layout=2), decal_validate=HOUSE_DECAL_GATE,
                 cull_targets=HIDDEN_CULL_TARGETS, reach=3.15, door=(0.0, -2.77), solid=(2.85, 2.5), ring_n=24)
    mill = Wing("mill", DrumFrame, "V4M", params=dict(detail_rule=True, rubble=MILL_RUBBLE), at=MILL_AT,
                steps=[(configure, dict(ENTRANCE_R8=True)), (tmpl_lod, MILL_LOD), (round_stone_drum, MILL["drum"]),
                       (drum_wall_core, dict(n_th=96)), entrance_step, (smock_tower, MILL["tower"]), (shake_apron, MILL["apron"]),
                       (mill_cap, MILL["cap"]), (fan_wheel, MILL["wheel"]), (rear_tail_vane, MILL["tail"]),
                       tmpl_lod_report, drum_finish],
                decals=drum_tower_decals_gated,
                cull_targets=DRUM_CULL_TARGETS + ("base_stones", "door_leaf", "interior", "door_surround",
                                                  "tower_boards", "cap_frame"), reach=2.45,
                door=(0.0, -2.02),
                view_heights=(0.4, 1.65, 3.4, 6.0), crane_heights=(6.0, 11.0, 16.0), solid=(2.05, 5.4), ring_n=16)
    return [house, mill]


# roof into tower (kit defaults): the roof wing trimmed at the drum face, the cut rafter feet on a hewn ledger over
# drum corbels, a mortar fillet fitted to the shingles (10 cm up the stone, 11 cm out, toe 5 cm over the butt
# peaks), lead end-aprons over the cut eave lips;  wall into tower: hewn abutment posts let into the masonry
JUNCTIONS = [(roof_tower_flashing, dict(roof="house", tower="mill")),
             (wall_tower_abutment, dict(wall="house", tower="mill"))]


def main():
    out = os.environ.get("V4_OUT", os.path.join(HERE, "v4_mixed.blend"))
    build_compound(dict(
        collection="V4", building_id="v4_mixed", wings=wings(), junctions=JUNCTIONS,
        cull=not os.environ.get("V4_FAST"), cull_procs=4, cull_max_views=300, decal_max=120,
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(recipe="buildings/variants/v4_mixed/build_v4_mixed.py",
                        kit_params=dict(house=dict(HOUSE, cone_age="age_defaults()"), mill=MILL,
                                        house_at=HOUSE_AT, mill_at=MILL_AT)),
    ))


if __name__ == "__main__":
    main()
