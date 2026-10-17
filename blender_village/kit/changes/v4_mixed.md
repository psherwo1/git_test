# v4_mixed: kit changes (variant builder, round 1)

Variant: `buildings/variants/v4_mixed/build_v4_mixed.py`, the MILL-HOUSE (a daub roundhouse built against a small
stone tower mill). Recorded here for the producer to merge into `../CHANGELOG.md` (proposed version 1.7.0).

## New modules (no existing function changed signature or default behaviour)

- **`village_kit/compound.py`**: one building from SEVERAL family frames. `Wing(name, frame, prefix, params, steps,
  at, yaw_deg, decals, decal_validate, cull_targets, reach, door, view_heights, crane_heights, solid)` and
  `build_compound(spec)`: each wing is built at the origin with its own family components (exactly the calls a hero
  recipe makes), parked, then placed (single-user meshes get the transform applied, pooled linked duplicates keep a
  placed matrix, decal anchors move with the wing); junction steps `fn(c, **kw)` run on the placed wings; ONE
  hidden-geometry cull over every wing's targets with every wing's actor / door / crane rings (viewpoints inside
  another wing's solid body dropped) plus the whole building's review cameras; the merged anchors are re-audited on
  the whole building (`anchor_audit.audit_anchors`, drop) and thinned per type to `decal_max` (deterministic).
  Step helpers: `configure(g, strict=False, **attrs)` (frame flags such as `ENTRANCE_R8`), `patches_by_azimuth(g,
  patches)` (RoundFrame daub patches by azimuth, to keep them off the side a neighbour covers), `thin_anchors`.
- **`components/junctions.py`**: junction pieces between bodies of different families, from generic body
  descriptions (`tower_of`: centre + battered face radius R(z) of a DrumFrame; `round_wall_of`: a RoundFrame wall).
  - `roof_tower_flashing(c, roof, tower, roof_parts, name, steep_deg, bury, lift, mortar_only, end_aprons, seed)`:
    traces the true roof-top / tower-face line by ray casts on the built roofing (`trace_roof_on_tower`, short
    misses through shingle joints interpolated), lifts it over the highest shingle (`_smooth_up` + `lift`) and closes
    it with the KEEP family's `thatch.flaunch_loop` (continuous mortar flaunching, or mortar + stepped lead where
    steeper than `steep_deg`); `end_apron` lead plates over the cut eave lips at the run ends. Object
    `<P>_<name>_fillet`. Moss anchors in the roof valley.
  - `wall_tower_abutment(c, wall, tower, name, post, into, z_mid, seed, pointing)`: at both plan intersections of a
    round wall's coat with the tower face a KEEP-family `hewn.hewn_square` post (plinth to wall plate) slid until its
    tower-side corner is `into` m inside the masonry, plus a mortar pointing bead along the post / stone seam
    (following the batter). Objects `<P>_<name>_posts`, `<P>_<name>_pointing`. Damp anchors at the post feet.
- **`components/round_apex.py`**: `turned_apex(g, hat_r, hat_pitch_deg, scale, lean_deg, lean_dir, seg, clear)`:
  the KEEP family's turned finial (`finial.turned_finial`) over a fitted lead hat (`finial.lead_hat(cover=...)`) on
  ANY RoundFrame cone; objects `<P>_cap_collar` / `<P>_finial` (the names `round_decals` looks for); sets
  `g.COLLAR_R`.

## Bug fixes in existing modules (behaviour identical for every existing building)

- `components/conical_roof.py`, `build_eave_closure`: the roof objects were looked up as the literal
  `"HUT_roof_shingles"` / `"HUT_roof_starter"`; now `f"{g.prefix}_roof_..."` (identical for the hut, whose prefix is
  HUT; any other RoundFrame prefix crashed with a KeyError).
- `components/rotor_checks.py`, `rotor_clearance` / `tail_clearance`: a mill built WITHOUT raking props crashed
  (`clr[P + "_props"]` KeyError, `np.concatenate` of an empty part). Absent / empty parts are now skipped (no
  constraint). Identical for the mill hero (it has props).
- `components/tail_vane.py`, `tail_boom`: the iron bands sit at fixed cap-local x' (-1.92 ... -5.92); a boom shorter
  than the hero's (`boom_end` > -6.0) left the outer band(s) and their bolts floating past the boom end. Bands within
  10 cm of / beyond the boom end are now skipped. The hero (`boom_end` -6.08) keeps all five bands; the mill
  KIT_VARIANT (`boom_end` -5.6) loses its floating -5.92 band.

## Hero re-runs (to scratch: KEEP_OUT / HUT_OUT / MILL_OUT)

All three were run after the last edit to an existing module. They built without errors at exactly their recorded
triangle counts:

| Hero | Triangles (= record) | Notes |
|---|---|---|
| tower_windmill | 1,146,243 | clearance PASS, 106 anchors |
| wattle_roundhut | 876,619 | |
| hilltop_keep | 1,166,874 | |
