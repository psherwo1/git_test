
## Round 1 (builder report): full asset built from scratch
- Script: `buildings/wattle_roundhut/build_wattle_roundhut.py` (deterministic: the geometry hash is identical across reruns; the build takes about 6 s). Output: `buildings/wattle_roundhut/wattle_roundhut.blend` (23.8 MB, compressed).
- Renders: `renders/wattle_roundhut/round_01/` (all 6 views at 32 samples, plus stats.json).
- Stats: 1,215,014 tris, 23 objects in collection `HUT`. bbox min (-4.55, -6.16, -0.094), max (4.62, 4.72, 8.60). size_m 9.17 x 10.88 x 8.69. Materials: M_daub, M_earth, M_iron, M_lead, M_roof_shingle, M_rubble, M_stone, M_timber, M_timber_weathered, M_wattle.
- Built:
  - Plinth: 40 sub-angular plinth boulders, plus pinning stones and chinking.
  - Posts: 14 round-hewn posts with lean, taper and adze flats, some with drying checks.
  - Wattle: real woven rods around stakes, about 580k tris, with taper, pairs, split rows with flicked stub tips and a drifting field.
  - Daub: an eroded bay left of the door, a full bay at the back right and a partial patch on the +X side. There is also a daubed inner skin.
  - Wall plate: 7 half-lapped segments with pegs.
  - Door frame: projecting, flat-fronted frame with jambs, lintel on the door posts, wattle side and cheek panels, tie beams, pegs and a boarded tympanum.
  - Threshold and path: a worn sill on a threshold stone, a step stone (top 0.09) and 7 flagstones.
  - Door leaf: 6 boards with ledges, a brace, latch and keeper, open 75 deg inward. Ironwork: strap hinges with spear ends, nails, pintles and a ring pull.
  - Roof structure: 28 pole rafters, with every 5th end split and the tips uneven. Also purlin rings, batten rings and a hub.
  - Shingles: 17 courses of individually modelled shingles with a doubled starter. They are tapered to the cone and include slipped, split and missing ones.
  - Apex: lead-hat collar with 10 standing seams and a drip roll, an upper collar, and a turned finial with a spike tip at 8.60.
  - Ground: earth apron with a drip-line trench, plus rubble.
  - Interior: floor and hearth.
- Key dimensions:
  - Eave lip about 2.42 (2.40 or more over the door).
  - Plate 2.66-2.86.
  - Door clear opening 1.00 x 2.08 from the sill (sill top 0.20, head 2.28).
  - Collar base dia 1.46 at z 6.72.
- Deviations from the spec numbers, and why:
  - Course exposure is 0.318 m. The spec's 17-19 courses at 0.36-0.40 do not fit the 5.4 m slope between the eave (r 4.13) and the collar (r 0.73) at 51 deg.
  - The collar sits 0.17 m higher than the spec says (drip at 6.72, not 6.55). A 44 deg collar has to clear a 51 deg shingle cone.
  - The lintel is 2.3 m long so that it sits on the door posts with 0.21 m side panels.
  - Plate top is 2.86, not 3.05, because the rafters seat on the plate with the eave lip held at 2.42.

## Round 1 — score 7/10

**Director review.** I reviewed all 6 views and stats.json in `renders/wattle_roundhut/round_01/` side by side with `hut_overall`, `hut_door`, `hut_wattle_daub_plinth` and `hut_cap_finial`. I also rendered 8 extra close-ups (apex, apex_side, profile, eave_under, daub_bay, door_front, wattle_macro, plinth) into `round_01/director_extra/` and measured the evaluated meshes.

**Verdict.** This is a strong first round and a complete, well-engineered asset.
- The overall cone/wall/plinth massing overlays ref2 closely. Roof + finial to wall height is about 2.3 (ref 2.4) and eave width to roof height is 1.34 (ref 1.36).
- Actor scale is correct.
- The shingle cone is genuinely good.

Four things hold it at 7:
- The apex reads wrong at every distance (collar too short and shallow, needle spike).
- The wattle reads as a fine, regular basket mat or screen rather than ref2's coarse open weave.
- The plinth stones are uniform pillowy loaves (the strongest CG tell in the actor close-up).
- The daub panels read as flat boards.

Axes:
- Silhouette 7 (apex).
- Proportion and scale 8.
- Construction 8.
- Detail and craft 7.
- Age 7.
- Technical 8 (apron seam artefact, extra `M_earth` slot).

**Strengths**
- The silhouette and massing match ref2: squat round wall on a plinth under a huge 51° cone. The convex profile, eave kick and eave wobble all read.
- **Shingles are hero quality.** About 690 individually modelled chunky shingles with thickness, cup, curl, stagger, slips and missing pieces. The profile render looks right, and they read at about 0.45 m next to the figure.
- **Scale is correct.** Clear door 1.00 x 2.08, eave lip 2.42 over the door, head clearance for the 1.8 m figure, and sensible step risers.
- **The roof structure reads from below.** Rafter pole ends (some split), battens in the eave gap, the plate and real eave thickness are all visible.
- **The door assembly is complete.** Projecting flat-fronted frame, leaf open 75° inward with ledges, brace and strap hinges, sill on a threshold stone, step stone and flag path. The interior reads dark and deep, with rafters, purlins and the hearth visible through the door. There is no sky void.
- **The wattle is real woven tube geometry.** In/out alternation is visible, the daub's eroded lower edge exposes it, and the bay placement matches ref2.
- **Technical work is clean.** Deterministic 6 s build, identity transforms, UVs, named slots, 1.215 M tris, 23.8 MB.

**Spec amendments (these supersede spec §H/§I and the art bible §1.5 "44°" for this hut).** I re-measured the reference crops (`hut_overall`, `hut_cap_finial`):
- **Lead-hat collar pitch.** It runs at the same pitch as the roof or slightly steeper (about 51–55°), not shallower.
- **Collar height.** The lower collar is about 0.65 m tall from the drip to a top Ø of about 0.5 m.
- **Upper collar.** It is a separate bell cone, base Ø about 0.55 m, with its own drip, about 0.3 m tall.
- **Finial.** It is chunky: spindle Ø up to about 0.2 m, and the spike base about 0.14–0.16 m Ø.
- **Wattle row pitch.** It is about 6–8 cm in ref2 (rods about 2.5–3.5 cm with dark gaps between rows), not 3.5–4 cm.
- **Shingle exposure.** The builder's 17 courses at 0.318 m exposure is ACCEPTED, because the spec's 0.36–0.40 cannot fit the 5.4 m slope.
- **Other accepted deviations.** The plate at 2.66–2.86, the 2.3 m lintel and `M_earth` are also accepted.

**Must-fix (priority order)**

1. **APEX COLLAR + FINIAL (silhouette; HUT_cap_collar, HUT_finial).**
   - *Problem:* the lower collar rises only 0.35 m (z 6.66 → 7.01, r 0.765 → 0.40) at 44°. Above it, the "upper collar" is a flat drum ring (r 0.40, 5 cm tall) plus a low cone. In hero, front and side the lead hat is invisible at thumbnail and merges into the shingle cone. In ref2 it is the second most recognisable feature.
   - *Lower collar:* rebuild it as a smooth cone at about 52–54°, drip edge at about 6.60 with base Ø 1.45–1.50, rising to z ≈ 7.25 with top Ø ≈ 0.50.
   - *Drip edge:* give it a vertical fascia 5–7 cm deep that stands 8–10 cm off the shingle surface, so a hard shadow line reads at 30 m. Keep the rolled lip, the slight dents and the 10 seams.
   - *Upper collar:* replace the drum + cone with a bell-cast cone, base Ø 0.55 at z 7.25 with a 4–5 cm drip overhanging the lower collar's top, rising to about 7.55 (top Ø about 0.16).
   - *Finial:* a turned spindle 7.55 → 7.95, with a bead ring Ø 0.20, a neck Ø 0.10 and a vase bulb Ø 0.18. Then a sharp conical spike from Ø 0.14–0.16 at 7.95 to a point at 8.60 (tip r ≤ 5 mm; currently r 0.021). The spike is currently a needle (r 0.05 → 0.02) that vanishes at distance.
   - Keep the 1° lean.

2. **WATTLE WEAVE READS AS A FINE MAT (HUT_wattle_rods; all bays and door side panels).**
   - *Problem:* row pitch is r_row + r_next (about 2.1–3.5 cm), so the rods touch and the wall reads as a regular screen in hero, side and back, and like a basket in close-up.
   - *Rows:* change to a row pitch of 6–8 cm (±1.5 cm random), with rods Ø 2.4–3.6 cm, so dark gaps of 2–4 cm show between rows as in `hut_wattle_daub_plinth`.
   - *Rods:* increase vertical drift to ±3 cm over 1 m (low-frequency noise per rod, not a shared field), add knots or kinks (Ø +15% bumps every 0.3–0.6 m) and a slight non-circular (oval/knobbly) section. About 15% of rows should be paired or tripled.
   - *Weave depth:* keep the in/out amplitude at ±2.5–3 cm.
   - *Budget:* this should also free about 300k tris; spend them on items 3–5.

3. **PLINTH STONES ARE PILLOWY LOAVES (HUT_plinth_stones, HUT_plinth_chinking, HUT_ground_rubble, step stone).**
   - *Problem:* all 40 boulders are similar rounded boxes (r_frac 0.3–0.5, D 0.40–0.52, nearly all full plinth height). They read as marshmallows or teeth in a ring (actor_closeup, director_extra/plinth.png).
   - *Shape:* make them sub-angular. Corner rounding should be 2–4 cm (r_frac 0.08–0.18), with 3–6 large flat fracture facets per stone and flatter bedding faces.
   - *Size and height:* vary heights 0.18–0.42. About 40% should be two-high (a big flat lower stone 0.15–0.25 tall plus a flatter upper stone or slab), and lengths should vary 0.25–0.85. Include 2–3 long through-stones.
   - *Faces:* the outer faces should form a rough wall line (±4 cm) with stones in contact, not a row of separated blobs.
   - *Chinking:* the chinking pieces currently stick out between stones as flat tabs. Recess them 2–5 cm behind the adjacent faces and make them wedge-shaped.
   - *Rubble and step stone:* apply the same sub-angular treatment. The step stone currently reads as a pillow/pill disc: give it a flat, slightly dished top with chipped edges and bury it 3–4 cm.

4. **DAUB READS AS FLAT BOARDS (HUT_daub; large bay left of the door, back-right bay, side patch).**
   - *Problem:* lumps are about ±1 cm at a 0.45 m wavelength, and in clay the panels read as planar sheets (daub_bay, back, side).
   - *Bulges:* add low-frequency bulges of 2.5–4 cm amplitude at 0.4–0.8 m wavelength, following the rods beneath (a faint horizontal ridging of 0.5–1 cm at the 6–8 cm rod pitch where the daub is thinner).
   - *Surface:* add hand-pressed trowel or palm smears of 0.5–1 cm and 3–6 shrinkage cracks per bay (0.3–0.8 m long, 0.5–1 cm wide, 1–2 cm deep).
   - *Edges:* chip the edges where the daub meets the posts, with no clean vertical cut lines. On the eroded lower edge, vary the break height by ±12 cm (currently it reads nearly straight) and leave 2–3 detached clumps clinging to the rods.

