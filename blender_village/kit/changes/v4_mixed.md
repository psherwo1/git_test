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

## Round 2 (director v4 r1 must-fixes 1-4)

New modules / functions (only v4_mixed uses `compound` and `junctions`, so their new defaults change no other
building):

- **`components/junctions.py`**
  - `tower_field(T, P)`: signed plan distance of points from a round tower's face R(z).
  - `clip_at_tower(ob, T, inset, z_range)`: TRIMS (not buries) any placed single-user mesh at the surface
    R(z) - inset. Crossing edges are split exactly on the curved surface (bisection on the true field, so long
    battens at a grazing angle cut in the right place; `bmesh.utils.edge_split` interpolates UV and `Mask`), the
    crossed faces are split along the cut, and everything inside is deleted.
  - `trim_wing_at_tower(c, wing, tower, parts, z_range)`: junction step that trims a wing's parts;
    `ROOF_TRIM_PARTS` lists a RoundFrame roof's rafters, purlin rings, battens, wall plate, eave closure, blocker,
    starter, shingles and under-laps with their insets (2-3.5 cm).
  - `ride_fillet(acc, th, zb, T, bvh, h_up, out, lift, bury, taper, cove)`: a mortar flaunching whose section is
    FITTED to the roofing it lies on (ray casts along the tower normal at 1 / 3.5 / 6.6 / 11 / 13 cm). Where a cone
    rises away from the tower (a 39 deg valley on the upslope side), the old keep fillet sank under the shingles.
    This one fills the valley: crease 10 cm up the stone, toe 11 cm out and 5 cm over the highest butt peak, a skirt
    3 cm into the course, ends tapered.
  - `pole_plate_ledger(c, th, zb, T, tower, name, section, drop, let_in, trim_end, min_rise, n_corbels, ...)`: a
    keep-family `hewn_square` pole-plate (0.15 x 0.20 m) that follows the traced roof line under the rafter feet
    (drop = shingle stack + batten + rafter / cos(pitch)), in 3-4 straight lengths scarfed over 2-3 stone corbels.
    The corbels are linked duplicates of the TOWER wing's pooled corbel meshes; the ledger's back is let 3 cm into
    the masonry.
  - `roof_tower_flashing(..., ledger=True, trim=True, section="ride", fillet=(0.10, 0.11), lift=0.05,
    apron=(0.20, 0.24))` uses these by default. `section="flaunch"` keeps the r1 keep-family `flaunch_loop` path
    (`mortar_only=False` gives the stepped lead option). The end aprons are larger so the starter course and the
    eave closure end under them.
- **`compound.py`**
  - `dedupe_views(V, sep, seed_views)`: greedy, deterministic viewpoint thinning.
  - `compound_views(c, wings, max_views)`: the wings' overlapping rings are thinned, with priority review cameras >
    door views > near rings > far / crane rings. With the review viewpoints that `visibility_cull` always adds, at
    most `max_views` remain (300 for v4: 665 -> 300).
  - `compound_cull(c, wings, procs, max_views)`: allows `procs` spawn workers for this cull only (it sets
    `VILLAGE_CULL_PROCS` for the call). `build_compound` spec keys `cull_max_views` (default 260) and `cull_procs`
    (default 4). A dying worker falls back to one process through `core.visibility_cull`'s
    `ProcessPoolExecutor` / `BrokenProcessPool` path (already in core, CHANGELOG).

Existing module changed (director must-fix 4):

- **`components/conical_roof.py`, `build_eave_closure(..., thickness=0.03)`**: the eave closure is now a CLOSED band
  3 cm thick: the face at r_b faces OUT (seen under the eave between the rafter feet), an inner face faces the hut,
  and top, bottom and end caps close it. The inner top rises with the pitch so it is buried as deep as the outer
  top. `thickness=0` gives the old single-sided band. This adds about 1,900 triangles to the hut hero (+0.2 %).

## Hero re-runs (to scratch: KEEP_OUT / HUT_OUT / MILL_OUT)

Round 2: see the table at the end of this file.

Round 1: all three were run after the last edit to an existing module. They built without errors at exactly their recorded
triangle counts:

| Hero | Triangles (= record) | Notes |
|---|---|---|
| tower_windmill | 1,146,243 | clearance PASS, 106 anchors |
| wattle_roundhut | 876,619 | |
| hilltop_keep | 1,166,874 | |

### Round 2 hero re-runs (after the conical_roof edit; to scratch)

| Hero | Triangles | Record | Change |
|---|---|---|---|
| wattle_roundhut | 878,355 | 876,619 | +1,736 (+0.20 %): the closed eave closure (director must-fix 4) |
| tower_windmill | 1,146,243 | 1,146,243 | exact, clearance PASS |
| hilltop_keep | 1,166,874 | 1,166,874 | exact |

