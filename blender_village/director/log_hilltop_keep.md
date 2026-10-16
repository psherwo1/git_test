# LOG: hilltop_keep

## Round 1 — score 7/10

**Reviewed:** renders/hilltop_keep/round_01/ — all 6 views plus stats.json. hero, front and side are the builder's 32-sample renders. The builder's background render had stopped, so the Director rendered back, aerial, actor_closeup and stats.json at 24 samples. The Director also rendered extra close-ups in renders/hilltop_keep/round_01/director_extra/:
- door, door_mid, hinge_graze
- eave_under, collar_cone, lantern_cap
- wing_turret, wing_door, back_wing
- wing_hall_n, wing_hall_s, ne_hall

**Stats:**
- 43 objects and 1,186,774 tris.
- bbox x −10.94..5.30, y −5.30..5.53, z −0.20..14.00 (size 16.24 × 10.84 × 14.20 m).
- .blend is 26.7 MB.
- All objects have identity transforms, UVs and named material slots.

**Verdict:** a strong round 1. At thumbnail size this is clearly ref1's keep. The tiers are in the right order with the right relative widths: skirt about 10.5 m, collar about 6.7 m, cone base about 4.5–5.3 m, cone top about 2.5 m and cap about 3.9 m. The finial tip is at 14.0 m and the door scale is correct. It is not yet film close-up quality, for three reasons:
- The wing "thatch" reads as clay pantiles or scales.
- All masonry reads as soft rounded-rectangle tiles floating in wide mortar joints. On the cone, the stones look glued onto a smooth plaster cone.
- The door strap hinges are modelled as horizontal fins.

Also, the turret is a near-cylinder where ref1 shows a strongly tapered stone cone, and the ridge comb reads as a picket fence. Score by axis:

| Axis | Score |
|---|---|
| Silhouette | 8 |
| Proportion and scale | 8.5 |
| Construction | 7 |
| Detail and craft | 6.5 |
| Age | 7 |
| Technical | 8.5 |
| **Overall** | **7** |

**Strengths:**
- Tier stack and silhouette match ref1: bell-cast octagonal skirt, steep shake collar with a comb, concave candle-snuffer cone, board lantern with a propped hatch, bell-cast cap and a slender leaning finial.
- The skirt underside holds up at eye level: sprocketed rafters, jack and hip rafters, soffit boards, fascia, and a lap-jointed eave plate with crossed ends.
- The skirt covering uses horizontal long-board courses, as in ref1, with saddle hips and a few slipped boards. The cap shingles have good hip boards.
- The main door is well composed: 13 irregular voussoirs thicker at the crown, alternating jambs, a 7-plank arched leaf with a split plank, ring pull, keyhole plate, threshold and step. Human scale is right.
- 8 posts on pedestals with pegged curved knee braces. Real wall depth at the openings, with the interior visible through them.
- Technical hygiene: deterministic build, collections, naming, identity transforms, UVs, and within budget.

### Must-fix (priority order)
1. **The wing thatch reads as tiles, not thatch** (`KEEP_wing_roof_thatch`; see director_extra/wing_hall_n.png, back_wing.png, wing_turret.png). Each unit is a discrete rounded tile with a ragged bottom and vertical slots between neighbours, so the roof reads as pantiles or fish scales.
   - Rebuild it as continuous stepped courses: about 0.30 m exposure, 0.06–0.10 m butt step, and **no vertical gaps between units**.
   - Each course butt is a dense fringe of tapering strand clumps: 1.5–3 cm pitch, ±4 cm length variance, splay ±8°.
   - The course line waves ±3 cm at low frequency.
   - The top surface carries fine raking striations along the fall line, 1–2 cm wide and 0.5–1 cm deep.
   - Keep the heavy rounded eave roll at 0.40–0.45 m.
   - Targets: ref1 keep_west_wing_turret.png (smooth, heavy, felted mass) and style_thatch_and_tiered_tower.png (stepped fibrous layers).
   - Up to about 250k tris may be spent here.
