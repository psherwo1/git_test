## Ensemble review 1 — 8.4/10

**Date:** 2026-10-16. **Verdict: APPROVED.** The pass mark is 8.2, set by the client "for now" once the hut daub correction and producer note 10 are in. Both are in.

**What I reviewed.**
- The lineup renders in `renders/_ensemble/round_01/`: hero, front and aerial, plus stats.json and hidden.json. I also made 3x crops of the front and hero lineups.
- The latest individual sets: `hilltop_keep/round_06` (8.4), `tower_windmill/round_06` (9.1) and `wattle_roundhut/round_07` (8.5).
- I compared all of them against ref1, ref2 and ref3.
- I checked the three build scripts for kit structure.
- Ground dressing is **not scored** (producer note 10).

**Client corrections confirmed.**
- **Round hut, mostly intact daub.** Hero and side views show a continuous hand-applied coat over about 84 % of the wall face. Exposed wattle shows only in 4 small fracture patches and in the ref2 band low in the door bay. The rope-woven door side panels read as intentional framing. Rods behind intact daub are deleted.
- **No loose stones or paths on any building.** hidden.json for the lineup lists no rubble, flag, path, apron or scatter object. What is left is part of the buildings:
  - the thresholds (HUT_threshold, KEEP_threshold);
  - the built-in steps (HUT_step_stone, MILL_door_step);
  - the plinths and footings;
  - the mill prop chocks, with their packed `M_earth` collar;
  - the hut's interior earth floor (`M_earth`) and hearth.

**Coherence (one world?).** Yes. In the lineup the three read as one village from ref1/ref2:
- The roof language is shared: steep witch-hat cones, a bell-cast octagonal skirt, small bell caps with deep overhangs, and spike finials on every apex.
- The stone and timber vocabulary is shared: rough coursed rubble, dressed surrounds only at openings, round arches, and hewn posts with knee braces.
- Scale is consistent next to the 1.8 m figure: hut 8.8 m, keep 14.0 m, mill 16.2 m, and every door is 2.05-2.3 m.
- There is no Gothic, crenellated or half-timbered vocabulary anywhere.

**Axes**

| Axis | Score | Why |
|---|---|---|
| Shared roof language | 8.5 | Cones, skirt, caps and finials agree. The shingle *scale* is not yet one system: hut shingles are about 0.45 m chunky units, the keep turret and lantern caps use narrow fine boards, and the mill apron uses shakes. |
| Stone / timber vocabulary | 8.5 | Keep rubble and hut boulders match. The mill drum is noticeably more regular and crisp (near-ashlar coursing, a classical baluster string course), so it reads slightly "newer" and more formal. |
| Detail density and age | 8 | The hut cone outline is the most perfect and regular surface in the set. The keep has sag and wobble; the hut cone and eave read straighter at lineup distance. |
| Scale consistency | 9 | Correct throughout. |
| Kit readiness | 8 | The keep and the mill have `kit_set()` and a variant switch. The hut has no kit entry point. Each script has its own stone generator (`stone_rec` / `stone_local` / `stone`), its own shingle generator and its own Mask writer (`write_mask` / `set_mask` / hut). These must be unified before phase 2. |
| Technical | 9 | 13 slots, all in the palette. Mask is complete. Each building is ≤ 1.31 M tris and ≤ 14.4 % hidden. The lineup-level 18.2 % hidden is a measurement artefact (distant lineup viewpoints and occlusion between buildings), not a building defect. |

**Per-building fixes (ensemble consistency only; none blocks approval)**

- **wattle_roundhut**
  - Add a kit entry point the same way as keep and mill: `kit_set()`, plus a `HUT_KIT_VARIANT` that builds a hut of a different radius and wall height.
  - Expose these as parameterised functions:
    - `daub_wall(radius, height, patches, seed)`;
    - `wattle_patch(...)`;
    - `drystone_plinth(radius, seed)`;
    - `conical_roof(radius, pitch, overhang, seed)`;
    - `lead_hat_finial(...)`.
  - Give the shingle cone the same low-frequency age pass as the keep: an eave line wave of ±3-5 cm, sag of 1-3 cm between rafters, and a 0.5-1° finial lean. That way it is not the most perfect silhouette in the lineup.
- **hilltop_keep**
  - Bring the turret and lantern bell-cap shingles up to the shared chunky scale: 0.35-0.55 m wide with 3-4 cm butts, matching the hut cone. They currently read as fine narrow boards next to the hut.
- **tower_windmill**
  - Roughen the drum masonry toward the keep and hut rubble: more course wander and pinch-outs, and fewer near-ashlar runs.
  - Age the baluster string course: varied baluster profiles, a lean of ±1°, a few chipped or missing balusters.
  - Both changes stop the mill reading newer and more formal than its neighbours.
- **Kit (all three, before phase 2)**
  - Merge the three stone generators, the three shingle and shake generators and the two or three Mask writers into one shared module that all three builds import.
  - Keep one shingle size table for the whole village.
