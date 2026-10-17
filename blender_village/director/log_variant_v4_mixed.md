# Variant v4_mixed: the mill-house

## v4_mixed round 1 — builder entry

**What I built.** A **mill-house**: a miller's wattle-and-daub roundhouse built against a small stone tower mill
that carries a fan wheel. The village has no mill-house yet. The building mixes module families from all three
heroes and is assembled from kit modules only.

- **House wing (hut family, `RoundFrame`, prefix `V4H`).**
  - Wall radius 2.85 m, eave 2.45 m.
  - Dry-stone plinth, daub wall with its exposed-wattle patches moved to the side away from the mill, pegged wall
    plate.
  - 51° chunky-shingle cone with the ensemble age pass.
  - Projecting framed door facing −Y, with its step and the interior behind it.
  - The apex carries the **keep family's** turned finial over a fitted lead hat (pitch 48°, shallower than the roof)
    instead of the hut's spike.
- **Mill wing (drum family, `DrumFrame`, prefix `V4M`).**
  - Slender battered rubble drum: r 1.95 → 1.82 m, 5.30 m to the cornice.
  - The balustrade band (3.62–3.99 m) and a 6-bay blind arcade are lifted clear of the house roof, so the roof
    meets plain rubble just under the band's lower string course.
  - Arched door facing −Y with its step; two slit windows on the +X and back faces.
  - Shake apron, boarded smock tower (6.35–10.05 m), hipped cap (yaw 25°).
  - 12-blade fan wheel (tip radius 3.05 m), tail vane on a 4.9 m rear boom.
  - No raking props.
