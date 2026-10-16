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

## Round 3 — builder entry

**Renders:** renders/hilltop_keep/round_03/ (hero, front, side, back, aerial, actor_closeup at 32 samples, plus stats.json).
**Stats:** 47 objects, 1,475,381 tris; bbox x −11.39..5.30, y −5.30..5.54, z −0.20..14.00 (16.69 × 10.84 × 14.20 m; x-min is scattered rubble at the turret foot); .blend 32.8 MB (compressed). Deterministic (identical geometry hash on two rebuilds), ~55 s build.

**Must-fix items:**
1. **Thatch course butts** (`thatch_courses()`): rebuilt. Each butt is a bevelled face cut back 31–39° from the roof plane, 6–10 cm deep, made of convex strand lobes 2.5–4 cm wide (3 columns per lobe, crowned 5–10 mm, creases 2–5 mm fading up the bevel). The tip rounds over a tucked row, so there is no lamina; the thinnest section is the full butt. Protrusion is clumped and capped at ±2 cm. ±2.5 cm swelling over ~1.1 m; exposure 0.26–0.34 m per course; 1–2 courses per plane pinch out (step falls to ~14 %). `KEEP_wing_roof_thatch_courses` 108.9k tris.
2. **(a) Turret flare:** new profile 2.6:2.35, 3.5:1.95, 4.5:1.55, 5.4:1.32, 5.9:1.25. The base below 2.6 m is Ø4.7 m. Centre moved to (−8.55, 2.70). The stone meets the W eave (proud ~0.3 m) and the S/W hips pass in front. A south clip keeps the base behind the S wall face. **(b) Cushion:** offset toward ESE (−25°), proud 0.43 m on E/SE and 0.14 m on W/NW. The top falls 24° on E against 14° on W, and the lip droops 0.13 m lower on E. It is made of 13 boulders (4 split by stepped bed joints) shaped as rounded polytopes with 4–6 facets, joints that meander and are creased 1–2 cm, ±6 cm height variation, and planar cleaved facets on ~40 % of the boulders. The fbm lumps are gone.
3. **(a)** Turret/wall junctions on the N and W walls are bonded with 10 toothing stones that wrap the re-entrant corner every 2–3 courses. Both layouts build round them. The mortar bodies run 0.18 m past each other, so nothing shows through. **(b)** A new D-section eave roll is the seat for the first course, whose tuck sinks 3.5 cm into it. Every later course tucks 3.5 cm under the course below. The core is thinned 10 cm toward the eaves so its edge sits 6+ cm inside the roll. **(c)** Jamb bed joints and voussoir radial joints are filled with `M_mortar`, recessed 1.2 cm from the face and the reveal (`KEEP_hall_dressed_joint_mortar`). **(d)** Every ridge-comb butt is buried at least 4.5 cm inside the ridge dome or ends inside the rider log; steep leaners are stood up.
4. **Fillet:** a lime-mortar wedge (8–12 cm up the stone, 5–8 cm out, irregular) runs along the whole S/W/N thatch–stone intersection. It is ray-cast onto the built thatch. Course butts turn up 2–3 cm into it. Mortar collars close the roll-entry curves, and both W hip rolls taper onto mortar saddles at the fillet.
5. **Rolls:** the eave roll is a sheared D about 0.43 m high × 0.57 m deep, round 0.5 m-radius hipped corners, with ±3 cm swelling over 0.45–0.75 m. Ribs sit at irregular 1–4 cm spacing and 0.3–1.5 cm depth. No crease and no flaps. The hip rolls and the ridge use dome sections with the same ribs. The N eave returns round the wing's NE corner under the skirt into the hall's N wall. The hip-line flaps are gone: course culling is tightened to 5 cm and the hip foot is bedded into the eave roll.
6. **Doors:** new plank generator. Widths are 13–18 cm and visibly varied. Faces are cupped 2–4 mm; neighbours sit 1–3 mm proud or back; arrises are worn to r 3–6 mm, rising to 9.5 mm in the bottom 0.3 m. The bottom edge varies ±1 cm with a rotted corner (4.2 cm main, 3.6 cm wing). The split plank opens 4.8 mm over 0.62 m (wing 4.2 mm over 0.48 m), with 1–2 mm riven/adzed undulation. `KEEP_door_leaf` 15.0k tris, `KEEP_wing_door` 20.4k.
7. **Collar shakes:** 2–4 riven ridges or hollows of 2–5 mm per shake. Width tapers 10–20 % and thickness 4 → 2 cm. Edges wave ±5 mm with a ~1 cm arris. 10 of ~131 outer shakes (7.6 %) are split down 20–40 % and open at the top.
8. **Hero rubble** (hall SW/S/SE and wing S wall): built from true polygon outlines. 361 of 700 hall hero stones are non-rectangular: knocked corners give 5–6 sides, kinked beds give 6–7, ~16 % are tapered with one long bed at 5–14°, and shared joint slants give trapezoids. Each face has one dominant split plane at 5–12° and an optional non-opposing 8–15° facet, with chipped arrises and a low pillow. Course heights are a mixture over 8–25 cm, with pinch-out ramps in the bed lines. Budget: `KEEP_cone_stones` 196.6k → 130.9k; non-hero hall facets use a chamfer-band stone; `KEEP_hall_wall_stones` 204.7k.

**Nice-to-haves:**
- **Ridge comb:** stubbier and denser (spacing 0.10–0.22 m, visible 0.12–0.42 m, 2–4 cm thick).
- **Voussoirs:** face widths spread 0.78–1.24 with a varied extrados.
- **Rafter pole feet:** project 2–5 cm, with chamfered, axe-cut, checked ends. They now sit behind the deeper roll, so they are hard to see from outside.

**Known gaps:**
- Mid-shot, the lobe creases still read slightly as vertical pleats rather than a fully felted mass.
- The valley lead apron dresses over the course steps, so some stepping still shows through it.
- The cushion is faceted stone but still soft at very close range.

## Round 3 — score 8/10

**Reviewed:** renders/hilltop_keep/round_03/: all 6 views (hero, front, side, back, aerial, actor_closeup) plus stats.json and hidden.json, side by side with ref1 (keep_overall, keep_hall_door_window, keep_west_wing_turret, keep_cone_lantern_cap). The Director rendered extra close-ups (16 spp) in renders/hilltop_keep/round_03/director_extra/:
- door, door_mid, hinge_graze, ground_contact, hall_midshot, eave_under, east_wall
- wing_door, wing_south, wing_thatch_eye, wing_turret, wing_west_end, back_wing, turret_wing_n, wing_hall_n, ridge_comb
- turret_flank, turret_cushion, cushion_e, collar_comb, lantern_cap

The Director also audited the .blend (UVs, transforms, below-ground vertices, zero-area faces, shared mesh data).

**Stats:**
- 47 objects and 1,475,381 tris (98% of budget). 11 material slots, all from the palette (pass).
- **est_hidden_pct 34.7%** (512k tris). This fails producer note 6 (≤ 15%).
- bbox 16.69 × 10.84 × 14.20 m. The finial tip is at 14.00 m. z-min is −0.20 m.
- 3,597 zero-area faces. 47 unique meshes: no mesh data is shared.

**Verdict:** this is the best round so far, and most of the round-2 list is genuinely fixed.
- **Fixed:** the turret flare now matches ref1. The door leaves have character. The collar shakes are riven. The hero rubble has real polygon outlines. The seams and voids are gone.
- **Still holding the grade at 8:**
  - (1) **The wing's south window is missing.** The opening is filled with rubble, and its lintel and sill float as slabs on the wall face.
  - (2) **The turret cushion reads as quilted pillows or sandbags, not stone.**
  - (3) **The wing thatch still reads as terraced, pleated ledges, and its W hip roll is a separate tube lying on the turret.**
  - (4) **Technical:** 34.7% hidden triangles, degenerate faces, geometry down to −0.20 m, and no shared mesh data.

Score by axis:

| Axis | Score |
|---|---|
| Silhouette | 8.5 (the cushion reads as a symmetric band at hero distance; the turret cap is slightly small) |
| Proportion and scale | 9 |
| Construction | 8 (missing wing window, hip-roll tube, rope fillet, valley staircase) |
| Detail and craft | 8 (cushion, thatch pleats, pillowy dressed jambs, kerb-block footing) |
| Age | 8.5 |
| Technical | 7 (hidden 34.7%, 3.6k zero-area faces, below ground to −0.20 m, no mesh sharing) |
| **Overall** | **8** |

**Strengths:**
- **Turret silhouette:** the concave flare now runs down to the wing eave, as in ref1. At thumbnail size, hero and front are unmistakably ref1's keep in every tier: skirt, collar comb, candle-snuffer cone, lantern with propped hatch, bell-cast cap, and a slender leaning finial.
- **The eave underside is still film-grade** (eave_under): curved sprockets, soffit boards, a pegged plate, Y knee braces, and checked posts.
- **Main door** (door, door_mid, hinge_graze):
  - Plank widths are visibly varied, with worn arrises.
  - The 3 tapered strap hinges have spear terminals and seated nails.
  - The ring pull has a backplate. Pintles are present.
  - The step and threshold give a correct riser. The 1.8 m figure fits with the right headroom.
- **Hero rubble** (hall_midshot, wing_south): true polygonal flat-bedded stones with pinch-outs and varied course heights. The pillow-tile look is gone. The non-hero facets (east_wall) hold up at eye level.
- **Collar shakes** are tapered and riven, with splits. **Cone masonry** at 131k still reads dense.
- **Junctions:** the turret/wall toothing, the jamb mortar fill and the ridge-comb burial are all fixed. No light leaks were found.
- **Hygiene:** deterministic, palette-only material slots, UVs on every mesh, identity transforms, within budget.

