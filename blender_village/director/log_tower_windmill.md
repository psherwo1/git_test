## Round 1 — score 7/10

**Reviewed:** renders/tower_windmill/round_01 (hero, front, side, back, aerial, actor_closeup, stats.json), plus director close-ups in renders/tower_windmill/round_01/director_extra (d01–d10, e01–e06, f01–f03). Compared with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village. Stats: 816,212 tris, 43 objects, bbox 12.93 x 8.97 x 17.17 m, .blend 17.9 MB. Technical compliance is clean.

**Verdict:** This is a strong first build. The stone drum, balustrade band, cornice, apron, octagonal smock tower, buttress, props, door and interior are all present and individually modelled. Detail density is already at the level of a solid game asset. The grade is capped by silhouette fidelity of the signature element, the rotor. ref1's mill reads as a large, dense 16-blade "sunflower" wheel with a single broad board-clad sail at about 9 o'clock. Ours reads as a conventional four-lattice-sail Dutch mill with a small, sparse fan of narrow paddles behind it. The lower sails also hide the whole timber tower in the front and hero views. On top of that:
- The cap is a tall pointed spire, where ref1 has a low ridged hipped cap.
- Several CG tells remain:
  - puffy "soap-bar" stones
  - door strap hinges that render as fins
  - a see-through hole in the apron over the door
  - the cap floating above the curb
  - identical balusters
  - perfect-cylinder props

Axis scores:
| Axis | Score |
|---|---|
| Silhouette | 6 |
| Proportion and scale | 8 |
| Construction | 7 |
| Detail | 8 |
| Age | 6.5 |
| Technical | 9 |

**Strengths:**
- The base massing matches mill_stone_base: battered drum, plain rubble zone, a balustrade band between two string courses, a blind arcade with real rubble-backed recesses and voussoir rings, a corbel cornice, a shake apron, and the sloping +X buttress. Props land on the left and the buttress sits on the right, as in ref1.
- Every stone is an individual piece in coursed rows with through-stones, and the footing course projects.
- The entrance is genuinely close-up-able: dressed jambs, an arched voussoir ring, a worn threshold and a step stone. The ledged plank leaf is ajar, and there is a plastered passage with a flagstone floor, a ladder and a ceiling.
- Human scale is right: the door is 1.05 x 2.18 m, the riser is 14 cm and the headroom is good.
- The timber tower is properly framed: proud corner posts, a sill, rails with drip boards, a top curb, three lifts of boards with battens, a propped hatch and a 0.55 deg lean.
- The rotor engineering is credible: poll end with bolts, clamps, hemlaths, a weather twist, riveted blades on two iron rings, spokes and ties. The numeric clearance checks pass.
- The build is deterministic and fast (7 s). Naming, collection, transforms, UVs and slots are compliant. 816k tris, well inside budget.

**MUST-FIX (priority order).** Items 1–3 deliberately amend spec_tower_windmill.md §E/§G/§H and acceptance criterion 1 ("four lattice sails"). Where they conflict with the spec, these numbers win.

1. **Rotor composition: match ref1, one board sail plus a dominant wheel.**
   - Delete the lattice (bars and hemlaths) from sails B, C and D. They become bare tapering stock arms (0.30 at the poll, 0.20 m at the end) that run out to the outer rim and are bolted to it. Each arm ends at r ≈ 3.35 m, about 0.15 m past the rim, with an iron strap and 2 bolts where it crosses the rim.
   - Optional: an iron or stone counterweight box (about 0.25 x 0.30 x 0.50 m) on arm C, which shares a stock with A, at r ≈ 2.6 m.
   - Sail A stays at about 9 o'clock (+8 deg) and runs to r 5.6 m. Rebuild it as ref1's broad plank paddle:
     - Board cladding on both sides of the stock and whip.
     - The panel runs from r ≈ 2.0 m to 5.6 m. It is about 1.5 m wide at the heel and 1.9 m at the tip (leading side 0.7→0.8, trailing side 0.8→1.1).
     - 6–9 radial boards per side, 2 cm thick, 14–24 cm wide, with 0.5–1.5 cm gaps and uneven ends of ±4 cm.
     - Nailed to 5–6 visible sail bars, with the hemlaths kept.
   - Target: in the front, hero and ref-angle views, the tower must be visible below the wheel (about 5.4 → 7.7 m), as in mill_overall.
2. **Wind-wheel blades** (spec §H amended):
   - Blades span r 1.35 → 3.90 m (currently 1.8 → 3.8).
   - Width is 0.55 m at the heel, flaring to 1.15–1.20 m at the tip. The gap between neighbouring tips should be 0.30–0.38 m, and the gap at r 2.5 m at most 0.25 m. The annulus must read as near-continuous, like mill_sails_wheel; today it reads as narrow paddles with gaps wider than the blades.
   - Pitch 12–15 deg (currently 25) so the blades read broad and face-on.
   - Inner ring at r 1.35 m and outer rim at r 3.15–3.25 m.
   - 3–4 boards per blade, square-cut tips with ±3 cm irregularity and worn corners.
   - Re-run the blade/stock and rotor/prop/apron clearance checks.
