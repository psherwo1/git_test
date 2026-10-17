# SPEC: hilltop_keep (prefix `KEEP`, collection `KEEP`)

**Files:**
- Build script: `buildings/hilltop_keep/build_hilltop_keep.py`
- Output: `buildings/hilltop_keep/hilltop_keep.blend`
- Renders: `renders/hilltop_keep/round_NN/`
- Log: `director/log_hilltop_keep.md`

**References:**
- Main: ref1 (the keep on the hill, left/centre).
- Crops:
  - `director/ref_crops/keep_overall.png`
  - `keep_hall_door_window.png`
  - `keep_west_wing_turret.png`
  - `keep_cone_lantern_cap.png`
- Style cousins: `style_tiered_hall.png` and `style_thatch_and_tiered_tower.png` (ref2).

Read `director/art_bible.md` first.

## 0. Scale derivation
In ref1 the arched door measures about 45 px tall at the keep's depth, and a door of about 2.2 m gives about 20 px/m. All heights below come from that scale. The finished building reaches **≈14.0 m to the finial tip**.

## 1. Plan and orientation

- **Octagonal hall:** centred on the world origin, **8.0 m across the flats** (facet length ≈3.31 m) at the outer wall face at ground level. Facet normals point at 0°, 45°, 90° and so on.
  - The **door facet faces −Y**.
  - The **window facet faces SW** (−X−Y diagonal), so the hero camera (azimuth −35°) sees the window facet almost face-on with the door facet turning away to the right, exactly as in ref1.
  - The **west wing attaches to the W (−X) facet**.
- **West wing:** a rectangular annex 5.0 m wide (y −2.5..+2.5) running from the hall's W facet out to x = −10.0 (outer faces).
- **Side turret:** round, engaged in the wing's far west end, centre at about (−9.4, +0.6). It rises through the wing roof.
- **Overall bounding box** is about x −11.5..+5.4, y −5.4..+5.4, z 0..14.0.

## 2. Components (top-down list; everything is required)

### A. Hall walls (`KEEP_hall_wall_stones`, `KEEP_hall_wall_mortar`)
- **Wall:** octagonal rubble wall 0.7 m thick, from 0 to 3.45 m. It batters 2° (slightly wider at the base), and each facet bulges convex by 3–5 cm. The vertical corners are softly rounded (r ≈ 0.08 m), not knife-sharp.
- **Masonry:**
  - Flat-bedded coursed rubble per art bible §3. Courses are 10–18 cm with occasional 25 cm stones.
  - A footing course runs 0–0.35 m of larger stones that project 6–10 cm, partly sunk below Z=0.
  - Every visible stone is individually modelled. The mortar body is recessed 1.5–3 cm.
- **Openings:**
  - **Door (−Y facet), the actor hero spot:**
    - Opening centre at x ≈ +0.35 m (right of the facet centre, as in ref1).
    - Clear opening 1.05 m wide, semicircular head springing at 1.65 m, crown at 2.18 m clear above the threshold.
    - Surround: dressed-stone jambs (alternating long and short blocks) and a ring of 13–15 irregular dressed voussoirs, 0.28–0.32 m deep on the face and projecting 0.05 m from the wall. The surround's outer envelope is about 1.75 m wide and 2.65 m tall, as in ref1 (a broad pale arch ring).
    - Reveal depth 0.30 m to the door leaf. The inner splay widens inward.
  - **Window (SW facet):**
    - Centred on the facet. Clear 0.72 × 0.92 m, sill at 1.35 m.
    - Heavy timber frame (0.10 × 0.12 m) with a cross mullion making 2×2 lights. Glass panes are allowed as thin geometry with `M_glass`.
    - Dressed-stone sill projecting 0.07 m with a drip groove, a timber lintel or stone lintel above, and a reveal 0.35 m deep.
  - **W facet:** a narrow slit window 0.18 × 0.60 m (dark slot, as in ref1) with dressed jambs.
  - **NE and E facets:** small windows 0.5 × 0.6 m.
  - **N facet:** where the turret and back would be, keep the wall plain.

