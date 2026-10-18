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