2. **The main door strap hinges are fins** (`strap_hinge()`, `KEEP_door_ironwork`; see director_extra/hinge_graze.png).
   - The profile `(wd/2, ±0.003)` is flipped by `[:, :, ::-1]`, so each strap is 6 mm tall and 50 mm deep, a horizontal shelf sticking out of the leaf. The nail heads sit on the plank above it, not on the strap.
   - Fix: the strap lies flat on the leaf, 50 mm tall tapering to about 38 mm, 6 mm proud, with a spear terminal about 80 mm wide. Seat the nails on the strap face.
   - Check the same on `KEEP_wing_door_ironwork`.
3. **Masonry joints and stone faces** (hall, wing, turret and especially the cone; see director_extra/collar_cone.png, door_mid.png, wing_door.png). The stones read as soft rounded-rectangle "soap" tiles floating in mortar.
   - (a) **Joints.** The outline shrink (end shrink clipped at 0.07 m, corner cuts up to about 0.65 × the half-size) opens 4–8 cm joints. Clamp it so visible joints are 1–3 cm, and fill any void over 3 cm with pinning stones.
     - Hall, wing and turret: visible mortar ≤ 15% of the wall area.
     - Cone: visible mortar ≤ 20%. Today it is about 40% and reads as stones glued onto smooth plaster. The cone stones must pack densely.
   - (b) **Face resolution.** The 5×5 and 7×7 face grids cannot carry relief. In the hero zone, use a front face of at least 14×10 with chisel and split facets of 0.5–2.5 cm and broken, chipped arrises. The hero zone is the −Y, SW and SE facets and the wing's south wall, below 3.5 m.
   - (c) **Protrusion.** Vary it from 0.5 to 4 cm, with some faces tilted back up to 3°. Vary the arris radius from 0.5 to 3 cm per stone. Today every stone has the same extruded vertical sides and uniform rounding.
4. **Dressed stone is CG-perfect** (door jambs and voussoirs, window jamb blocks, the about 1.5 m SW window lintel, the NE window blocks, post pedestals and wing quoins). Today they are perfect rounded boxes with dead-flat faces.
   - Add tooled faces: 2–5 mm undulation and an optional 2–3 cm drafted margin.
   - Add 2–4 arris chips per block, 1–3 cm each.
   - Set blocks ±1–2° out of square, with extra wear on the lower jamb blocks and the threshold.
5. **Turret silhouette** (`KEEP_turret_stones`, `KEEP_turret_corbel_collar`).
   - ref1 shows a strongly tapered stone cone: the visible flank leans about 20–25° off vertical below the cushion. The build is a near-cylinder (Ø 3.4 → 2.6 over 6 m).
   - New concave profile: about Ø 4.0 where it leaves the wing roof (about z 2.5–3.0), down to Ø 2.5 just under the cushion (5.9 m). Let it protrude beyond the north wing wall as needed.
   - Cushion collar: a bulbous, soft, mushroom-like ring (ref1) projecting 0.25–0.35 m beyond the stone body and the drum, max Ø about 3.0–3.1, with a rounded top. Use large, irregular, rounded stones or a sculpted bulge, not 3 neat corbel courses of wall-sized stones.
6. **Wing ridge comb reads as a picket fence** (`KEEP_wing_ridge_comb`; see director_extra/wing_turret.png).
   - Today: evenly spaced, vertical, pencil-pointed stakes.
   - ref1: splayed, crossed split shakes in V/X pairs, each leaning 20–35° to either side of the ridge, 0.3–0.5 m long, irregular spacing 0.15–0.3 m, blunt split ends, held by the ridge-rider log with pegs.
7. **Collar comb tips are crystal shards** (`KEEP_roof_collar_shakes`; see director_extra/collar_cone.png).
   - Today the shake tops end in acute sawtooth points, and several shakes on the E and W flanks splay out like shards.
   - Tips should be broken or split blunt ends: square to 20–40° diagonal breaks, tip width ≥ 3 cm, about 1 cm bevel, protrusion 0.05–0.25 m, and no tip deviating more than 8° from its shake plane.
