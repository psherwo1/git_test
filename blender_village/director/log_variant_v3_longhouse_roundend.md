# Variant log: v3_longhouse_roundend

## v3_longhouse_roundend round 1 — builder entry

**What it is.** The ref1 longhouse (lower middle): a long, low rubble longhouse under a layered thatch gable roof,
ending in a round rubble house under a conical chunky-shingle roof with a stone ball finial.  Principal door on the
long south (-Y) wall.  Graded on the note-12 modularity rubric; no surface-detail work was done (note 12).

- Build: `buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py` (declarative recipe, 88
  non-blank non-comment lines including its docstring) -> `v3_longhouse_roundend.blend` (13.0 MB, compressed) +
  `decal_anchors.json`.  Build time 13 min (the hidden-geometry ray test is most of it; `LONG_FAST=1` skips it for
  look-dev, 70 s).
- Renders: `renders/variants/v3_longhouse_roundend/round_01/` (hero, front, side, back, aerial, actor_closeup at
  24 samples + stats.json + hidden.json).

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 518,075 |
| est_hidden_pct | 14.9 % |
| material slots | 10 (M_stone, M_stone_dressed, M_mortar, M_timber, M_timber_weathered, M_roof_shingle, M_roof_shake, M_thatch, M_iron, M_lead) |
| mask_attribute_missing | none |
| bbox | 17.72 x 8.56 x 7.67 m (z -0.05 .. 7.62), plan bbox centred on the origin |
| objects | 59 (28 pooled peg instances) |
| decal anchors | 88 (101 placed, kit gate `anchor_validate.validate_anchors` applied: 11 footprint, 1 no surface, 1 occluded dropped) |

### Dimensions

- Round end: RoundFrame radius 3.50 (plate line), rubble face r 3.64 m at the ground, 2.5 deg batter, wall head 2.5 m
  under a pegged plate; cone 48 deg, eave radius 4.22 m, eave lip 2.30 m, chunky kit shingles with the AGE_R10 sag /
  under-lap, lead hat + stone ball finial to 7.62 m.  Two deep-set windows.
- Body: rubble walls 13.0 x 5.2 m to the outer faces (gable face to the round-end centre; 11 m of it outside the
  round end), deck at the faces 2.75 m, 40 deg thatch, 0.45 m eave overhang (eave lip underside 2.33 m over the door),
  0.40 m verge at the free gable.  Door 1.00 x 2.10 m clear on a 12 cm threshold slab; four windows (sills 1.25-1.30).

### The recipe (what is combined)

`RoundFrame` (dimension table) -> `set_entrance` -> `round_stone_body` (clip: inside the body) -> `wall_plate` ->
`path_stone_wall` along the U-shaped body plan (clip: inside the round wall; gable top from the roof spec) ->
`cone_roof` -> `ball_finial` -> `round_eave_fill` -> `linear_roof(GableRoof, covering="thatch", abut_cone=(0, 0))` ->
`cone_abutment` -> `composite_hidden_cull` -> `recenter`; decals `composite_decals` + the kit anchor gate.
The only numbers in the recipe are the plan, heights, pitches, opening positions and seeds.

### New kit modules (all new files; no existing kit file edited -> no hero re-run needed)

Recorded in `kit/changes/v3_longhouse_roundend.md`.
- `components/linear_roof.py`: `GableRoof` spec + `linear_roof` (deck backing, rafter tails, verge rafters, layered
  thatch with rounded bundle butts and a half-round eave nose, or kit chunky shingles; ridge roll + shake comb; clip
  for the end that dies into another body).
- `components/roof_junction.py`: `inside_cone`, `abutment_curve`, `cone_abutment` (the linear-roof-to-cone junction:
  exact junction line from eave soffit over the eave nose, slopes and ridge roll to the other side, closed lead
  flashing with both skirts dressed into the coverings), `round_eave_fill`.
- `components/wall_openings.py`: frame-placed door (threshold, posts, lintel, plank leaf via `plank_doors.plank_leaf`,
  straps) and window (sill with drip, deep frame + mullion, lintel, reveal, blocker room) for any masonry wall.
- `components/rubble_walls.py`: `path_stone_wall` (coursed rubble along any plan polyline: footing, solid long-and-short
  quoins at every outside corner, gable rake top, openings, junction clip, mortar body) and `round_stone_body`.
- `components/ball_finial.py`: lead hat + stone ball finial (the README's "ball" extension point).
- `components/composite.py`: cone roof without the hut daub closure, entrance zone, junction clips, footprint-loop
  hidden cull, recentre, composite decal anchors.

### Junctions (rubric axis 4) -- checked in all six views

- Thatch -> cone: clipped under the cone covering; continuous lead flashing along the whole junction line (soffit,
  nose, both slopes, over the ridge roll); no see-through in back / hero / aerial.
- Body walls -> round wall: body stones dropped >12 cm inside the round face, the body mortar body continues into it;
  the round wall is dropped inside the body.  The footing courses meet in a re-entrant corner.
- Round wall head -> cone: wall plate + eave fill up into the shingle stack.
- Gable wall -> roof: stones and mortar follow the rake 2 cm into the deck; verge rafter and thatch verge face.

### Known gaps

- The thatch reads as rounded layered bundles at mid-shot but is fairly regular from the back / aerial; the ridge
  comb is small at review distance (ref1 shows a stronger crest).
- At the south / north eave corners where the thatch eave dies into the cone eave, the flashing end makes a small
  lead lump under the eave (closed, but not elegant).
- Straight walls have no batter (quoins are solid boxes); the round end has no timber posts in its wall (ref1 shows
  some) and no fringe under its eave.
- `cone_abutment` covers a linear roof meeting a CONE; a roof meeting a taller round WALL needs a cylinder variant.
- Determinism: every step is seeded (np.random default_rng / RandomState); a second full build was not compared
  bit for bit this round.

## v3_longhouse_roundend round 1 — score 7.8/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_01/`, plus `stats.json`, `hidden.json`
  and `decal_anchors.json` (88 anchors).
- The recipe and the six new kit modules.
- 17 director junction close-ups and 7 see-through checks (black clay against a red sky) in
  `renders/variants/v3_longhouse_roundend/round_01/director_extra/`.
- A second full build to scratch.

**Determinism and compliance (director-verified).** The rebuild matches the delivered file exactly: same geometry
hash (`381aeb20…`, 518,075 tris) and a byte-identical `decal_anchors.json`. Other checks all pass:
- every unique mesh has an identity transform;
- every mesh has a UV map;
- `Mask` is present on every mesh and is both the active and the render colour attribute;
- there are no zero-area faces;
- the collections are `LONG`, `LONG_kit_instances` and `DECAL_ANCHORS`.

The full build took 1017 s here, with director renders running at the same time; the builder reports 13 min.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.3 | It is unmistakably the ref1 longhouse with a round end: a low rubble body, a 48 deg cone and a ball finial, in the right plan arrangement. However, the "thatch" reads as rows of pillow tiles at thumbnail size, and the ridge crest is weak next to ref1. |
| 2 Proportion and actor scale | 8.8 | The door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is 2.33 m, sills are at 1.25-1.30 m and the round-end eave is at 2.30 m. The body is 13.0 x 5.2 m (about 10.5 m of exposed wall), which is in ref1's ratio to the 7.3 m round end. |
| 3 Construction logic | 8.4 | Walls sit on footings, there is a pegged wall plate on the round wall, rafter tails sit under the deck, and the gable wall follows the rake into the deck. The door has posts, a lintel and a threshold. The weak point is the eave crossing: both eaves are at about 2.3 m, the cone's eave shingles run into the thatch eave nose, and a crumpled lead mass hides the clash. |
| 4 Seams and junctions | 7.4 | The slope and ridge flashing is excellent: it follows the true intersection, with no gaps. The wall-to-wall joint is closed. But the flashing ends at both eaves crumple into faceted lead lumps that hang below the eave lines, 4.7 m from the door at eye level. The free gable verge shows a black barcode of slots along both rakes. Sky shows under the ball-finial lead hat, and there are sky pinholes under the cone overhang beside the junction (both ray-confirmed). |
| 5 Distinctness and reuse | 8.5 | It is a genuinely new building type. The recipe is 107 declarative lines, with six new reusable kit modules and no hero file edited. Points off: the thatch covering invents a second thatch language that does not match the kit's `thatch.py`. Several modules duplicate parallel-built ones (`stone_body`, `framed_openings`, `tier_hidden_cull`, `junctions.roof_tower_flashing`); this is for the producer's merge. |
| 6 Technical compliance | 8.5 | 518k tris, 14.9 % hidden (at the 15 % limit), 10 palette slots, no missing `Mask`, no ground dressing, 88 plausible decal anchors, and the bit-identical rebuild is confirmed. The build takes 13 min, over art bible §8's limit of about 10 min. |

**Verdict: 7.8/10, NOT PASSED (pass mark 8.2).** The kit test itself mostly works. GableRoof, the cone abutment
along the slopes and ridge, the polyline rubble wall and the round body combine from a short declarative recipe
into a convincing ref1 longhouse, and the rebuild is bit-identical. The grade is capped by the junction axis:
- the abutment's eave terminations crumple;
- the thatch verge has open slots;
- there are two see-through spots (under the finial hat, and under the cone overhang).

The thatch covering also needs to read as thatch. All the fixes are module-level, so every future building that
uses these modules gets them for free.

**Strengths**
- It is a genuinely new structure from a 107-line declarative recipe: a RoundFrame plus a GableRoof spec and
  ordered kit steps. No hero file was edited, and the rebuild is bit-identical.
- `GableRoof` is one spec object that the walls (`body_top`), the junction and the decals all read. Pitch, yaw,
  verge, covering and abutment are parameters, so it is properly reusable.
- The `cone_abutment` flashing on the slopes and over the ridge roll follows the analytic intersection cleanly.
  No gaps or clipping showed in the crane, back or ridge close-ups (j03, j04, j05, j17).
- `path_stone_wall` works on any polyline, with solid long-and-short quoins, a gable rake top tucked under the deck
  and junction clips. The gable wall and the verge rafter close with no sky (j11 red check).
- Actor scale is right everywhere, and the door, windows, threshold and sills are all module-built.
- Technically clean: palette, `Mask`, UVs, transforms, Nanite hygiene, pooled pegs, and decal anchors on plausible
  surfaces.

**Must-fix (round 2)**
1. **`roof_junction.cone_abutment`, eave ends.** These are on both sides at x ≈ 2.3, y ≈ ±3.1, z ≈ 2.2-2.5 m (after
   the recentre); see j01, j02, j06 and j17.
   - What is wrong: the 8-point flashing section is swept round the 90 deg soffit -> nose -> slope corners, and it
     crumples into a faceted lead lump that hangs below both eave lips. It is visible from the door approach and
     from the back.
   - What it should be: the swept flashing stops at the top of the thatch eave nose. Each end becomes a separate
     closed lead end-apron, folded down over the nose face and tucked under the cone's starter course. No part may
     sit below the cone eave lip (2.30 m), and the apron should be no more than about 0.35 m across. The soffit
     closure belongs to the deck and eave fill, not to the sweep.
   - Make it a `cone_abutment(end="apron")` option and use it by default, so every linear-roof-to-cone junction gets
     it.
2. **`linear_roof._thatch_courses`, free verge.** This is the west gable, both rakes, x ≈ -8.8; see j11.
   - What is wrong: the clump verge side faces leave an open wedge cavity between every two courses. They render as
     about 20 black slots per rake, from eye level at 5 m.
   - What it should be: one continuous closed verge face per rake, running from the deck underside to the covering
     top and following the course steps (or a continuous verge roll). The verge must read as a solid thatch edge,
     with no dark slots.
3. **`linear_roof` thatch covering: make it read as thatch, with LESS geometry, not more detail.**
   - What is wrong: the 0.20-0.48 m crowned clumps read as rows of clay tiles or slates in the hero, front, back and
     aerial views. They do not match the kit's existing thatch language (`thatch.py`, the keep's west wing) or ref1.
   - What it should be: continuous courses with drifting butt lines and only soft bundle undulation (crown ≤ 1 cm,
     clump runs of 1 m or more, or continuous). Reuse `thatch.py`'s eave roll (`d_roll`) and course approach where
     the geometry allows. A linear thatch roof and the keep wing must read as one material family at mid-shot.
