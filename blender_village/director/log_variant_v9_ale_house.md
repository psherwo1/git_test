# Variant log: v9_ale_house (ALEH), builder round 1 (EARLY PREVIEW, ungraded)

## Design brief
A low, roofed T-plan village ale-house / inn (producer notes 16-19: same builders, techniques and materials; round element; soft organic lines; rounded-hip soft-crown thatch "an oval on the rectangle"; at least one eyebrow). Recipe: `buildings/variants/v9_ale_house/build_v9_ale_house.py` (copy of the v7 structure; no new kit code).

## Dimension table (summary)
| Part | Value |
|---|---|
| Hall | 12.0 x 6.0 m rubble (RUBBLE_LARGE), deck 2.90 m at the faces, thatch loaf 46 deg, crown 0.5, round hips both ends, ridge sag 0.15 |
| Wing (cross wing, front) | 4.4 m wide, projects 6.0 m from the hall front (x 0.8..5.2, y -9.0..-3.0), 42 deg, crown 0.12, round hip at the free S end, west eave lifted 1.75 m in one soft arch over the porch |
| Valley | roof_valley, wing into hall |
| Eyebrows | 2 thatch eyebrows: front slope x -2.8, back slope x +2.2 |
| Gabled dormer | back slope x -2.2 |
| Porch | kit porch (shingle bell-cast hood on two curved brackets) on the entrance, the wing's west wall, y -5.8; beam 2.32 m |
| Turret | round rubble stair turret r 1.25 m (batter 2 deg), head about 3.9 m, at the wing's free SW corner (pushed 0.55 m out), under a thatch dome (round-hipped GableRoof, 52 deg, eave lip about 3.5 m); the wing's thatch runs into it (wall_abutment) |
| Chimney | round rubble stack, east round hip, dressed cap and round pot |

## Preview status (FAST build, no cull)
- 676,075 triangles in the FAST build (stats est. 34 % hidden; the cull will reduce it). Cap 1,000,000.
- Guards: clearance PASS (lip over the door 2.711 m, door head 2.09 m); seal probe 0 leaks on all 3 junctions (wing roof / turret, porch / wall, roof / stack ring); decal anchors 97.
- 3 build attempts used: (1) porch eave margin too small, (2) hood too close to the lifted eave roll, (3) built.
- Previews: `buildings/variants/v9_ale_house/preview/` (clay).

## PRODUCER NOTES
(placeholder: client direction and producer notes go here; binding for the next round)