5. **ENTRANCE TIMBER IS CG-CLEAN (HUT_door_frame, HUT_posts).**
   - *Problem:* in door_front the door posts, jambs and cheek members read as straight, smooth extruded boxes. The 14 round posts read as smooth tubes in daub_bay.
   - *Frame members:* add visible hewing: adze facets 4–8 cm wide and 3–6 mm deep, wane (bark-edge rounding) on 1–2 arrises of the door posts, ±8 mm width swell along the length, and 2–3 drying checks (3–6 mm wide, 15–40 cm long) on the two door posts.
   - *Lintel and pegs:* show end-grain checks at the projecting lintel ends, and make the pegs proud 1.5 cm.
   - *Round posts:* give them 6–10 visible adze flats (5–8 mm deep) and a knot or two.

6. **DOOR SIDE WATTLE PANELS READ AS LADDERS (HUT_door_frame side panels).**
   - *Problem:* each 0.21 m panel has rods crossing a single central stake, so it looks like rungs.
   - *Fix:* use 2 stakes per panel and the coarser woven rods from item 2. Alternatively, follow `hut_door.png`, which shows a diagonal, rope-like twisted weave in those narrow panels.

7. **APRON SEAM ARTEFACT (HUT_ground_apron).**
   - *Problem:* the apron's outer rim at r about 4.74 sits about 2 mm above the review ground plane, and renders as a dashed or z-fighting ring (actor_closeup, director_extra/plinth.png).
   - *Fix:* give the apron a flat outer band at least 0.4 m wide at exactly the bbox-min level, so the rim is coplanar and hidden, or tuck the rim under the plane by feathering it.
   - Keep M_earth (accepted).

**Nice to have**
- Standing seams on the collar: make them folded seams (a 6–8 mm raised fin with soft fillets) instead of round rods.
- Shingle butts: more raggedness (2–3 notches per butt, ±1.5 cm), and a few more cracked/split shingles near the eave on the door side.
- Path flagstones: bed them 3–5 cm into the apron (they currently sit on top), with tufts of apron height between them.
- Optional low-poly moss cushions at the collar drip and a few eave butts.
- Door leaf: a little more visible ironwork scale. Hinge straps should be 45–55 mm wide so they read in actor_closeup.

## Round 2 (builder report): all 7 must-fix items + nice-to-haves
- Script: `buildings/wattle_roundhut/build_wattle_roundhut.py` (deterministic; geometry hash identical across reruns; build ~6 s). Output `buildings/wattle_roundhut/wattle_roundhut.blend` (29.3 MB compressed).
- Renders: `renders/wattle_roundhut/round_02/` (all 6 views, 32 samples, stats.json).
- Stats: 1,465,554 tris, 23 objects. bbox min (-5.10, -6.12, -0.095), max (5.11, 5.21, 8.71); size_m 10.20 x 11.33 x 8.81. Materials unchanged (M_daub, M_earth, M_iron, M_lead, M_roof_shingle, M_rubble, M_stone, M_timber, M_timber_weathered, M_wattle).
- Changes:
  1. Apex: lower collar is a smooth 53 deg cone, drip dia 1.49, 6.5 cm vertical drip fascia with rolled bead standing ~8-10 cm off the shingles, 10 folded standing-seam fins (7.5 mm, filleted). Upper collar: bell-cast cone dia 0.57 with its own 4.5 cm drip. Spindle: seat, bead ring dia 0.20, neck 0.10, vase bulb 0.18, top ring (0.385 tall, M_timber). Spike: conical dia 0.15 -> tip r 1.2 mm (M_iron). 1 deg lean kept. Heights: drip 6.705, fascia top 6.77, lower collar top 7.43, upper 7.73, spindle 8.11, tip 8.71.
  2. Wattle: row pitch 5.8-7.8 cm, rods dia 2.7-3.6 cm (2-4 cm gaps), per-rod drift (+-3 cm/m), knots (+15 % dia every 0.3-0.6 m with extra rings), kinks, oval knobbly 6-side section, ~15 % paired/tripled rows. 411k tris. Inner daub skin moved 8 cm behind the wattle line so gaps read recessed/shadowed.
  3. Plinth: new `rock()` primitive (2-segment 2-4 cm rounding, 4-7 filleted fracture facets, broken outer faces, flat beds, batter). 37 bays: 12 single, 13 two-high, 9 low+pinning slabs, 3 through-stones with uppers (43 % two-high). Faces on a +-2 cm wavy line, stones in contact; wedge chinking recessed 2-7 cm. Rubble, door-post pads and threshold stone are sub-angular too. Step stone: thin chipped slab with wear-dished top, earth banked round it (~5 cm proud).
  4. Daub: 0.75 cm grid front coat; 2.5-3.5 cm bulges at ~0.6 m, patchy 0.5-0.7 cm rod ridging where thin, curved palm smears, 4-6 shrinkage cracks/bay (snapped V grooves 0.5-1 cm wide, 1-2 cm deep, some branched), ragged chipped margins at the posts, eroded edge 0.51-0.78 m (+-13 cm) with 3 clinging clumps.
  5. Entrance timber: `hewn_member()` for door posts, jambs, lintel, tie beams, sole rails: adze strokes in 2-3 skewed lanes per face (4-8 cm, 3-6.5 mm), +-8 mm swell, wane on 1-2 arrises, 2-3 drying checks per door post (4-6 mm, 15-40 cm), end-grain checks at lintel/tie-beam ends, whittled octagonal pegs proud 1.5-1.8 cm, 28 deg auto-smooth so ridges read. Round posts: 48 sides, 6-10 long adze flats 5-8 mm (15 deg sharp edges so they read), 1-2 branch-stub knots, narrow V drying checks.
  6. Door side panels: 2 stakes each, steep diagonal rope-like weave (slant 0.85) as in hut_door.png; cheek panels 2 stakes, slant 0.6.
  7. Apron: polar mesh with a >= 0.4 m flat outer band at exactly the bbox-min level (Z -0.095), irregular soil margin (no grid stair-steps). A hairline remains where the band edge sits 2 mm above the review plane (the review plane is always 2 mm below bbox min, so no edge can be coplanar).
- Nice-to-haves: folded seams done; shingle butts ragged (per-column offsets, 2-3 notches, skew +-1.2 cm) plus extra split shingles in the 4 eave courses on the door side; flags bedded 0.6-2 cm proud; hinge straps 52 mm x 7 mm. Moss cushions not added (optional).
- Deviation: lead-hat drip is 6.70 not 6.60 and tip 8.71 not 8.60 (+1.3 %), because a 53 deg collar must clear the 17th-course shingle stack (accepted roof geometry). Roof+finial / wall ratio rises toward ref's 2.4.

## Round 2 — score 8/10

**What I reviewed.**
- All 6 views and stats.json in `renders/wattle_roundhut/round_02/`, side by side with `hut_overall`, `hut_door`, `hut_wattle_daub_plinth` (plus a 2x zoom of its open bay) and `hut_cap_finial`.
- 14 Director close-ups at 16 spp in `round_02/director_extra/`: apex, apex_eye, profile, door_front, daub_bay, wattle_macro, wattle_mid, plinth, eave_under, side_wall, flags, threshold, frame_raking and plinth_back.
- `tools/hidden_tris.py` on the round-2 .blend, which gives est_hidden_pct 46.0%.
- I read `weave_panel()`, `flagstone()`, `build_collar_finial()` and the plinth chinking code.

**Verdict.** This is a clear step up from round 1.
- The apex now reads at every distance.
- The daub bay beside the door is now convincing.
- The door side panels match ref2.

It is now a solid game asset (rubric 8), but it is not yet close-up worthy:
- The open wattle, which is the hut's identity, still reads as a garden trellis or grid at every distance.
- The plinth still reads as stacked rounded cuboids.
- The path flags are polygon "cookies".
- The entrance timber is still CG-clean at actor distance.

**Axes:**

| Axis | Score | Why |
|---|---|---|
| Silhouette | 8 | The apex is fixed. The walls read as a regular grid, not ref2's dark woven band. |
| Proportion and scale | 9 | |
| Construction | 8 | Rods pass through the stakes. Flags have contact gaps. |
| Detail and craft | 7 | |
| Age and irregularity | 7 | Regular stake grid, cuboid stones, polygon flags. |
| Technical | 8 | Clean this round. Producer notes 3 and 6 become binding from round 3. |

**Strengths**
- **Apex fixed.** The 53° lead hat, Ø1.49 with a 6.5 cm drip fascia, now casts a hard shadow line and reads as ref2's second signature feature in hero, front, side and apex_eye. The folded seams, upper collar drip, spindle and spike all read. The +0.1 m on the apex heights (tip 8.71) is ACCEPTED.
- **Daub bay is close to ref2.** The thick, bulging coat, branched shrinkage cracks, chipped post margins and eroded, ragged lower edge exposing the rods (with clinging clumps) all match `hut_wattle_daub_plinth`.
- **Door side panels.** The diagonal rope-like weave with dark slots now matches `hut_door.png`.
- **Roof is still hero quality.** Ragged butts and split eave shingles add age. The eave underside reads from eye level, with rafter ends, battens, plate and real lip thickness.
- **Round posts.** The 48-sided posts with adze flats and knots no longer read as smooth tubes.
- **Scale is correct.** Door 1.00 × 2.08, eave lip ≥ 2.40 over the door, and the figure reads right.
- **Technical work is clean.** The build is deterministic and takes about 6 s. It has 1.466 M tris, 29.3 MB, identity transforms, UVs, and 10 slots, all in the producer palette.

**Closed or accepted**
- Round-1 items 1, 3 (partly), 4, 5 (partly) and 6 are done.
- Item 7, the apron hairline, is WAIVED. It is a review-plane artefact: the plane sits 2 mm under the bbox minimum. The new polar flat band removed the dashed z-fighting.
- Moss stays optional.

**Spec amendment (supersedes spec §C and art bible §5 stake spacing for this hut).** I re-measured the 2x zoom of ref2's open bay:
- **Stakes:** thin (Ø3–4 cm), only about 3 per 1.57 m bay (spacing 0.38–0.50 m), and mostly hidden behind the rods.
- **Rods:** continuous across several stakes, wavy, and visibly bending round each stake.
- **Gaps:** narrow (0.5–2.5 cm) and dark.
- My round-1 call of "2–4 cm gaps" over-opened the weave. Use the numbers below.

### Must-fix (priority order)

