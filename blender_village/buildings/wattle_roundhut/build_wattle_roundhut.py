"""Wattle-and-daub round hut (HUT) -- a thin declarative assembly on the shared village kit (phase 2, round 10).

Run:  /opt/bpyenv/bin/python build_wattle_roundhut.py
          -> wattle_roundhut.blend + decal_anchors.json (next to this script)
      HUT_KIT_VARIANT=1 /opt/bpyenv/bin/python build_wattle_roundhut.py
          -> kit_variant/wattle_roundhut_kit_variant.blend + kit_variant/decal_anchors.json
             (the kit test: a smaller, taller-walled hut from the same components)

The hut is the signed-off phase-1 hut (round 7, ref2 foreground hut) rebuilt from village_kit components:
  * dry-stone plinth ring on a flat Z = 0 datum (<= 4 cm buried skirt, producer note 10: no ground dressing)
  * 14 round-hewn posts, MOSTLY INTACT DAUB (client correction) with the ref2 eroded band left of the door and 3
    small fallen-out patches; wattle modelled only where it shows; scarf-jointed pegged wall plate
  * 51 deg chunky-shingle cone (17 courses, kit SIZE_TABLE) on 28 pole rafters with the ensemble age pass
    (eave wave, sag between rafters), lead-hat collar, spindle and spike finial leaning ~1 deg
  * projecting flat-fronted door frame, worn sill, threshold slabs, step, plank leaf open 75 deg with ironwork
  * earth floor and hearth seen through the door
Producer note 11: sub-2 cm relief is not modelled (entrance zone: >= 1 cm kept, gated per vertex by the kit daub);
decal anchors are exported, snapped and validated by the kit gate (village_kit.anchor_validate).
Round 9 (kit 1.3.0, director r8 #1-#3): WALL_FINISH (note-11 entrance relief per vertex, 2-2.5 cm hand lumps on
every bay, sag 1.1-1.5 cm, flakes deleted, <= 6 foot bites), rigid per-shingle cone sag + joint under-lap
(cone.AGE_R9), decal layout 2 + DECAL_VALIDATE.
Round 10 (kit 1.5.0, sign-off audit r9): WALL_FINISH_R10 (ragged leaning / chamfered / spalled patch outlines with a
1.5-5 cm fracture face, clinging clumps >= 2 cm proud hugging the rods at every break, plinth scars >= 8 mm kept as
note-11 spalls), AGE_R10 (under-lap under the first course too: no eave light leak over the door), decal layout 3
(macro-normal collar soot, no lichen on the step, corner cracks from the real outline) and a footprint-mean normal
test in the gate.
Round 11 (kit 1.6.0, sign-off audit r10): WALL_FINISH_R11 (door-bay break rebuilt in the _ragged_margin language with
a mitred slope-normalised field and a steep 3 cm / 7.4 cm-thick edge face; flat-fronted slab clumps, <= 1 at a corner;
plinth scars as planar split-facet pockets, no 1 cm skin lumps, flat bed with a <= 1 cm skirt; entrance relief gated
per feature; chinking / cheek-spall noise and the 9 mm step dish gated by g.detail.min_at), decal layout 4 and the
strict anchor gate (STRICT_R11: >= 7 of 9 footprint points within 4 cm on the slot, footprint-mean normal dot >= 0.97,
wall slots |n.z| <= 0.15), door-head soot on the lintel.
All randomness is seeded; the build is deterministic.  Dimensions live in ONE table, KIT (kit_set convention).
"""
import os
import sys
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.anchor_validate import STRICT_R11  # noqa: E402
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.frame import RoundFrame, round_hidden_cull  # noqa: E402
from village_kit.components.plinth import drystone_plinth  # noqa: E402
from village_kit.components.daub import round_daub_wall, wall_finish_r11  # noqa: E402
from village_kit.components.round_wall import wall_plate  # noqa: E402
from village_kit.components.conical_roof import conical_roof  # noqa: E402
from village_kit.components.finial import finial  # noqa: E402
from village_kit.components.doors import door_step, framed_door  # noqa: E402
from village_kit.components.interior import interior  # noqa: E402
from village_kit.components.round_decals import round_building_decals  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# the hut's dimension table (components.frame.RoundFrame documents every key)
KIT = KitParams(
    radius=3.50,              # wattle / post centre line: wall dia 7.0 m
    eave_z=2.395,             # eave lip 2.38-2.45 m (>= 2.40 over the door)
    overhang=0.63,            # eave dia 8.26 m
    pitch_deg=51.0,
    finial_tip=8.60,          # spike tip (bbox top 8.73 with the lean)
    cone_age=age_defaults(**AGE_R10),  # ensemble eave wave +-3-5 cm, 1-3 cm sag between rafters, applied RIGIDLY
                              # per shingle (<= 1.5 deg tilt) + 8 cm under-lap beside every side joint, course 1 too
    detail_rule=True,         # producer note 11
    wall_finish=wall_finish_r11(),  # r10 finish + r10 audit: crisp door-bay break, slab clumps, split-facet plinth,
                              # per-feature entrance gating, fine-relief gates
)
# HUT_KIT_VARIANT: a different hut from the same components -- 2.9 m radius (5.8 m wall), a 0.2 m taller wall,
# post / rafter counts and door-post azimuth derived by the frame, finial derived from the collar
HUT_KIT_VARIANT = dict(radius=2.90, eave_z=2.60, finial_tip=None)
# director r8 #3 / r9 #4: every anchor snapped onto its surface along -normal (none within 5 cm -> dropped), on its
# declared slot, open along +normal, footprint on the surface, its normal within ~25 deg of the surface normal
# AVERAGED over the footprint, shingle anchors >= 7 of 9 footprint rays on the shingles, no lichen on trodden
# stones, no same-type duplicate within 0.25 m
DECAL_VALIDATE = dict(reach=0.05, min_sep=0.25, clear=0.15,
                      exclude_objects=("_daub_interior", "_roof_blocker", "_eave_closure", "_roof_underlap",
                                       "_door_panel_backing", "_floor"),
                      strict_types=("plaster_patch", "repair_patch"),
                      normal_fp_dot=0.9, fp_ntol=0.10, fp_skip_need=7,
                      no_tops={"lichen": ("_step_stone",), "moss": ("_step_stone",)},
                      strict=STRICT_R11)