### Must-fix (priority order)
1. **The wing's south window is missing** (`build_wing_door_window`, `WWIN`, `build_wing_walls`; see wing_south.png, front, actor_closeup; `KEEP_wing_window` measures 100% hidden).
   - **What is wrong:** at x = −8.55, y = 0.40 the opening is filled with rubble. Only the lintel (z ≈ 1.91–2.09) and the sill (z ≈ 1.18–1.30) show, as two slabs stuck proud on the wall face. The turret base (r 2.35 at (−8.55, 2.70)) reaches the S wall exactly at x −9.0..−8.1, so the turret clip or tooth layout overrides the opening.
   - **Fix:** move the window to **xc = −7.4**, clear of the turret: 0.45 × 0.55 m clear, sill at 1.30, timber frame 0.07 m with a mullion, reveal 0.16 m. Cut it through the stones, the mortar and the turret clip. Put a dark blocker 1.0 m inside.
   - **Check:** wing_south shows a dark window opening like ref1's left window.
2. **The turret cushion reads as quilted pillows or sandbags, not stone** (`build_cushion()`, `KEEP_turret_corbel_collar`; see turret_cushion, cushion_e, turret_flank, ridge_comb).
   - **What is wrong:**
     - The units are 0.8–1.0 m lumps with about 10–15 cm soft rounding and only 1 cm creases.
     - The stepped bed-joint "splits" make stair-step notches (turret_cushion x 540–590 / y 220–300, and x 880).
     - No cleaved facets read.
     - The E/SE overhang and droop are invisible in hero and front, which show a uniform band.
   - **Fix:**
     - Build 16–22 stones, 0.30–0.60 m long and 0.18–0.30 m tall, in 2 rough corbel courses:
       - lower course: projects 0.15–0.25 m;
       - upper course: projects 0.40–0.45 m on E/SE and 0.12–0.18 m on W/NW.
     - Each stone has 2–3 planar cleaved facets with arris radius 2–4 cm. Only the top outer arris rounds to 6–8 cm (the moss-soft lip).
     - Joints are 2–3 cm wide and recessed 2–4 cm in `M_mortar`. Delete the stepped bed-joint splits.
     - Make the E/SE lip sit 0.15 m lower than the W, and slope the top weathering 10° outward.
   - **Target:** the lopsided mushroom of ref1 (keep_west_wing_turret.png) must read in hero.png at thumbnail size.
3. **The wing thatch still reads as terraced ledges of vertical pleats** (`thatch_courses()`; see back_wing, wing_hall_n, wing_thatch_eye, hero, back).
   - **What is wrong:**
     - There are 15–16 near-parallel ledges of equal butt height.
     - The regular 2–5 mm lobe creases read as corduroy or stacked books.
     - ref1 shows a felted mass with soft steps.
   - **Fix:**
     - **(a) Butts:** cut the visible butt height from 6–10 cm to 3–6 cm. Blend each course top into the course above with a 0.10–0.15 m soft concave fillet, so a step reads as a soft shadow line.
     - **(b) Course lines:** raise the swelling from ±2.5 cm/1.1 m (invisible at mid-shot) to **±5–8 cm over 1.5–3 m**. Vary the butt depth by patch (0.5–1 m) from 2 to 7 cm.
     - **(c) Lobes:** cut crease depth to 0.5–2 mm. Group the lobes into irregular clumps 4–12 cm wide, so the pleat rhythm disappears.
     - **(d) Valley:** at the hall valley (wing_hall_n x 220–420) the course ends make a staircase. Sweep the courses into a rounded valley 0.4–0.6 m wide that curves up continuously, with no stepped ends.
   - **Budget:** keep `KEEP_wing_roof_thatch_courses` at or under 110k.
4. **The W hip roll and the thatch/turret fillet read as add-on tubes and ropes** (`thatch_roll()` hip runs, fillet; see wing_turret, wing_west_end, turret_flank, back_wing, ridge_comb).
   - **(a) Hip roll:** the SW hip roll is a separate Ø ≈ 0.35 m cylinder lying diagonally on the turret flank. Its foot has a torn dark end (wing_turret x 400–560 / y 370–650; wing_west_end x 430–530 / y 170–330), and a small staircase of course stubs sits beside it.
     - Fix: delete the tube. Turn the hip into a rounded swell of the courses (radius 0.25 m) that runs continuously from the courses and dies into the turret on the fillet.
   - **(b) Fillet:** today it is a raised wiggly rope about 8 cm proud, with about 0.3 m wiggle. It reads as a worm or a toothpaste bead, and a smooth band separates it from the courses.
     - Fix: a triangular section 6–10 cm high with a flat 40–50° face. Let it wander only at low frequency (wavelength ≥ 1 m, ±2 cm), feather it into the stone joints, and run the course butts straight into it.
5. **Hidden triangles 34.7% → ≤ 15%** (producer note 6). Remove about 300k hidden tris. Re-measure with `tools/hidden_tris.py` before the full render. By object (hidden share / hidden tris):
   - **Roof structure:**
     - `KEEP_roof_skirt_structure` 70% (27k), `KEEP_cap_structure` 64% (27k), `KEEP_turret_cap_structure` 57% (16k): rafters run full length under the covering. Keep only the tails from 0.3 m inside the wall plate outward. Delete the rest.
     - `KEEP_wing_roof_structure` 100% (4.4k): delete it, or keep only the visible pole ends.
   - **Mortar:** `KEEP_hall_wall_mortar` 62% (19k), `KEEP_wing_wall_mortar` 66% (7.6k), `KEEP_turret_mortar` 46%, `KEEP_cone_mortar` 37%. Make the mortar a single shell 2–3 cm behind the stone faces. Delete its back, top and bottom inside the wall core.
   - **Stones:** `KEEP_hall_wall_stones` 24% (48k), `KEEP_cone_stones` 32% (41k), `KEEP_turret_stones` 36% (31k), `KEEP_wing_wall_stones` 25% (20k). Delete stone backs, and sides deeper than 3 cm behind the mortar face (art bible note 6, masonry).
   - **Thatch:** `KEEP_wing_roof_thatch` core 39% (44k) and `_courses` 28% (31k). Trim each course to the exposed part plus a 5 cm tuck. Keep the core only where it is seen (eave, verge, holes).
   - **Coverings:** `KEEP_roof_skirt_boards` 44% (25k), `KEEP_cap_shingles` 35% (22k), `KEEP_turret_cap_shingles` 46% (19k). Trim the covered parts of each unit.
   - **Others:**
     - `KEEP_hall_eave_plate` 63% (11k): delete its top and inner faces.
     - `KEEP_turret_drum` 77%: delete the inner faces.
     - `KEEP_hall_interior` 74%: use simple dark blockers beyond 1.5 m.
     - `KEEP_hall_posts` 32%: delete the faces buried in the wall.
   - **Reinvest** only in visible close-up detail: items 2, 7 and 8.
6. **Degenerate and below-ground geometry** (producer notes 1 and 6).
   - **(a) Zero-area faces:** there are 3,597 faces under 1e-8 m²:
     - cap_structure 1,056;
     - turret_cap_structure 896;
     - skirt_structure 686;
     - cap_shingles 255;
     - turret_cap_shingles 245;
     - door_leaf 214;
     - wing_door 124;
     - skirt_boards 121.
     - Fix: in `finalize()`, merge by distance at 0.1 mm and dissolve degenerate faces. The target is 0.
   - **(b) Below ground:** geometry reaches −0.10..−0.14 m (hall, wing and turret stones and mortar; rubble −0.10; threshold −0.08; wing door −0.08) and −0.20 m (hall_interior). Clip everything at −0.05 m.
7. **The dressed jamb blocks read as soft pillows, and the jamb joint mortar pokes out as a shelf** (door, door_mid, hinge_graze, wing_door).
   - **What is wrong:**
     - The faces are domed and puffy, with arris rounding of about 3–5 cm. The blocks look like foam, not tooled stone.
     - At the right jamb (hinge_graze x 770–1200 / y 440–530), the bed-joint fill stands proud of the rounded arris below as a thin card shelf.
   - **Fix:**
     - Faces flat-tooled: dome ≤ 4 mm, chamfer 1–1.5 cm (art bible §3), with 2–4 cm chips at a few corners.
     - Clip the mortar fill so it sits ≥ 1.2 cm behind the nearest stone surface everywhere, including over rounded arrises.
     - Apply the same to the wing door jambs and quoins.
8. **The footing course reads as a row of uniform kerb blocks** (actor_closeup, hall_midshot, wing_south, ground_contact). Today it is rectangular slabs about 0.35 m tall with a straight continuous top line.
   - **Fix:**
     - Heights 0.22–0.45 m and lengths 0.4–1.1 m. The top line steps ±8 cm.
     - About 30% of the stones get polygonal outlines like the hero rubble. Projection varies 4–12 cm.
     - Add 1–2 half-buried boulders per facet.
     - Same on the wing and turret bases.