3. **Cap profile** (spec §E amended): the current pointed pyramid (apex 12.6 m plus spike to 13.1 m) reads as a turret spire in the side, back and d07 views.
   - Rebuild it as a low hipped cap with a short ridge along the windshaft heading: ridge length 0.9–1.2 m and eave-to-ridge height 1.1–1.3 m (ridge ≈ 12.0 m).
   - Main pitch about 40 deg, bell-cast to about 25 deg at the eave.
   - Footprint stays about 2.7 x 2.5 m.
   - Replace the spike with either nothing or a 0.2–0.3 m knob at the rear hip.
   - Rebuild the hood/cap junction with a proper valley. Today the hood's ridge shingles stick out as spiky slivers (e04).
4. **Cap floats above the curb:**
   - Today there is an open band about 0.15–0.25 m high between the cap eave plate (10.80 m) and the curb top (10.55 m), carried on Ø≈6 cm truck wheels. It reads as a hovering hat (f02, d07, side).
   - Fix: add a vertical board skirt/valance 0.30–0.35 m deep hanging from the cap frame outside the curb, with a gap to the curb of at most 3 cm.
   - Make the truck wheels Ø 0.18–0.22 m cast iron with axle brackets, sitting on the curb.
5. **Apron defects:**
   - (a) **Hole in the apron:** on the −Y face directly above the door, a patch of about 1.0 x 0.4 m of shakes and sarking is missing, and you can see the battens and rafters through it (f03, also visible in hero and front). Only individual missing shakes that expose the course below are allowed (art bible §6), never a see-through hole.
   - (b) **Floating shake cluster:** a cluster of about 5 "slipped" shakes at the front-right top course floats 5–8 cm off the roof. Seat it.
   - (c) **Shake shape:** shakes are uniform flat parallel-edged slats. Give them:
     - a taper from a 2.5–3.5 cm butt to a 0.8 cm head
     - split, tapered outlines (±2 cm)
     - a slight cup or crown
     - lengths of 0.6–0.8 m
     - more ragged butts
6. **Door ironwork and leaf:**
   - The strap hinges are rotated 90 deg. The prof is 9 mm x 52 mm swept with up=(0,−1,0) at y=−0.0045, so the 52 mm width stands out of the leaf as a fin and they render as thin rods (e01, d06).
     - Lay them flat: 50 mm wide and 7 mm thick, with the back face on the plank face and a flat spear terminal. Seat the nail heads on the strap.
     - Audit every other strap swept with the same convention (prop straps, collar lugs, blade brackets).
   - The arched head of the leaf shows polygon facets at the crown (e01). Use at least 24 arc segments and cut the boards to the arc.
7. **Masonry looks puffy (the biggest close-up CG tell).** Rubble and dressed stones read as inflated soap bars or pillows (actor_closeup, e01, d09).
   - (a) Rubble arris radius: reduce from up to 2.8 cm to 0.8–1.5 cm.
   - (b) Outlines: more angular split-stone polygons, with 3–4 straight fracture cuts per stone instead of rounded blobs.
   - (c) Faces: a flat bed with 1–2 tilted facets per face and pillow at most 1.0 cm.
   - (d) Mortar recess: reduce from 2.4 cm to 1.2–1.5 cm, with joints 1–2.5 cm, so the wall reads as tight coursed rubble as in mill_stone_base.
   - (e) Dressed jambs, voussoirs, coping and cornice:
     - Keep the 1 cm chamfer, but shade the large faces flat (sharp edges plus weighted normals). Today smooth-shaded normals bulge every block.
     - Add 2–4 spalls or chips on each hero block (door jambs, arch, coping).
     - Vary voussoir widths ±25%.
8. **Arcade proportion:**
   - The blind arches are squat: about 0.72 w x 0.80 h clear (h/w ≈ 1.1). In mill_stone_base they are tall round-headed recesses with h/w ≈ 1.5.
   - Make the clear opening 0.70–0.75 w x 1.05–1.10 h. Start the recess sill directly on the upper string course (≈2.95 m) and put the crown at about 4.0 m.
   - Make room by moving the cornice, curb and apron up by at most 0.12 m (cornice about 4.15–4.60, apron eave about 4.55), and/or slimming the balustrade band to 2.50–2.85 m.
9. **Balusters:** the 69 identical lathe-perfect balusters at an exact pitch are a repetition tell. Vary:
   - height ±8 mm and diameter ±10%
   - pitch ±1.5 cm and lean ±1.5 deg
   - erosion: 10–15% eroded or chipped (a broken bead or neck)
   - 2–3 replaced by plain blocks
   - a stubbier profile closer to ref (2–3 turned bands, not a classical vase)