### B. Hall corner posts (×8) (`KEEP_hall_posts`, `KEEP_hall_post_bases`, `KEEP_hall_knee_braces`)
- **Posts:** square hewn timber 0.28 × 0.28 m with 3 cm chamfers, one at each octagon corner, engaged so they stand about 0.12 m proud of the wall corner. They run from the pedestal to the eave plate at 3.45 m.
- **Pedestals:** dressed stone blocks 0.48 × 0.48 × 0.35 m, chamfered, with a slightly splayed foot.
- **Knee braces:** each post carries a pair of curved knee braces (Y-bracket as in ref1), about 0.14 × 0.14 m section. They spring from the post at about 2.55 m and reach the eave plate about 0.65 m to each side, pegged at both ends with visible pegs.
- **Eave plate:** an octagonal ring beam 0.25 × 0.30 m sitting on the wall top and posts, lap-jointed at the corners with pegs.

### C. Skirt roof: tier 1 (`KEEP_roof_skirt_boards`, `KEEP_roof_skirt_structure`, `KEEP_roof_skirt_hips`)
- **Form:** octagonal hipped skirt roof.
  - Eave lip at **3.55 m** (lowest point), overhang 1.25 m horizontally beyond the wall face (eave across-flats about 10.5 m).
  - Rises to about 5.3 m where the collar sits, at a radius of about 3.5 m (across-flats).
  - Profile: about 40° main pitch, bell-cast to about 25° over the last 0.8 m. Hips are slightly concave.
- **Covering:** horizontal courses of long wooden shingles/boards as in ref1.
  - Each piece 0.6–1.2 m long, 0.20–0.28 m exposure, 3 cm butts. Courses are staggered.
  - Around 9–10 courses from eave to collar. The course lines wave ±2 cm.
  - Hip lines carry hip boards or saddle boards.
- **Underside (seen at actor eye level):**
  - Rafters and sprockets, about 6 per facet, 0.10 × 0.14 m, with chamfered ends.
  - A thick fascia/eave board (0.04 × 0.18) with a slight upturn at the hip corners.
  - Soffit boards between the rafters, and the eave plate visible.

### D. Shake collar: tier 2 (`KEEP_roof_collar_shakes`)
- **Form:** a steep skirt of long split shakes wrapping the base of the stone cone.
  - Foot at 5.25 m on the skirt roof with a foot diameter of about 7.0 m.
  - Top at about 6.2 m with a diameter of about 5.8 m (around 58–62°).
