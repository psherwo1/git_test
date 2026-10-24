# ART BIBLE: "Fjord Village" hero buildings (geometry only)

Owner: Art Director. Builders read this file before every round. If this file and a spec disagree, the spec wins for that building.

Reference images (the source of truth):
- `reference/ref1_hilltop_keep_windmill.jpg`: stone hilltop keep, stone/timber tower windmill, longhouse with a round end.
- `reference/ref2_harbor_village_eye_level.jpg`: eye-level harbour village; the foreground round wattle hut is our hut.
- `reference/ref3_fjord_village_aerial.jpg`: aerial view of the same village.
- Upscaled detail crops are in `director/ref_crops/*.png`. Open them with the Read tool. They are the quickest way to check a detail.

The renders are neutral clay on purpose. **We judge geometry only**: silhouette, proportion, massing, construction logic, detail density, age, and actor-scale correctness. A building that is only good once it has textures is not good.

---------------------------------------------------------------------------------------------------

## 1. What makes it THIS world and not "generic medieval"

1. **Round and polygonal plans.** Halls are octagons, huts are circles and towers are round. Rectangles only appear in low annexes and harbour sheds. Gabled boxes are wrong for hero buildings.
2. **Tall witch-hat cones.** Hut and tower roofs are steep cones of 48–55° whose height is 1.5–2.2× the wall height. The roofs dominate the walls: walls are short (2.3–3.6 m) and roofs are huge.
3. **Stacked tiers (the signature).** A wide, moderately pitched polygonal skirt roof (~40°, flattening at the bell-cast eave) → a steep collar of long split shakes with a ragged comb top → a concave stone or shingle cone (a "candle-snuffer" or bottle profile) → a short lantern belt of vertical boards → a small bell-cast cap with a deep overhang → a tall turned finial. Every tier steps *inward and upward*, and every eave *overhangs* the tier below.
4. **Bell-cast eaves.** Caps and skirt roofs kick outward and flatten over the last 0.5–1.0 m (sprocketed eaves). Hip lines are slightly concave. Big hut cones are straight to very slightly convex, and they get a small kick only at the eave.
5. **Spike finials on a "lead hat".** The apex of every cone is covered by a smooth collar cone. That collar is shallower than the roof (about 44° against 51°), 1.2–1.5 m in diameter on huts, with a drip edge that overhangs the shingles. Above it sit stacked turned rings, a necked spindle and a tall sharp spike. Finial height above the collar is 0.9–1.3 m. Stone ball finials appear only on stone-roofed round ends (ref1 longhouse).
6. **Chunky, oversized roofing.** Shingles are big and few: 0.35–0.55 m wide, 0.36–0.40 m exposure and 3–4 cm butts. Courses are clearly readable from 30 m. Shake collars are long (0.9–1.2 m) radiating split boards with uneven butts and jagged tops. Thatch is thick (0.35–0.5 m) and laid in visibly stepped layers of about 0.3 m.
7. **Soft, mossy, organic age.** Nothing is crisp. Eave lines wave, cones sag slightly between rafters, finials lean, shingles curl and slip, and stones bulge out of the wall plane. It looks lived-in for 150 years without looking ruined.
8. **Nordic and Slavic timber-church flavour** (bell-cast shingle caps, lantern belts of vertical boards, carved knee-braces) combined with **rough rubble masonry** and **wattle and daub**. Keep that blend and avoid pure Gothic, Tudor or fantasy-castle vocabulary. There are no crenellations, no Gothic pointed arches (arches are round or segmental) and no half-timbered black-and-white framing.

## 2. Roof language (numbers)

| element | pitch | overhang beyond wall face | notes |
|---|---|---|---|
| hut cone | 50–52° | 0.55–0.65 m horiz. | very slightly convex; small eave kick; 16–20 shingle courses eave→collar |
| keep lower skirt roof (octagonal, hipped) | ~40° with bell-cast to ~25° in last 0.8 m | 1.1–1.4 m | horizontal courses of long boards/shingles, hip lines visible, eave fascia slightly upturned at hip corners |
| shake collar | 55–65° | sits 0.3–0.5 m proud of the cone it wraps | 0.9–1.2 m long split shakes, radiating, ragged comb top, uneven butt line |
| caps (keep, turret, mill apron) | 40–50° main, bell-cast to ~25° at eave | 0.45–0.7 m | octagonal pyramid with concave hips; carved eave beam visible underneath |
| thatch (keep west wing) | 48–52° | 0.5–0.6 m | 0.4 m thick, stepped layers, rounded eave roll, comb ridge of splayed shakes |
| mill shingle apron | 35–45° | 0.6–0.8 m beyond cornice | short skirt between stone base and timber tower |

Roof construction must read from below (actor eye level): exposed rafter or pole ends, wall plate/ring beam, battens visible in the eave gap, drip edges, and real thickness at every eave lip (no single-sided planes anywhere).

## 3. Stone language