10. **Raking props:** these are 12-sided smooth perfect cylinders with single-vertex "knot" spikes, resting on top of box chocks, with stone pads pasted onto the ground (d08).
    - 16–20 sides, tapering from Ø 0.20 m at the foot to 0.15 m at the head.
    - A visible bow of 6–12 cm.
    - 4–6 real knots or branch stubs (Ø 3–5 cm, 2–4 cm proud) plus a few checking grooves.
    - An axe-cut foot seated in a notched chock, with the iron pin visible.
    - Sink the stone pads 5–8 cm into the ground and soften their edges.
11. **Iron prop collar at 9.5 m:** today it is a thin round wire hovering off the tower faces (d07, e03).
    - Make it a flat strap 60 x 10 mm lying on the boards and following the octagon.
    - Add bolted lugs where the props attach.
    - Also break the top curb ring into 8 timber segments with lap joints and pegs. It is currently one continuous crisp octagonal box.
12. **Buttress coping:**
    - The coping slabs are near-identical (about 0.8 m), stair-stepped, and there is a see-through gap under one slab at mid-slope (d09).
    - Vary lengths 0.5–0.9 m, bed them on mortar, and close every gap.
13. **Path flags at the door:** today they are thin plates lying on Z=0 (actor_closeup). Make them 8–12 cm thick, sunk 3–5 cm, with worn soft edges.

**Nice to have:**
- ref1's timber tower is about 1.3x the stone base height (ours is about 1.15x). If clearances allow, raise the tower curb by about 0.4 m (hub to about 12.0 m).
- Board-level irregularity on the tower: ±0.5 deg board lean, 2–3 split board ends and one patched board.
- Optional `M_moss_clump` cushions at the apron eave lip and the cap eave.
- Slightly vary the wheel-blade outlines per blade (±2 cm) so the 16 blades are not clones.

## Round 2 — score 8/10

**Reviewed:** renders/tower_windmill/round_02 (hero, front, side, back, aerial, actor_closeup, stats.json), plus director close-ups in renders/tower_windmill/round_02/director_extra (r01–r13, s01–s07, t01–t04). Compared side by side with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village. Stats: 899,500 tris, 35 objects, bbox 12.76 x 8.92 x 15.70 m, .blend 20.2 MB. Deterministic, transforms identity, UVs and named slots present. A BVH check of the 74 wind-wheel parts found no blade-to-blade interpenetration; the only contacts are battens seated on their boards.

**Verdict:** This is a big step up. At thumbnail size it now reads as ref1's mill:
- a dense near-continuous 16-blade "sunflower" wheel
- one board sail at 9 o'clock
- bare arms
- a low hipped cap
- the timber tower visible below the wheel
- props on the left and the buttress on the right

The apron is now real split shakes with no hole, the strap hinges lie flat, the arcade has the right tall proportion, and the balusters vary.

It is not yet near-hero, for these reasons:
- **Sail A is the wrong shape and texture.** The signature board sail reads as a long, narrow gridded crate. In ref1 it is a broad, almost square paddle of radial boards.
- **The rubble reads as flat plates on plaster.** In the actor close-up, the stones look like thin flat plates stuck onto a smooth plaster wall.
- **The timber tower and apron sit about 0.5 m too low against the art.** The apron pitch of 30 deg is below the art bible's 35–45 deg.
- **Several primitive-looking parts remain:**
  - plastic-dowel props on clean box chocks and slab pads
  - 114-face box stocks
  - a messy cap ridge with slivers at the hood

Axis scores:
| Axis | Score |
|---|---|
| Silhouette | 8 |
| Proportion and scale | 8 |
| Construction | 8 |
| Detail | 8 |
| Age | 7 |
| Technical | 9 |

**Strengths:**
- The rotor composition now matches ref1. The wheel is a near-continuous annulus with an open eye of about 0.35 R, and one board sail sits at 9 o'clock. B, C and D are bare arms strapped to the rim, with a counterweight on C. The tower reads below the wheel. Clearances pass.
- The low hipped cap (ridge 12.40 m) replaces the spire, so the side and back silhouettes now read as a mill cap. The valance closes the hovering gap. Truck wheels, sheers, rafters and the curb of 8 half-lapped, pegged segments are present.
- The apron rebuild is good:
  - tapered, split, ragged-butt shakes in 4 readable courses
  - full sarking and a fascia
  - no see-through hole
  - no floating shakes
- The base band is now right:
  - The arcade is 0.72 x 1.08 clear with h/w 1.5, and its rubble-backed recesses, irregular cracked voussoirs and dressed piers match mill_stone_base (s07).
  - The balusters are stubby, varied and partly replaced by plain blocks.
- The ironwork is right: flat strap hinges with spear terminals and seated nails, a ring pull, a flat 60x10 collar with bolts, clevis lugs and cleats at the prop heads (t02), and hex-bolted poll-end plates (t04).
- The base massing, door scale (1.05 x 2.18, 14 cm riser), interior depth, dentil cornice and buttress remain correct.

**MUST-FIX (priority order).** Item 1 amends my own round-1 numbers for sail A after measuring the crops. Where it conflicts with round 1 or the spec, these numbers win.