- **Junctions (new kit module `components/junctions.py`, using keep-family pieces).**
  - **Roof to tower.** The house cone runs into the drum between z 2.61 and 3.45 m, over 79° of drum azimuth.
    The real roof-top / drum-face line is traced by ray casts on the built shingles. It is closed by one continuous
    lime-mortar flaunching band (the keep's `thatch.flaunch_loop` / `mortar_fillet`), 2.5 cm over the highest
    shingle and its back buried 3.5 cm in the masonry. Lead end-aprons cover the cut eave lips where the eave dies
    into the stone (object `V4J_roof_tower_fillet`).
  - **Wall to tower.** The daub wall runs 0.12 m into the drum. At both crossings a hewn abutment post (the keep's
    `hewn.hewn_square`, 0.22 × 0.22 m) stands from the plinth to the wall plate, with its drum half let 4 cm into
    the masonry so it straddles the daub / stone seam. A mortar pointing bead follows the post / stone seam up the
    batter (`V4J_abutment_posts`, `V4J_abutment_pointing`).
  - **Plinth to footing.** The house plinth boulders run into the drum's footing course (stone into stone).

**Plan.** House centre (−1.70, 0.15), drum centre (2.82, 1.36), 4.68 m apart on a 15° line. Both doors face −Y;
the house door is the principal entrance. The footprint is centred on the origin within about 0.3 m. The wheel and
tail push the bounding box to +X / +Y.

**The recipe.** `buildings/variants/v4_mixed/build_v4_mixed.py`: 92 non-blank, non-comment lines, including the
module docstring.
- It is two `Wing`s and two junction steps. Each wing is a list of the same component calls a hero recipe makes,
  with parameter dicts: `HOUSE`, `HOUSE_PATCHES`, `APEX`, `MILL` (drum / tower / apron / cap / wheel / tail) and
  `MILL_RUBBLE`.
- A different mill-house is a different `HOUSE_AT` / `MILL_AT` and parameter set.
- Environment switches: `V4_OUT` builds to scratch; `V4_FAST=1` skips the cull (look-dev only).

**New kit modules** (recorded in `kit/changes/v4_mixed.md`):
- **`village_kit/compound.py`.** `Wing` and `build_compound` assemble several family frames in one building.
  - Each wing is built at the origin with unmodified family components, then parked, then placed. Meshes are
    baked; pooled duplicates keep their matrices; anchors are transformed with the wing.
  - Junction steps run after placement.
  - ONE note-6 cull runs over every wing's targets. It uses each wing's actor / door / crane rings and drops
    viewpoints inside another wing's body.
  - The merged anchors are re-audited on the whole building (`anchor_audit`). Anchors covered by the neighbour or
    a flashing are dropped, and the rest are thinned per type to 120.
  - Step helpers: `configure` and `patches_by_azimuth`.
- **`components/junctions.py`.** `roof_tower_flashing` and `wall_tower_abutment`, which run on generic body
  descriptions (`tower_of`, `round_wall_of`), plus `trace_roof_on_tower` and `end_apron`.
- **`components/round_apex.py`.** `turned_apex`: the keep's turned finial and lead hat on any `RoundFrame` cone.

**Bug fixes to existing kit modules.** Each fix is behaviour-identical for the heroes.
- `conical_roof.build_eave_closure` looked up the literal `HUT_` names.
- `rotor_checks` crashed on a mill without props.
- `tail_vane.tail_boom` left iron bands floating past a boom shorter than the hero's.

**Stats** (`renders/variants/v4_mixed/round_01/stats.json`):

| Measure | Value |
|---|---|
| Triangles | 1,391,180 (1,587,416 before the compound cull; −99,224 polygons) |
| Hidden (est_hidden_pct) | 13.5 % |
| Material slots | 12, all from the palette |
| `mask_attribute_missing` | none |
| Objects | 285 |
| Bounding box | x −5.18 … 6.27, y −3.79 … 5.85, z −0.041 … 14.00 (size 11.45 × 9.64 × 14.04 m) |
| `.blend` | 31.7 MB, compressed |
| Decal anchors | 120 (191 placed; 19 dropped by the whole-building audit; 52 thinned) |

- Anchor counts by type: crack 29, moss 19, water_streak 19, damp_rise 14, lichen 11, rust_stain 7,
  plaster_patch 6, repair_patch 6, soot 5, grime 4.
- Anchor gates: house anchors `validate_anchors` (applied); mill anchors `drum_tower_decals_gated` (snap, validate,
  audit); every anchor `anchor_audit` on the finished building.

**Renders.** `renders/variants/v4_mixed/round_01/`: all six views at 24 samples. I inspected every view, plus
scratch close-ups of both junctions, both posts and the tail.
- No gaps or see-through pixels at the roof / drum line. The eave lips die into the stone under the lead aprons.
- The posts cover the daub / stone seam.
- The band sits clear above the flaunching.
- A floating iron band past the shortened boom end was found in look-dev and fixed in the kit (above).

**Known gaps.**
- From most angles the flaunching band reads as a soft mortar fillet half-hidden by the chunky shingle butts. In
  the round-1 renders it is not a strongly legible lead / mortar line.
- The house uses the kit-1.0.0 default daub coat (smooth). This was chosen for the triangle budget, and per note 12
  no surface detail was added.
- The junctions are built for round tower bodies (`tower_of` = `DrumFrame`). Another family's round body needs a
  one-line adapter.
- The compound cull is slow on the shared CPU (about 30 min, 15 targets × ~580–660 viewpoints).
- Under memory pressure a spawn worker can die. `core.visibility_cull` then hangs: respawned workers cannot import
  bpy. This happened in one of my runs (MemoryError), and I killed and re-ran that run with 3 processes.
- The house's eave closure (hut module) faces inward.
- No windows in the daub house; the kit has no window module for a round daub wall yet.

**Hero re-runs.** Existing kit modules were changed, so all three heroes were rebuilt to scratch via `KEEP_OUT` /
`HUT_OUT` / `MILL_OUT`, after the last kit edit. All three built without errors at exactly their recorded
triangle counts:

| Hero | Triangles | Record | Notes |
|---|---|---|---|
| tower_windmill | 1,146,243 | 1,146,243 | clearance PASS, 106 anchors |
| wattle_roundhut | 876,619 | 876,619 | |
| hilltop_keep | 1,166,874 | 1,166,874 | |

## v4_mixed round 1 — score 8.0/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v4_mixed/round_01/`, plus `stats.json`, `hidden.json` and
  `buildings/variants/v4_mixed/decal_anchors.json` (120 anchors).
- The recipe, `kit/changes/v4_mixed.md` and the new kit modules `compound.py`, `components/junctions.py` and
  `components/round_apex.py`.
- 33 director close-ups of every module junction and 23 see-through checks (black clay against a red sky) in
  `renders/variants/v4_mixed/round_01/director_extra/`. The j01, j02 and j17 framings are too tight; the k and m
  series replace them.
- Ray probes on the delivered `.blend`: interpenetration with the drum, light leaks through both doorways, door
  clear openings, eave height over the door, anchor-to-surface distance and eave-closure normals.

**Recipe and kit check (director-verified).** The recipe imports only kit modules. It holds no bmesh or geometry
code of its own: two `Wing`s, each an ordered list of standard family components, plus two junction steps. The new
geometry (the flaunching band, end aprons, abutment posts, pointing and the turned apex on a round cone) all lives
in new kit modules that work on generic body descriptions (`tower_of`, `round_wall_of`). They are recorded in
`kit/changes/v4_mixed.md`. That is the modular behaviour note 12 asks for.

**Compliance (director-verified).**
- 1,391,180 tris, 13.5 % hidden, 12 palette slots, `mask_attribute_missing` empty.
- Every unique mesh has an identity transform and a UV map.
- 285 objects in the collections `V4`, `V4_house`, `V4_mill`, `V4_junctions`, the two `_kit_instances` pools and
  `DECAL_ANCHORS`. Pegs, nails, hinges, chinks, balusters, corbels and bolts are pooled linked duplicates.
- No ground dressing. Interior floor, hearth, step stone and threshold belong to the building.
- All 120 anchors are within 5 cm of a surface, and their placement is plausible: damp_rise at 0.46–0.73 m, lichen
  on up-facing stone, moss in the roof/drum valley, water_streak under drips.
- Determinism was not re-verified by a second build (the build takes about 30 min); every seed in the recipe is fixed.

**Probe results.**
- House door: 0.97 m clear width, 2.10 m clear height above the 0.17 m threshold, eave lip over the door 2.49–2.59 m.
- Mill door: 1.0 m wide, head at 2.26 m.
- Through the house doorway, 0 of 5,616 rays reach the sky. Through the mill doorway, 16 of 5,616 slip through gaps
  in the interior floor (see the nice-to-have list).
- House parts that run into the drum stay inside solid masonry and never reach the drum's interior void. Shingles go
  up to 0.41 m into the drum, battens up to 0.64 m, plinth boulders up to 0.39 m.
- `V4H_eave_closure`: all 478 faces point at the hut interior.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.4 | A believable mill-house of this village at thumbnail size: a tall-coned daub roundhouse leaning on a slim battered stone tower mill with shake apron, smock tower, cap, 12-blade fan wheel and tail vane. The front, back and hero views read as one building, and the concept-art style is right. |
| 2 Proportion and actor scale | 8.6 | Both doors are correct next to the 1.8 m figure: house 0.97 × 2.10 m clear, mill 1.0 m wide with its head at 2.26 m. The eave over the house door is 2.5 m, the cone is 51°, total height is 7.9 m to the finial, and the mill rises to 14 m (a smaller mill than the hero, as intended). The mill door sits a little tight in the re-entrant corner, about 1.2 m from the house wall. |
| 3 Construction logic | 8.0 | The house sits on its plinth, the cone on a pegged plate, and the drum on its footing. Abutment posts carry the daub/stone seam and the plinth runs into the footing course. The weak point is where the half-cone dies into the drum: rafter poles, battens and the eave closure end inside the stone at random angles, with nothing for the cut rafter feet to bear on. |
| 4 Seams and junctions | 7.7 | Every junction is closed and no see-through shows anywhere on the building (all red checks are clean except true sky). Wall to tower (k01, k04, j16) and plinth to footing (k08, k09) are good. The roof to tower junction is closed but not legible: at mid-shot and from the crane the shingles seem to run straight into the rubble, with the fillet hidden under the butts (j03, k03, k10, m04). At both eave ends, seen from eye level under the eave, the structure stabs into the stone as a tangle (m01, m02, k06, k07). |
| 5 Distinctness and reuse | 8.2 | A new building type built 100 % from kit modules, with three new generic modules recorded for the merge. It is clearly different from v1, v2 and v3. Points off: the two wings are close to the existing presets (`HUT_KIT_VARIANT` r 2.90 / eave 2.60, against 2.85 / 2.45 here; the mill `KIT_VARIANT` drum 2.00 / 1.88 with 12 blades, against 1.95 / 1.82). It therefore reads as the hero hut parked against the small hero mill. The keep family contributes only a finial, a fillet and two posts. |
| 6 Technical compliance | 7.8 | All producer-note gates pass (budget, hidden, palette, `Mask`, pooling, anchors, no ground dressing). But the build takes about 30 min, three times art bible §8's limit of about 10 min, and the compound cull hangs when a spawn worker dies. `V4H_eave_closure` is a single-sided band, facing inward, that is seen from outside under the eave. |

**Verdict: 8.0/10, NOT PASSED (pass mark 8.2).** As a modularity test this is the strongest variant so far. It
is a short declarative recipe, two family frames are combined through `compound.build_compound`, and the new
junction modules work on generic body descriptions, so the next roof-into-tower or wall-into-tower joint gets them
for free. Two things cap the grade:
- the roof/drum junction is closed but reads as clipping, and its two eave ends are a tangle of structure in the
  stone;
- the 30-min build breaks §8.

Every fix below is module-level (`junctions`, `compound`, `conical_roof`), so every future compound building inherits
it.

**Strengths**
- The recipe really is a recipe: 92 lines, two `Wing`s and two junction steps, with no geometry code. A different
  mill-house is a different `HOUSE_AT` / `MILL_AT` and parameter set.
- `compound.build_compound` is a real assembly API for multi-family buildings:
  - each wing is built at the origin with unmodified family components, then placed;
  - pooled duplicates keep their matrices;
  - one combined hidden cull runs over all wings;
  - the anchors are re-audited on the whole building.
- `junctions.roof_tower_flashing` traces the true roof-top/tower-face line by ray cast on the built roofing. It
  works for any roof against any round tower and reuses the keep's `flaunch_loop`.
- `wall_tower_abutment` is a convincing, generic seam answer: hewn posts let into the masonry with a pointing bead
  that follows the batter. It reads well at eye level (k01, k04).
- No see-through anywhere on the building: all 23 red checks show only true sky, and 0 of 5,616 house-doorway rays
  escape.
- The three bug fixes to existing modules (the hard-coded `HUT_` lookup, the prop-less `rotor_checks` and the
  floating boom bands) make the kit more general and keep the heroes behaviour-identical, re-run at exact triangle
  counts.
- Technically clean: 13.5 % hidden, 12 palette slots, `Mask` on everything, identity transforms, UVs, 285 objects
  and 120 plausible anchors.

**Must-fix (round 2)**
1. **`junctions.roof_tower_flashing`, the two eave ends of the roof/drum run.** Front end at about (1.0, −0.3,
   2.45–3.1); back end at about (0.9, 2.3, 2.45–3.1). See m01, m02, k06 and k07.
   - What is wrong: `V4H_rafters`, `V4H_battens` (up to 0.64 m into the drum), `V4H_roof_starter` and
     `V4H_eave_closure` all cross the drum face at random angles. From eye level under the eave, beside both doors,
     they read as poles and boards stabbed into the rubble, and the cut rafter feet have nothing to bear on.
   - What it should be: the junction step clips every structural part of the roof wing at the tower face R(z)
     (trim, not bury).
     - The rafters that land on the tower stop on a timber pole-plate or ledger (`hewn.hewn_square`, about
       0.15 × 0.20 m). It follows the traced roof line about 0.25 m under the deck and is carried on two or three
       stone corbels from the drum's corbel pool.
     - The starter course and the eave closure end under the lead end-apron.
     - Make this `roof_tower_flashing(ledger=True)` and the default, so every roof-into-tower junction gets it.
2. **`junctions.roof_tower_flashing`, flaunching legibility.** This is `V4J_roof_tower_fillet` along the 79° roof/drum
   line, z 2.46–3.54. See j03, k03, k10 and m04.
   - What is wrong: the 2.5 cm lift buries the fillet under the chunky shingle butts. At mid-shot and from the crane
     the shingles seem to run straight into the stone, which reads as clipping, not a flashed joint.
   - What it should be: a junction section that reads at 10 m. Either:
     - a mortar fillet at least 8 cm up the stone face and at least 8 cm out over the shingles, riding over the butt
       peaks (lift of 5 cm or more at the peaks); or
     - the stepped lead-flashing option (`mortar_only=False`) with a cover flashing 12–15 cm up the face.
   - This is the junction's silhouette, not surface detail.
3. **Build time: `compound.build_compound` cull and `core.visibility_cull`.**
   - What is wrong: the full build takes about 30 min (15 targets × about 580–660 viewpoints), against the art
     bible §8 limit of about 10 min on 4 shared cores. When a spawn worker dies (MemoryError), the cull hangs
     instead of failing.
   - What it should be: a full build of 10 min or less with `est_hidden_pct` still at or below 15 %. Possible
     routes:
     - re-cull only targets within about 1 m of a junction or a neighbour wing, and reuse each wing's own cull from
       its build at the origin;
     - dedupe the wings' rings to about 250 viewpoints in total.
   - `visibility_cull` must detect a dead worker and fall back to serial instead of hanging.
4. **`conical_roof.build_eave_closure` → `V4H_eave_closure`, z 2.78–3.35 round the house wall head.**
   - What is wrong: it is a single-sided band, with all 478 faces pointing into the hut. It is seen from outside
     under the eave between the rafter feet, and it disappears there with a one-sided material in Unreal (art bible
     §8: no single-sided planes where seen).
   - What it should be: a closed band at least 3 cm thick (inner face, outer face and top and bottom caps), in the
     kit module. Re-run the hut hero to confirm the triangle count change.

**Nice-to-have (not blocking)**
- Distinctness: push the wings further from the presets, or swap in a keep-family module so the keep family
  contributes more than a finial, a fillet and two posts. Examples: the keep's thatch on the house, an octagonal
  skirt, a lean-to annex between house and mill. The mill-house should not read as the hero hut against the small
  hero mill.
- A window module for a round daub wall. The house is blind (the builder noted the gap).
- Mill door: about 1.2 m from the house wall in the re-entrant corner. Consider about −60° azimuth on the drum for
  room in the shot, or an inner connecting door between house and mill.
- Mill interior floor: 16 of 5,616 doorway rays slip through gaps between the `V4M_interior` floor pieces at
  r 0.6–1.45 m (they would show the terrain). Add a cheap backing slab just under the floor.
- House roof: one pinhole near (−0.2, 2.2, 3.7) at the drum side is visible only from inside the house (j06). No
  ray through the doorway reaches it. Extend `V4H_roof_blocker` to the drum face.
- `tower_of` adapters for other round bodies (the keep turret, `stone_body`), as the builder noted, so the
  junctions are not drum-only.
- After fix 3, build twice and compare geometry hashes. The director did not re-verify determinism this round.

## v4_mixed round 2 — builder entry

All four must-fixes were made at module level (`components/junctions`, `compound`, `conical_roof`, `core`). The
recipe changed only in its junction parameters, which now use the kit defaults, and in two cull keys. It is 93
non-blank, non-comment lines with no geometry code. Kit changes are recorded in `kit/changes/v4_mixed.md`
(round 2 section).

**Must-fix 1: roof/drum eave ends (`junctions.roof_tower_flashing(ledger=True, trim=True)`, now the default).**
- New `clip_at_tower` / `trim_wing_at_tower` / `ROOF_TRIM_PARTS`. Every structural part and the roofing of the roof
  wing is TRIMMED at the drum face R(z), not buried:
  - rafters, battens, purlin rings, wall plate, eave closure, blocker, starter, shingles and under-laps;
  - insets of 2-3.5 cm, so each cut end sits just inside the stone face.
  - Crossing edges are split exactly on the curved surface (bisection on the true field), and UV and `Mask` are
    interpolated.
  - Probe on the delivered `.blend`: rafters and battens now reach at most 2.9 cm into the drum (r1: battens
    0.64 m), the starter 3.8 cm and the shingles 4.5 cm (r1: 0.41 m). The eave closure stops 2 cm short of the face.
- New `pole_plate_ledger`. The cut rafter feet bear on a keep-family `hewn_square` pole-plate:
  - 0.15 × 0.20 m, in 4 straight lengths (3.0 m in all, z 2.26-3.01);
  - it follows the traced roof line under the rafter feet (drop = shingle stack + batten + rafter / cos(pitch));
  - its back is let 3 cm into the masonry;
  - it is scarfed over 3 corbels that are linked duplicates of the drum wing's own pooled corbel meshes
    (`V4J_roof_tower_ledger`, `V4J_roof_tower_corbel_001-003`).
- The lead end-aprons are larger (0.20 m wide, 0.24 m drop), so the starter course and the eave closure end under
  them.

**Must-fix 2: flaunching legibility (new `junctions.ride_fillet`, `section="ride"`, the default).**
- The r1 fillet used the keep's thatch section, which assumes the roof falls AWAY from the wall. Here the house cone
  RISES away from the drum (a 39° valley on the upslope side), so the 8 cm toe sat about 10 cm under the shingles.
- The new section is fitted per station by ray casts along the drum normal (1, 3.5, 6.6, 11 and 13 cm out):
  - the back is buried 3.5 cm;
  - the hard crease is 10 cm up the stone over the highest roofing at the face;
  - a cove runs out to a toe 11 cm out, 5 cm over the highest butt peak there, so the mortar edge stands proud;
  - the skirt drops 3 cm into the course;
  - both ends taper over 0.3 m.
- In `builder_extra/k03`, `k10` and `m04` it reads as a continuous mortar band along the whole roof/drum line.

**Must-fix 3: build time and the hanging cull.**
- `compound_views(max_views)` with the new `dedupe_views`:
  - the wings' overlapping rings are thinned, with priority review cameras > door views (all 72 kept) > near rings >
    far and crane rings;
  - 588 ring / door / camera viewpoints -> 222, plus the 77 review viewpoints = 299 in total (r1: 665).
- `compound_cull` runs 4 spawn workers for this cull only (`cull_procs=4`).
- The roof parts trimmed inside the drum no longer enter the cull.
- Result: the full build took **625 s (10.4 min)**. The cull itself ran from 46 s to 623 s. The r1 build took about
  1,990 s.
  - That 625 s was measured while the three hero re-runs and another agent's builds shared the CPU, so an
    uncontended build should come in under 10 min.
  - `V4M_base_stones` (180k polygons, -37,101) is the largest single target at about 190 s.
  - `cull_max_views` (kit default 260) is the knob if more margin is needed.
- `est_hidden_pct` is 12.6 % (r1: 13.5 %). The thinner viewpoint set culls slightly more: -105,904 polygons
  (r1: -99,224).
- **Dead worker.** The core's `ProcessPoolExecutor` / `BrokenProcessPool` path (CHANGELOG) still HUNG in my first
  r2 build:
  - with 4 workers, the executor started one worker lazily, after the pre-bpy `sys.path` had been restored;
  - that worker died importing the build script (`No module named '_bpy'`), and the executor never noticed.
  - Fix in `core.visibility_cull`, behaviour-identical for every building:
    - new `_vis_map_watched` submits the tasks with the pre-bpy path in place, so late workers start correctly;
    - every 5 s it checks the worker processes, and a dead one raises, so the rest of the cull falls back to one
      process instead of hanging;
    - at the end, the workers are stopped instead of joined.

**Must-fix 4: `conical_roof.build_eave_closure(thickness=0.03)`, now the default.**
- A CLOSED band: the face at r_b now faces OUT, an inner face 3 cm in faces the hut, and top, bottom and end caps
  close it. The inner top rises with the pitch, so it is buried in the shingle stack as deep as the outer top.
- `thickness=0` reproduces the old band.
- Probe on the delivered `V4H_eave_closure`: 1,438 faces (717 outward, including the up-and-out top caps; 478
  inward; 243 caps), 0 non-manifold edges.
- The hut hero was re-run (table below).

**Stats** (`renders/variants/v4_mixed/round_02/stats.json`):

| Measure | Value |
|---|---|
| Triangles | 1,382,693 |
| est_hidden_pct | 12.6 % |
| Material slots | 12, all from the palette |
| `mask_attribute_missing` | none |
| Objects | 289 (r1: 285; + ledger, 3 corbels) |
| Bounding box | unchanged: 11.45 × 9.64 × 14.04 m |
| `.blend` | 31.5 MB, compressed |
| Decal anchors | 120 (191 placed, 19 dropped by the whole-building audit, 52 thinned) |

**Renders.** `renders/variants/v4_mixed/round_02/`: all six views at 24 samples, inspected.
- No holes or see-through, and the silhouette is unchanged. No blocking problems were found, so no post-render
  fixes were made.
- Junction close-ups (the director's r1 framings, plus red-sky checks) are in `round_02/builder_extra/`.

**Determinism.** A second full build to scratch (with the last `core` edit) gave an identical geometry hash
(SHA-1 over every object's name, vertices and matrix: `c8eca347...`) and 1,382,693 triangles. It took 670 s, also
under contention: three other builds were running.

**Hero re-runs** (to scratch via `HUT_OUT` / `MILL_OUT` / `KEEP_OUT`):

| Hero | Triangles | Record | Change |
|---|---|---|---|
| wattle_roundhut | 878,355 | 876,619 | +1,736 (+0.20 %): the closed eave closure, as the director asked |
| tower_windmill | 1,146,243 | 1,146,243 | exact (clearance PASS) |
| hilltop_keep | 1,166,874 | 1,166,874 | exact |

- The hut run started before both `core` edits.
- The mill and keep runs used the watched-map `core` but started before the last edit (stop the workers instead of
  joining them).
- Both `core` edits change only how the worker pool is managed; the cull results are the same.

**Known gaps.**
- From eye level under the eave (m01, m02, k06, k07), the eave-stub rafters still meet the drum at oblique angles.
  They now stop at the face, over the ledger, but that corner is still busy. A future `jack_rafters` option could
  replace the stubs that land on a tower with rafters set square to the ledger.
- The build time of 10.4 min is borderline because it was measured under contention.
- Not addressed this round (nice-to-haves): the round-wall window module, the mill door position, the mill
  interior floor slab, and `tower_of` adapters for non-drum towers.

## v4_mixed round 2 — score 8.4/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v4_mixed/round_02/`, plus `stats.json`, `hidden.json`,
  `buildings/variants/v4_mixed/decal_anchors.json` (120 anchors) and all 14 builder close-ups in `builder_extra/`.
- The recipe, `kit/changes/v4_mixed.md` (round 2 section), and the new kit code: `junctions.tower_field`,
  `clip_at_tower`, `trim_wing_at_tower` / `ROOF_TRIM_PARTS`, `ride_fillet`, `pole_plate_ledger`, the new
  `roof_tower_flashing` defaults, `compound.dedupe_views` / `compound_views` / `compound_cull`, and
  `core._vis_pre_bpy_path` / `_vis_map_watched`.
- 24 director close-ups of every module junction (roof/drum both eave ends from outside, from actor eye level and
  looking up under the eave; flaunching from crane, mid-shot front and back; wall/drum; plinth/footing; house eave
  closure; apex/cone; both doors; drum/apron/smock; cap/tail boom; wheel hub/cap; band over roof) and 18 black-on-red
  see-through checks, in `renders/variants/v4_mixed/round_02/director_extra/` (d01–d24). d10 and d11 are badly
  framed (camera under the house eave / at the house door) and add nothing; the other 22 are informative.
- Ray probes on the delivered `.blend`: penetration into the drum, manifold checks on every junction object and the
  eave closure, anchor-to-surface distance, transforms and UVs, sky rays through the junction zone from 9 exterior
  cameras and from under both eave ends, and rays through the mill doorway.

**Recipe and kit check (director-verified).** The recipe still imports only kit modules and holds no geometry code
(two `Wing`s, two junction steps, 93 lines). Every round 2 fix is in a kit module and on by default, so any roof
that meets a round tower gets it: the trim (`clip_at_tower` works on any placed single-user mesh and any tower
field), the fitted fillet, the ledger (keep-family `hewn_square`, corbels as linked duplicates of the tower wing's
own pooled corbel meshes) and the closed eave closure (`conical_roof.build_eave_closure(thickness=0.03)`, hut hero
re-run, +1,736 tris). The dead-worker watchdog in `core.visibility_cull` is real: a dead worker raises, the target
falls back to one process with the same chunks, and the pool is stopped at the end.

**Probe results.**
- Trim works: house parts now reach at most 2.9 cm (rafters, battens), 3.8 cm (starter) and 4.5 cm (shingles) into
  the drum (r1: 0.64 m / 0.41 m). Only stone-into-stone (plinth 0.39 m), the daub wall under the abutment posts
  (0.15 m) and buried backs of the fillet / ledger / pointing (≤ 7 cm) go deeper — all covered.
- No see-through: junction-zone sky rays 0–1 of 348 per camera (the 1s are true sky past the cone), 0 sky rays from
  under either eave end; all 18 red checks show only true sky.
- `V4H_eave_closure`: 1,438 faces, 0 non-manifold edges, 0 degenerate (must-fix 4 confirmed).
  `V4J_roof_tower_ledger`, `_abutment_posts`, `_abutment_pointing`: 0 non-manifold edges.
- `V4J_roof_tower_fillet`: 28 non-manifold edges (20 boundary, 8 shared by three faces), all on `M_lead` at
  z 2.38–2.42 m — the drip lips of the two end aprons (`junctions.end_apron`) are open folded strips welded onto
  the plate edge. The corbels' 60 open edges are their culled backs in the masonry (note 6, fine).
- Ledger: 3.0 m in 4 lengths at z 2.19–3.12, 408 of 544 vertices outside the house wall line (it sits under the
  eave overhang). The three corbels sit at the inner joints and are 100 % hidden in `hidden.json`; the only visible
  parts of the ledger are its two ends under the eave (d01, d03, d05, d12).
- 120 anchors, all within 5 cm of a surface, placement unchanged and plausible. Every single-user mesh has an
  identity transform and a UV map. 12 palette slots, `Mask` everywhere, 12.6 % hidden.
- Mill doorway: 42 of 5,184 rays reach the terrain through gaps in `V4M_interior` (r1: 16 of 5,616).

**What the renders show.**
- Flaunching (d07, d08, d09, d24; builder k03, k10, k11, m04): now a continuous, legible mortar band riding over the
  shingle butts along the whole roof/drum line, with a clear crease on the stone. From mid-shot and crane height the
  roof no longer reads as running into the rubble. Must-fix 2 is done.
- Eave ends (d01–d06; builder m01, m02, k06, k07): from outside (d01, d02) the eave dies cleanly into the drum under
  the lead apron and the fillet's tapered end. From actor eye level looking up into the corner (d03, d05) the cut
  rafter stubs, battens and ring purlin still converge at oblique angles over the sloping ledger end — tidy and
  stopped at the face, but busy (the builder's own known gap). No longer anything stabbed into the stone. Must-fix 1
  is done.
- Wall/drum (d12, d13), plinth/footing (d14, d15), apex (d18), doors (d19, d20), apron/smock (d21), cap/boom (d22)
  and wheel hub (d23) are unchanged from round 1 and clean.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.4 | Unchanged and right: a tall-coned daub roundhouse against a slim battered stone tower mill with shake apron, smock tower, cap, 12-blade fan wheel and tail vane. Reads as one believable mill-house of this village in hero, front, back and aerial. |
| 2 Proportion and actor scale | 8.6 | Unchanged: house door 0.97 × 2.10 m clear, eave over the door about 2.5 m, mill door 1.0 m wide with the head at 2.26 m, 51° cone, 7.9 m to the house finial, 14 m overall. The mill door still sits tight in the re-entrant corner. |
| 3 Construction logic | 8.4 | The roof now stops at the drum and its cut rafter feet bear on a hewn ledger on pooled corbels; the eave closure is a real 3 cm band. Remaining: the corbels sit at the hidden inner joints, so the two visible ledger ends under the eave show no bearing, and the oblique rafter stubs over them make the corner busy from eye level. |
| 4 Seams and junctions | 8.4 | Every junction is closed, flashed or covered; no see-through anywhere (0 sky rays, 18 clean red checks); the flaunching now reads as a mortar band at 10 m; nothing runs on into the stone. Points off for the busy eave-end corner at actor eye level and the open lead apron lips. |
| 5 Distinctness and reuse | 8.3 | Reuse is now excellent: three more generic junction modules (`clip_at_tower`, `ride_fillet`, `pole_plate_ledger`) on by default, and the keep family adds the ledger. Distinctness is unchanged: the two wings are still close to the hut and small-mill presets, so it reads as the hero hut parked against the small hero mill. |
| 6 Technical compliance | 8.3 | Budget, hidden 12.6 %, palette, `Mask`, pooling, anchors, transforms, UVs all pass; two builds hash-identical; the watchdog removes the hang. Points off: the build is 625 s and 670 s (art bible §8: about 10 min) while the recipe overrides `cull_max_views` to 300, above the kit default 260; and the end aprons' lead lips are open, non-manifold pieces (note 1). |

**Verdict: 8.4/10, PASSED (pass mark 8.2).** All four round-1 must-fixes are fixed in kit modules and on by
default, not in the recipe, which is exactly the note-12 behaviour: the next roof that runs into a round tower gets
the trim, the fitted flaunching, the ledger and the closed eave closure for free. The junction now reads as built
from crane, mid-shot and eye level, with no see-through. What keeps it from higher is distinctness (still the hero
hut beside the small hero mill) and two small module-level loose ends listed below.

**Strengths**
- `junctions.clip_at_tower` is a general, exact trim: any placed single-user mesh, any round tower field, edges
  bisected on the true curved surface, UV and `Mask` interpolated. Battens went from 0.64 m into the drum to 2.9 cm.
- `junctions.ride_fillet` fits its section to the roofing by ray casts, so it works where a roof rises away from the
  tower (the case the keep's fillet could not handle) and reads as a continuous mortar band at 10 m.
- `junctions.pole_plate_ledger` is a real cross-family module: keep-family `hewn_square` lengths on corbels that are
  linked duplicates of the tower wing's own pooled corbel meshes.
- `conical_roof.build_eave_closure(thickness=0.03)` is closed (0 non-manifold edges), with `thickness=0` for the
  old band and the hut hero re-run.
- Build time went from about 1,990 s to 625 s (viewpoint dedupe 665 → 299, door views kept, 4 workers) with
  hidden still 12.6 %, and the dead-worker hang is fixed in `core`. Two builds gave identical geometry hashes.
- The recipe is still a 93-line declarative recipe with no geometry code.

**Must-fix (round 3)**
1. **`junctions.end_apron` → `V4J_roof_tower_fillet`, the lead end-aprons at both eave ends (z 2.38–2.42 m,
   front about (1.0, −0.3), back about (0.9, 2.3)).**
   - What is wrong: the drip lip is an open folded strip (`lip` quads, no end caps) welded onto the plate's bottom
     edge: 28 non-manifold edges on `M_lead` (20 boundary, 8 shared by three faces). These are seen from under the
     eave at actor eye level. Producer note 1 asks for closed pieces.
   - What it should be: the lip as a closed piece with its own vertices (top, bottom and both end caps), or the plate
     and lip as one closed bent sheet; 0 non-manifold edges on the `M_lead` parts of the fillet object, in the kit
     module so every roof/tower junction inherits it.
2. **Build time: the recipe `build_v4_mixed.py`, `build_compound(... cull_max_views=300 ...)`.**
   - What is wrong: the recipe overrides the kit default (260) upward, and the measured builds are 625 s and 670 s,
     over art bible §8's "about 10 minutes".
   - What it should be: drop the override (use the kit default 260, or lower) and log one full build of 600 s or
     less with `est_hidden_pct` still at or below 15 %.

**Nice-to-have (not blocking)**
- `junctions.pole_plate_ledger`: put the corbels where they can be seen. Today all three sit at the inner joints and
  are 100 % hidden, while the two visible ledger ends under the eave show no bearing. Place one corbel under each
  visible end (within about 0.3 m of the eave end) and fewer at the hidden joints.
- The builder's proposed `jack_rafters` option: set the rafters that land on a tower square to the ledger, so the
  eave-end corner reads calmer from actor eye level (d03, d05).
- Distinctness (carried from round 1): push the wings off the presets, or swap in a keep-family module (thatch on
  the house, an octagonal skirt, a lean-to annex between house and mill), so it no longer reads as the hero hut
  against the small hero mill.
- A window module for a round daub wall (the house is still blind).
- Mill interior floor: 42 of 5,184 doorway rays now reach the terrain through gaps in `V4M_interior`; add a cheap
  backing slab just under the floor.
- Mill door position in the re-entrant corner (about 1.2 m from the house wall), and `tower_of` adapters for other
  round bodies (keep turret, `stone_body`), as in round 1.

## v4_mixed round 3 — builder entry

Every fix is in a kit module (`components/junctions.py`, new functions and new optional parameters only) or in the
recipe's parameters. The recipe holds no geometry code: two `Wing`s, two junction steps, 94 non-blank, non-comment
lines. Kit changes are in `kit/changes/v4_mixed.md` (round 3 section).

**Audit issue 1: the roof-to-tower ledger (`junctions.rafter_bearings`, new; `roof_tower_flashing(bearing="corbels")`,
now the default).**
- The sloping `pole_plate_ledger` is no longer used by default (`bearing="ledger"` keeps it, unchanged).
- New `rafter_feet`: it finds each rafter's cut foot on the trimmed rafter object (the vertices on the cut surface,
  clustered per rafter).
- New `rafter_bearings`: a STEPPED bearing, one LEVEL keep-family `hewn_square` pad (0.40 x 0.15 x 0.11 m, back
  3 cm in the masonry) per rafter foot, its top at the rafter's underside at the stone face, on a pooled drum corbel
  under its middle. Every visible end has a corbel under it and nothing slopes.
- A foot whose pad would reach the roof wing's wall head gets nothing, because the wall plate carries it. The wall
  head is the outer radius of the wing's own `wall_plate` and `eave_closure`, and the abutment-post faces, plus 5 cm.
  So by construction no bearing can pass through the plate, the eave closure or the posts.
- On this building (with the smaller house below) only 2 rafters reach the drum, and both land within the wall
  head, on the house's own trimmed wall plate. So no pad or corbel is placed (`V4J_roof_tower_pads` is empty and not
  built), and nothing hangs under the eave any more.
- The r2 problem is gone: there is no beam outside the wall line and no member under the eave line at either run
  end. A BVH overlap test of every `V4J_` part against `V4H_wall_plate`, `_eave_closure`, `_rafters`, `_battens`,
  `_roof_starter`, `_roof_shingles`, `_daub` and the posts finds only the designed contacts: abutment posts against
  the daub they are set into (279 pairs), and against the plate that sits 1 cm on their heads (24 pairs).
- See `round_03/actor_closeup.png`: the eave runs cleanly into the drum beside the mill door.

**Audit issue 2a / director must-fix 1: `junctions.end_apron(closed_lip=True)`, passed by
`roof_tower_flashing(apron_closed=True)`.**
- The drip lip is a closed bent strip with its own vertices: a four-sided section swept along the edge, with both
  end caps. Its root is tucked 3 mm up into the plate's bottom edge, not welded onto it.
- Probe on the delivered `.blend`: `V4J_roof_tower_fillet` (1,232 faces, mortar + lead) has **0 non-manifold
  edges** (r2: 28 on `M_lead`). `V4J_abutment_posts` and `V4J_abutment_pointing` also have 0.

**Audit issue 2b / director must-fix 2: build time.**
- The `cull_max_views=300` override is dropped.
- A first full build at the kit default (260) took **609 s**. Part of that time overlapped a short probe run.
- The recipe now sets `cull_max_views=230`, below the default, as the brief allows: 592 ring / door / camera
  viewpoints thinned to 153, plus 77 review viewpoints.
- Logged full build (uncontended): **462 s (7.7 min)**, 1,385,232 triangles, `est_hidden_pct` **12.2 %**.

**Audit issue 3: distinctness. Both wings are pushed off their presets (recipe parameters only, the same kit
modules).**

| | r2 | r3 | Hero / preset |
|---|---|---|---|
| House plan (wall line) | r 2.85 m | **r 2.55 m** | hut 3.50; hut variant 2.90 |
| House cone | 51 deg, eave lip 2.45 m, overhang 0.55 m | **58 deg needle cone**, eave lip 2.40 m, overhang 0.60 m | 51 deg on both |
| House cone apex | ~6.7 m | ~7.4 m on a 6.3 m eave diameter | hut 8.6 m on 8.3 m |
| Mill drum | 5.30 m, r 1.95 -> 1.82 | **5.50 m, r 2.05 -> 1.70 (strong batter)** | mill 4.62 m, 2.60 -> 2.45; mill variant 4.20 m, 2.00 -> 1.88 |
| Fan wheel | 12 blades | **16 blades** (ref1) on the small mill's 3.05 m tip radius | mill 16 on 3.90 m; mill variant 12 on 3.40 m |

- The house is now a tall, narrow miller's cottage with a steep needle cone: height over width is about 1.3, against
  about 1.0 for the hut. The mill is a tall, tapering stone tower, and its apron, smock, cap and boom ride 0.2 m
  higher.
- Placement is recomputed from the radii: the centres are 4.43 m apart on the same 15 deg line, so the daub wall
  still runs 0.09 m into the drum. The band and arcade are lifted to clear the steeper cone: band 3.80-4.17 m,
  arcade sill 4.17 m. The roof/drum line now runs z 2.58-3.46.
- I did not add a keep-family body module (lean-to, thatch, octagonal skirt). There was not enough time to
  integrate a `tier_frame` / `oct_frame` body into `compound` in this round. That is the next distinctness step.

**Stats** (`renders/variants/v4_mixed/round_03/stats.json`):

| Measure | Value |
|---|---|
| Triangles | 1,385,232 |
| est_hidden_pct | 12.2 % |
| Material slots | 12, all from the palette |
| `mask_attribute_missing` | none |
| Objects | 277 (r2: 289; the ledger and its 3 corbels are gone, and the house has fewer posts) |
| Bounding box | 10.91 x 9.28 x 14.21 m |
| `.blend` | 31.9 MB, compressed |
| Decal anchors | 120 (191 placed, whole-building audit and thinning to 120) |

**Renders.** `renders/variants/v4_mixed/round_03/`: all six views at 24 samples, inspected.
- No holes or see-through, and the silhouette is clean.
- The eave/drum corner at the mill door is clean (actor_closeup).
- No blocking problem was found, so no post-render fixes were made.

**Hero re-runs** (`junctions.py` is an existing kit module, although no hero imports it), to scratch via
`KEEP_OUT` / `HUT_OUT` / `MILL_OUT`:

| Hero | Triangles | Record | Change |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 | exact |
| wattle_roundhut | 878,355 | 878,355 (r2 accepted; 876,619 before the closed eave closure) | exact |
| tower_windmill | 1,146,243 | 1,146,243 | exact |

**Known gaps.**
- The new bearing module is proven by probe but not exercised on this building: no rafter lands on the drum outside
  the wall head. A roof wing with a deeper overhang against a tower would show the pads and corbels.
- `cull_max_views` 230 is a recipe override, downward.
- `V4J_abutment_pointing` is estimated 100 % hidden (buried in the daub / stone seam) and could be dropped or culled.
- The round-wall window module, the mill interior floor slab and `tower_of` adapters for non-drum towers are still
  open (nice-to-haves).

## v4_mixed round 3 — score 7.9/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v4_mixed/round_03/`, plus `stats.json`, `hidden.json` and
  `buildings/variants/v4_mixed/decal_anchors.json` (120 anchors).
- The recipe (94 lines), `kit/changes/v4_mixed.md` (round 3 section) and the new kit code in `components/junctions.py`:
  `rafter_feet`, `rafter_bearings`, `_world_co`, `end_apron(closed_lip=True)` and the new `roof_tower_flashing`
  defaults (`bearing="corbels"`, `apron_closed=True`). Also `compound.compound_views` (viewpoint thinning).
- Director close-ups of every module junction in `renders/variants/v4_mixed/round_03/director_extra/`, rendered with
  `dir_render_r03.py`:
  - roof/drum: both eave ends from outside, close and looking up (r01, r02b, r03–r06), and the flaunching from crane,
    mid-shot and above (r07, r08, r09b, r10–r13);
  - wall/drum, post head and plinth/footing (w01b, w02, w03b, w04, w05b);
  - the house wall head under the eave at 4 m (h01–h04, a07);
  - apex, both doors, apron/smock, cap/boom, wheel hub (a01–a06), and the thumbnail and overview (t01, t02);
  - 18 black-on-red see-through checks (`*_seethrough_red.png`).
  - Badly framed and ignored: r02 and w05 (camera inside the house wall), w01, w03 and i01 (blocked by the door
    frame or door leaf). The b-versions replace them.
- Ray probes on the delivered `.blend` (`dir_probe_r03.py` and `dir_probe2…6_r03.py`):
  - junction hygiene (non-manifold and degenerate faces);
  - how far house parts reach into the drum;
  - rafter feet against the wall plate;
  - the eave height over the house door;
  - fillet clearance against the band;
  - see-through rays toward the fillet from 8 cameras;
  - back-face rays at the house wall head from 4 m and 6 m eye-level rings;
  - boundary edges at the wall head;
  - transforms, UVs, `Mask` and anchor distances.
- A director test build to scratch (`V4_FAST`, house overhang 1.10 m, recipe otherwise unchanged) to check that
  `rafter_bearings` really places a bearing when a rafter lands on the drum outside the wall head (x01, x02).

**Recipe and kit check (director-verified).** The recipe still imports only kit modules and holds no geometry code:
two `Wing`s and two junction steps. The round-3 distinctness changes are parameter changes only. The bearing and the
closed lip are new kit functions and new optional parameters in `junctions.py`, on by default, so every roof/tower
junction gets them. The heroes do not import `junctions.py`, and their re-runs match exactly.

**Probe results.**
- `V4J_roof_tower_fillet` (1,232 faces), `V4J_abutment_posts`, `V4J_abutment_pointing` and `V4H_eave_closure` have
  0 non-manifold and 0 degenerate faces. Round-2 must-fix 1 is done.
- No pads or corbels are placed on this building: the sloping ledger is gone. The rafter feet cut at the drum lie at
  r 2.61–2.77 m from the house centre (z 2.81–3.16). The wall plate runs from r 2.47 to 2.66 m with its top at
  z 2.97. So these rafters cross the plate at their own azimuth (outside the drum there) before their tails die
  into the stone. They are carried.
- The director's scratch test with a 1.10 m overhang logged "3 rafter feet at the tower face, 1 level pads on
  corbels (z 2.47), 2 carried by the wall plate". In x01 and x02 the pad sits level on a pooled drum corbel under the
  rafter. The module works and is reusable.
- Trim still holds:
  - rafters, battens, starter and shingles reach at most 4–6 cm into the drum;
  - the daub reaches 7.9 cm in, under the abutment posts;
  - plinth into footing is stone into stone.
  - One house wall post (`V4H_posts`, house az about 5°, x 1.12–1.21, y 0.40–0.51) runs 0.20 m into the drum.
    It is visible only from inside the house.
- No see-through at the roof/drum junction:
  - rays aimed at fillet points: 0 of 178 escape from 7 of 8 cameras, and 1 of 178 from the 8th;
  - every red check of the junction shows only true sky.
- The fillet's top crease (z 3.83 at about (1.18, 0.76)) runs 3 cm into the lower string course of the drum's band
  (`V4M_base_dressed`, bottom edge z 3.80): 11 overlapping face pairs. This is visible only from crane height, down
  the valley (r12, r13).
- **House wall head (new finding).** On the west side the cull has opened holes in `V4H_daub` (and the outer faces of
  `V4H_wall_plate`) at z 2.45–2.95, under the eave.
  - Eye-level probe from 4 m from the house centre: at house azimuth 135–225°, 43–111 of 825 rays per camera hit a
    back face (`V4H_wall_plate`, `V4H_daub_interior`).
  - From 6 m it drops to 0–2 rays, and at the front and the drum side to 0–6 rays.
  - `V4H_daub` has 427–576 boundary edges above z 2.3 in the west sectors, against 70–280 elsewhere.
  - In h01–h04 and a07 these show as blocky black voids along the top of the daub. They do not reach the sky,
    because the closed cavity behind is dark. In Unreal the one-sided back faces disappear, so these are holes into
    the house.
  - The cause: the 58° cone on a 0.60 m overhang drops the eave lip (2.40 m) about 0.4 m below the wall head
    (plate 2.76–2.97). That band of wall is then seen only from close, low viewpoints. The recipe's lowered
    `cull_max_views=230` thins exactly those near-ring viewpoints away (`compound_views` dedupes the near rings).
  - The six review cameras do not look at the west wall from close range, which is why the builder's "no holes"
    check missed it.
- Eave lip over the house door: 2.42–2.45 m (≥ 2.30). The framed door's head beam is at about 2.28 m, just under it.
  Door openings are unchanged (house 0.97 × 2.10 m clear; mill 1.0 m wide, head at 2.26 m).
- Every mesh has an identity transform (single-user), a UV map and `Mask`. 120 anchors, all within 5 mm of a surface,
  with plausible types and heights. 12 palette slots, 12.2 % hidden, 1,385,232 tris.
- The logged 462 s build was not re-timed and determinism was not re-hashed this round. Both are taken from the
  builder's log.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.6 | Now its own building at thumbnail (t01, front, back): a narrow miller's cottage under a 58° needle cone leaning on a tall, strongly battered stone tower with apron, smock, cap, 16-blade wheel and tail. This style of steep cone is in the concept art (ref3 aerial). It no longer reads as the hero hut parked against the small mill. |
| 2 Proportion and actor scale | 8.5 | Doors are right next to the 1.8 m figure, and the eave lip over the house door is 2.42–2.45 m. The cone is about 2× the visible wall height. Points off: the framed door head sits only about 0.15 m under the eave lip, and the mill door is still tight in the re-entrant corner. |
| 3 Construction logic | 8.4 | The sloping ledger is gone. The rafter tails cross the house plate and then die into the drum, and the new stepped bearing provably places a level pad on a corbel when a rafter lands outside the wall head (director test x01, x02). Points off: the fillet crease runs 3 cm into the band's lower string course, so the band seems to sit on the roof from the crane (r12). One house post is buried 0.20 m in the drum (seen only from inside). |
| 4 Seams and junctions | 7.6 | Roof/drum is now right: closed lead aprons with 0 non-manifold edges, a legible fillet, eave ends clean from outside and from under the eave, no see-through. Wall/drum and plinth/footing are clean. But the roof-to-wall junction of the house wing is open on the west side: cull holes along the wall head under the eave, at actor eye level from 4 m (h01–h04, a07). |
| 5 Distinctness and reuse | 8.5 | Pushed off the presets by parameters alone, and it reads as a new building type. The recipe is still 94 lines of kit calls. Three new generic functions are on by default, and the heroes re-run exactly. The keep family still adds only the finial, posts and fillet (the pads do not appear on this building), and the 16-blade wheel moves the mill back toward the hero. |
| 6 Technical compliance | 7.7 | Budget, palette, `Mask`, pooling, transforms, UVs and anchors pass, hidden is 12.2 %, and the logged build is 462 s. Points off: producer note 6 ("never open holes when culling") is broken at the house wall head. That is a side effect of the recipe lowering `cull_max_views` to 230 so the build stays under §8's limit. |

**Verdict: 7.9/10, NOT PASSED (pass mark 8.2).**
- **Fixed at kit level, on by default:**
  - both round-2 must-fixes (the closed apron lips and the build time);
  - the sloping ledger, replaced by a reusable stepped bearing that the director verified in a test build.
- **Distinctness has moved on:** this is now clearly its own building.
- **What fails the round** is a new, visible defect: the thinned cull opened holes along the house wall head, at eye
  level on the west side. Every other compound building that uses the same viewpoint thinning will inherit it. This
  is a producer-note-6 must-fix and a seam defect.
- **The fix is one module-level change** (below). Everything else is close to passing.

**Strengths**
- `junctions.rafter_bearings` / `rafter_feet` replace the sloping ledger with a generic stepped bearing: one level
  keep-family pad on a pooled corbel per rafter foot outside the wall head, and nothing for feet the plate carries.
  On this building, by construction, nothing hangs under the eave. With a deeper overhang it places the pad
  correctly (x01, x02).
- `junctions.end_apron(closed_lip=True)` is a closed swept lip with end caps. The fillet object went from 28 to 0
  non-manifold edges, and every roof/tower junction inherits it.
- The roof/drum junction now reads as built from every distance: aprons over the cut eave lips (r03, r06), the
  fillet band from mid-shot and crane (r08, r10), calm eave ends from under the eave (r02b, r04, w05b), and no
  see-through.
- Distinctness through parameters alone (r 2.55, 58°, 0.60 m overhang; 5.5 m drum battered from 2.05 to 1.70 m;
  16 blades) gives a new silhouette from the same modules. This is the note-12 workflow working as intended.
- Technically clean otherwise: 1,385,232 tris, 12.2 % hidden, 12 palette slots, `Mask`, identity transforms, UVs,
  120 anchors within 5 mm. The hero re-runs are exact.

**Must-fix (round 4)**
1. **Cull holes at the house wall head. Module: `compound.compound_views` / `compound_cull` (with the recipe's
   `cull_max_views=230`). Target: `V4H_daub` and the outer faces of `V4H_wall_plate`, z 2.45–2.95, house azimuth
   135–225° (west side, world about x −4.1…−3.6, y −1.0…+1.6). See h01–h04 and a07.**
   - What is wrong: the cull deleted visible faces of the daub skin and the plate along the wall head under the eave.
     From 4 m at eye level you see blocky voids into the dark daub cavity: 43–111 of 825 rays per camera hit back
     faces (probe 5). In Unreal these are holes into the house. This breaks producer note 6 ("never open holes when
     culling") on an eye-level wall (note 4).
   - What it should be: 0 back-face hits from the 4 m and 6 m eye-level rings round every wing (re-run
     `dir_probe5_r03.py`), with the build still ≤ 600 s and hidden ≤ 15 %. Make the fix in the kit, so every
     compound building inherits it:
     - `compound_views` keeps each wing's near eye-level ring complete (all `ring_n` stations at r + 0.4 m and
       r + 1.5 m, z 1.0 and 1.65), undeduped in the `head` group like the door views. Thin only the far and crane
       rings to meet `max_views`.
     - And/or the RoundFrame cull targets protect the wall-head band from the eave lip up to the plate top (here
       z 2.40–2.97) whenever the eave lip lies below the wall head, as on any steep cone with a short overhang.

**Nice-to-have (not blocking)**
- `junctions.roof_tower_flashing` / `ride_fillet`: read the tower's band zones (`T` / `DrumFrame` zones) and keep the
  fillet crease at least 5 cm under the lowest string course. Today the crease is at z 3.83, against the band bottom
  at 3.80. Or raise this recipe's band to z ≥ 3.95. See r12 and r13.
- `junctions.wall_tower_abutment`: trim (`clip_at_tower`) or drop house wall posts that fall inside the tower.
  `V4H_posts` at house az about 5° runs 0.20 m into the drum (seen only from inside the house).
- `junctions.rafter_bearings`: set a sensible default `end_clear` (about 0.25 m), so that a pad cannot sit
  directly under a lead end-apron when the overhang is deep (x01).
- `V4J_abutment_pointing` is 100 % hidden in `hidden.json`. Let the cull take it or drop it.
- Carried from earlier rounds:
  - a keep-family body module (lean-to, thatch wing or octagonal skirt) so the keep family contributes more;
  - a window module for a round daub wall (the house is still blind);
  - a backing slab under the mill interior floor;
  - `tower_of` adapters for non-drum round bodies;
  - more room for the mill door in the re-entrant corner.


## CLIENT RULE (2026-10-16, producer note 15): at most 1,000,000 triangles

Client's words: "Keep the new structures to a one million triangle limit". This building rendered 1,382,693 triangles in round 2 and must come in at 1,000,000 or fewer. It is now a hard requirement for the director and the audit; see the art bible, note 15, for how to cut without losing what the camera sees.


## v4_mixed round 4 — builder entry

Both fixes are in kit modules and on through the recipe; the recipe still holds no geometry code (two `Wing`s, two
junction steps, kit parameter dicts; 104 non-blank, non-comment lines incl. the docstring). Kit changes are recorded
in `kit/changes/v4_mixed.md` (round 4 section).

**Director must-fix: cull holes at the house wall head (`compound.py`, producer note 6).**
- `compound_views` keeps each wing's near EYE-LEVEL rings complete: every `ring_n` station at r + 0.4 m and
  r + 1.5 m, z 1.0 and 1.65 (`Wing.eye_heights`, default on), go into the never-thinned head group with the review
  cameras and door views. Only the other near heights and the far / crane rings are thinned (log: 617 ring / door /
  camera viewpoints -> 223 + 77 review, 210 kept whole incl. 132 eye-level stations; the rest are inside the other
  wing's solid). `cull_max_views` is 300 (r3: 230).
- New `wall_head_views` + band protection, automatic for any round wing whose eave lip lies below its wall head
  (`Z_EAVE` 2.40 < `PLATE_TOP` 2.97 here):
  - per-target viewpoints for `daub`, `wall_plate`, `posts`, `wattle_rods`: eye-height rings under the eave, outside
    the lip and about 6 m out, plus a band-guard ring in front of the band (254 stations);
  - `split_band` / `join_band`: the outward polygons of those parts between the lip - 5 cm and the plate top + 2 cm
    (9,590 daub, 664 plate, 998 post polygons; none inside the drum) are kept out of the cull and merged back
    afterwards, seam welded. The extra stations alone still lost one grazing daub sliver beside a post in the
    re-entrant corner (1 ray from 6 m at house az 45 deg); the protection closes it by construction.
- **Probe 5 re-run** (`round_03/director_extra/dir_probe5_r03.py` on the delivered `.blend`): **0 back-face hits of
  33,000 rays** at 4 m and 6 m (r3: 43-111 of 825 per west camera). `V4H_daub` boundary edges above z 2.3 in the
  west sectors (135-225 deg): 194 / 184 (r3: 683 / 836). The door side (az -120..-75, r3 0-6 rays) is also 0.
- Two door-head gaps the same probe exposed on the door side are fixed with new frame attributes (absent =
  unchanged):
  - `doors.build_door` `DOOR_INFILL_DECK`: on the 58 deg cone the infill boards stopped at the rafter line, leaving
    a ~0.26 m slot between the rafters over the door into the roof void. They now run to just under the batten deck,
    with a lath behind each board gap.
  - `conical_roof.build_eave_closure` `EAVE_CLOSURE_DOOR_HALF_DEG`: the closure now runs on behind the door infill,
    because the cheek opening beside it looked into the eave void (back of the roof blocker).
- My own wider ring probe (rays over each wing's whole wall from 4 / 6 m, any object): 626 back-face hits against
  944 on the r3 build. The rest are long-standing open-backed elements (shingle / starter undersides under the
  eave, the interior skin behind the wattle patches, the drum's dressed work and mortar around the slits). None of
  them is new or a cull hole, and they are listed under known gaps.

**CLIENT RULE / producer note 15 (at most 1,000,000 triangles): 1,385,232 -> 938,453.** No silhouette, entrance or
ground-contact geometry was cut. All of it is reusable kit LOD / density parameters:
- **New `village_kit/lod.py` (`tmpl_lod` step):** height-banded grid LOD for template-instanced pieces. A piece of a
  listed part whose lowest point is above `z` is re-meshed on every 2nd (above `bands` z, every 3rd) grid line of its
  `tmpl_box` template. It keeps both outer and both arris lines and all outward lines, and the piece's own shaped
  vertices, so outline corners, arrises, size and placement are unchanged and only the face grid is thinner. The
  entrance zone (r 1.3 m round the door, below 2.6 m) and the footing course (below 0.6 m) keep full density.
  Hooked into `tmplmesh.BatchAcc.add` (`LOD_HOOK`, None by default). Mill: 2,421 pieces, -292k triangles before
  the cull (base stones 323k -> 170k, arcade dressed 101k -> 33k, plus smock / cap / apron timbers, blades and the
  pooled cornice corbels).
- House (frame attributes via `compound.configure`): `DAUB_GRID` (the coat on a 7-7.5 cm grid, its relief is the
  >= 0.5 m bulge / sag; 178k -> 64k), `PLINTH_DENSE=0.55` outside the entrance zone (77k -> 38k),
  `SH_RING_STEP=0.21` (shingle rings above the butt; 72k -> 58k).
- Cull targets added (existing parameters): mill `door_leaf`, `interior`, `door_surround`, `tower_boards`,
  `cap_frame`; `drum_wall_core(n_th=96)`.
- Drum rubble a little larger within art bible 3: hr 0.10-0.21, lr 0.20-0.68 m.

**Stats** (`renders/variants/v4_mixed/round_04/stats.json`):

| Measure | Value |
|---|---|
| Triangles | **938,453** (cap 1,000,000; r3 1,385,232) |
| est_hidden_pct | **13.2 %** (r3 12.2 %) |
| Material slots | 12, all from the palette |
| `mask_attribute_missing` | none; every mesh has a UV map and `Mask`; 0 non-identity single-user transforms |
| Objects | 275 |
| Bounding box | 10.91 x 9.28 x 14.21 m (unchanged) |
| `.blend` | 22.2 MB, compressed |
| Decal anchors | 120 (191 placed, 21 dropped by the whole-building audit, thinned to 120) |
| Build time | 281 s, logged on a CPU shared with other builders and my hero re-runs (r3: 462 s) |

**Renders.** `renders/variants/v4_mixed/round_04/`: all six views at 24 samples, inspected.
- Silhouette, proportions and the roof / drum junction are unchanged.
- The door head now shows the infill boards up to the eave (actor_closeup).
- The LOD'd drum and smock read the same at review distance.
- No holes or see-through were found, so no further post-render fixes were made.

**Hero re-runs** (to scratch via `KEEP_OUT` / `HUT_OUT` / `MILL_OUT`, after every edit to an existing module that a
hero imports): hilltop_keep 1,166,874, wattle_roundhut 878,355, tower_windmill 1,146,243. All exact.

**Known gaps.**
- Long-standing open-backed elements still show back faces to a wide eye-level ray probe: shingle / starter
  undersides under the eave, the interior skin through the wattle patches, and the drum's dressed work and mortar
  near the slits. They are not cull holes and are unchanged from earlier rounds. A one-sided-in-Unreal audit of
  those kit parts is the next note-6 step.
- `est_hidden_pct` is a sampled estimate that moves about +-0.4 % between near-identical builds. The cull-target
  additions give 1.8 % of margin.
- Determinism was not re-hashed this round. Every new step is seeded or deterministic, with no random draws.
- The r3 nice-to-haves are still open: the fillet crease against the band string course, the house post buried in
  the drum, the `rafter_bearings` end_clear, a keep-family body module and a round-wall window module.

## v4_mixed round 4 — score 8.4/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12). Note 15 (at most 1,000,000 triangles) applied as a hard rule.

**Reviewed:**
- All six review renders in `renders/variants/v4_mixed/round_04/`, plus `stats.json`, `hidden.json` and the 120
  anchors in `DECAL_ANCHORS` / `decal_anchors.json`.
- The recipe (104 lines), `kit/changes/v4_mixed.md` (round 4 section), and the new kit code: `village_kit/lod.py`
  (`tmpl_lod`, `coarse_template`, `_hook`, `register` / `unregister`, `tmpl_lod_report`), the `tmplmesh.LOD_HOOK`
  call site, `compound.compound_views` (eye-level head group), `wall_head_views`, `wall_head_band`, `split_band`,
  `join_band`, `compound_cull(wall_head=True)`, and the new frame attributes `DAUB_GRID`, `PLINTH_DENSE`,
  `SH_RING_STEP`, `DOOR_INFILL_DECK`, `EAVE_CLOSURE_DOOR_HALF_DEG`.
- Director close-ups of every module junction in `renders/variants/v4_mixed/round_04/director_extra/`
  (`dir_render_r04.py`, 44 framings), in four passes:
  - clay: roof/drum eave ends (r01–r06), flaunching and band (r07–r13), wall/drum, plinth/footing and post head
    (w01b–w05b), apex, both doors, apron/smock, cap/boom, wheel hub, house eave closure (a01–a07), the house wall
    head under the low eave all round (h01–h07), the door head and its cheeks (d01–d03), the LOD'd drum and smock
    at eye level and mid height (L01–L06), thumbnail and overview (t01, t02);
  - 25 black-on-red see-through checks (`*_seethrough_red.png`);
  - 14 back-face maps, camera-seen back faces in red (`*_backface.png`, `dir_render_bf_r04.py`);
  - 20 one-sided simulations, back faces transparent on a red sky, i.e. what Unreal would show
    (`*_onesided_red.png`, `dir_render_onesided_r04.py`), with the signed-off hut and windmill heroes rendered the
    same way for comparison (`cmp_*`).
- Ray probes on the delivered `.blend` (`dir_probe_r04.py`, `dir_probe2…4_r04.py`), the same eave probe on the
  builder's scratch copy of the r3 deliverable, and a **director rebuild** of the recipe to scratch
  (`dir_hash_r04.py`).

**Recipe and kit check (director-verified).** The recipe still imports only kit modules and holds no geometry code:
two `Wing`s, two junction steps and parameter dicts. Both round-4 changes are kit-level:
- The wall-head fix is automatic in `compound` for any round wing whose eave lip is below its wall head
  (`Z_EAVE < PLATE_TOP`), and the eye-level rings are kept whole for every compound building (`Wing.eye_heights`,
  default on).
- The triangle cut is a new reusable module (`lod.tmpl_lod`, an opt-in hook that is `None` by default, so the heroes
  are untouched) plus five optional frame attributes (absent = unchanged). The LOD keeps the outer and arris lines
  and the pieces' own shaped vertices, so every stone stays a discrete, closed piece with its outline.

**Probe results.**
- **Round-3 must-fix done.** r3 probe 5 on the r4 `.blend`: 0 back-face hits on the wall band objects (daub,
  wall plate, daub interior, eave closure, blocker) of 33,000 rays from the 4 m and 6 m eye-level rings
  (r3: 43–111 of 825 per west camera). The h01–h07 close-ups show a closed daub skin and plate all round the house
  (compare `round_03/director_extra/h01`).
- Counting back faces on ANY object, the same rays find 345 hits: rafter tails (143), the starter course (119) and
  eave shingles (79), under the eave lip. These are the culled open shells of the eave pieces, seen through the
  course gaps. They are NOT new: the r3 deliverable gives 417 on the same probe, and the signed-off hut hero shows
  the same pattern (`cmp_hut_eave_west_eye_backface`). The one-sided simulations show no sky through them: a solid
  surface lies behind every one (note 6 backing rule met). Kit audit item, not a must-fix.
- Wide eye-level probe (4 m / 6 m rings, z 1.0 / 1.65, whole wall): house 148 of 16,367 back-face hits, drum 24 of
  15,310, all on the long-standing open-backed parts the builder listed.
- Door head: 0 sky rays and 7 of 4,500 back-face hits through the door head and cheeks (d01–d03 clean). The slot
  over the door on the 58° cone is closed by the infill boards up to the deck.
- Doorways: house 14 of 19,380 rays reach z 0 through floor gaps; mill floor and threshold gaps still show terrain
  (a03 and m01 see-through; the hero windmill shows the same in `cmp_mill_door_actor`). Carried nice-to-have.
- Hygiene: 938,453 triangles (evaluated), 275 objects, 12 palette slots, `Mask` and UVs on every mesh, 0
  non-identity single-user transforms, 0 degenerate faces in every part touched this round; `V4H_eave_closure`,
  `V4J_roof_tower_fillet`, `V4J_abutment_posts` and `V4M_wheel_blades` closed (0 boundary edges). The 4 + 1 edges
  with more than two faces in `V4M_base_stones` / `_base_dressed` are within single stones (not visible).
- 120 anchors, all within 4 mm of a surface; damp_rise at 0.46–0.73 m, lichen on stone tops up to 4.2 m,
  water_streak under drips up to the boom end, soot over openings. Plausible.
- **Director rebuild:** 279.5 s (log 281 s; art bible 8: about 10 min), 938,453 triangles, and a geometry hash
  identical to the delivered `.blend` (SHA-1 over names, vertices, polygon counts and matrices, `908e73e0…`).
  Determinism confirmed.

**What the renders show.**
- Silhouette unchanged (hero, front, side, back, aerial, t01). The LOD is invisible at review distance, and at 2–3 m
  the drum rubble still reads as individual flat-bedded stones with arrises and recessed joints (L01–L03, L06);
  the wheel blades, smock and apron read the same (a04–a06, L05).
- Wall/drum (w01b, w02), plinth/footing (w03b, w04), roof/drum eave ends (r01–r06) and the flaunching band (r07,
  r10) are unchanged from round 3 and clean.
- Still open from round 3: the fillet's top crease meets the band's lower string course in the valley (r12, r13,
  crane height only).
- Soft sunlight dashes on the daub under the eave (h01, h02, a07) are sun rays slipping through shingle gaps at
  grazing angles. No camera sees the sky there (all red checks clean). Not a defect.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.6 | Unchanged and right: a narrow miller's cottage under a 58° needle cone against a tall battered stone tower with apron, smock, cap, 16-blade wheel and tail. A new building of this village at thumbnail (t01). The note-15 LOD does not touch the outline. |
| 2 Proportion and actor scale | 8.5 | Unchanged: house door 0.97 × 2.10 m clear, eave lip over it 2.42–2.45 m, mill door 1.0 m wide with its head at 2.26 m. Points off as before: the framed door head sits only about 0.15 m under the eave lip, and the mill door is tight in the re-entrant corner. |
| 3 Construction logic | 8.5 | The door head now reads as built: infill boards run up to the batten deck, and the eave closure continues behind them (d01–d03). Roofs on plates, walls on plinth and footing, rafter tails stopped at the drum. Points off for the round-3 leftovers: the fillet crease runs into the band string course (r12, r13), and one house post is buried in the drum (seen only from inside). |
| 4 Seams and junctions | 8.3 | The round-3 defect is fixed in the kit: the house wall head is closed all round (0 of 33,000 band back-face hits; h01–h07), and no see-through anywhere (25 red checks). Roof/drum, wall/drum and plinth/footing are unchanged and clean. Points off: the fillet/band crease, and the open-shell eave pieces that show back faces (backed, kit-wide, also on the hut hero). |
| 5 Distinctness and reuse | 8.5 | The new `lod.py` is a genuine reusable module: opt-in, per-prefix, height-banded, with entrance and footing zones kept dense. It brought a 1.39 M recipe under the 1 M cap with parameters only. Heroes re-run exactly. Points off as before: the keep family still adds only the finial, posts and fillet. And the door-head fixes are opt-in attributes, so the next steep-cone building must remember to set them. |
| 6 Technical compliance | 8.5 | Note 15 met (938,453 ≤ 1,000,000). Hidden 13.2 %, 12 palette slots, `Mask`, UVs, identity transforms, 120 plausible anchors. Build 279.5 s, and a director rebuild is hash-identical. Points off: only 1.8 % of hidden margin on a sampled estimate, and the open-shell eave pieces still to audit for one-sided rendering (kit-wide). |

**Verdict: 8.4/10, PASSED (pass mark 8.2).** The round-3 must-fix is fixed where it belongs: `compound` now keeps
every wing's eye-level rings whole and protects a wall-head band under a low eave lip automatically, so every
future compound building with a steep, short-overhang cone inherits it. The new client rule (note 15) is met
without touching silhouette, entrance or ground contact, through a reusable LOD module and frame attributes. The
director rebuild confirms the 280 s build, the triangle count and determinism. Nothing on this building breaks a
producer note. The remaining items are kit polish.

**Strengths**
- `compound.compound_views` / `wall_head_views` / `split_band` / `join_band`: the fix is generic and automatic. It
  keys on the frame's own numbers (`Z_EAVE < PLATE_TOP`) rather than on this recipe, and the protected band makes a
  cull hole there impossible by construction.
- `village_kit/lod.py` is a clean, reusable LOD layer. It is opt-in through a hook that is `None` by default, keyed by
  object prefix, and height-banded (note 15: mid-distance first). Entrance and footing zones stay at full density,
  and it keeps each piece's outline, arrises and placement. Mill pieces 323k → 170k (base stones) and 101k → 33k
  (arcade) with no visible change at 2–3 m.
- Triangles 1,385,232 → 938,453 with the silhouette, entrance and ground contact untouched, all by kit parameters.
- The door-head slot and cheek gap found by the r3 probe were fixed as reusable frame attributes in `doors` and
  `conical_roof`, not in the recipe.
- Build time 462 s → 280 s, now with 300 viewpoints, and hash-identical between the builder's and the director's
  builds.

**Must-fix (round 5)**
- None. No producer-note violation was found on this building, and no junction is open.

**Nice-to-have (not blocking; kit-level, so every building gains)**
1. `conical_roof` eave pieces (`roof_starter`, the eave shingle courses, `rafters` tails outside the wall line,
   about r ≥ R_WALL): the cull leaves them as open shells, and from 4 m at eye level you see their insides through
   the course gaps (345 back-face hits here, 417 in r3, the same on the hut hero; `h01_…_backface`). Either keep
   the outward and under faces of the first two courses and the rafter tails out of the cull (as `split_band` does
   for the wall head), or give them closed caps, so that nothing at the eave renders one-sided in Unreal.
2. `junctions.ride_fillet`: read the tower's band zones and keep the crease at least 5 cm under the lowest string
   course (today z 3.83 against the band bottom at 3.80; r12, r13). Carried from round 3.
3. `doors.build_door` `DOOR_INFILL_DECK` and `conical_roof.build_eave_closure` `EAVE_CLOSURE_DOOR_HALF_DEG`: switch
   them on automatically when the cone pitch leaves the infill short of the deck (for example pitch above about
   55°), so the next steep-cone building does not reopen the slot over the door.
4. `lod.tmpl_lod`: unregister the prefix rule at the end of the wing (in `tmpl_lod_report` or `drum_finish`), so
   that a later wing or building in the same process with the same prefix cannot inherit it.
5. Carried: a mill floor backing slab (threshold and floor gaps show terrain through the mill door, a03 and m01); clip
   or drop the house post inside the drum; `rafter_bearings` `end_clear` about 0.25 m; a keep-family body module
   (lean-to, thatch wing or octagonal skirt); a round daub-wall window module; and the kit README update for
   `lod.py` and the round-4 frame attributes.