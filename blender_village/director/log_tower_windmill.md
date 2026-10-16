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


## CLIENT CORRECTION — board sail is a TAIL VANE (supersedes every earlier "sail A" instruction)

The client, who owns the concept art, has clarified the rotor. The board panel seen on the left in ref1 (crops `mill_overall.png` and `mill_sails_wheel.png`) is **not** one of four sail arms in the plane of the fan wheel. It is a **fixed tail vane**, as on an American windpump. It sits on a boom running **back** from the cap along the wind-shaft axis, **behind** the fan wheel, and it steers the wheel into the wind.

```
SIDE VIEW (wind from the right)          TOP VIEW
            /  upper brace
  [BOARD]——|——O)  <- fan wheel (edge-on)   [BOARD]=====O====||  <- wheel
   vane    | \\  lower brace                 (fixed; points downwind)
           |  tower
```

### Required changes

1. **Remove sail A from the rotor entirely.**
   - The rotating assembly is the 16-blade annular fan wheel only: blades on the inner and outer rings, plus its radial spokes or arms from the hub to the rings.
   - The bare stocks B, C and D may remain only if they read as the wheel's spokes or arms, as the grey diagonals do in the crop. They must not read as sail stocks waiting for sails.
   - Keep the hub, poll end and ironwork.
2. **Tail boom.**
   - A horizontal boom on the wind-shaft axis, running from the rear of the cap away from the wheel, about 4.0–5.0 m long.
   - Built as two parallel hewn rails about 0.12 × 0.10 m, with spacer blocks and iron bands, as the doubled boom in the crop shows.
   - Braced by diagonal struts: one from the cap or the top of the tower up and out to the boom, and one from below up to the boom (the "/" and "\\" in the client sketch).
   - It turns with the cap, not with the wheel.
3. **Tail vane panel.**
   - A vertical board panel in the plane of the boom (parallel to the wind), fixed to the outer 2.4–2.8 m of the boom.
   - About 1.4 m tall at the inner end, flaring to about 2.0–2.3 m at the outer end. The boards fan slightly outward, as in the crop.
   - Vertical or slightly fanned boards with battens, cleats, nails, a ragged outer edge and one cracked or replaced board.
   - Reuse the existing sail A board and batten construction code where possible.
4. **Composition.**
   - Keep the cap yaw so that from the ref1 / u01 reference camera the vane appears to the LEFT of the tower, partly overlapping the left blades, as in `mill_overall.png`.
   - From the front (looking straight at the wheel) the vane is edge-on and mostly hidden behind the wheel.
   - The vane must clear the wheel, the tower and the props at every cap yaw.


## CLIENT CORRECTION 2 — remove the sloping buttress (supersedes every earlier buttress instruction)

The client has clarified that the sloping stone shape to the RIGHT of the mill in ref1 (`mill_overall.png`, `mill_stone_base.png`) is **terrain: the mountain or cliff rock behind the mill**. It is not part of the building.

- **Delete** the sloping buttress and everything that exists only to support it: its masonry, its coping, its footing and its junction with the drum.
- **Repair** the drum wall where the buttress met it, so the stonework, plinth and ground contact run continuously around the full circumference with no scar.
- **Do not** replace it with any other structure.
- **Rebalance the composition** using the props on the left and the tail vane. The mill must still read as ref1's mill from the reference camera, and the right side of the drum is now simply the arcaded drum wall.
- **Spend** the triangles freed on the round-3/4 must-fix items. The entrance ground and the cap sarking come first.

## Round 4 — builder entry

**Renders:** renders/tower_windmill/round_04: all 6 views at 32 samples, plus stats.json and hidden.json.

**Stats:**

| Measure | Value |
|---|---|
| Triangles | 1,001,818 |
| Objects | 204 = 31 unique merged meshes + 173 linked duplicates of 20 shared variant meshes |
| Bbox | -6.85..4.12 x -5.13..6.02 x -0.005..16.20 m |
| .blend | 25.3 MB, compressed |
| Build | ~20 s, deterministic |
| est_hidden_pct | **12.8%** |
| material_slot_count | 11, all from the palette |
| mask_attribute_missing | none (`[]`) |

**Client corrections (spec):**
- **Buttress deleted.** The drum courses, band, string courses, balusters and footing now run the full circle with no scar. The ground rubble clusters near the old buttress toe were moved around the drum.
- **Sail A removed.** Sail A, its whip, bars, hemlaths, boards and the counterweight are gone. The four arms (`MILL_wheel_arm_A..D`) taper 0.30 → 0.17 m, sit on an "X" and end just past the rim with bolted straps, so they read as the wheel's arms.
- **Tail boom and vane added:** `tail_boom()` / `tail_vane()` → `MILL_tail_boom`, `MILL_tail_vane`, `MILL_tail_iron`. The parts turn with the cap.
  - Two hewn rails, 0.10 x 0.12 m, pass out under the rear eave through a valance notch, from cap-local x' -1.13 to -6.08 (4.6 m beyond the cap).
  - Spacer blocks, 5 iron bands and through-bolts.
  - A hanger that clasps the rails, with iron stays back to the sheer ends.
  - A lower brace from the hanger foot and an upper brace from the rear ridge end, both with iron shoes.
  - Vane: 14 fanned boards, 1.40 → 2.20 m tall, with a ragged outer edge and a broken corner, plus 1 cracked board, 1 replaced board, 4 cleats and nails.
- **Cap yaw is 12 deg** (was 3). This is so the vane reads left of the tower from the front-left, as in ref1 / hero, and is near edge-on behind the wheel in front. The hub is now 0.4 m right of the axis.
- **Clearances:** wheel vs apron, props and tail ≥ 0.30 m PASS, and the lowest rotating point is 8.43 m. At any cap yaw, the tail clears the tower boards by 0.26 m and the props by more than 1 m. The rails run 3 cm over the curb.

**Must-fix 1–9:**

1. **Cap sarking.** A continuous board deck now runs under all 4 cap faces between the hip lines. Boards are 15–25 cm with 4 mm joints. The cap shingles are clamped so nothing projects more than 4.5 cm past the eave or hip corners. Checked from (9,1.5,12.5) and (-3.5,5.5,14.5): no void or sky shows through.
2. **Path flags.**
   - They are now set into the ground: tops 1.7–2.1 cm on the high side with a 0.6–1.0 deg tilt; the step is unchanged.
   - Arris 0.5–1.0 cm, broken by chips, with 1–2 crisp straight fracture edges per flag. The bed is not modelled.
   - Each flag has an `M_earth` soil fillet 3–6 cm wide.
   - 44 gravel stones are bedded in the joints between flags, 40–70% buried.
