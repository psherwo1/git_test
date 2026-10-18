# v6_barn: the village barn (plan step 3, after the harbour house)

## CLIENT DIRECTION (2026-10-17, session 2)

- Plan step 3 (client "Yes proceed"): the timber / rectangular / waterfront family through the harbour house, **then a boathouse or barn**. The client chose: "Let's do the barn".
- Team method as before: one builder; the Art Director grades every round on the note-12 modularity rubric (pass mark 8.2); an independent audit must uphold a pass. **At most 3 rounds** (time matters: the client said "do not spend time that can be avoided, and the earlier a correct result is obtained, the better").
- Binding: producer notes 1-17 in `director/art_bible.md`, in particular:
  - **note 16:** the same builders, techniques and materials as the rest of the village;
  - **note 17:** round structures and soft, organic lines are the village's signature.

  The client's reuse mandate also stands: "Reuse as many existing modules as possible".

## Brief

A working village barn for hay, carts and animals, standing on ordinary ground (Z = 0).
- **Plan:** rectangular, about 12-14 m x 6.5-7.5 m.
- **Walls:** the village rubble as a plinth or the lower walls (`path_stone_wall`), with rough, old timber boarding above (`path_timber_wall(rough=True)`), or rubble gable ends with boarded long walls.
- **Openings:**
  - large double **cart doors** in a long side (the timber host's large-door head rules);
  - a **hayloft door** high in a gable, with a hoist beam;
  - a man door;
  - a few small openings or slits.
- **Roof:** the village's soft, slumped roof (`GableRoof` ridge sag, eave sweep, verge flare), steep and dominant.
  - **Thatch is preferred** for variety, since the roundhut and the longhouse are thatched and the harbour house is shingled, if `linear_roof`'s thatch covering takes the soft options cleanly. Otherwise use the village shingle.
  - Village finials (ball or turned) at the gables.
- **Round element (note 17):** at least one round element that is integral to the composition.
  - It must **not** repeat the "rectangular block + round stone tower at one corner" formula of v3 and v5.
  - Options, builder's choice, with the reason recorded:
    1. a half-round (apsidal) end under a half-cone or round-hipped roof;
    2. a round stone granary or drying kiln built into the middle of a long side, under its own cone, breaking the eave;
    3. a round-arched cart entrance through a cruck frame, as the barn's signature (`cruck_frame` on dry land).
  - The director checks distinctness against v3 and v5 at thumbnail size.
- **Optional, if cheap:** an eyebrow over the hayloft door (`GableRoof(eyebrows=[eyebrow(profile="arch", respace=True)])`). It is shingle-only today.

**Start from the family proof:** `buildings/variants/v5_harbour_house/scratch/barn_smoke/build_barn_smoke.py` (30 lines). It is a post-and-plank barn on a rubble plinth with clamp / trim boat doors, shuttered windows, and a soft shingle roof with finials.

**Kit polish to fold in, ONLY where the barn uses the part** (kit changes, defaults unchanged), from the harbour-house grades:
- the swept eave / verge corners (the `linear_roof verge="board"` rafter tail below the bargeboard foot);
- the dark slot along a swept eave;
- the ridge-comb slits;
- the eyebrow's tower-side shoulder and window margin, if an eyebrow is built.

Everything else on that list waits.


## v6_barn round 1 — builder entry

**Built:** `buildings/variants/v6_barn/build_v6_barn.py` (97 lines, declarative) -> `v6_barn.blend` + `decal_anchors.json`. A working village barn, 14.0 x 7.0 m, ground Z = 0, with:
- **Walls:** a rubble plinth (`path_stone_wall`, `RUBBLE_LARGE`) under rough old post-and-plank walls with board-and-batten gables (`path_timber_wall(rough=True, bow=0.03)`).
- **Roof:** a steep, soft **thatch** roof, 50 deg (`linear_roof(covering="thatch")`), using the `GableRoof` soft options: 0.30 m ridge sag, eave sag, a 0.22 m swept eave, verge flare and wave. Thatch takes them cleanly: every course, eave roll, verge face and ridge roll follows the warp. Turned finials on lead hats at both gables (`apex_finial="turned"`).
- **Cart doors** on the front long side, 3.0 x 2.8 m clear from the ground. The thatch eave **sweeps up over them in one soft arch** (new `eave_lift`, 0.85 m), so the eave lip over the door head is 3.00 m (guard PASS at 2.80).
- **Hayloft door:** high in the west gable (new `loft_door`, the open two-leaf loft door on the plate), under a **hoist beam** with a curved knee brace, pulley block and hook (new `hoist_beam`).
- **Man door** with built-in stone steps in the east gable. Small shuttered windows; vent slits in the back and gables.

**Round element (note 17):** option 2. A squat **round rubble drying kiln / granary built into the middle of the front long side** (`round_stone_body`, face r 2.25 m, 1.5 deg batter, 4.9 m wall). It projects 3.7 m, sits 0.8 m into the barn, and carries its own mossy shingle cone (`cone_roof` on a `RoundFrame`, eave 5.05 m) with the spike finial. It has a granary door and two small windows.
- The barn's thatch runs into its wall (`wall_abutment`: one trace run eave to eave round the drum's inner side, mortar flaunching, lead end aprons; seal probe 82k rays, **0 leaks**). The cone's eave oversails the thatch with 0.57 m clear at the wall.
- **Why it is distinct from v3 / v5:**
  - v3 is a long block ENDING in a big round house, its drum rising a storey past the ridge.
  - v5 is a hall with a tall round TOWER at one CORNER, with a timber top storey, rising far above the ridge.
  - Here the drum is low and wide, set in the MIDDLE of a long side. It **breaks the eave line** (the thatch eave runs into it from both sides), and its cone apex is only about 0.4 m above the sagging ridge. At thumbnail it reads as a long, dominant thatched roof with a round kiln pushed through its eave. It is not a block with a tower. The lifted cart-door eave beside it adds a second soft curve the other two buildings do not have.

