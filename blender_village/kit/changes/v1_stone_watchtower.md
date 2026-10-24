# Kit changes: v1_stone_watchtower (variant builder, round 1, 2026-10-16)

Recipe: `buildings/variants/v1_stone_watchtower/build_v1_stone_watchtower.py` (prefix `WATCH`).

## New modules (nothing existing changed by them)

- **`components/tower_roof.py`** -- the head of a round stone tower, usable by any drum-family building and (the
  roof) by any round wall head:
  - `corbelled_parapet(g, height=0.85, proj=0.24, coping_h=0.12, seed=None, rubble=None)`: coursed rubble parapet
    set OUT on the drum's corbelled cornice (face `proj` beyond the drum face), bottom course bedded 3 cm into the
    cornice cap, dressed coping ring (`COPING_PROFILE`, top bed 0.34 m deep), continuous mortar backing 2.2 cm
    behind the faces.  Objects `<P>_parapet_stones / _parapet_coping / _parapet_mortar`.  Publishes
    `g.WALL_HEAD = dict(r_face, z_top, r_bed_in, coping_out)`.
  - `round_tower_roof(g, pitch_deg=52, eave_out=0.62, bell_deg=12, bell_len=0.85, collar_r=0.62,
    collar_pitch_deg=50, finial_tip=None, n_raft=None, cone_age="kit", plate_in=0.14, clear=0.07, seed=None)`:
    conical chunky-shingle roof with a bell-cast eave on `g.WALL_HEAD` (or the drum's cornice top).  It runs the
    hut's roof modules unchanged (`conical_roof.build_rafters / build_purlins_battens / build_shingles`,
    `round_wall.wall_plate`, `finial.finial`) on a sub-frame built by `roof_frame(...)`: a `frame.RoundFrame` whose
    cone profile is replaced by `_bell_profile` (pitch flattening by `bell_deg` over `bell_len`), whose eave height
    is solved so the wall plate beds 1.2 cm into the wall head, and which shares the building's collection, pools and
    decal anchors.  The plate moves toward the face until the rafter undersides clear the coping arris by `clear`.
    Own junction pieces: `_roof_deck` (continuous sarking deck on the rafters under the battens, lip to apex,
    facing out; over the eave overhang a closed 12 mm board slab with a soffit face and an eave edge, so no
    sunlight leaks through the overhang's shingle joints onto the wall head -- the backing for every culled /
    slipped shingle) and `_eave_closure` (mortar band between the rafter feet, plate top into the shingle stack,
    facing out; the generic form of `conical_roof.build_eave_closure`, which hard-codes `HUT_` names and faces in).
    Publishes `g.ROOF`.
  - `drum_ceiling(g, z=3.45, inset=0.775)`: boarded ceiling disc closing the hollow drum above the interior seen
    through the door (`<P>_ceiling`).
  - `tower_hidden_cull(g, targets=TOWER_CULL_TARGETS, procs=3)`, `tower_views(g)`: note 6 with the drum views plus
    eave-level / crane rings round the roof; only backed pieces are culled (drum stones / mortar skin / dressed work
    over the wall core, parapet stones / coping over the parapet backing, roof timbers / shingles over the deck);
    missing objects are skipped.  Culling the 0.8 M-triangle drum rubble takes ~10 min on 3 workers.
- **`components/tower_decals.py`** -- `round_tower_decals(g, seed=7410)` and `round_tower_decals_gated(g, ...)`:
  note-11 anchors for a rotor-less stone tower (damp / moss foot, lichen on string course and slit sills, streaks
  below sills / string course / coping drip, rust under the door iron, soot over the door and slits, cracks at the
  openings / settlement / under the band, grime, repairs over the lower and upper shaft, render beside the door,
  north-roof moss) through the drum family's three gates (snap, validate, audit; asserts 0 failures, 40-120).

## Optional parameters added to existing modules (defaults keep the old behaviour)

- `components/drum_frame.py`
  - `DrumFrame.WIN_DZ = None` (per-window height offsets) and `DrumFrame.BATTER_TOP = 4.6` (new attributes, so
    `g.set()` accepts them).
  - `R_out(g, z)`: the clip height is `getattr(g, "BATTER_TOP", 4.6)` (was the literal 4.6).
  - new helper `win_dz(g)` (zeros when `WIN_DZ` is None).
  - `hw_window(g, z, dz=0.0)`; `derive()` builds the window openings with each window's `dz`;
    `inside_clear()` shifts each window by its `dz`.