`core.py` round 2 edits change only how the spawn pool is managed:
- `_vis_pre_bpy_path` and `_vis_map_watched`: tasks are submitted with the pre-bpy `sys.path`, so a lazily started
  worker can import; a dead worker raises, and the cull falls back to one process instead of hanging;
- the workers are stopped instead of joined once every result is in.

The cull results are identical. The hut run predates both `core` edits; the mill and keep runs predate the last
one.

## Round 3 (audit of r2: ledger, open lead lips, build time, distinctness)

Only `components/junctions.py` changed (a kit module that only v4_mixed imports; no hero, no other variant uses
it). New functions and new optional parameters; `pole_plate_ledger` and every existing signature are unchanged.

- **New `rafter_feet(ob, T, inset, tol, link)`**: the cut feet of a rafter object trimmed at a round tower
  (`clip_at_tower`): the vertices on the cut surface, clustered into one foot per rafter -> [(centroid, z_min)].
- **New `rafter_bearings(c, roof, tower, name, part, inset, pad, let_in, head_clear, ends, end_clear, ...)`**: a
  STEPPED bearing instead of the sloping ledger. Every rafter foot cut at the tower face that lands OUTSIDE the roof
  wing's wall head gets its own short LEVEL keep-family `hewn_square` pad (0.40 x 0.15 x 0.11 m, back 3 cm in the
  masonry, top at the rafter's underside at the stone face) on a stone corbel under its middle (linked duplicate of
  the tower wing's pooled corbel meshes). So the bearing steps with the roof line, one level length per rafter,
  every visible end has a corbel, and nothing slopes. Feet whose pad would reach the wall head (the outer radius of
  `<P>_wall_plate` / `<P>_eave_closure`, and the abutment-post faces at `r_line + 0.15`, plus `head_clear`) bear on
  the wall plate and get nothing, so no bearing can pass through the plate, the eave closure or the posts.
  Objects `<P>_<name>_pads`, `<P>_<name>_corbel_###` (an empty pads accumulator builds no object).
- **`roof_tower_flashing(..., bearing="corbels", bearing_kw=None, apron_closed=True)`**: new parameters.
  `bearing="corbels"` (default) uses `rafter_bearings`; `bearing="ledger"` is the r2 `pole_plate_ledger` path,
  unchanged. `ledger=False` still switches the bearing off.
- **`end_apron(..., closed_lip=False)`**: new parameter. `True` builds the drip lip as a CLOSED bent strip with its
  own vertices (four-sided section swept along the edge, both end caps), its root tucked 3 mm up into the plate's
  bottom edge instead of welded onto it. `roof_tower_flashing` passes `apron_closed=True`, so
  `<P>_<name>_fillet` (mortar + lead) has 0 non-manifold edges (r2: 28 on `M_lead`). `False` is the r2 open strip.

No other kit file was touched.

### Round 3 hero re-runs (after the last junctions.py edit; to scratch)

| Hero | Triangles | Record | Change |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 | exact |
| wattle_roundhut | 878,355 | 878,355 (r2) | exact |
| tower_windmill | 1,146,243 | 1,146,243 | exact |

## Round 4 (director r3 must-fix: cull holes at the house wall head; producer note 15: at most 1,000,000 triangles)

Every existing-module edit is a new optional parameter or frame attribute whose default keeps the old behaviour.
`compound.py` is imported only by v4_mixed, so its default change reaches no other building.

**Cull holes (producer note 6) -- `compound.py`:**
- `Wing(..., eye_heights=(1.0, 1.65))` (new, default on). `compound_views(max_views=...)` now puts each wing's near
  EYE-LEVEL rings -- every `ring_n` station at r + 0.4 m and r + 1.5 m, z = `eye_heights` -- into the never-thinned
  head group with the review cameras and the door views. Only the remaining near heights and the far / crane rings
  are thinned. `eye_heights=()` is the r3 behaviour. (Also fixed: the head / rest split now follows the
  solid-body filter row by row instead of by count.)
