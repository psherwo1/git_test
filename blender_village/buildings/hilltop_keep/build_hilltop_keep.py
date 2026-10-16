"""Hilltop Keep (KEEP) -- a thin declarative assembly on the shared village kit (phase 2, round 7).

Run:  /opt/bpyenv/bin/python build_hilltop_keep.py
          -> hilltop_keep.blend + decal_anchors.json (next to this script)
      KEEP_KIT_VARIANT=1 /opt/bpyenv/bin/python build_hilltop_keep.py
          -> kit_variant/hilltop_keep_kit_variant.blend + kit_variant/decal_anchors.json
             (the kit test: a different keep from the same components)
      KEEP_FAST=1 skips the hidden-geometry ray test (quick looks only; never a deliverable)

The keep is the signed-off phase-1 keep (round 6, ref1's hilltop keep) rebuilt from village_kit components
(components.oct_frame.OctFrame is its frame `g`; every dimension below is one row of its table):
  * octagonal battered rubble hall, 8.0 m across the flats, wall to 3.45 m, arched door facing -Y with dressed jambs
    and an irregular voussoir ring, a timber-framed SW window, E / NE windows, a W slit (oct_hall, windows)
  * 8 hewn corner posts on dressed pedestals, paired curved knee braces, pegged eave and raising plates (oct_hall)
  * tier 1 bell-cast octagonal skirt roof of long board courses with rafters / soffit / fascia (oct_roof)
  * tier 2 riven-shake collar with a jagged comb, tier 3 concave rubble cone, lantern belt, tier 4 bell cap of the
    village's CHUNKY shingles (ensemble review 1), lead hat and turned finial to 14.0 m (stone_cone)
  * west wing: rubble walls with a plank door and a small window (annex, plank_doors, windows), a hipped thatch roof
    of stepped clumped courses with an eave roll, ridge comb and mortar / lead junctions (thatch)
  * engaged side turret with a corbelled cushion, board drum and a chunky-shingle bell cap (turret)
Client corrections kept: no ground dressing (producer note 10) -- only the building's own footing course, pedestals,
threshold and built-in step meet the ground.  Producer note 11: sub-threshold relief is not modelled (the entrance
zone keeps >= 1 cm) and decal anchors are exported.  All randomness is seeded; the build is deterministic.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.oct_frame import OctFrame  # noqa: E402
from village_kit.components.oct_hall import door_threshold, oct_hall_frame, oct_hall_walls  # noqa: E402
from village_kit.components.plank_doors import arched_door, door_spec, plank_door  # noqa: E402
from village_kit.components.windows import annex_window, hall_windows, window_spec  # noqa: E402
from village_kit.components.oct_roof import skirt_roof  # noqa: E402
from village_kit.components.stone_cone import cone_cap, lantern, shake_collar, stone_cone  # noqa: E402
from village_kit.components.annex import annex_walls  # noqa: E402
from village_kit.components.thatch import ridge_comb, thatch_junctions, thatch_wing_roof  # noqa: E402
from village_kit.components.turret import side_turret  # noqa: E402
from village_kit.components.oct_cull import oct_hidden_cull  # noqa: E402
from village_kit.components.oct_decals import oct_building_decals  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# the keep's dimension table (components.oct_frame.PARAMS documents every key)
KIT = KitParams(
    A0=4.0, WALL_H=3.45,                    # hall: 8.0 m across the flats, eave plate on the 3.45 m wall
    CONE_TOP=9.6,                           # stone cone up to the lantern sole (finial tip 14.0 m)
    WX_W=-10.0, WX_E=-1.3, WY_S=0.4, WY_N=4.6,      # west wing plan (outer wall faces)
    W_WALL_H=2.55, W_PITCH_DEG=47.0, W_OVH=0.55, CORE_T=0.30,
    WDOOR=door_spec(xc=-5.05, width=1.0, height=2.10, frame=0.18, depth=0.20, threshold=0.10),
    WWIN=window_spec(xc=-7.4, width=0.45, height=0.55, sill=1.30, frame=0.07, depth=0.16),
    TUR_C=(-8.55, 2.70), TUR_SCALE=1.0,     # side turret engaged in the wing's west end
    detail_rule=True,                       # producer note 11
    units="kit",                            # SIZE_TABLE units: chunky shingles on the bell caps (ensemble review)
    seed_offset=0,
)
# KEEP_KIT_VARIANT: a different keep from the same components -- a shorter, narrower wing (6.98 x 4.0 m) with a
# steeper (52 deg) thatch, a 0.8x turret moved with it, a lower, stubbier stone cone (top 8.9 m), the annex door and
# window re-spaced, and every masonry / roofing layout re-seeded
KEEP_KIT_VARIANT = dict(WX_W=-8.3, WY_N=4.4, W_PITCH_DEG=52.0, TUR_C=(-7.14, 2.24), TUR_SCALE=0.8, CONE_TOP=8.9,
                        WDOOR=door_spec(xc=-4.85), WWIN=window_spec(xc=-6.05), seed_offset=17)


def kit_set(**kw):
    """publish component parameters to the keep's dimension table (unknown keys raise)."""
    KIT.set(**kw)


def steps(off=0):
    """the components in build order (later components read what earlier ones built: the skirt scribes into the
    thatch outline, the junction fillets ray-cast the built thatch, the cull runs last)."""
    return [(oct_hall_walls, dict(seed=101 + off)), (oct_hall_frame, dict(seed=202 + off)), (arched_door, {}),
            (hall_windows, {}), (door_threshold, {}),
            (skirt_roof, dict(seed=303 + off)),
            (shake_collar, dict(seed=505 + off)), (stone_cone, dict(seed=404 + off)), (lantern, dict(seed=606 + off)),
            (cone_cap, dict(seed=707 + off)),
            (annex_walls, dict(seed=1111 + off)), (plank_door, {}), (annex_window, {}),
            (thatch_wing_roof, dict(rng_seed=1313 + off)), (ridge_comb, dict(seed=1414 + off)),
            (thatch_junctions, {}),
            (side_turret, dict(seed=1616 + off)),
            oct_hidden_cull]                 # producer note 6


def main():
    variant = bool(os.environ.get("KEEP_KIT_VARIANT"))
    if variant:
        kit_set(**KEEP_KIT_VARIANT)
        out = os.path.join(HERE, "kit_variant", "hilltop_keep_kit_variant.blend")
    else:
        out = os.path.join(HERE, "hilltop_keep.blend")
    out = os.environ.get("KEEP_OUT", out)
    build_building(dict(
        prefix="KEEP", collection="KEEP", building_id="hilltop_keep" + ("_kit_variant" if variant else ""),
        frame=OctFrame, params=KIT,
        steps=steps(KIT["seed_offset"]),
        decals=oct_building_decals,         # producer note 11
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: (v if not hasattr(v, "tolist") else v.tolist()) for k, v in KIT.items()}),
    ))


if __name__ == "__main__":
    main()