8. **Hole through the wing roof.** The north thatch slope near the eave, at about (−5.1, 5.0, 2.7), shows a black rectangular void (back.png, director_extra/back_wing.png, wing_hall_n.png). A missing or slipped unit must expose thatch underneath, never the void. Make the core body continuous under every course.
9. **Skirt/wing junction at the hall's NW corner** (director_extra/wing_hall_n.png).
   - The skirt fascia, the eave-plate/hip end and the boards end as blunt cut boxes floating 0.2–0.4 m above the thatch.
   - Fix: terminate the fascia on a bearing, scribed to the thatch surface. Run a valley or mortar/lead flashing from the skirt eave down into the thatch. Leave no floating plate ends.
   - Check the matching south-side and NE verge junctions too.
10. **The timber is too clean** (`KEEP_hall_posts` at about 200 faces per post, the eave plate, the skirt fascia, the cap and turret eave rings, the wing door lintel).
    - Posts: ±1° lean, ±1 cm swell or taper, and adze facets. Add 1–2 modelled checks on the two posts flanking the door and the post by the SW window.
    - Fascia: wave ±2–3 cm, with butt or scarf joints every 2.5–4 m.
    - Cap eave rings: a visible joint per facet.

**Accepted spec deviations (Director ruling):**
- Wing width 4.2 m at y 0.4..4.6, and turret centre at (−8.65, 3.0).
- Collar foot about 5.0 m and top 6.02 m. Wing pitch 47°. Cap exposure about 0.15 m.
- Spec §6.1's line "turret cap lower than the collar top" is **struck**: in ref1 the turret cap eave reads above the main collar comb. Keep the turret cap eave at about 7.0–7.1 m and the apex at about 8.5 m.

**Nice-to-have:**
- Straighten the skirt's upper profile toward a uniform 35–40°, with the bell only in the last 0.8 m.
- Slim the SW window surround: ref1 shows a simple timber frame in rubble, not heavy dressed blocks.
- Make the knee braces chunkier, as Y-brackets.
- Delete buildings/hilltop_keep/hilltop_keep.blend1.
- Before reporting: deliver all 6 views plus stats.json and append the builder log entry.

## Round 2 — builder entry

**Renders:** renders/hilltop_keep/round_02/ (hero, front, side, back, aerial, actor_closeup at 32 samples, plus stats.json).
**Stats:** 45 objects, 1,462,090 tris; bbox x −11.07..5.30, y −5.30..5.51, z −0.20..14.00 (size 16.37 × 10.81 × 14.20 m); .blend 32.6 MB (compressed). Build is deterministic (identical geometry hash on rebuild), ~30 s. All objects have identity transforms, UVs and named material slots. buildings/hilltop_keep/hilltop_keep.blend1 deleted; the script now saves without .blend1 backups.

**Must-fix items:**
1. **Wing thatch** (`KEEP_wing_roof_thatch_courses`, ~120k tris).
   - Rebuilt as continuous stepped courses, one unbroken strip per course per roof plane, so there are no vertical gaps between units.
   - Courses: ~0.30 m exposure, 0.06–0.10 m butt step, course line waving about ±3 cm.
   - Each butt is a fringe of tapering strand clumps: 1.5–3 cm pitch, ±3.5 cm length, ±8° splay.
   - Clump boundaries continue up the course as striations along the fall line, 0.5–1 cm deep.
   - Heavy rounded eave roll about 0.43 m tall, with its underside at 2.40 m. It is continuous round the hipped corners and carries wrapped strand striations; the eave course rests on it.
   - Thatch total thickness is now 0.30 m core + course, about 0.32–0.40 m.
