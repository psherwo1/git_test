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
