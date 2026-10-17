# Kit baseline (step 0, before any refactor)

Built 2026-10-17 from the **current** kit (no kit code changed) with Blender 5.1.2 as a Python module, on the
reference machine (Ryzen 5 5600X, 16 GB). Each build went to a scratch path under `kit/baseline/0_baseline/<id>/`
through its output override (`KEEP_OUT`, `HUT_OUT`, `MILL_OUT`, `WATCH_OUT`, `HALL_OUT`, `LONG_OUT`, `V4_OUT`). All
seven scripts already had an override, so no build script was edited. The fingerprints are in
`kit/baseline/0_baseline/<id>.json`, produced by `tools/geom_hash.py`.

Build time is wall-clock seconds with three builds running at once (default `VILLAGE_CULL_PROCS`, 2 spawn workers
per build). Treat it as indicative only: it depends on which builds overlapped.

| Building | Triangles | Recorded | Drift | Geometry hash | UV hash | Mask hash | Build time (s) |
|---|---:|---:|---|---|---|---|---:|
| hilltop_keep | 1,166,874 | 1,166,874 | none | `b2f847333a2ec943` | `0c1f12176f0f1235` | `c7ddfbfe5d33f6d8` | 376 |
| wattle_roundhut | **878,355** | 876,619 | **+1,736 (+0.20 %)** | `7e5e7c2df5c4d367` | `9c0dd5aecb5d869c` | `794266c3463d1240` | 561 |
| tower_windmill | 1,146,243 | 1,146,243 | none | `89bf4a2a2c60e049` | `9f132597bb379825` | `04f7ade47b360102` | 230 |
| v1_stone_watchtower | 1,057,164 | 1,057,164 | none | `47e4208df661a5a9` | `9929b9e5101d3d5f` | `c8e787ab4b8e0bff` | 301 |
| v2_tiered_hall | 954,925 | 954,925 | none | `87ba64b7f9d4a746` | `15bb7bdc5ae3c360` | `e976015053c38848` | 496 |
| v3_longhouse_roundend | 478,877 | 478,877 | none | `73e77867096725ec` | `71215dfc7294b03a` | `3d5ef6b3dc13b4fc` | 416 |
| v4_mixed | 938,453 | 938,453 | none | `2e87caad61b68d34` | `a73b4ef99fd15564` | `b6c2768f3068057b` | 366 |

Every build finished without errors and saved its `.blend` and `decal_anchors.json`. Two builds that use
`mill_cap`, the mill and v4, log one harmless numpy `RuntimeWarning: All-NaN slice` from `components/mill_cap.py:194`.

## Cross-check against the delivered files

I also fingerprinted the delivered `.blend` next to each build script, opening each one read-only. Those
fingerprints are in `0_baseline/delivered/<id>.json`, and none of the delivered files was written.

- **Six of seven are identical** to their delivered file on all three channels (geometry, UV and mask) and in
  triangle count. Their `decal_anchors.json` files are byte-identical too: keep, mill, v1, v2, v3 and v4.
- **wattle_roundhut drifted.** The current kit builds a hut that differs from the delivered
  `buildings/wattle_roundhut/wattle_roundhut.blend` and from the CHANGELOG record (876,619). Its decal JSON is still
  byte-identical. `tools/geom_diff.py` limits the drift to the eave / roof ring:

  | Object | Delivered | Baseline | Delta | Changed channels |
  |---|---:|---:|---:|---|
  | HUT_eave_closure | 956 | 2,876 | +1,920 | geometry, uv, mask |
  | HUT_wall_plate | 1,874 | 1,716 | -158 | geometry, uv, mask |
  | HUT_roof_shingles | 110,162 | 110,140 | -22 | geometry, uv, mask |
  | HUT_rafters | 5,708 | 5,704 | -4 | geometry, uv, mask |

  **Cause (already documented, not merged):** `kit/changes/v4_mixed.md` (director must-fix 4) changed
  `components/conical_roof.py` `build_eave_closure(..., thickness=0.03)`. The eave closure became a closed band
  3 cm thick by DEFAULT, which adds the closure triangles. The closed band then occludes a little more of the wall
  plate, shingles and rafters in the hidden-geometry cull. The v4 builder recorded the hut at 878,355 (+1,736,
  +0.20 %) in its round-2/3 re-runs, which matches this baseline exactly. The producer CHANGELOG table still says
  876,619, and the delivered hut `.blend` was built before the change. `thickness=0` restores the old single-sided
  band.

  The drift is within the kit's ±0.5 % rule, but it is a default-behaviour change to an existing function, which
  the kit edit rules forbid. **This baseline records the drift and does not fix it.** Before a refactor step, the
  producer should decide which hut is the reference:
  - **878,355 (this baseline):** merge the v4 note and update the CHANGELOG table;
  - **876,619 (the delivered hut):** make the hut opt out with `thickness=0`, or make the 3 cm band opt-in for v4.

  Later refactor steps should compare against the hashes above (the baseline as the kit builds today).