4. **`ball_finial`, apex at z ≈ 6.4-6.6 m.** See j14 and `j14_ball_finial_cone_seethrough_red.png`.
   - What is wrong: sky is visible from crane height through the gap under the lead hat rim (ray-confirmed near
     (4.0, -0.1, 6.55)). The hat is also pitched at about 29 deg (`hat_drop` 0.34 on r 0.62), not the art bible's
     about 44 deg collar.
   - What it should be: hat pitch 44 deg (`hat_drop` ≈ r·tan 44 deg ≈ 0.60), with the drip fitted no more than 3 cm
     over the top shingle course, as `round_apex.turned_apex` already does, plus a closed apex blocker under the hat.
     No sky may pass under the hat from any crane view.
5. **`composite.cone_roof`, the round-end overhang.** This is at x ≈ 3.3-4.5, y ≈ -3.4 to -3.9, z ≈ 2.5-3.1 m,
   beside the junction; see `j10_round_eave_lookup_seethrough_red.png`.
   - What is wrong: there are pinholes of sky between the rafters, plate, battens, under-lap and shingles. The roof
     blocker starts at z = 2.91, so the overhang has no backing.
   - What it should be: a continuous sarking or soffit deck under the whole cone overhang (v1's
     `tower_roof.round_tower_roof` boarded soffit slab solves exactly this; reuse it). No eye-level ray may reach
     the sky through the eave.
6. **Build time, `composite.composite_hidden_cull`.**
   - What is wrong: the full build takes 13 min (17 min measured here under load), over the art bible §8 limit of
     about 10 min. `footprint_views` produces 953 viewpoints.
   - What it should be: a full build of 10 min or less on 4 shared cores, with est_hidden_pct still ≤ 15 %. For
     example, trim it to 2 loop distances x 3 heights + crane + door views, or ray-test only the large stone and
     shingle objects.

**Nice-to-have (not blocking)**
- The producer should merge the parallel duplicates into one kit API:
  - `rubble_walls.round_stone_body` with `stone_body.stone_body`;
  - `wall_openings` with `stone_body.opening` / `framed_openings`;
  - `composite_hidden_cull` with `tier_finish.tier_hidden_cull`;
  - `cone_abutment` with `junctions.roof_tower_flashing` / `tier_roof.roof_flashing`, as one junction family.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's strong crest; a silhouette change,
  not surface detail).
- In the recipe, `X_END` and the clip depth are hand-tuned (the body path runs 0.3 m into the round wall). A
  `path_to_round(center, r_face)` helper should derive the path end from the round body.
- A few clipped sliver stones remain near the body/round re-entrant joint at the wall head (j01, j07). The joint
  itself is an acceptable straight joint.
- Decals: add moss or debris anchors in the thatch-to-cone valley, and `water_streak` under the cone eave drip.
  `composite_decals` promises both, but none survived the gate. Move `lichen_003`/`004` off the threshold top
  (a walked surface).
- `cone_abutment`: a cylinder variant (roof into a taller round wall), as the builder noted.
- Optional later module parameters for ref1: timber posts in the round wall, and an eave fringe.
- Hidden is 14.9 %. Leave some margin after fixes 1-5 add backing.

## v3_longhouse_roundend round 2 — builder entry

All six must-fixes were made in the KIT MODULES (new functions and new keywords; the round-1 behaviour is still
available through the old keyword values). The recipe changed by one argument (`cone_roof(..., soffit_skip=in_body)`)
plus one decal-gate exclusion. No surface-detail work was done (note 12). Kit changes are recorded in
`kit/changes/v3_longhouse_roundend.md`. Only v3's own round-1 modules were edited. Grep confirms that no hero and no
other variant imports `linear_roof`, `roof_junction`, `ball_finial` or `composite`, so hero triangle counts cannot
move. `thatch.d_roll` is reused unchanged.

- Build: `buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py` (90 non-blank, non-comment lines
  including the docstring) -> `v3_longhouse_roundend.blend` (11.9 MB, compressed) + `decal_anchors.json` (89 anchors).
- Renders: `renders/variants/v3_longhouse_roundend/round_02/` (all six views at 24 samples, plus stats.json and
  hidden.json). Builder close-ups and red see-through checks are in `round_02/builder_checks/`.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 469,769 (round 1: 518,075) |