2. **Strap hinges:** the profile now lies flat on the leaf: 50 mm tall tapering to 38 mm, 6 mm proud, spear terminal about 80 mm wide. Nails sit on the strap face. KEEP_wing_door_ironwork uses the same flat profile.
3. **Masonry:**
   - Pinning-stone void fill now runs on every wall. Visible mortar by footprint, before → after pins:
     - Hall: 13.6 → 9.9 %
     - Wing: 12.6 → 10.4 %
     - Turret: 14.7 → 11.9 %
     - Cone: 20.8 → 13.5 %, with joints tightened to 0.8–1.6 cm.
   - Hero zone uses a 14×10 face grid: hall SW, S and SE facets plus the wing south wall below 3.5 m.
   - Stone faces get 4 chisel/split facets of 0.6–3 cm each, plus chipped arrises.
   - Protrusion ranges 0.5–4 cm, with about a third of the stones tilted back by up to 3°.
   - Arris radius varies per stone from 0.5 to 3 cm.
4. **Dressed stone:**
   - Door jambs, voussoirs, NE/E window blocks and wing quoins now have tooled faces: 4–5 mm undulation, a pitched centre and a drafted margin.
   - Each block has 3–5 arris chips of 1.6–3.8 cm and is set 1–2° out of square. Lower jamb blocks get extra wear.
   - Face grids are 22–30 × 24–32.
   - The post pedestals are tooled, chipped and rotated ±2°.
5. **Turret:**
   - Concave stone cone, Ø 4.0 at z 2.8 down to Ø 2.5 under the cushion at 5.92 m. The base below the roof is Ø 4.0–4.16 and bulges out of the wing's N and W walls.
   - Centre moved 0.2 m east to (−8.45, 3.0) so the base stays within the west eave.
   - The cushion is a sculpted mushroom ring of two rows of fused rounded boulders, max Ø about 3.05, projecting about 0.27 m beyond the body and about 0.35 m beyond the drum, with a rounded top.
6. **Ridge comb:** split shakes in V/X pairs (about 10% singles) crossing on the ridge-rider log.
   - Each shake leans 20–35° to either side; the crossing plane is yawed 12–38° so the V/X shapes read from the south.
   - 0.30–0.50 m above the crossing, spaced irregularly at 0.15–0.30 m.
   - Ends are blunt: square-broken, a 20–40° diagonal break, or a split notch. Pegs remain through the log.
7. **Collar tips:** no pointed tips any more. Ends are square-broken, a 20–40° diagonal break, or split with a 3–7 cm notch. Prong width is at least 3 cm, the bevel is about 0.8 cm, and protrusion is 0.05–0.25 m. Twist is reduced to well under 8° off the shake plane.
8. **Hole in the wing roof:** fixed. Thatch is no longer culled under the hall skirt; it is squashed under the skirt sheathing instead. The courses are continuous, so no void can open.
9. **Skirt/wing junctions:**
   - The higher surface always wins. Skirt pieces buried in thatch are dropped, and thatch under the skirt is tucked beneath it.
   - The skirt fascia is clipped per vertex and scribed down onto the thatch; there are no floating cut ends.
   - Lead flashing runs along the skirt/thatch valley on the W facets and along the collar/thatch intersection.
   - The wing thatch now runs over the hall skirt into the collar, which closes the stair-stepped open end at the ridge. Shakes buried under the thatch are dropped.
   - Wing rafter poles and battens are skipped under the skirt.
10. **Timber:**
    - Posts are hewn members: ±1° lean, ±1 cm swell or taper, adze scallops. Posts c1, c2 and c3 (the two flanking the door and the one by the SW window) carry modelled checks 2.2–3.2 cm deep and 1.2–1.8 cm wide.
    - Eave and raising plates are hewn, with waves and checks on the hero facets.
    - The skirt fascia waves ±2 cm and has a butt joint every 2.5–4 m. Cap fascias wave ±0.6 cm.
    - Cap and turret eave ring beams are one hewn piece per facet, butted or lapped and pegged at the corners. The turret drum sill and head rings are 8 pegged segments.
    - The wing door jambs and lintel are hewn, with checks in the lintel.

**Nice-to-haves done:**
- The skirt profile is now near-uniform at 37–39°, with the bell-cast only in the last 0.8 m. Overall rise and collar heights are unchanged.
- The SW window has a simple timber frame in rubble with a stone sill, and no dressed jambs.
- Knee braces are chunkier (0.17 × 0.16) and shorter Y-brackets springing at 2.78 m.

