# Queued: kit UV fix (client-approved 2026-10-16; run after the variants workflow finishes)

Client's words: "Yes, queue the kit UV fix (wood grain along each piece's long axis, fix collapsed UVs on steps and thatch butts, no moss on walked steps) to run after the variants workflow finishes."

Found by the lookdev test (`lookdev/scripts/analyze_uv_grain.py`, `check_uv_stretch.py`; renders in `lookdev/renders/`).

## Scope (kit level, every building benefits)

1. **Wood grain along each piece's long axis.** Box UVs at about 1 UV unit per metre must stay, but for every timber-type piece (planks, boards, posts, beams, rafters, shingles, shakes, sail-wheel blades, tail-vane boards, door planks), U must run along the piece's long axis on every face. Slots: M_timber, M_timber_weathered, M_roof_shingle, M_roof_shake. Measured before the fix:
   - keep M_timber: 13 % of area along the long axis;
   - windmill apron shakes: 96 % across the slope;
   - windmill cap shingles: 7 % up-slope;
   - windmill blades: 61 % across the long axis.

   Target: 90 % or more along the long axis (shingles and shakes: up-slope) in `analyze_uv_grain.py`. Thatch is already right (96 % downhill), so keep it.
2. **No collapsed UVs.** Faces whose UV/3D area ratio is under 0.2 (they smear textures into streaks) must be re-projected:
   - keep threshold and step tops (64 % of their area), post-base tops (ratio 0), thatch course butt faces (dark vertical streak bands);
   - about 5 % of the keep cap shingles and 8 m² of the hut shingle edges.

   Target: under 1 % of any object's area below ratio 0.2 in `check_uv_stretch.py`.
3. **No moss on walked steps.** On threshold, step and door-sill pieces, set `Mask` B to 0.05 or less on the up-facing tops within each door's walking zone (clear width + 0.1 m each side, 1.5 m out), so the moss layer never lands where feet go. Keep B on step ends and outer edges.

## Rules

- UV and Mask only: geometry must not change. Every hero must rebuild to the same triangle count (keep 1,166,874, hut 876,619, windmill 1,146,243), and so must every variant (its count recorded after the variants run).
- Do it in the shared writers (`core.Acc` / `geom` / `tmplmesh` UV code, `mask.py`), with per-piece long-axis detection, not per building.
- After the fix: re-run `lookdev/scripts/apply_lookdev.py` on the keep, windmill and hut and compare against the first lookdev renders. Also send a textured render of one variant.
- The signed-off windmill snapshot `buildings/tower_windmill/signoff_kit_r08/` is never modified. The fixed windmill is a new build; tell the client before it replaces the snapshot.
