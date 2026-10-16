# SPEC: tower_windmill (prefix `MILL`, collection `MILL`)

**Files:**
- Build script: `buildings/tower_windmill/build_tower_windmill.py`
- Output: `buildings/tower_windmill/tower_windmill.blend`
- Renders: `renders/tower_windmill/round_NN/`
- Log: `director/log_tower_windmill.md`

**References:**
- Main: ref1 (the mill right of the keep).
- Crops:
  - `director/ref_crops/mill_overall.png`
  - `mill_sails_wheel.png`
  - `mill_stone_base.png`
- Supporting ref2/ref3 mills: `style_mill_lattice_sails.png` and `style_aerial_village.png`. They show four lattice sails on tower mills with conical/pyramidal caps.

Read `director/art_bible.md` first.

**Concept:** a hybrid tower mill unique to this world.
- A **round stone base** with a blind arcade and a corbelled cornice.
- A **shingle apron** at the top of the stone.
- A **tall tapering octagonal timber smock tower**.
- A **small shingled cap**.
- A rotor combining **four lattice "common" sails** with an **annular wind-wheel of 16 board blades** carried on a ring (ref1's distinctive look).
- Long **raking timber props** shoring the timber tower down to the ground.
- A **sloping stone buttress** on one side.

## 0. Scale derivation
Measured against the keep door in ref1 (about 20 px/m), then scaled up about 12% because the mill stands further back. The stone base comes to Ø about 5.2 m and the cap top to about 13 m, with a sail radius of 5.6 m.

## 1. Orientation
- **Tower axis:** at the world origin.
- **Entrance:** the stone-base door faces **−Y**.
- **Cap and rotor:** the cap is yawed so the windshaft points toward azimuth −15°, i.e. direction (−0.26, −0.97, 0) plus tilt. The rotor then reads almost face-on in the front and hero views, slightly to the right of the tower in the hero view, as in ref1.
- **Raking props:** they land on the **−X side** (left in front/hero views, as in ref1).
- **Sloping buttress:** on the **+X side** (right, as in ref1).

## 2. Components

### A. Stone base (`MILL_base_stones`, `MILL_base_mortar`, `MILL_base_dressed`)
- **Shell:** round, outer Ø 5.2 m at the ground, battering to Ø 4.9 m at 4.05 m. Wall 0.8 m thick (interior hollow; visible through the door).
- **Zones, bottom to top:**
  1. **Footing, 0–0.4 m:** larger stones projecting 0.08 m, partly sunk.
  2. **Plain rubble, 0.4–2.55 m:** coursed rubble per art bible §3.
  3. **"Balustrade" band, 2.55–2.95 m:** read `mill_stone_base.png`.
     - A lower dressed string course 0.12 m tall, projecting 0.12 m.
     - A row of stubby dressed balusters/blocks, 0.24 m tall, 0.10–0.12 m wide, at about 0.22 m pitch, slightly irregular, like a relief railing.
     - An upper string course 0.10 m tall, projecting 0.10 m.
  4. **Blind arcade, 2.95–4.05 m:** 10 round-headed arched recesses around the drum (skip or adapt the one above the door if needed).
     - Clear 0.72 m wide × 1.0 m tall, springing at 3.35 m, recessed 0.25 m with a rubble back.
     - Each has a ring of 9–11 dressed voussoirs.
     - Dressed pier blocks between the arches.
  5. **Corbelled cornice, 4.05–4.50 m:**
     - A row of about 40 small dressed corbel/dentil blocks, 0.12 w × 0.15 h × 0.18 proj.
     - Under a projecting moulded cap course 0.18 m tall, overhanging 0.30 m, with a chamfered underside and a drip.
- **Door (−Y), the actor close-up:**
  - Clear 1.05 m wide; semicircular head springing at 1.65 m, crown at 2.18 m clear above the threshold.
  - Dressed jambs and voussoir ring (outer crown at about 2.48 m, under the band at 2.55).
  - Reveal 0.30 m.
  - Arch-topped plank door with 3 strap hinges, a ring pull and ledges, in the same vocabulary as the keep door.
  - Threshold stone top at +0.14 m, plus one outside step stone (riser ≤ 18 cm).
- **Windows:** 2 slit windows (0.16 × 0.55 m, dressed jambs) in the plain zone at azimuth +70° and −130°.
- **Interior:** floor at +0.14 m and the inner wall face (cheap). One timber ladder or stair foot visible through the door is a bonus.

### B. Sloping buttress (+X side) (`MILL_buttress_stones`)
- **Form:** a battered stone buttress/ramp 1.4 m wide running radially out along +X. It meets the tower at a height of 3.6 m and slopes down to the ground at r ≈ 5.6 m (about 35°).
- **Finish:** dressed coping stones along the sloped top, rubble sides and a footing.

### C. Curb and shingle apron (`MILL_curb`, `MILL_apron_shingles`)
- **Curb:** a timber curb ring at 4.50 m on the cornice (0.2 × 0.25 section).
- **Apron:** a conical shingle skirt from an eave lip at **4.45 m**, radius 3.15 m (overhanging the cornice by about 0.4 m), rising to the timber tower foot at radius about 1.6 m and 5.4 m (≈32°). Two to three courses of long shakes, 0.6–0.8 m long and 0.14–0.22 m wide, with uneven butts and an irregular, slightly comb-like top edge (ref1).
- **Underside:** rafters on the curb, visible.

### D. Timber smock tower (`MILL_tower_boards`, `MILL_tower_frame`)
- **Form:** octagonal, across-flats 3.1 m at 5.4 m tapering to 2.0 m at 10.55 m.
- **Frame:**
  - 8 cant (corner) posts 0.2 × 0.2 m with chamfers.
  - A sill ring at the bottom and a top curb ring at 10.4–10.55 m (0.2 × 0.25).
  - Horizontal rails at 7.2 m and 9.0 m, with small drip boards (ledges) projecting 4 cm.
- **Cladding:**
  - Vertical weatherboards, 0.15–0.28 m wide and 3 cm thick, with battens over some joints. Ref1 shows vertical planks with a couple of horizontal joints.
  - Board ends are uneven and a few boards are slightly loose or askew.
- **Hatch:** one window hatch (0.5 × 0.6, frame and shutter propped open) on the −Y side at about 8.0 m.
- **Prop collar:** an iron band or timber collar at 9.5 m where the props attach.

### E. Cap (`MILL_cap_shingles`, `MILL_cap_frame`)
- **Form:** a small hipped pyramidal cap with a short ridge running along the windshaft.
  - Footprint about 2.7 × 2.5 m (overhang 0.3 m), seated on the curb.
  - Eave lip at 10.55 m, ridge or apex at about **12.6 m**.
- **Front:** a projecting gablet/hood over the windshaft neck.
- **Covering:** small shingles (0.12 m exposure) with hip boards and a small spike finial 0.4 m (to about 13.0 m).
- **Underside:**
  - Cap frame (sheers/weatherbeam) visible from below.
  - Small iron truck-wheels or rollers under the cap edge as a detail bonus.
- **Yaw:** the cap is yawed per §1.

### F. Windshaft and poll end (`MILL_windshaft`, `MILL_poll_end`)
- **Windshaft:** a timber shaft Ø 0.38 m, tilted up 8°, emerging from the cap front. Hub centre at **11.6 m** height, 1.55 m in front of the tower axis.
- **Poll end:** a cast-iron canister/cross box 0.55 m long with 2 square mortises for the stocks, bolt heads and an iron end-cap.

### G. Four lattice sails (`MILL_sail_A..D_stock`, `_whip`, `_bars`, `_hemlaths`, `MILL_sail_A_boards`)
- **Arrangement:** 4 sails at a "+" rotated 8° (as in ref1 one sail reads near 9 o'clock). Two stocks cross through the poll end, slightly offset front and back.
- **Stocks:** 0.30 × 0.30 m at the poll, tapering to 0.16 × 0.16 m at the tip. Sail radius **5.6 m** from the hub.
- **Whip:** each sail has a whip (0.16 × 0.16, tapering) bolted to the stock face with 4 iron clamps/U-bolts, running from r 1.2 m to the tip.
- **Lattice:**
  - Starts at r 1.3 m and runs to 5.6 m. Width 1.55 m: leading side 0.45 m, trailing side 1.10 m.
  - Sail bars about 3 cm × 5 cm at about 0.24 m pitch (~18 per sail), mortised through the whip.
  - 2 uplongs/hemlaths on the trailing edge and 1 on the leading edge, with real thickness and bevels.
  - A slight weather twist: the bars twist about 12° from heel to tip.
- **Boards on sail A:** sail A (the near-horizontal 9 o'clock sail) carries **board cladding** on its trailing lattice, as in ref1: 4–6 weathered boards 2 cm thick, slightly uneven, nailed. The other three are bare lattice.
- **Clearance:** the lowest point of any sail must clear the apron and props by **≥ 0.3 m**. Check this numerically in the build script and print it.

### H. Annular wind-wheel (`MILL_wheel_rim`, `MILL_wheel_blades`, `MILL_wheel_spokes`)
- **Position:** a plane 0.25 m behind the sail lattice plane.
- **Rings:** an inner ring at r 1.8 m and an outer rim at r 2.85 m. Each ring is an iron flat bar 60 × 10 mm, or a timber felloe of 0.08 × 0.10 segments with iron ties.
- **Blades:** **16 blades** spaced evenly, each spanning r 1.8 → 3.80 m.
  - 0.52 m wide at the inner end, flaring to 0.78 m at the outer end, with a slightly rounded and irregular outer edge.
  - Built from 2–3 boards (2 cm) and a central batten.
  - Pitched about 25° to the rotation plane.
  - Riveted or nailed to both rings.
- **Spokes:** 8 iron spokes (Ø 25 mm) from the poll end to the inner ring, plus 8 diagonal ties to the outer rim.
- **No collisions:** blades must not pass through the stocks. Where a stock crosses the wheel, the blade at that angle is omitted or notched, as in ref1 where the lattice sails read in front.

### I. Raking props (−X side) (`MILL_props`, `MILL_prop_anchors`)
- **Poles:** 3 long timber poles Ø 0.16–0.20 m, slightly bent and with bark knots.
  - Two run nearly parallel from the prop collar at about 9.5 m on the −X faces of the tower down to ground anchors at about (−6.3, −1.2) and (−6.0, +0.9).
  - The third runs from about 7.0 m down to about (−5.2, −2.6).
- **Joints:** iron straps/bolts at the tower end. At the ground, each sits on a stone pad block with a timber chock and iron pin, partly sunk.
- **Optional:** one cross-lashing or cross-brace between the parallel pair.
- **Clearance:** the rotor, especially the left half of the wheel, passes close to the props. Keep **≥ 0.3 m** clearance between any rotating part and any prop or apron (check numerically). Prop anchors may move up to ±1 m, and the attachment height between 8.5 and 9.8 m, to achieve this, while keeping the ref1 look of two near-parallel long props plus one shorter one on the left.

### J. Ground contact (`MILL_ground_rubble`)
- **Footing:** a larger footing course.
- **Rubble:** 40–70 scattered rubble stones of 0.05–0.45 m around the base and buttress, half-buried and clustered.
- **Path:** a worn flat path stone or two at the door.

## 3. Budget guidance (target 0.8–1.3 M triangles)
- Base masonry: about 450k (cull hidden backs).
- Apron + tower boards + cap: about 200k.
- Sails + wheel: about 250k. Lattice bars must be real boxes with bevels; they are the silhouette.
- Props, iron and rubble: about 80k.

## 4. 10/10 acceptance criteria
1. **Silhouette:** at thumbnail size it is unmistakably ref1's mill.
   - A stout stone drum with the arcade band, cornice and shingle apron, then a tall slender tapering timber tower, a small cap, and the rotor.
   - The rotor reads as four lattice sails plus a 16-blade ring.
   - Raking props on the left and the sloping buttress on the right.
   - Height ratios: stone base about 4.5 m vs timber tower about 5.2 m; rotor diameter about 11.2 m. All within ±10%.
2. **Scale:** the 1.8 m figure at the door shows a proper man-door with headroom of about 0.35 m. The step riser is ≤ 18 cm.
3. **Masonry:**
   - Individual bevelled stones and recessed mortar.
   - Dressed band, balusters, voussoirs, corbels and cornice as real separate pieces with chamfers.
   - The arcade recesses have real depth.
4. **Timber tower:** framed and boarded with real board thickness, rails, drip boards and a hatch.
5. **Rotor:**
   - Every bar, blade, ring, spoke, clamp and bolt is modelled with thickness.
   - Plausible attachment everywhere and nothing floating.
   - The clearance check passes. It reads mechanically believable.
6. **Age pass:** board irregularity, slight lean of the timber tower (≤ 1°), uneven shake tips, weathered or chipped dressed stones, slightly irregular blade edges. No perfect CG repetition.
7. **Technical:** all of art bible §8 (deterministic, oriented per §1, named, material slots, UVs, ≤ 1.5 M triangles, `.blend` < 80 MB, no artefacts in the 6 views).
8. **Must-fix list empty**, and no objection in the Director's side-by-side with the reference crops.


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
