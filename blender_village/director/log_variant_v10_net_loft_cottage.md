# v10_net_loft_cottage (NETC): variant log

## Design brief
A fisher's cottage: a rubble ground storey (path_stone_wall) with a rough board-and-batten (path_timber_wall) upper
half-storey loft under ONE thatch loaf with round hips and a soft crown ("an oval on the rectangle"), a thatch eyebrow
dormer over the front door, an attached ROUND rubble store / oven house at the rear (north-east) corner under its own
cone, and a rounded thatch lean-to on the back wall for net drying. Compact, 8 x 5 m main plan. Low and roofed (eaves
under 4 m, no tower). Notes 16-19: same builders, techniques and materials; round element; soft lines; eyebrow;
rounded-hip crowned roof.

Recipe: `buildings/variants/v10_net_loft_cottage/build_v10_net_loft_cottage.py` (prefix NETC, `NETC_FAST=1`,
`NETC_OUT=`). Built from v7 (loaf roof, eyebrow, path walls), v3 (RoundFrame store + `wall_abutment`) and a1
(`lean_to` with `roof_ends="round"`). No new kit code.

## Dimension table (summary)
| Part | Value |
|---|---|
| Main plan | 8.0 x 5.0 m, ridge along x; deck 2.85 m at the faces; stone to 2.15 m, board-and-batten loft above |
| Main roof | thatch GableRoof, 46 deg, hips both (round), crown 0.5, overhang 0.45, ridge sag 0.15, eave sweep 0.16 |
| Eyebrow | thatch, arch profile, 2.5 m wide, 0.9 m lift, front slope over the door (x = -6.2) |
| Round store | face r 1.65 m (batter 2 deg), cone 40 deg, eave_z 3.85 m, ball finial; door az 40, window az 115 |
| Junction | loaf runs into the round WALL below the cone eave (`wall_abutment`, min_clear 0.25 passed) |
| Lean-to | back wall, 3.8 x 2.0 m, rounded thatch, host eave arch +2.1 m, z_face 3.08 |

## Early preview (FAST build, no cull)
Triangles 465,041 (FAST, est. hidden 31 %, so the culled build will be well under the 1,000,000 cap).
Guards: clearance PASS (door 2.50 m, lean-to front 2.35 m, store door 3.85 m); seal probe 0 leaks on both junctions.
Preview renders: `buildings/variants/v10_net_loft_cottage/preview/`.

## Known weaknesses (builder, before grading)
- The board-and-batten loft sits mostly under the deep thatch oversail; on the front it reads as a thin dark band.
- The store's cone is the kit's shingle cone (no thatch dome exists in the kit), and its eave is tall (3.85 m) because
  the eaves may not cross the thatch (the v3 lesson); it reads as a slim silo.
- The host eave arch over the lean-to is large (+2.1 m) to clear the guard (plate 2.10 m, lip 2.30 m).
- The eyebrow is large; the store is centred on the NE corner, not abutting via `cone_abutment` (the v3 r8 method,
  `wall_abutment`, was used).

## PRODUCER NOTES
(placeholder)


## Round 2 (2026-10-18): wattle-and-daub across the cottage (producer note 20) -- PREVIEW ONLY, not graded
Client direction (note 20): the village technique is wattle-and-daub; it must not be pasted on. What changed (FAST build, no cull, 881,356 triangles):
- LOFT / GABLETS: the board-and-batten is gone. `path_timber_wall(style="post_daub", gable_style="post_daub", bay_max=1.5)` (new optional kit style,
  kit 1.22.0): timber posts every <= 1.5 m to the roof line over the rubble sill, daub panels between, odd exposed wattle patches. Loft bands on
  front / back / west / east (front and east stop short of the store). The loft is now 1.0 m (deck 3.05 m, stone 2.05 m) instead of 0.7 m.
- STORE: `round_stone_body` replaced by the hut's chain: `drystone_plinth` -> `round_daub_wall` (r 1.50 m wall line, 8 posts, coat, exposed wattle,
  `wall_finish_r11`) -> `wall_plate` -> framed door + step. Same cone (40 deg, eave 3.85 m) and ball finial; the loaf still runs into the round wall
  below the cone eave (`wall_abutment`, radius given as a function because the daub body publishes no WALL_FACES; roof top 3.58 m vs eave lip 3.85 m).
  Door head infill is daub (`DOOR_INFILL_DAUB`), not boards.
- PLAN: the hut's door faces -Y and its door frame is 2.5 m wide, so the store moved from the back-east to the FRONT-east corner (house now y 1..6,
  store at the origin); east end window moved to the north half; lean-to z_face 3.08 -> 3.28 with the deck 0.2 m higher; front door 1.85 m (stone 2.05 m).
- Preview renders: `preview_r2/` (hero, front, side, back, aerial, actor_closeup clay; `color_*_mat.png` use the file's materials).
Guards: clearance PASS (3 doors), seal probe 0 leaks (roof / round wall 31,851 rays; lean_to / wall 74,870 rays), decal gate ran (anchors dropped as in r1).
Weaknesses: (1) store is a tall (3.4 m wall) slim daub silo, its upper wall a plain flat white coat with only low wattle patches; (2) loft daub is mostly in the
thatch shadow, wattle patches read as small dark lattices; (3) store walls have no decal anchors (not in WALL_FACES); (4) the door-head slab is a flat box
inside the flat door frame; (5) 6 builds were run (2 were trivial syntax / API errors); (6) `post_daub` duplicates kit 1.21.0 daub modules; (7) full cull
not run; (8) 8-building baseline NOT run.