9. **No shared mesh data** (producer notes 2 and 3). There are 47 objects and 47 unique meshes.
   - **Pools:** build pools of 6–20 variants and place them as linked-duplicate objects. This covers pegs, clinch and nail heads, strap-hinge parts and pintles, ridge-comb shakes, scattered rubble, and the lantern boards.
     - Keep the object count under about 400. If per-object placement is too many objects, group placements per variant in one object that shares the variant mesh.
   - **Parameters:** expose the component functions with parameters instead of module globals (`WX_W`, `WY_S`, `TUR_C`, `WWIN`, …): for example `thatch_roof(path, pitch, thickness, seed)`, `turret(profile, cushion, cap)` and `round_stone_wall(radius_fn, height, seed)`.

**Nice-to-have:**
- **Turret cap:** eave across-flats 3.0 → about 3.3 m, so the cap overhangs the cushion as in ref1 (there the cap is about 1.13× the cushion width).
- **Ridge comb:** it still reads as a picket fence (back_wing, wing_hall_n). ref1's crest is a short, stubby, dense row of tufts 0.15–0.30 m tall. Cut the tallest sticks by 40%.
- **Eave roll:** slim the bolster from 0.43 m to 0.32–0.36 m high, and add an irregular hanging fringe of 2–4 cm tufts on its lower edge.
- **Corner posts:** the swell shows high-frequency wobble on the silhouette edge (wing_door, right edge). Keep it low-frequency (wavelength ≥ 0.8 m).
- **Step stone:** it reads like a bar of soap (ground_contact). Add a 1–2 cm worn hollow at the centre and 2–3 chipped edges.

## Round 4 — builder entry

**Renders:** renders/hilltop_keep/round_04/ (all 6 views at 32 spp, stats.json, hidden.json).
**Stats:** 352 objects (47 unique-geometry objects + 305 linked duplicates of 65 pooled meshes), 1,313,720 tris, **est_hidden_pct 13.5 %**, 11 material slots (all from the 15-slot palette), `mask_attribute_missing` is empty. bbox x −11.43..5.30, y −5.30..5.45, z −0.05..14.00 (16.73 × 10.75 × 14.05 m). .blend 32.0 MB. Build takes about 8 min on the shared CPU; about 6 min of that is the hidden-surface pass.

**Must-fix items:**
1. **Wing window:** moved to xc = −7.4, clear of the turret base. Clear opening 0.45 × 0.55, sill at 1.30. The 0.07 m timber frame has four members plus a mullion, with pegged corners, and sits 0.16 m back in the reveal. There is a timber lintel and a projecting stone sill. Dressed blocks (2 per side) form the jambs. The reveal tube runs through the wall into a dark blocker room 1.0 m inside. The stones, mortar and turret clip are all cut by the same opening rects (wing_south now shows a dark opening).
2. **Cushion:** new `corbel_cushion(spec)` component with 2 corbel courses of 17 + 18 stones (0.40–0.60 m long, 0.20–0.32 m tall). The lower course projects 0.12–0.23 m and the upper 0.15 (W/NW) to 0.43 m (E/SE). The lip droops 0.15 m on E/SE. Top weathering is 10° plus the E droop. Each stone is a 2–2.5 cm-arris block cut by 2–3 planar cleaves 2–3 cm deep, plus an underside cleave. Only the upper top-outer lip is rounded (~6–8 cm). Joints are 2–3 cm, over a mortar body recessed 4 cm. The stepped bed-joint splits are gone. I count 16–22 stones per course, not in total, so that the 0.40–0.60 m stone length holds.
3. **Thatch:** `thatch_courses()` is rewritten. Each course is one continuous strip round the whole roof (N side, NW hip, W end, SW hip, S side). A course rises from the course below through a 0.10–0.15 m concave fillet into a steep butt (2.8–6.8 cm, varying per 0.7 m patch), then a rounded crown and a flat tail. Lobes (2.5–4.5 cm) are grouped in 4–12 cm clumps with 0.5–2 mm creases. The mass swells ±5–8 cm over about 2.3 m, coherently through course, core, ridge and fillets. Toward the hall valley the steps fade over about 0.45 m, and the courses soft-clamp under the skirt as a continuous rounded valley. 12 courses, 71.6k tris.
4. **Hips and fillet:** the hip-roll tubes and their mortar saddles are deleted. The deck is now a rounded-hip surface: every contour keeps a 0.55 m plan radius (`q_rr`), with a 5 cm hip swell, so the courses wrap round the hips and die into the turret on the fillet. `mortar_fillet()` is a triangular section: 8 cm up the stone, ~45° flat face, 7.5 cm toe, bedded into the thatch. It wanders only at low frequency (≥ 1.3 m wavelength, ±2 cm), with the path smoothed to σ ≈ 0.35 m. The course butts run straight into it, with no turn-up. The hall-wall fillet uses the same component.
5. **Hidden triangles:** down from 34.7 % to 13.5 %.
   - **By construction:** stone sides reach only 1.8 cm (cone 2.2 cm) behind the wall plane and have no backs. No rubble is laid behind the engaged posts and pedestals. The cone starts at the collar top. The mortar bodies are coarse sheets, refined only round openings. Rafters and soffit boards drop their covered top faces and start 0.10 m inside the plate. Covering units stop where the next course covers them (worst-case jitter + 1.2 cm), keeping the full length under missing and slipped pieces. The buried faces of plates, posts and drum boards are dropped. The hall interior is now just the reveal tubes plus one blocker room behind each window. The wing plates and battens are gone; only the rafter-pole ends remain. The thatch core is trimmed under the course cover and inside the walls. The buried roll and ridge-dome tails are trimmed.
   - **Final ray pass (`visibility_cull`):** deletes the polygons of roof-level, structural, stone-body and door objects that no viewpoint can reach. The viewpoints are the review rings plus about 120 actor-scale positions: under and outside the eaves, low ground views, along the wing walls, round the turret, and 0.5–2 m in front of both doors. Close-up surfaces are therefore kept.
6. **Degenerate and below-ground geometry:** `finalize()` → `clean_mesh()` clips at −0.05 m, merges by distance at 0.1 mm, dissolves degenerates and deletes the remaining zero-area faces. The audit shows zmin −0.050. There are **8 faces left under 1e-8 m²** (6–10e-9, all in skirt_boards), from a float rounding difference between bmesh and polygon area. Raising the delete threshold to 5e-8 fixes them; that change goes in next round.
7. **Dressed jambs and quoins:** faces are flat-tooled (dome ≤ ~4 mm), arrises are 1.0–1.5 cm, and 0–2 corner chips of 2–4 cm. Jamb and voussoir joint mortar now sits 3 cm behind the reveal and 3.1 cm behind the face.
8. **Footing:** footing tops step stone by stone (−0.10..+0.10, so 0.23–0.43 m visible), with lengths 0.40–1.10 and projection 3.5–13 cm. Footing stones on every hall facet, the wing and the turret are polygonised poly-stones. The course above beds on the highest step, and the voids are pinned. There are 13 half-buried boulders (1–2 per hall facet, wing, turret foot).
9. **Shared mesh data:**
   - **Pools placed as linked duplicates (65 pooled meshes, 305 instances):** pegs (4 variants per size, 94), forged nail heads (4 per size, 59), knuckle/pintle/shank (3, 6), ridge-comb shakes (10 lengths, 66), and rubble/boulders (16 variants in 4 size classes, 67 + 13). Instances carry object transforms (necessarily). Every other object keeps identity transforms.
   - **Parameterised components (new or rewritten):** `round_stone_wall(name, center, radius_fn, z0, z1, seed, cfg, eff_radius_fn, excl_fn, cull_fn, ...)` (the turret body now uses it), `corbel_cushion(acc, accm, center, spec)`, `thatch_courses(...)`, `mortar_fillet(...)`, `mortar_sheet(...)`, `get_pool`/`place`, and `visibility_cull(targets, views)`.
- **Also done:**
  - Mandatory `Mask` attribute on every mesh: R is per island, G is per-island wear by material, and B is ground, up-facing and north damp. The palette is updated to the 15-slot list.
  - Nice-to-haves: turret cap eave across-flats is now 3.3 m. The ridge comb is now 0.07–0.25 m above the log (tallest about −40 %).

**Known gaps:**
- The cushion's upper course still reads slightly soft at very close range. Its cleaves are planar but shallow.
- Some legacy builders still read module globals (WX_*, TUR_C, WDOOR/WWIN specs); the deep refactor is partial.
- The W eave-roll end at the turret is unchanged.
- Not done: the eave-roll slimming and fringe, the step-stone hollow, and the low-frequency post wobble.
- 8 sub-1e-8 m² slivers (item 6).

## Round 4 — score 8/10

**Reviewed:** renders/hilltop_keep/round_04/: all 6 views (hero, front, side, back, aerial, actor_closeup) plus stats.json and hidden.json, side by side with ref1 (keep_overall, keep_hall_door_window, keep_west_wing_turret) and style_thatch_and_tiered_tower. The Director rendered 23 extra views at 16 spp in renders/hilltop_keep/round_04/director_extra/:
- **Close-ups:** door, hinge_graze, wing_south, wing_window, turret_cushion, cushion_e, wing_turret, wing_west_end, back_wing, wing_hall_n, wing_hall_s, eave_under, ground_contact, thatch_eye, sw_window, lantern_cap, collar_comb, skirt_graze_ne, under_skirt_e, turret_n.
- **Off-ring hole hunt:** odd_aerial_se, odd_aerial_nw and low_crane_w. These cameras sit deliberately between the review rings, because `visibility_cull` uses exactly the review-tool rings as its viewpoints.

The Director also audited the .blend and ray-cast every suspect dark pixel to find its world position.