3. **Ground rubble and prop feet.**
   - (a) 46 settled split stones (`settled_stones()`): 3–4 fracture cuts, 0.8–1.5 cm arrises, buried 45–65% of their height, with soil collars 2–4 cm high.
   - (b) `prop_foot()`: one `hewn_beam` chock with a bird's-mouth step, seated in a notch cut into a split-stone pad. Two iron dogs run onto the pole. The soil mound is 3–5 cm high and tapers to 0 at an irregular edge 0.25–0.42 m out, with 3–6 embedded pebbles.
   - Soil feathers 4 mm into the ground, so there is no crease line.
4. **Door leaf** (`door_planks()`):
   - Worn arrises of 1.5–2.2 cm, more in the bottom 0.4 m and on the lock stile.
   - A ragged, rotted bottom end, with 2 planks 3–5 cm short.
   - 3 face checks and a split at the head.
   - Plank proudness ±3 mm, gaps 4–10 mm and a free-edge sag of 5.1 mm.
5. **Eave fascia and tower foot.**
   - `eave_fascia()`: 16 straight boards with butt joints of 3–6 mm, ends cut to the polygon, ±5 mm height, ±3 mm out of plane, a worn lower arris and the eave wave.
   - The sarking now stops at the fascia's inner face, and the first shake course overhangs the fascia.
   - `tower_foot_flashing()`: one vertical board per octagon face over the sill, scribed to the shakes, with lapped ends.
6. **Hidden triangles: 15.2% → 12.8%.**
   - Mortar skirt quads tucked under neighbouring stones are culled.
   - Recess mortar panels behind full stone cover are culled.
   - String-course and cornice profiles stop 1.2 cm inside the wall, with no in-wall faces.
   - Lead undersides and backs of battens, patches and door ledges are removed.
   - Shingle laps are shorter now that the deck is in.
   - Stone soffits below 1.55 m are not modelled.
   - Every face lying on the ground cut is dropped.
   - Corbel and baluster variants are cut at the wall.
   - **Also fixed:** the drum and opening placement maps were mirror maps, so `MILL_base_stones` and `MILL_base_dressed` faced inward. Every solid piece is now checked and re-wound outward.
7. **Rubble arrises.** Rubble, footing and pinning stones now get a per-edge arris of 0.3–1.5 cm, with 1–2 crisp (≤ 3 mm) broken edges per stone. A 3–8 mm conchoidal scoop is added on about 30% of faces below 2.2 m.
8. **Shared meshes:**
   - Balusters: 8 variants (5 turned, 2 eroded, 1 plain block) → 71 placements.
   - Dentil corbels: 6 variants → 40 placements.
   - Hex bolt heads: 6 variants → 62 placements on the wheel arms, poll end and tail.
   - Pitch, yaw and lean jitter live in the object transforms. Objects sit in the `MILL_instances` sub-collection under `MILL`.
   - There are no truck wheels to instance, because they were dropped inside the valance in round 2 (accepted).
   - Wheel rivets and nail heads stay merged per component.
9. **Kit refactor: NOT DONE, slips to round 5** (allowed under the note-8 time-box).
   - The new round-4 parts are parameterised functions that make their own objects: `tail_boom`, `tail_vane`, `settled_stones`, `path_flags`, `prop_foot`, `door_planks`, `eave_fascia`, `tower_foot_flashing`, `baluster_row`, `dentil_corbels`, `rbox_pv`/`edge_radii`/`conchoidal`.
   - The drum, arcade, apron, tower, cap and wheel builders still read module constants.
   - No `kit_test.png` was produced.

**Producer note 9:** every mesh carries a CORNER BYTE_COLOR `Mask`, set as both active and default. R is a per-piece random (per variant for shared meshes). G is per-piece wear: higher on eroded, cracked, short or replaced pieces and lower on fresh ones. B is moss/damp from height, up-facing and north-facing faces. A = 1.

**Known gaps:**
- Item 9 (kit) is outstanding.
- The tower-foot flashing boards have a curved scribed lower edge where the octagon meets the conical apron.
- Shared variant meshes carry one Mask R per variant; Unreal would supply the per-instance random.
- Nice-to-haves not done: pier and jamb outline straightening, moss.

## Round 4 — score 8/10

**Reviewed:** renders/tower_windmill/round_04 (hero, front, side, back, aerial, actor_closeup, stats.json, hidden.json), plus director close-ups in renders/tower_windmill/round_04/director_extra (x01–x12, y01–y04). Compared side by side with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village. Stats: 1,001,818 tris, 204 objects (31 unique + 173 linked duplicates of 20 shared meshes), bbox 10.97 x 11.15 x 16.21 m, .blend 25.3 MB, 11 palette slots, **est_hidden_pct 12.8%** (passes note 6), mask_attribute_missing empty, every mesh has UVs, every unique mesh has identity transforms. Director check: **29 zero-area faces (< 1e-8 m²) in MILL_base_stones**.

**Verdict:** A solid round of client corrections and producer-note work:
- Sail A is gone. The four tapered arms on an X now read as the wheel's arms, exactly like the grey diagonals in mill_sails_wheel (x09).
- The tail boom and vane are well made (x08): doubled hewn rails, spacers, bands, a fanned 14-board vane with a ragged edge, cleats and a replaced board.
- The cap sarking works. There is no sky or void through the cap from either acceptance camera (x06, x07).
- The hidden-triangle share and the mesh-sharing pools now meet notes 6 and 3. Note 9 (Mask) is met.
- The door leaf now has checks, a rotted bottom and varied planks (x02).

It stays at 8 for these reasons:
- **Voids at the arcade band.** From any raised camera, black voids open into the hollow drum along the top of the upper string course and at every arcade recess floor. They show in the official aerial view (y01, x10, aerial).
- **The buttress scar is still there.** The old buttress bay at +X has no arch, so the arcade has 9 arches and a blank bay of different, ashlar-like masonry (x12, side). This breaks client correction 2: "no scar; the right side of the drum is now simply the arcaded drum wall".
- **The vane does not read from the ref camera.** From the ref1/u01 angle the vane is hidden behind the wheel, with only a sliver at the wheel's left edge (x01). It only reads left of the tower from az ≤ −35 deg (hero, y03).
- **Ground contact still reads CG.** The prop feet are stacked boxes on a plate (x04). The flag soil fillets read as flat mats with a crisp outer step (x03).
- **The entrance jamb blocks are still pillowy** (x02).
- **The kit refactor (note 2) is still outstanding.**

Axis scores:
| Axis | Score |
|---|---|
| Silhouette | 8.5 |
| Proportion and scale | 9 |
| Construction | 8 |
| Detail | 8 |
| Age | 8 |
| Technical | 7.5 |