- **Shakes:**
  - 1.0–1.2 m long, 0.12–0.22 m wide, 2.5–4 cm thick, wedge-tapered, with uneven butts of ±6 cm.
  - The top ends project irregularly above the collar as a **jagged comb** (ref1's spiky crest), protruding 0.05–0.25 m with split and pointed tips.
  - Two overlapping layers; no gaps through to the sky.

### E. Stone cone tower: tier 3 (`KEEP_cone_stones`, `KEEP_cone_mortar`)
- **Form:** a tapering masonry "candle-snuffer" whose foot starts inside the collar at about 5.3 m.
  - Diameter about 5.3 m at the collar top (6.2 m), tapering to **2.5 m at 9.6 m**.
  - Profile slightly concave near the bottom: an elegant flare like ref1, not a straight cone.
  - Suggested radius profile (z: r): 6.2: 2.65, 7.0: 2.05, 8.0: 1.62, 9.0: 1.36, 9.6: 1.25.
- **Surface:**
  - Rough small rubble (stones 0.12–0.35 m) laid in rough courses following the cone surface.
  - Very uneven faces: this is the roughest stonework on the building.
- **Top:** at 9.6 m, a timber sole ring (0.2 × 0.2) for the lantern.

### F. Lantern belt (`KEEP_lantern_boards`, `KEEP_lantern_frame`)
- **Size:** octagonal, across-flats 2.75 m, 9.6–10.55 m (about 0.95 m tall), slightly overhanging the cone top.
- **Frame:** 8 corner posts 0.14 × 0.14 m, a sill ring and a head ring.
- **Boards:** vertical boards 0.14–0.24 m wide, 3 cm thick, with gaps and a couple of boards slightly askew.
- **Openings:**
  - On the −Y and SW faces, one opening 0.35 × 0.45 m with a frame.
  - ref1 also shows one large slanted board/hatch leaning on the front. Add one hinged hatch board propped open on the SW side.

### G. Lantern cap: tier 4 (`KEEP_cap_shingles`, `KEEP_cap_structure`)
- **Form:** an octagonal bell-cast pyramid.
  - Eave lip at **10.45 m**, eave across-flats **3.9 m** (deep overhang of about 0.6 m beyond the lantern).
  - Apex at about **12.55 m**.
  - Main pitch about 48–52°, flattening to about 25° at the eave. Hips are concave.
- **Covering:** small shingles 0.12–0.18 m wide, 0.12 m exposure, ~14 courses. Courses run horizontally, as in ref1, not radially.
- **Hips:** hip boards.
- **Underside:**
  - A carved eave ring beam and 8 small brackets at the corners.
  - Rafter tails visible.

### H. Main finial (`KEEP_finial_main`, `M_iron` + `M_timber`)
From the apex to **14.0 m** (about 1.45 m), as a turned/forged profile:
1. A socket collar Ø 0.20.
2. A ring.
3. A bulb Ø 0.22.
4. Two thin rings.
5. An elongated onion/teardrop Ø 0.15 × 0.30 tall.
6. A neck.
7. A tapering spike to a point.

It leans about 1° and has 24–32 radial segments (smooth silhouette).

### I. West wing (`KEEP_wing_wall_stones`, `KEEP_wing_roof_thatch`, `KEEP_wing_ridge_comb`, `KEEP_wing_door`, `KEEP_wing_window`)
- **Walls:** rubble, 0.6 m thick, eave/wall top at 2.55 m, in the same masonry character as the hall but slightly rougher.
- **Roof:**
  - A steep thatch-style roof at 50° (ref1 shows a thick straw/shake thatch), 0.40 m thick, overhang 0.55 m, with the eave lip at **≥2.40 m**.
  - Ridge at about 6.0 m running E–W from the turret into the hall's collar/skirt roof, with properly modelled valleys and junctions. No intersecting-through-wall cheats; flashing/fillet where thatch meets stone.
  - Thatch as stepped layers about 0.3 m deep, with bundles or strand clumps along the eave edge and a rounded eave roll.
  - The east end dies into the hall roof. The west end hips around or butts the turret.
- **Ridge comb:** a row of splayed split shakes/sticks along the ridge (ref1's spiky crest), 0.3–0.5 m tall, irregular, with a ridge-rider log or pegs holding them.
- **Plank door:** in the wing's south wall, in the re-entrant corner next to the hall (centre at about x = −4.9).
  - Rectangular, 1.0 × 2.10 m clear.
  - Heavy timber frame 0.18 × 0.20 with a lintel and a stone threshold at +0.10.
  - 6–7 vertical planks, 3 strap hinges and a latch.
  - Set back 0.2 m in the wall.
- **Window:** a small window 0.45 × 0.55 m, sill 1.3 m, with a timber frame, in the south wall near the west end.

### J. Side turret (`KEEP_turret_stones`, `KEEP_turret_corbel_collar`, `KEEP_turret_drum`, `KEEP_turret_cap_shingles`, `KEEP_finial_turret`)
- **Body:** a round rubble tower, Ø 3.4 m at the ground, tapering (concave) to Ø 2.6 m at 6.0 m. It is visible inside the wing at the west end and rises through and above the wing roof.
- **Corbelled cushion collar:** a band of large rounded stones, bulbous, 6.0–6.6 m, max Ø 3.0 m (ref1: a mossy rounded ring under the cap).
- **Short drum:** Ø 2.3 m, 6.6–7.0 m, with a vertical-board belt.
- **Cap:** octagonal bell-cast cap, eave lip at 7.0 m, eave across-flats 3.0 m, apex 8.4 m, small shingles, in the same vocabulary as G.
- **Finial:** in the same vocabulary as H, scaled to about 1.15 m. Tip about 9.6 m.

### K. Ground contact (`KEEP_ground_rubble`, `KEEP_threshold`)
- **Thresholds and steps:**
  - A worn flat threshold stone at the main door, top at 0.12 m.
  - One outside step stone, 0.6 × 1.4 × 0.12 m (risers 12 cm), with rounded edges.
- **Rubble:** 40–80 scattered rubble stones of 0.05–0.4 m along the wall bases, some half-buried, clustered at corners and pedestals.
- **Interior:** a floor slab inside at +0.12 m, visible through the window reveal or door.

## 3. Detail priorities

1. The entrance close-up is the most important: door surround, door leaf, hinges, threshold, adjacent corner post with knee brace, eave underside.
2. Tier silhouettes: skirt, collar comb, cone flare, lantern, cap, finial. Each must overlay ref1 within about 10%.
3. Masonry realism.
4. Wing roof and turret.

## 4. Door leaf detail (actor close-up)
- **Leaf:** an arch-topped leaf filling the opening. 7 vertical planks 40 mm thick, varying 13–18 cm wide, with V-chamfered joints, slightly uneven bottom edges and one plank split.
- **Back:** 3 ledges on the back.
- **Ironwork:**
  - 3 forged strap hinges on the face, 50 mm wide and 6 mm thick, tapering to a spear/fleur terminal, with 6–8 domed nail heads each.
  - Pintles in the stone jamb.
  - A ring pull with a backplate and a keyhole plate.
- **Clinch nails:** a grid of clinch-nail heads along the ledge lines.

## 5. Budget guidance (target about 0.9–1.4 M triangles)
- Hall + wing + turret masonry: about 550k. Cull or skip stone back faces that are buried in the wall core.
- Cone masonry: about 150k.
- All roofing: about 300k.
- Timber and iron: about 150k.
- Rubble and ground: about 50k.

## 6. 10/10 acceptance criteria (all must be true)
1. **Silhouette:** the hero and front renders read as ref1's keep at a glance, with the same tier order and relative widths: skirt eave ≈ 10.5 m, collar ≈ 7.0 m, cone base ≈ 5.3 m, cone top ≈ 2.5 m, cap ≈ 3.9 m. The finial is tall and slender. The turret cap is lower than the collar top of the main cone. Heights are within ±10% of this spec.
2. **Scale:** the 1.8 m figure fits the door with about 0.35 m headroom. The eave over the door is ≥ 3.5 m and the wing eave over the plank door is ≥ 2.4 m. The step riser is ≤ 18 cm.
3. **Masonry:** every stone is individual and bevelled, with recessed mortar, coursed rubble character, dressed surrounds and a footing course. No repeating tiles visible, no flat walls with displacement.
4. **Roofs:**
   - Each covering unit is individually modelled with thickness and staggered overlap.
   - The bell-cast eaves, the jagged collar comb and the ridge comb are present.
   - The eave underside shows rafters, soffit, plate and fascia.
   - The roofs meet each other and the walls cleanly: no gaps and no visible interpenetration.
5. **Timber:** the 8 posts with pedestals and paired knee braces, pegged; chamfers everywhere; the lantern framing.
6. **Ironwork and door:** per §4, all modelled.
7. **Age pass:** wavy eaves and courses, slight sag, finial lean, a few slipped or missing shingles, uneven shake tips, stones varying in protrusion. Nothing is perfectly regular, and the effect is believable rather than chaotic.
8. **Technical:**
   - Deterministic script, origin and orientation per §1, named objects and material slots, UVs on all meshes.
   - ≤ 1.5 M triangles and `.blend` < 80 MB.
   - No artefacts in any of the 6 review views.
9. **Must-fix list empty**, and the Director's side-by-side with the reference crops raises no objection.