1. **Sail A shape and face (silhouette signature; r01, r11, front, hero).**
   - In mill_overall and mill_sails_wheel the board sail is a broad, almost square paddle:
     - panel from r ≈ 2.5 to 5.6–5.8 m (≈ 3.2 m long)
     - ≈ 2.3 m wide at the heel, flaring to ≈ 2.9 m at the tip
     - the stock roughly centred, with leading side ≈ 45%: leading 1.0 → 1.25 m, trailing 1.3 → 1.65 m
   - Ours is 1.5 → 1.9 m wide over 3.6 m, which reads as an ordinary lattice sail.
   - The face reads as a crate or grid. Six full-width bars and two hemlath rails sit in front of short board segments.
   - Fix:
     - Put the sail bars **behind** the boards (on the back, windward face), so only their ends show 3–5 cm past the panel edges.
     - On the front face keep only the stock and whip with their U-clamps, plus at most 2 cross cleats (heel and mid, 8 x 3 cm).
     - Use full-length radial boards (one 1–2 butt joint per board line is fine). Make them 8–10 per side, 2 cm thick and 14–22 cm wide, with 0.5–1.5 cm gaps.
     - Fan the boards slightly so the seams diverge toward the tip.
     - Make the tip edge ragged by ±4 cm, with 1–2 boards short by 8–15 cm or split at the tip.
     - Add a slight cup or warp per board (±5 mm) and nail-head rows at the cleats.
   - Re-run the rotor/prop and rotor/apron clearance checks. The sweep radius grows to about 5.85 m.
2. **Rubble masonry reads as flat plates on plaster (actor_closeup, r13, r06).**
   - The fracture-cut outlines leave wide triangular mortar voids at stone ends (5–10 cm). The stone faces stand only ≈ 1.4 cm proud with ≈ 1 cm depth variation, so the wall reads as thin appliqué tiles on a smooth plaster body. About 25% of the plain zone is visible mortar.
   - Fix:
     - (a) Fill every void wider than 3 cm with pinning stones of 4–12 cm (art bible §3), or let neighbours share fracture planes. The target is joints of 1–2.5 cm and no more than 12–15% visible mortar.
     - (b) Recess the mortar 2–3 cm, raking it to 4–5 cm in the bottom 0.6 m.
     - (c) Vary face depth 0.5–2.5 cm per stone as specified, and tilt 15–20% of stones 2–4 deg so one end stands proud.
     - (d) Give the mortar body low-frequency relief (±5 mm), and slump it slightly into each joint (a concave strike) instead of a smooth cylinder.
   - Keep the crisp split-stone arrises. They were the right fix.
3. **Timber-tower height and apron pitch (front, hero, r02 against mill_overall).**
   - Measured against ref1 (wheel R 3.9 m = 59 px/m), the art has:
     - the apron top ≈ 6.1 m (ours 5.52)
     - the cap eave ≈ 12.2 m (ours 11.22)
     - the hub ≈ 12.4 m (ours 11.87)
     - the timber tower ≈ 1.3 x the stone base (ours 1.18 x)
   - Our apron pitch is ≈ 30 deg (rise 0.90 over 1.55 m), which is below the art bible's mill apron range of 35–45 deg.
   - Fix:
     - Raise the tower foot and sill to ≈ 6.0 m. The apron then runs from eave 4.62 m at r 3.15 m up to 6.0 m, ≈ 41 deg, with 3 courses of 0.66–0.8 m shakes.
     - Raise everything above it by ≈ 0.5 m: top curb ≈ 11.47, cap eave ≈ 11.72, ridge ≈ 12.9, hub ≈ 12.37.
     - Keep the tower taper (3.1 → 2.0 m across flats).
     - Re-seat the props (collar ≈ 10.3 m), and re-run the clearance checks.
   - This amends the spec's 4.5/5.2 ratio.
4. **Cap ridge, hips and hood junction (t03, t04, s01).**
   - The ridge is a pile of hip-saddle boards lying at random angles around the knob, with no continuous ridge capping.
   - Thin triangular shingle slivers (1–3 cm wide, 20–40 cm long) stick out at the hood/front-face valley and at the hip below the hood.
   - Fix:
     - Fit a continuous ridge capping of two boards in a V (2.5 cm thick, 15–18 cm per leaf) along the 1.0 m ridge.
     - Run hip capping boards from each ridge end to the eave in 0.6–0.9 m lengths with lapped joints. Each piece should follow the hip line within ±1 deg and sit within 1 cm of the shingles.
     - Seat the knob on a small square plinth block at the rear ridge end.
     - Cull or merge any clipped shingle narrower than 5 cm at the hips and valleys, and let the lead flashing take that strip.
   - Nothing may stand off the roof surface more than 2 cm except the knob.