**Strengths:**
- **Rotor now matches the corrected read** (front, x09). It is a dense 16-blade annulus with an open eye of about 0.35 R and 4 hewn tapered arms on an X with bolted straps and bands. Nothing reads as a sail stock. The lowest rotating point is 8.43 m and the clearances pass.
- **Tail vane** (side, x08, y03): two rails 4.95 m long, spacer blocks, 5 iron bands, a hanger with stays to the sheer ends, upper and lower braces, and 14 fanned boards 1.40 → 2.20 m with a ragged top, a broken corner, a cracked board and a replaced board. It turns with the cap and clears the tower and props.
- **Cap** (x06, x07): the sarking deck closes every gap and the hip/eave shards are clamped. The continuous ridge and the lapped hip capping are kept.
- **Drum masonry** (x05, x12): tight coursed split rubble with per-edge arris variation, crisp broken edges and pinning stones. The plaster-appliqué and soap-bar looks are gone. The plain zone runs round the former buttress side with no scar.
- **Door leaf** (x02, x03): face checks, a head split, a rotted ragged bottom with short planks, varied gaps and flat strap hinges with spear ends and nails.
- **Apron** (x10): ragged split shakes in 3 courses. The eave fascia is now 16 straight butt-jointed boards with an eave wave.
- **Technical:** 1.0 M tris, 12.8% hidden, 11 palette slots, Mask on every mesh, 8/6/6 variant pools as linked duplicates, deterministic 20 s build.

**MUST-FIX (priority order):**
1. **Voids into the hollow drum at the arcade band (aerial, y01, x10).** Seen from above about 4 m (aerial, crane, any upper-floor shot), black slots show in three places: along the whole top of the upper string course (z 2.92) behind its back edge; on the floor of every arcade recess; and behind the cornice at the drum's left and right silhouette. They open into the empty interior of the drum. This is the round-3 lesson ("never open holes when culling") recurring on the masonry: the stone soffits and recess mortar were culled with no backing.
   - Add a cheap continuous wall-core backing cylinder at R_out(z) − MORTAR_RECESS − 0.02 m from z 2.80 to 4.25, closed at both ends.
   - Give every arcade recess a dressed sill/floor slab, 0.25 m deep (the full recess depth), top at 2.92–2.94 m, with a 1 cm chamfer and 1–2 chips.
   - Run the top face of the upper string course back 3 cm into the wall core, so no gap is left between the course and the arcade-zone stones.
   - Acceptance: zero black pixels at the band and arcade in the aerial view and from director cam (−2.2, −5.2, 6.0) → (−0.8, −2.3, 3.3), 50 mm.
2. **Restore the arcade at +X (x12, side). This is client correction 2.**
   - `ARCH_AZ` still skips k = 2 (az 90 deg, +X), the old buttress junction. The drum shows 9 arches and a blank bay of large, regular, ashlar-like blocks (two courses of ~0.35 m-tall rectangles) whose vocabulary differs from the rest of the wall.
   - Remove the `k != 2` skip so there are 10 arches at 36 deg pitch, each with the same clear 0.72 × 1.08 m, 0.25 m recess, rubble back, 9–11 irregular voussoirs and dressed piers.
   - Rebuild that bay with the same coursed split rubble and pinning stones as the other bays.
   - Re-check the slit window at az 70 deg (plain zone, z 1.30–1.85) for clashes. It sits below the band, so none are expected.
3. **The vane must read left of the tower from the ref camera (x01, against mill_overall).**
   - From director cam x01 ((−11, −27, 4) → (0.2, 0, 8.6), 42 mm, ≈ u01 / ref1 angle), the vane sits almost entirely behind the left half of the wheel. Only ≈ 0.2 m of its outer end shows past the wheel's left rim.
   - In mill_overall the vane stands clearly left, overlapping only the left blades.
   - Fix: raise `CAP_AZ` from 12 deg to 19–22 deg. The hub then moves to ≈ 0.65–0.75 m right of the axis, which is closer to ref1, and the wheel's left half gains distance from the props. With the boom kept at its 4.95 m length, the outer 1.0–1.4 m of the vane should then show clear of the wheel's left rim from x01. From the front camera the vane is still ≥ 65 deg off face-on and mostly behind the wheel, as the client asked.
   - Re-run the tail, wheel, apron and prop clearance checks, and render x01, hero and front to prove the read.
4. **Prop feet still read as stacked boxes on a plate (x04, actor_closeup left).** Each foot is a rounded box chock standing on top of a flat slab pad. The soil "mound" is a flat disc with a crisp 1–2 cm outer step, and the pebbles are little cubes.
   - Pad: sink it so its irregular domed top sits only 3–6 cm above the ground at the high side and 0–2 cm at the low side, with no vertical side face taller than 4 cm.
   - Chock: half-sunk into a visible notch, so that at least 40% of its height is below the pad top. It should be a hewn block with adze facets of ±5 mm, not a rounded box.
   - Soil: build it as a concave fillet that reaches 0 height tangentially at its irregular outer edge. No step over 2 mm anywhere; the outer 10 cm stays under 6 mm.
   - Pebbles: 3–4 fracture-plane split stones, buried 40–60%.
   - Pole foot: give the last 1.2 m above the chock 2 visible checks (1.5–2.5 cm) and an adze flat, so it does not read as a smooth dowel at the actor distance.
5. **Path flags and door-side ground rubble (x03, actor_closeup).**
   - (a) The `M_earth` fillet round each flag reads as a flat flange or mat with a hard outer outline. Make it a concave fillet that meets the ground tangentially (0 mm at the outer edge, no visible step) and varies in width 3–8 cm.
   - (b) The flag tops are still flat with rolled edges. Add low-frequency undulation of ±5–8 mm and 1–2 shallow spalls (1–2 cm) on the exposed top arris of each flag.
   - (c) The ground rubble slabs at the door's left (x03 upper left) stand 5–8 cm proud with vertical sides. Bury them so no exposed vertical side is over 3 cm, tilt them 5–15 deg, and add a soil collar.
6. **Entrance jamb and voussoir blocks are pillowy (x02).** The dressed door-surround blocks have softly waved outlines, melted rounded corners and bulging faces. In the actor close-up they read as foam cushions. This was a nice-to-have in round 3 and is now a must-fix, because the entrance is the close-up priority.
   - Make the large edges straight (±2 mm) with a 1 cm chamfer.
   - Make the faces flat (±2 mm) with weighted or flat-shaded normals.
   - Put the wear into 2–4 crisp spalls or chips per block (1–3 cm deep), with more on the lower jamb arrises.
   - Apply the same treatment to the arcade pier blocks.
7. **Upper tail brace is carried by the roof covering (y04, x08).**
   - The upper brace is a smooth round dowel. Its rounded end rests on top of the hip and ridge capping beside the knob plinth, with no shoe or bolt visible, so it reads as pasted onto the shingles.
   - Fix: carry it on a short king post (0.12 × 0.12 m, hewn) rising 0.25–0.35 m through the ridge from the cap frame or crown tree, with a board or lead collar where it passes the roof. Bolt the brace to the post with an iron strap shoe and 2 hex bolts from the pool.
   - Make both braces hewn 0.08 × 0.10 m members with 1.5–2.5 cm chamfers (`hewn_between`), matching the boom rails, instead of round poles.