- `components/drum_wall.py`
  - `round_stone_drum(..., window_z=None, batter_top=None)`: `window_z` = one slit bottom height per window
    (slits stacked up a tall drum); `batter_top` = batter height, `"full"` = the whole drum.  `arcade=dict(n=0,
    ...)` now builds a drum without an arcade.
  - `build_slit_windows`: every height offset by the window's `dz`; `WIN["fw"]` indexed modulo its length (any
    number of windows; identical for the mill's two).
  - `build_base`: the "no arcade" ashlar zone is skipped when it is empty (`ARCH["zs"] <= Z_BAND1 + 0.05`).
  - `build_band_cornice_and_finish`: the arcade-backs report is skipped when there is no arcade (it raised on an
    empty list).
  - `_drum_openings`: windows shifted by their `dz`.

## Hero re-runs (to scratch, KEEP_OUT / HUT_OUT / MILL_OUT, after the last edit to an existing module)

| Building | Triangles | Record | Anchors |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 (0.0 %) | 116 |
| wattle_roundhut | 876,619 | 876,619 (0.0 %) | 98 |
| tower_windmill | 1,146,243 | 1,146,243 (0.0 %) | 106 |

All three built without errors.  Later edits touched only the two new modules (`tower_roof.py`, `tower_decals.py`),
which no hero imports.

---

# Round 2 (2026-10-16): lookout windows, parameterised slits, plain string course, fast drum cull

## New functions (nothing existing changed by them)