def kit_set(**kw):
    """publish component parameters to the hut's dimension table (unknown keys raise)."""
    KIT.set(**kw)


def main(steps_extra=True):
    variant = bool(os.environ.get("HUT_KIT_VARIANT"))
    if variant:
        kit_set(**HUT_KIT_VARIANT)
        out = os.path.join(HERE, "kit_variant", "wattle_roundhut_kit_variant.blend")
    else:
        out = os.path.join(HERE, "wattle_roundhut.blend")
    out = os.environ.get("HUT_OUT", out)
    steps = [drystone_plinth,          # publishes the stone-top sampler
             round_daub_wall,          # wattle where it shows, posts, coat, clinging clumps, inner skin
             wall_plate,
             conical_roof,             # rafters, rings, battens, starter + shingle courses, under-lap, blocker, closure
             finial,                   # lead-hat collar, spindle, spike
             door_step, framed_door, interior,
             round_hidden_cull]        # producer note 6
    if os.environ.get("HUT_NO_CULL"):      # quick look-dev builds only (never the deliverable)
        steps = steps[:-1]
    build_building(dict(
        prefix="HUT", collection="HUT", building_id="wattle_roundhut" + ("_kit_variant" if variant else ""),
        frame=RoundFrame, params=KIT,
        steps=steps,
        decals=partial(round_building_decals, layout=4),    # producer note 11
        decal_validate=DECAL_VALIDATE,
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items()}),
    ))


if __name__ == "__main__":
    main()
