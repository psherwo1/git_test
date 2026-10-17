# Kit feasibility decision (phase 2): Art Director

Date: 2026-10-17. Geometry only. Ground dressing is not scored (note 10), and no surface detail is asked for (note 12).

## Verdict: PARTIAL

**The client's question:** can the kit's reusable modules be combined into entirely unique structures for a 40-50
building village?

**Answer:** not yet, and not for 40-50 unique buildings. The kit is real. It has four working building families and a
compound layer that joins two of them. It can author about 12-14 convincingly distinct designs today, which meets the
producer note-14 target of 12-15 curated designs in number. It cannot cover the village's vocabulary, though.
- Every design it can make is a round or stone building: daub roundhuts, stone drums and towers, tiered stone halls,
  and rubble longhouses.
- The timber, rectangular half of the concept art has no modules at all: the harbour and waterfront houses, gabled
  timber halls, boathouses and multi-storey jettied buildings (ref2 right, ref3 right).
- Roofs cannot yet meet each other in an L or T plan, nor take a dormer.

**Note on scope.** My task brief calls note 12 the newest client note. The art bible and the production plan also
record notes 13 to 15, and I graded with them:
- note 13: no LED volume;
- note 14: the kit is reframed as an authoring toolbox for 12-15 curated designs, and the 40-50 generator is dropped;
- note 15: at most 1,000,000 triangles per new structure.

