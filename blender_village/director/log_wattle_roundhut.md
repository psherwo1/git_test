
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