1. **WATTLE READS AS A TRELLIS OR GRID** (`HUT_wattle_rods`, `HUT_wattle_stakes`; every open bay). See profile.png, side_wall.png, wattle_macro.png, wattle_mid.png, side and back.
   - **(a) Rods run through the stakes.** In `weave_panel()` the in/out amplitude is A = 2.5–3 cm. Stake radius (2.0–2.7 cm) plus rod radius (1.35–1.8 cm) is 3.4–4.5 cm, so every rod intersects every stake it should wrap. No rod visibly bends round a stake, and each row looks laid in front of a fence.
   - **(b) Stakes form a vertical grid.** About 5 stakes per bay at Ø4–5.4 cm and 0.29 m spacing make a regular grid that dominates the walls at 30 m.
   - **(c) Gaps show a lit wall.** The 2–4 cm gaps show the sunlit inner skin 8 cm behind, with rod shadows, so it reads as "sticks in front of a wall", not a dark woven wall.
   - **Fix, stakes:** Ø3–4 cm at 0.38–0.50 m spacing (3 per bay). Jitter them ±4 cm and lean them ±1.5°.
   - **Fix, weave offset:** set it per rod to stake_r + rod_r + 3–5 mm (about ±3.5–4.5 cm), so the bend round each stake is visible. Keep the cosine path, but give it a tighter wrap at the stake: 60% of the swing within ±6 cm of it.
   - **Fix, rows:** pitch 4.5–6.5 cm with rods Ø2.5–3.8 cm, so gaps are 0.5–2.5 cm and the open area is ≤ 20% in front view. Use per-rod drift of ±1 rod diameter at 0.5–1 m wavelength, so neighbouring rows occasionally touch or cross.
   - **Fix, rod lengths:** rods 1.2–2.5 m long, not post-to-post. Taper butt to tip 1.0 → 0.55, staggering the ends at least 0.3 m between consecutive rows, and flick the tips 2–5 cm outward.
   - **Fix, inner skin:** move it at least 0.15 m behind the rod centreline, or delete it behind the open bays and close the interior with a dark blocker about 0.6 m inside (see producer note 6).
   - **Acceptance:** in profile and side, the open bays read as horizontal woven texture with no vertical grid. In wattle_macro, every rod visibly wraps its stakes with zero rod/stake intersection (verify with a BVH overlap test). The gaps read dark.

2. **PLINTH STILL READS AS ROUNDED CUBOIDS** (`HUT_plinth_stones`, `HUT_plinth_chinking`, door-post pad stones). See plinth.png, plinth_back.png, actor_closeup.
   - **Problem, stones:** in elevation the stones are rectangles, with parallel vertical sides, planar faces and uniform edge rounding. The `rock()` fracture facets do not read. The two-high stacks form tidy courses, like bricks or soap bars.
   - **Problem, pad stones:** the two door pad stones are about 0.55 m near-cubes that read as concrete blocks.
   - **Problem, chinking:** many chinking pieces stick OUT 1–4 cm as flat rectangular tabs. In plinth_back.png see the joints right of centre and the pinning slabs under the post stone.
   - **Fix, outlines:** use irregular elevation outlines (rounded trapezoid, D-shape, rounded triangle; 5–8 corners) with no two parallel vertical sides.
   - **Fix, faces:** dome the outer faces 2–5 cm and tilt them 5–15° in random directions. Run 1–2 fracture planes visibly across the face, with edge breaks of 3–8 cm.
   - **Fix, rounding:** vary arris rounding per stone from 1 to 6 cm.
   - **Fix, courses:** follow ref2, which is mostly one course of low rounded stones 0.2–0.3 m tall and 0.4–0.7 m long. Cut the two-high stacks to about 20–25%, with uppers clearly smaller than the stone below.
   - **Fix, pad stones:** rough boulders about 0.45 × 0.35 × 0.25 with an irregular plan and a flat bed for the post.
   - **Fix, chinking:** measure the recess locally, so each chink sits at least 2 cm behind BOTH adjacent stone faces (ray-test against the stones and push back any that fail). Make them wedge-pointed, with a visible face of no more than 6 × 10 cm.

3. **PATH FLAGS AND STEP STONE ARE POLYGON COOKIES** (`HUT_threshold`; see flags.png, actor_closeup, threshold.png).
   - **Problem:** `flagstone()` lathes a convex 5–7-corner polygon. The flags read as hexagons and octagons with uniform chamfers. The outer flags show black contact hairlines (they sit on the review plane beyond the apron band). The step stone is a flat slab with straight facet edges.
   - **Fix, outlines:** non-convex, 10–16 corners, plus 3–8 cm-scale edge noise and 1–2 notches.
   - **Fix, shape:** thickness varying ±2 cm, tops tilted 1–3°, edge rounding varying 0.5–3 cm around the outline.
   - **Fix, bedding:** tops 1–3 cm above the surrounding earth, bases buried at least 3 cm, with a soft earth lip (apron) wrapping each edge. Keep every flag inside the apron's flat band, with none past its edge.
   - **Fix, step stone:** the same outline treatment, with a visibly dished wear hollow (1–2 cm) where feet land.

4. **ENTRANCE TIMBER STILL CG-CLEAN AT ACTOR DISTANCE** (`HUT_door_frame`, `HUT_threshold` sill, `HUT_door_leaf`; see frame_raking.png, door_front.png, threshold.png).
   - **Problem:** the 3–6.5 mm adze strokes vanish except under grazing light. The drying checks are single uniform knife slits with pointed ends. The sill reads as a rounded extrusion. The leaf boards are near-uniform width with ruler-straight gaps.
   - **Fix, adze:** on the outward faces of the door posts, jambs and lintel, use scallops 6–12 mm deep and 5–9 cm wide.
   - **Fix, checks:** 6–10 mm wide at the mouth, tapering in both width and depth, wandering ±3 mm, and some with a short parallel or branch check.
   - **Fix, arrises:** vary the chamfer 1.5–3 cm along each member, and let the wane come and go.
   - **Fix, sill:** a 1.5–2.5 cm worn dip over the middle 0.6 m, a worn outer arris, and end checks.
   - **Fix, leaf:** board widths 16–30 cm, gaps 0.5–1.5 cm varying along the length, board ends uneven ±1 cm, and 1–2 boards cupped 3–5 mm.

5. **DAUB PATCH AND RIDGING** (`HUT_daub`).
   - **Patch:** the +X partial patch (side_wall.png) is a rectangle pasted onto the wattle, with straight vertical left and right edges and uniform thickness. Give it an irregular outline with no straight run over 15 cm. Feather the thickness 0 → 4 cm at the edge, expose some rods through thin spots, and add a crumbled lower margin.
   - **Ridging:** in the large bay, the upper-third ridging over the rods reads as regular corrugation (daub_bay.png). Break it into patches of 0.3 m or less with varying pitch and amplitude, only where the coat is thin.

6. **INTERIOR FLOOR SEAM** (`HUT_floor` / `HUT_threshold`). A dark curved seam line crosses the earthen floor about 0.1–0.3 m inside the sill (threshold.png, door_front.png). Close the gap or overlap, and make the floor meet the sill and the inner skin without a visible line.

7. **APEX POLISH** (`HUT_finial`). See apex.png, compared with hut_cap_finial.
   - **Upper collar:** its profile is a concave trumpet (`(1-f)**1.9`), which reads as a vase foot. Ref2's is a straight-to-slightly-convex cone. Make it straight at about 54°, r 0.285 → 0.07 over 0.30 m, keeping the drip bead with 1.5 cm projection.
   - **Spindle:** simplify the double-bulb baluster, which reads as furniture, to ref2's stack: bead ring → tapered spindle → ring.
   - **Spike:** base Ø 0.18–0.20, with a knop ring (+3 cm Ø, 3 cm tall) about 0.2 m up, then a straight taper to the point.

8. **TECHNICAL: producer notes 3 and 6 are binding from round 3.**
   - **Hidden triangles:** est_hidden_pct is 46.0% (674,887 of 1,465,554); the target is ≤ 15%. Hidden share and count per object:

     | Object | Hidden share | Hidden tris |
     |---|---|---|
     | rods | 50.5% | 206k |
     | shingles | 55.8% | 124k |
     | door frame | 41% | 49k |
     | plinth stones | 55% | 48k |
     | daub | 14% | 38k |
     | apron | 76% | 34k |
     | battens | 83% | 33k |
     | posts | 40% | 27k |
     | rubble | 65% | 18k |
     | purlins | 92% | 16k |
     | rafters | 75% | 15k |
     | chinking | 51% | 14k |
     | starter | 60% | 12k |
     | wall plate | 97% | 6k |

   - **Cuts:**
     - Drop rod backs facing the daub and inner skin, and every rod section buried under daub.
     - Trim covered shingle bodies to the exposed part plus about 5 cm of overlap.
     - Delete stone backs and sides behind the face line, and anything more than 5 cm below ground.
     - Keep battens, purlins and rafters only where they are visible under the eave or through the door.
   - **Reinvest** the saved triangles in item 1 (wattle) and items 2–4.
   - **Sharing:** build variant pools for pegs, nails, hinge parts, chinking and rubble (6–12 each) as linked-duplicate (shared mesh data) objects, staying under the 400-object limit. Shingles may stay joined, but generate them from a pool of 12–20 variant base meshes.
   - **Stats:** report est_hidden_pct and material_slot_count from the new render_review.

**Nice to have**
- Low-poly moss cushions at the collar drip and a few door-side eave butts.
- Slightly irregular rafter-end cuts: more saw/axe facets on 4–6 ends.

## Round 3 — builder entry
- Script `buildings/wattle_roundhut/build_wattle_roundhut.py` (deterministic: the geometry/transform hash matches across reruns; the build takes about 10 s). It saves `wattle_roundhut.blend` (23.5 MB, compressed, no `.blend1` backups). Renders are in `renders/wattle_roundhut/round_03/` (all 6 views at 32 spp, plus stats.json and hidden.json).
- **Stats:**
  - 1,083,921 tris, down from 1.466 M.
  - **est_hidden_pct 14.2 %**, down from 46 %. Below ground 0 %.
  - **material_slot_count 10**, all from the 15-slot palette, and the build asserts palette membership.
  - `mask_attribute_missing` is empty.
  - bbox min (-5.10, -7.48, -0.045), max (5.11, 5.21, 8.73).
  - 168 objects: 23 unique meshes plus 145 linked duplicates from 32 pooled meshes, in the sub-collection `HUT_kit_instances`.
- **Must-fix 1 (wattle):**
  - Stakes are Ø2.8-3.6 cm, 3 per bay, jittered ±4 cm, leaning ±1.5° and set 2.2 cm back.
  - Every rod wraps its stakes. The offset is stake_r + 1.24·rod_r + 3-5 mm, using a Hermite wrap with 30 % of the half-swing within 6 cm of each stake. By construction, no rod intersects a stake.
  - Rods are Ø2.5-3.8 cm with 0-1 cm packing gaps, plus taper 1.0→0.55. Drift is ±1 rod diameter at 0.35-0.75 m wavelength.
  - About 65 % of rows have staggered rod joints (≥0.3 m stagger, 0.18-0.32 m overlaps) with tips flicked 2-5 cm outward and capped.
  - Rods are trimmed wherever the daub buries them. The inner skin is a single lumpy sheet 0.17 m behind the rod centreline, so the gaps read dark.
- **Must-fix 2 (plinth):**
  - New `shell_stone()`: irregular outlines (trap / D / tri, 5-8 corners, no parallel sides), domed and tilted faces, 1-2 crisp fracture planes (4.5-8 cm edge breaks) plus 3-5 split facets, and arris rounding of 0.8-5 cm that varies round each stone.
  - One course, top about 0.33 m, earth banked about 5 cm, 22 % two-high with clearly smaller uppers.
  - Door pad stones are irregular boulders with a flat bed.
  - Chinking: a pool of 8 wedges, ray-tested against the stones so each one sits ≥2 cm behind both neighbouring faces and is placed only where an open joint shows it (44 placed).