**Covering:** thatch (main roof, the village's layered courses, seated ridge roll, comb) + village shingle on the kiln cone (as v3 pairs thatch and a shingle cone).

**Reuse table:**

| part | module | status |
|---|---|---|
| kiln drum | `rubble_walls.round_stone_body` (`RUBBLE_LARGE`, `open_z="mid"`, clip under the barn deck) | existing, unchanged |
| kiln cone, finial, beam-fill | `composite.cone_roof`, `finial.finial("spike")`, `roof_junction.round_eave_fill(z_bot="wall")` on `frame.RoundFrame` | existing, unchanged |
| thatch into the kiln wall | `roof_junction.wall_abutment` | existing, unchanged |
| plinth | `rubble_walls.path_stone_wall` (two open paths: ending in the kiln and in the cart-door pads) | existing, unchanged |
| walls, gables | `timber_walls.path_timber_wall(rough, bow)` | existing, + new options |
| doors, windows | `openings.door / window`, `wall_openings.door_spec / window_spec`, `timber_walls.boat_door` | existing, + new options |
| thatch roof | `linear_roof.linear_roof(thatch, apex_finial="turned")` + `GableRoof` soft options | existing, + new options |
| cull, decals, recentre | `composite_hidden_cull`, `composite_decals(timber=True)`, `recenter`, `set_entrance` | existing, unchanged |
| **lifted eave over a wide door** | `GableRoof(eave_lifts=[eave_lift(...)])` | **new option** (warp term; thatch + shingle) |
| **seated ridge roll** | `GableRoof(ridge_seat=True)` | **new option** (fixes the slot under the ridge roll on a steep thatch: the "ridge slits") |
| **cart door to the ground on stone pads** | `boat_door(to_ground=True, pad=)` | **new option** (sill beam cut, dressed pads under the jambs) |
| **gable openings / open loft door** | `window(gable=True)`, `window(lights=0)`, `loft_door()` | **new options / helper** |
| **hoist beam** | `timber_walls.hoist_beam` | **new kit component** |

Kit changes are recorded in `kit/changes/v6_barn.md` (kit 1.16).

**Stats (round_01/stats.json):** 336,426 tris; hidden 12.3 %; 10 palette slots (iron, lead, mortar, roof_shake, roof_shingle, stone, stone_dressed, thatch, timber, timber_weathered); no mesh missing `Mask`; 90 decal anchors; bbox 16.1 x 11.9 x 9.75 m. Build: 393 s full, 16 s with `BARN_FAST=1`. Guards: clearance PASS (kiln door 5.05 m lip; cart doors 3.00 m lip over a 2.80 m head; east man door), seal probe 0 leaks.

**Hash rule:** not triggered. Every change to an existing module (`linear_roof`, `timber_walls`, `wall_openings`) is a new option or key whose default takes the old code path: no warp term or `warped` change without `eave_lifts`, the old ridge-roll profile without `ridge_seat`, the same single sill `wbox` call and rects without `to_ground`, and the old boxes for `lights` 4 / 2. No rng draws were added or moved. So there was no `v6r1_hash` run.

**Renders:**
- `renders/variants/v6_barn/round_01/`: the six views at 24 samples. The early preview (first FAST build) is in `round_01/preview/`.
- `builder_extra/` (`bld_render_r01.py`):
  - the four builder close-ups: b01 kiln, b02 cart doors, b03 west gable with roof and hoist, b04 ref4-style high three-quarter;
  - 15 seam probes with red see-through twins. No see-through found.

**Seams fixed in round 1:**
- the slot under the thatch ridge roll along the whole ridge (`ridge_seat`);
- the cart-door threshold, which sat on the sill beam (0.53 m) and was clamped to 2.27 m clear (`to_ground` + pads);
- the eave lip below the cart-door head (`eave_lift`);
- the cone's eave dipping toward the thatch: the drum was widened to r 2.25 at 1.45 m in front of the wall, the cone eave set at 5.05 m and the overhang at 0.42 m.

**Known gaps:**
- The kiln is still a fairly upright drum (4.9 m wall, 4.5 m diameter): the thatch at its inner face sets the cone eave's minimum height. The director should judge its distinctness at thumbnail.
- The back long side is plain: three slits, no round element visible except the cone tip.
- Hoist beam: no rope. The pulley block's sheave is a box.
- No eyebrow (the optional item; shingle-only).
- `s14` (cone eave over the thatch) was mis-aimed; the junction is covered by s02 and the seal probe.
- The kiln's granary door is the masonry `door_spec` with a flat lintel. There is no arched head.


## v6_barn round 1 — score 8.0/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note 10), no surface-detail requests (note 12). Binding: producer notes 1-17, the CLIENT DIRECTION and the Brief at the top of this log (at most 3 rounds; "Reuse as many existing modules as possible"). I re-read the log before starting and before writing: no CLIENT DIRECTION or PRODUCER NOTE was added after the round-1 builder entry.

**Reviewed:**
- the recipe `build_v6_barn.py`, `kit/changes/v6_barn.md` and the kit 1.16 code in `linear_roof._ridge_roll` / `_ridge_comb`;
- `build.log` (guards, seal probe, the decal gate);
- the six `round_01` views, `stats.json`, `hidden.json` and `decal_anchors.json`;
- the preview, the 4 builder close-ups and the 15 seam probes with their red twins.

**Director checks** (`renders/variants/v6_barn/round_01/director_extra/`):
- `dir_render_r01.py` (the builder's / v5 rig) makes 16 shots:
  - d02-d06 are the kiln junctions the builder did not probe (s14 was mis-aimed): the thatch against the back of the drum from the ridge, W and E; the cone eave and the E fin; the eave lip into the drum low, W and E. All have red twins.
  - d07 / d08: the hoist, side-on and from below.
  - d09: the SW eave / verge corner under the lift.
  - d10: the ridge skyline, with a red twin.
  - d11 / d12: the kiln door and the loft door at eye level.
  - d13-d15: thumbnails at 45 m.
  - d16 / d17: three-quarter views at eye level.
- `dir_lineup_r01.py` (from v5's `dir_lineup_r03.py`) makes the note-16 line-up of v3 longhouse, v5 harbour house, v6 barn and the roundhut at one scale (L01 ortho front, L02 three-quarter, L03 aerial). It also makes per-building thumbnails from ONE camera rig (46 m, lens 50, 320 x 180, SW and SE), composed in `T_thumb_montage_v3_v5_v6_hut.png`.

**Numbers:**
- 336,426 tris (cap 1,000,000);
- hidden 12.3 % (cap 15 %);
- 10 palette slots (shared palette only);
- no mesh is missing `Mask`;
- 90 decal anchors;
- guards PASS, seal probe 0 leaks.

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **7.9** | **Strengths:** the steep, slumped thatch is the dominant mass, and the lifted eave over the cart doors is the best soft line in the village after the harbour-house eyebrow. Ridge sag, swept eaves and flared verges all read at thumbnail. **Against:** (a) the kiln reads as a **turret**, not a kiln: a 4.9 m drum on a 4.5 m diameter under a steep cone with the spike (d16, front, hero). (b) The steep thatch verges have a regular **saw-tooth skyline**, one tooth per course end (side, b03, d08, d12), which is the opposite of note 17's rolled, rounded verges. |
| 2 | Proportion and actor scale | **8.4** | **Doors and windows:** cart doors 3.0 x 2.8 m clear, from the ground on dressed pads; man door 2.05 m with stone steps; kiln door 2.05 m; small shuttered windows and slits, all right next to the 1.8 m figure. **Roof:** plate 3.0 m and a 50 deg roof, in range. **Hoist:** the hook hangs only about 0.45 m outside the verge face (d07). |
| 3 | Construction logic | **8.2** | **Sound:** the plinth runs into the pads and the kiln, the timber stands on the plinth, the thatch is carried on rafters and the deck, and the kiln is bonded into the long side under its own cone. **Against:** (a) under the eave lift the rafter tails are short loose blocks stuck on the boarded infill (b02, s08). Nothing visibly seats them, and they end short of the lifted soffit. (b) The ridge's binding spars stand off the roll at one end (d03, s09, d10). |
| 4 | Seams and junctions | **8.0** | **Closed:** the kiln junction is closed everywhere: seal probe 0 leaks; s01-s05 and d02-d06 are clean, and every red twin is black. **Against:** (a) **red slits between the ridge-comb shakes along the whole ridge** (d10_red, s09_red). This is the "ridge-comb slits" item the Brief asked to fold in. `ridge_seat` fixed the slot under the roll, not the comb. (b) At all four eave / verge corners the **eave roll's end cap bulges past the verge face as a crumpled, faceted blob** under the first verge tooth (s12, s13, d09, d12). |
| 5 | Distinctness and reuse | **8.0** | **Reuse is exemplary:** about 20 existing modules, unchanged or with defaults-off options; one new kit component (`hoist_beam`); two spec helpers (`loft_door`, `eave_lift`). **Note 16** holds: the same rubble, timber, thatch, shingle cone, finials and lead (L01 / L02). **Distinctness is only partial.** The mid-side placement follows option 2 and is new. But the element is the same drum plus steep spiked shingle cone as v5's tower and v3's round end, at a turret's proportions. At the SE thumbnail (montage, bottom row) the barn reads as a long gabled body with a round drum at its front-left: v3's formula from that angle. The roof, not the round element, carries the distinctness. |
| 6 | Technical compliance | **8.4** | **Within limits:** triangles, hidden %, palette and `Mask`; the build is deterministic and seeded. **Against:** (a) the **thatch, the dominant surface, carries 0 decal anchors.** All 32 footprint rejections in the gate are the moss on the 50 deg thatch (n.n0 0.49-0.74). v3's thatch carries 13 moss anchors; here all 14 moss anchors are on the cone shingle. (b) Soot is placed on the timber heads of a hay barn (DA_soot_003-007). (c) The hash rule was reasoned from the code but not run (acceptable, but the audit should run it). |

**Overall 8.0 / 10: REVISE (round 2 of at most 3).** It is a strong first round, and its reuse is the best of any design so far. The roof is right, and every junction is closed. It is held below 8.2 by the round element's turret reading (note 17 distinctness) and by three linear_roof thatch details that the steep pitch exposes.

**Strengths:**
- **Roof and soft lines:** one soft, dominant thatch roof. The cart-door eave lift is a genuinely new soft line, done the right way: one warp term that every part follows.
- **The kiln junction:** the thatch abutment into the drum is closed and flashed (0 leaks, all red twins black). The cone eave clears the thatch.
- **The working barn reads at a glance:** cart doors to the ground on stone pads, an open loft door with a curved-brace hoist, a man door with steps.
- **A short recipe:** 97 lines, declarative, almost all existing modules. The new options default to the old path.

**Must-fix (round 2):**
1. **Kiln massing** (recipe `DIM` / `KIT`, `round_stone_body` + `cone_roof` + `finial`; front long side): today the drum is upright (4.9 m wall, about 4.5 m diameter) with a spike, so it reads as a turret and, from the SE, as v3's block plus drum. Make it a **squat kiln / granary** with a wall-height to diameter ratio of about 0.8 or less:
   - set the axis further out (c of about r, so the drum's back meets the thatch near the eave, not 0.8 m up the slope);
   - widen it (r_kiln about 2.4-2.6) and drop the wall and cone eave to about 3.8-4.1 m, still oversailing the thatch by at least 0.3 m at the wall;
   - keep `wall_abutment`, and re-run the seal probe.

   The cone apex must then sit clearly **below** the barn ridge. Replace the spike with the village ball finial or, better, a small boarded kiln vent at the apex built from the existing lantern / board-belt language. Check it again in the T-montage SE view.
2. **Thatch verge** (`linear_roof`, `covering="thatch"`, both gables): two defects.
   - (a) The rake shows one tooth per course (side, b03, d08). Add a defaults-off option that gives the verge one continuous soft edge: for example, a verge roll along the rake that matches the eave roll, or course butts that taper into the verge face over the last ~0.3 m. The verge should read as one rolled line on the sky.
   - (b) At the eave / verge corners (s12, s13, d09) the eave roll's end cap sticks out past the verge face as a faceted blob. End the roll in the verge plane, so the roll turns into the verge in one rounded corner with no faceting.
3. **Ridge** (`linear_roof._ridge_comb` / `_ridge_roll`, the whole ridge):
   - (a) The comb shakes advance by `w * 0.92`, and their ragged tips leave red slits along the crest (d10_red, s09_red). Overlap more (about 0.75 w) or seat them on a continuous comb backing, so the red twin shows no slit.
   - (b) The binding spars are laid on the constant `roll_centre_z()` and y = 0, while the roll follows `_ridge_centre(x)` with its wobble, so one end of each spar floats (d03). Lay each spar on `_ridge_centre(x)` at its own x, and put it on the seated profile when `ridge_seat=True`.
4. **Rafter tails under the eave lift** (`linear_roof` rafters + `path_timber_wall` `roof_top_fn` over the cart doors; b02, s08): the tails are loose blocks on the infill boarding. Either seat them on a head beam that follows the lift (the boarding's top), with each tail reaching the soffit, or drop the tails where the lift is over about 8 cm and close the arch with the boarded soffit. Nothing should look stuck on above the main entrance.
5. **Decals on the thatch** (`composite_decals` moss recipe on `M_thatch` at 50 deg): get about 10-15 moss anchors onto the main thatch, as on v3. For example, use a smaller footprint or the course-mean normal on thatch, so the gate stops rejecting all of them. While there, stop the generic soot recipe placing soot on the barn's timber door and loft heads (keep the kiln's).

**Nice-to-have:**
- **Hoist beam:** lengthen it to about 1.5 m (the hook at least 0.9 m clear of the verge face) and add a rope; the sheave can stay simple.
- **Kiln door:** an arched or rounded head (note 17), if the `door_spec` round-head option exists.
- **Back long side:** one more element on the back, such as a small shuttered window or a lean-to hook point for the later add-ons.
- **Loft door:** a slightly deeper dark room, so it does not read as a shallow box at eye level (d12).
- **Audit:** run the hash rule (`v6r1_hash` against `kit/baseline/6_r8kit_check` / `7_v5_ref`), since linear_roof and timber_walls changed.

**Note 17:** the soft lines PASS (ridge sag, swept and lifted eaves, flared verges, bowed walls, the curved hoist brace), apart from the saw-tooth verge (must-fix 2). The round element is **integral** (bonded into the wall and roof, with the thatch running into it) but **not yet distinct enough** (must-fix 1).

**Reuse:** PASS, and exemplary: no bespoke one-off geometry, and every softness is a kit option.

## CLIENT DIRECTION (2026-10-17, session 2, 19:40): the round element is a round-arched CRUCK CART ENTRY; keep the low plinth (round 2)

The client reviewed the early preview (`round_01/preview/`) and chose:
1. **"Cruck arched cart entry".**
   - **Remove** the mid-wall round rubble kiln / granary, its cone and its `wall_abutment`. It reads as the same stone-drum-plus-cone formula as v3 and v5.
   - **The barn's round element becomes its cart entrance:** a big round-arched timber **cruck frame** (`cruck.cruck_frame` on dry land, re-using the harbour house's boat-arch module, e.g. `respond_z=None`), framing the double cart doors in the front long side under the existing thatch **eave lift** (`eave_lift`). It should read as ONE organic composition: the arched timber entry and the thatch eyelid over it.
   - Keep the cart doors 3.0 m wide or a little wider, with clearances passing. The arch springs from posts on dressed pad stones.
   - The doors may follow the arch head (a round-headed leaf top) or sit under a tie with arched braces above, whichever reads more organic and stays sealed.
   - Keep everything else that works: the soft thatch roof, the ridge seat, the loft door and hoist beam, and the gables.
2. **"Keep low plinth":** the rubble stays a low plinth with boarded walls above. Do not raise it.

The back long side may stay plain. Re-check distinctness against v3 / v5 at thumbnail: the barn should now read as a long, soft thatched roof with an arched timber cart entry, not a block with a round tower.
## PRODUCER NOTE (2026-10-17, session 2, 20:16): the cruck cart entry is a round-2 MUST-FIX

The round-2 fixer started at 19:57, before the client's 19:40 direction was written here at 20:15.
- **Round-2 fixer:** if you are still working, apply it now (it replaces the kiln). Re-read this log before writing your entry.
- **Art Director:** a round that still has the mid-wall kiln instead of the client's cruck arched cart entry cannot pass; give at most 8.1.
- **Round-3 fixer:** do it first.

## v6_barn round 2 — builder entry

I re-read this log before starting and again before writing. The CLIENT DIRECTION of 19:40 (written here at 20:15) and the PRODUCER NOTE of 20:16 arrived while I was working. **They are applied in this round: the kiln is removed, and the round element is the round-arched cruck cart entry.** I had already fixed the director's five round-1 must-fixes when the direction arrived. Fixes 2-5 are kit work and carry over unchanged. Fix 1 (the kiln massing) was rebuilt as graded (a squat r 2.5 drum with a 3.95 m wall, cone eave 4.15 at 44 deg and a ball finial; seal probe 0 leaks) and is now superseded. That build is archived in `buildings/variants/v6_barn/scratch/r02_kiln/` with its renders, for reference only.

**Built:** `buildings/variants/v6_barn/build_v6_barn.py` (112 lines, declarative) -> `v6_barn.blend` + `decal_anchors.json`. A working village barn, 14.0 x 7.0 m, ground Z = 0, built centred on a `PlanFrame`:
- **Walls (client "keep low plinth"):** the low rubble plinth (`path_stone_wall`, `RUBBLE_LARGE`, 0.35 m) under rough old post-and-plank walls with board-and-batten gables (`path_timber_wall(rough=True, bow=0.03)`). These are unchanged from round 1.
- **The round element: a round-arched timber cruck cart entry** in the middle of the front long side. It uses `cruck.cruck_frame` on dry land, the harbour house's boat-arch module with no change to its code paths:
  - clear 4.0 m, jamb posts on dressed pad stones, opening 3.40 m between the posts;
  - a near-semicircular arch: spring 1.90, crown 3.26, R 1.74;
  - a tie beam at 3.52-3.78, with short blades and plank infill up to the thatch on a closed backing.
  - **Doors:** round-headed plank cart doors fill the arch (new `cruck.arched_doors`: two leaves, rough boards on a closed backing, ledges and straps). The leaves' arched top edge hides behind the arch ring.
  - **Wall junction:** the front wall runs into the posts (an open path). Over the frame's width it stops at the tie's bearing, where the frame's infill takes over (v5's `hall_top` pattern).
- **The thatch eyelid:** over the entry the eave sweeps up in one soft arch (`eave_lift`, now 10 m wide and 1.55 m high, 3.0 m fade): the eave lip is about 4.2 m over the centre. The arched timber entry and the thatch eyelid read as ONE organic composition (b01, b02, hero, front).
- **Kept as before:** the soft 50 deg thatch (ridge sag, swept eaves, flared verges, wave, the ridge seat), turned finials on lead hats, the loft door with its hoist beam in the west gable, and the east man door with steps. The front now has a small shuttered window either side of the entry.

**Distinctness (note 17, client):** at thumbnail (d13 / d14) the barn reads as a long, soft thatched roof with an arched timber cart entry under a thatch eyelid, with no stone drum and no cone anywhere. That is not the block plus round tower of v3 / v5. The round element is now timber and the roof's own line, not masonry.

**Round-1 must-fixes:**
1. **Kiln massing:** done as graded, then removed per the client (see above).
2. **Thatch verge** (`linear_roof(verge_roll=True)`, new, defaults off):
   - **(a)** One continuous ROLLED edge per slope: the eave roll's own D section, swept from the apex down the rake, round the eave corner, along the eave and up the other rake. The rake part's lip runs 7 cm outside the course ends, and the verge face is clamped under the roll. Result: no saw-tooth on the sky (b05, side, b03, d10).
   - **(b)** The corner is one 0.28 m fillet in the slope plane (s12, d09, s13). There is no end cap and no blob. The deck's eave corners follow the fillet, and the verge rafter starts above it.
3. **Ridge:**
   - **(a)** `comb_step=0.75` plus `comb_backing=True` (a continuous backing board in the saddle). The red twins d10_red and s09_red show no slit: red is only the sky above the crest.
   - **(b)** With `ridge_seat`, each spar is laid on `_ridge_centre(x)` at its own x (s16).
4. **Rafter tails under the lift:** `rafter_lift_max=0.08`. The 13 front tails where the lift exceeds 8 cm are dropped, and the arched boarded soffit closes the eave (s08, s08_red: only sky). Nothing is stuck on over the entry.
5. **Decals on the thatch:** the recipe's gate now uses v3's settings for stepped courses (`fp_skip_surfaces` incl. `M_thatch`, the course-mean normal test). There are **16 moss anchors on `M_thatch`** (0 in round 1). `composite_decals(timber_soot=False)` (new, defaults on) puts no soot over the timber doors and loft. With the kiln gone, the barn has no soot at all.

**Reuse table (round 2):**

| part | module | status |
|---|---|---|
| cart entry | `cruck.cruck_frame` (the harbour house's arch frame, on dry land) | existing, unchanged |
| round-headed cart doors | `cruck.arched_doors` | **new kit component** (reads the frame's published arch) |
| thatch eyelid | `GableRoof(eave_lifts=[eave_lift(...)])` | existing (kit 1.16) |
| rolled verge + corner | `linear_roof(verge_roll=True)` | **new option** |
| comb overlap / backing, rafter tails under a lift | `linear_roof(comb_step=, comb_backing=, rafter_lift_max=)` | **new options** |
| plinth, walls, gables, loft door, hoist, windows, man door | `path_stone_wall`, `path_timber_wall`, `loft_door`, `hoist_beam`, `openings.door / window` | existing, unchanged |
| roof, finials, cull, decals, recentre | `linear_roof(thatch)`, `composite_hidden_cull`, `composite_decals(timber=True, timber_soot=False)`, `recenter`, `set_entrance` | existing + one new option |

Kit changes are in `kit/changes/v6_barn.md` (round 2, proposed kit 1.17).

**Hash rule:** not triggered, so there was no `v6r2_hash` run. Every change is a new option, function or record key whose default takes the old code path, and no rng draw was added or moved on a default path. The cruck module only gained `arched_doors` and extra keys in `g.CRUCKS`, with no geometry change for v5. The reasoning is in `kit/changes/v6_barn.md`.

**Stats (round_02/stats.json):**
- 213,945 tris;
- hidden 13.3 %;
- 9 palette slots (iron, lead, mortar, roof_shake, stone, stone_dressed, thatch, timber, timber_weathered);
- no mesh is missing `Mask`;
- 68 decal anchors;
- bbox 16.09 x 8.79 x 9.27 m;
- build 262 s full, about 9 s with `BARN_FAST=1`.

**Guards:** the clearance gate passes for the east man door. With the kiln gone there is no roof abutment, so no seal-probe junction is registered.

**Renders:**
- `renders/variants/v6_barn/round_02/`: the six views at 24 samples.
- `builder_extra/` (`bld_render_r02.py`, adapted from round 1):
  - close-ups: b01 cart entry eye, b02 entry three-quarter, b03 west gable verge roll, b04 high three-quarter, b05 side elevation of the rake;
  - seam probes with red twins: s08 lift soffit, s09 / d10 comb, s10 apex, s12 / d09 / s13 corners, s16 spars, s17 arch-tie-infill, s18 / s19 post-pad-plinth, s20 frame end at the wall head;
  - thumbnails d13 / d14, and d16 eye three-quarter.

  s17 and s20 have 0 red. s18 / s19 / s08 / s10 show red only where the ground or sky shows (the twin hides the ground). There is no see-through.

**Known gaps:**
- The cart entry is not a wall opening, so the kit's clearance gate does not check it. Measured: the opening between the posts is 3.40 m, the arch crown is 3.26 m, and the eave lip over it is about 4.2 m. I did not add a guard hook.
- The cruck pad stones are flush with the ground (the module's -0.30..0 pads). They read as a stone top face only.
- `verge_roll`: the two rakes' roll ends meet under the capped ridge roll and the lead hat at each apex. They read as a ridge-end knot (b05, s10).
- No round-3 polish was attempted: no hoist rope or longer beam, and no lean-to hook on the back.
- The director's line-up / T-montage (`dir_lineup_r01.py`) was not re-run. d13 / d14 are the builder's thumbnails from the same rig.
- A stray empty directory `C:\buildings` was created outside the repo by one render call with a relative path. Its contents were moved or removed. The tool guard blocks deleting the empty folder itself.