- **`components/drum_frame.py`**
  - `window_spec(clear_w=0.16, clear_h=0.55, sill=1.30, kind="slit", fw=None, lintel_h=None, course_h=0.30,
    splay=0.22, room=1.5)`: a drum window of ANY size as a spec dict. Jamb courses (about `course_h` each, faces
    alternating), sill and lintel widths, lintel height and the rubble keep-out bands (`zb`, `zt`, `hw_sill`,
    `hw_jamb`, `hw_lintel`) are all derived from the clear size. `kind="slit"` gives the splayed, closed
    embrasure. `kind="lookout"` gives a straight reveal and a closed dark room (see `lookout_room`).
  - `win_list(g)`: every window as `(azimuth, spec, dz)`. Without `g.WIN_SPEC` it returns `g.WIN` and `win_dz()`
    (the mill's numbers, unchanged).
  - `WINDOW_FW`: jamb face widths per kind.
- **`components/drum_band.py`**: `string_course(g, part, rng, z0, z1, proj=0.07, drip=0.014, seg, skip)` and
  `string_course_profile(h, proj, drip)`. A plain dressed projecting string course with a vertical face, a weathered
  top and a drip lip, with no balusters. It is built by `drum_wall.profile_course`.
- **`components/drum_wall.py`**: `lookout_room(g, th, W, Rz, wall=0.66, side=0.30, head=0.30)`. A straight mortar
  reveal through the wall, then a closed dark room `W["room"]` m behind the face (boarded floor flush with the sill,
  boarded ceiling, plastered sides, back and inner face), in object `<P>_lookout_rooms`, which is not culled
  (note 6 blocker). Also `_quad()`, a helper.
- **`components/tower_roof.py`** (round-1 module):
  - `drum_precull(g, targets, slack, margin, inward, gap)`: an analytic, ray-free removal of drum masonry faces
    wholly behind the continuous wall core, plus inward faces behind the mortar skin. It never touches faces near
    openings.
  - `drum_view_masks(g, cen, views)`: per polygon, the views whose sight line is not certainly blocked by the
    closed wall-core cylinder.
  - `drum_ray_cull(g, targets, views, procs)` and `_drum_vis_worker`: the probes and hit rule of
    `core.visibility_cull`, with each polygon tested only against its unblocked views. A polygon with none left is
    deleted with no ray. It reuses `core._vis_spawn_pool` on Windows.
  - `tower_views_lite(g)`: eye and knee rings, a first-floor / lookout ring, a crane ring, door close-ups and
    review cameras.
  - `tower_head_views(g)`: reduced rings round the roof (below and above the eave, crane).
  - `tower_hidden_cull(..., precull=DRUM_PRECULL, lite=DRUM_PRECULL)`: the new optional parameters. Drum masonry
    goes through precull first. Then every target (drum, parapet, roof) runs in ONE `drum_ray_cull` pass on
    `tower_views_lite + tower_head_views` (one BVH and one worker pool). A sight line is blocked when its chord
    inside the closed core cylinder lies between 5 cm and the cornice. `precull=(), lite=()` gives the round-1
    behaviour.
- **`components/tower_decals.py`**: window anchors (sill lichen, sill streaks, soot over heads, head cracks) are
  derived from each window's spec, so slits and lookouts of any size get them. The anchor beside the door is now
  `repair_patch` on stone; `plaster_patch` stays only on the plastered passage.

## Optional parameters / attributes added to existing modules (defaults keep the old behaviour)

- `drum_frame.DrumFrame`: `WIN_SPEC = None`, `BAND_STYLE = "balustrade"` (new attributes).
- `drum_frame.hw_window(g, z, dz=0.0, w=None)`: `w` is a window spec. With `None` it uses `g.WIN` and the literal
  1.17 / 2.04 / 0.31 / 0.37 bands, so the mill's slit is unchanged. `derive()` and `inside_clear()` iterate
  `win_list()`.
- `drum_wall.build_slit_windows`: per-window spec through `win_list()`, with any number of jamb courses
  (alternating faces). The sill and lintel sizes and heights come from the spec, with `.get` defaults equal to the
  old literals. A `kind="lookout"` window builds `lookout_room` instead of the splayed embrasure.
- `drum_wall.round_stone_drum(..., window_size=None, lookouts=None)`:
  - `window_size=(clear_w, clear_h)` gives every slit a `window_spec`.
  - `lookouts=dict(n, az0 | az, w, h, sill, room)` adds lookout windows.
  - `zones=dict(string=(z0, z1))` selects the plain string course (`BAND_STYLE="plain"`).
  - `arcade=dict(n=0)` alone now means "no arcade", so the dummy `z_sill` / size values are no longer needed.
- `drum_wall.build_band_cornice_and_finish`: `BAND_STYLE == "plain"` calls `drum_band.string_course`. Otherwise
  the old balustrade band code runs unchanged (re-indented only).
- `drum_wall.wall_core_backing`: the inner ring is holed behind `kind="lookout"` windows only. When there are none,
  `keep=None`, as before.
- `drum_wall._drum_openings`: iterates `win_list()`.

## Round 2 hero re-runs (to scratch: MILL_OUT, HUT_OUT and KEEP_OUT, after the last edit to an existing module)

| Building | Triangles | Record |
|---|---|---|
| tower_windmill | 1,146,243 | 1,146,243 (0.0 %) |
| wattle_roundhut | 876,619 | 876,619 (0.0 %) |
| hilltop_keep | 1,166,874 | 1,166,874 (0.0 %) |

All three built without errors. After the mill re-run, I edited only `tower_roof.py`, which no hero imports.
The `drum_frame`, `drum_wall` and `drum_band` edits all came before all three runs.
`buildings/variants/v4_mixed` also calls `round_stone_drum` with the mill's parameters. That goes through the same
default paths, but I did not re-run it.

## New module: `components/square_cabin.py` (client direction: square timber cabin on the drum)

`square_cabin(g, side=5.4, height=2.30, z_bed=None, bed_r=None, bearers=(-1.6, 0.0, 1.6), n_joists=7,
struts=True, strut_drop=1.25, n_open=2, open_w=1.10, open_sill=1.00, open_h=0.90, pitch_deg=48.0,
eave_out=0.50, exposure=0.34, cap_r=0.62, seed=None)`. It builds a square timber lookout cabin on any wall head.
`z_bed` / `bed_r` default to the drum's cornice top and cornice cap.

- **Floor:** a mortar bed disc closes the wall head. Bearers along Y rest on the head, joists along X sit on the
  bearers, and a plank deck goes on top.
- **Brackets:** a dragon beam runs out to every corner. Each is carried by a raking knee strut in the diagonal
  plane, whose foot sits on a dressed corbel pad set into the wall face.
- **Walls:**
  - A framed wall: sill and top plate half-lapped at the corners, corner posts, jamb posts, a breast rail with a
    sill board, and a head beam.
  - Vertical plank infill.
  - `n_open` open lookout openings on every side.
  - A boarded ceiling at the plate.
- **Roof:**
  - A square pyramid at `pitch_deg`, with rafter tails and hip rafters on the plate.
  - A closed sarking deck (soffit and eave edge).
  - A starter board, then coursed kit shingles (`shingles.shingle_mesh`, `SHINGLE_VARIANTS`, `SIZE_TABLE`) trimmed
    at the hips, with hip boards over them.
  - A square lead apex cap that is lifted clear of every shingle and hip-board vertex beneath it, and
    `finial.turned_finial` on top.
- **Objects:** `<P>_cabin_floor`, `_struts`, `_corbels`, `_bed`, `_frame`, `_boards`, `_ceiling`, `_roof_frame`,
  `_roof_deck`, `_shingles`, `_hips`, `_lead` and `_finial`.
- **Publishes:** `g.CABIN` and `g.ROOF`, which `tower_views`, `tower_head_views` and `round_tower_decals` read.

This is a new file only: no existing module changed for it.

## Hero re-runs for round 2

All three were re-run to scratch after the last edit to an existing module (`drum_frame` / `drum_wall` /
`drum_band`). All are identical to their records:
- tower_windmill: 1,146,243
- wattle_roundhut: 876,619
- hilltop_keep: 1,166,874

Later edits touched only `tower_roof.py` (the cull functions, all new), `tower_decals.py` and `square_cabin.py`,
which no hero imports.

---

# Round 3 (2026-10-16): windows negotiate with fixed courses, no anchors on blockers, cabin anchors

## New functions / names (nothing existing changed by them)

- **`components/drum_frame.py`**
  - `fit_window_courses(W, beds_above=(), tops_below=(), min_gap=0.20, lintel_grow=2.2, label)`: a drum window
    negotiates with the FIXED courses round it. If the gap between its keep-out top (`zt`) and the bed of the next
    fixed course above is under `min_gap` (one real rubble course), the lintel grows to bed directly under the
    course (up to `lintel_grow` x nominal); if that is not enough the window rises so its lintel beds under the
    course; a keep-out running INTO a course lowers the window. The same rule applies under the sill against a
    fixed course below (the window drops so its sill beds on it). Returns `(spec, note)`.
  - `drum_window_spec`: an unambiguous alias of `drum_frame.window_spec` (director nice-to-have: three kit
    functions are called `window_spec`).
- **`components/tower_decals.py`**
  - `BLOCKER_PARTS = ("_lookout_rooms", "_ceiling", "_cabin_ceiling")`, `blocker_hit(g, hit, exclude)`,
    `drop_blocker_anchors(g, probe, exclude)`: note-6 blocker meshes (and `<P>_interior` above the door crown)
    are never decal surfaces.
  - `cabin_decals(g, da, probe, rng)`: anchors of a `square_cabin` crown read from `g.CABIN` (water streaks below
    each lookout's sill board on the plank wall, and below each knee-strut corbel pad on the stone face).

## Optional parameters / behaviour added to existing modules

- `drum_wall.round_stone_drum(..., course_fit=True)`: only read inside the `window_size` / `lookouts` branch (round
  2, used by no building but this one), so the mill and `v4_mixed` (which pass neither) are unchanged. Every such
  window goes through `fit_window_courses` against the string-course bed and the cornice bed (`Z_CORN0`) above
  and the string-course top below; `min_gap` = the plain rubble's `hr[0] + hr[1]`. Each change is logged
  (`course fit: ...`). `course_fit=False` gives the round-2 placement, a number sets `min_gap`.
  - This tower: slit 2 (az -60) rises 0.255 m so its lintel beds under the string course.
  - The round-2 lookout crown (`WATCH_KIT_VARIANT=lookout`): the four lookout lintels grow 0.24 -> 0.385 m and
    bed under the cornice (the 0.145 m pinner zipper is gone); slit 2 rises as above.
- `drum_frame.drum_finish(g, checks=True)`: when no rotor was built (`wheel_blades` part empty) the rotor
  clearance checks skip themselves with a log line. The mill builds its rotor, so it is unchanged; recipes no
  longer pass `checks=False`.
- `tower_decals.round_tower_decals(g, seed, exclude=BLOCKER_PARTS)` / `round_tower_decals_gated(..., exclude=)`:
  the three repair-patch scatters accept only exterior hits (`wall_scatter(accept=)`), blocker anchors are dropped
  before the gates, `validate_anchors(exclude_objects=)` rejects them, and a final assert checks none remain.
  `cabin_decals` runs when `g.CABIN` exists. (Only v1 uses this module.)
- `square_cabin.square_cabin`: publishes `g.CABIN["pads"]` (strut corbel pads); a round lead sleeve (in
  `<P>_cabin_lead`) dresses the finial's foot into the pointed lead cap, which before left the finial perched on
  the apex point with a visible gap. (Only v1 uses this module.)

## Round 3 hero re-runs (to scratch: MILL_OUT, HUT_OUT, KEEP_OUT, after the last edit to drum_frame / drum_wall)

| Building | Triangles | Record |
|---|---|---|
| tower_windmill | 1,146,243 | 1,146,243 (0.0 %), rotor checks still run (min blade gap 0.060 m PASS) |
| hilltop_keep | 1,166,874 | 1,166,874 (0.0 %) |
| wattle_roundhut | 876,619 | 876,619 (0.0 %) |

All three built without errors after the last `drum_frame` / `drum_wall` edit. Later edits touched only
`square_cabin.py`, `tower_decals.py` and `tower_roof.py`, which no hero imports.

## Fix forced by a concurrent kit change

`core._vis_spawn_pool` returns a `concurrent.futures.ProcessPoolExecutor` since 20:52 (another builder's edit).
`tower_roof.drum_ray_cull` called `pool.close()` / `join()` on it and its first round-3 deliverable build died at the
end of the cull. Now `tower_roof._close_pool(pool)` closes either kind, the executor's lazy `map` is consumed inside
the `try` (`list(...)`), and a broken pool falls back to one process for the remaining targets.

---

# Round 4 (2026-10-16): reusable bell-cast pyramid roof, closed crown bed, true finial tip

## New module (nothing existing changed by it)

- **`components/pyramid_roof.py`**: `pyramid_roof(g, p_wall, z_plate, name="pyramid", sides=4, rot_deg=-90.0,
  cx=0.0, cy=0.0, pitch_deg=48.0, eave_out=0.50, bell_deg=0.0, bell_len=0.70, kick=0.0, kick_len=0.60, sag=0.0,
  exposure=0.34, cap_r=0.62, finial_scale=0.80, finial_lean=0.5, rafter_step=0.60, t_deck=0.025, seed=None,
  rng=None)`. It is extracted from `square_cabin`'s inline straight pyramid (round-3 lines 199-347) and generalised.
  - Any regular polygon (`sides` >= 3, rotation and centre) on any wall head. The deck underside passes over
    `z_plate` at the wall-face apothem `p_wall`.
  - `PyramidSurface`: the pitch profile along the apothem, with a bell-cast eave (`bell_deg` flattening over the last
    `bell_len` m of slope, cosine-blended, so the hip lines come out concave in elevation), upturned hip corners
    (`kick`) and a dish between the hips (`sag`). It exposes `under` / `top` / `normal(k, u, p)`, `p_of_m` / `m_of_p`
    and `apothem`.
  - Parts, all following the curved surface:
    - deck (top, soffit and eave edge, with denser rows through the bell);
    - rafter tails and hip rafters, swept along the surface;
    - starter board, then coursed kit shingles bent onto the surface (`shingle_mesh`, `SHINGLE_VARIANTS`,
      `SIZE_TABLE`) and trimmed at the hips;
    - **one closed saddle per hip**, swept along the hip line. This replaces the two separate boards that left an
      open V slot along every hip (round-3 j13).
    - a polygonal lead cap lifted clear of the covering, a lead sleeve, and `finial.turned_finial(scale=finial_scale)`.
  - It returns a record (`objs`, `surface`, `r_eave`, `z_eave`, `z_eave_corner`, `apex`, `cap_top`, `collar_drip`,
    `tip`, ...). **`tip` is the max z of the built finial mesh**, not a formula.
  - Objects: `<P>_<name>_roof_frame / _roof_deck / _shingles / _hips / _lead / _finial`. `name="cabin"` gives the
    round-3 object names, so cull targets and probes are unchanged.
  - `bell_deg = kick = sag = 0` reproduces the round-3 straight pyramid. A scratch build with round-3 cabin parameters
    gave the identical eave (11.11 m, r 3.16), apex 14.66, 448 shingles / 43,610 shingle polygons and the identical
    deck, lead and finial bboxes. The only change is the hip saddles.

## `components/square_cabin.py` (existing module; only v1 imports it)

- The roof is no longer built inline. `square_cabin` calls `roof_fn or pyramid_roof` with `p_wall` (wall face) and
  `z_plate` (plate top), `name="cabin"` and its own rng (so the round-3 shingle sequence is kept). The new parameters
  are:
  - `roof=dict(...)`: overrides for the roof module, e.g. `bell_deg`, `bell_len`, `kick`, `sag`;
  - `roof_fn`: any roof module that returns `pyramid_roof`'s record;
  - `finial_scale=0.80`: was a hard-coded 1.4, which gave 2.0 m above the cap. 0.8 gives 1.14-1.16 m (bible 1.5:
    0.9-1.3).
  - `g.CABIN["tip"]` and `g.ROOF["tip"]` now come from the built mesh. `g.CABIN` also carries `bed`, `bed_r`,
    `bearers` and `roof` (the record).
- `bed_fill=True` (new, default on): a closed timber rim ring on the wall head (r `bed_r - 0.18` .. `bed_r - 0.06`).
  It is bedded 1 cm into the cornice cap and runs up to 4 mm under the deck, as blocking between the bearers and
  between the joists. It goes in `<P>_cabin_floor`. Open framing remains only on the cantilevers outside the drum.
  Level ray test at z 8.72-9.18, |s| < 2.3 m: 0 sky rays from -Y, +X and az 45. The round-3 build had 6,032 from -Y
  and 7,420 from +X.
- `bearers=None` (new default): x = 0 and +-0.65 `bed_r`, so bearers land on any wall head. That is
  (-1.6, 0, 1.6) here, as before.
- Head beam: when the plate is less than 5.5 cm above the head beam, the beam grows into the plate. Raising
  `open_sill` to 1.10 left a 1 cm see-through slot under the plate.

## Hero re-runs

Not run. No existing module that a hero imports was touched: the only existing file edited is `square_cabin.py`, and a
grep finds it imported only by `build_v1_stone_watchtower.py`. `pyramid_roof.py` is new.

# Round 5 (2026-10-17, kit 1.10.1): closed floor sandwich to the bed edge, closed hip-saddle ends, tucked hip shingles

Fixes for the round-4 sign-off audit (three axis-4 junction blockers) and note 15 (v1 was 1,057,164 triangles).

## New module (nothing existing changed by it)

- `components/level_probe.py`: `level_sky_probe(g, z0, z1, s_max, centre, n_az=16, az0, ds=0.005, dz=0.005, objects,
  far, name, fail=True, report)` and the step `cabin_bed_probe(g, n_az, ds, dz, margin=0.05, fail=True)`.
  - A level see-through check for any horizontal junction band (floor sandwich, sole plate, jetty on a wall head):
    horizontal orthographic rays every 5 mm across `|s| <= s_max` and every 5 mm in z, from `n_az` azimuths over 180
    deg. A line that meets no mesh is a see-through; with `fail=True` it raises `LevelSeeThroughError`.
  - `cabin_bed_probe` runs it over a `square_cabin` crown (bed + 4 mm to deck top - 4 mm, `|s| <= bed_r + 0.05`).
    Run it AFTER the cull. About 1.56 M rays in 2-3 s.
  - Proof: on the round-4 deliverable it finds 2,732 see-through lines (first at az 0, s -2.51, z 8.944: the audit's
    outermost-joist-bay slot); on round 5, 0.
  - It complements `seal_probe.through_seal_probe` (roofs a body rises through), which cannot test a level band.

## `components/pyramid_roof.py` (existing module; only v1 builds with it -- `tier_roof._pyramid_tier` imports it
## lazily for non-8-sided tiers, which no building uses)

- New keywords `hip_tuck=None`, `hip_bed=0.30` (signature and header updated). **`hip_tuck=0.012, hip_bed=0`
  reproduce round 4 exactly** (same rng draws; the saddle stations and profile are unchanged when `hip_bed=0`).
  - `hip_tuck` (default None = 0.8 x the saddle board width = 0.104 m): the coursed shingles end this far short of
    the hip (trim line `p*tanh - hip_tuck`, and each course's last shingle is sized to end there), so the trimmed /
    clamped shingle ends sit under the saddle board and none shows past its edges (audit item 3, line 251).
  - `hip_bed` (default 0.30 m): over the last 0.30 m of slope at the eave the saddle's underside runs (smoothstep)
    from `lift` down to 1.2 cm inside the deck, on 8 extra stations. The saddle end is a closed hip-roll end flush
    with the lip: no open mouth under it (audit item 2; the black pip at every eave corner).
- Defaults changed on purpose: the fix is on for every future pyramid roof. No other building calls `pyramid_roof`
  (grep), and the hash re-run below shows every other building unchanged.

## `components/square_cabin.py` (existing module; only v1 imports it)

- `bed_n=16` (new): the bed fill is now a curb of `bed_n` straight timbers, one piece each (own Mask R), flats facing
  +-X / +-Y, corners 1 cm inside the bed ring, bedded 1 cm into the wall head and **1 cm into the deck** (round 4
  stopped 4 mm under the deck: a hairline). Director nice-to-have "rim ring as built timber".
- End blocking (part of the bed fill): on every bearer, from inside the curb out 3 cm into the outermost joist on each
  side, wherever the curb stops short of that joist (here 6 blocks, 0.14 m wide, bearer top to deck). This closes the
  audit's slot at |y| 2.40-2.51 m from +-X (audit item 1). Rule-based, so any side / bed_r / bearer layout gets it.
- The `cabin_bed` mortar disc is laid only without a curb (it was 100 % hidden).
- `bed_n=0` = the round-4 lathed 32-gon ring without end blocks.
- `open_sill` default 1.00 -> 1.10 (bible 7; v1 passes 1.10 anyway). Dead imports (`SHINGLE_VARIANTS`, `SIZE_TABLE`,
  `shingle_mesh`) and the unused `_slab` removed; header signature updated.
- `g.CABIN` also publishes `deck_under` and `deck_top` (read by `cabin_bed_probe`).
- Known limit: with `struts=False` there are no dragon beams, so the bearer band on the +-X sides beyond the curb is
  closed only by the curb (inside bed_r - 0.01). The probe would catch it.

## Recipe (note 15)

- `lod.tmpl_lod(z=4.0, step=2, parts=("base_stones", "base_dressed"))` first: drum rubble and dressed work above 4 m,
  outside the entrance zone, on every 2nd grid line (2,556 pieces, -140,920 triangles before the cull). Nothing below
  4 m, at the entrance or on the silhouette is touched. Result 937,933 triangles (was 1,057,164).
- `cabin_bed_probe` after the cull.

## Hash re-run (HASH RULE): `tools/build_baseline.ps1 -Step v1r5_hash -MaxParallel 2`, the six other buildings

Built 05:13-05:40 after the last edit to `pyramid_roof.py` (05:10:59) and `square_cabin.py` (05:09:36), into
`kit/baseline/v1r5_hash/`, compared with the kit 1.10.1 references (`kit/baseline/5_determinism/`, `tools/geom_diff.py`):

| Building | Triangles | Geometry hash | vs 1.10.1 |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 3e2a219a5901afc5 | identical |
| wattle_roundhut | 878,355 | 7e5e7c2df5c4d367 | identical |
| tower_windmill | 1,146,243 | 89bf4a2a2c60e049 | identical |
| v4_mixed (accepted) | 938,453 | 2e87caad61b68d34 | identical |
| v2_tiered_hall | 969,527 | 44ae9b286b85aaae | differs: the v2 builder's concurrent round (recipe saved 05:28, new kit files `tier_flashing.py` 05:18 / `tier_cull.py` 05:09; changed objects are the skirt / lantern / turret flashings, cheeks, plates, openings) |
| v3_longhouse_roundend | 479,791 | 26b91b3f1df9d1be | differs: the v3 builder's concurrent round (recipe saved 05:38, `composite.py` 05:34, `roof_junction.py` 05:34, `linear_roof.py` 05:40; new pegs and wall plate, cheek removed) |

Neither v2 nor v3 reaches the edited code: their build logs contain no `pyramid roof` / `square cabin` line (they have
no pyramid tier and do not import `square_cabin`), and `level_probe.py` is new. The four buildings whose recipes and
modules nobody else changed are hash-identical. v1 itself: 937,933 triangles, geometry `465c7b1b8a7dbb22`.