5. **Raking props still read as plastic dowels (r08, hero, aerial).**
   - Each pole has only 34 rings over about 10 m. The checks are one-vertex grooves of 0.6–1.1 cm and vanish under smooth shading. The knots are hard to see. The foot end is a rounded bullet between plain box cheeks. The pads are clean chamfered slabs on top of the ground.
   - Fix:
     - Use ring spacing of 6–8 cm or less and 24 sides.
     - Add 2–3 real checks per pole: V-grooves 1.5–2.5 cm wide and 1.5–2.5 cm deep, over 0.8–2 m.
     - Add 2–3 long adze flats or bark-strip remnants (±1 cm).
     - Add 4–6 knots of Ø 4–7 cm, 2–4 cm proud, at least 2 of them within 2.5 m of the foot.
     - Make the foot a faceted axe-cut end (2–3 planar facets, crisp), seated in the chock notch with the bird's mouth visible.
     - Use hewn chocks and cheeks (adze-faceted, 1.5–2.5 cm worn chamfers, an end check).
     - Make the pad an irregular rough stone 0.55–0.75 m across with a domed, uneven top (±2 cm), sunk so only 5–9 cm shows, with 4–6 small rubble stones and a soil lip around it.
6. **Stocks, arms and whip are clean boxes (r10, r07, r12).**
   - MILL_sail_B, C and D stocks are 114-face tapered boxes. The A stock and whip are equally clean.
   - Fix:
     - Give them hewn faces (2–3 shallow adze facets per face, ±5 mm) and varying chamfers of 1.5–3 cm.
     - Add 1–2 long checks per stock (1 cm wide, 0.5–1.5 m) and split or checked end grain at the arm tips.
     - Add 2 iron bands per arm near the poll (50 x 6 mm, with bolts).
   - Arm C's counterweight is fine.
7. **Buttress coping (r09).**
   - The slabs are large, smooth, perfectly flat soap-bars with no visible spalls. Each joint shows a 1–2 cm step lip.
   - Fix:
     - Use a weathered, slightly dished top (±1 cm) with 1–2 visible spalls per slab on the top arris.
     - Wear the upper edges more than the lower ones.
     - Make each slab's top surface flush (±3 mm) with the next at the joint, with no stepped lips.
     - Add 1–2 cracked slabs and one slab rotated 1–2 deg in plan.
8. **Path flags and step (s06, actor_closeup).**
   - They are soft, smooth, uniform-thickness rounded rectangles that read as rubber tiles.
   - Fix:
     - Use irregular 5–7-sided outlines with ±4 cm deviation and 1–2 straight broken edges.
     - Give the tops low-frequency undulation (±1 cm) and edge chips (2–3 per flag).
     - Make the step stone's front arris worn more at the centre (2–3 cm hollow).
     - Add a ring of small half-buried gravel and stones (3–8 cm) around each flag so it sits in the ground rather than on it.
9. **Valance vs sheer ends (t01, s05).**
   - The sheer ends (cap-local x = 0.98 and −1.20, r ≈ 1.25 and 1.43 m) pass straight through the valance boards (inner face r 1.112 m) with no notch.
   - Fix: notch the boards around each sheer end (1 cm clearance), and either fit a small end board, or chamfer the sheer ends and let them project 8–15 cm, with an end check.
10. **Tower boards too clean (s03, t02, r02).**
    - The cladding is long, straight boards of identical thickness. The ±0.5 deg lean is invisible.
    - Fix:
      - Add 1–2 horizontal butt joints per face at staggered heights between rails, with 1–2 cm drip gaps (ref1 shows horizontal joints).
      - Vary board proudness ±4 mm and the bottom ends ±3 cm.
      - Add 2–3 more visibly warped boards (cupping 6–10 mm) and 4–6 more split or checked ends on the hero (−Y and −X) faces.
11. **Baluster erosion.** The rate is 4 of 61 (7%), against the requested 10–15%. Bring it to 7–9 balusters, with at least 2 visible from the front camera.

**Accepted from known gaps:**
- Diagonal rim ties dropped (the blade battens and arm straps carry the rim).
- Truck wheels hidden inside the valance.
- Hatch clearance of 0.16 m.
- Moss skipped.
- Ivy is set dressing, not building geometry.

**Nice to have:**
- In ref1 the hub sits right of the tower axis (≈ 1.4 m in the painting, a painterly cheat). Consider yawing the cap from −15 deg to 0..+6 deg (hub offset x = 1.95·sin(yaw), so currently −0.50 m, i.e. left), so the hub reads 0–0.2 m right of the axis in the front view and the wheel's left half gains distance from the props. Keep the hero view readable.
- Shingle rotation jitter on the cap side faces is a little noisy at grazing angles. ±3 deg is enough.

## Round 3 — builder entry

**Renders:** renders/tower_windmill/round_03 (hero, front, side, back, aerial, actor_closeup, stats.json, hidden.json), 32 samples. This replaces the provisional 04:15 render.
**Stats:** 1,110,929 tris, 34 objects, bbox 12.96 x 9.05 x 16.19 m (sail tip), .blend 28.0 MB (compressed). Build time 12 s, deterministic. **est_hidden_pct 15.2%** (was 44.6% in the provisional render). **material_slot_count 11**, all from the palette (`M_soil` is now `M_earth`).

