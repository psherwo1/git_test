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
