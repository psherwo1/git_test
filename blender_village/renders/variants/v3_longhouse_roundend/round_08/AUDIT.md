## v3_longhouse_roundend round 8 — sign-off audit: UPHELD-IF-PASSED

Independent auditor, 2026-10-17. Read-only. I built nothing and edited no recipe, kit file or director log.
Audited file: `buildings/variants/v3_longhouse_roundend/redesign_r8_wip/v3_longhouse_roundend_r8.blend` (33 meshes, **617,342 tris**, under the 1,000,000 limit), built by `redesign_r8_wip/build_v3_longhouse_roundend_r8.py` (`linear_roof(clip=inside_round(depth=0.10))` + `roof_junction.wall_abutment`).
Scripts and evidence are in `renders/variants/v3_longhouse_roundend/round_08/audit/`: `a2_measure.py` → `measure.json`, `a3_followup.py` → `followup.json`, `a4_islands.py` → `islands.json`, and close-ups `a01`-`a08*.png` (1280x720, Cycles 24 spp, denoised, OPTIX).
Round centre in world space: (4.61, 0.0), from the cone and finial bounding box. Drum face R(z) = 3.70 - z·tan 1.5°.

### Measurements

| check | result | evidence |
|---|---|---|
| **See-through gaps at the junction** (roof/flaunching/drum) | **0 leaks in 745,302 rays.** Targets were 2 cm behind the drum face, azimuth 110-250° in 1° steps, z 2.0-6.05 m in 2.5 cm steps. Cameras: 62 positions at eye height (1.6 m) and 6 m, 5-12 m out on both sides, plus 6 m gable-end cameras. A leak meant a first hit more than 8 cm inside the face, or sky. A second pass at z 0.05-2.0 m: **0 leaks in 409,550 rays.** | measure.json `leak_count`, followup.json `lowz_leaks` |
| **Roof parts inside the masonry** (target 2-3 cm) | Deepest point inside the face: covering 2.4 cm, eave roll 2.5, ridge 1.9, deck 3.5 (12 verts > 3 cm, none > 5), flaunching/aprons 4.0 (intended 3.5 cm bury; none > 5). Comb and rafters stop 25 cm and 43 cm short of the face. **No roof part is more than 5 cm into the drum.** None of the roof-part vertices deeper than 3 cm is visible from any camera (412 tested). | measure.json `penetration_into_drum`, `visible_deep_roof_verts` |
| **Cone eave over the roof** (the eaves must not cross) | Lowest cone parts: rafters 5.89 m, battens 5.93, starter 5.965, shingles 5.99. Highest thatch under the cone: comb 5.706 m. **Minimum vertical clearance is 0.241 m** (comb tip at (0.48, -0.04, 5.71) to the cone battens). The cone eave lip never meets the thatch, and a05 and a08 show it oversailing clear. | measure.json `cone_clearance_min`, a05_ridge_gable_6m.png, a08_ridge_end_tele.png |
| **Eave-end aprons** | 4 lead pieces (a plate and a closed lip at each eave end) at x 3.05-3.26, y ±3.31-3.45, z 2.60-2.97. They stand 1.6-8 cm proud of the face and nowhere go into it. Both eave rolls end on the apron with no slot (0 leaks). | measure.json `aprons`, a01/a02/a06 |
| **Flaunching** | The radial range against the face is -12.8 cm to +4.0 cm (toe out over the covering, back buried). One run, eave to eave over the ridge, follows the curve on the cylinder (a03/a04). | measure.json `flaunching_depth_range` |
| **Floating pieces** within 0.5 m of the drum | Abutment, eave roll, comb, rafters and deck: none. Three small loose islands: (1) a covering sliver of 10 verts, 0.60 x 0.07 x 0.06 m, at (1.02-1.62, 2.17-2.24, 3.52-3.58), 2.8 cm off its neighbours. It is visible from some cameras, but at 85 mm tele (a07) it cannot be told apart from the course below. (2) A ridge ligger ring of 36 verts at x 0.66, 2.1 cm proud; it reads as a ligger (a08). (3) A 2-tri `LONG_purlin_rings` remnant at (2.5, 2.48, 6.83), 8.7 cm loose, **seen by 0 cameras** (inside the cone void). | measure.json `floating`, islands.json, a07, a08 |
| **Door clearance** (entrance body_wall_3, 1.0 m wide, head 2.22) | The lowest overhead from 0.05 to 1.5 m in front of the door is the rafter feet at **2.317 m** (>= 2.30). The approach is clear: no hit on horizontal rays at 0.3-2.1 m across the 0.9 m opening. | followup.json `door_overhead_min`, `door_approach_blocked` |
| **Mask attribute** | Present on all 33 meshes (`mask_missing: []`). | measure.json |
| **Decal anchors** `decal_anchors_r8.json` | 89 anchors (moss 28, crack 20, lichen 11, damp 10, soot 9, streak 5, patch 3, grime 2, rust 1). All are within 6 cm of a surface (0 far), and the blend holds 89 matching DA_ empties. | measure.json `decal_*` |
| Triangle budget | 617,342 / 1,000,000 | stats.json |

### Visual confirmation
Close-ups at ground level and at 6 m are a01 and a02 (eave ends, eye level, 7.5 m), a03 and a04 (slopes from 6 m), a05 (ridge into the drum from the gable side, 6 m) and a06 (eave look-up). In them the thatch, eave roll and ridge die into the drum under one continuous flaunching. No crossing eaves, no splayed shingle fan, no dark slot and no clipped course is visible. The six official views (hero, front, side, back, aerial, actor_closeup) are clean. The redesign removes the eave-crossing junction behind every rejection from round 3 to round 6.

### Non-blocking notes (for the director; none is visible as a defect from ground level or in quick pans)
1. **`LONG_body_roof_deck` is listed as 100% hidden** in `round_08/hidden.json` (sampled estimate, about 617 of 624 tris). The round-4 audit's note-1 rule says "no object may be 100% hidden", and round 6 had none. The cost is 0.1% of the budget and the deck is the trim reference for the roof. I did not verify this with my own rays. The fix is a cull, or accepting it as structural.
2. The eave-end lead apron reads as a small flat grey plate beside the roll nose (a02, a06), not as lead dressed over it. It is closed and has no gap. This is a matter of taste.
3. `LONG_body_wall_stones` and `_mortar` go up to 17.8 and 23 cm into the drum at the body/drum corner (x 2.28-2.30, y 2.58, z 0-2 m). This is carried over from round 6. The low-z leak pass found no see-through, and actor_closeup shows a clean corner. (My follow-up visibility count for these vertices is not valid: some of its cameras were inside the drum. It is not used here.)
4. The covering sliver (2.8 cm loose) and the 2-tri purlin remnant are cleanup items only.

**Verdict: UPHELD-IF-PASSED.** I found no geometric defect at the new roof-into-round-wall junction, or elsewhere, that should block sign-off at the 8.2 bar.