## Round 2 — score 8/10

**Reviewed:** renders/hilltop_keep/round_02/: all 6 views (hero, front, side, back, aerial, actor_closeup) plus stats.json, side by side with ref1 (keep_overall, keep_west_wing_turret, keep_hall_door_window, keep_cone_lantern_cap, plus a 2× crop of the ref1 wing and turret). The Director rendered extra close-ups (16 spp) in renders/hilltop_keep/round_02/director_extra/:
- door, hinge_graze, eave_under, hall_midshot
- wing_door, wing_thatch_eye, wing_turret, turret_cushion, ridge_comb
- wing_hall_n, back_wing, north_slit, turret_wing_n, wing_west_end, roll_end_ne
- collar_cone, collar_comb, lantern_cap

Ignore wing_hall_s.png: the camera ended up inside the SW window reveal.

**Stats:**
- 45 objects and 1,462,090 tris, which is 97% of the budget.
- The biggest meshes are hall_wall_stones 226k, cone_stones 197k, wing_roof_thatch_courses 134k, wing_wall_stones 92k, turret_stones 75k and wing_roof_thatch 72k. door_leaf is only 3.3k.
- bbox 16.37 × 10.81 × 14.20 m. The finial tip is at 14.00 m.

**Verdict:** a real step up from round 1, and now a solid hero-adjacent asset.
- **Fixed:** the strap hinges, the eave underside, the cone masonry, the collar tips, the north hole and the NW skirt/thatch junction.
- **Silhouette:** at thumbnail size it is unmistakably ref1's keep, and the main tier stack overlays well. The one silhouette miss is the side turret:
  - In ref1 the turret's visible stone flank leans about 25–28° and runs down to the wing eave, with a lopsided, drooping cushion.
  - Ours leans only about 12° (a near-cylinder above the thatch) and wears a symmetric "cumulus" donut cushion.
  - My round-1 numbers (Ø4.0 → Ø2.5) did not match the 20–25° I asked for. That was my error; the corrected profile is below.
- **CG tell:** the biggest remaining CG tell is the wing thatch. The continuous courses fixed the pantile read, but each course butt is now a comb of flat, card-thin teeth. Mid-shot it reads as stacked paper or shredded card. Close up it reads as upward-pointing blades.
- **Small artefacts:** a few open seams and voids remain:
  - a full-height open slot between the turret base and the wing walls;
  - black slivers between the first course and the eave roll;
  - open black bed joints between the door jamb blocks.
- **Other:** the eave and hip rolls read as ribbed tubes. The door leaf and the collar shakes are still milled-clean.

Score by axis:

| Axis | Score |
|---|---|
| Silhouette | 8.5 (turret flare and cushion) |
| Proportion and scale | 9 |
| Construction | 8.5 (seams, missing thatch/stone fillet) |
| Detail and craft | 7.5 (thatch butts, clean planks and shakes) |
| Age | 8 |
| Technical | 8.5 (visible voids; no budget headroom) |
| **Overall** | **8** |

**Strengths:**
- **Strap hinges** are done properly: flat, tapering 50 → 38 mm, spear terminals and seated nails (hinge_graze, door).
- **The eave underside is film-grade** (eave_under):
  - curved sprocketed rafters;
  - soffit boards;
  - a hewn plate with checks;
  - chunky pegged Y knee braces;
  - posts with modelled checks.
- **The stone cone** now packs densely, with tight joints and a convincing candle-snuffer flare (collar_cone).
- **The collar comb** has blunt, broken and split tips, and the crystal shards are gone. **The ridge comb** is crossed V/X shakes on a pegged rider log.
- **Skirt:** straightened to about 38° with a late bell-cast, matching ref1. The lantern, propped hatch, bell-cast cap with hip boards and the slender leaning finial are all strong (lantern_cap).
- **Junctions:** the north-thatch hole is gone. The NW skirt/thatch junction is resolved with a scribed fascia and lead flashing (wing_hall_n).
- **Dressed stone:** the door surround now has tooled, chipped, out-of-square blocks, and the SW window has a simple timber frame, as in ref1.
- **Hygiene:** deterministic, named, UV'd and within budget.