- **Must-fix 3 (flags and step):** non-convex 10-16-corner outlines with edge noise and notches, ±2 cm thickness, 1-3° tilt, arris 0.5-3 cm, 2.2-3.2 cm proud, and soft earth lips modelled into the apron. The apron now extends under the whole path, so no flag is off the earth. The step stone has a 1.6 cm wear dish.
- **Must-fix 4 (entrance timber):**
  - `hewn_member` gives hero faces adze scallops 6-12 mm deep and 5-9 cm long.
  - Chamfers vary 1.5-3 cm along each member, and the wane comes and goes.
  - Checks are 6-10 mm wide at the mouth, taper in width and depth, wander ±3 mm, and 60 % have a branch.
  - Sill: a 2.2 cm trodden dip over the middle 0.6 m, a worn outer arris and end checks.
  - Leaf boards are 16-30 cm wide, with gaps that vary along the length, ends uneven by ±1 cm, and 2 cupped boards.
- **Must-fix 5 (daub):** the side patch is an irregular blob with a crumbled lower margin, thin spots and rods showing through. It feathers over about 12 cm. The ridging is broken into patches of 0.3 m or less with varying pitch and amplitude, only where the coat is thin.
- **Must-fix 6 (floor seam):** the floor now runs under the sill in the door sector and steps down about 2.5 cm inside the sill, so the seam is gone.
- **Must-fix 7 (apex):** the upper collar is a straight 54° cone (r 0.285→0.07 over 0.30 m) with its drip bead. The spindle is bead ring → tapered spindle → ring. The spike base is Ø0.19 with a knop ring 0.2 m up, then a straight taper.
- **Producer notes 6 and 7, and must-fix 8:**
  - Shingles are modelled as the exposed part plus 6.5 cm overlap. They are full length only where the covered part can be seen: under missing shingles, and in the back-arc window seen through the door. Undersides and heads are dropped above course 1. 16 pooled base shapes.
  - Rods and stakes are open-backed shells with arcs that depend on height and how proud the rod sits.
  - Posts are open at the back.
  - Hidden faces of hewn members are closed with coarse quads.
  - Rafters are eave stubs, full length only in the back arc. Purlins and battens are kept only where visible (eave gap / doorway).
  - A dark roof blocker keeps the interior dark.
  - Nothing is below -4.5 cm.
  - Pools: pegs 6, nails 3, clench nails 3, hinge strap / knuckle / pintle, chinking 8, rubble 10.
- **Producer note 9:** every mesh has a CORNER `Mask` (R per piece, G wear: higher on slipped or split shingles and the worn sill, B ground / up-facing / north dirt).
- **Known gaps:**
  - The flags read faintly in the frontal clay light.
  - Stakes still show as thin verticals at close range.
  - The apron margin hairline remains (waived r2).
  - Instanced pieces carry transforms, and their Mask R is per variant, not per instance.
  - Plinth top (0.33) and wattle base (0.345) are about 4 cm below spec §A, following the r2 note that the stones should be 0.2-0.3 m visible.

## Round 3 — score 8/10

**What I reviewed.**
- All 6 views, stats.json and hidden.json in `renders/wattle_roundhut/round_03/`, side by side with `hut_overall`, `hut_door`, `hut_wattle_daub_plinth` and `hut_cap_finial`.
- 16 Director close-ups at 16 spp in `round_03/director_extra/`: apex, apex_eye, profile, eave_under, eave_close, door_front, door_near, frame_raking, threshold, flags, plinth, plinth_back, daub_bay, side_wall, wattle_mid and wattle_macro. Ground plane at bbox min (-0.047).
- Ray-picks on suspect pixels. I read `weave_panel()` (junction logic), `make_daub_fields()`, `plan_path()`/`build_path()` and the threshold-stone code.

**Verdict.** This is a real step forward, but not yet a 9.
- The trellis is gone. At hero, front, side and back distance the walls now read as a dark woven band like ref2.
- The apex now overlays `hut_cap_finial` (apex_eye is the best view of the asset).
- The producer notes are all met: 14.2 % hidden, 10 palette slots, Mask on every mesh, pooled instances.

What holds it at 8 is the eye-level and actor-distance read, which producer note 4 says matters most:
- At mid-shot the wattle reads as stacked kindling, because rod ends float in mid-span everywhere.
- The door side panels read as fishbone ribs at actor distance.
- Every ground-contact stone (plinth, pad stones, threshold stone, step stone, rubble) still reads as soft boxes or pillows.
- The path flags read as puddles.
- The back daub bay has a ruler-straight lower edge, and the side patch reads as a decal.

The entrance is therefore still not close-up worthy, which is the rubric-8 marker.

**Axes**

| Axis | Score | Why |
|---|---|---|
| Silhouette | 9 | Apex, cone and walls all read as ref2 at thumbnail. |
| Proportion and scale | 9 | Door 1.00 × 2.08, eave ≥ 2.40, plinth top 0.33 (accepted, see below). |
| Construction | 8 | Rod joints float in mid-span. Side panels are ribs. The threshold stone is a kerb. |
| Detail and craft | 7 | Ground-contact stones, flags, side panels and timber checks are not close-up worthy. |
| Age and irregularity | 8 | Good on the roof and apex. The stones are still uniform soft blocks. |
| Technical | 9 | All producer notes are met. Two rulings are below. |

**Strengths**
- **The wattle reads as woven at distance.** The 3 thin stakes per bay, packed rows and dark inner skin give ref2's dark horizontal woven band in hero, side, back and side_wall. Rods wrap the stakes with no rod/stake intersection. Round-2 must-fix 1(a)-(c) is substantially closed.
- **The apex is now a match.** The 53° lead hat has its drip shadow line. The upper collar is a straight 54° cone. The bead ring / spindle / ring stack and the Ø0.19 knopped spike overlay `hut_cap_finial` (apex_eye.png). Round-2 item 7 is CLOSED.
- **The shingle roof is still hero quality** (profile.png). It has chunky, ragged butts, staggered joints, slips, a convex profile and eave kick, and it reads at about 0.45 m next to the figure.
- **The door assembly and interior.** The leaf is open 75° with ledges, brace and strap hinge. The interior is dark and deep, with the floor, hearth ring and rafters visible, and there is no sky void. The floor seam is gone (round-2 item 6 CLOSED).
- **The large daub bay beside the door** still matches ref2's bay: a thick coat, an eroded lower edge exposing rods, and clinging clumps.
- **Technical work is clean.**
  - 1.084 M tris, est_hidden_pct 14.2 % (round-2 item 8 CLOSED).
  - 10 slots, all in the palette. `mask_attribute_missing` is empty.
  - 168 objects (32 pools, 145 linked duplicates). Deterministic 10 s build, 23.5 MB.
  - Components are parameterised: `shell_stone`, `hewn_member`, `weave_panel`, `shingle_mesh` and `pool_mesh`.

**Rulings**
- **Pooled instances.** Linked-duplicate pool instances carrying object transforms are ACCEPTED. That is what producer note 3 asks for, and they become ISMs. Mask R per variant (not per instance) is ACCEPTED for pooled pieces, because Unreal's PerInstanceRandom supplies the per-instance value.
- **Plinth height.** The plinth top at 0.33 and the wattle base at 0.345 are ACCEPTED, following my round-2 note on ref2 stone height.
- **Apron hairline.** The apron's outer hairline stays WAIVED as a review-plane artefact.
- **Budget constraint.** est_hidden_pct must stay ≤ 15 % after the fixes below. Aim for ≤ 13 % to leave headroom.

### Must-fix (priority order)

1. **WATTLE READS AS KINDLING AT MID-SHOT: mid-span rod ends** (`HUT_wattle_rods`; every open bay; see wattle_mid.png, wattle_macro.png, daub_bay.png).
   - **Problem, ends:** in `weave_panel()`, 65 % of rows get a junction at a random `sj` anywhere in the bay. Each junction leaves two free ends floating between stakes, flicked 2-5 cm outward, so a bay face shows roughly 40 or more loose stick ends. The wall reads as a hairy stack of sticks, not ref2's continuous wavy rows.
   - **Problem, doubled rows:** the two pieces are also offset vertically by ±0.55·rod_r (`dzf`). Every overlap therefore reads as a doubled, thickened row and causes the rod/rod intersections listed in the known gaps.
   - **Fix, joint frequency:** cut junction rows to 20-25 %.
   - **Fix, joint position:** put every joint AT a stake. Each end stops 2-5 cm past the stake on the side where that rod passes BEHIND it, so the end is hidden.
   - **Fix, row lane:** drop the `dzf` split, so the two pieces share the row lane (one in front of the shared stake, one behind).
   - **Fix, flicked tips:** keep an outward flick (1-3 cm) on no more than 10 % of ends.
   - **Acceptance:** at most about 6 visible rod ends per bay face in wattle_mid, and the rows read as continuous wavy bands in side_wall.

2. **DOOR SIDE AND CHEEK PANELS READ AS FISHBONE RIBS** (`HUT_door_frame` side panels, slant 0.85, and cheek panels, slant -0.6; see door_near.png, door_front.png, frame_raking.png). At actor distance each diagonal rod is a separate rib, with ends poking past the outer stake and 2-3 cm see-through slots between rods.
   - **Fix, ends:** start and end every rod behind the jamb, sole rail or outer stake, with no protruding ends.
   - **Fix, rods:** use rods Ø2.4-3.0 cm packed with a perpendicular gap of 0.5 cm or less. Each rod is a continuous S-curve that visibly wraps both stakes, so the panel reads as the twisted rope of `hut_door.png`.
   - **Fix, gaps:** no see-through gap to the interior wider than 1 cm.

3. **GROUND-CONTACT STONES STILL READ AS SOFT BOXES OR PILLOWS** (`HUT_plinth_stones`, door-post pad stones, threshold stone, step stone, `HUT_ground_rubble_*`; see side_wall.png, plinth.png, plinth_back.png, threshold.png, actor_closeup).
   - **(a) Plinth.** The stones have a flat top plateau, a planar front and near-vertical sides. In elevation they read as a row of similar trapezoid kerb blocks of near-equal height, with 4-10 cm gaps holding round nubs.
     - Crown the tops 4-8 cm with the high point off-centre, and bulge the fronts 3-6 cm.
     - No planar area wider than about 12 cm, except the fracture facets, which should be on only about 35 % of stones.
     - Vary visible heights 0.18-0.34 with neighbours differing by at least 4 cm.
     - Close the face joints to 3 cm or less.
     - Replace the round chinking nubs with flat wedges.
   - **(b) Door-post pad stones** are drums with vertical sides. Make them low irregular boulders, about 0.45 × 0.35 × 0.22, with sloping sides and a post bed only about 0.25 wide.
   - **(c) Threshold stone** (`shell_stone(0.98, 0.10, …)` at FRONT_Y-0.03) is a 1.96 × 0.20 m kerb with a ruler-parallel front edge.
     - Split it into 2-3 stones, or give it a front edge wandering ±5 cm with depth 0.22-0.35.
     - Add 1-2 chipped notches of 3-6 cm and 1-2 cm height steps between pieces.
   - **(d) Step stone** reads as a pillow. Flatten the top to a slightly dished plane with a 1-1.5 cm arris, slope the sides, and add 1-2 edge chips of 4-8 cm.
   - **(e) Rubble pool** reads as rounded sugar cubes. Make the 10 variants sub-angular with 3-5 flat fracture facets, thickness 0.4-0.6 × length, and bury them 30-50 %.

