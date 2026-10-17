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