### Must-fix (priority order)
1. **Wing thatch course butts read as card teeth or shredded paper** (`thatch_courses()`, `KEEP_wing_roof_thatch_courses`; see hero, wing_turret, wing_thatch_eye, north_slit, wing_west_end).
   - Today each strand clump is a single flat flap whose butt drops as a thin vertical blade. Seen from below, they read as blades pointing up.
   - **Butt face:** rebuild each course butt as a sheared, bevelled face, cut back about 30–40° from the roof plane and 0.06–0.10 m deep, like dressed reed.
   - **Clumps:** build the butt from rounded, convex strand lobes:
     - Each lobe is 2.5–4 cm wide and at least 1.5 cm thick, with tips rounded at r ≥ 5 mm.
     - No lamina may be thinner than 1 cm anywhere.
     - Lobe protrusion varies ±2 cm, not ±3.5.
   - **Course lines:** add low-frequency swelling of ±2–3 cm over 0.8–1.5 m so the courses are not parallel ruler lines. Vary exposure per course from 0.26 to 0.34 m, and let 1–2 courses per plane pinch out or merge.
   - **Target:** ref1's smooth, felted, heavy mass with soft steps (keep_west_wing_turret.png), not a shake roof.
   - **Budget:** stay at or under about 135k.
2. **Turret flare and cushion silhouette** (`tur_r()`, `KEEP_turret_stones`, `build_cushion()`, `KEEP_turret_corbel_collar`).
   - **(a) Flare.** The visible stone flank should lean 22–28°, as in ref1.
     - New concave radius profile (z: r): 2.6: 2.35, 3.5: 1.95, 4.5: 1.55, 5.4: 1.32, 5.9: 1.25.
     - On the W and N the flank may stand proud of the eave line by up to about 0.3 m, and the stone runs down to the wing eave.
     - The thatch's W hip passes in front of the cone, as in ref1.
     - The centre may move to y 2.5–2.7 to keep the base balanced in the wing.
     - Below 2.6 m the body may stay a Ø4.2–4.7 bulge out of the N and W walls.
   - **(b) Cushion.** Today it is a symmetric lathe donut with two even rows of domes, which reads as a marshmallow or cloud (turret_cushion.png). ref1 shows a lopsided, drooping, slab-like mossy stone cushion.
     - Offset the cushion 0.12–0.18 m toward the E/SE. Projection beyond the body should be 0.40–0.45 m on the E/SE and 0.12–0.18 m on the W/NW.
     - Tilt the top surface down about 8–12° toward the E, and let the lower lip droop 0.10–0.15 m lower on that side.
     - Build it from 9–14 irregular boulders of 0.35–0.8 m. At least a third should have a flat cleaved facet.
     - Crease the joints between boulders 1–2 cm deep, and vary the height ±6 cm around the ring.
     - Remove the uniform fbm "cumulus" lumps.
3. **Open seams and voids (CG tells):**
   - **(a) Turret/wing wall junction.** A full-height open vertical slot, 1–3 cm wide, runs where the turret base meets the wing N wall (about x −9.8, y 4.6, z 0–2.5; turret_wing_n.png, roll_end_ne.png). The same happens on the W wall (wing_west_end.png).
     - Bond the two walls with toothing stones that span the joint every 2–3 courses.
     - Make the mortar body continuous behind both walls. No light or black may show through.
   - **(b) Black slivers between the first thatch course and the eave roll.**
     - North slope: about x −5.6..−4.6, y 5.0, z 2.9 (north_slit.png), plus two spots in roll_end_ne.png.
     - SW, above the roll: wing_west_end.png, right side.
     - Fix: sink the eave course and its core at least 3 cm into the roll along its whole length.
   - **(c) Main door jamb bed joints.** These are open black slots about 1.5–2 cm wide with no visible back (hinge_graze.png). Fill them with `M_mortar` recessed 1–1.5 cm, as on the rubble.
   - **(d) Ridge comb shake butts pierce the ridge roll.** Small triangular shards stick out of the roll 0.1–0.15 m below the rider log at most pairs (ridge_comb.png). End the shake butts inside the log, or bury them at least 3 cm in the roll.