- **Masonry type:** flat-bedded, roughly coursed limestone/sandstone rubble. Course heights 8–25 cm (mostly 10–15), lengths 20–70 cm, with occasional through-stones up to 90 cm. Courses wander ±3 cm and pinch out. Small pinning stones fill gaps.
- **Every stone is an individual mesh piece** with an irregular outline, 1–3 cm rounded or chamfered arrises, and a slightly pillowed face (proud by 0.5–2 cm). The faces are not coplanar: each one varies 0.5–2.5 cm in depth.
- **Mortar:** a recessed mortar body behind the stones. Joints are 1–3 cm wide and recessed 1–3 cm. Some joints are raked deeper (5 cm) near the ground.
- **Dressed stone** (larger, squarer, flatter faces, 1 cm chamfer) is used only for door and window surrounds, voussoirs, quoins, string courses, cornices and corbels. Voussoirs are irregular in width (no CG-perfect radial fan), and they are thicker at the crown.
- **Walls batter** 2–4° (wider at the base), with footing stones that are larger and project 5–10 cm at ground level.
- **Dry-stone plinths** (huts) are large rounded or sub-angular boulders 0.25–0.6 m across, with no mortar, stacked 1–2 high, and small chinking stones in the gaps.
- **Ground contact:** every building meets the ground through larger footing stones, a few half-buried stones, scattered rubble and a flat threshold stone. No building simply sits on Z=0 as a clean extrusion.

## 4. Timber language

- **Members** are hand-hewn and weathered: square posts 0.22–0.30 m, wall plates 0.20×0.25 m, round poles for hut rafters (Ø 8–12 cm), and planks 25–40 mm thick.
- **Edges:** every arris carries a 1.5–3 cm chamfer or rounded wear. End grain is slightly checked or split; at least some members show modelled splits or notches on hero faces.
- **Irregularity:** posts are within ±1° of plumb, tapered or swelling ±1 cm, never perfectly straight. Planks vary in width (16–30 cm) and have small gaps (0.5–1.5 cm) between them.
- **Joinery is visible:** mortise and tenon with protruding oak pegs (Ø 2.5–3 cm, proud 1–2 cm), curved or straight knee braces (Y-brackets) from posts to the eave beam, and lap joints at ring beams.
- **Doors:** vertical plank doors with 3 horizontal ledges (or 2 ledges + 1 brace) on the inside, iron strap hinges (5–8 mm thick, 40–60 mm wide, ending in a spear or round terminal) with nail heads, a ring pull or latch, and a timber or stone threshold. Arched stone doorways get arch-topped plank doors that fit the arch.
- **Windows** are small (0.5–0.8 m) and set deep in thick walls. They have a heavy timber frame, a cross mullion (2×2 lights), a projecting stone sill with a drip, and a lintel stone or timber lintel.

## 5. Wattle and daub language (huts)

- **Structure:** main posts on the plinth, plus vertical stakes (sails, Ø 4–6 cm) at 0.25–0.35 m spacing.
- **Weave:** horizontal withies (rods, Ø 1.5–3.5 cm) woven alternately in and out of the stakes, with each row offset by one stake. Rods vary in diameter, bundle in pairs or triples in places and are not perfectly horizontal (±2 cm drift).
- **Daub:** applied on some bays as a thick (3–6 cm), lumpy skin with soft bulges and a broken, eroded lower edge that exposes the wattle beneath (ref2: the bay left of the hut door).
- **Visible top and bottom:** the weave tucks under a ring wall plate at the top and sits on the plinth at the bottom.

## 6. Age, sag, irregularity: mandatory "lived-in" pass

- **Deterministic seeds:** use `random.Random(seed)` with a fixed seed per component. The build must be bit-for-bit reproducible.
- **Ridges and eave lines** deviate ±2–5 cm (smooth low-frequency noise, not jitter).
- **Cones** sag 1–4 cm between rafters. Finials lean 0.5–2°. Caps can rotate a couple of degrees off-axis.
- **Shingles:** rotation ±3–5°, lift ±1–2 cm, width ±25%, butt line ±2 cm. About 2–4% are slipped, missing (showing the shingle beneath) or split. Shingles near the eave curl slightly.
- **Stones:** size, rotation and protrusion vary per stone. No stone shape may visibly repeat within 2 m of another. Use at least 24 base variants and then deform each placement.
- **Moss:** moss is a texture job. Optional low-poly moss cushions (`M_moss_clump`) are allowed only at shingle butts, collar tops and eave lips. They are never required and never a substitute for detail.

## 7. Proportion and scale rules (human-scale anchors)

- **Human:** 1.80 m (render_review adds one). Eye height is 1.65 m.
- **Clear openings:** stone arched doors are 1.00–1.10 m wide and 2.15–2.30 m tall to the crown (springing about 1.65 m). Timber door frames give 2.05–2.15 m clear height and 0.95–1.05 m width. Every eave lip directly over a doorway is at least 2.30 m.
- **Steps:** risers 15–20 cm and treads ≥ 30 cm. Threshold stones are 8–15 cm above the outside ground. Window sills are 1.1–1.5 m above floor.
- **Mass references:**
  - Hut: wall 2.4 m and roof about 5 m (total ≈ 8.6 m with finial).
  - Keep: total ≈ 14 m to the finial tip.
  - Mill: hub about 11.5 m and top of the sails about 17 m.