| est_hidden_pct | 12.9 % (round 1: 14.9 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m (z -0.05 .. 7.64), plan bbox centred on the origin |
| objects | 62 (28 pooled peg instances) |
| full build time | 9 min 24 s, measured with the CPU at 100 % load from other builders (round 1: 13 min) |

### Must-fixes

1. **`roof_junction.cone_abutment` eave ends -> `end="apron"` (new default).**
   - `abutment_curve(..., ends="crest")` makes the sweep run over the slopes and the ridge only. It stops 6 cm
     up-slope of the eave-roll crest.
   - The new `end_apron` builds each eave end as a separate closed lead apron lying on the roll's nose. It runs
     from just above the crest down the nose face. It is a band 0.20 m onto the thatch plus 0.12 m tucked under the
     cone's starter course (0.32 m across). The band is centred on the seam where the cone covering crosses the
     nose, and the seam line is smoothed.
   - Nothing sits below the cone eave lip: the apron's floor is g.Z_EAVE + 3 cm, and the roll's lowest point is
     about 2.36 m.
   - Checks: `builder_checks/apron_front`, `apron_w`, `s_eave_eye`, `n_eave_eye` and `actor_closeup` show no lumps
     under either eave.
   - Supporting module change: `linear_roof(..., abut_wall_in=0.10)`. A roof that abuts a cone is now dropped only
     where it is under the cone AND inside the round wall head. Under the cone's oversailing eave, the deck, eave
     roll and courses run on and die into the round wall. This closes the pocket the old soffit sweep used to hide,
     and leaves the soffit to the deck and the eave fill, as the review asked.
2. **Free verge -> `_verge_faces`.** Each free gable gets ONE tessellated closed polygon in the gable plane. It runs
   from the deck underside up to the upper envelope of the eave roll and of every course's end section, across both
   rakes and under the ridge roll. A foot strip runs back under the deck end. `verge` and `verge_red` show no slots
   and no sky.
3. **Thatch covering -> `linear_roof(..., thatch_style="courses")` (new default; `"clumps"` is round 1).**
   - Courses: each course is one continuous sheet per slope with a rounded butt. The butt line drifts by ±4.5 cm
     over 2-4 m. Courses are laid in bundle runs of 1.0-2.2 m, each with a ±1.8 cm set, at most 1.2 cm of lift and a
     soft crown of at most 9 mm.
   - Eave: the keep wing's eave-roll language. It is a D-section roll (`GableRoof.eave_roll`) swept with
     `thatch.d_roll`.
   - Result: fewer, wider units. The covering plus the roll is about 26k polygons, against the round-1 clumps
     (76k tris in the covering). In hero, back, aerial and `roof_mid` it reads as layered thatch courses, not tiles.
4. **`ball_finial`.**
   - The hat is pitched at 44 deg (`hat_drop = hat_r tan 44°` ≈ 0.60), with the apex set the way
     `round_apex.turned_apex` sets it. `finial.lead_hat` fits the drip over the top shingles with 2 cm clearance.
   - The new `apex_blocker` is a closed plug under the hat, 4 cm under the cone reference surface, out to
     r = 0.92 m (`LONG_apex_blocker`, backing).
   - `finial` and `finial_red` show no sky under the hat.
5. **`composite.cone_roof(..., soffit=True)` -> new `cone_soffit`.** This is v1's `tower_roof._roof_deck` closed
   boarded slab, limited to the overhang (top face, soffit face and eave edge) from 10 cm above the lip to 7.5 cm
   inside the plate line. The part inside the body is skipped. `s_soffit_up_red` and `s_eave_eye_red` show no sky
   through the round eave beside the junction.
6. **Build time -> `composite_hidden_cull(..., views="lean")`.**
   - Views: `LEAN_VIEWS` is 2 loop distances x 3 heights, 1 crane loop and 27 door views. Roof coverings
     (`ROOF_PARTS`) are ray-tested from `ROOF_VIEWS` only: no knee-height loop and no door views. That is 286
     viewpoints, against 953 in round 1.
   - Lighter roll: the eave roll is built without its buried back.
   - Result: 9 min 24 s under full shared load, with est_hidden 12.9 %.

### Known gaps

- I did not ray-test the hat drip gap per azimuth. `lead_hat` guarantees 2 cm clearance over every shingle vertex
  under the hat, but at one or two azimuths a shingle edge can show as a faint crease line on the hat in
  `builder_checks/finial`.
- Nice-to-haves were not done: the stronger ridge-comb crest, `path_to_round`, the decal valley moss, the cone
  cylinder variant and the duplicate-module merge.
- I did not compare a second full build bit for bit this round. Every step is seeded. The deliverable is the build
  made to scratch with the final code, copied in with its `decal_anchors.json`.

## v3_longhouse_roundend round 2 — score 8.1/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_02/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (89 anchors) and the builder's `builder_checks/`.
- The recipe, `kit/changes/v3_longhouse_roundend.md` and the round-2 module code (`roof_junction.end_apron`,
  `cone_abutment(end="apron")`, `linear_roof` courses / `_verge_faces` / `abut_wall_in`, `ball_finial.apex_blocker`,
  `composite.cone_soffit`, `LEAN_VIEWS`).
- 27 director junction close-ups, 11 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_02/director_extra/` (d01-d27): both eave crossings from west and
  east at eye level, both slopes from the crane, the ridge into the cone, both soffit crossings looking up,
  body wall into round wall (S and N), round wall head to cone eave, two round-eave look-ups, both gable verges, the
  verge/eave corner, the ridge end, the gable footing corner, the body eave look-up, the finial from four crane
  azimuths plus a clay close-up, the door, a round-end window, the ridge comb, a top-down junction and a back
  three-quarter.
- A second full build to scratch, compared with the delivered file.

**Determinism and compliance (director-verified).** The rebuild matches the delivered file exactly: same geometry
hash (`f14d1009…`, 469,769 tris) and a byte-identical `decal_anchors.json` (SHA-256 `4E359FB3…`). Every unique mesh
has an identity transform and a UV map; `Mask` is present on every mesh and is both the active and the render
colour attribute; there are no zero-area faces; the collections are `LONG`, `LONG_kit_instances` and
`DECAL_ANCHORS`; the 28 pegs share one mesh. Stats: 469,769 tris, est_hidden 12.9 %, 10 palette slots, nothing in
`mask_attribute_missing`, 62 objects, 11.9 MB. The rebuild took 678 s (11.3 min) here, with about ten other
builder processes on the CPU; the builder measured 9 min 24 s. That is at the art bible §8 limit (about 10 min) and
is not blocking.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | It is unmistakably the ref1 longhouse with a round end: a low rubble body, a 48 deg cone with a ball finial, and the thatch now reads as layered thatch courses (not tiles) in the hero, front, back and aerial views. The ridge crest is still weak next to ref1's strong comb. |
| 2 Proportion and actor scale | 8.8 | Unchanged and right: the door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is about 2.33 m, sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. The body-to-round-end ratio matches ref1. |
| 3 Construction logic | 8.3 | Walls sit on footings, the plate, rafters, deck and soffit carry the roofs, the finial has a hat and an apex plug, and the door and windows are module-built. The one illogical spot is the eave crossing: the cone's eave courses do not stop where the thatch eave roll is, they run on through it (must-fix 1). |
| 4 Seams and junctions | 7.9 | All four round-1 junction defects are fixed. There is no lead lump (d01, d02), the verge has no slots (d15/d16 red), there is no sky under the hat at any of four azimuths (d21) and none through the round eave (d13/d14 red); the slope and ridge flashing is still clean (d05-d07). One clear clipping defect remains at the key junction: at both eave crossings the cone's starter, under-lap and bottom shingle courses splay into a fan of 6-8 stacked plates with dark wedge gaps, crossing the thatch roll and hanging below the soffit (d03, d04, d08, d09). It is visible at eye level about 4.7 m from the door. There is also a dark open slot at both free-gable eave-roll ends (d15, d16) and shingle corners poke through the lead hat (d22). |
| 5 Distinctness and reuse | 8.6 | It is a genuinely new building type from a 90-line declarative recipe. All six fixes landed in kit modules as new keywords, the round-1 behaviour is still reachable, and the recipe changed by one argument. Points off as before: the parallel duplicate modules still await the producer's merge. |
| 6 Technical compliance | 8.8 | The rebuild is bit-identical; 470k tris, 12.9 % hidden, 10 palette slots, `Mask` everywhere, no ground dressing and 89 plausible decal anchors. The build time is at the limit under shared load. Two anchors (`lichen_003`/`004`) still sit on the threshold's walked top. |

**Verdict: 8.1/10, NOT PASSED (pass mark 8.2), but close.** Round 2 is a clear step up (7.8 -> 8.1). Every round-1
must-fix was made at module level, and four of the five junction defects are gone. The thatch reads as thatch with
fewer triangles, and the rebuild is bit-identical. The grade is capped by the eave crossing, the junction the brief
names as the key test. The linear roof now yields to the cone, but the cone does not yield to the linear roof: its
covering is built with no knowledge of the body roof and runs through the thatch eave roll as a splayed stack of
shingles. This is one module-level fix in `cone_roof`, and every future round-end, tower-annex or turret-to-roof
junction gets it for free.

**Strengths**
- All six round-1 must-fixes were made in the kit modules as new keywords (`end="apron"`, `thatch_style="courses"`,
  `abut_wall_in`, `soffit=True`, `apex_blocker`, `views="lean"`), with the old behaviour still reachable. The recipe
  changed by a single argument, which is how a kit should evolve.
- `end_apron`: the eave ends are now neat closed lead aprons, and nothing hangs below the cone eave lip (d01, d02).
  The slope and ridge sweep still follows the analytic intersection with no gaps (d05-d07, d07 red).
- `_verge_faces`: one closed verge face per gable, with no slots and no sky from either diagonal (d15/d16 red).
- `cone_soffit` and `apex_blocker` close every see-through path (d13, d14 and d21 red). Eye-level rays find no sky
  through the round eave, the body eave (d20 red) or under the hat.
- The thatch reads as layered thatch courses with a D eave roll reused from `thatch.d_roll`: the same family as the
  keep wing, with 48k fewer triangles than round 1.
- Technically clean and bit-identical on a director rebuild (geometry hash `f14d1009…`, identical decal JSON).

**Must-fix (round 3)**
1. **`composite.cone_roof` / `conical_roof.build_shingles`: the cone covering at the eave crossing.** This is on
   both sides at x ≈ 2.0-2.6, y ≈ ±(2.9-3.4), z ≈ 2.25-2.70 m (after the recentre); see d03, d04, d08, d09 and the
   enlarged crops `crop_d03`, `crop_d04` and `crop_d08` in `director_extra/`.
   - What is wrong: the cone's starter course, under-lap and bottom 2-3 shingle courses are built round the full
     360 deg with no knowledge of the body roof. Where the cone eave crosses the thatch eave roll they run on through
     the roll. They show as a fan of 6-8 splayed plates with dark wedge gaps, crossing the roll and hanging
     diagonally below the soffit over the wall head, visible from the door approach.
   - What it should be: a reusable keep-out on the cone side, matching `linear_roof(abut_cone=...)`, for example
     `cone_roof(..., abut_roof=ROOF)` or `keep_out=fn`. It drops every cone covering unit (shingle, starter,
     under-lap) whose footprint lies below `ROOF.top_z + 2 cm` on the body side of the abutment line, and the
     battens and soffit there with them.
   - Result: the cone's eave courses end in a regular, closed course line that rests on the end apron. The apron's
     `w_in` tucks under the last remaining starter. No cone unit sits inside or under the thatch roll, and none
     below the cone eave lip.
   - Re-shoot d03, d04, d08 and d09, plus red twins.
2. **`linear_roof._eave_rolls` / `_verge_faces`: the eave-roll ends at the free gable.** This is at both corners,
   x ≈ -8.8, y ≈ ±3.0, z ≈ 2.30-2.55 m; see d15 (north end) and d16 (south end, `crop_d16`).
   - What is wrong: a dark open slot about 4-5 cm wide and 20 cm tall between the end of the D-roll and the verge
     face. It reads from each diagonal approach at eye level.
   - What it should be: a closed end cap on the roll, and the verge face's lower envelope extended over the roll's
     full D section, so the verge face and the roll end meet with no gap or dark slot.
3. **`ball_finial` / `finial.lead_hat` fit: shingles through the hat.** This is at the apex, z ≈ 6.4-6.6 m,
   r ≈ 0.3-0.5 m, two azimuths; see d22 (`crop_d22`).
   - What is wrong: two shingle corners pierce the 44 deg hat surface as dark creases. The 2 cm clearance is tested
     against shingle centres or butts, not against every corner after the age lift and rotation.
   - What it should be: no shingle geometry above the hat's underside. Test the clearance against every vertex of
     every unit under `hat_r` + 5 cm, or drop and shorten the units that fail. This is the same rule
     `round_apex.turned_apex` applies.

**Nice-to-have (not blocking)**
- Thatch courses: in the back three-quarter and the north crane views (d27, d06), thin bright hairlines run along
  several course butts where a lower course's buried tail surfaces through the course above in a drift trough.
  Clamp each tail at least 1 cm under the envelope of the course above.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's strong crest; open since round 1).
- Verge face: it now reads as a flat barge board. A soft rounded or stepped thatch edge on the same closed face
  would read more like ref1 at mid-shot (silhouette, not surface detail).
- Decals: move `DA_lichen_003`/`004` off the threshold top (a walked surface). Add the promised `water_streak`
  under the cone eave drip and moss in the thatch-to-cone valley.
- Producer merge and helpers, carried over from round 1: `path_to_round(center, r_face)`; one junction family
  (`cone_abutment` + `junctions.roof_tower_flashing` + `tier_roof.roof_flashing`); a cylinder variant of
  `cone_abutment`; merging `round_stone_body` / `stone_body` and `wall_openings` / `framed_openings`.
- Build time: 11.3 min measured here under heavy shared load. Keep the margin when the cone keep-out adds work.

## v3_longhouse_roundend round 3 — builder entry

All three must-fixes were made in v3's own KIT MODULES as new functions, methods and keywords (the round-2
behaviour stays reachable through the keyword defaults). The shared `conical_roof.py`, `finial.py` and `thatch.py`
were reused unchanged. Grep confirms that no hero and no other variant imports `linear_roof`, `roof_junction`,
`ball_finial` or `composite`, so no hero re-run was needed. No surface-detail work was done (note 12). Kit changes
are recorded in `kit/changes/v3_longhouse_roundend.md` (round 3 section).

- Recipe: `linear_roof` now runs before `cone_roof`, because the cone needs the roof's eave-roll section for its
  keep-out. Two arguments were added: `cone_roof(..., abut_roof=ROOF)` and `ball_finial(..., hat_seg=96, fit=True)`.
  The recipe is 91 non-blank, non-comment lines.
- Build: `v3_longhouse_roundend.blend` (12.0 MB, compressed) and `decal_anchors.json` (88 anchors). The full build
  took 7 min 59 s under shared load (round 2: 9 min 24 s).
- Renders: `renders/variants/v3_longhouse_roundend/round_03/` (all six views at 24 samples, plus `stats.json` and
  `hidden.json`). There are 23 builder close-ups in `round_03/builder_checks/`, 7 of them red see-through twins.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 476,893 (round 2: 469,769) |
| est_hidden_pct | 13.4 % (round 2: 12.9 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 62 (28 pooled peg instances) |

### Must-fixes

1. **The cone covering at the eave crossing → `composite.cone_keep_out` / `cone_roof(abut_roof=ROOF)`.**
   - This is the mirror of `linear_roof(abut_cone=...)`: the cone now yields to the roof.
   - The roof is described as a solid by new `GableRoof` methods: `section_loop`, `section_columns`, `keep_out`,
     `top_depth`, `eave_zone` and `under_soffit`. The solid is the deck, courses, D eave roll and ridge roll, in
     vertical columns, so everything under the roof counts as inside it too.
   - The new helpers `mesh_islands` and `drop_units` delete whole units (connected islands) and never cut a unit.
   - Rule "tuck" (the default) drops whole shingles, starters, under-laps and battens in these cases:
     - the unit lies wholly inside the roof solid;
     - any vertex is under the soffit or the roll belly;
     - any vertex is in the eave band (the eave roll);
     - any vertex is more than 15 cm under the roof top.
   - Rafter, purlin and soffit faces that lie wholly inside are dropped as well.
   - Removed polygons: 12,910 shingle, 1,040 starter, 780 under-lap, 132 batten, 673 rafter and 96 soffit.
   - Result: at both eaves the cone's courses end on whole units over the roll and its end apron. Nothing sits
     inside or under the roll, and nothing hangs below the soffit (`s_/n_eave_east_eye`, `s_/n_eave_close`,
     `s_/n_soffit_up`). The red twins show no sky.
   - On the slopes, a unit may still tuck a corner just under the thatch beside the flashing, as it did in round 2,
     which the director graded clean (`s_slope_crane` and its red twin).
2. **Free-gable eave-roll ends → `_eave_rolls(end_caps=True)` + `_verge_faces(roll_cover=0.012)`.**
   - The roll keeps its back over the last 0.10 m of each free end, so the end is a closed, rounded cap.
   - The verge face's eave end now covers the roll's whole D section, 1.2 cm inside the roll's outline.
   - `s_/n_verge_corner` show no slot, and their red twins show no sky.
3. **Hat fit → `ball_finial(fit=True)`: `hat_fit_units`, `fine_hat` and `hat_underside`.**
   - The round-2 "creases" were not shingles. An exact BVH overlap test found no shingle polygon crossing the hat's
     outer surface; every shingle vertex was at least 2.0 cm under it. What did pierce the 44 deg hat was the
     `conical_roof` rafter hub (r 0.39 m), at the two bulges of its wavy lathe.
   - `hat_fit_units` tests every vertex of every covering and structure unit within hat_r + 5 cm against the BUILT
     hat's actual profile. It drops the units that come through the hat and the units wholly under it; this round
     that was the hub, 120 polygons.
   - `fine_hat` re-lathes the same fitted hat from a smooth, finely subdivided profile.
   - `hat_underside` adds an 8 mm lead underside.
   - The worst clearance kept is 2.0 cm. BVH overlap on the delivered file: nothing crosses the hat's outer surface.
     The only contacts are the drip's closed bottom cap on the top course, and the finial socket seated in the hat
     top.
   - `finial_az020`, `finial_az110`, `finial_az200`, `finial_az290` and `finial_top` are clean.

### Known gaps

- Soffit and rafter faces are dropped only when every vertex is inside the keep-out, so that no sky path opens. One
  thin soffit-board edge and one cone rafter tail still show at each eave crossing (`n_soffit_up`, top centre).
- A few small dark notches remain beside the slope flashing where a unit was dropped (`actor_closeup`, above the
  junction).
- The end apron's `w_in` is not yet sized from the last remaining cone unit. It reads closed in the checks, but it
  is not adaptive.
- Nice-to-haves were not done: the stronger ridge-comb crest, `path_to_round`, the decal valley moss, moving the
  threshold lichen, and the course-tail hairlines.
- I did not make a second build to compare bit for bit. Every step is seeded.

## v3_longhouse_roundend round 3 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_03/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (88 anchors) and all 23 builder close-ups in `round_03/builder_checks/`.
- The recipe, `kit/changes/v3_longhouse_roundend.md` (round 3) and the round-3 module code
  (`composite.cone_roof(abut_roof=...)`, `cone_keep_out`, `drop_units`, `mesh_islands`, the new `GableRoof` solid
  methods, `_eave_rolls(end_caps=True)`, `_verge_faces(roll_cover=...)`, `ball_finial.hat_fit_units` / `fine_hat` /
  `hat_underside`).
- 33 director close-ups, 21 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_03/director_extra/` (d01-d30): both eave crossings from west and east
  at eye level and on a 100 mm lens, both soffit crossings looking up, both slopes from the crane, the ridge into the
  cone, a top-down, body wall into round wall (S and N), round wall head to cone eave, a round-eave look-up, both
  gable verge corners, the gable ridge end, the body eave over the door, the finial from four crane azimuths plus a
  close-up, the door, a round-end window, the gable footing corner, a back three-quarter, a mid-shot of the junction
  from the door approach, and 160 mm tele shots of both flashing ends (d28, d29) and the south soffit crossing (d30).
- A second full build to scratch, compared object by object with the delivered file.

**Determinism and compliance (director-verified).** The rebuild is geometry-identical: all 62 objects have the same
vertices (max difference 0.0) and the same 476,893 triangles, and `decal_anchors.json` is byte-identical (SHA-256
`8A6F98A6…`). The one difference is the face ORDER of `LONG_body_wall_stones` (same face set; this rebuild ran the
visibility cull single-process inside blender.exe, the builder's ran 4 processes). Every mesh has an identity
transform and a UV map, `Mask` is present and is both the active and the render colour attribute on every mesh,
and there are no zero-area faces. Stats: 476,893 tris, est_hidden 13.4 %, 10 palette slots, nothing in
`mask_attribute_missing`, 62 objects, 12.0 MB. The rebuild took 988 s here because the cull ran single-process;
the builder's 7 min 59 s with 4 processes is inside the art bible §8 limit.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: it is unmistakably the ref1 longhouse with a round end (low rubble body, layered thatch, 48 deg cone, ball finial on a 44 deg hat). The ridge comb is still weak next to ref1's strong crest. |
| 2 Proportion and actor scale | 8.8 | Unchanged: the door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is about 2.33 m, sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. |
| 3 Construction logic | 8.5 | The cone now yields to the thatch: its courses stop over the eave roll and the end apron, and nothing sits inside or under the roll (d01-d06). The hat no longer has a hub through it. Points off: at each crossing one thin soffit sheet cantilevers out over the thatch roll, carried by nothing (d07, d08, d30), and from the east the cut cone covering ends as a stacked, ragged edge (d03, d04). |
| 4 Seams and junctions | 8.2 | All three round-2 defects are gone. There is no shingle fan at either eave crossing, the free-gable roll ends are closed caps with no slot (d17, d18), and the hat is clean at four azimuths with no sky under it (d21, d22). All 21 red twins are closed. One small defect remains at both ends of the key junction: where the slope flashing sweep stops above the roll crest, its end is an open, crumpled lead tip, and beside it there is a dark void of about 0.25 x 0.08 m where `cone_keep_out` dropped units and nothing covers the gap (d28, d29). It reads as a dark notch at mid-shot from the door approach (d27) and in the official `actor_closeup`. The soffit sliver adds a little more. |
| 5 Distinctness and reuse | 8.8 | A genuinely new building type from a 91-line declarative recipe. The fix is the right kind of kit work. `GableRoof` now describes itself as a solid that any body can query, `drop_units` and `mesh_islands` are generic, `cone_keep_out` is the exact mirror of `linear_roof(abut_cone=...)`, and `hat_fit_units` tests units against the built hat. All are new keywords, the round-2 behaviour is still reachable, and the recipe changed by two arguments and one step order. The parallel duplicate modules still await the producer's merge. |
| 6 Technical compliance | 8.8 | 477k tris, 13.4 % hidden, 10 palette slots, `Mask` and UVs everywhere, identity transforms, no zero-area faces, no ground dressing, 88 decal anchors, and a geometry-identical rebuild. `DA_lichen_003`/`004` still sit on the threshold's walked top (third round). `LONG_cap_collar` is 12.3k tris, 57 % of them hidden (96-segment hat plus underside). |

**Verdict: 8.3/10, PASSED (pass mark 8.2).** The kit test the brief named is passed: a linear thatch roof and a
cone now each yield to the other through reusable keep-outs. The eave crossing is closed and logical from every
eye-level, look-up and crane view, with no see-through anywhere. Building 1 of the client-approved fallback list is
therefore proven buildable from kit modules. The grade is held at 8.3 by the junction axis: the small open flashing
tip and dark void at the bottom of each slope sweep, and the soffit sliver. All are module-level clean-ups in
`roof_junction` and `composite.cone_keep_out`, and every future round-end, tower-annex or turret junction gets the fix
for free.

**Strengths**
- `cone_keep_out` / `cone_roof(abut_roof=ROOF)` is a general mechanism, not a patch. The roof is a queryable solid
  (`keep_out`, `top_depth`, `eave_zone`, `under_soffit`), units are dropped whole (`drop_units`), never cut, and the
  same helpers can serve any body-meets-body junction in the kit.
- The eave crossing (the brief's key test) now reads as built: the cone courses finish over the thatch eave roll and
  the end apron, and nothing hangs below the soffit (d01-d06, red twins closed).
- `_eave_rolls(end_caps=True)` and `_verge_faces(roll_cover=...)` close the free-gable corners with no slot and no
  sky (d17, d18 and their red twins).
- `hat_fit_units` found and fixed the real cause of the round-2 hat creases (the rafter hub, not the shingles) by
  testing every unit vertex against the built hat. The hat is clean from four azimuths (d21).
- The recipe stays short and declarative, and every fix is a new keyword with the old behaviour reachable.
- Technically clean, with a geometry-identical director rebuild and a byte-identical decal JSON.

**Must-fix (next round on these modules)**
1. **`roof_junction.cone_abutment` sweep end, plus `end_apron`, at the lower end of both slope flashings.** This is
   at x ≈ 2.3, y ≈ ±2.85, z ≈ 2.9-3.0 m (after the recentre); see d28 and d29, which are visible in d27 and in
   `round_03/actor_closeup.png`.
   - What is wrong: the slope sweep (`ends="crest"`) stops 6 cm above the roll crest as an open, un-capped section
     that folds into a crumpled tip. Beside it is a dark void of about 0.25 x 0.08 m where `cone_keep_out` dropped
     cone units above the apron and nothing covers the gap.
   - What it should be: the sweep's lower end is closed with an end cap and laps at least 5 cm over the end apron,
     so it reads as one continuous lead piece from slope to apron.
   - The apron's cone-side width (`w_in`) is computed from the cone units that `cone_keep_out` actually kept, so the
     apron always runs under the last kept unit.
   - Alternatively, `cone_keep_out` lays a lead soaker under every dropped unit within 0.3 m of the junction line.
   - Either way, no dark void and no open lead end may be visible from the door approach or the crane.
   - Re-shoot d27, d28 and d29, plus red twins.
2. **`composite.cone_keep_out` on `LONG_roof_soffit_deck` (rule `"faces"`), at both soffit crossings.** This is at
   x ≈ 2.1-2.6, y ≈ ±(2.9-3.4), z ≈ 2.4-2.6 m; see d07, d08 and d30.
   - What is wrong: the slab's top, soffit and edge sheets are dropped face by face, independently. One thin soffit
     sheet is left cantilevering out over the thatch eave roll, single-sided and carried by nothing.
   - What it should be: treat the soffit slab as one unit per azimuth column (top, soffit and edge together). Drop a
     column when its centre lies inside the roof keep-out, and close the cut with an end face along the keep-out
     boundary. Alternatively, build `cone_soffit` with the roof keep-out passed in as `skip`.
   - No soffit board may reach past the round wall face into the body roof's zone.
3. **Decal anchors (producer note 11, plausible placement): `DA_lichen_003` and `DA_lichen_004`.**
   - They are at (-2.99 / -1.79, -2.81, 0.12), normal +Z: on the threshold slab's walked top, open since round 1.
   - Move them to the threshold's front riser or the door-jamb footing stones, or drop them.
   - Make `anchor_validate` exclude upward-facing threshold and step faces for `lichen` and `moss`.

**Nice-to-have (not blocking)**
- The cut cone covering seen from the east (d03, d04) ends as a stacked, ragged edge of plate ends. Add an even
  cut-line option (trim or align the last kept unit of each course parallel to the flashing), or lap a narrow lead
  skirt over the cut ends.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's crest, a silhouette change; open
  since round 1).
- Ridge roll free end (d19): a flat octagonal disc with a dark slot under it, and a small open triangle at the comb
  end. Give it the same rounded closed cap as the new eave-roll ends.
- Thatch course-tail hairlines in the back three-quarter (d26).
- `composite_hidden_cull`: sort the kept faces canonically, so the file is bit-identical whatever the process count.
- `LONG_cap_collar`: 64 hat segments would read the same with fewer hidden triangles.
- One clipped wedge stone above the south-east round-end window (d24).
- Carried over: the producer's merge of duplicate modules, `path_to_round`, a cylinder variant of
  `cone_abutment`, and valley moss / cone-drip `water_streak` anchors.


## v3_longhouse_roundend round 4 — builder entry

All fixes are kit-module keywords whose defaults keep the round-3 behaviour. They are in v3's own `composite.py` and
`roof_junction.py`, plus one shared module, `anchor_validate.py`. That module got new optional keywords (default off),
so the three heroes were re-run to scratch. Kit changes are recorded in `kit/changes/v3_longhouse_roundend.md`
(round 4 section). No surface-detail work was done (note 12).

- Recipe: three steps changed and one gate keyword was added. It is now 94 non-blank, non-comment lines.
  - `cone_roof(..., abut_trim=True, abut_soakers=True, soffit_cut=True)`
  - `cone_abutment(..., taper=0.12, apron=dict(w_in_kept=True, u_top=0.54))`
  - `DECAL_VALIDATE["walk_zones"] = "da"`
- Build: `v3_longhouse_roundend.blend` (12.0 MB) and `decal_anchors.json` (82 anchors). The full build took
  7 min 09 s under shared load.
- Renders: `renders/variants/v3_longhouse_roundend/round_04/` holds all six views (24 samples), `stats.json` and
  `hidden.json`. `round_04/builder_checks/` holds re-shoots of d03, d04, d07, d08 and d27-d30 with red twins, made
  with the director's round-3 cameras.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 478,877 (round 3: 476,893) |
| est_hidden_pct | 13.8 % (round 3: 13.4 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 63 (new: `LONG_cone_soakers`) |

### Fixes

1. **Sweep end and void (hard requirement): `cone_abutment(taper=...)`, `end_apron(w_in_kept, u_top)` and
   `cone_keep_out(soakers=True)`.**
   - Cause: in the band where the cone surface runs under the thatch roll's top, both roofs yield. The thatch is
     clipped under the cone and the cone units are dropped inside the thatch solid, which left a pit. The round-3
     crumpled tip came from the last 3 sweep stations: there the junction turns over the roll plateau, the roof
     normal swings about 45 deg and the section twists.
   - Sweep end: the sweep now ends where the roof normal still follows the slope (stations more than 25 deg off are
     dropped). Its section closes over the last 0.12 m into a domed ring 3 cm past the end, so the end is closed
     lead with no open section.
   - Apron: it now runs 0.54 m up the roll tail (7 rows), under the sweep end, so the two lap by about 7 cm. Its
     cone-side `w_in` is computed per row from the cone units the keep-out actually kept (0.12-0.41 m south,
     0.12-0.32 m north).
   - Soaker: `cone_soakers` lays ONE closed lead soaker slab on the cone's reference surface under every unit
     dropped within 0.30 m of the roof top (40 units, each footprint grown by 3.5 cm).
   - Result: the pit now shows lead, not a dark void. The black slot is gone from `round_04/hero.png`,
     `actor_closeup.png` (px 800-850, 170-190) and `back.png`, and from d27, d28 and d29.
2. **Soffit crossing: `cone_soffit(cut=roof keep-out)` via `cone_roof(soffit_cut=True)`.**
   - The slab is built as whole azimuth spans. Each span's ends are refined per slope row by bisection onto the
     keep-out boundary, and each span is closed with top, soffit, eave edge and an end face at each cut.
   - No single-sided sheet is left and no board lies inside the roof's zone. The d30 and d07/d08 cantilevered sliver
     is gone.
3. **Decal anchors (note 11).**
   - `composite_decals(door_lichen="jamb")` puts the door lichen on the footing stones beside the jambs. They are now
     `DA_lichen_003` / `004` at (-3.51 / -1.27, -2.75, 0.24) with a -Y normal, so they are not on the threshold.
   - `south_moss=False` puts thatch moss on the north (+Y) slope only. Every thatch moss anchor now has y > 0.
   - `anchor_validate.validate_anchors(walk_zones="da")` (new, shared, default off) rejects lichen and moss on
     upward faces inside each door's trodden zone (`decal_gate.door_walk_zone`, reused unchanged). This build
     rejected nothing, because nothing is generated there any more.
4. **Even cut line (east, d03/d04): partly done.**
   - `trim_units` and `roof_eave_planes` (new kit helpers) cut units that cross the roof solid's eave plane on that
     plane and cap them, instead of dropping them whole: 8 shingles, 4 starters, 5 under-laps and 8 battens.
   - The ragged stack seen from the east is mostly NOT at that plane. It is the cone's eave courses that the keep-out
     keeps because they sit above the roll top, where the cone eave oversails the thatch. Each course ring meets the
     roll at a different azimuth. The soaker now backs the wedges with lead, but the stepped stack still reads in
     d03/d04 and the d07/d08 look-ups.

### Hero re-runs (anchor_validate changed; scratch outputs)

| hero | reference | round-4 re-run (scratch) | delta |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 | 0 |
| wattle_roundhut | 876,619 | 878,355 | +0.20 % (inside +/-0.5 %; `anchor_validate` changes no geometry, so this is not from this change) |
| tower_windmill | 1,146,243 | 1,146,243 | 0 |

### Known gaps

- Item 2 of the audit is not finished: the stepped course ends over the roll from the east (d03, d04). The fix would
  be a second cut surface: trim the oversailing courses against the roof TOP (not the eave plane) near the eave band,
  or lap a lead skirt over them along the lower junction line. `cone_abutment(sweep_end="plane", fit_kept=True)` was
  tried and left in the kit as options, but the resulting skirt read as a folded flap, so the recipe does not use it.
- d29 (north, 160 mm tele) still shows one small dark slot beside a trimmed shingle at the cone side of the
  flashing. It does not show in the six review views.
- `cone_soakers` covers the whole slope junction (most of it under the thatch, and the cull removes 1,325 of its
  1,717 polygons). Hidden is 13.8 %.
- I did not make a second build to compare bit for bit. Every step is seeded.

## v3_longhouse_roundend round 4 — score 8.6/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12). Note 13 (no LED volume; the client's desktop is the reference
machine) changes nothing in this grade.

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_04/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (82 anchors) and all 16 builder re-shoots in `round_04/builder_checks/`.
- The recipe (94 lines, every step a `village_kit` import), `kit/changes/v3_longhouse_roundend.md` (round 4) and the
  round-4 module code (`composite.cone_soakers`, `trim_units`, `roof_eave_planes`, `_island_vertex_sets`,
  `cone_keep_out(trim, soakers, soffit_cut)`, `cone_soffit(cut=...)` / `_soffit_spans`, `roof_junction.end_apron
  (w_in_kept, u_top)` / `kept_cover_points`, `cone_abutment(taper)`, `anchor_validate(walk_zones)`).
- 48 director close-ups, 25 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_04/director_extra/`: the round-3 set d01-d30 re-shot on the round-4
  file, plus new d31/d32 (both eave crossings from the east at 9 m, the mid-shot an actor walk-by sees), d33/d34
  (both slope-flashing lower ends from the crane on a 110 mm lens, the soaker zone), d35/d36 (the east stack on a
  120 mm lens), d37 (threshold and jamb footing), d38/d39 (the free gable and the ridge-roll end at eye level).
- A second full build to scratch, compared with the delivered file.

**Determinism and compliance (director-verified).** The rebuild is geometry-identical: the same 63 objects, 478,877
triangles and vertex hash (`ad0b6892…`), and a byte-identical `decal_anchors.json` (SHA-256 `1E858AC5…`). Every
unique mesh has an identity transform and a UV map (the 28 pegs are linked duplicates of 5 pooled meshes); `Mask` is
present and is both the active and the render colour attribute on every mesh; there are no zero-area faces; the
collections are `LONG`, `LONG_kit_instances` and `DECAL_ANCHORS`. Stats: 478,877 tris, est_hidden 13.8 %, 10 palette
slots, nothing in `mask_attribute_missing`, 12.0 MB. The rebuild took 7 min 32 s here, with director renders on the
GPU at the same time.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: unmistakably the ref1 longhouse with a round end (low rubble body, layered thatch, 48 deg cone, ball finial on a 44 deg hat). The ridge comb is still weak next to ref1's strong crest, and the ridge roll ends in a flat faceted disc against the sky at the gable (d38). |
| 2 Proportion and actor scale | 8.8 | Unchanged: door 1.00 x 2.10 m on a 12 cm threshold, eave lip over the door about 2.33 m, sills at 1.20-1.30 m, round-end eave at 2.30 m. |
| 3 Construction logic | 8.5 | The soffit sliver is gone: the boarded soffit now stops on the thatch boundary as whole closed spans (d07, d08, d30). The slope flashing now reads as one lead piece from slope to apron (d27, d28, d33). Points off: from the east the cone's eave courses over the thatch roll still end as a stepped stack of plates at actor distance (d03, d04, d35, d36), and the round end's pegged wall plate and all 28 pegs are now fully buried behind the soffit (100 % hidden in `hidden.json`), so a built module carries nothing visible. |
| 4 Seams and junctions | 8.5 | The round-3 hard requirement is met: no dark void and no open or crumpled lead tip at the lower end of either slope flashing (d27-d29, d33, d34; all red twins closed), and nothing shows in the official `actor_closeup`, `hero` or `back`. Every red twin across the 25 checks is closed. Remaining: the stepped east stack (closed, lead-backed, but cluttered at 5 m; at 9 m, d31/d32, it reads as a laced shingle valley and is acceptable); one small dark pocket beside a trimmed shingle at the north flashing (d29, d34, d06, tele only); and the ridge-roll free end (a flat octagonal disc with a dark slot under it, d19, d38, d39), open as a nice-to-have since round 3. |
| 5 Distinctness and reuse | 8.8 | A genuinely new building type from a 94-line declarative recipe. All round-4 geometry landed in kit modules as new keywords whose defaults keep round 3: `cone_soakers` and `trim_units` are generic (any mesh, any planes, any GableRoof), and `cone_soffit(cut=...)` takes any keep-out function. Points off: `cone_roof` has grown to 12 keywords, two options were left in the kit unused (`cone_abutment(sweep_end="plane")`, `fit_kept=True`), and `roof_junction.end_apron` now shares its name with the unrelated `junctions.end_apron`. The producer's merge of the parallel junction modules is still pending. |
| 6 Technical compliance | 8.9 | The rebuild is geometry-identical with a byte-identical decal JSON. 479k tris, 13.8 % hidden, 10 palette slots, `Mask` and UVs everywhere, no ground dressing, and 82 plausible anchors. The door lichen is now on the jamb footing stones (-Y normals), and the shared gate `walk_zones` is opt-in, so heroes are untouched. Build 7 min 09 s (builder) / 7 min 32 s (director, under load). Small points off: the wall plate and 28 peg objects are 100 % hidden, against note 1 ("nothing modelled that will never be seen"); and five thatch moss anchors carry a straight-up normal on a 40 deg slope. |

**Verdict: 8.6/10, PASSED (pass mark 8.2).** This round fixes all three round-3 must-fixes at module level, and the
key junction the brief names now holds from every eye-level, look-up and crane view:
- the slope flashing ends closed and laps the apron;
- a lead soaker backs every dropped unit;
- the soffit stops cleanly on the thatch;
- no see-through remains anywhere.

The rebuild is bit-identical. Building 1 of the client-approved fallback list is proven from kit modules, now with
cleaner seams than round 3 (8.3 -> 8.6).

Grade limits:
- The east-side stepped stack, still visible at close range.
- The ridge-roll end at the free gable.
- A built-but-invisible wall plate.

All three are module clean-ups that every future round-end, tower-annex or turret junction will inherit.

**Strengths**
- `cone_soakers` is the right kind of kit fix. Any body that yields to another backs its dropped units with one
  closed lead slab, so a keep-out can never open a dark void. It is generic over any GableRoof and is culled to 392
  visible polygons.
- `cone_abutment(taper)` together with `end_apron(u_top, w_in_kept)` makes the slope flashing one continuous, closed
  lead piece that laps the apron. The apron is sized from the units that were actually kept, so it adapts to any cone
  and roof combination (d27, d28, d33).
- `cone_soffit(cut=...)` builds the soffit as whole closed spans that stop on any keep-out boundary, with end faces.
  There are no single-sided sheets (d07, d08, d30, and their red twins are closed).
- `trim_units` and `roof_eave_planes` give the kit a general "cut on a plane and cap" helper alongside
  `drop_units`, for any unit mesh.
- Decal logic is now physical. Door lichen sits on the jamb footings, and moss is limited to the north slope. The
  shared gate's `walk_zones` is opt-in, so the heroes are unchanged.
- The recipe changed by three arguments and one gate keyword, and every fix is a keyword with round-3 behaviour still
  reachable. The rebuild is geometry-identical with a byte-identical decal JSON.

**Must-fix (next round on these modules; not blocking this pass)**
1. **`composite.cone_keep_out` / `trim_units`: the oversailing eave courses at both eave crossings, seen from the
   east.** This is at x ≈ 2.0-2.7, y ≈ ±(2.9-3.4), z ≈ 2.45-2.85 m (after the recentre); see d03, d04, d35 and d36.
   - What is wrong: the cone's lowest 3-4 courses that oversail the thatch eave roll are kept whole, because they sit
     above the roll top. Each course ring meets the roll at a different azimuth, so from the east at 5 m they end as a
     splayed, stepped stack of plate ends with dark slivers between them. It is closed and lead-backed, but cluttered.
   - What it should be: a second trim surface, `trim_units` against the GableRoof's TOP surface offset by `lift`
     within the eave band (`GableRoof.eave_zone`), for example `roof_top_planes(roof)` or a top-surface cut function.
     Every kept course should then end on one line that follows the roll's top, with capped cut ends that rest on
     the soaker or apron.
   - Do not use the folded-flap skirt.
   - Re-shoot d03, d04, d35 and d36 with red twins.
2. **`linear_roof` ridge roll, free (west) gable end.** This is at x ≈ -8.9, y ≈ 0, z ≈ 4.9-5.2 m; see d19, d38 and
   d39.
   - What is wrong: the ridge roll ends in a flat, faceted octagonal disc that oversails the verge face, with a thin
     dark slot under it. It reads against the sky from the gable approach at eye level.
   - What it should be: the same rounded, closed end cap the eave rolls got in round 3 (`_eave_rolls(end_caps=True)`),
     for example `_ridge_roll(end_caps=True)`. Its end should be flush with or no more than 5 cm past the verge face,
     and the verge face's top envelope should cover the roll's underside, so there is no slot.
3. **`composite.cone_soakers` and `trim_units`: the north flashing pocket.** This is at x ≈ 2.3, y ≈ +2.85,
   z ≈ 2.9-3.0 m; see d29, d34 and d06.
   - What is wrong: a dark pocket about 5 x 5 cm sits beside a trimmed shingle at the cone side of the flashing. The
     soaker's footprint is built from the DROPPED units only, so a unit that `trim_units` cut has no lead under its
     cut end.
   - What it should be: `cone_keep_out(soakers=True)` passes the trimmed units' removed parts (or their cut caps) to
     `cone_soakers` as footprints too, so lead runs under every cut or dropped unit within `reach`. No dark pocket may
     remain beside any trimmed unit.
4. **`round_wall.wall_plate` under `composite.cone_soffit` (note 1, nothing modelled that will never be seen).**
   - What is wrong: `LONG_wall_plate` (598 tris) and all 28 `LONG_peg_*` objects are 100 % hidden in
     `round_04/hidden.json`. The boarded soffit slab runs to 7.5 cm inside the plate line and buries them.
   - What it should be, either of:
     - `cone_soffit(r_in=...)` stops at the plate's outer face, so the plate and its pegs read under the eave from
       eye level (preferred: it is better construction logic);
     - or `wall_plate(pegs=False)` / a recipe flag that skips the plate and pegs when a soffit covers them.
   - Either way, no object may be 100 % hidden.

**Nice-to-have (not blocking)**
- Ridge comb: a crest at least 0.3 m proud of the ridge roll (ref1, silhouette; open since round 1).
- Thatch course-tail hairlines along several butts in the back three-quarter (d26; open since round 2).
- Decals:
  - `DA_moss_006/008/010/013/015` (thatch, y = 1.37) carry a (0, -0.03, 1.00) normal on a 40 deg slope. Snap the
    projection to the slope normal.
  - The `water_streak` under the cone eave drip and the valley moss promised by `composite_decals` are still absent.
- Kit hygiene:
  - Remove or document the unused `cone_abutment(sweep_end="plane")` and `fit_kept` options.
  - Rename `roof_junction.end_apron` (it clashes with `junctions.end_apron`).
  - Consider a `cone_roof(abut=dict(...))` sub-spec instead of 12 flat keywords.
- The small lead nub where the sweep's domed end ring shows at 100 mm (d06) could be flattened into the apron.
- Carried over for the producer:
  - merge the duplicate junction, opening and body modules;
  - add `path_to_round`;
  - add a cylinder variant of `cone_abutment`;
  - give `composite_hidden_cull` a canonical face order.
- The producer should confirm the wattle_roundhut +0.20 % drift in the builder's hero re-run has its own cause, as the
  builder says. `anchor_validate` changes no geometry.


## v3_longhouse_roundend round 4 — sign-off audit: REJECTED

Blocking issues (independent audit, copied by the producer from the workflow record):
- Seams and junctions are overgraded, and so is the overall score. The six official views (hero, front, side, back, aerial, actor_closeup) are clean, and every red twin is closed. But the director_extra close-ups show visible clipping and gaps at the brief's key junction. I score seams about 8.0 and construction about 8.2, not 8.5 and 8.5. The rubric overall is roughly the lowest axis, so this lands at about 8.0-8.1, under the 8.2 pass mark. The 8.6 is also inconsistent with round 2: there the same class of defect (a splayed shingle fan at the eave crossing) capped seams at 7.9.
- Hard requirement, clipping at the key junction: the east side of both eave crossings (composite.cone_keep_out / trim_units). Location: x 2.0-2.7, y +/-(2.9-3.4), z 2.45-2.85 m. In d03 and d04 (eye level, about 5 m away, about 4.7 m from the main door, inside the close-up priority zone of note 4) and in d35 and d36, the cone's lowest 3-4 oversailing courses end as a splayed jumble. Plates sit at different angles and trimmed caps are embedded in neighbouring plates; on the north side (d04) plate ends hang down beside the thatch eave roll. This is visible interpenetration, not just clutter. Fix it at module level: add a second trim against the GableRoof TOP surface inside eave_zone (e.g. roof_top_planes(roof) or a top-surface cut function), so every kept course ends on one line along the roll top with capped ends resting on the soaker or apron. No folded-flap skirt. Re-shoot d03, d04, d35 and d36 with red twins.
- Hard requirement, visible gaps beside the north slope flashing (composite.cone_soakers + trim_units). d29 and d34 show a dark pocket of about 5 x 5 cm beside a trimmed shingle at x 2.3, y +2.85, z 2.9-3.0 m. The top-down d12 shows another dark slot beside the north flashing near the ridge (around px 720,265). The cause: soakers are laid under DROPPED units only, so a unit that trim_units cut has no lead under its cut end. Fix: pass the trimmed units' removed parts (or their cut caps) to cone_soakers as footprints, so lead runs under every cut or dropped unit within reach.
- Hard requirement, visible gaps at the free (west) gable, linear_roof ridge-roll end and verge apex. Location: x -8.9, y 0, z 4.9-5.2 m. The ridge roll ends in a flat faceted octagonal disc that oversails the verge face, with a dark slot under it, seen against the sky from the eye-level gable approach (d19, d38, d39). There is also a small dark hole at the verge apex where the two verge faces and rafters meet (d39 around px 660,512; d38 around px 640,298). Fix: add _ridge_roll(end_caps=True), a rounded closed cap flush with or no more than 5 cm past the verge face, and extend the verge face's top envelope so it covers the roll underside and closes the apex.
- Technical compliance (note 1: nothing modelled that will never be seen; note 6): LONG_wall_plate (598 tris) and all 28 LONG_peg_* objects are 100% hidden in round_04/hidden.json, buried behind cone_soffit. A kit module that is built but never seen fails both construction logic and note 1. Fix: preferably cone_soffit(r_in=<plate outer face>), so the plate and pegs read under the eave from eye level. Otherwise use a wall_plate(pegs=False) / skip-when-soffit flag. No object may be 100% hidden.
- Construction logic in the soffit look-ups at both crossings (d07, d08): body rafter-tail blocks butt into and overlap the round wall's face stones. A loose thin curved stick pokes out of the deck edge into the dark slot between the body deck and the round wall head (d08, around px 1100-1190, 320-360). The linear_roof rafter tails should be clipped at the round wall face, using the same inside_round clip the walls use, and stray slivers removed.

## PRODUCER NOTE (2026-10-17) — closing round on kit 1.10.1

The kit has since been consolidated (1.8.0), the guard-rails turned on (1.9.0), the UV fix applied (1.10.0) and needle repair made deterministic (1.10.1); see kit/CHANGELOG.md and the rewritten README. Round 5 fixes every blocking issue above that still applies, on the current kit, and stays at or under 1,000,000 triangles (note 15). Kit edits to existing modules must keep every other building's geometry hash (HASH RULE).