**Round-2 must-fix items:**
1. **Sail A** is now a broad paddle with r 2.5 → 5.8 and 19 full-length fanned radial boards. The bars sit behind the boards and only 2 cleats show on the face. The tip is ragged, two boards are short and one is broken, and there are butt joints, cupping and nail rows.
2. **Rubble.** 993 pinning stones were added. Visible mortar is now 9.8% on the drum and 9–10% on the buttress, and the widest void is 3 cm. The mortar is recessed and raked deeper below 0.6 m. Stone depth and tilt vary, the mortar has relief and a concave strike, and the hidden mortar skin is culled.
3. **Heights.** The tower now runs from 5.95 to 11.45 m. The apron is ≈ 41 deg with 3 courses, the cap ridge is at 12.88 m and the props are re-seated. The cap is yawed +3 deg, so the hub sits about 0.1 m right of the axis.
4. **Cap.**
   - Continuous V ridge capping.
   - 12 lapped hip pieces, max deviation 0.91 deg.
   - The knob sits on a plinth block.
   - Shingles narrower than 5 cm are culled at the hips, valleys and hood: 22 + 6 slivers, plus 27 fully covered shingles.
5. **Props.**
   - 24–35 sides at 4.5 cm ring spacing.
   - 2–3 V checks, adze flats and a bark strip per pole.
   - 4–6 knots, 2 of them within 2.5 m of the foot.
   - Axe-cut feet in a bird's-mouth sole, and hewn chocks and cheeks.
   - Sunk rough stone pads with a ring of small stones and a soil lip.
6. **Stocks and whip** use `hewn_beam`, with adze facets, variable chamfers, checks and split end grain. Each arm has 2 bolted iron bands near the poll.
7. **Buttress coping.** 8 dished slabs with tops flush at the joints. They have spalls and more wear on the upper edges, 2 are cracked and 1 is turned in plan.
8. **Path flags and step.** The flags are irregular 5–7-sided slabs with undulating tops and chips. The step has a worn hollow. 73 half-buried gravel stones were added.
9. **Valance.** The boards are notched around all 4 sheer ends.
10. **Tower boards.** Staggered horizontal butt joints with drip gaps, varied proudness and bottom ends, 3 strongly cupped boards and 8 split ends.
11. **Balusters.** 8 of 61 are eroded (13%), 3 of them on the front arc, plus 3 plain blocks.

**Clearances:** sails vs apron and props ≥ 0.30 m PASS. Lowest rotating point 8.43 m. Blade/stock, board/wheel and board/stock gaps all pass.

**Known gaps:**
- Hidden triangles are at 15.2%, just over the 15% target. The largest remaining hidden share is base mortar (30.7%, ~21k), and the base stones and dressed stone still carry back and side faces. This is planned for round 4.
- Moss is not modelled.
- Diagonal rim ties have been dropped (accepted in round 2).

## Round 3 — score 8/10

**Reviewed:** renders/tower_windmill/round_03 (hero, front, side, back, aerial, actor_closeup, stats.json, hidden.json), plus director close-ups in renders/tower_windmill/round_03/director_extra (u01–u14, v01–v06, w01–w02). Compared side by side with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village. Stats: 1,110,929 tris, 34 objects, bbox 12.96 x 9.05 x 16.19 m, .blend 28.0 MB, 11 material slots (all palette), **est_hidden_pct 15.2% (over the 15% limit)**. Director measurements on the .blend: sail A board panel spans r 2.51 → 5.82 m, ≈2.3 m wide at the heel → ≈2.7 m at the tip (target met). Wind-wheel gaps from area sampling: 16 clean inter-blade gaps of 0.22 m at r 2.5, 0.27 at r 3.0, 0.38 at r 3.8; no intra-blade board gap over 1.2 cm, so the wheel reads as 16 distinct paddles (target met).

**Verdict:** A clear step up and now an upper 8. Every round-2 silhouette item landed:
- Sail A is ref1's broad, near-square board paddle.
- The wheel reads as a dense 16-blade sunflower.
- The timber tower is tall enough (5.95 → 11.45 m) and the apron is steep enough (about 41 deg).
- The cap is a tidy low hipped cap with continuous ridge and hip capping.
- The rubble is now tight, coursed split stone with pinning stones.

At thumbnail and mid-shot it is unmistakably ref1's mill. It is not yet a 9 for four reasons:
- **The cap roof is see-through.** Missing shingles show a black void and battens, and sky leaks through between courses.
- **The entrance ground still reads CG.** The path flags look like cushions sitting on the ground. The rubble looks like rounded boxes on top of the ground. The prop feet look like stacked soap bars on a melted-wax disc.
- **The door leaf is brand-new joinery** in the actor close-up.
- **Producer notes are not met:**
  - hidden triangles are at 15.2% (note 6)
  - repeated parts share no mesh data (note 3)
  - the build code is not a parameterised kit (note 2)

Axis scores:
| Axis | Score |
|---|---|
| Silhouette | 9 |
| Proportion and scale | 9 |
| Construction | 8.5 |
| Detail | 8 |
| Age | 8 |
| Technical | 7.5 |