I answer both framings:
- **40-50 unique structures** (the brief's wording): not viable today.
- **12-15 curated designs, instanced to 40-50 placements** (note 14): partial. The count can be met, but only with
  narrow vocabulary, and too many of the designs would be parameter siblings of each other.

## Evidence

### Variant proof of concept

All four variants were graded on the note-12 modularity rubric, with a pass mark of 8.2.

| Variant | Last round | Director | Accepted (director + audit) | Notes |
|---|---|---|---|---|
| v1 stone watchtower | r4 | 8.3 | no | Pure kit recipe of 57 lines. New `pyramid_roof` module. Two open must-fixes: the open mouths under the hip saddles, and a sky slot at the outer joist bay. At **1,057,164 triangles it breaks note 15**. |
| v2 tiered hall | r4 | 8.4 | no | The best-generalised family: a BODIES table plus 22 steps, with the `roof_clearance` and `seal_probe` kit checks. Remaining issues: fascia ends at the turrets, hip-board ends at the aprons, and polygon tiers are octagonal only. |
| v3 longhouse with round end | r4 | 8.6 | no | A new building type from a 94-line recipe. Four module-level must-fixes are open: the stepped east stack, the ridge-roll free end, the north flashing pocket, and a 100 %-hidden wall plate. |
| v4 mixed (mill-house) | r4 | 8.4 | **yes** | The only one accepted. `compound` joins a RoundFrame wing and a DrumFrame wing. New `lod.py` took it from 1.39 M to 0.94 M triangles. |

What the variants prove:
- **Recipes are short and declarative.** Every recipe is 57-104 lines with no geometry code. Every fix landed in kit
  modules, and the hero builds re-ran exactly.
- **Builds are deterministic.** Director rebuilds of v2, v3 and v4 were hash-identical to the deliverables.
- **The kit's checks work.** `seal_probe`, `roof_clearance`, the anchor gates and the hidden-geometry cull with
  backing surfaces all did their job.

What the variants also show:
- **Only 1 of 4 variants is accepted.** All four needed four rounds to reach about 8.3-8.6. Each new pairing of
  modules found new junction defects: the eave crack at a tier, the wall-head cull hole, the soffit sliver, the stepped
  course stack, the saddle mouth.
- **Junctions are not plug-and-play.** They were fixed one design at a time. That is the note-14 working model, not
  "combine freely".

### Hero state

- **tower_windmill:** kit round 8, signed off.
- **wattle_roundhut:** kit round 11 graded 8.9, but no audit was run. The phase-1 version stays the deliverable.
- **hilltop_keep:** kit round 9 graded 8.6, and the audit rejected it. The phase-1 version stays the deliverable.
  - The keep family is the weakest part of the kit. It is the keep, refactored, and not a toolbox: the v2 builder had to
    write a whole new tier family because `oct_frame` hard-codes one tier stack.

## Usable components (proven in a passed or near-passed build)

- **Shared core.** `core`, `palette`, `mask`, `pools`, `stones` and `split_stones` (one generator), `shingles`
  (`SIZE_TABLE`), the decal stack (`decals`, `anchor_validate`, `decal_gate`, `anchor_audit`),
  `assembly.build_building` and `lod.tmpl_lod`.
- **Round family.**
  - `RoundFrame` (radius and eave derive everything), `cone`, `conical_roof`, `plinth`, `round_daub_wall`,
    `round_wall.wall_plate` and `doors`.
  - Finials: `finial` in the spike and turned styles, `round_apex.turned_apex` and `ball_finial`.
- **Drum family.**
  - `DrumFrame` and `round_stone_drum`, with any window spec, lookouts, a plain string course or balustrade, and an
    optional arcade. Also `drum_wall_core` and `drum_door`.
  - Mill parts: `shake_apron`, `smock_tower`, `mill_cap`, `fan_wheel`, `tail_vane` and `raking_props`.
  - `tower_roof`: the parapet, the round cone roof and the drum cull.
  - `pyramid_roof` for any polygon, verified on 3, 6 and 8 sides.
- **Tier family.** `TierFrame` with `declare_bodies`, `stone_body` (quoins, `clip_by`), `bell_tier` and `round_tier`
  (profiles skirt, skirt_steep, cap, spire and witch_hat), `board_belt`, `roof_flashing`, `tier_finial`, the
  `roof_clearance` gate, `seal_probe` and `tier_finish`.
- **Linear and composite family.** `GableRoof` and `linear_roof` (thatch courses), `path_stone_wall` (any polyline,
  with quoins), `round_stone_body`, `wall_openings`, and `composite.cone_roof` (keep-out, soakers, trim and soffit).
  Also `roof_junction.cone_abutment` and `end_apron`.
- **Compound layer.** `Wing` and `build_compound`, `configure`, `junctions.roof_tower_flashing`,
  `wall_tower_abutment` and `clip_at_tower`.

## Weak or unusable components

- **Keep family: usable for the keep only.** This covers `oct_frame`, `oct_hall`, `annex`, `windows`, `turret`,
  `stone_cone`, `thatch` (the wing roof), `oct_cull` and `oct_decals`.
  - They read a global proxy (`FR`) and use absolute heights.
  - The wing path is fixed at x = -3.70.
  - `windows.window_spec` defaults to xc = -7.4.
  - The thatch wing's macro-form was audit-rejected.
- **`daub.round_daub_wall`: round walls only.**
  - It is a 75 KB monolith with the hut's round-9 to round-11 options layered in.
  - There is no straight daub or wattle wall.
  - There is no window module for a round daub wall.
- **`conical_roof`: shingles only, with no thatch cone.**
  - Its eave pieces are open shells that show back faces, on every cone.
  - The door-head fixes (`DOOR_INFILL_DECK`, `EAVE_CLOSURE_DOOR_HALF_DEG`) are opt-in, so the next steep cone can
    reopen the slot over the door.
- **Duplicated modules, which make recipes non-interchangeable:**
  - three eave closures: `conical_roof`, `round_roof_parts`/`tower_roof`, and `composite.round_eave_fill`;
  - two polygonal bell-cast roofs: `pyramid_roof` and `bell_tier`/`oct_roof`;
  - two stone-body modules: `stone_body` and `rubble_walls`;
  - two opening modules: `framed_openings` and `wall_openings`;
  - three functions named `window_spec`;
  - two functions named `end_apron`.
- **`bell_tier`.** Polygon tiers can only be octagonal.
- **`linear_roof`.** The ridge-roll free end is unfinished and the ridge comb is weak. The shingle covering never got
  the course rework that the thatch covering got.
- **`cone_abutment`.** It handles only a horizontal ridge running into a cone. There is no variant for a cylinder or a
  tower wall.
- **`square_cabin`.**
  - It sits on a round wall head only, and its bed ring is lathed.
  - The hip-saddle mouths and the joist-bay sky slot are open.
  - The v1 build that uses it is over note 15.
- **`compound` and `junctions`.** They are proven on one pairing only: a round daub wing against a stone drum.
- **`lod.tmpl_lod`.** It only reaches template-instanced (BatchAcc) pieces, and its rule must be unregistered after
  each wing.
- **`interior`.** It is a placeholder.
- **Budget.** Each design is about 0.5-1.0 M unique triangles and takes 5-10 minutes to build. Instancing saves 1-6 %.
  Note 15 has to be met per design, by hand, using LOD parameters.

## Missing module types (the village needs them; the kit has none)

1. A rectangular timber-frame wall: post and beam with braces, and daub or plank infill.
2. Plank or weatherboard cladding for barns, boathouses and harbour houses.
3. A straight wattle-and-daub wall, for rectangular daub houses.
4. A multi-storey floor stack with a jettied upper floor (the ref2 and ref3 waterfront houses).
5. Gable-to-gable junctions (valleys for L and T plans) and hipped or half-hipped linear roofs.
6. Dormers, gablets and dormer turrets on a roof slope (the ref2 hall).
7. A gable roof abutting a round wall or tower (a cylinder version of `cone_abutment`).
8. A conical thatch covering for round huts (ref2's thatch cones).
9. Note-14 add-ons: lean-to, porch or canopy, chimney or smoke louvre, and roof-covering swaps.
10. Waterfront structure: piles and stilts, a platform, and large boathouse openings.
11. A four-sail lattice-sail rotor beside `fan_wheel`. The mills in ref2 and ref3 read as four-sail.
12. Free, generalised turret, stone-cone and lantern modules (today they are locked in the keep family), and polygon
    tiers with any number of sides.

## How many distinct buildings it can make today

**About 12-14 convincing designs, in roughly 8 silhouette families.**

**Existing designs (7):**
1. the windmill;
2. the roundhut;
3. the keep (phase-1 deliverable);
4. v1 watchtower (needs a note-15 trim);
5. v2 tiered hall;
6. v3 longhouse with round end;
7. v4 mill-house.

**Designs reachable by recipe and parameters only (about 5-7), each needing its own review round:**
- a small roundhut and a large tall-cone roundhut with a turned or ball finial (`RoundFrame` radius, eave and pitch);
- a stone round hut or store (`round_stone_body` + `cone_roof` + `ball_finial`);
- a parapet watchtower under a round cone (the `tower_roof` crown);
- a plain gabled rubble longhouse or barn (`path_stone_wall` + `linear_roof`);
- a round tiered tower or chapel (`TierFrame`, round bodies, witch-hat tiers);
- a smaller mill (`MILL_KIT_VARIANT`).

**Caveats:**
- The parameter siblings of the hut, the mill and the keep are size variants, not "entirely unique".
- Nothing timber-built, rectangular-timber or waterfront can be made today.
- Repeating 12-14 designs 3-4 times each, all stone or round, would not read as the ref2/ref3 village.

## Recommendation

**Proceed with the kit.** Do not drop to bespoke heroes. Under the client-approved fallback, two of the three new
heroes already exist as kit builds: v3 is approved building 1 and v2 is approved building 2. Build approved
building 3, the timber harbour house, **as a new kit family** rather than as a bespoke hero.

1. **Timber family.** Add a rectangular timber family: frame walls with plank or daub infill, a straight daub wall, a
   floor stack with a jetty, and a gable-to-gable valley with a dormer. Prove it on the harbour house, then on a
   boathouse or barn.
2. **Consolidation pass.** One eave closure, one polygonal roof, one body module and one opening module. Free the keep
   family's turret, stone cone and lantern as generic modules. Polygon tiers with any number of sides.
   `cone_abutment` against a cylinder. A thatch cone covering. The add-ons from note 14.
3. **Close the open variants.**
   - v1: the saddle mouth, the sky slot, and bring it under 1 M triangles.
   - v3: its four must-fixes.
   - Then run independent audits on v1, v2 and v3.
4. **Revisit the decision.** Once the timber family passes, re-grade feasibility. With it, the kit should reach 15 or
   more genuinely distinct designs and cover the full ref2/ref3 vocabulary.