4. **PATH FLAGS READ AS PUDDLES** (`HUT_path_stones`; see actor_closeup, flags.png). The flags are 2.2-3.2 cm proud, with a 1.4-2 cm earth lip on the full perimeter, so only about 1 cm of edge reads. They are small (`plan_path`: 0.36-0.84 × 0.34-0.53 m) and widely spaced.
   - **Fix, height and lip:** tops 3.5-5 cm proud. The earth lip should wrap only 30-50 % of each perimeter.
   - **Fix, edges:** arris 0.8-1.5 cm with 2-3 chipped breaks per flag.
   - **Fix, size and spacing:** enlarge to 0.5-0.9 m (spec §F) and tighten joints to 5-15 cm, so the path reads as the paving in `hut_door.png`. All flags stay on the apron.

5. **DAUB: BACK BAY EDGE, SIDE PATCH, CLOTH FOLDS** (`HUT_daub`).
   - **(a) Back-right bay.** `back_field` (z > 0.50 + 0.05·noise) gives a ruler-straight lower edge with a square corner, exposing a strip of rods (plinth_back.png). Spec §D says this bay is fully daubed.
     - Carry it down to the plinth top, with an eroded margin of 0.35-0.60 at 0.3-0.6 m wavelength.
     - Crumble the edge, with no straight run over 15 cm and no square corners.
   - **(b) Side patch** (`side_field`, bay 2). It reads as a flat jigsaw-piece decal with drawn-on cracks (side_wall.png, wattle_mid.png).
     - Make it 2-4 cm thick at the centre with lumps, feathering into the rods over 8-12 cm, with rod ridges showing through the thin margin.
     - Remove or soften the long crack lines.
   - **(c) Ridging.** In the large bay and back bay the ridging reads as draped cloth folds: long smooth ridges, diagonal at the upper left of daub_bay.png and vertical in eave_under.png.
     - Ridging may only follow the horizontal rod rows (pitch 4.5-6.5 cm, 3-6 mm amplitude).
     - No vertical or diagonal folds. Break the long undulations with 1-3 cm palm-press dents.

6. **ENTRANCE TIMBER: RECTANGULAR CHECK POCKETS AND SOFT ADZE NOISE** (`HUT_door_frame` door posts and jambs; see door_front.png, door_near.png, frame_raking.png).
   - **Problem, checks:** the branched checks render as rectangular pockets with vertical walls, for example the right jamb at (0.59, -3.71, 1.41) and the left jamb at (-0.60, -3.72, 1.56). This is a CG tell at 2 m.
   - **Fix, checks:** make the checks V-section, closing to zero width at both ends, with branches leaving at 30° or less.
   - **Problem, adze:** the scallops read as low-frequency lumpy noise ("soft clay"), not tool work.
   - **Fix, adze:** give the scallop boundaries crisp creases (20-35°, sharp-edged or split normals), and run the scallops in consistent diagonal lanes per face, so they read under frontal light.

7. **SMALL HYGIENE: PALE CHIPS UNDER THE PLATE** (eave_close.png, eave_under.png). A `HUT_daub` fragment at about (-1.78, -3.10, 2.60) and a `HUT_posts` sliver at about (-2.49, -2.58, 2.63) show as floating pale chips just under the wall plate at about az -30°. Trim the daub to at least 2 cm below the plate underside, and close or trim the open-backed post top so no sliver shows.

**Nice to have**
- Low-poly moss cushions at the collar drip and a few door-side eave butts (still optional).
- A Mask G/B tuning pass: B high on plinth and flag tops, G high on the sill dip and the step-stone dish.
- More hidden-tris headroom: the rods (16 % hidden) and the wall top in the eave shadow are the cheapest cuts.

## Round 4 — builder entry
- Script `buildings/wattle_roundhut/build_wattle_roundhut.py` (deterministic: geometry/transform hash identical across rebuilds; ~18 s build). Saves `wattle_roundhut.blend` (23.1 MB, compressed). Renders: `renders/wattle_roundhut/round_04/` (6 views, 32 spp, stats.json, hidden.json).
- **Stats:** 1,061,091 tris; **est_hidden_pct 13.8 %** (standalone runs 13.1-13.3 %); **material_slot_count 10** (all palette); `mask_attribute_missing` empty; 144 objects (120 linked duplicates from 31 pools); bbox min (-5.10, -7.48, -0.045), max (5.11, 5.21, 8.73).
- **#1 Wattle:** `weave_panel()` junctions now in 22 % of rows (`junction_p`), always AT a stake the row passes behind, never the same stake in consecutive rows; the old rod stops 2-5 cm past that stake, the new rod starts 2-5 cm before it tucked just behind it (`dzf` split removed, shared lane); only ~10 % of those tips flick out 1-3 cm. Rows now read as continuous wavy bands (side_wall, wattle_mid).
- **#2 Door side/cheek panels:** new `rope_panel()`: diagonal rods Ø2.4-3.0 cm, 2-5 mm perpendicular gap, each one continuous S-curve wrapping both stakes in alternate phase; every end buried 3-5 cm in jamb / door post / sole rail / lintel / tie beam / wall post; daub backing sheet behind (no see-through). New hewn sole rail under each cheek panel; plinth now runs on under the cheeks.
- **#3 Ground stones:** new `facet_stone()` / `field_stone()` (implicit curved facets, log-sum-exp joined, ray-bisection meshed): crowned tops 4-8 cm with off-centre high point, fronts bulging 3-6 cm and battered back, top-front bevel and corner facets, arris radius varying along the edge, crisp fracture facets on ~35 % (actual 9/38 + uppers); crown heights alternate (visible 0.20-0.34, neighbours >= 4 cm apart), ends overlap so joints close; flat pooled wedge chinking. Weave and posts are bedded onto the actual stone tops (`wall_floor`, `stone_top`). Door pads: low boulders ~0.46 x 0.36 x ~0.22 visible, sloping sides, ~0.25 m bearing bed (post base lowered to 0.27, earth mound). Threshold: 3 flat slabs, wandering fronts, depth 0.26-0.34, 1-2 cm steps, chipped notches. Step stone: flat slightly dished top, 1-1.5 cm arris, sloping sides, 2 edge chips (moved 8 cm out). Rubble pool: sub-angular, 3-5 crisp facets, thickness 0.4-0.6 x length, buried 30-50 %, kept off the flags.
- **#4 Flags:** 8 flags 0.5-0.85 m laid in staggered rows from their real outline extents (5-11 cm nearest-point joints), 3.5-5 cm proud, earth lip on only 30-50 % of each perimeter, 0.8-1.5 cm arris with 2-3 chipped breaks; geometry now uses the planned outline (lip and stone match).
- **#5 Daub:** (a) back bay carried down to the stone tops with eroded bites up to ~0.6 m, rounding up into the posts (no straight run / square corner); (b) side patch: smooth organic outline, 2-4 cm proud with lumps, feathered over ~10 cm, no cracks; (c) ridging horizontal only (one pitch per bay 5.0-6.2 cm, phase independent of height drift, 3-6 mm), strokes replaced by round palm dents; cracks shorter (0.12-0.35 m).
- **#6 Timber:** checks are V-section (mouth width and depth both run to zero at the ends, depth ~1-1.3 x width), branches are en-echelon (parallel, own lips); adze strokes run in one consistent 25-40° diagonal per face with a steep-entry scoop profile (crisp creases), hero members sampled at 9.5 mm.
- **#7 Hygiene:** daub stops 2 cm under the plate and tucks back; rods continue up under the plate there (no visible plate underside gap); post heads taper over the top 0.26 m to r 0.082 and bury 3.5 cm into the plate.
- **Known gaps:** adze lanes stair-step slightly at grazing angles (rings are perpendicular to the member); the rope panel nearest the camera reads as hooked rods when seen very obliquely; the plinth stones are still on the smooth side in flat light; moss cushions not modelled.

## Round 4 — score 8/10

**What I reviewed.**
- All 6 views, stats.json and hidden.json in `renders/wattle_roundhut/round_04/`, side by side with `hut_overall`, `hut_door`, `hut_wattle_daub_plinth` and `hut_cap_finial`.
- 21 Director close-ups at 16 spp in `round_04/director_extra/`: apex_eye, profile, door_front, door_near, frame_raking, rope_panel, inside_left, threshold, flags, pad_stone, plinth, plinth_side, plinth_back, daub_bay, daub_full, back_bay, side_wall, wattle_mid, wattle_macro, eave_under and eave_close. Ground plane at -0.047.
- Ray-picks on suspect pixels. A ray-grid open-area measurement on 5 open bays (horizontal rays normal to the wall, z 0.6-2.4). I read `weave_panel()`, `build_inner_skin()`, `build_plinth()`/`field_stone()` and the door pad-stone code.

**Verdict.** Real progress on the round-3 list, but the asset is still an 8, not a 9.
- The rope panels beside the door are now a match for `hut_door.png`.
- The mid-span rod ends are gone. Rows read as continuous wavy bands, with at most about 4 visible ends per bay face in wattle_mid.
- The back bay now runs down to the stones.
- Roof, apex and scale are still hero quality.

What holds it at 8 is the same rubric-8 marker as last round: the entrance and eye-level wall are not close-up worthy.
- The open wattle measures 40-45 % open, so it reads as sticks in front of a wall rather than ref2's packed weave.
- Every ground-contact stone is still a smooth soft form. The door-post pads are now literal hemispheres.
- The door posts and jambs show stair-stepped, voxel-like adze patches.
- Culling has opened see-through holes that are visible through the doorway from an actor-position camera. That breaks producer note 6 ("never open holes when culling").

**Axes**

| Axis | Score | Why |
|---|---|---|
| Silhouette | 9 | Cone, lead hat, finial, plinth and door frame all overlay ref2 at thumbnail. |
| Proportion and scale | 9 | Unchanged and correct: door 1.00 × 2.08, eave ≥ 2.40, shingles read about 0.45 m. |
| Construction | 8 | See-through wall and roof through the door, a void under the left cheek sole rail, and sugar-cube daub clumps. |
| Detail and craft | 7 | Weave 44 % open; pad, plinth, threshold and flag stones read as soft pillows or soap; blocky adze. |
| Age and irregularity | 8 | Roof and apex convincing. The stones are uniform soft loaves, and the side daub patch is a lobed cookie. |
| Technical | 8 | 1.061 M tris, 13.8 % hidden, 10 palette slots, Mask complete, 144 objects. But holes are open after culling, and the r3 #7 daub chip is still there. |