**Strengths:**
- **Silhouette matches ref1:**
  - stout arcaded drum, steep shake apron, tall tapering boarded smock tower and low hipped cap
  - the 16-blade annulus with one broad board sail at 9 o'clock, plus bare stocks strapped to the rim
  - two long near-parallel props plus a shorter one on the left, and the sloping buttress on the right
  - the tower reads below the wheel in the front and hero views
- **Sail A (u02, v04)** has fanned full-length radial boards, the bars hidden behind with only their ends showing, 2 nailed cleats, a ragged tip, a broken board and butt joints. It is exactly the ref read.
- **Rubble (actor_closeup, u05, u10, v06)** is now tight, flat-bedded split stone with pinning stones, recessed and raked mortar, and varied depth and tilt. The plaster-appliqué look is gone.
- **Cap (v01, v02)** has continuous V ridge capping, lapped bell-cast hip boards, a knob on a plinth, notched valance boards and no slivers at the hood.
- **Timber tower (u13, back)** has staggered horizontal butt joints with drip gaps, cupped and loose boards, split ends, rails with drip boards and a propped hatch.
- **Base band (u14)** has varied stubby balusters (eroded and plain blocks), irregular voussoirs, rubble-backed tall arcade recesses and a dentil cornice, matching mill_stone_base.
- **Rotor hardware (u03, w02)** has hewn stocks with iron bands, a bolted poll end, U-clamps and riveted rings. Clearances pass, with the lowest rotating point at 8.43 m.
- **Technical:** an 11-slot palette, deterministic 12 s build, 1.11 M tris and a 28 MB file.

**MUST-FIX (priority order):**
1. **Cap roof is see-through (v02, w01, w02).**
   - At least 2 "missing" shingles on the +X roof face open onto a black void with battens visible behind. One is mid-face about 0.45 m above the eave, the other about 0.3 m below the ridge.
   - Thin sky-coloured slits show between courses all over the cap.
   - Cause: culling covered shingle heads left nothing under the gaps.
   - Fix: lay a continuous sarking deck under every cap face, hip and hood: boards 2 cm thick and 15–25 cm wide, top face plus eave and verge edges only. Alternatively, put a full shingle of the course below under every missing or slipped shingle.
   - Also trim the shingle and hip-board shards that stick 5–10 cm past the hip-board ends at the eave corners (v02 lower right and lower left). Nothing may project more than 2 cm beyond the hip capping or the eave line.
   - Acceptance: zero black or sky pixels inside the roof outline from any exterior camera, checked at camera (9, 1.5, 12.5) → (0, 0, 12.2) at 70 mm and from the rear (−3.5, 5.5, 14.5).
2. **Path flags and step read as cushions on the ground (u11, actor_closeup).**
   - The flag tops sit 4.8–6.2 cm above the ground (fl z = 0.048–0.062). The full vertical sides are exposed and cast shadows, and the top arris is a continuous 1.6 cm roll.
   - Fix:
     - Set the flag tops 1.0–2.5 cm proud on the high side and 0–1 cm on the low side (tilt 0.5–1 deg). Keep the step at its current height (riser OK).
     - Replace the continuous roll with a 0.5–1.0 cm arris broken by the existing chips plus 1–2 crisp straight fracture edges per flag.
     - Add an `M_earth` soil fillet 3–6 cm wide around every flag edge, rising to the flag top.
     - Move the gravel (currently loose "sugar cubes" on top at the flag edges) into the joints between flags. Bury 40–70% of each stone, so that at least half sit 1 cm proud or less.
3. **Ground rubble and prop feet look placed, not settled (v03, u06, hero).**
   - (a) **Ground rubble.** The "boulder" pieces are rounded boxes buried only 20–45% (z centre = H·0.05–0.3).
     - Bury 45–65% of their height.
     - Switch them to the split-stone style used on the drum: 3–4 fracture planes and 0.8–1.5 cm arrises.
     - Give each cluster a soil collar 2–4 cm high.
   - (b) **Prop feet.** The chock, the slab under it and the two cheeks read as 3–4 stacked soap bars, and the soil lip is a flat plate of constant thickness with a wavy outline (melted wax).
     - Make the chock one hewn block using hewn_beam (adze facets ±5 mm, 1.5–2.5 cm worn chamfers, an end check).
     - Drop the intermediate slab, so the chock sits directly in a notch cut into the rough stone pad.
     - Model the soil lip as a mound that is 3–5 cm high at the pad and tapers to 0 at an irregular outer edge 0.25–0.4 m out, with 3–6 embedded pebbles.
4. **Door leaf is pristine in the actor close-up (u04, v06).** It has 6 planks of identical 4.2 cm thickness with 6 mm arrises, a dead-straight bottom end at Z_TH + 0.01, no checks and no wear. Per art bible §4:
   - Wear the outer arrises to 1.5–2.5 cm, with more wear at the bottom 0.4 m and on the lock stile.
   - Make the bottom end ragged and rotted (±2–4 cm), with 1–2 planks 3–5 cm short.
   - Add 2–3 face checks (3–5 mm wide, 0.3–0.9 m long) and 1 split at the arched head.
   - Vary plank proudness ±3 mm and the gaps 4–10 mm.
   - Let the free edge sag 5–8 mm.
