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

## Builder round 2 (EARLY PREVIEW, ungraded): WATTLE AND DAUB across the design (producer note 20)
Client direction (note 20): wattle-and-daub must be a village technique, not one building.  Rubble where it takes weight and meets the ground, daub where it is light; same slots (M_daub / M_wattle / M_timber), same plinth, same thatch.
**What changed** (recipe `build_v9_ale_house.py`; new kit module `kit/village_kit/components/daub_path.py`, additive, see kit/CHANGELOG.md 1.21.0 -- daub.py / wattle.py / frame.py untouched):
- STAIR TURRET: the rubble body is now a 0.62 m rubble PLINTH (round_stone_body, same r 1.25 m / 2 deg batter) with a flat mortar cap; above it a full ROUND DAUB WALL (arc run, r 1.0 m wattle line, 6 round-hewn posts at 45 + 60 k deg, hut coat section, two exposed-wattle patches, 4 daub windows) up to the dome deck (z follows DOME.under_z_world).  Clips / abutment re-seated on the daub face (r 1.092 m).
- HALL HIP ENDS (the old board-and-batten "gablets" were hidden under the 2 m hip overhang): the end walls are rubble to 1.50 m and DAUB above it, posts + sill beam, up to the deck (W end, E-south, E-north beside the round stack); one patch on W and E-south; the west window and a window by the stack moved up into the daub.
- CROSS WING: rubble ground storey to 1.45 m, then a DAUB HALF-STOREY with sill beam on the east wall, the south hip end and the west wall either side of the masonry entrance bay (rubble to the lifted eave, 1.15 m each side of the door; the porch is unchanged); 4 upper windows, 2 patches.  The wing's four stone windows moved into the daub.
- The long hall walls (front / back) stay rubble.
**Daub walls now**: turret (all round, z 0.62 to deck); hall W, E-south and E-north hip-end walls above 1.50 m; wing east wall, wing south end, wing west wall north of the porch (to y -4.72) and south of it (y -6.88 to -8.70), all above 1.45 m.  Not daub: hall front / back walls, the wing's ground storey and entrance bay, the chimney, the dormer.
**Build**: FAST (no cull), 2 attempts (1 hip ends first built as a hidden gablet above the rubble cap -- invisible under the hip; 2 hip-end walls lowered to a visible half-storey).  1,096,350 triangles FAST (676,075 before); tools est. 45.9 % hidden -> about 590k after the cull (cap 1,000,000; cull not run).  The new daub objects are about 266k polys of that (posts 100k polys: round_post is 33 x 46 per post).
**Guards**: clearance PASS (lip over the door 2.711 m, door head 2.09 m); seal probe 0 leaks on all 3 junctions (wing roof / turret daub face 38,832 rays, porch / wall, roof / stack ring); decal anchors 65 (97 before: less rubble area).
**Honest weaknesses**: not graded or audited; coat relief is the kit's low-frequency bulge + 2 cm lumps only (flat in clay, needs the textured look); hip-end daub above about 3.2 m is hidden under the thatch (culled in the final build); turret has posts but no plate / horizontal rails; the wing door bay is a rubble pier up to the lifted eave beside daub, which may read heavy; the two path-daub kit modules (daub_wall.py by v8, daub_path.py here) must be converged; round_post meshes are dense (budget); no baseline run of the 8 buildings (nothing existing imports daub_path, but it MUST be run before grading).
Previews: `buildings/variants/v9_ale_house/preview_r2/` (clay six views) and `preview_r2/colour/` (flat colour by material slot, a quick technique check, not textures).