**Strengths**
- **Door rope panels (r3 #2 CLOSED).** `rope_panel()` reads as the twisted rope of `hut_door.png` in door_front, rope_panel and daub_full. Ends are buried, and nothing shows through. The left panel's hooked read at very oblique angles is acceptable.
- **Wattle rod ends (r3 #1 junction part CLOSED).** Joints sit at stakes. Rows are continuous wavy bands, with at most about 4 visible ends per bay face in wattle_mid and wattle_macro. Rods wrap the stakes.
- **Roof and apex are still hero quality.** In profile and apex_eye: chunky ragged shingles, stagger, slips, a convex profile with eave kick, a 53° lead hat with drip shadow and seams, and the knopped spike.
- **Back bay (r3 #5a CLOSED).** It reaches the stone tops with bites and rounds into the posts. The ridging is horizontal only (r3 #5c CLOSED).
- **Timber checks (r3 #6 checks part CLOSED).** They are V-section and close to zero at the ends. The branches are en-echelon.
- **Technical.** The build is deterministic and takes 18 s. It has 1,061,091 tris, est_hidden_pct 13.8 % (≤ 15 %), 10 slots all in the palette and `mask_attribute_missing` empty. There are 120 linked duplicates from 31 pools, the file is 23.1 MB, and components are parameterised (`rope_panel`, `field_stone`, `facet_stone`, `boulder`, `stone_top`).

**Closed or accepted**
- Round-3 items 2, 5a, 5c and the check part of 6 are CLOSED.
- Item 1 is closed for ends and junctions, but reopened below for open area.
- The plinth top 0.33, pooled-instance Mask R and the apron hairline rulings all stand.

### Must-fix (priority order)

1. **OPEN WATTLE IS 40-45 % OPEN: it reads as sticks in front of a wall, not ref2's packed weave** (`HUT_wattle_rods`; every open bay; see side_wall.png, wattle_mid.png, wattle_macro.png, plinth_side.png, daub_full.png left bay, and the pale crosshatch in hero and actor_closeup).
   - **Measured:** horizontal rays normal to the wall at z 0.6-2.4 give rods + stakes / inner skin of:

     | Bay (az) | Rods + stakes | Inner skin |
     |---|---|---|
     | 100-120° | 45 % | 35 % |
     | -150 to -130° | 51 % | 31 % |
     | -110 to -90° | 48 % | 31 % |

     The rest is posts. Excluding posts, the open area is 38-44 %. The spec (r2 amendment) is ≤ 20 % with 0.5-2.5 cm dark gaps.
   - **Cause:** `gap=(-0.004, 0.01)` is applied to the row envelope at the butt radius. The 1.0 → 0.55 taper, the in/out swing and the ±1-diameter drift then open 2-4 cm gaps over most of each rod.
   - **Fix, taper:** reduce it to 1.0 → 0.8.
   - **Fix, row spacing:** derive it from the *local* rod radius along s, not the butt radius, so that the envelope gap is 0.3-1.5 cm everywhere.
   - **Fix, drift:** let neighbouring rows touch or overlap by up to 0.5 cm where the drift brings them together, rather than opening.
   - **Fix, rods:** keep Ø 2.8-3.8 cm at the butt.
   - **Acceptance:** the same ray-grid gives inner skin ≤ 20 % of (rods + stakes + skin) in every open bay, and side_wall reads as a dark packed woven band.
   - **Budget:** pay for it by thinning the hidden rod arcs. Keep est_hidden_pct ≤ 15 %.

2. **GROUND-CONTACT STONES ARE STILL SMOOTH PILLOWS, AND THE DOOR PADS ARE HEMISPHERES** (pad_stone.png, plinth.png, plinth_back.png, plinth_side.png, threshold.png, flags.png). This is the single biggest close-up CG tell at the entrance.
   - **(a) Door-post pad stones** (`boulder((0.23, 0.18, 0.15)…, taper=0.32)` at (±1.04, -3.61)). Both render as smooth, rotationally symmetric domes with the post on a small flat.
     - Make them low and wide, with a visible height of 0.16-0.20 against a plan of 0.46 × 0.36, so the visible width:height is ≥ 2.2:1.
     - Give them an irregular 6-9-corner plan and 2-3 planar split faces meeting at visible arrises (radius 0.5-1.5 cm).
     - The flat bed should be about 0.25 m across, tilted 1-3°. No symmetric profile.
   - **(b) Plinth stones** (`field_stone`). In elevation every stone is a rounded-rectangle loaf with the same 5-8 cm arris and a perfectly smooth surface. The "fracture facets" do not read in any view.
     - **Surface:** add 6-12 shallow conchoidal facets per visible face (8-20 cm across, 4-10 mm deep, crease radius ≤ 5 mm), lumps of 1-2 cm at 10-15 cm wavelength, and a few pits.
     - **Arrises:** vary the radius 1-3 cm.
     - **Fractures:** ≥ 50 % of stones should show one planar fracture face with a crisp edge that reads in plinth.png.
     - **Shape mix:** about 30 % sub-rounded boulders with an irregular, non-rectangular top profile, about 40 % flattish slabs (height:length ≤ 0.45), and the rest blocky. No two neighbours of the same type.
   - **(c) Threshold slabs and step stone.** They read as soap bars: perfectly flat tops and a uniform 2-3 cm rounded arris all round.
     - **Tops:** undulate 0.5-1.5 cm at 15-25 cm wavelength, with 2-3 shallow spalls 2-5 mm deep.
     - **Arrises:** vary 0.5-2.5 cm along the edge, with chipped breaks.
     - **Bedding:** the step stone shows a dark undercut on its +X edge (flags.png). Bed it so no underside arris is visible.
   - **(d) Flags.** The earth lip is a smooth fillet, so the flags read as melted dough or puddles.
     - Where there is no lip, show ≥ 2.5 cm of near-vertical stone edge face.
     - Where there is a lip, keep it ≤ 1.5 cm high and ≤ 4 cm wide.
     - Apply the top undulation from (c).
   - **(e) Clinging daub clumps** on the door-bay rods (daub_full.png, plinth.png). They are three rounded cubes. Replace them with 2-3 flattened, torn blobs (4-8 cm) wrapped around the rods, conforming to them.
   - **(f) Rubble.** It reads as smooth beans in plinth.png and flags.png. The 3-5 crisp facets must read at 2 m.

3. **SEE-THROUGH HOLES FROM CULLING, VISIBLE THROUGH THE DOOR** (producer note 6; frame_raking.png, inside_left.png).
   - **(a) Wall.** From an eye-level camera 1.3-2.5 m to the right of the door axis, for example (2.2, -4.9, 1.65) looking at (-0.6, -3.2, 1.5), lit stripes show on the inside of the left wall at az -45° to -55°, z 1.0-2.6.
     - `build_inner_skin()` drops the skin behind the daub bay (`sb0+0.06`). The posts and rods there are open-backed shells, so rays exit to the sky.
     - Ray-picked: frame_raking pixels (600,100), (605,200) and (610,300) MISS; (600,420) passes posts (back open) → rods → MISS.
     - Keep the inner skin (or a dark blocker) over the full circumference, including behind the daub bays. It is a few thousand tris.
   - **(b) Roof.** Through the same door view, the roof underside at az about -72° shows shingles from below with sky behind them (pixels (690,42) and (650,30): shingles, then MISS). `interior_visible()` and the roof blocker cover only ±110° about the back.
     - Extend `HUT_roof_blocker` (low-poly) to the full 360°, or at least to the ±150° about the back that the door can see.
   - **(c) Cheek sole rail.** There is a black void under the left cheek sole rail between the pad stone and the first plinth stone (pad_stone.png, x 400-500, y 300-420). Close it with chinking or an earth bank.
   - **Acceptance:** from eye-level cameras on an arc r = 5 m, az -60° to +60° about the door axis, no ray through the doorway misses geometry.

4. **ENTRANCE TIMBER: STAIR-STEPPED, VOXEL-LIKE ADZE PATCHES** (`HUT_door_frame` door posts and jambs; door_front.png, door_near.png, rope_panel.png left jamb, inside_left.png right jamb x 730-800, pad_stone.png).
   - The diagonal strokes are cut on rings perpendicular to the member. They render as rectangular steps and blocks a few mm high, which reads as low-res displacement at 1-2 m. The builder's known gap understates it: it shows under frontal light, not only at grazing angles.
   - **Fix:** generate the hero-face surface on a grid aligned to each stroke, or subdivide to ≤ 4 mm with the crease placed on the stroke boundary curve. Each scallop edge must be a continuous line with no step > 1.5 mm.
   - **Keep:** scallops 5-9 cm, 6-12 mm deep, one diagonal per face.
   - **Sill:** remove the periodic bead lumps along the sill's front face (threshold.png). They read as a repeating pattern. Replace them with irregular wear (1-3 lumps per metre, varied).

5. **DAUB: DOOR-BAY EROSION SHAPE, SIDE PATCH, STAIR-STEP EDGES** (`HUT_daub`).
   - **(a) Door bay.** The erosion reads as an arched "mouse hole": a smooth arch whose daub comes down to the plinth at both posts (daub_full.png, actor_closeup). In ref2 (`hut_wattle_daub_plinth`) the broken edge runs across the full bay width and exposes the bottom wattle post to post.
     - Put the lower edge at z 0.65-0.95 across the whole bay: ragged ±12 cm at 5-15 cm wavelength, plus 2-3 deeper bites.
     - Nothing below z 0.5 except ≤ 2 small remnants.
     - Keep the lip thickness feathering 4 → 1 cm.
   - **(b) Side patch** (+X, side_wall.png, plinth_side.png). It is still a lobed "cloud" or cookie with a scalloped outline, standing proud of the rods as a separate slab.
     - Make it an elongated horizontal patch, 0.5-0.9 × 0.3-0.5 m. Its top and bottom margins should break along rod rows (stepped horizontally), with no round lobes.
     - Press it into the weave so that the rod ridges show over its whole outer 8-12 cm.
   - **(c) Stair-steps.** Daub margins show grid stair-steps: a comb at the door-bay edge (plinth.png x 720-770, y 130-160) and on the side-patch rim (plinth_side.png x 360-540, y 90-195). Resample the boundary at ≤ 1 cm, or clip the mesh along the contour, so no grid steps show.
   - **(d) Daub chip (r3 #7, not closed).** It is still a pale chip under the plate at (-1.78, -3.08, 2.61) (eave_under.png), and thin pale post-head slivers show at about (-2.48, -2.55, 2.61). Drop the daub top to ≥ 4 cm under the plate underside there, and give the post-head taper a dark tuck or hide it behind the plate.

**Nice to have**
- Low-poly moss cushions at the collar drip and a few door-side eave butts (still optional).
- A Mask G/B tuning pass: B high on the plinth and flag tops, G on the sill dip and step dish.

## Round 5 — builder entry
- Script `buildings/wattle_roundhut/build_wattle_roundhut.py` (deterministic: geometry/transform hash identical across rebuilds; ~25 s build). Saves `wattle_roundhut.blend` (27.7 MB, compressed). Renders: `renders/wattle_roundhut/round_05/` (6 views, 32 spp, stats.json, hidden.json).
- **Stats:** 1,274,341 tris; **est_hidden_pct 13.9 %** (standalone 13.8 %); **material_slot_count 10** (all palette); `mask_attribute_missing` empty; 162 objects (137 linked duplicates from 31 pools); bbox min (-5.10, -7.48, -0.045), max (5.11, 5.21, 8.73).
- **#1 Open wattle:** in `weave_panel()` each row is now laid on the row below. Its centre line is the previous row's real envelope top (local tapered radius along s), plus a 0.2-0.9 cm gap that wanders slowly and is clipped to -0.3..+1.2 cm (rows touch, never open), smoothed over about 3.5 cm. Taper is 1.0 → 0.8, butt Ø 2.8-3.8 cm, and the old ±1-diameter free drift is gone. The rod section arcs were also wrong: below eye level the visible top stopped at 46°. Now the side facing the viewers runs past vertical (98-112°) and the far side stops at 76-90°. Same ray-grid as the director (horizontal rays normal to the wall, z 0.6-2.4, skin / (rods + stakes + skin)): **12.3-14.4 %** in all 7 bays tested (100-120: 13.2; -150..-130: 13.1; -110..-90: 14.1; 60-80: 12.3; -80..-60: 13.3; 20-40: 14.4).
- **#2 Stones:** new parameterised `pad_stone()`, `plinth_kind_stone()`, `spall_stone()`, `stone_skin()` and `dir_grid()` (dense mesh over the visible front and top, sparse back and bed).
  - **(a) Pads:** 6-8-corner irregular plan 0.46 × 0.36. Battered planar sides, 2-3 planar split faces at about 3-5 mm LSE arrises, flat bed tilted 1-3°. Visible about 0.17 (PAD_TOP 0.225, earth banked 5 cm).
  - **(b) Plinth:** kinds slab / block / boulder, never the same kind twice in a row. Built 15 / 10 / 11 (42 / 28 / 31 %); slabs are 0.62-0.84 long and 0.17-0.22 visible. Each stone has 6-12 planar flake scars (plane tilted 6-16°, 4-10 mm deep, 8-20 cm, soft window so the crease is the plane line), 1-1.4 cm lumps at about 12 cm, and pits. Arris k varies by kind (slab 4-6 mm, block 6-9, boulder 10-14) and along each edge. A crisp fracture plane is on 62 % (actual 19/36 plus uppers). Auto-smooth is 30° so the creases read.
  - **(c) Threshold and step:** tops undulate about 1.3 cm at about 20 cm, with 2-3 planar spalls 2-5 mm deep. The arris varies 0.5-2.5 cm with chips. The fracture planes are removed (they stair-stepped on the polar mesh). The step is bedded deeper (0.16) with an earth lip on about 55 %.
  - **(d) Flags:** tops 4.7-6.2 cm proud, so ≥ 2.5 cm of vertical edge shows where there is no lip. Lips are 0.8-1.4 cm high and 3-4 cm wide on 30-50 % of the perimeter. The apron is a 2 cm grid over the path, with vertices snapped onto each flag outline, and is culled only below the bare earth (no saw-tooth). Same undulation and spalls as (c).
  - **(e) Clumps:** 3 torn daub sleeves 4-8 cm long, wrapped round real rod paths (stored from `weave_panel`) just under the break.
  - **(f) Rubble:** 5-8 planar fracture faces with 2.5 mm arrises.
- **#3 Holes:**
  - (a) `HUT_daub_interior` now runs the full circumference.
  - (b) New `build_eave_closure()`: a daub band on the inner half of the plate, from the plate top into the shingle stack. Its top is lowered automatically wherever a missing shingle would expose it. Note: this band, not a full-360° `HUT_roof_blocker` as the must-fix asked, is what seals the roof underside; the blocker still leaves the back window open where full-length shingles are seen through the door.
  - (c) Two split packing stones under each cheek sole rail.
  - Acceptance test: rays through the doorway from eye-level cameras on r = 5 m and r = 2.2 m arcs (az -60..+60°, 13 each), plus the frame_raking and inside_left cameras, give **0 misses of 54,804**.
- **#4 Adze:** `hewn_member()` now uses stroke-aligned topology. Each adzed face's vertex columns are slid along the member by -skew·across (plus a slight per-face bow), so every vertex row lies on a stroke boundary, with no stair-steps. The shear ramps out over the last 12 cm so the end cuts stay square. Hero posts and jambs are sampled at 7 mm along the member with 10-11 points across each face. One stroke lane per face (no lane-seam steps). The sill has no adze beads; it has 3-4 irregular soft lumps or hollows plus slow undulation on the front.
- **#5 Daub:**
  - (a) The door-bay edge runs post to post at z 0.62-1.0 (base 0.79, ±5 cm at about 8/m plus ±3.5 cm at about 15/m), with 3 asymmetric bites of 8-13 cm. Scabs stay within 10 cm of the edge, so nothing is below z 0.5.
  - (b) The side patch is 0.74 × 0.42, elongated horizontally. Its top and bottom margins step by one or two rod rows (36 mm) at 6-22 cm runs, the ends are ragged and there are no lobes. It is pressed in about 0-1 cm proud of the rod fronts, with rods kept over the outer 13 cm.
  - (c) The cut boundary of every sheet is Newton-snapped onto the field contour, so there are no grid steps.
  - (d) The daub top sits 4.5 cm under the plate and the rods above it are kept. Posts are cut square under the plate (1.6 cm head chamfer only), so there is no tapered post-head sliver.
- **Known gaps:**
  - A drying check that crosses the adze strokes on the hero face of the left door post leaves a small zipper-like crease (post_close).
  - A few flag-lip margins still show a faint fringe from the 2 cm grid.
  - 4 short spans of the eave closure sit in the shadow of missing shingles. The band is lowered there, but those spans still show through the shingle gap from above.
  - Moss cushions are not modelled.


## CLIENT CORRECTION — the exterior is MOSTLY INTACT DAUB (supersedes the earlier exposed-wattle balance)

The client says there is too much exposed wattle.

- **Daub coverage.** The exterior walls must be **mostly intact daub, about 80–90% of the wall face**.
- **Exposed wattle** appears only in **small sections**: about 3–5 patches around the whole hut, each roughly 0.3–1.0 m², where the daub has fallen away. Each patch has an eroded, ragged, thick daub edge, with rods visible beneath and a few clinging clumps. This is the existing "daub bay" erosion language, inverted.
- **The door side panels** may keep their visible woven rope look if they read as intentional framing. Otherwise daub them too.
- **Daub surface.** Keep a hand-applied, slightly bulging coat with shrinkage cracks, a weathered lower margin and slight sag. Avoid flat board-like daub.
- **Hidden geometry.** Rods behind intact daub become hidden geometry. **Delete them.** Keep wattle only inside the exposed patches, plus about 10 cm under the patch edges. Re-check est_hidden_pct ≤ 15%.
- **Ground dressing.** Per producer note 10, delete all path flags, stepping stones, ground rubble and the ground apron. Keep the stone plinth, the door-post pad stones and the threshold.

## Round 6 — builder entry
- Script `buildings/wattle_roundhut/build_wattle_roundhut.py` (seeded, ~27 s build), saves `wattle_roundhut.blend` (28.6 MB). Renders: `renders/wattle_roundhut/round_06/` (6 views, 32 spp, stats.json, hidden.json).
- **Stats:** 1,333,964 tris. **est_hidden_pct 12.9 %.** **material_slot_count 10**, all from the palette. `mask_attribute_missing` is empty. 123 objects (99 linked duplicates from 22 pools). bbox min (-4.19, -4.59, -0.041), max (4.19, 4.20, 8.73).
- **Client correction: mostly intact daub.**
  - Every one of the 13 bays now carries the daub coat (`make_daub_fields`, `low_margin`, `daub_hole`, `poly_sdf`).
  - Coverage was ray-measured with horizontal rays at z 0.45-2.6 all round. Daub is the first hit on **86 %** of the wall face; posts are 11 %, exposed rods 2 % and stakes 0.1 %. Leaving out the posts, the coat covers 97 % of the infill.
  - **Exposed wattle: 4 patches.**
    - (1) The ref2 eroded band left of the door, kept as approved: post to post, edge at z 0.62-1.0, about 0.7 m² (front, hero, actor_closeup).
    - (2) A break at mid-height on the +X side, about 0.4 m² (side view).
    - (3) A low break above the plinth, back-right, about 0.35 m² (back view).
    - (4) A break under the eave, back-left, about 0.3 m² (hero, aerial).
  - **Patch outlines.** Patches 2-4 are fracture polygons: 9-14 straight breaks with sharp corners and 2-3 re-entrant notches, so no oval ports. Their top and bottom margins step along the rod rows. The thick broken edge is the existing erosion ramp (behind the rods, up to 8.8 cm proud in about 4.5 cm). Two torn daub sleeves are wrapped round the exposed rods in each patch, and three in the door bay.
  - **Coat surface.**
    - Hand-applied dabs (handful pats 6-11 cm) and a sag belly 0.6-0.9 m up.
    - Palm dents, bulges, and 2-4 shrinkage cracks per bay.
    - A splash-eroded foot: thinner and pitted over the bottom 25 cm, with occasional bites that show the bottom rod row.
    - Rod ridging only where the coat thins at a patch margin.
  - **Coat top.** The coat now runs up into the wall plate. There is no gap, so there are no rods and no pale chips under the plate.
  - **Mesh.** A graded tensor grid: 7.5 mm at patch margins and cracks, 1.05 cm at the foot, 1.6 × 1.3 cm on the intact coat.
- **Hidden geometry.**
  - Rods and stakes buried in the coat are deleted. Rods are kept only in the patches, plus 7 cm under their margins and about 3.5 cm (the bottom row) under the foot. `HUT_wattle_rods` went from 404k to about 80k tris, about half of it the door rope panels.
  - The post flanks buried in the coat and the post backs are culled (`post_cull`). The two door-bay wall posts are kept whole on their door side.
  - The plinth tops under the daub foot are culled (`plinth_under_coat` / `cull_object`).
- **Producer note 10.**
  - Deleted: `HUT_ground_apron`, all path flags, ground rubble and the earth mound, drip trench and bank, with their code (`build_apron`, `build_rubble`, `_mound`, `_path_mound`, `apron_phi`, flag lips).
  - The building stands on a flat Z = 0 datum. Footing, pads, step and threshold keep a buried skirt of at most 4 cm (`GROUND_SKIRT`).
  - Kept: plinth and chinking, door-post pads, cheek packing stones, threshold slabs and sill, and the built-in step (`HUT_step_stone`).
  - The pad stones now have near-upright sides (batter 5-13°), so no flared foot shows on bare ground.
- **Unchanged from round 5:** door rope side panels (they read as intentional framing, so they are kept), entrance timber (stroke-aligned adze), plinth stones, roof, apex.
- **Known gaps:**
  - A few plinth stones show small stair-stepped flake-scar edges at about 1 m (pre-existing `stone_skin`).
  - Crack groove lips can zigzag slightly at under 1 m.
  - The drying-check crease on the left door post from round 5 is still there.
  - Moss cushions are not modelled.

## Round 6 — score 8.3/10

**What I reviewed.**
- All 6 views, stats.json and hidden.json in `renders/wattle_roundhut/round_06/`, side by side with `hut_overall`, `hut_door`, `hut_wattle_daub_plinth` and `hut_cap_finial`, and the CLIENT CORRECTION (mostly intact daub) plus producer note 10.
- 12 Director close-ups at 12 spp in `round_06/director_extra/`, rendered with the ground plane at **Z = 0** (the Unreal datum, not the review's -0.041): patch_side, patch_side_near, patch_back_low, patch_eave, door_bay, wall_eye, wall_rake, coat_rake2, coat_close (too dark, ignore), foot_ground, under_plate and door_near.
- Ray-measured radial profiles of the coat and the posts (horizontal rays, az 60-128°, z 1.0 / 1.5 / 2.2). Listed every object in the .blend. Read `DAUB_PATCHES`, `daub_hole()`, `daub_edge_door_bay()`, `low_margin()` and the clinging-clump code in `build_daub()`.
- Ground dressing is **not scored** (producer note 10). Its absence is correct.

**Verdict.** The client correction has landed.
- The hut now reads as a daubed hut with a few breaks, not a wattle hut. Daub is 86 % of the wall face, there are 4 patches of 0.3-0.7 m², and the buried rods are gone.
- All the ground dressing is gone, and the footing sits convincingly on a flat Z = 0 plane.
- Roof, apex, silhouette and scale stay hero quality.

What keeps it below 9 is how the new daub work is crafted. Four CG tells show at actor or thumbnail distance:
- the door-bay break, the most visible one, which reads as dripping icing in the actor close-up;
- the clinging clumps, which render as round beads threaded on the rods;
- a five-point star cut-out on the +X side;
- posts that sit flush with, or behind, a quilted coat.

A continuous dark slot also runs under the coat foot all round the hut. Every one of these is a contained fix. **8.3 clears the user's revised pass mark of 8.2.**

**Axes**

| Axis | Score | Why |
|---|---|---|
| Silhouette | 9 | The cone, lead hat, finial, plinth and projecting door frame all overlay ref2. The daubed wall now matches the client brief. |
| Proportion and scale | 9 | Unchanged and correct: door 1.00 × 2.08, eave ≥ 2.40, shingles about 0.45 m. bbox 8.37 × 8.78 × 8.77. |
| Construction | 8 | Posts are flush with the coat (0-4 cm proud), so the frame does not read as carrying the infill. The coat hangs above the plinth on a continuous slot. |
| Detail and craft | 8 | Bead clumps, an icing-drip door-bay edge and a star-shaped side patch. The coat dabs and cracks read only in raking light. The rope panels, adze work and stones hold up. |
| Age and irregularity | 8 | The roof and stones are convincing. The patch outlines are formulaic: a radial star, and evenly spaced drip teeth. |
| Technical | 9 | 1,333,964 tris (≤ 1.5 M), est_hidden_pct 12.9 % (≤ 15 %), 10 slots all in the palette (M_earth is only the interior floor and M_rubble only the chinking), Mask complete, 123 objects, 22 pools, below-ground 0 %. HUT_daub alone is 718k tris (54 %); see the nice-to-haves. |

**Strengths**
- **Client correction met in substance.**
  - Daub is 86 % of the wall face (97 % of the infill), with 4 small patches and rods deleted behind the intact coat. `HUT_wattle_rods` went from 404k to 81k tris.
  - The back-low patch (patch_back_low.png) is exactly the right language: a near-straight break above the stones, rods exposed down to the plinth and a thick broken coat edge. Use it as the model for the others.
- **Producer note 10 met.** The apron, flags, rubble, mound, trench and their code are all deleted. Rendered on a true Z = 0 plane (foot_ground.png), the plinth, pads, threshold and step meet the ground cleanly with no flared feet and no floating parts. The pad stones now read as upright-sided boulders.
- **The coat surface is not board-like.** Raking light (coat_rake2.png) shows hand-dab relief and a palm dent. The shrinkage cracks are V-section, and a natural shrinkage slit opens at the post. There is no gap and no pale chip under the wall plate any more (under_plate.png; r3 #7 / r4 #5d **CLOSED**).
- **The entrance holds.**
  - The rope side panels read as intentional framing, as the client allowed.
  - The stroke-aligned adze has no stair-steps (door_near.png).
  - The doorway gives dark depth with no see-through (r4 #3 holds).
- **Roof and apex are unchanged hero quality.**

**Closed or accepted**
- These r4 items are CLOSED: #3 (holes), #4 (adze and sill) and #5d (plate chip).
- The r4 #1 open-weave item is superseded by the client correction.
- The r4 #2 pad and plinth items are accepted at r5/r6 quality. Ground dressing items r4 #2d and #2f are void under producer note 10.
- The r4 #5a door-bay edge, #2e clumps and #5b side patch are reopened below, in the new daub context.

### Must-fix (priority order)

1. **DOOR-BAY BREAK READS AS DRIPPING ICING** (`HUT_daub`, door bay az -45..-21°; actor_closeup.png, hero.png, front.png, director_extra/door_bay.png). This is the most visible tell, because it sits in the hero close-up.
   - **What's wrong:** `daub_edge_door_bay()` adds Gaussian bites and n2 noise, which gives evenly spaced rounded lobes pointing DOWN. They are about 12-18 cm apart and 6-10 cm deep, with a soft pillowed lip, so they read as frosting or wax drips. ref2 (`hut_wattle_daub_plinth`) shows a ragged but essentially horizontal fracture line.
   - **Fix, break line:** make the break a fracture line at z 0.72-0.95.
     - Build it from straight runs of 8-25 cm that step by 1-2 whole rod rows (3.6-7.2 cm; reuse `stepped_curve`).
     - Join the runs with short vertical or diagonal breaks that have sharp corners (radius ≤ 1 cm).
     - **No downward-pointing convex tooth narrower than 12 cm.**
   - **Fix, bites:** turn the 3 bites into flat-floored notches stepped UP by 2-3 rod rows (7-11 cm), not Gaussian dips.
   - **Fix, edge face:** the broken edge face is 2.5-4 cm thick and within 30° of the wall normal, with a crisp outer arris (radius ≤ 5 mm) and 3-6 mm grit relief on the fracture face. Feather the coat thin over the rods (ridging) along only about 30 % of the edge length.

2. **CLINGING CLUMPS RENDER AS ROUND BEADS ON THE RODS** (`HUT_daub` "sleeves", `build_daub()` lines about 2722-2772; actor_closeup.png shows 3, plus door_bay, patch_side_near, patch_back_low, patch_eave and foot_ground).
   - **What's wrong:** a 4-8 cm, 12-sided closed tube with a (1-t²)^0.6 thickness profile, up to about 2.5 cm proud, is a spindle bead. It reads as knots or beads threaded on the withies.
   - **Fix:** replace each clump with a flat torn FLAKE of coat.
     - Size: 8-15 cm wide × 5-10 cm tall, bridging 2-3 adjacent rod rows on their front face. Thickness 1-2 cm, with a flat dab-textured front.
     - Outline: polygonal and torn, with 4-7 straight breaks, the same fracture language as #1.
     - Placement: preferably still attached to, or within 8 cm of, the main break.
   - **Not allowed:** a closed sleeve round a single rod, or any rotationally symmetric bulge.
   - **Count:** at most 2 per patch and 3 in the door bay. Deleting them is better than keeping beads.

3. **+X SIDE PATCH IS A FIVE-POINT STAR CUT-OUT** (`DAUB_PATCHES` bay 2, az about 82°, z 1.0-1.6; side.png, where it reads at thumbnail size; patch_side.png, patch_side_near.png).
   - **What's wrong:** `daub_hole()` places 9-14 vertices at radius 0.72-1.12 × the half-size and pulls 2-3 of them in to 0.55-0.75, which alternates spikes and notches into a star.
   - **Fix, outline:** build the outline as a broken, irregular quadrilateral or pentagon.
     - Use 4-6 principal breaks, a width:height of 1.4-2.2:1, and top and bottom margins near horizontal along the rod rows (stepped by 1 row over runs of 8-25 cm).
     - Sides are vertical (often following a stake) or diagonal at 30-60°.
     - Allow at most ONE re-entrant notch, ≤ 25 % of the patch height deep. No convex corner sharper than 70°.
   - **Eave patch (bay 10, az about 275°, patch_eave.png):** it is a rounded lens with a pillowed lip. Give it the same outline and the crisp edge face of #1.
   - **Target:** match the back-low patch (patch_back_low.png).

4. **POSTS SIT FLUSH WITH THE COAT, SO THE WALL READS AS QUILTED CUSHIONS** (`HUT_daub` against `HUT_posts`; wall_eye.png, coat_rake2.png, side.png, back.png).
   - **Measured:** horizontal rays at z 1.0, 1.5 and 2.2 put the post fronts at r 3.58-3.63 and the coat at r 3.56-3.61. Posts are 0-4 cm proud, and the post at az about 93° is flush. Each bay bulges up to the post, so the posts read as narrow grooves between pillows. In ref2 the posts stand clearly proud of the infill.
   - **Fix, coat face:** bring the mean coat face back to r 3.555-3.57 (2-4 cm over the rod fronts, lumps ±1.5 cm).
   - **Fix, post margin:** within 8-12 cm of each post, let the coat dip a further 1-2 cm into the existing shrinkage slit, so every post face stands **5-8 cm proud** of the coat over its full height.
   - **Fix, sag belly:** keep it, but at ≤ 1.5 cm amplitude.

5. **CONTINUOUS DARK SLOT UNDER THE COAT FOOT ALL ROUND** (`low_margin()`; hero.png, side.png and back.png show it as a dark ring line at thumbnail; wall_eye.png, patch_back_low.png).
   - **What's wrong:** the coat stops 2.8 cm or more above the stone tops in every bay, so a black slot and the bottom rod row run unbroken round the hut, and the coat reads as a curtain hanging over the plinth.
   - **Fix, contact:** bed the coat foot onto the stone tops, as a rough fillet pressed into the stone joints, along **≥ 65 % of each bay's length**.
   - **Fix, bites:** show the bottom rod row only in 1-3 splash-eroded bites per bay, each 10-30 cm long and 3-8 cm tall.
   - **Keep** the culling of plinth tops under the coat consistent with the new contact line, so no holes open.

**Nice to have**
- **Daub budget.** `HUT_daub` is 718k tris (54 % of the asset) at a 1.6 × 1.3 cm grid over the intact coat, but the relief that reads is ≥ 6 cm wavelength.
  - Coarsen the intact field to about 3 cm and keep 7.5 mm only at margins and cracks. That should give about 250-300k.
  - Spend part of the saving on the fracture faces of #1 and #3.
- Pre-existing items:
  - Small stair-stepped flake-scar edges on a few plinth stones at about 1 m.
  - The drying-check zipper crease on the left door post.
  - Crack-lip zigzag under 1 m.
- Moss cushions remain optional.
- **Mask:** set G high on the patch fracture faces and B high on the coat foot.