4. **No fillet or flashing where the thatch meets the turret stone** (spec §I). The courses simply intersect the stone, leaving a bare intersection curve (wing_turret, back_wing, wing_west_end).
   - Add a lime-mortar fillet (`M_mortar`) along the whole intersection on S, N and W: 8–12 cm high, 5–8 cm out, irregular. Alternatively, use a lead apron with 12 cm stepped flashing let into the stone joints.
   - Course butts turn up 2–4 cm into the fillet.
   - The W hip rolls must terminate on the fillet rather than diving into the turret at mid-height.
5. **The eave roll and hip rolls read as ribbed tubes** (`thatch_roll()`; see wing_thatch_eye, back_wing, wing_turret). Today the eave roll is a uniform round section about 0.43 m with regularly spaced ribs, like a pool noodle or caterpillar. There is a crease line between the roll and the first course, and the W hip roll carries triangular flaps.
   - Make the eave roll section a flattened, sheared D-shape about 0.42 m high × 0.55 m deep, blended into the first course without a crease.
   - Vary the section ±3 cm along the run, with 0.5–1 m bulges.
   - Rib striations: irregular 1–4 cm spacing and 0.3–1.5 cm depth.
   - Hip rolls use the same D-section, with no flaps.
6. **The door leaves are CG-clean** (`KEEP_door_leaf` at only 3.3k tris and `KEEP_wing_door`; see door.png, hall_midshot, wing_door). Today the planks are dead flat, equal in thickness and width, and crisp-edged, and the split plank does not read.
   - Plank widths: visibly varied, 13–18 cm.
   - Faces: cupped 2–4 mm, with neighbouring planks offset 1–3 mm proud or recessed.
   - Arrises: worn to r 3–6 mm, rounder in the bottom 0.3 m.
   - Bottom edge: uneven ±1 cm, with one corner rotted back 3–5 cm.
   - Split plank: the split must open 3–6 mm and run 0.4–0.8 m.
   - Grain: riven or adzed undulation of 1–2 mm.
   - Spend about 15–25k tris here.
7. **The collar shakes are milled planks** (`KEEP_roof_collar_shakes`; collar_comb.png): flat, constant width and thickness, with crisp edges.
   - Give each shake a riven face: 2–4 longitudinal ridges of 2–5 mm.
   - Taper the width 10–20% and the thickness from 4 to 2 cm along the length.
   - Edge waviness ±5 mm, with about 1 cm arris rounding.
   - Split 5–8% of shakes down 20–40% of their length.
8. **The hero-zone rubble still reads as rounded-rectangle "pillows"** (door, hall_midshot, wing_door; the builder's own known gap).
   - Outlines: at least 30% of stones have non-rectangular outlines (wedges, trapezoids, 5–7 sided pieces with slanted ends), and about 15% have one long edge angled 5–15°.
   - Faces: each stone gets 1–2 large conchoidal or split planes at 5–15° to the face, so the soft pillow shading breaks up.
   - Courses: vary heights over the full 8–25 cm range, with visible pinch-outs. Today the course heights look near-uniform.
   - **Budget for items 1–8:** take triangles from `KEEP_cone_stones` (197k → at most 140k; it never appears in a close-up) and from the hall's N, NE and E facets (non-hero).

**Nice-to-have:**
- **Ridge comb:** ref1's crest is shorter, denser and stubbier. Vary shake length 0.20–0.50 m and thickness 2–4 cm so it does not read as an even row.
- **Wing rafter pole ends** under the eave are flat 12-gon discs flush with the plate. Give them 2–5 cm of variable projection, chamfers and a check or two.
- **Main door voussoirs** are a slightly even fan. Vary their face widths ±20%.

**Rulings:**
- The turret centre (−8.45, 3.0) is accepted. It may move per must-fix 2(a).
- The 1.46M-triangle total is accepted, but round 3 must stay at or under 1.5M.