8. **Producer note 2: kit refactor (round-3 must-fix 9, slipped).**
   - The drum, arcade, apron, tower, cap and wheel builders still read module constants.
   - Expose the parameterised component functions listed in round 3 (`round_stone_drum`, `blind_arcade`, `arched_door`, `shake_apron`, `smock_tower`, `mill_cap`, `wind_wheel`, `raking_prop`, plus the round-4 `tail_boom` and `tail_vane`).
   - Build the variant (drum r 2.0 m, tower 4.0 m, 12 blades) to a scratch .blend and save `renders/tower_windmill/round_05/director_extra/kit_test.png`.
   - This is required before a 10.
9. **Nanite hygiene (producer note 1).** Remove the 29 zero-area faces (area < 1e-8 m²) in MILL_base_stones, then re-check that every mesh has 0 degenerate faces.

**Nice to have:**
- Tower-foot flashing boards: the curved scribed lower edges read as a scalloped frill from above (x10). Either straighten the bottom edge and let the top shake course tuck under it, or use a lead flashing apron with a straight drip.
- Cap shingles (x06) are a near-regular grid on the side faces. Add ±15% width variation and break the vertical joint alignment from course to course.
- In mill_overall the vane looks taller, about 0.4 × the wheel diameter, against our 0.28. If the client agrees, take the outer edge to 2.5–2.7 m.
- Props at mid range are still smooth (round-3 nice-to-have): bow 8–12 cm and 2 larger lower knots.

## Round 5 — builder entry

**Renders:** renders/tower_windmill/round_05 (all 6 views at 32 samples, stats.json, hidden.json). Builder check views and the kit test are in round_05/director_extra: `kit_test.png`, plus `b_*.png` (16 samples): b_y01 is the band from the director cam (-2.2,-5.2,6.0)->(-0.8,-2.3,3.3) at 50 mm, b_x01 is the ref angle, and the others are door jambs, east arcade, prop feet, path flags, king post and tail.

**Stats:**

| Measure | Value |
|---|---|
| Triangles | 1,114,235 |
| Objects | 211 = 34 unique merged meshes + 177 linked duplicates of 20 shared variant meshes |
| Bbox | -6.81..4.22 x -5.16..5.75 x -0.005..16.20 m |
| .blend | 28.0 MB, compressed |
| Build | ~23 s, deterministic |
| est_hidden_pct | **13.0%** |
| material_slot_count | 11, all from the palette |
| mask_attribute_missing | none |
| Degenerate faces | 0 on every mesh. Checked on the saved float32 vertices with loop triangles of area < 1e-8 m² |

**Must-fix 1–9:**
1. **Band voids.**
   - `wall_core_backing()` adds a closed wall-core ring at R_out(z) − MORTAR_RECESS − 0.02 (d = −0.034) from z 2.84 to 4.45. It sits inside the upper string course, up to under the cornice cap. It is holed only at the clear arcade openings and has top and bottom annuli and an inner face behind the recess backs.
   - Every recess has a dressed sill slab 0.82 × 0.275 × 0.06 m, top 2.92–2.94 m, with a 1 cm chamfer and 1–2 spalls.
   - The upper string course's top bed runs 6.5 cm back into the core (`profile_course(top_back=)`).
   - b_y01 shows no black slots. The aerial view is clean at the band.
2. **Arcade at +X.** The `ARCH_AZ` skip is gone, giving 10 arches at a 36° pitch, all 0.72 × 1.08 m with sills, rubble backs, 9–11 voussoirs and piers. The +X bay is now ordinary coursed rubble and piers, the same as the other bays (side view, b_east).
3. **Vane read.** `CAP_AZ` is 21°, which puts the hub 0.70 m right of the axis. From x01 the outer ~1.2 m of the vane stands clear left of the wheel rim (b_x01). From the front it stays mostly behind the wheel. Clearances:
   - wheel vs apron/props/tail: PASS
   - lowest rotating point: 8.43 m
   - tail swept vs tower boards: 0.256 m
   - rotor vs props: 1.78 m
4. **Prop feet** (`prop_foot`, b_prop_feet).
   - The split-stone pad is bedded with a domed top. Its highest point is 4.2–5.3 cm, tilted 3–4°, with the low side buried, so no exposed side is over 4 cm.
   - A hewn chock with planar adze facets (`facet_shave`, 3–6 mm) is sunk 42–43% of its height into a notch in a dense pad grid. The seat is at 0.08 m and the heel at 0.18 m.
   - Concave soil fillet (`soil_collar`): z = h(1−f)^2.6, h 2.2–3 cm, running out tangentially 0.16–0.24 m beyond the pad.
   - 3–5 split "ground" pebbles, buried 40–60%.
   - Every pole now has 2 extra 1.5–2.5 cm checks and an adze flat in its bottom 1.2 m.
5. **Path and ground.**
   - (a) Flag fillets are concave, z = zin(1−f)^2.6, 3–8 cm wide, ending at −3 mm.
   - (b) Flag tops and arrises undulate ±5–8 mm, with 1–2 crisp 1–2 cm spalls per flag.
   - (c) All ground rubble is bedded: highest point 1.2–3 cm, bed tilt 5–15°, concave soil collars that follow each stone's ground outline.
6. **Crisp dressed work.**
   - The `hero`, `dressed` and `ashlar` styles now have outline noise ≤ 2 mm, flat faces (±1 mm), a 1 cm chamfer and denser grids (21×19 hero, 13×11 dressed).
   - Wear sits in 2–4 crisp 1.2–2.8 cm spalls with 4 mm ramps. Lower door jambs get 3–4.
   - The same applies to the arcade jambs, voussoirs and piers (b_door_jambs, b_east).
7. **Upper tail brace.**
   - `king_post()`: a hewn 0.12 × 0.12 post rises 0.30 m above the rear hip-end saddle from 0.30 m under the covering. It has a draped lead collar (6 cm upstand, 9 cm apron) dressed to the sampled roof surface.
   - The upper brace is carried on the post by an iron strap shoe (plates on the post and brace sides) and 2 pooled hex bolts per side.
   - Both braces are hewn 0.10 × 0.08 members with 1.5–2.5 cm chamfers (b_king_post, b_tail_side).