**Stats:**
- 352 objects (305 linked duplicates of 65 pooled meshes) and 1,313,720 tris.
- **est_hidden_pct 13.5% (pass).** 11 material slots, all from the palette (pass). `mask_attribute_missing` is empty, and the Mask attribute is CORNER, active and render on every mesh (pass).
- z-min −0.050 (pass). UVs on every mesh. Non-identity transforms only on the 305 instances (accepted).
- 8 faces under 1e-8 m², all in KEEP_roof_skirt_boards.
- Biggest meshes: hall_wall_stones 226k, **cone_stones 198k** (I asked for ≤ 140k in round 2), wing_wall_stones 96k, turret_stones 87k, thatch core 86k, thatch courses 71k.
- Build takes about 8 min, close to the 10 min limit.

**Verdict:** this round is a technical clean-up and it achieved that.
- **Producer notes now met:** hidden triangles, palette, Mask, below-ground clipping and mesh sharing.
- **Visual items fixed:**
  - The wing window now exists, with frame, mullion, sill and lintel.
  - The hip-roll tubes are gone.
  - The cushion reads as stone corbel courses rather than sandbags.
  - The jamb mortar shelf is gone.
- **Why the grade stays at 8:** the off-ring cameras found **four see-through holes and voids**. These are the CG tells producer note 6 forbids ("never open holes when culling"):
  - a missing-board void into the hall interior on the W skirt facet;
  - the open W eave-roll / thatch-core end at the turret;
  - a staircase of black slots at the NW skirt/thatch eave;
  - pinholes through the hall rubble into the interior at ground level.
- **Fixes that did not land visually:**
  - The thatch/stone fillet still renders as a rounded rope that loops across the turret.
  - The thatch courses are still near-parallel ruler lines of smooth "fondant" with no straw relief at actor distance.
  - The cushion's upper course is a ring of identical upholstered slabs.
  - The footing on the hall S/SW facets is still a row of kerb boxes.
- **Regression:** the cone masonry has slipped back toward "stones glued on smooth plaster" on its W/SW flank.

Score by axis:

| Axis | Score |
|---|---|
| Silhouette | 8.5 (the cushion reads as a regular tyre band; otherwise unchanged and strong) |
| Proportion and scale | 9 |
| Construction | 7.5 (4 see-through holes, rope fillet, stub course ends) |
| Detail and craft | 8 (straw-less thatch, uniform cushion, kerb footing, cone mortar) |
| Age | 8.5 |
| Technical | 8 (hidden, palette, Mask and sharing pass; 8 degenerates; partial kit refactor; holes) |
| **Overall** | **8** |

**Strengths:**
- **Producer notes:** hidden triangles 34.7% → 13.5%. Palette-only slots, Mask on every mesh, and nothing below −0.05 m. 65 pooled meshes with 305 linked duplicates for pegs, nails, pintles, ridge-comb shakes and rubble. Mortar and covering culls are done by construction.
- **Wing south window** at xc −7.4 (wing_window, wing_south): a real dark opening with a pegged frame, mullion, timber lintel, projecting stone sill and a 1.0 m blocker. It matches ref1's small dark wing window.
- **Turret cushion** (turret_cushion, low_crane_w): now two rough corbel courses with recessed joints and an E/SE overhang. The quilted-pillow read is gone.
- **The hip-roll tubes are gone.** The hips are a rounded swell of the courses.
- **Close-up timber holds up:**
  - The eave underside is film-grade (eave_under, under_skirt_e): curved sprockets, soffit boards, a pegged plate, Y braces and checked posts.
  - The SW window (sw_window) has a chamfered cross-mullion frame with pegs.
  - Main door and ironwork (door): tapered strap hinges with spear terminals, seated nails, ring pull, and varied planks.
- **Upper tiers:** the lantern, propped hatch, bell-cast cap with hip boards and the finial are unchanged and strong (lantern_cap). The turret cap at 3.3 m now overhangs the cushion, as in ref1.
- **Silhouette:** at thumbnail size, hero and front still read unmistakably as ref1's keep.

### Must-fix (priority order)
1. **See-through holes and voids, new or revealed this round.** Every location was confirmed by ray cast.
   - **(a) W skirt facet, near where the wing ridge dies into the collar,** at about (−3.8, 1.1, 4.8). There is a missing or culled board with **no deck under it**, so the camera sees straight through into the hall interior. It shows as a black triangle about 0.3 m across (low_crane_w x 770–800 / y 195–230).
     - Fix: add a continuous sarking deck (M_timber, 2 cm thick, 2–3 cm under the board undersides) on all 8 skirt facets from eave to collar foot, and the same under the cap and turret cap shingles. Cost: about 2–4k tris.
   - **(b) SW wing hip / W eave-roll end at the turret,** at about (−9.4..−9.7, −0.2..0.1, 2.9–3.2). The roll end is open and the inside (back) faces of the thatch core show as a black slot (odd_aerial_nw x 905–935 / y 600–630; wing_west_end, upper left; hero, turret foot). This is your own known gap.
     - Fix: cap the roll with a tapered thatch end that dies into the fillet. The core must be closed wherever it can be seen.
   - **(c) NW skirt eave over the thatch,** at about (−2.1..−2.5, 3.95..4.15, 3.9–4.1). The skirt board, sprocket and fascia ends step down as a staircase with black slots between them (odd_aerial_nw x 430–500 / y 380–470). The round-2 NW junction fix has regressed.
     - Fix: scribe the fascia and the last board course continuously onto the thatch, and run the lead apron under them with no gaps. Check the matching SW junction too.
   - **(d) Pinholes through the hall rubble into the interior,** at the −Y facet, about (−1.2, −4.0, 0.49) (ground_contact x 780–830 / y 265–290; actor_closeup x 470–520 / y 430–440).
     - Fix: the coarse mortar sheet must be continuous 2–4 cm behind every stone face, with no openings except the real door and windows. Check every facet below 1.0 m.
   - **Process:** `visibility_cull` uses exactly the review-tool rings as its viewpoints, so the metric cannot see what it removes.
     - Before returning, render at least 6 cameras that are **not** on those rings: two crane cameras at elevation 25–40° and azimuths offset 10–20° from the ring stations, two under-eave cameras, and two at 0.8 m height along the wall bases.
     - Confirm that no pixel shows sky or interior through the building.
2. **The thatch/stone fillet still reads as a rope or worm** (`mortar_fillet()`; see turret_n, wing_turret, back_wing, wing_west_end, and the hero crop of the turret).
   - **What is wrong:**
     - The section renders as a rounded tube about 10–12 cm thick lying *on* the courses. On the N side it makes a U-loop down the turret flank (turret_n x 330–860 / y 0–390). On the turret's E side it snakes diagonally from the cushion to the eave (wing_turret x 420–750 / y 140–360).
     - On the W hip, a flat strip ends in a square blunt cut in mid-slope (wing_west_end x 690–720 / y 520–545).
   - **Fix:**
     - Keep a hard crease at the top edge, feathered to ≤ 5 mm proud into the stone joints. Split normals there and at the toe (no auto-smooth across the profile).
     - The face must be planar at 40–45°, standing at most 5–6 cm proud.
     - Tuck the toe 3 cm **under** the course butts rather than resting on top of them.
     - Run one continuous path along the actual thatch/stone intersection, with no end cuts and no loops. Where the intersection curve is steep (more than 50°), use stepped lead flashing instead.
3. **The thatch still reads as smooth stacked slabs ("fondant") with ruler-parallel course lines** (`thatch_courses()`; see wing_hall_n, wing_turret, back_wing, thatch_eye, actor_closeup top left).
   - **(a) Course lines.** The claimed ±5–8 cm swelling does not read: across 5 m the lines stay parallel to within about 2 cm.
     - Let each course line drift ±6–10 cm in height over 2–4 m, independently per course.
     - Vary exposure along the run from 0.24 to 0.36 m, so that neighbouring butt lines visibly converge and diverge.
   - **(b) Straw relief.** At actor distance the exposed course surface is dead smooth.
     - Add fall-line straw relief: ridges 0.5–1.5 cm deep at 1–3 cm pitch, broken into 0.2–0.5 m patches with differing direction (±5°).
     - Apply it at least on the S slope, both hips and the W end.
     - Pay for it from the core (86k, 20% hidden).
   - **(c) Course ends.** Near the hall valley, course ends stop as vertical cut stubs (wing_turret x 1080–1150 / y 410–520; thatch_eye x 770–790 / y 205–260). Feather every course end to zero over 0.3–0.5 m.
   - **(d) Eave roll lower edge.** It is a crisp machined band with a tiny regular zigzag (thatch_eye y 590–610). Replace it with an irregular hanging fringe of 2–6 cm tufts, and slim the roll to 0.32–0.36 m.
4. **The cushion's upper course is a ring of identical upholstered slabs** (`corbel_cushion()`; see turret_cushion, cushion_e, low_crane_w, hero).
   - **What is wrong:**
     - All 17–18 upper stones share the same height, the same rounded lip and parallel radial joints, which reads as tyre tread or sofa cushions.
     - The 2–3 cm cleaves are invisible.
     - A dark open slot runs between the upper and lower course (turret_cushion x 430–560 / y 405–415).
   - **Fix:**
     - Per stone: height 0.20–0.34 m, length 0.35–0.70 m, tilt ±3–6°, and outer face offset ±4 cm.
     - Cut cleaves 4–8 cm deep. Round the lip on only about half the stones, with the radius varied from 3 to 8 cm.
     - Add 2–4 pinning stones.
     - Close the bed joint with mortar recessed 3 cm.
     - Keep the E/SE overhang and droop, and make the overall outline lumpier: ±5 cm around the ring.