## Later steps

- `1_consolidate/` (kit 1.8.0): all seven identical to this baseline (CHANGELOG 1.8.0).
- `2_guardrails/` (kit 1.9.0, guard-rails on by default): hut, mill, v1, v2, v4 identical; v3 changed on purpose
  (clearance fix, `WALL_Z` 2.75 -> 2.81, 483,508 triangles); the keep's first build differs only in the polygon ORDER
  of `KEEP_wing_wall_stones` (a pre-existing run-to-run artefact), and its rerun (`hilltop_keep_rerun.json`) matches
  this baseline exactly.  Details: CHANGELOG 1.9.0.
- `3_uvfix/` (kit 1.10.0, the queued UV fix: UV and Mask only): hut, mill, v1, v2, v3, v4 have exactly the step-2
  geometry hash, with new uv and mask hashes; the keep's geometry is identical but its `KEEP_turret_cap_shingles`
  polygon ORDER varies between builds (one of five 1.10 builds, `3_uvfix/pass1/hilltop_keep_rerun`, matches this
  baseline's `b2f847333a2ec943` exactly).  `3_uvfix/audit_before/` and `audit_after/` hold the UV measurements
  (`tools/uv_measure.ps1`), `3_uvfix/lookdev/` the look-dev re-renders.  `3_uvfix/pass1/` is the first pass (same
  geometry; timber U axis since changed).  Details: CHANGELOG 1.10.0.
- `4_verify/` (independent TD verification of kit 1.10.0, no kit code changed): all seven rebuilt; hut, mill, v1,
  v2, v3, v4 match step 3 on all three hashes, the keep matches step 0 exactly (`b2f847333a2ec943`) with new uv /
  mask hashes `968a9ef37e5872c4` / `37113e4c0fc8de83` (canonically identical to `3_uvfix/hilltop_keep_rerun`).
  Correction to step 3: in `3_uvfix/hilltop_keep` and `hilltop_keep_rerun2`, 88 polygons of `KEEP_turret_cap_shingles`
  have REVERSED winding (same vertex sets, flipped normals), not only a different polygon order
  (`4_verify/verify_tools/canon_hash.py` hashes geometry independent of vertex / polygon order).  Helper scripts
  and a README-only test recipe (`rubble_store/`) are in `4_verify/`.

## Reproduce / compare a later step

```
powershell -NoProfile -ExecutionPolicy Bypass -File blender_village/tools/build_baseline.ps1 -Step <step> [-Only id1,id2]
python blender_village/tools/geom_diff.py kit/baseline/<step>/<id>.json kit/baseline/0_baseline/<id>.json
```

`build_baseline.ps1` runs at most 3 builds at once, writes `kit/baseline/<step>/<id>/<id>.blend`, the build log
(`build.log` / `build.err`), `<step>/<id>.json`, `runner.log` and `build_times.json`. The step-0 run's
`build_times.json` shows `code: null`, a Windows PowerShell 5.1 `ExitCode` quirk that the added tool now avoids.
Success here was confirmed from each log's `saved ...` line.