- New `wall_head_views(w, wings, n=48, eye=1.65, parts=WALL_HEAD_PARTS)`: for a round wing whose eave lip is BELOW
  its wall head (frame `Z_EAVE < PLATE_TOP`: a steep cone on a short overhang) three eye-height rings (under the
  eave at `R_WALL + 0.45` and outside the lip at `R_EAVE + 0.25`, `n` stations each; about 6 m out at
  `R_EAVE + 2.9`, `2n` stations, for the grazing view under the lip past a neighbouring wing) are added as per-target
  viewpoints
  (`core.visibility_cull(extra_by_target=...)`, existing parameter) for the wing's `daub`, `wall_plate`, `posts`,
  `wattle_rods`. Nothing for drums, keeps or a hut whose lip is above its wall head.
  A fourth BAND-GUARD ring (2n stations, 0.2 m in front of the wall at the band's mid height, kept unless inside a
  neighbour's solid with no margin) covers the re-entrant corner beside a neighbouring wing.
- New `wall_head_band(w)`, `split_band(ob, z0, z1, center, inward=-0.2, solids=())`, `join_band(ob, ob2)`: the
  band PROTECTION. Before the cull the outward polygons of the wing's `WALL_HEAD_PARTS` whose centres lie between the
  eave lip - 5 cm and the plate top + 2 cm (and outside every other wing's solid) are split into a temporary
  `<name>__band` object (still an occluder, not a target); after the cull they are merged back and the split seam
  is welded (coincident boundary vertices only). A grazing sliver of a band face beside a post could miss every
  sample point of `core.visibility_cull` even with the extra stations (director probe 5: 1 ray at 6 m, house az
  45 deg); with the protection the band cannot be opened at all.
- `compound_cull(..., wall_head=True)` (new) and `build_compound` spec key `cull_wall_head` (default True).

**Door-head gaps on a steep cone (seen by the eye-level probe) -- frame attributes, absent = unchanged:**
- `components/doors.py` `build_door`: `g.DOOR_INFILL_DECK` -- the infill boards over the lintel run up to just
  under the batten deck (`+ (2 RAFT_R + BATTEN_T) / cos(pitch) - 3.5 cm`) instead of 2 cm into the rafter line,
  each with a thin lath behind it covering the board gap. On the 58 deg cone the old top left a ~0.26 m slot between
  the rafters over the door.
- `components/conical_roof.py` `build_eave_closure`: `g.EAVE_CLOSURE_DOOR_HALF_DEG` -- the closure runs on over the
  door sector behind the infill, leaving +-that many degrees on the door axis (default: stop 2 deg inside the
  door-flanking wall posts). The cheek opening beside the infill looked into the eave void on a small plan.

**Triangle budget (producer note 15) -- new module and frame attributes, absent = unchanged:**
- **New `village_kit/lod.py`**: height-banded grid LOD for template-instanced pieces. `tmpl_lod(g, z, step, parts,
  keep, keep_r, keep_z, bands)` (a STEP, run first in a wing) registers a rule; every piece of a listed BatchAcc part
  whose lowest point is above `z` (and outside the entrance zone: plan radius `keep_r` round the frame's door, below
  `keep_z`) is re-meshed on every `step`-th grid line of its `tmpl_box` template, `bands=[(z_b, step_b)]` coarser
  higher up. Both outer and both arris lines of every axis and all outward (y) lines are kept, and the kept vertices
  are the piece's own shaped vertices, so outline corners, arrises, size and placement are unchanged -- only the face
  grid between them is thinner. Part names ending in `*` match pooled variants (`pool_corbel*`, local coordinates,
  thinned at any z). `coarse_template(T, step)`, `register`, `unregister`, `tmpl_lod_report(g)` (logs pieces and
  triangles saved per part), `DRUM_LOD_PARTS`.
- `tmplmesh.py`: module global `LOD_HOOK = None` and `BatchAcc.add(..., _lod=True)`: when a rule is registered,
  `add` hands the batch to the hook first. With no rule (every hero, every other variant) nothing changes.
- `components/daub.py` `build_daub`: `g.DAUB_GRID = (H_S, H_Z, H_CR[, h_fine])` -- the coat grid under the note-11
  rule (default 0.03 / 0.03 / 0.02 / 0.0075 m).
- `components/plinth.py` `build_plinth`: `g.PLINTH_DENSE` -- mesh-density factor of the plinth boulders OUTSIDE the
  entrance zone (note-11 relief >= 1.5 cm); the entrance stones keep the hero density.
- `components/conical_roof.py` `build_shingles`: `g.SH_RING_STEP` -- shingle cross-section rings above the butt
  every `SH_RING_STEP` m instead of 0.07 m (the six butt rings are kept).

v4_mixed sets them with the existing `compound.configure` step and `lod.tmpl_lod`: drum family LOD above 0.6 m (every
3rd line above 3.0 m) incl. the cornice corbel pool; `DAUB_GRID=(0.075, 0.07, 0.035, 0.0125)`, `PLINTH_DENSE=0.55`,
`SH_RING_STEP=0.21`, `DOOR_INFILL_DECK=True`, `EAVE_CLOSURE_DOOR_HALF_DEG=1.0`; existing parameters only:
`drum_wall_core(n_th=96)` and the mill wing's cull targets + `door_leaf`, `interior`, `door_surround`,
`tower_boards`, `cap_frame` (est_hidden_pct 14.8 -> 13.2 %); `cull_max_views` 230 -> 300.

### Round 4 hero re-runs (after every edit to an existing module except compound.py, which no hero imports)

| Hero | Triangles | Record | Change |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 | exact |
| wattle_roundhut | 878,355 | 878,355 (r2/r3) | exact |
| tower_windmill | 1,146,243 | 1,146,243 | exact |

Kit edits to existing modules this round: `compound.py`, `tmplmesh.py`, `components/daub.py`, `components/plinth.py`,
`components/conical_roof.py`, `components/doors.py`. New: `lod.py`.
