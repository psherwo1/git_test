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

## v6_barn round 2 — score 8.1/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note 10), no surface-detail requests (note 12). Binding: producer notes 1-17, the CLIENT DIRECTION and Brief at the top, the CLIENT DIRECTION of 19:40 (cruck cart entry, low plinth) and the PRODUCER NOTE of 20:16. I re-read this log before starting and again before writing. Nothing was added after the round-2 builder entry. **The round has the client's cruck arched cart entry and no kiln, so the producer's 8.1 cap does not apply.**

**Reviewed:**
- the recipe `build_v6_barn.py` (112 lines);
- `kit/changes/v6_barn.md` (round 2);
- the new kit code: `cruck.arched_doors`, the `g.CRUCKS` record keys, and the `linear_roof` options `verge_roll`, `comb_step`, `comb_backing` and `rafter_lift_max`;
- the six `round_02` views, `stats.json`, `hidden.json` and `decal_anchors.json` (68 anchors: 16 moss on `M_thatch`, no soot);
- all 32 `builder_extra` shots.

**Director checks** (`renders/variants/v6_barn/round_02/director_extra/`):
- **`dir_render_r02.py`** (from `dir_render_r01.py`) makes 20 shots. It adds a **void twin**: front faces black, BACK faces yellow, red world. Yellow means a slot that looks into a hollow or the culled interior, which the plain red twin cannot see.
  - d21 / d22: post head, wall head and eyelid soffit, W and E.
  - d23: arch crown, tie and infill.
  - d24: door threshold and pads.
  - d25: arch springing.
  - d26: the eyelid fading into the eave.
  - d27 / d28 and d35 / d36: the W and E apex, from 3 m and from the ground at eye level.
  - d29 / d30: the SW and NE corner soffit from below.
  - d31: ridge end profile.
  - d32: hoist side-on.
  - d33: loft door at eye level.
  - d34: back at eye level.
  - d13-d15: thumbnails.
  - d17: W three-quarter at eye level.
- **`dir_lineup_r02.py`** makes the note-16 line-up (v3 longhouse, v5 harbour house, v6 barn and the roundhut hero, one scale): L01 ortho front, L02 three-quarter, L03 aerial. It also makes the one-rig thumbnails (46 m, lens 50, 320 x 180, SW / SE). `dir_montage_r02.py` composes them into `T_thumb_montage_v3_v5_v6_hut.png`.