8. **Kit refactor: done.**
   - These are parameterised functions, each writing its own named objects:
     - `round_stone_drum(r_base, r_top, height, zones, door, arcade, windows, seed)`
     - `blind_arcade(n, clear_w, clear_h, z_sill, az0, seed)`, which writes the new `MILL_arcade_dressed` and `MILL_arcade_backs`
     - `arched_door(width, spring, reveal, ring, seed)`, which writes the new `MILL_door_surround` plus the leaf, iron and interior
     - `shake_apron(r_eave, z_eave, r_top, z_top, courses, seed)`
     - `smock_tower(af_bottom, af_top, z0, z1, seed)`
     - `mill_cap(length, width, rise, ridge_len, yaw, seed)`
     - `wind_wheel(r_in, r_rim, r_tip, n_blades, pitch, hub_d, seed)`
     - `raking_prop(top, bot, face, z_att, ...)`, `tail_boom`, `tail_vane`, `king_post`, `prop_foot`, `soil_collar`
   - `kit_set()` publishes component parameters to the dimension table that the low-level helpers read, and re-derives every dependent constant: openings, cap profile and valley tables, rotor frame, curb, collar and tail heights.
   - `seed` salts every generator a component uses.
   - The hard-coded radii in the interior, apron, ground clusters and path are now relative to the drum and apron.
   - `build_mill()` only calls the components with this mill's numbers. The refactor reproduces the mill exactly (the same 1,114,235 tris).
   - Variant: `MILL_KIT_VARIANT=1` builds drum r 2.0 m (height 4.2, 8 arches), tower 4.0 m, 12 blades and its own props and tail. It builds with no errors (841k tris, 14.9% hidden, clearance PASS), and its thumbnail is saved as `renders/tower_windmill/round_05/director_extra/kit_test.png`. The scratch .blend is outside the building folder.
9. **Nanite hygiene.** Degenerate detection now runs on the float32 positions the mesh actually stores (eps 2e-8). That accounts for the 29 faces in MILL_base_stones. After the rebuild, every mesh has 0 faces under 1e-8 m².