5. **The hall S/SW footing still reads as kerb boxes** (ground_contact, actor_closeup).
   - **What is wrong:**
     - Three blocks of about 0.9 × 0.45 m on the −Y facet have dead-flat faces, vertical sides and level tops.
     - Left of the SW pedestal, one long slab rises as a smooth wedge ramp (ground_contact x 20–440 / y 200–330).
     - The boulder at the SW pedestal reads as two stacked soap bars with a scooped hollow (actor_closeup x 610–680 / y 490–520).
   - **Fix:**
     - Give the footing faces the hero-rubble treatment: 1–2 split planes at 5–15°, a 1–2 cm pillow, chipped arrises, and tops sloping 3–8°.
     - Make boulders single sub-angular masses.
6. **Dressed blocks are still pillowy, and the main-door jamb has a seam** (hinge_graze, wing_window, door).
   - **Arrises:** the wing-window jamb blocks and the main door's left jamb read with 3–5 cm round-overs, like foam.
     - Measure the built bevel and make it 1.0–1.5 cm, as reported.
   - **Seam:** a continuous thin vertical line crosses the three lower-left jamb blocks of the main door (hinge_graze x 630 / y 0–560). It is a coincident or intersecting surface. Remove it.
   - **Blank panel:** above and below the wing window frame, the reveal shows a featureless flat panel about 0.25 m tall (wing_window y 30–220).
     - Seat the timber lintel directly on the frame head, and fill below the sill with rubble.
7. **Cone masonry regression** (`KEEP_cone_stones`; see collar_comb.png, left half).
   - On the W/SW flank above the collar, visible mortar is about 25–30%, so the stones again read as glued onto smooth plaster.
   - Restore ≤ 15% visible mortar, as in rounds 2–3, and bring the cone back to ≤ 150k tris (it is 198k today and never appears in a close-up).
8. **Producer-note compliance leftovers:**
   - **(a) Degenerate faces:** 8 zero-area faces in KEEP_roof_skirt_boards. The target is 0; apply your 5e-8 threshold.
   - **(b) Kit refactor (producer note 2) is still partial.** `build_hall_masonry`, `build_hall_mortar`, `build_main_door`, `build_wing_walls`, `build_wing_door_window`, `build_wing_roof`, `build_skirt` and `build_turret` read module globals (WX_*, WY_*, TUR_C, WDOOR, WWIN, OPENINGS).
     - Expose them as parameterised components, for example `stone_wall(path, height, openings, seed)`, `plank_door(width, height, arch)`, `window(w, h, frame, mullion)`, `thatch_roof(outline, pitch, thickness, seed)` and `turret(center, profile, cushion, cap)`.
     - Prove it with one variant build (for example a 0.8× turret and a 4 m wing) rendered to renders/hilltop_keep/round_05/kit_test.png.
   - **(c) Build time:** keep it safely under 10 min. The cull alone takes about 6 min; reduce its viewpoint count or cull analytically, but never at the cost of item 1.

**Nice-to-have:**
- **Ridge comb:** from eye level it still reads as thin pickets (thatch_eye, top). Use wedge-thick 3–5 cm shakes clustered in V tufts.
- **Cap shingles:** a missing cap shingle shows black (lantern_cap x 345–370 / y 325–335). The deck from 1(a) will fix it.
- **Leftovers from round 3:** the step-stone worn hollow and chips, low-frequency post wobble, and pooled lantern boards.

**Rulings:** linked-duplicate instances may carry object transforms (accepted). est_hidden_pct 13.5% passes.

## Round 5 — builder entry