- **Forbidden:** doors that look 3 m tall (a toy-scale giveaway) and doors under 2.0 m (unusable). Detail scale must match reality: shingles that read as 1 m wide or stones that read as 1 m bricks immediately break the illusion next to an actor.

## 8. Technical standards (non-negotiable)

- **Environment:** Blender 5.1.2 as a Python module only: `/opt/bpyenv/bin/python build_<id>.py`. Start with `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- **Source and output:**
  - The build script `buildings/<id>/build_<id>.py` is the single source of truth. It is deterministic, rerunnable and self-contained.
  - It saves `buildings/<id>/<id>.blend` with `bpy.ops.wm.save_as_mainfile(filepath=..., compress=True)`.
  - Never write outside your own building folder and your own renders folder. Do not run git.
- **Units and orientation:**
  - Metres, Z up, ground at Z=0, building base centred at the world origin, all transforms applied (location/rotation/scale identity on mesh objects).
  - **The principal entrance faces −Y**, because render_review's "front" and "actor_closeup" cameras look from −Y.
- **Collections and naming:** one top-level collection per building (`KEEP`, `MILL`, `HUT`), with sub-collections optional. Name objects `<PREFIX>_<part>`, for example `KEEP_wall_hall_stones`, `KEEP_roof_skirt_shingles`, `MILL_sail_A_bars` and `HUT_roof_shingles`.
- **Material slots:** use named placeholder slots only, never textures. Use the shared names `M_stone`, `M_stone_dressed`, `M_mortar`, `M_timber`, `M_timber_weathered`, `M_roof_shingle`, `M_roof_shake`, `M_thatch`, `M_wattle`, `M_daub`, `M_iron`, `M_lead` (smooth cap collars), `M_glass` (if any), `M_rubble` and `M_moss_clump`. Assign them per face where one mesh mixes surfaces.
- **UVs:** every mesh has a UV map (smart UV project or cube projection is fine). Shingles and planks should ideally have UVs running along the grain.
- **Bevels:** no razor edges anywhere. Use real chamfer geometry or Bevel modifiers (angle-limited, 1–3 segments, 0.5–3 cm) plus weighted or auto smooth normals. Live modifiers are allowed because render_review counts the evaluated mesh, but keep viewport and render counts identical.
- **Geometry hygiene:**
  - No visible z-fighting and no gaps where parts should meet. Normals face outward.
  - No floating parts; every piece is carried by something.
  - Single-sided planes are not allowed for anything that can be seen edge-on. Roofing, boards and blades all have real thickness.
- **Budget:**
  - Up to about 1.5 M triangles per building (render_review `stats.json` is the authority), and the `.blend` under 80 MB.
  - Spend triangles where the camera goes: the entrance (actor close-ups), eave undersides, silhouette, finials and sail lattice. Hidden faces (stone backs inside walls, shingle undersides fully covered) should be cheap.
- **Instancing:** prefer real joined meshes, or linked-duplicate mesh objects (shared mesh data), for repeated parts. Collection-instance empties and pure geometry-nodes instances are **discouraged**: render_review only counts and frames MESH/CURVE objects, so instanced parts can be missing from stats and camera framing. If you use them, realize instances in the evaluated mesh.
- **Performance:** a build must complete in under about 10 minutes on 4 shared cores. Generate with bmesh and numpy and avoid per-object operator loops over thousands of objects. Keep the object count sane (under about 400).
- **Review renders:**
  - Command: `/opt/bpyenv/bin/python tools/render_review.py buildings/<id>/<id>.blend renders/<id>/round_NN/ --samples 24`.
  - Quick checks: `--views hero --samples 12`.
  - Full deliverable per round: all 6 views (hero, front, side, back, aerial, actor_closeup) plus stats.json.
  - The CPU is shared, so run one render at a time, with a Bash timeout of 600000 or in the background.
- **Logging:** after every round, append to `director/log_<id>.md` the round number, what changed, the stats (tris, bbox, size_m, file size) and the render folder path.

## 9. Grading rubric (Director grades every round against the references)

Each round is scored on 6 axes. The overall grade is roughly the *lowest* axis rounded up by at most one, so a single weak axis caps the grade.

1. **Silhouette and massing fidelity:** at thumbnail size, is it unmistakably the building in the concept art?
2. **Proportion and actor scale:** are doors, eaves, steps and windows right next to the 1.8 m figure? Do the dimensions match the spec within ±10%?
3. **Construction logic:** does every element look built and carried (plates, rafters, braces, lintels, corbels)? Are there no impossible joints?
4. **Detail density and craft:** individual stones, shingles, withies and planks with thickness; bevels; joinery; ironwork; close-up worthiness at the entrance.
5. **Age and organic irregularity:** controlled sag, lean, wobble and variation, with no CG repetition and no perfect circles or rulers.
6. **Technical compliance:** naming, collections, material slots, UVs, budget, determinism, origin and orientation, and no artefacts.

**What each grade looks like:**

- **≤5, blockout.** Primitive cylinders and cones, flat planes for roofs, no individual units. The silhouette is only roughly right.
- **6, good blockout plus some detail.** The silhouette is recognisable, but surfaces are mostly smooth primitives or displacement noise. Some components are missing (lantern, collar, braces, sails incomplete). Repetition is obvious. It is not usable near camera.
- **8, solid game asset.** The correct silhouette and tiers, individually modelled shingles and stones, and every major component present. Several issues remain:
  - It reads slightly CG: courses too regular, edges too clean, cones too perfect.
  - Some construction details are missing under the eaves or at joints.
  - The entrance is not yet close-up worthy.
  - One or two proportions are off by 10–20%.
- **9, near hero.** Everything in 8 is fixed. It survives a mid-shot. Proportions match the art within 10%. Only minor polish remains: a few repetitive patches, a missing peg or hinge detail, a slightly weak finial profile, small intersections visible only in close-up.
- **10, approved hero asset.** A production designer would sign this off today for close-up shots with real actors, and placed beside the concept art it is unmistakably the same building.
  - The silhouette overlays the art's at every tier.
  - The actor close-up at the entrance holds up: real joinery, ironwork, worn stone, a threshold and plausible depth through the door.
  - Construction logic is complete and the age pass is convincing.
  - Technical compliance is 100%.
  - **Nothing remains on the must-fix list.** If the Director can name any defect a production designer would flag, the grade is not 10.

The Director keeps a must-fix list per building in `director/log_<id>.md`. A round may only be graded 10 when that list is empty and the newest full 6-view render set has been reviewed side by side with the reference crops.

---

## Producer notes from the client (added mid-production; apply from the next round on)

1. **Target is Unreal Engine 5.8 with Nanite enabled.**
   - No manual LODs are needed.
   - Keep geometry Nanite-friendly:
     - closed or solid pieces where possible;
     - no zero-area or degenerate faces;
     - no huge single meshes mixing hero and hidden geometry;
     - nothing modelled that will never be seen (interiors beyond the visible depth of doorways and windows).
2. **The village will need 40-50 buildings, and these three heroes become the basis of a MODULAR KIT.**
   - Write build code so every component is a separate, parameterised function. Examples:
     - `round_stone_wall(radius, height, seed)`
     - `conical_roof(radius, pitch, flare, overhang, tiers, seed)`
     - `arched_door(width, height)`
     - `finial(style)`
     - `turret(...)`
     - `sail(...)`
   - Each component produces its own named object(s).
   - Avoid code that only works for one hard-coded size.
3. **Repeated small elements should share mesh data** where it does not hurt the look. These are shingle or shake variants, stone variants, balusters, pegs, nails and hinge parts.
   - Build a small pool of variants, roughly 6-20, and place linked duplicates or instances rather than unique copies of everything.
   - This becomes Unreal instanced static meshes and keeps memory sane across 50 buildings.
4. **Camera usage:**
   - at most about 3 buildings within 10 m of actors at once;
   - typical shots are actors right outside one building's entrance, and walk-throughs past many buildings.
   - Close-up quality matters most at entrances, ground contact and eye-level walls. Roof tops are seen mainly from the aerial and mid distance.
5. These notes do NOT lower the 10/10 bar. They govern how the geometry is structured.

### Producer note 6: hidden / buried triangles (client requirement; applies from the next round on)

Remove or minimise geometry that can never be seen from outside the building, wherever that is practical.

**How it is measured.** `tools/render_review.py` now runs `tools/hidden_tris.py`.
- The script ray-casts sampled triangles from eye-level, crane and aerial viewpoints.
- It writes `est_hidden_pct` into `stats.json`, with a per-object breakdown in `hidden.json`.
- You can also run it on its own: `/opt/bpyenv/bin/python tools/hidden_tris.py <file.blend>` (about 10 s).
- **Target: est_hidden_pct ≤ 15%.** The round-2 roundhut measured about 46% (about 680k of 1.47M triangles).

**Typical fixes:**
- **Masonry:** each stone keeps only its exposed face, plus its sides down to the mortar recess depth and a few mm more. Delete the back faces and the buried sides. Delete the wall core behind full stone cover.
- **Shingles, shakes and thatch courses:** model the exposed part plus only enough hidden overlap to read correctly where edges ARE visible (eaves, hips, verges, ridge, holes). Delete the rest of each covered unit.
- **Wattle:** do not model rod halves buried inside daub, or rod backs facing a solid wall.
- **Roof structure:** battens, purlins and rafters only where they can be seen: under the eaves from eye level, and through doors and windows. Delete the rest.
- **Below ground:** nothing deeper than 5 cm.
- **Interiors:** only the depth visible through openings, about 1.5 m. Close the rest off with simple dark blocker surfaces.
- **Mill rotor:** keep the backs of sails and blades. They are visible from behind.

**Never open holes when culling (lesson from the windmill, round 3).**
- When covered parts of shingles, shakes, thatch or stones are removed, put a cheap continuous backing surface underneath: a sarking or deck plane, a wall core face, or a dark blocker. Then any gap, slipped piece or missing piece shows a solid surface, not sky or a black void.
- A single low-poly backing plane costs almost nothing. It also lets you cull far more aggressively.
- Before returning, check the roof and wall outlines for see-through pixels from several exterior cameras.

**Reinvesting the savings.** Triangles saved should go into visible close-up detail: entrances, ground contact and eye-level walls. Never cut anything that affects the silhouette or a visible edge.

### Producer note 7: material slots (client requirement, revised: the limit is 15)

**At most 15 material slots across the whole kit, and so also per building.** Every building and kit component uses only this shared palette, which is the set already in use plus moss:

| Slot | What goes on it |
|---|---|
| `M_stone` | stone |
| `M_stone_dressed` | dressed stone |
| `M_rubble` | rubble |
| `M_mortar` | mortar, chinking |
| `M_daub` | daub, plaster |
| `M_wattle` | wattle rods |
| `M_timber` | timber |
| `M_timber_weathered` | weathered timber |
| `M_roof_shingle` | shingles |
| `M_roof_shake` | shakes |
| `M_thatch` | thatch |
| `M_iron` | iron |
| `M_lead` | lead |
| `M_earth` | earth, apron, path |
| `M_moss` | moss clumps, if modelled |

**Rules:**
- Do not invent new slot names. Map anything new onto the closest palette entry.
- The `Mask` colour attribute is now MANDATORY. See producer note 9, whose channel layout supersedes the one given here earlier.
- `stats.json` reports `material_slot_count`. The director treats any slot outside this palette as a must-fix, or more than 15 slots.

### Producer note 8: pace (applies to builders)

Time-box each builder round to roughly 60-90 minutes of work. After the full review render, fix only blocking problems you find in it, then return your report. The director's next grade is the feedback loop. Open-ended self-polishing after the review render slows the whole production.

### Producer note 9: MANDATORY `Mask` colour attribute (client requirement; applies from the next round on)

**Why.** Texturing will use jointless Megascans-style surfaces (rock, wood grain, straw), applied with world-aligned (triplanar) projection in Unreal. The geometry supplies the stones, joints, shingles and planks. The material needs per-piece data so that every stone, shingle and plank doesn't show the same patch of texture.

**Requirement.** Every mesh object carries a colour attribute named exactly `Mask`:
- domain CORNER;
- type BYTE_COLOR or FLOAT_COLOR;
- set as both the active and the default (render) colour attribute, so it exports to Unreal as vertex colour.

**Channels:**

| Channel | Meaning | Rule |
|---|---|---|
| **R** | per-piece random, 0–1 | Constant across each individual piece (one stone, one shingle or shake, one plank, one rod, one thatch clump), and different between neighbours. Seeded and deterministic. |
| **G** | wear / damage, 0–1, per piece | Higher on chipped, split, slipped, weathered or replaced pieces. Low on fresh dressed work. |
| **B** | moss / dirt / damp, 0–1, may vary per vertex | High near ground contact and plinths, on upward-facing ledges, sills and roof butts, under drips and on shaded north faces. Low on sheltered vertical faces high up. |
| **A** | reserved | 1.0 |

**Applies to:**
- all repeated-piece geometry: stones, shingles, shakes, planks, rods, thatch clumps, balusters, blades and boards;
- every other mesh too. Use R = a per-object random, and fill G and B sensibly.

**Enforcement.** `stats.json` lists `mask_attribute_missing`. Any object listed there is a must-fix.

### Producer note 10: NO loose ground stones or paths (client requirement; applies from the next round on)

**Rule.** Loose stones, scattered rubble, path flags, stepping stones, gravel and ground aprons or earth discs that are **not part of the building itself** are out of scope. Terrain and set dressing will be built separately in Unreal.

**Delete** every such object from every building, together with any code that exists only to place them.

**The director and auditors must NOT score anything against the reference for ground dressing.** Do not penalise its absence. Do not ask for it back.

**What stays**, because it is part of the building:
- the building's own footing, plinth and foundation course;
- the door threshold, and a door step that is built into the entrance;
- pad stones under posts;
- the feet and chocks of the mill props;
- anything structurally attached.

**Ground contact still matters.** The building's own footing must meet Z = 0 convincingly, so that it can sit on any terrain. A shallow (≤ 5 cm) buried skirt is allowed.

### Producer note 11: detail-scale and decal rule (client requirement; applies in the kit phase, phase 2, onward)

**Goal.** Better performance and cheap variation across 40–50 buildings.

**Geometry KEEPS:**
- all silhouette and edge detail;
- every discrete piece (stones, shingles, shakes, planks, rods, thatch clumps, balusters, ironwork);
- joints and recesses that cast real shadows;
- anything with relief of about **2 cm or more**.
- **Entrance exception:** within about 3 m of a main entrance, between 0 and 2.5 m high, keep relief of **1 cm or more** where it reads in grazing light at actor distance.

**Geometry DROPS** (it goes to materials and decals instead) surface relief under those thresholds:
- daub shrinkage cracks;
- wood checks, splits, adze and saw marks, and grain;
- chisel tooling;
- chips and spalls under 2 cm;
- straw striation grooves;
- fine plank wear.

Megascans-style normal and height maps on jointless surfaces supply these. Never model weathering (moss, damp, soot, streaks, stains, lichen, rust) as geometry. The `Mask` B channel covers macro moss and dirt. Decals cover the rest.

**Decal anchors.** Every building, and every kit assembly, exports the places where decals naturally belong. This lets Unreal PCG place and vary them with a seed.

- **In Blender:** a collection `DECAL_ANCHORS` of empties named `DA_<type>_<nnn>`. Each empty's −Z axis points into the surface it decorates, and each carries these custom properties:
  - `decal_type`, one of: `crack`, `damp_rise`, `moss`, `soot`, `water_streak`, `rust_stain`, `plaster_patch`, `repair_patch`, `lichen`, `grime`;
  - `size_w` and `size_h` in metres;
  - `surface`, the palette material slot it sits on;
  - `probability`, 0–1, the chance PCG uses it;
  - `seed`.
- **As a file:** `buildings/<id>/decal_anchors.json` holding the same data. It records position, normal, up, size, type, surface, probability and seed. Positions are in metres, building-local, Z up. State the units and axes in the file header.
- **Placement logic must be physically plausible:**
  - `damp_rise` and `moss` at the base and on north faces;
  - `water_streak` under sills, eaves drips and the ends of the wheel and boom;
  - `soot` above openings and smoke holes;
  - `rust_stain` under ironwork;
  - `crack` at the corners of openings, under lintels and at settlement points;
  - `plaster_patch` and `repair_patch` scattered on daub and rendered walls;
  - `lichen` on stone tops and weather faces.
- **Count:** aim for about 40–120 anchors per hero building.

**Still in force:** hidden triangles ≤ 15%, the material palette, `Mask`, and every other producer note. Triangles freed by this rule may go to silhouette and discrete-piece quality, or stay saved.

### Producer note 12: modularity over detail (client direction, 2026-10-16; applies from now on)

**Direction (client's words):** "We don't need more detail at this point, we need reusable modules that can be combined to complete entirely unique structures." The client is hesitant to push surface detail further before materials and textures are added.

**What this changes:**
- **No more detail rounds on the heroes.** The hero kit gates are closed (see the production plan). Do not spend builder time on finer surface detail, micro-wear, hewing marks, crack shapes or similar polish. Materials, textures and decals will carry that.
- **The work is the kit.** Builders improve reusable, parameterised modules and the way they combine: new module types where a building needs one, parameter ranges that produce genuinely different results, clean junctions between any two modules that can meet, and an assembly API that makes a new building a short declarative recipe.
- **Variant grading uses the modularity rubric below, pass mark 8.2.** It replaces rubric axes 4 (detail density) and 5 (age) for variants. Detail is judged only to the extent that a module reads as the right construction at mid-shot distance; do not ask for more surface detail.

**Modularity rubric (variants and any kit-assembled building).** The overall grade is roughly the lowest axis, rounded up by at most one.
1. **Silhouette and massing:** a distinct, believable building of this village at thumbnail size, unmistakably the concept-art style.
2. **Proportion and actor scale:** doors, eaves, steps and windows right next to the 1.8 m figure.
3. **Construction logic:** every module looks built and carried; roofs sit on walls, walls on footings, nothing floats or interpenetrates visibly.
4. **Seams and junctions:** where modules meet (wall to wall, roof to wall, roof to roof, turret to body, annex to main body, roof to tower) the joint is closed, flashed or covered, with no gaps, see-through pixels, z-fighting or obvious clipping.
5. **Distinctness and reuse:** clearly a different building from the three heroes and from the other variants, yet built from shared modules. Score down for a near-copy of a hero, and for bespoke one-off geometry that is not a reusable kit module.
6. **Technical compliance:** producer notes 1-3 and 6-11 (Nanite hygiene, pooling, hidden ≤ 15 %, palette, `Mask`, no ground dressing, decal anchors plausibly placed), deterministic seeded build, real-world scale.

**Kept unchanged:** the 8.2 pass mark, producer notes 1-11 as technical rules, every client correction, and the signed-off deliverables.

### Producer note 13: CLIENT CORRECTION — no LED volume; a hobby production aiming for high polish (2026-10-16)

Client's words: "there is no LED volume in use here. This is an amateur hobby production but I want to attempt to have high level of polish".

- **Supersedes** every earlier mention of an "LED-volume virtual production" in this bible, the logs, the specs and the workflow prompts. The target is still **Unreal Engine 5.8 with Nanite** (producer notes 1-11 stand as technical rules), but there is no stage, no real-time playback requirement on an LED wall and no stage render nodes.
- **The reference machine is the client's own desktop:** Ryzen 5 5600X, 16 GB RAM, RTX 3060 12 GB. Memory and streaming budgets are judged against it (see the production plan's memory estimate).
- **Final frames can be rendered offline** (Movie Render Queue, with path tracing or high-quality Lumen), so frame rate is not the constraint; GPU memory, build time and disk size are.
- **Polish still matters most** — the client wants a high level of finish. Per note 12, that polish now comes mainly from materials, textures, decals, lighting and set dressing, on top of clean, well-constructed modular geometry.
- Close-up quality rules (note 4: entrances, ground contact, eye-level walls) stay, because shots still come close to the buildings.

### Producer note 14: CLIENT DIRECTION — the kit is an authoring toolbox for 12-15 curated designs (2026-10-16)

- The village of 40-50 placements is built from **12-15 unique curated designs**. Variety comes from instancing (rotation, mirroring), PCG decals on the exported anchors, per-instance `Mask` material variation, small kit add-ons and set dressing.
- **The kit is the authoring toolbox** for those designs: shared modules, palette, `Mask`, decal anchors and UVs, with fixes made once for every building.
- **Dropped:** the requirement that any combination of modules be clean, and the 40-50-building variant generator.
- Each design is a curated recipe, reviewed as a building on its own merits, with the modularity rubric (note 12) still applied. Junction fixes are made as each design needs them and stay reusable in the kit.
- See the production plan (phase 2 and phase 3) for the reframed decision and scope.

### Producer note 15: CLIENT RULE — new structures at most 1,000,000 triangles (2026-10-16)

Client's words: "Keep the new structures to a one million triangle limit".

- **Every new structure** (every kit variant and every curated design from now on) must render at **1,000,000 triangles or fewer**, as counted by `stats.json` `triangles`. This supersedes the 1.5 M per-building limit for new structures.
- The three signed-off heroes keep their current counts (keep 1.17 M, windmill 1.15 M, hut 0.88 M).
- Over the cap is a **hard requirement failure** for the director and the auditor, the same as hidden % or the palette.
- How to get under it without losing what the camera sees, in priority order:
  1. drop hidden and near-hidden geometry;
  2. coarsen stone and shingle tessellation on faces seen only from mid-distance (above about 4 m, roof tops);
  3. reuse pooled pieces rather than unique ones.
  
  Never cut silhouette, entrance or ground-contact detail (note 4).
- At the time of this note: v3 longhouse 0.47 M and v2 tiered hall 0.95 M comply; v1 watchtower 1.06 M and v4 mill-house 1.38 M are over.

### Producer note 16: CLIENT DIRECTION — one village, one building culture (2026-10-17)

Client's words: "Remember that the new designs should still give off the feeling that they were built by the same people with the same techniques and materials of the other buildings".

- **Every new design** (the harbour house, the boathouse or barn, the add-ons and all later designs) must read as built by the **same community, with the same techniques and materials** as the existing buildings: the heroes (keep, windmill, roundhut) and the accepted variants (v1-v4).
- **Same materials:** the shared 15-slot palette only (rubble and dressed stone, lime mortar, timber and weathered timber, shingle and shake, thatch, daub, wattle, iron, lead, moss). A timber building still sits on the same rubble plinths and dry-stone footings, uses the same timber sections, the same shingle sizes and courses, the same iron hardware and the same lead flashing as the rest of the village.
- **Same techniques:** reuse the kit's existing construction details wherever they apply, rather than inventing new ones: the door frames, thresholds and steps, window frames and shutters, eave rolls, verges and ridge pieces, corner and plinth details, finials, and the age and moss treatment (`age_defaults`). A new family is **new forms from the same hands**, not a new style.
- **Same proportions and age:** the same storey heights, door and window sizes against the 1.8 m figure, roof pitches within the bible's ranges, and the same weathering level.
- **Director and auditor:** "reads as the same village" is part of the **distinctness and reuse** axis. A design that looks imported from another place or period, or that uses materials or details found nowhere else in the village, is a must-fix.
### Producer note 17: CLIENT DIRECTION — round structures and soft, organic lines (2026-10-17)

Client's words: "something that makes the initial concept art unique is the use of round structures and soft, organic lines. In my opinion It's what gives it a unique aesthetic rather than a more generic village building".

- **This is the village's signature** (it extends rule 1 and note 16). Every new design, timber and rectangular ones included, must carry it; a building that could stand in any generic medieval village is a must-fix.
- **Round structures:** each design includes at least one round or polygonal element that is integral to its composition, not stuck on: for example a round stair or lookout turret, a round end or annex under a cone, a drum-like corner, a bowed or apsidal end, a round hoist or smoke hood. Prefer the kit's existing round families (drum, round stone body, cone roof, tiers, finials) so it also satisfies note 16.
- **Soft, organic lines:** no ruler-straight silhouettes. Bell-cast or swept eaves, gently sagging ridges and settling courses, rolled and rounded eaves and verges (the thatch / shingle rolls), curved braces and brackets, slightly bowed walls and out-of-true timber, rounded thresholds and plinth stones. Keep it believable and structural, never cartoon-wobbly.
- **Director and auditor:** judge it under **silhouette** and under **distinctness and reuse**. Make the new softness reusable: an option on the kit module (e.g. a swept eave or ridge sag on a roof, a bow on a wall run), not one-off code.
### Producer note 18: CLIENT RULE — a rectangular or square cottage has at least one eyebrow dormer (2026-10-18)

Client's words: "If the cottage will be rectangular / square it minimum needs a eyebrow dormer".

- **Every cottage / house design whose plan is rectangular or square** (or built from rectangular wings) carries **at least one eyebrow dormer** (`linear_roof.GableRoof(eyebrows=[eyebrow(profile="arch", respace=True, ...)])`, the harbour-house form: one continuous arch, no flat run). This keeps a plain box in the village's organic language (notes 16 and 17).
- Other dormers, chimneys and add-ons may be added on top of it; they do not replace it.
- **Director and auditor:** missing on such a design is a must-fix.
- The eyebrow must work on both village coverings: shingle (exists) and **thatch** (the kit option is to be extended, defaults unchanged).
### Producer note 19: CLIENT RULE — square, angular walls get rounded roofs: "an oval on the rectangle" (2026-10-18)

Client's words: "if the walls be square and angular we should counterbalance with rounded roofs. Not just /\ An oval on the rectangle". The client chose the form: **"Rounded hips + soft crown"**.
- **The form:** on a rectangular (or square) wall plan, the roof has **no flat gable ends**.
  - Each free end curves round as a **half-cone / round hip**, so the roof reads as an **oval in plan** over the rectangle, oversailing the corners.
  - The **cross-section is softly convex**: a gentle bulge with a rolled ridge, not a straight-sided triangle.
  - The village soft options still apply: sag, swept eaves.
  - This is the classic rounded thatch "loaf" roof, and it counterbalances the angular walls.
- **Applies to every new design with square / angular walls** (cottages, houses, stores, add-on wings).
  - Exceptions only where the client has chosen otherwise: the ref4 harbour house's cruck gable, and the barn's cart-entry gable.
  - The accepted buildings are not retrofitted unless the client asks.
- **Kit:** a reusable roof option or module (e.g. `GableRoof(hips="round", crown=...)` or a `loaf_roof` component) for **thatch first, shingle if feasible**, with defaults unchanged. It must work with:
  - the valley, where wings meet (the joined end has no hip);
  - the eyebrow (note 18);
  - dormers;
  - a chimney through the roof or rising through a round hip.
- **Director and auditor:** a plain /\ gable roof on square walls in a new design is a must-fix.
### Producer note 20: CLIENT DIRECTION - use wattle and daub across the village (2026-10-18)

Client's words: "lets make sure that we are utilizing wattle and daub as right now we have a singular building using this technique so it seems out of place".
- Wattle-and-daub (kit `daub.round_daub_wall`, `wattle`, `frame.RoundFrame`, path walls via `arc_path` / `line_path`) must appear on several buildings, not only the wattle_roundhut and the v4 house wing, so it reads as a village technique.
- Every NEW design carries daub on a meaningful wall area: an upper storey, a gable or hip-end infill between timber posts, a round annex or oven house, a lean-to, or a whole wall. It sits on the usual rubble plinth and under the usual thatch (note 16). Prefer reuse of the kit daub / wattle modules; if they only do round walls, add an optional path-wall mode (defaults unchanged, kit edit rules).
- Rubble, board-and-batten and daub should mix in each design (rubble where it takes weight and meets the ground, daub where it is light).
- Director and auditor: a new design with no daub, or daub that looks pasted-on, is a must-fix under distinctness and reuse. Accepted buildings are not retrofitted unless the client asks.
### Producer note 21: CLIENT DIRECTION - v8, v9, v10 are the LAST three building types; hero-comparable quality; 2 quality-lift rounds (2026-10-18)

Client's words: "these should be our last three building types for the village before we start diversifying with add ons, decals, set dressing, etc so they should still remain a comparable quality. add 2 quality lift rounds. we can wait to see the textured renders before committing to this direction."
- v8_byre_smokehouse, v9_ale_house and v10_net_loft_cottage complete the curated set (14 designs). Variety after them comes from add-ons, decals and set dressing.
- They must stay comparable in quality to the hero buildings (the client judged the round-2 previews substantially lower). The director grades against the heroes' level of modelled detail, texture read and composition.
- Budget: 2 quality-lift rounds per design (rounds 3 and 4), on top of the 2 done. Further rounds need the client's OK.
- Gate: wait for the textured lookdev renders (lookdev/renders_r2/) and compare with the heroes before the lift list is fixed.