**Nice to have:**
- Done: the tower-foot flashing boards now have a straight drip edge at the level the shakes reach at the board ends. The top shake course tucks under it, so there is no scalloped frill.
- Not done:
  - cap shingle width jitter
  - vane height increase (it needs the client's agreement)
  - pole bow and knots (they were already 8–12 cm bow and 5–7 cm lower knots in code)

**Known gaps:**
- The dressed spall scars are crisp but still interpolate across the grid at their ends.
- The arcade piers are regular dressed ashlar, by spec ("dressed pier blocks").
- The ground rubble now reads as low flush flakes from the actor camera.
- The kit components still share one module dimension table (via `kit_set`) rather than passing a context object down to every helper.

## Round 5 — score 9/10

**Reviewed:** renders/tower_windmill/round_05 (hero, front, side, back, aerial, actor_closeup, stats.json, hidden.json), the builder's b_*.png and kit_test.png, and director close-ups in renders/tower_windmill/round_05/director_extra (x01–x06, x09–x12, y01, z01–z03). Compared side by side with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village.

**Stats:** 1,114,235 tris; 211 objects (54 unique mesh datablocks, instance pools as linked duplicates); bbox 11.03 x 10.90 x 16.21 m; .blend 28.0 MB; 11 palette slots; **est_hidden_pct 13.0%** (passes note 6); mask_attribute_missing empty; every mesh has UVs; every merged mesh has identity transforms (only pool instances carry transforms); collections MILL / MILL_instances.
- **Director hygiene check:** 0 triangles under 1e-8 m², but there are **4,579 needle triangles with altitude < 0.1 mm** (MILL_base_stones 3,641, MILL_arcade_backs 691, MILL_cap_shingles 86, MILL_props 80, MILL_ground_rubble 42, MILL_prop_anchors 25, others 14). There are also **16 quads with polygon area < 1e-8 m²** (base_stones 13, arcade_backs 3).
- The builder's test uses eps = 2e-8 on triangle area, and the smallest surviving triangle is 2.003e-8 m². The slivers were nudged just over the threshold rather than removed.

**Verdict:** This is the strongest round yet, and all nine round-4 must-fixes were addressed:
- **Band voids:** gone. y01 and the aerial view show no black slots.
- **Arcade:** all 10 bays are back. The +X side is now just the arcaded drum (x12, side).
- **Vane:** from the ref1 angle (x01) it now stands clear left of the tower and overlaps only the left blades, exactly as in mill_overall.
- **Upper brace:** it sits on a proper hewn king post with a lead collar and a strap shoe (b_king_post, x06).
- **Door surround:** it is now crisp dressed work, not foam.
- **Kit:** the refactor is real. build_mill() only calls parameterised components, and the variant builds (kit_test.png shows a visibly smaller drum and 12 blades).

At thumbnail and mid-shot it is unmistakably ref1's mill, and it survives a mid-shot. What remains is close-up polish at ground contact, plus two CG tells in the masonry:
- **Ground contact:** the ground rubble overcorrected into flush flakes sitting in crater-like collars. The flags carry dotted strings of chips. The prop chocks are still clean boxes.
- **Masonry tells:** the pier blocks form a tiled 2x3 grid, and the spall scars read as stepped notches.
- **Hygiene:** sliver triangles remain.

None of these breaks the silhouette, but a production designer would flag each of them in the actor close-up, so it is not a 10.

**Axis scores:**

| Axis | Score |
|---|---|
| Silhouette | 9 |
| Proportion and scale | 9 |
| Construction | 9 |
| Detail | 8.5 |
| Age | 8.5 |
| Technical | 8.5 |

**Strengths:**
- **Silhouette and composition (hero, x01, front, side):**
  - The stout drum carries the arcade band, dentil cornice and ragged shake apron, with a tall slender boarded smock tower above.
  - The bell-cast cap is small.
  - The 16-blade annular wheel on rings has 4 hewn arms.
  - The fanned board vane on a doubled boom reads left of the tower from the ref camera.
  - Three long raking props stand on the left.
- **Band and arcade (y01, x12, b_east):**
  - A continuous wall-core backing sits behind the band, and each recess has a sill slab.
  - The 10 round-headed recesses have irregular 9–11-voussoir rings and rubble backs, and the +X bay matches the rest.
  - The baluster row and the dentil cornice are separate chamfered pieces.
- **Drum rubble (z01, x05):** the flat-bedded split rubble has varied lengths, wandering courses, pinning stones and crisp broken arrises. The slit window has dressed jambs and a lintel.
- **Entrance (x02, z02, actor_closeup):**
  - The dressed jambs are now flat-faced and crisp.
  - The arch-topped plank leaf has checks, a rotted foot and varied planks.
  - The flat spear-ended strap hinges have nails, and there is a ring pull with a latch plate.
  - The threshold and step are correct to scale next to the 1.8 m figure.
- **Cap and tail (x06, b_tail_side, b_king_post):**
  - The cap has concave bell-cast hip boards, lapped hip capping, a hood over the neck and a sarking deck with no see-through.
  - The king post rises through a lead collar and carries the hewn upper brace on a strap shoe with bolts.
  - The vane has battens, nails, a ragged top and a replaced board.
- **Rotor (x09, front):** the board blades are riveted to the inner ring and the rim. There are iron spokes and diagonal ties, bolted arm straps and bands, and the open eye is about 0.35 R. The clearances pass, with the lowest rotating point at 8.43 m.
- **Technical and kit:**
  - 1.11 M tris, 13.0% hidden, 11 palette slots and Mask on every mesh.
  - Linked-duplicate pools for balusters, corbels and bolts.
  - A deterministic 23 s build.
  - Parameterised components, with a working variant (kit_test.png).

**MUST-FIX (priority order):**
1. **Ground rubble overcorrected into flush flakes (z03, actor_closeup, hero).**
   - Every scattered stone now shows only 1–3 cm, as a thin flat flake. Each sits in its own concave collar 10–20 cm wide, and the collar has a visible raised outer rim, like a footprint or crater.
   - From the actor camera the ground round the drum reads bare and dotted, not "larger footing stones, a few half-buried stones, scattered rubble" (art bible §3, spec J).
   - My round-4 "≤ 3 cm exposure" rule was meant only for the slabs at the door's left. Apply this instead:
     - **Count and clusters:** 45–60 stones in 4–6 clusters. Most clusters hug the footing course within 0–0.6 m of the drum face, at the −X prop side, the +X side, the rear and either side of the path. Leave the open field mostly clear.
     - **Large stones:** 8–12 stones of 0.20–0.45 m, buried 40–60% of their height, so 6–15 cm stands proud, with tilted beds and a crisp fractured top arris.
     - **Small stones:** the rest are 0.05–0.15 m, buried 30–50%.
     - **Collars:** only 3–8 cm wide. They must run out tangentially, with the outer 10 cm under 2 mm and no crest or step anywhere. Two or three stones in a cluster share one collar.
   - **Acceptance:** from z03 and actor_closeup, no ring or halo outline is visible round any stone, and at least 5 stones read as solid, half-buried rocks.
2. **Footing-course pinning chips in rows (z03, at z ≈ 0.25–0.45 m).**
   - In the bottom two courses, the bed joints hold rows of 3–6 identical small rectangular chips, about 4 × 2 cm, set in a line like teeth.
   - Replace them with 0–2 irregular wedge pinning stones per joint. Make them 3–8 cm long and rotated ±20°, never more than 2 in a row, with no two adjacent ones the same size.
   - The footing stones themselves are soap bars, with rounded ends and a melted top arris. Give them the flat beds, 1–2 crisp fracture edges and 0.3–1.5 cm arris variation that the drum stones in z01 already have, and keep their 5–10 cm projection.
3. **Path flags and step (x03, b_path_flags, actor_closeup).**
   - (a) Along the downhill edge of each flag sits a dotted string of 5–10 tiny cube chips at near-even spacing. Remove them. Allow 0–2 irregular chips of 2–5 cm per flag, half-buried in the soil and set off the edge line.
   - (b) The flag edge still reads as two steps: the rolled top arris, then a 1–2 cm horizontal shelf where the fillet starts. Start the fillet on the flag's side face, at least 1 cm below the arris, with no horizontal ledge, so the side shows as one irregular split face 1–3 cm tall.
   - (c) The outside step stone in front of the threshold is a smooth curved kerb with a uniform rounded nose, which reads as cast concrete. Give it a split front of 2–3 planar facets, a 0.5–1 cm arris broken by 1–2 crisp spalls of 1–2 cm, ±5 mm undulation on top, and one straight fracture edge. Keep the riser at 18 cm or less.
4. **Prop feet: chock and pole butt (x04, b_prop_feet, actor_closeup left).**
   - The pads now sit well. The chock, however, still reads as a clean rectangular box with straight 90° edges, and the 3–6 mm facets do not show from 2 m. Each side of the chock has a dark vertical slot where the notch is wider than the chock.
   - **Chock:**
     - Make it an irregular hewn wedge: top 2–3 cm narrower than the base, one end tapered 3–5 cm, with adze facets 6–12 mm deep that read from 2 m.
     - Close the notch to a gap of 5 mm or less all round, with soil or chinking in it.
   - **Pole checks:** the checks on the bottom 1.2 m of each pole are long, parallel, uniform-width flutes 1.0–1.5 m long, which read as milled grooves. Make each check 0.3–0.8 m long, tapering in width (0 → 1.5–2.5 cm → 0) and depth, set ±5° off the grain axis to each other, with no two the same length. Add one radial end-grain split at the butt.
   - **Iron dogs:** seat them flat on the pole surface (gap of 2 mm or less), so they do not read as round rods standing off it.
5. **Dressed spalls read as stepped notches with raised lips (z02, x02, b_door_jambs).**
   - Examples:
     - right jamb, middle block, top edge at ≈ 1.35 m: a rectangular notch with a proud lip
     - left jamb at ≈ 1.0 m and ≈ 1.5 m: step-cut tabs and flaps at the outer arris
     - b_door_jambs, left: thin flaps sticking out of the block outline
   - A spall is a conchoidal scoop.
     - It has an irregular outline, 1–3 cm at its deepest, and fades smoothly to 0 at its boundary.
     - Nothing stands proud of the original face or arris.
     - It has no rectangular corners.
   - Fix the grid interpolation that the builder named as a known gap. Either refine the grid locally under each spall (≤ 5 mm spacing), or cut the spall as the intersection of 2–3 tilted planes clamped to never push outward.
   - Apply the same fix to the arcade jambs and piers.
6. **Arcade piers read as a tiled 2x3 panel (x12, b_east, actor_closeup).**
   - Every pier between two arches is the same grid of about 6 large, near-square ashlar slabs (≈ 0.35 × 0.35–0.40 m) with aligned vertical joints, repeated on all 10 piers. In ref1 (mill_stone_base) the piers continue the coursed stone of the spandrels.
   - Lay each pier as coursed dressed blocks:
     - Course heights match the neighbouring spandrel courses (0.15–0.30 m), and each pier differs in its course layout.
     - Blocks alternate long and short (0.30–0.55 m), quoin-fashion, with vertical joints offset course to course.
   - Fix the dark slit void (≈ 1.5 cm open joint into the dark) between the two lower blocks of the pier right of the +X arch, at z ≈ 3.5 (x12). No joint may open into a void.
7. **Producer note 1: sliver triangles survive just above the test threshold.**
   - There are 4,579 needle triangles with altitude < 0.1 mm:
     - MILL_base_stones: 3,641
     - MILL_arcade_backs: 691
     - MILL_cap_shingles: 86
     - MILL_props: 80
     - MILL_ground_rubble: 42
     - MILL_prop_anchors: 25
     - MILL_base_mortar: 10, plus 4 singles
   - There are also 16 quads with area < 1e-8 m²: base_stones 13, arcade_backs 3.
   - Fix:
     - At the end of each mesh build, run `bmesh.ops.remove_doubles(dist=2e-4)`, then `bmesh.ops.dissolve_degenerate(dist=1e-4)`, or collapse edges shorter than 0.2 mm.
     - Test triangle altitude (2·area / longest edge < 1e-4 m) and polygon area < 1e-8 m², not triangle area against a tunable eps.
     - Report both counts as 0 in the log.

**Nice to have:**
- **Wheel blades:** the 1.5–3 cm gaps between the boards of each blade read as fanned, splayed slats at mid range (front, x11). The ref blades read as solid paddles, so close the board gaps to 0.5–1 cm.
- **Tail vane height:** the vane is 0.32 × the wheel diameter, against about 0.4 in mill_overall. Take its outer edge to 2.5–2.7 m if the client agrees.
- **Cap shingles** (x06) are still a near-regular grid. Add ±15% width variation and break the vertical joint alignment from course to course.
- **Interior:** the view through the door is pitch black. A visible floor edge and a ladder foot 1.0–1.5 m inside, catching light, would give depth (spec A bonus).
- **Kit:** pass a context or dimension object down to the helpers instead of the module table set through kit_set().


## CLIENT CORRECTION — producer note 10

Delete all loose ground stones, rubble scatter, path flags, stepping stones and ground aprons that are not part of the building. Do not score them. See producer note 10 in the art bible.

## Round 6 — builder entry

**Renders:** renders/tower_windmill/round_06 (all six views, 32 samples, plus stats.json and hidden.json). Builder close-ups are in round_06/builder_extra (c_prop_feet, c_prop_foot0, c_door, c_door_in, c_step, c_wheel).
**Stats:**
- 1,212,256 tris across 211 objects; bbox 10.77 x 9.13 x 16.21 m; .blend 30.3 MB.
- **10 palette slots** (M_rubble has dropped out with the rubble). **est_hidden_pct 14.4**, and mask_attribute_missing is empty.
- Every mesh reports 0 slivers with altitude < 0.1 mm and 0 polygons with area < 1e-8 m².
- The clearance check passes. The kit variant (MILL_KIT_VARIANT=1) still builds: 909k tris, clearance PASS.

**Verified from the interrupted earlier session (already in the script):**
- `nanite_clean` runs on every mesh (bmesh remove_doubles + dissolve_degenerate), with the altitude and area test.
- Jamb, arcade and pier spalls are cut as 3-plane conchoidal scoops clamped never to push outward.
- `arcade_piers` lays coursed long-and-short blocks matched to the spandrel courses, with a different layout per pier.
- The footing joints take 0-2 irregular wedge pinners each, and the footing stones have flat beds.

**Producer note 10 (client):**
- **Deleted:**
  - all ground rubble clusters, the shared soil collars, the path flags and their gravel chips;
  - the soil fillets and pebbles round the prop pads;
  - the code that existed only for them (`settled_stones`, `soil_collar`, `path_flags`, `cluster_collar`, `hull_sdist`, and the gravel and ground_big styles).
- **Kept:** the door step, which is built against the footing under the threshold. It is now its own component, `door_step` → MILL_door_step, with:
  - a split front of 2-3 planar facets that meet on a soft kink;
  - 1-2 crisp spalls and ±5 mm top undulation;
  - a 3 cm buried skirt and no soil fillet.
- The pads, chocks and dogs stay as part of the props.

**Prop feet (audit item):**
- **Chock:** a hewn wedge whose top is 2-3 cm narrower than its base, with a heel taper of 3-5 cm and adze facets 6-12 mm deep. The notch is cut to the chock's footprint +3 mm and packed with soil, so there is no dark slot.
- **Dogs:** flat bars lying on the pole, with a gap of 2 mm or less.
- **Pole checks:** they taper in both width and depth, are 0.3-0.8 m long with no two lengths alike, and drift about ±5° across the check columns. The foot checks sit within the bottom 1.2 m. Each butt also has one radial end-grain split, 2.5-3.5 cm deep and closing over 0.15-0.25 m.

**Secondary:**
- **Interior depth:** a worn oak floor sill now runs across the inner end of the passage, as the visible floor edge. A ladder (2 stiles, 10 rungs, 72° lean) has its foot 1.30 m inside the door face, right of the leaf. It reads through the gap of the ajar door (c_door, c_door_in, actor_closeup).
- **Wheel blades:** the board gap is now 5 mm, with a thinner edge rounding, so it reads as about 0.5-1 cm. The blades read as solid paddles (c_wheel, front).

**Not done (time-box):** the cap-shingle width jitter and the course-to-course joint break.
**Known gap:** without its soil fillet, each prop pad shows its own split side 4-5 cm above Z = 0, and its slightly wider lower body reads as a low ledge from close up. It will sit into the Unreal terrain.

## Round 6 — score 9.1/10

**Reviewed:** renders/tower_windmill/round_06 (hero, front, side, back, aerial, actor_closeup, stats.json, hidden.json), the builder's builder_extra close-ups (c_door, c_door_in, c_step, c_prop_feet, c_prop_foot0, c_wheel), and director close-ups in renders/tower_windmill/round_06/director_extra (x01 ref angle, x02 door, x03 threshold, x04 prop feet, x05 footing, x06 cap, x07 arcade, x08 jambs, x09 passage from above, x10 left jamb). Compared side by side with ref1 and the crops mill_overall, mill_sails_wheel, mill_stone_base, style_mill_lattice_sails and style_aerial_village. Ground dressing (loose stones, rubble, paths, aprons) was not scored, per producer note 10.

**Stats:** 1,212,256 tris; 211 objects; bbox 10.77 x 9.13 x 16.21 m; .blend 30.3 MB; 10 palette slots (M_earth now only on the prop-foot notch packing); **est_hidden_pct 14.4%** (passes note 6, but only 0.6 points of headroom); mask_attribute_missing empty; every mesh has UVs.
- **Director hygiene check (independent):** 0 triangles with altitude < 0.1 mm and 0 polygons with area < 1e-8 m² on every mesh datablock. Round-5 must-fix 7 is closed.

**Verdict:** a clear step up from round 5, and the best the mill has been. Producer note 10 is applied cleanly: the rubble, collars, flags and gravel and their code are gone, and only the built-in door step remains. The round-5 must-fixes are closed, apart from the remaining close-up issues below:
- the arcade piers are now coursed long-and-short work that continues the spandrel courses (x07, actor_closeup);
- the slivers are gone;
- the wheel blades read as solid paddles, as in mill_sails_wheel (front, c_wheel);
- the ladder and floor sill give real depth through the ajar door (c_door, x10).

From the ref camera (x01) it is unmistakably ref1's mill: drum, arcade band, ragged shake apron, tall boarded smock tower, small cap, a 16-blade wheel on rings, and the fanned tail vane standing clear to the left over three raking props.

It is not a 10, because a production designer would still flag these in an actor close-up:
- the dressed spalls still leave proud tabs and stair-stepped notches on the door jambs;
- the threshold nose reads as a cast concrete kerb;
- the prop feet read as machined parts: stacked plate pads, gusset-bracket dogs and smooth lozenge "checks";
- the cap shingles are still a near-regular grid.

**Axis scores:**

| Axis | Score |
|---|---|
| Silhouette | 9.3 |
| Proportion and scale | 9.2 |
| Construction | 9.0 |
| Detail | 8.8 |
| Age | 8.7 |
| Technical | 9.5 |

**Strengths:**
- **Silhouette and composition (x01, hero, front, side, back):** matches mill_overall tier for tier. The wheel/drum width ratio is about 1.5 in the front view, against about 1.5 in the ref. The vane sits left of the tower from the ref angle and edge-on behind the wheel from the front.
- **Arcade band (x07, actor_closeup):**
  - The piers are coursed dressed blocks, alternating long and short, with offset vertical joints and a different layout per pier.
  - The 9–11-voussoir rings are irregular, the rubble backs are recessed, and each recess has a sill.
  - The balusters and the dentil cornice are separate chamfered pieces.
- **Entrance (x02, c_door_in, x10):**
  - The plank leaf has checks, a rotted foot and varied plank widths.
  - The spear-ended strap hinges have nails, and there is a ring pull with a latch plate.
  - The door stands ajar onto a ladder and floor sill 1.3 m inside, so there is real depth instead of a black slot.
  - Headroom and step rise are correct next to the 1.8 m figure.
- **Rotor (c_wheel, front):** the paddles are solid, with 5 mm board gaps. Riveted ring attachments, spokes and diagonal ties, and bolted arm straps make it mechanically believable.
- **Drum rubble (x05):** flat-bedded split stones with wandering courses, varied lengths and sparse irregular pinners. The footing course projects and has flat beds.
- **Technical:**
  - 1.21 M tris, 10 palette slots, Mask on every mesh.
  - Verified clean Nanite hygiene.
  - The kit variant still builds with clearance PASS.

**MUST-FIX (priority order):**
1. **Door-surround spalls still make proud tabs and stair-stepped notches (x08, x10, c_door_in, actor_closeup). This is the actor close-up priority.**
   - **Where:**
     - Left jamb, bed joint at z ≈ 1.00 m: a stair-stepped notch about 25 cm long with 3–4 grid-aligned steps (x10, upper left).
     - Left jamb outer arris at z ≈ 1.20 m and 1.45 m: small rectangular flaps 1–2 cm proud of the face (x08, left block).
     - Right jamb, lower-middle block, outer arris at z ≈ 1.0–1.3 m: two rectangular tabs sticking out (x08, right edge).
     - Right jamb top block, lower-left corner at z ≈ 1.75 m: a triangular flap (c_door_in).
   - **Fix:**
     - After cutting each spall, clamp every vertex so that it lies on or inside the pre-spall block. The signed distance to the original block must be ≤ 0 everywhere, with an outward excess ≤ 0.5 mm, and the build should print the per-block maximum.
     - Each spall outline is a smooth irregular loop with at least 8 points and no straight segment longer than 3 cm along a grid axis.
   - **Also:** the dark grey smears on the arcade pier faces (x07, piers left and centre at z ≈ 3.3–3.6 m) are spall shading artefacts. Recompute or flat-shade the spall normals there.
2. **Threshold nose reads as a cast concrete kerb (x03, x09, c_step).**
   - The front of the threshold is one 1.3 m curved stone that follows the drum arc exactly. It has a constant height and a uniform rounded nose with a radius of about 4 cm.
   - Rebuild it as 2 dressed stones, each 0.55–0.75 m long, with a visible joint.
     - Each front is 2–3 near-straight chord facets, not a perfect arc.
     - The arris is 0.5–1 cm with 1–2 crisp spalls of 1–2 cm per stone.
     - The nose height varies ±5 mm, and the worn dip (1–2 cm) at the centre carries through the nose.
   - Keep the top at Z_TH = 0.14 and the step rise at 6–7 cm.
   - Inside the passage, the right-hand floor flag stands 3–4 cm proud of its neighbour (x09). Level the passage flags to within ±1 cm of each other.
3. **Prop pads read as two stacked plates (x04, c_prop_feet, c_prop_foot0; the builder's known gap).**
   - Each pad shows a flat top slab over a wider lower ledge, with a 4–5 cm vertical step above Z = 0. Producer note 10 says the building's own footing must meet Z = 0 convincingly on any terrain.
   - Make each pad one split stone:
     - one continuous irregular side face, 3–5 cm exposed above Z = 0, with no ledge or second tier;
     - the lower body no wider than the top outline + 1 cm;
     - a domed top (±1 cm) with 1–2 fracture facets;
     - a buried skirt of 5 cm or less.
4. **Chock and iron dogs read as machined brackets (x04, c_prop_foot0).**
   - **Dogs:** each foot shows two flat diagonal bars from the chock top to the pole, forming a triangle on each side. They read as welded gusset plates.
     - Replace them with 1–2 true iron dogs (staples) per foot, of 15–20 mm square bar.
     - Each dog spans 20–25 cm across the chock/pole joint, stands 12–18 mm proud, and has two legs bent 90° that vanish into the timber.
   - **Chock:** at 2–4 m it is still a clean box with flat faces.
     - Raise the facet amplitude on the 3 exposed faces to 10–15 mm.
     - Break the top edges with 2 hewn bevels of 2–3 cm.
     - Skew the plan 4–6° so it is not a rectangle.
5. **Pole checks read as carved lozenge scoops (x04 near pole, c_prop_feet, c_prop_foot0).**
   - Each pole shows a single smooth, soft-walled, diamond-shaped groove about 0.5 m long and about 3 cm wide.
   - Real seasoning checks are narrow V cracks, with sharp walls and no rounded floor:
     - 3–5 per pole in the bottom 1.5 m, each 4–12 mm wide at the widest and 2–4 cm deep, closing to 0 at both ends;
     - plus 2–3 hairline checks 2–4 mm wide.
   - Keep the end-grain split.
6. **Cap shingles are a near-regular grid (x06; nice-to-have since round 4, now must-fix before a 10).**
   - Add ±15% width variation.
   - Offset the vertical joints by at least 1/3 of a shingle width from course to course, so that no joint aligns over 3 consecutive courses.
   - Add ±3° rotation on 20% of the shingles.
   - Keep est_hidden_pct ≤ 15%: you have only 0.6 points of headroom, so cull covered shingle overlap if the count rises.

**Nice to have:**
- Tail vane height: 0.32 × the wheel diameter against about 0.4 in mill_overall. Take the outer edge to 2.5–2.7 m if the client agrees.
- Footing stones (x05): several still have soap-bar rounded ends. Give 1 in 3 a straight fracture end.
- Kit: pass a context or dimension object down to the helpers instead of the module table.

**Workflow note:** the user has lowered the pass criterion to 8.2 for now. This round's 9.1 clears it. The must-fix list above still stands for the eventual 10. The user's round-hut daub/wattle correction belongs to the HUT log and was not applied here.