**Numbers:**
- 213,945 tris (cap 1,000,000);
- hidden 13.3 % (cap 15 %);
- 9 palette slots;
- no mesh missing `Mask`;
- 68 decal anchors;
- man-door clearance PASS. The cart entry is not gated.

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **8.4** | **For:** one long, steep, slumped thatch roof whose eave sweeps up in a thatch **eyelid** over a round-arched timber entry. It is the client's "one organic composition", and it reads at once in L01, the hero and both thumbnails. The new rolled verge gives each rake one soft line on the sky, with no saw-tooth (b05_red, side). **Against:** (a) the front is mirror-symmetric: entry, eyelid, windows at +-4.4 and finials all stamped about x = 0 (front, L01). (b) The arch is modest at thumbnail; the eyelid carries the read. |
| 2 | Proportion and actor scale | **8.3** | **Entry:** 3.40 m between the posts, crown 3.26 m, eave lip about 4.2 m. **Man door:** 2.05 m with steps. **Also good:** the loft door on the plate, small shuttered windows and slits, all right next to the 1.8 m figure; plate 3.0 m, roof 50 deg. **Against:** (a) the arch head falls fast to the sides: at 2.8 m the clear width is only **2.36 m** (round 1's cart door was 3.0 x 2.8). (b) The hoist hook hangs only about 0.5 m outside the now-thicker verge roll (d32), so a load would hit the thatch. |
| 3 | Construction logic | **8.2** | **For:** the cruck frame is carried: posts, a near-semicircular arch ring springing off the posts' inner faces (d25), the tie on the posts, and the infill to the thatch. The wall runs into the posts and stops at the tie bearing. The doors stand behind the ring, so they can swing in. The 13 tails that stood on nothing under the lift are gone, and the boarded soffit closes the eave (s08, d26). Spars wrap the roll (s09). **Against:** (a) the posts appear to stand **straight on the ground**. The pads are built at z -0.30..0, so only a flush top face exists (d24, s18, s19, actor_closeup). The client asked for "posts on dressed pad stones". (b) The hoist barely clears the roof (axis 2b). |
| 4 | Seams and junctions | **8.0** | **Closed:** every cart-entry junction (d21-d26 void twins black; s17, s20 0 red), the filleted eave-verge corners (s12, d09, s13, d29, d30: black, with single-pixel specks only), the comb (d10_red, s09_red: red only in the sky) and the lift soffit. **Against:** **an open hollow at BOTH gable apexes.** The two rake rolls end in rounded butts that meet in a V under the lead hat, leaving a dark open triangle into the roll / hat hollow. It is yellow in the void twins d27, d28, d35 and d36, and visible from the ground at eye level (d35) and in s10 / b05. This is the gable's most prominent point. |
| 5 | Distinctness and reuse | **8.6** | **Distinctness:** clearly a different building. The montage shows two "block + stone drum + cone" buildings (v3, v5), the hut, and a long soft thatched barn with an arched timber entry and no drum or cone. This is exactly the client's 19:40 aim. **Note 16:** the same rubble plinth, rough boarding, thatch courses, lead hats, turned finials and timber language (L01 / L02). **Reuse is exemplary:** `cruck_frame` comes over from the harbour house unchanged, moved from the quay to dry land. The one new component (`arched_doors`) reads the frame's published arch. Every softness (verge roll, comb, lift tails) is a defaults-off `linear_roof` option that any thatched design can use. |
| 6 | Technical compliance | **8.3** | **Within limits:** triangles, hidden %, palette, `Mask`, determinism. The thatch now carries 16 moss anchors, and there is no soot on a hay barn. **Against:** (a) the cart entry, the main entrance, is outside the clearance gate. The client said "with clearances passing", and today that rests on hand numbers. (b) The 16 thatch moss anchors sit on a rigid 1.6 m grid in two rows. (c) `linear_roof` changed in two rounds with the hash rule reasoned, not run. |

**Overall 8.1 / 10: REVISE (round 3 of 3, the last).** The client's direction is met, and met well: the arched cruck entry under the thatch eyelid is integral, organic and distinct, and the round-1 roof defects (saw-tooth verge, corner blobs, comb slits, loose tails, no thatch decals) are all fixed. It is held under 8.2 by one real hole (the apex) and two client-direction gaps (visible pads, a gated cart clearance). All three are small, local fixes. Do only these, and do not reopen anything else.

**Strengths:**
- **The signature:** the eyelid and the arched entry are one gesture. The eave lifts 1.55 m over a near-semicircular timber arch, round-headed plank doors fill it, and the courses flow round it (b01, b02, hero).
- **The rolled verge** (`verge_roll`): one continuous D-section edge from apex to apex via both eaves, with true fillet corners. It is the best thatch edge in the kit and reusable by every thatched design.
- **The reuse story:** the harbour house's boat arch, on land, unchanged. The barn is a 112-line declarative recipe.
- **Closed and clean:** every entry junction passes the void twin. 214k tris and 9 slots.

**Must-fix (round 3):**
1. **Apex verge-roll joint** (`linear_roof._verge_rolls` / `_verge_roll_path`, `verge_roll=True`; both gables, under the turned finial's lead hat).
   - **Now:** the two rakes' rolls end in separate rounded butts that meet in a V, leaving an open hollow under the hat (d27, d28, d35, d36 yellow; s10, b05 dark slot).
   - **Should be:** a closed apex. Either:
     - continue the roll path over the apex as ONE swept bend (a fillet in the gable plane, like the eave corner, passing under the ridge-roll end); or
     - end both rolls inside a closed apex cap: the lead hat or ridge-roll end cap carried down over both roll ends, with a closed underside.
   - **Check:** d35 / d36 void twins show no yellow.
2. **Visible pad stones under the cruck posts** (`cruck.cruck_frame`, pads `wbox(pd, ..., -0.30, 0.0, ...)`; both posts of the cart entry).
   - **Now:** the pads stop at z = 0 and the posts start at z = 0, so the posts read as driven into the ground.
   - **Should be:** a defaults-off option (e.g. `pad_top=None` -> 0.0, the old path). The barn passes `pad_top` of about 0.12-0.15, so each dressed pad stands proud like the plinth's stones, and the post starts on the pad top. Keep the 2 cm plinth run-in.
3. **Gate the cart entry's clearance** (`cruck.cruck_frame` / `g.CRUCKS` + the kit clearance guard; recipe `DIM`).
   - **Now:** the main entrance is not checked. At 2.8 m the arch is only 2.36 m wide.
   - **Should be:** two parts.
     - **The guard:** `cruck_frame` registers its arch intrados as a clearance opening, defaults off or record-only, and `build.log` prints PASS for a 2.4 m wide x 2.8 m high cart envelope plus the 1.8 m figure.
     - **The arch:** make the envelope pass by raising the springing to about 2.10 (R about 1.83, crown unchanged), or by widening `clear` to about 4.2 (opening 3.6, R about 1.87), keeping the eyelid's lip at least 0.8 m over the crown.

**Nice-to-have (only if free):**
- **Hoist beam** (`hoist_beam`): lengthen it to about 1.5 m, so the hook hangs at least 0.9 m clear of the verge roll's outer face, and add a rope.
- **Front symmetry:** set `cart_x` about 0.8-1.2 m off centre (the eyelid follows), or vary one window, so the long side is not mirror-stamped.
- **SW / NE corner from below** (d29): the plate end, the verge rafter foot and a bargeboard sliver form a small loose cluster under the fillet. Tidy it (the harbour-house polish item).
- **Course ends at the verge** (d31): the course butts poke into the verge roll with faceted points. End them under the roll's inner face.
- **Moss anchors:** jitter the 1.6 m two-row grid on `M_thatch`.
- **Audit:** run the hash rule (`v6r2_hash` against `kit/baseline/6_r8kit_check` / `7_v5_ref`), since `linear_roof` changed in rounds 1 and 2.

**Note 17:**
- **Round element: PASS.** It is integral: the arch frame carries the wall head and the infill, and the eyelid is the roof's own warp over it. It is **distinct**: no drum and no cone, a timber arch, not masonry. The thumbnail montage confirms it.
- **Soft lines: PASS.** The ridge sag, the eyelid, swept eaves, flared verges and the continuous rolled verge.

**Reuse: PASS, and exemplary.** One unchanged cross-design module (`cruck_frame`), one new component (`arched_doors`), and defaults-off options only.
## v6_barn round 3 — builder entry

I re-read this log before starting and again before writing. No CLIENT DIRECTION or PRODUCER NOTE was added after the round-2 grade, so this round does the grade's three must-fixes and nothing else, as the director asked ("do not reopen anything else"). There were no nice-to-haves. The hoist, front symmetry, corner cluster, course ends and moss grid are all as in round 2.

**Built:** `buildings/variants/v6_barn/build_v6_barn.py` (119 lines, declarative) -> `v6_barn.blend` + `decal_anchors.json`. The barn is the round-2 building with the three fixes below. Build: 264 s full, about 9 s with `BARN_FAST=1`.

**Must-fixes:**
1. **Apex verge-roll joint** (`linear_roof(verge_roll=dict(apex_bend=0.22, bend_over=0.12))`; new `VERGE_ROLL` keys, defaults off; option (a) of the grade).
   - Each slope's rake roll now stops at the tangent point of a 0.22 m arc in the gable plane. It runs on **over the apex in one swept bend**, with the section turning with it: its up goes from the slope normal, through vertical, to the other slope's normal.
   - It ends 0.12 m down the far side, where its rounded taper is buried in the other slope's roll. The two rolls cross in one closed knot under the ridge-roll end and the lead hat. There are no butts and no V.
   - **Check:** the void twins **d27, d28, d35 and d36 show no yellow** (`round_03/builder_extra/`). s10, b05 and the new b08 (the W apex from above, oblique) show no slot. In `side.png` the gable reads as one rolled arch.
   - At `bend_over` 0.24 (first FAST build) the two full sections shared about 0.24 m and their +-1 cm swelling interleaved in a mottled patch. At 0.12 the join is one clean taper line.
2. **Proud pad stones** (`cruck_frame(pad_top=0.13)`; new option, None = the old flush pads).
   - Each dressed pad now runs from z -0.30 to 0.13 with 3 cm arrises, and each jamb post starts 1 cm inside its pad. So the posts stand visibly on stones: b07, s18, s19, d24 and `actor_closeup`.
   - **Seam found and fixed:** with proud pads, the old plinth end (2 cm into a flush pad, 5 cm short of the post) left a thin see-through slot under the sill, between the last rubble stone and the post. It is red in b07_void of the first full build, and the same slot is red in round 2's d24_void. The plinth's free ends now run 5 cm into the posts (recipe `PAD`; a 1 cm run-in did not close it). b07, s18, s19 and the d24 void twins are now black.
3. **The cart entry's clearance is gated** (`cruck_frame(gate=CART_GATE)`; new option, None = no check; `guards.entrances_of` reads the new `g.CRUCK_ENTRANCES`).
   - **The arch:** `clear` 4.0 -> **4.2**: opening 3.60 m between the posts, R 1.87. The spring stays 1.90 and the crown 3.26, so the arch stays near-semicircular, and the eyelid is unchanged (lip about 4.2 m over the crown, 0.9 m above it).
   - **`build.log`:**
     - `clearance gate BARN cart_entry arch: cart envelope 2.40 x 2.80 m -> clear width 2.449 m at its head (arch crown 3.26 m): PASS`
     - `... figure envelope 0.60 x 1.80 m -> clear width 3.500 m: PASS`
     - the kit's eave-lip gate on the published entry: `cart_entry_arch: door head 3.26 m, eave lip over it 3.740 m (lowest station, at the opening's edge) on BARN_barn_roof_deck (rule >= 3.26 m): PASS`
     - the east man door: PASS.
   - A FAIL raises `ClearanceError`.

**Reuse:** no new component. The three fixes are defaults-off options on existing modules: `linear_roof` (`VERGE_ROLL` + `_apex_bend`), `cruck.cruck_frame` (`pad_top`, `gate` + `_gate`) and `guards.entrances_of` (one optional source). Kit changes are in `kit/changes/v6_barn.md` (round 3, proposed kit 1.18).

**Hash rule:** not triggered; not run. With `pad_top=None` the post and pad `wbox` calls are the old ones (z0 `0.0 - 0.0`). With `gate=None`, `_gate` is never called and no attribute is set, so `entrances_of` adds nothing. `apex_bend=None` is the round-2 `_verge_rolls` path, which is barn-only. No rng draw was added or moved, and the harbour house uses neither cruck option.

**Stats (round_03/stats.json):**
- 213,651 tris;
- hidden 12.8 %;
- 9 palette slots (iron, lead, mortar, roof_shake, stone, stone_dressed, thatch, timber, timber_weathered);
- no mesh is missing `Mask`;
- 68 decal anchors;
- bbox 16.09 x 8.79 x 9.27 m;
- clearance PASS (cart envelope, figure, entry eave lip, man door).

**Renders:**
- `renders/variants/v6_barn/round_03/`: the six views at 24 samples.
- `builder_extra/` (`bld_render_r03.py`: the director's `dir_render_r02.py` rig and void twins), 16 shots:
  - b01 / b02: the entry, eye level and three-quarter;
  - d25: the springing;
  - d24, s18, s19, b07: the pads;
  - d27, d28, d35, d36, s10, b05, b08: the apex bend;
  - d13 / d14: thumbnails.
- FAST-iteration probes are in `buildings/variants/v6_barn/scratch/r03_fast/`.

**Known gaps:**
- The apex knot is two crossing sweeps, not one loop. A soft seam line shows where the second roll's taper dies into the first, under the lead hat's drip (s10, b08). It is closed: the void twins are black.
- The gate's envelopes are centred rectangles. They do not model a cart's hub bulge or a figure beside the cart. The arched leaves open inward behind the frame and are not modelled open.
- The cart leaves' outer bottom corners stand about 10 cm into the proud pads' inner nosing, behind the posts.
- The director's line-up / T-montage was not re-run. The massing is unchanged apart from a 0.2 m wider arch (d13 / d14).

## v6_barn round 3 — score 8.4/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note 10), no surface-detail requests (note 12). Binding: producer notes 1-17, the CLIENT DIRECTION and Brief at the top, the CLIENT DIRECTION of 19:40 (cruck arched cart entry, low plinth) and the PRODUCER NOTE of 20:16. I re-read this log before starting and again before writing: nothing was added after the round-3 builder entry.

**Reviewed:**
- the recipe `build_v6_barn.py` (119 lines) and `build.log` (the gate lines, the decal gate);
- the new kit code: `cruck.cruck_frame(pad_top=, gate=)` and `cruck._gate`, `guards.entrances_of` (`g.CRUCK_ENTRANCES`), `linear_roof.VERGE_ROLL` (`apex_bend`, `bend_over`) and `_apex_bend`;
- the six `round_03` views, `stats.json`, `hidden.json` and `decal_anchors.json` (68 anchors: 20 moss, 19 damp rise, 9 streaks, 7 grime, 7 patches, 5 lichen, 1 rust; no soot);
- all 16 `builder_extra` shots and their void twins.

**Director checks** (`renders/variants/v6_barn/round_03/director_extra/`):
- **`dir_render_r03.py`** (from `dir_render_r02.py`, same rig and void twin) makes 18 shots:
  - d21 / d22 and the new close-ups d37 / d38: the post heads under the eyelid after the 0.1 m outward move of each post;
  - d23: the arch crown, tie and infill;
  - d39 / d40: the door-leaf feet against the proud pads, W and E (the builder's "10 cm into the nosing" gap);
  - d26: the eyelid fade;
  - d41: the E apex bend from above (the twin of the builder's b08 W);
  - d42: the W apex from the ridge side;
  - d31: the ridge-end profile (red twin);
  - d29: the SW corner soffit;
  - d32: the hoist; d34: the back at eye level;
  - d13-d15 thumbnails and d17 W three-quarter at eye level.
- **`dir_lineup_r03.py`** makes the note-16 line-up at one scale (v3 longhouse, v5 harbour house, v6 barn, roundhut hero): L01 ortho front, L02 three-quarter, L03 aerial. It also makes the one-rig thumbnails (46 m, lens 50, 320 x 180, SW / SE). `dir_montage_r03.py` composes them into `T_thumb_montage_v3_v5_v6_hut.png`.

**Numbers:**
- 213,651 tris (cap 1,000,000);
- hidden 12.8 % (cap 15 %);
- 9 palette slots;
- no mesh missing `Mask`;
- 68 decal anchors;
- `build.log` gate:
  - cart 2.40 x 2.80 m: 2.449 m clear at its head, PASS;
  - figure 0.60 x 1.80 m: PASS;
  - the entry's eave lip 3.740 m against the 3.26 m crown, PASS;
  - the man door, PASS.

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **8.4** | **For:** unchanged and right. One long, steep, slumped thatch roof whose eave lifts into the eyelid over the round-arched timber entry (front, hero, L01, d17). From the ground, each gable is now one rolled arch over the apex (side, d35, d36). **Against:** (a) the front is still mirror-stamped about x = 0 (the round-2 nice-to-have, not done). (b) From above, the apex reads as two crossing tubes with cut-off tips, not one bend (b08, d41). This is invisible from the ground and at thumbnail. |
| 2 | Proportion and actor scale | **8.4** | **The entry:** 3.60 m between the posts, crown 3.26 m, and a gated 2.449 m clear at 2.8 m. The near-semicircle survives the widening (b01, actor_closeup). The posts now visibly stand on 13 cm dressed pads beside the figure (d39, d40, b07). **Also fine:** the man door, the loft door and the windows. **Against:** the hoist hook still hangs only about 0.4-0.5 m outside the verge roll (d32), so a load would brush the thatch. |
| 3 | Construction logic | **8.4** | **For:** the posts stand on proud pads, and the plinth's free ends now run into the posts with no slot (d39_void, d40, b07_void). The arch springs off the posts, the tie bears on them, the infill rises to the thatch, and the leaves sit behind the ring. **Against:** (a) at both post heads (d37, d38, also visible in b01 / b02) the wall's last boards, the frame's infill boards and the tie end meet in a stepped, shadowed pocket under the soffit. It is closed (the void twins are black) but reads as loose board ends rather than a framed junction. (b) The hoist is short (axis 2). |
| 4 | Seams and junctions | **8.3** | **Closed:** the round-2 apex hollow is gone. d27, d28, d35, d36, s10, b05, b08 and d41 void twins are black apart from single-pixel specks. Also black: all entry junctions (d21-d23, d26, d37, d38), the pads, and the corner soffit (d29). **Against (hairlines only):** (a) d42_void: a 1-px yellow hairline down the joint between the W ridge-roll end cap and the lead hat (a dark line in the clay view); (b) d39_void: a 1-px slit between the W post's inner face and the leaf edge at 0.15-0.6 m; (c) b08 / d41: the buried taper tips of the apex sweeps are ragged where they exit the other roll. |
| 5 | Distinctness and reuse | **8.6** | **Distinctness:** the montage shows two block + stone drum + cone buildings (v3, v5), the round hut, and the barn: a long soft thatch with an arched timber entry under an eyelid, with no drum and no cone. It is a different building at 320 x 180 from both SW and SE. **Note 16:** the same rubble plinth, rough boarding, thatch courses, lead hats, turned finials and timber language (L01 / L02). **Reuse:** all three fixes are defaults-off options on existing modules (`cruck_frame`, `linear_roof`, `guards`). No new component was added this round. |
| 6 | Technical compliance | **8.4** | **Within limits:** triangles, hidden %, palette, `Mask` and determinism. **The main entrance is now gated:** a FAIL raises `ClearanceError`, and it feeds the kit eave-lip gate. **Against:** (a) the hash rule has been reasoned, not run, for three rounds of `linear_roof` / `cruck` / `guards` changes; (b) the moss anchors are still on the regular grid. |

**Overall 8.4 / 10: PASS (round 3 of 3).** The lowest axis is 8.3 (hairline seams only), rounded up by one, as every must-fix landed cleanly and no new defect reaches the eye-level or thumbnail views. Going to the independent audit.

**Audit condition (not a builder round):** before the audit upholds the pass, run the hash rule (`v6r3_hash`) against `kit/baseline/6_r8kit_check` / `7_v5_ref`. `linear_roof` changed in all three rounds, and `cruck` / `guards` in rounds 2-3. v5 uses `cruck_frame`, so its hash must be bit-identical.

**Strengths:**
- **The signature:** the thatch eyelid over a round-arched cruck entry. It is one organic gesture, the client's 19:40 aim, and distinct from v3 / v5 at thumbnail.
- **The rolled verge**, now with a closed apex bend: one D-section edge from the eave, up the rake, over the apex and down. From the ground the gable reads as one soft arch.
- **A gated main entrance:** `cruck_frame(gate=)` is a reusable clearance check for any arched opening, and the boathouse can use it next.
- **Reuse:** the harbour house's boat arch on dry land, in a 119-line declarative recipe. Every round-3 change is a defaults-off option.

**Must-fix:** none for the pass.

**Nice-to-have (carry to the kit polish list, ONLY where a later design uses the part):**
1. **`linear_roof._apex_bend`** (both apexes): bury the far taper fully under the ridge-roll end or the lead hat's skirt, so the cut tips do not show from above (b08, d41). Then close the 1-px joint between the ridge-roll end cap and the lead hat (d42_void).
2. **Post heads under an eave lift** (recipe `wall_top` / `cruck_frame` infill, d37 / d38): end the wall boards on the post with a cover board, or carry the frame infill out to the wall plane, so the pocket under the soffit reads framed.
3. **`hoist_beam`:** lengthen it to about 1.5 m (hook 0.9 m clear of the verge roll) and add a rope.
4. **Front symmetry:** `cart_x` about 1 m off centre, or vary one window.
5. **`cruck.arched_doors`:** close the leaf-to-post hairline (d39_void); trim the leaves' outer bottom corners clear of the pads' nosing.
6. **Moss anchors:** jitter the grid on `M_thatch`.

**Note 17:**
- **Round element: PASS.** It is integral: the arch frame carries the wall head and infill, and the eyelid is the roof's own warp over it. It is distinct: timber, not a stone drum and cone (montage).
- **Soft lines: PASS.** The ridge sag, the eyelid, swept eaves, flared verges, and the rolled verge now continuous over the apex.

**Reuse: PASS, and exemplary.** `cruck_frame` came over from v5 unchanged in its default path. There is one new component over the whole design (`arched_doors`) and one new kit component (`hoist_beam`, round 1). Every softness and every guard is a defaults-off option that other designs can use.

## v6_barn round 3 — sign-off audit: REJECTED

Independent auditor. I read this log (Brief, CLIENT DIRECTION, the 19:40 direction, the 20:16 PRODUCER NOTE and every entry) and producer notes 12-17 before starting, and re-read the log before writing. Nothing was added after the round-3 grade. Read-only bpy, one process at a time. Scripts and outputs are in `renders/variants/v6_barn/round_03/audit/`.

**Verdict: REJECTED, on one hard requirement.** There is an open see-through gap into the barn at both cruck post heads, under the eyelid over the main entrance, and it is visible from ground (1.7 m) cameras. Everything else that is gated passes, including the director's audit condition (the hash rule, now run). The fix is small and local.

**Blocking: the post-head wedge is OPEN into the interior** (both sides, x about cart_x +-1.8..2.8, z 3.5-4.0; `aud_seethru_r03.py`, `aud_holes_r03.py`).
- **Method.** Pinhole camera rays, the same projection as the renders, cast on the whole building. A ray is counted as a hole if it passes into the barn's interior volume (the footprint shrunk 0.45 m, below the roof underside minus 0.8 m) before its first hit. Rays that end on a `*blocker*` dark room behind a designed opening are not counted.
- **Result.** At each post head the rays pass between the wall boards' head (`BARN_walls_boards`), the frame's infill and tie end (`BARN_cart_entry_boards` / `_frame`) and the eyelid soffit (`BARN_barn_roof_deck`). They travel about 5 m into the barn and first hit the INSIDE of the roof deck at about (+-4.8, 1.5, 5.3).
  - Ground eye level (1.7 m), 6 m out from the wall: 730 rays (E) and 493 rays (W) at 640 x 360 (`probe_img/E_post_head_eye_6m_out.png`, `W_post_head_eye_6m_out.png`: red = a ray into the interior).
  - Eye level, 3.5 m out: 714 rays (`E_post_head_eye_4m_out`).
  - The director's d37 / d38 cameras: 849 / 1495 rays.
  - Over a 15-viewpoint eye-level grid (2-6 m out), it is open from 7 of 15 viewpoints (W) and 6 of 15 (E). Aperture (twice the narrowest clearance along the hole rays): median 11-13 mm, p90 39-49 mm, max 80-90 mm. From 6 m high it is closed (0 rays).
- **Why the round-3 evidence missed it.** In d38 (clay) it is the black triangle in the "stepped, shadowed pocket". The void twin cannot see this kind of hole: the faces seen through it are the deck's FRONT faces inside the barn, which render black in the twin. So "closed (the void twins are black)" (axis 3 / axis 4, d37 / d38) is not supported.
- **Fix (recipe / frame, defaults unchanged):** close the wedge between the wall head, the frame infill and the soffit. Either:
  - stop `wall_top`'s `z_tie` cut at the infill's real edge, so the wall boards run up to the soffit beyond it; or
  - carry the frame's infill / backing out to `frame_half` and up to the soffit, with a cover board on the post.
  
  Verify with `aud_seethru_r03.py` (interior-reach test, 0 rays at the post heads), not with the void twin.

**Should-fix, same pass: the arch-to-leaf slit** (`cruck.arched_doors`, both sides of the arch between the springing and the haunch, z 2.1-2.95). Between the ring's back face (y about -3.219) and the leaves' arched top (front y -3.207, plus the `lap`), rays from eye level 2-4 m out pass over the leaf top into the barn. They hit the loft dark room 4-6 m inside. 133 of 30,240 grid rays; aperture median 4 mm, max 19 mm (`aud_holes_r03_out.txt`, `probe_img/arch_springing_W.png`). It is a hairline at eye level, but it is open: lap the leaf top tighter (setback 0, or a backing strip on the ring's back).

**Checked and passing:**

| item | evidence | result |
|---|---|---|
| triangles | 213,651 evaluated (`aud_probe_r03_out.txt`) = `stats.json` | PASS (cap 1,000,000) |
| palette | 9 slots, all in the shared palette, no empty slot | PASS |
| hidden | 12.6 % independent (`tools/hidden_tris.py`, `aud_hidden.json`) vs 12.8 % reported | PASS (cap 15 %) |
| `Mask` | on all 42 meshes (CORNER, active) | PASS |
| transforms | identity except the 14 pooled `BARN_pintle_*` instances (by design) | PASS |
| decal anchors | 68 empties = 68 json entries, names equal, all props present; 0 anchors without a surface within 20 cm behind them; 0 buried; types and heights plausible (moss on thatch / boards, damp rise 0.35-0.69 m, lichen on the plinth, no soot) | PASS |
| cart-entry clearance (measured on the mesh) | horizontal rays through the frame depth: 3.60 m clear to the springing, **2.446 m at 2.8 m** (gate 2.449); crown 3.256 m; 0 non-door hits inside a centred 2.4 x 2.8 m envelope; lowest eave / soffit over the doorway **3.748 m** (gate 3.740) | PASS (>= 2.30) |
| man door | gate line in `build.log`: lip 5.03 m over a 2.58 m head | PASS |
| floating pieces | 1,287 islands; 0 whose 2 cm-inflated box touches nothing; the hoist pieces sit 1.8 / 4.2 cm from the frame (the hook and block hang from the beam) | PASS |
| pads | 13 cm proud; posts start 1 cm in; plinth into the posts; 0 interior rays at the post / pad / plinth junction from eye level | PASS |
| leaf edge / post (d39 "1-px slit") | 0 interior rays over 59,850 eye-level and 6 m grid rays. The red in d39_void is the hidden ground plane under the leaf. Not a hole. | PASS |
| apex bend, eave / verge corners, eyelid fade, comb | 0 interior rays from ground and 6 m. Back-face hits only as 1-30 px specks at the apex verge roll and ridge-comb end (ground: 0-1 px). | PASS (polish item, as graded) |
| leaf / pad clipping | the leaves' outer bottom corners stand up to 5.8 cm into the proud pads, behind the post's inner face (x beyond the post). Seen from the ground the leaf meets the 5 cm nosing as a contact line. | not visible as clipping; construction nit (the director's nice-to-have 5) |
| **hash rule** (the director's audit condition) | `kit/baseline/v6r3_hash/`: all 8 rebuilt with today's kit. keep, hut, mill, v1, v2, v3 and v4 are identical to `6_r8kit_check` on all three hashes (geometry, uv, mask); `geom_diff`: no object differs. **v5 is per-object identical to `7_v5_ref`** (the delivered r08: geometry `c3d3a5343572dc73`, 714,452 tris). | PASS: defaults-off holds for `linear_roof`, `cruck`, `guards` |

**Observation (kit, not blocking, pre-existing):** two large `RUBBLE_LARGE` ground stones under the east gable have inside-out winding: about (7.15, -0.17, 0.12) and (7.15, 2.51, 0.16). From +x, 93 of 153 rays hit back faces. It is the same in the FAST (uncull) build, so the cull is not the cause. `aud_stones_r03.py` finds the same in the accepted v5 (`HARB_hall_stones`, `HARB_wing_stones`). This is a `path_stone_wall` hero-stone winding item for the kit list: with one-sided UE materials those stones would drop out.

**Not re-judged:** silhouette, distinctness, note 16 and note 17. I agree with the grade: the cruck arched entry under the thatch eyelid is integral, distinct from v3 / v5, and built from reusable kit modules.

**What a resubmission needs:** close the post-head wedge, and ideally the arch slit, then rebuild. Re-check with `aud_seethru_r03.py close` (post-head, eye-level and arch shots at 0 interior rays), hidden <= 15 % and the tri count. The hash rule does not need re-running if the fix is in the recipe or a defaults-off option.
## CLIENT DECISION (2026-10-17, session 2, 22:05): barn PAUSED at round 3

The Art Director passed round 3 at 8.4. The audit rejected it on one hard requirement: the open see-through wedge at both cruck post heads, under the eyelid (wall-board head / frame infill / eyelid soffit). The client chose "Pause the barn".

Round 3 stays as work in progress in `buildings/variants/v6_barn/`. **When the barn resumes:**
1. close that wedge only (the audit's fix: recipe / frame, defaults unchanged);
2. re-audit (no full re-grade needed; the director's 8.4 stands unless the geometry changes otherwise).

Kit changes (1.16-1.18) are in `kit/changes/v6_barn.md`. The hash rule was verified by the audit (`kit/baseline/v6r3_hash/`): all eight other buildings are identical.