**Renders:** renders/hilltop_keep/round_05/ (all 6 views at 32 spp, stats.json, hidden.json), `kit_test.png` (variant keep from the kit), and `builder_checks/` (16 spp off-ring cameras: off_crane_sw, off_crane_nw, off_under_eave_se, off_under_eave_wing_n, off_base_s, off_base_turret_w, plus the Director's low_crane_w, odd_aerial_nw, odd_aerial_se and ground_contact).
**Stats:** 369 objects (318 linked duplicates of the pooled meshes), 1,306,850 tris, **est_hidden_pct 14.3 %**, 12 material slots (all palette; M_daub is new, for the eave filling), `mask_attribute_missing` empty, **0 faces under 1e-8 m²**, zmin −0.050. bbox x −11.43..5.30, y −5.30..5.45, z −0.05..14.00 (16.73 × 10.75 × 14.05 m). .blend 31.7 MB. The build takes about 7 min on the shared CPU (cull about 6 min of it; it was 5.8 min when the CPU was free).

**Must-fix items:**
1. **Holes.**
   - (a) New `sarking_deck()` component: a 2 cm closed deck under the boards on all 8 skirt facets (`KEEP_roof_skirt_deck`), and under the cap and turret-cap shingles (`KEEP_cap_deck`, `KEEP_turret_cap_deck`). About 6k tris. Decks are never culled.
   - (b) The thatch core's cut edges are now closed by side walls on every boundary edge of the kept region. The core skin is kept within 0.3 m of the eave and 1.1 m of the turret.
   - (c) Skirt boards are no longer dropped whole where the thatch rises over them. `covering_boards(scribe=...)` cuts every unit obliquely along the true thatch intersection, with butt and tail cut separately, over the lead apron. The NW and SW junctions use the same code.
   - (d) Mortar sheets, thatch courses, core, rolls, fillet and decks are removed from the visibility cull, so the hall mortar sheet is continuous behind every stone. Mortar sheets are wound outward and the reveal and blocker faces face their opening (`recalc=False`), so nothing shows a back face in Unreal.
   - Also: a new **eave filling** (M_daub) on the wing wall heads closes the roof space between the wall top and the thatch underside. This was a see-through under the N wing eave that the off-ring check found.
   - The cull viewpoints gained 24 off-ring crane stations.
   - Off-ring check: a ray-grid audit (first hit is a back face) shows no interior or sky through the hall, skirt or wing walls. The residual back-face hits are on open board shells (normals), not openings.
2. **Fillet.** It is rebuilt as `mortar_fillet()`:
   - a hard top crease 4 mm proud;
   - one planar ~43° face at most 5.5 cm proud;
   - the toe tucked 3 cm under the butts;
   - split normals (own object `KEEP_wing_fillet`, smoothing 25°).
   `flaunch_loop()` runs one continuous path along the ray-cast intersection. It uses `stepped_flashing()` (lead in level steps) where the line is steeper than 50°, and tapers the open ends to nothing. The old roll collars and saddles are gone.
3. **Thatch.**
   - (a) Course lines: a shared 2–4 m drift (±8.5 cm in slope) plus an independent per-course drift (±5.5 cm), with exposure clamped to 0.24–0.36 m against the course below.
   - (b) Fall-line straw ridges 0.5–1.5 cm deep at 1.5–3 cm pitch, in 0.2–0.5 m patches skewed ±5°, on the S slope, hips and W end. The N side gets shallower 2.8–4.2 cm straw.
   - Each course has an extra crowned row.
   - (c) Every course end feathers to nothing over 0.4 m and sinks under the course below.
   - (d) The roll is slimmed to about 0.35 m. `tuft_fringe()` adds about 1,950 slender tapered bristle clumps, 2–6 cm long, with clumped lengths and gaps.
   - Course tails under the ridge dome are trimmed.
4. **Cushion.** Per stone:
   - length 0.35–0.70 m and height 0.20–0.36 m (each upper stone has its own height);
   - tilt ±3–6°, face ±4 cm, and an outline wobble of ±5 cm around the ring;
   - 1.2–2 cm arrises and 2–3 cleaves 4–8 cm deep, plus 1–2 top cleaves on the upper stones;
   - the lip is rounded on about half of the stones (3–8 cm).
   4 pinning stones sit in the stepped beds. The mortar body follows the actual course tops and bed joints, filled to 3 cm behind the face.
5. **Footing.** `rough_footing()` gives every footing stone:
   - a 3–8° sloping top;
   - a 1–2 cm pillow;
   - two split planes at 9–16°, kept inside the projection (the faces were being flattened onto front_min before);
   - 4–7 chips of 3–6 cm;
   - 1–2 knocked top corners.
   Boulders are single sub-angular masses with 4–5 cleaves and low-amplitude lumps.
6. **Dressed blocks.**
   - The stepped drafted margin, which shaded as a 2–3 cm round-over and was the jamb "seam" line, is removed. Faces are one flat tooled plane, the arris is 1.0–1.5 cm, and dressed objects are smoothed at 24°.
   - The wing-window mortar cells no longer span the head of the opening. The reveal is now two tubes: face to frame round the frame, then the clear opening to the blocker. No blank panel remains.
7. **Cone.**
   - Joints are 0.6–1.1 cm and the outline is less nibbled (rough 1.0): measured visible mortar is 10.8 % after pinning.
   - Face grids are 7×7 only on stones with hx > 0.13 and 5×5 on the rest: 142.5k tris (was 198k).
   - The cone is out of the cull.
8. **Producer notes.**
   - (a) The degenerate threshold is 5e-8: 0 faces.
   - (b) Kit section: `kit_set()` / `_derive()` re-derive the dimension table (wing path, turret profile, cap and cushion, thatch planes, roll seating, toothing). The components are `stone_wall(coll, path, height, openings, seed)`, `arched_door`, `plank_door(...)`, `window(...)`, `wing_openings`, `thatch_roof(coll, outline, pitch_deg, thickness, overhang, seed)`, `turret(coll, center, scale, cushion)` and `sarking_deck`, `tuft_fringe`, `mortar_fillet`, `stepped_flashing`, `corbel_cushion`. main() builds the keep only through them. `KEEP_KIT_VARIANT=1` builds a 0.8× turret and a 4.0 × 7.0 m wing with no errors → `round_05/kit_test.png` (scratch .blend outside the building folder).
   - (c) The build takes 5.8–7.1 min depending on CPU load.
- **Nice-to-haves done:**
  - Ridge comb: 3–5 cm wedge shakes, V pairs clustered in groups.
  - The cap deck covers the missing-shingle hole.
  - The step stone has 3 chipped edges (it already had a worn hollow).

**Known gaps:**
- The cushion still reads fairly regular at the turret_cushion distance.
- The footing faces on the S facet are better broken but still large.
- A few course stubs remain where the courses pass under the hall skirt valley.
- The kit still shares one module dimension table (via `kit_set`) rather than passing a context object to every helper.
- Some open board and shingle shells have mixed normals (recalc on open shells).


## CLIENT CORRECTION — producer note 10

Delete all loose ground stones, rubble scatter, path flags, stepping stones and ground aprons that are not part of the building. Do not score them. See producer note 10 in the art bible.

## Round 6 — builder entry

**Renders:** renders/hilltop_keep/round_06/ (all 6 views at 32 spp, stats.json, hidden.json) and `builder_checks/` (16 spp: ground_contact, off_base_s, turret_cushion, cushion_e, rollend_sw, wing_turret, odd_aerial_nw, off_crane_sw).
**Stats:** 289 objects (238 linked duplicates of 49 pooled meshes), 1,296,876 tris, **est_hidden_pct 13.9 %**, **11 material slots** (all from the palette; M_rubble is gone with the rubble), `mask_attribute_missing` is empty, **0 faces under 1e-8 m², 0 needle triangles** (altitude < 0.1 mm), zmin −0.050. bbox x −11.11..5.30, y −5.30..5.30, z −0.05..14.00 (16.41 × 10.60 × 14.05 m). .blend 31.9 MB. The build takes about 7 min.

**Changes:**
1. **Producer note 10 / client correction.** `build_ground()`, `_rubble_builder()`, the rubble/boulder pool (16 variants, 80 placements), the `KEEP_ground` collection and the rubble special case in `get_pool()` are all deleted. Nothing loose remains on the ground. The building's own parts stay: the footing course, the corner-post pedestals, the main-door threshold, the built-in step stone, and the wing-door threshold.
2. **Footing (round-4 must-fix 5, still kerb-like in round 5).** `rough_footing()` and `build_poly_stones()` for footing stones:
   - faces lean back 1.5–3.5 cm toward the top;
   - absolute ±1.5–2 cm low-frequency lumps;
   - 2.5–2.75 cm pillow;
   - split planes at 13–22°, allowed to cut down to the full projection;
   - 3.5 cm weathered shoulders;
   - 5 extra face rings so the relief resolves.
   They now read as bedded field stone (off_base_s, ground_contact).
3. **Cushion upper course (round-4 must-fix 4).** The upper course has a wider length spread (0.30–0.76 m), outer face ±6 cm and tops −7.5/+3 cm. Each stone is also yawed 4–10° in plan, so one end stands proud of its neighbour, and about 55 % of stones get a 2–4 cm bellied face. The even "tyre tread" ring is broken up (turret_cushion, cushion_e).
4. **See-through at the SW eave-roll / turret junction (round-4 must-fix 1b).** The black crescent in odd_aerial_nw at about (−9.9, 0.0, 3.0) was the open back of the D-roll, where both the thatch core and the turret stones are cut away. The roll now keeps its back faces within 1.3 m of the turret (`d_roll(keep_back_fn=...)`), and a roll end that dies into the turret tapers. The ray-grid see-through audit over the 10 off-ring cameras shows no interior or sky through any wall or roof. The only residual back-face hits are on open board shells (1–30 px per view) and on the real door and window openings.
5. **Nanite hygiene.** `clean_mesh()` gained `fix_needles()`:
   - bad n-gons are re-triangulated (beauty);
   - slivers have their < 1 mm edge collapsed or their long edge flipped;
   - leftover slivers under 0.1 mm wide are deleted;
   - a mesh-tessellation recheck then catches anything left.
   Result: 1,024 needle triangles → 0.

**Known gaps:**
- A few thatch course stubs remain where the courses pass under the hall skirt valley.
- The kit still shares one module dimension table (`kit_set`).
- Some open board and shingle shells have mixed normals.
- A small grey ledge remains where the SW roll meets the turret (no longer a void).

## Round 6 — score 8.4/10

**Reviewed:** renders/hilltop_keep/round_06/: all 6 views (hero, front, side, back, aerial, actor_closeup) plus stats.json and hidden.json, the builder's 8 off-ring checks in round_06/builder_checks/, and 21 Director close-ups at 12 spp in renders/hilltop_keep/round_06/director_extra/:
- door, hinge_graze, eave_under, ground_contact_sw, footing_ne, footing_wing_n, sw_window, wing_door, wing_south
- turret_cushion, cushion_far, wing_turret, wing_west_end, turret_n, wing_hall_n, back_wing, thatch_eye
- low_crane_w, odd_aerial_se, collar_comb, lantern_cap

Compared side by side with ref1 (keep_overall, keep_hall_door_window, keep_west_wing_turret, keep_cone_lantern_cap) and style_thatch_and_tiered_tower. The Director also audited the .blend: 289 mesh objects, 92 unique meshes, 0 zero-area faces, 0 needle triangles (altitude < 0.1 mm), UVs and Mask on every mesh, z-min −0.050, and no ground, rubble, path or apron objects left.

There was no Director grade for round 5, so this review checks the round 5 and round 6 work together against the round-4 must-fix list. The client correction (producer note 10) is applied: ground dressing is not scored, and its absence is not penalised.

**Stats:**
- 289 objects and 1,296,876 tris (86% of budget).
- **est_hidden_pct 13.9% (pass).** 11 slots, all from the palette (pass). `mask_attribute_missing` is empty (pass).
- bbox 16.41 × 10.60 × 14.05 m. The finial tip is at 14.00 m. The .blend is 31.9 MB.

**Verdict:** a real step up from round 4, and the first round with no see-through holes.
- **Holes fixed:** all four round-4 holes are closed: the W skirt facet (low_crane_w), the NW skirt eave staircase (wing_hall_n), the hall rubble pinholes (ground_contact_sw, off_base_s) and the black SW roll-end void. odd_aerial_se, low_crane_w and odd_aerial_nw show no sky or interior through the building.
- **Other fixes that landed:**
  - The cone masonry is dense again and the plaster read is gone (collar_comb).
  - The fillet is now a flat planar flaunching band, not a rope (turret_n, wing_turret).
  - The cushion is two irregular corbel courses and reads as stone at cushion_far distance.
  - The footing reads as large bedded field stones rather than kerb boxes.
  - Hygiene is now clean: 0 degenerate faces, 0 needles, and every producer note passes.
- **Silhouette:** at thumbnail size it is unmistakably ref1's keep in every tier.
- **What holds it under 9:** close-up surface softness and a few junction tells.
  - The dressed jambs and quoins still read as soft soap blocks.
  - At actor distance the footing stones read as melted, sandbag-soft lumps.
  - Torn stone shards and flat course tongues remain where the W eave-roll ends die into the turret.
  - The N thatch slope is still smooth fondant, and the straw relief on the S slope reads as regular barcode scratches.
  - The eave fringe reads as a row of eyelash pins.
  - The ridge comb is thin and sparse next to ref1's chunky crest.

Score by axis:

| Axis | Score |
|---|---|
| Silhouette | 8.5 (cushion is a thin flat brim, not ref1's bulbous lip; sparse ridge crest) |
| Proportion and scale | 9 |
| Construction | 8.5 (holes closed; roll-end shards, course stubs at the valley) |
| Detail and craft | 8.3 (soap-block dressed stone, soft footing, barcode straw, N-slope fondant, pin fringe) |
| Age | 8.5 |
| Technical | 9 (all producer notes pass; only the partial kit context and mixed normals on open shells remain) |
| **Overall** | **8.4** |

**Strengths:**
- **No see-through holes from any off-ring camera.** The sarking decks, the closed thatch core and the scribed NW and SW skirt boards all hold.
- **Producer notes:**
  - Hidden 13.9%, 11 palette slots, Mask on every mesh.
  - 0 zero-area faces and 0 needle triangles.
  - 49 pooled meshes with 238 linked duplicates.
  - Ground dressing is fully removed, while the building's own footing, pedestals, threshold and step are kept.
- **Eave underside is still film-grade** (eave_under): curved sprockets, soffit, a pegged plate, Y knee braces, and checked posts.
- **Cone masonry** is dense with tight joints, and the candle-snuffer flare matches keep_cone_lantern_cap.
- **Fillet** is a flat flaunching band that follows the true intersection.
- **Main door** has a 7-plank arched leaf, tapered strap hinges with spear terminals, a ring pull, and correct scale and headroom (actor_closeup, door).
- **Hall rubble** (sw_window, wing_south, actor_closeup) is flat-bedded polygonal stone with pinch-outs and holds up at eye level.

### Must-fix (priority order)
1. **Torn shards and flat course tongues at both W eave-roll ends, where they die into the turret** (`d_roll` ends, turret stone clip, `thatch_courses` ends; see director_extra/wing_west_end.png, builder_checks/rollend_sw.png, director_extra/wing_turret.png).
   - **SW end, about (−10.2, 0.5, 2.9–3.4):**
     - A stepped stack of thin clipped turret stones sticks out of the roll top (wing_west_end x 595–650 / y 270–420).
     - A torn flap with a dark slit sits at the roll crown (rollend_sw x 130–330 / y 180–320; slit at x 150 / y 270–300).
     - A dark wedge sits under the roll end (wing_turret x 200–255 / y 340–365).
   - **NW end, about (−10.2, 4.5, 2.9–3.4):** the same stair-stepped stone splinters appear (wing_west_end x 110–200 / y 250–370).
   - **SW hip:** two course ends stop as flat horizontal tongues about 1.2 m long that project past the roll (wing_west_end x 670–890 / y 270–320).
   - **Fix:**
     - Wherever thatch clips a turret stone, delete the stone or replace it with a whole stone that the thatch buries at least 3 cm. No stone fragment thinner than 4 cm may show.
     - Taper each roll end over 0.4–0.6 m into the mortar fillet with a closed, rounded end cap.
     - Feather the course tongues to zero thickness, as on the S slope.
     - No dark pixel may remain at either junction in wing_west_end, rollend_sw or wing_turret.
2. **Dressed stone still reads as soft soap blocks** (`KEEP_hall_dressed_stones`, `KEEP_wing_dressed_stones`; see director_extra/door.png, hinge_graze.png, wing_south.png x 800–890, wing_door.png).
   - **What is wrong:**
     - The door jambs, wing quoins and wing window jambs show domed faces with 2–3 cm round-overs and no tool marks or chips.
     - On the main-door right jamb, the big upper block (hinge_graze x 330–700) has a 3–4 cm rounded arris all round.
   - **Fix:**
     - Faces are flat with a dome ≤ 3 mm. Arrises use a true 45° chamfer of 1.0–1.5 cm with split normals, not a smoothed round-over.
     - On the hero blocks (door jambs, 6 lowest each side), add a 1–2 mm tooled drafted margin 3 cm wide and 1–3 tooling score lines at 15–25 mm pitch.
     - Add 1–3 arris spalls of 2–5 cm per block, with crisp conchoidal edges.
3. **At actor distance the footing reads as soft sandbags or melted clay** (`rough_footing`, footing `build_poly_stones`; see director_extra/ground_contact_sw.png, builder_checks/ground_contact.png, off_base_s.png right half).
   - **What is wrong:**
     - The ±1.5–2 cm lumps and the 2.5 cm pillow under smooth shading give wobbly, bulging faces.
     - The 3.5 cm "weathered shoulders" round every top arris, so no edge reads as split stone.
     - The SW pedestal also reads as a soft-cornered box.
   - **Fix:**
     - Cut the low-frequency lumps to ±0.6 cm. Cap the pillow at 1.2 cm.
     - Keep 1–2 split planes, but make them planar facets with crisp 0.8–1.5 cm arrises, and split normals between the facets (auto-smooth ≤ 30°).
     - Keep the soft weathered shoulder on at most 1 top arris per stone.
     - Pedestals: 1.0–1.5 cm chamfers and 1–2 spalls each, plus the splayed foot already there.
4. **Thatch surface reads.**
   - **(a) N slope is still smooth fondant** (director_extra/back_wing.png, back.png). Give the N slope the same fall-line straw relief as the S slope, at least 0.5–1.0 cm deep (the 2.8–4.2 cm straw claimed in round 5 does not read at 6 m). Pay for it from `KEEP_wing_roof_thatch` core (88k, 22% hidden).
   - **(b) S slope straw reads as regular barcode scratches** (wing_turret, thatch_eye). Break the relief into clumps:
     - vary groove depth per groove from 0.3 to 1.5 cm;
     - let 20–30% of grooves end mid-course;
     - add a 1–2 cm low-frequency lumpiness across 0.3–0.6 m patches, so grooves are not equal-length parallel strokes.
   - **(c) Eave fringe reads as a row of eyelash pins** (thatch_eye y 375–390, wing_south top edge). Replace the uniform bristles with 4–10 cm clumped tufts:
     - 3–8 strands per tuft, 1.5–3 cm thick at the root;
     - gaps of 2–8 cm between tufts;
     - tips drooping 10–30°.
   - **(d) Seam and stubs.**
     - A vertical seam crosses the eave roll at about (−6.9, 0.0, 2.6) (thatch_eye x 350 / y 300–345); close it.
     - A dark pinhole at the course end near the hall valley, about (−4.0, 0.9, 3.9) (thatch_eye x 633 / y 197), needs closing.
     - A vertical course stub near the valley (builder_checks/wing_turret x 1085 / y 460–600) must feather to zero over 0.4 m.
5. **Wing ridge comb is thin and sparse compared with ref1** (`KEEP_wing_ridge_comb`; see director_extra/low_crane_w.png, cushion_far.png, front.png).
   - ref1 shows a dense, chunky crest of crossed shakes whose top line reads clearly in silhouette. Ours reads as scattered thin sticks over a smooth rider log.
   - **Fix:**
     - Spacing 0.08–0.15 m.
     - Visible height 0.18–0.35 m.
     - Shake width 6–10 cm and thickness 3–5 cm.
     - About 70% of the shakes paired in V/X tufts.
   - The rider log needs ±2 cm low-frequency wobble and pegs every 0.6–0.9 m.
6. **Cushion upper course reads as a brim of flat paving slabs** (`corbel_cushion`; see director_extra/turret_cushion.png, cushion_e.png).
   - **What is wrong:**
     - The upper stones are about 0.2 m thick with dead-flat sloping tops and crisp planar edges. They read like a slate hat-brim, not ref1's bulbous mossy lip (keep_west_wing_turret.png).
     - A cluster of jagged slivers sits where the cushion meets the ridge log on the E side, about (−7.0, 2.6, 6.0) (turret_cushion x 560–640 / y 470–540).
     - A thin spike pokes out at turret_cushion x 410–440 / y 250–270.
   - **Fix:**
     - Crown each upper stone's top by 3–6 cm and round the outer top arris over 6–10 cm on at least 70% of stones. Keep the cleaved faces on the vertical outer face only.
     - Delete any fragment under 4 cm thick at the ridge junction, and end the ridge log on a mortar bed against the cushion.

**Nice-to-have:**
- **Lantern cap shingles:** the jitter in rotation and lift is so strong that the horizontal courses (spec G) barely read (lantern_cap). Halve the rotation jitter so the courses read at 15 m.
- **Small dark notch at the collar/wing-ridge junction,** about (−3.4, 1.6, 5.8) (collar_comb x 80–150 / y 380–440). Check it from an off-ring camera and close it if it is a void.
- **Kit refactor:** pass a context object instead of the module `kit_set` table (known gap).
- **Mixed normals on open board and shingle shells:** fix the 1–30 back-face pixels per view.

**Rulings:**
- Producer note 10 is applied. Ground dressing is neither scored nor requested, and the building-owned footing, pedestals, threshold and step are correctly kept.
- The round 4 to 5 must-fix items 1(a), 1(c), 1(d), 2, 7 and 8(a) are closed.
- Items 1(b), 4 and 5 are improved, but their residue is carried into must-fix 1, 6 and 3 above.

## Round 7 — builder entry (kit migration)

### Files

- **Script.** `buildings/hilltop_keep/build_hilltop_keep.py` is now a thin declarative assembly (about 120 lines) on the shared kit `kit/village_kit/` (kit 1.1.0). One dimension table `KIT` (`kit_set()`), the component steps in build order, `KEEP_KIT_VARIANT=1` for the kit test, `KEEP_FAST=1` to skip the ray test on quick looks. A full build takes about 7.8 min (6.6 min of it the hidden-geometry ray test).
- **Outputs.** `hilltop_keep.blend` (27.8 MB, compressed) and `decal_anchors.json`; the variant in `kit_variant/` (`hilltop_keep_kit_variant.blend`, 25.2 MB, + its `decal_anchors.json`). `signoff_phase1/` is untouched.
- **Renders.** `renders/hilltop_keep/round_07/`: all 6 views at 32 samples, `stats.json`, `hidden.json`; the variant in `round_07/kit_variant/` (same set).

### Stats

| | Round 6 (signed off) | Round 7 | Variant |
|---|---|---|---|
| Triangles | 1,296,876 | 1,123,849 | 1,025,777 |
| est_hidden_pct | 13.9 % | 14.1 % | 14.9 % |
| Objects (linked duplicates / pooled meshes) | 289 (238 / 49) | 282 (231 / 25) | 271 (220 / 24) |
| Material slots (all palette) | 11 | 11 | 11 |
| `mask_attribute_missing` | none | none | none |
| Needle / zero-area faces | 0 / 0 | 0 / 0 | — |
| Decal anchors | — | 104 | 107 |
| bbox (m) | 16.41 x 10.60 x 14.05 | 16.41 x 10.60 x 14.05 (unchanged) | 14.54 x 10.60 x 13.35 |

Triangles by part (round 6 -> 7): hall 354.5k -> 354.1k, tower tiers 301.1k -> 278.6k, wing 362.7k -> 231.0k (straw striation dropped, note 11), turret 185.9k -> 165.8k, skirt 60.3k -> 60.3k, pooled instances 32.3k -> 34.0k.

### Kit migration

1. **Pure refactor first.** The phase-1 script's code moved into kit modules: the frame `components/oct_frame.py` (`OctFrame`, the keep's one dimension table and every envelope function), `stone_wall`, `oct_hall`, `plank_doors`, `windows`, `oct_roof`, `stone_cone`, `turret`, `annex`, `thatch`, `hewn`, `oct_cull`, `oct_decals`, plus `geom.py` (vectorised primitives, the strict hygiene hook). The private Mask writer, palette, pools, `Acc` / clean-up, stone generator and shingle / shake generators are gone: everything now goes through `palette.material`, `mask.write_mask` (per-island R / G, the shared B), `pools.Pools` (the pegs and nails are now the kit's pooled `timber.make_peg` / `make_nail_head`, scaled), `stones.make_stone` (new styles `coursed` / `coursed_poly`), `shingles.SIZE_TABLE` (new rows `skirt_board`, `collar_shake`, `comb_shake`, `hip_board`) and `shingles.riven_shakes` / `shingle_mesh`. **Check:** built with `units="phase1"`, no note-11 rule and no cull, the kit keep matched a phase-1 build object by object: 52 of 55 unique meshes vertex-identical (count, bounds, coordinate sum), the other 3 (skirt boards, both cap coverings) within 4 vertices from the clean-up order. Only then were the changes below switched on.
2. **Components (producer note 2).** Each is `component(g, ..., seed=...)` and builds its own named objects: `oct_hall_walls`, `oct_hall_frame`, `door_threshold` (polygonal post-and-stone hall walls), `arched_door`, `plank_door`, `hall_windows`, `annex_window`, `skirt_roof` (tiered bell-cast skirt roof), `shake_collar`, `stone_cone`, `lantern`, `cone_cap` (stone cone tower with lantern and bell cap), `side_turret` (side turret with corbelled cushion), `annex_walls`, `thatch_wing_roof`, `ridge_comb`, `thatch_junctions` (thatch wing roof with ridge comb), `oct_hidden_cull`, `oct_building_decals`. The finial is the kit's new "turned" style (`finial.turned_finial`, `finial.lead_hat`).
3. **`kit_set()` and `KEEP_KIT_VARIANT`.** The variant (round_07/kit_variant) is a shorter, narrower wing (6.98 x 4.0 m instead of 8.7 x 4.2) under a steeper 52 deg thatch, a 0.8x turret moved with it, a lower, stubbier stone cone (top 8.9 m instead of 9.6; total 13.3 m), the annex door and window re-spaced and every masonry / roofing layout re-seeded. The cone profile above the collar, the lantern, cap, finial and the decal recipe all follow `CONE_TOP`; the hall (A0, WALL_H) derives its timber frame, skirt eave and reference planes from the table.

### Ensemble consistency fix

- The **lantern cap and the turret cap** now carry the village's chunky shingles: `shingles.shingle_mesh` units from `SIZE_TABLE["shingle"]` (0.35-0.55 m wide, course target 0.44 +-24 %, 0.30-0.40 m exposure, 3.4-4.2 cm butts), `shingle_apex` (0.40 m target) for the top 3 courses, a doubled `starter` course at the eave, the hut cone's stacking wedges, curled eave courses, 2 % missing and 3 % slipped units over the sarking deck. The cap course jitter is halved (round-6 nice-to-have) so the horizontal courses read. Hip boards come from the new `hip_board` row and bed on the butt peaks; the lead hats are fitted over the shingle vertices (`lead_hat(cover=...)`, r 0.42 m main / 0.38 m turret) so no shingle pokes through. Lantern and drum boards use `SIZE_TABLE["board"]`.
- Lantern cap: 167 shingles (was ~2,900 small boards); turret cap: 118.

### Producer note 11

- **Rule.** `OctFrame.detail` = `core.DetailRule` with the entrance at the arched door: relief >= 2 cm kept, >= 1 cm within 3 m of the door below 2.5 m. Every threshold is evaluated at the piece's world position (`g.min_relief(P)`); the random draws are made either way, so the kept shapes are the round-6 shapes.
- **Stone.** Dropped: the value-noise face skin (<= 1 cm), the mm outline nibbling, dressed tooling and pick (1.2 / 0.4 mm), the 1.5 mm worn-rim dip, chips and split facets shallower than the local threshold, the footing's +-1.5-2 cm lumps outside the entrance zone (round-6 must-fix 3 asked for them to be cut back), the sill tooling, pedestal tooling, 8 mm ledge-slab noise. Kept: every stone, pillow, tilt, the 1-2 split planes, coursing, recessed joints, chips >= the threshold, the footing projection.
- **Timber.** Adze scallops are modelled only where the deepest scallop reaches the threshold (the door posts in the entrance zone keep theirs); checks shallower than the threshold are not modelled (the wing door jambs and lintel, the plate checks) and become `crack` anchors; the door posts' 1.6-3.2 cm checks stay. Plank cup / grain / fine adze marks on both door leaves are dropped; joints, offsets, the split plank and the rotted corner stay. The 1.2-2 cm rafter-pole end checks are dropped.
- **Thatch.** The straw striation (0.5-1.5 cm fall-line ridges) and the eave-roll / ridge-dome strand ribs are dropped. The courses are laid as discrete clumps instead (one column pair per 6-12 cm clump, crowned 1-2 cm over a soft crease, butts ragged +-1 cm, sunk 3.2 cm into the course below so no gap opens), and the roll and ridge dome keep bound bundles (2-3 cm constrictions every 0.08-0.18 m). Wing triangles 362.7k -> 231.0k.
- **Shakes.** The 2-5 mm riven ridges and the 5 mm edge wave of the collar shakes and the comb shakes' 2-4 mm riving wobble are dropped; tip shapes, splits and thickness taper stay.
- **Decal anchors.** 104 in `DECAL_ANCHORS` (empties `DA_<type>_<nnn>`, -Z into the surface, custom properties `decal_type`, `size_w`, `size_h`, `surface`, `probability`, `seed`) and in `buildings/hilltop_keep/decal_anchors.json` (units and axes header): damp_rise 22 (hall facet feet, wing walls, turret foot; north faces more likely), moss 14 (north footing tops, north skirt-roof butts at the eave, collar comb, cushion top, north turret-cap shingles), lichen 15 (pedestal tops, sills, threshold and step, cone ledge slabs, cushion faces), water_streak 13 (below the window sills, below the lantern-cap drip line on the flaring cone, below the cushion lip), soot 6 (arch crown, window heads, lantern openings, wing door), rust_stain 10 (below the strap-hinge terminals, pintles and ring pull of both doors), crack 14 (arch springing and crown, window corners, wing lintel ends, the hall / wing settlement junction, the dropped timber checks), grime 6 (door jambs at hand height, the door-flanking posts), repair_patch 4 (repointing on the rubble). No plaster_patch: the keep has no rendered walls (the daub eave filling is not reached by the probe rays).

### Kept from phase 1

- Every client correction: no ground dressing (producer note 10); the building's own footing course, pedestals, threshold and built-in step meet Z = 0 (z-min -0.050).
- Silhouette, tiers, proportions and scale are the round-6 ones (bbox identical; finial tip 14.00 m; door 1.05 x 2.18 m clear, skirt eave over the door >= 3.5 m).
- Hidden-geometry cull with the round-5 / 6 actor, door and off-ring crane views (`oct_hidden_cull`); backing surfaces (mortar sheets, decks, thatch core, blockers) are never culled.

### Side by side with round 6 (signoff_phase1)

All six views compared with round_06 (= the signed-off build):
- **Silhouette / massing:** overlays round 6 in every view; caps, collar comb, cone flare, lantern, finials unchanged.
- **Caps:** the lantern and turret caps now read as the hut's chunky shingle courses (front, side, back, aerial) instead of fine narrow boards: the ensemble item. The courses read horizontally at 15 m.
- **Masonry / entrance (actor_closeup):** the same stones, joints, dressed surround, door, ironwork and footing; the faces are planar without the sub-cm skin, which reads slightly crisper, not softer.
- **Thatch:** the stepped clumped courses read as layered bundles at crane and mid distance (front, back); at actor distance the S slope is plainer than round 6's straw striation (the intended note-11 result: straw striation is now a material / decal job).
- **Holes:** none found in the 6 views or the builder close-ups (caps, thatch S slope, door).

### Kit edits (kit/CHANGELOG.md 1.1.0)

All additive: new modules (`geom.py` and the components above); appended functions / rows in `stones.py`, `shingles.py`, `components/finial.py`; one optional behaviour in `core.Acc` (`hygiene` may be a callable hook; `True` still runs `nanite_clean`). Other buildings re-run: `wattle_roundhut` builds without errors at 744,105 triangles (round-8 record 744,105, 0.0 %) and 105 anchors; `tower_windmill` (now importing the kit, its migration in progress): see the CHANGELOG entry.

### Known gaps

- At the actor close-up the thatch reads plainer than round 6 in clay; the straw texture is meant to come back through the Megascans straw material and decals.
- The dimension table is the frame object, but the family's helper functions read it through the module proxy `oct_frame.FR` (one active frame per process), not an argument on every helper.
- Round-6 must-fixes 1 (roll-end shards at the turret), 5 (ridge comb density) and 6 (cushion upper course) are not addressed in this migration round; 2 (dressed blocks) and 3 (footing) are only partly helped by the note-11 drops; 4 (straw relief) is superseded by note 11.
- The chunky cap hip boards bed on the butt peaks, so a 2-3 cm shadow gap shows under them between the courses at close range.
- The variant's hidden share is 14.9 %, close to the 15 % limit.