5. **Apron eave fascia is one perfect smooth ring (u12, actor_closeup top edge, hero).** Bent timber cannot do this; it reads as a plastic rim.
   - Rebuild it as 14–18 straight fascia boards (0.9–1.3 m chords, 2.5–3.5 cm thick, 14–18 cm deep) with butt joints, 3–6 mm gaps and ends cut to the polygon.
   - Vary each board ±5 mm in height and ±3 mm out of plane, and wear the lower arris.
   - Add a low-frequency eave wave of ±2–3 cm (art bible §6).
   - The smooth plain ring at the apron top or tower foot (u12 top) gets the same treatment: one flashing board per octagon face, with lapped ends.
6. **Producer note 6: hidden triangles at 15.2% (must be ≤ 15%; aim for ≤ 13% so the round-4 additions fit).** Main offenders, from hidden.json:
   - MILL_base_mortar: 31% hidden, ≈20k. Delete the mortar body behind full stone cover and keep only a 2–3 cm skirt around each joint.
   - MILL_base_stones: 13.5%, ≈59k. Cut the buried side faces below the mortar recess depth + 5 mm.
   - MILL_buttress_stones: 16%, ≈22k. Same fix as the base stones.
   - MILL_base_dressed: 16%, ≈15k. Remove the baluster, corbel and voussoir faces against the wall or band.
   - MILL_cap_shingles: 23%, ≈11k. Cull covered heads once the sarking from item 1 is in.
   - MILL_tower_boards: 26%, ≈7k. Remove the back faces against the frame.
   - MILL_cap_iron: 39%. The truck wheels are invisible inside the valance; keep only what shows below its lip.
   Do not cut anything on a silhouette or a visible edge.
7. **Eye-level rubble arrises are uniform (u05).** Every rubble and pinning stone has the same continuous chamfer band all round its face, which reads as a moulded lip at 1–2 m.
   - Vary the arris per edge between 0.3 and 1.5 cm, with 1–2 crisp (≤ 3 mm) broken edges per stone.
   - Add a shallow conchoidal facet or step (3–8 mm) on 30% of the faces in the bottom 2.2 m of the drum and on the buttress sides.
8. **Producer note 3: repeated parts share no mesh data.** Everything is unique geometry merged into large meshes; MILL_base_stones alone is 437k tris.
   - Build variant pools and place them as linked-duplicate mesh objects (shared mesh data):
     - balusters: 61 placements from 8 variants, including the eroded and plain-block ones
     - dentil corbels: 6 variants
     - cap truck wheels: 1 mesh
     - hex bolt heads and ring-rivets: one pool of about 6 for the rotor, merged per component if the object count would pass about 250
   - Keep the per-placement jitter in the object transform (rotation ±, lean).
   - Report in the log: object count, unique-mesh count and shared-mesh count.
9. **Producer note 2: the build code is not a modular kit.**
   - Today the components are `build_base(parts)`, `build_cap(parts)` and so on, reading module constants (R_out, ARCH, DZ, AP_*, TW_*, CAP_*, HUB_*).
   - Expose parameterised component functions, each producing its own named object(s):
     - `round_stone_drum(r_base, r_top, height, zones, seed)`
     - `blind_arcade(n, clear_w, clear_h, z_sill, seed)`
     - `arched_door(width, height, reveal, seed)`
     - `shake_apron(r_eave, z_eave, r_top, z_top, courses, seed)`
     - `smock_tower(af_bottom, af_top, z0, z1, rails, seed)`
     - `mill_cap(length, width, rise, ridge_len, yaw, seed)`
     - `board_sail(r0, r1, w_heel, w_tip, seed)` / `stock_arm(...)`
     - `wind_wheel(r_in, r_rim, r_tip, n_blades, pitch, seed)`
     - `raking_prop(foot_xy, head_xyz, dia, seed)`
   - `main()` only calls them with this mill's numbers.
   - Prove it works: build a variant (drum r 2.0 m, tower 4.0 m, 12 blades) to a scratch .blend without errors, and save a hero thumbnail as renders/tower_windmill/round_04/director_extra/kit_test.png.
   - If the round time-box (note 8) is exhausted, item 9 may slip to round 5, but it must be done before a 10.

**Accepted / no action:**
- Moss not modelled (optional by the art bible).
- Diagonal rim ties dropped.
- The cap reads only through the wheel eye in the front view. The rotor must physically be in front of the cap; ref1's cap-over-wheel overlap is a painterly cheat.

**Nice to have:**
- Buttress coping (u10): the dishing and spalls barely read at mid range. Deepen 2–3 spalls to 1.5–2.5 cm and break one slab end.
- Door jamb and arcade pier blocks (u04, u14) still have softly waved outlines. Straighten the large edges and keep the wear to chips.
- Props at mid range (v05) still read smooth. Increase the bow to 8–12 cm and make the 2 lower knots 5–7 cm.
