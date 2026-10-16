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
