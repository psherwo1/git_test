# v5_harbour_house: kit changes (variant builder)

Variant: `buildings/variants/v5_harbour_house/build_v5_harbour_house.py`, approved building 3 -- the timber /
rectangular / waterfront kit family, proved on the harbour house (round 2: the ref4 boat hall).  Recorded here for the
producer to merge into `../CHANGELOG.md` (proposed version 1.12.0).

---

## Round 2 (the ref4 boat hall; reuse mandate, note 16, note 17)

### Summary

- **Existing modules changed (optional parameters / new functions, defaults = kit 1.11.0 behaviour):**
  `linear_roof`, `rubble_walls`, `wall_openings`, `board_belt`, `composite`.  Hash rule re-run: step
  `kit/baseline/v5r2_hash/` (result in the round-2 builder entry of `director/log_variant_v5_harbour_house.md`).
- **New module:** `components/cruck.py` (`cruck_frame`).
- **Round-1 modules reworked (no other building uses them):** `timber_walls` (openings moved onto
  `wall_openings.build_opening(host=...)`, head rule, rough / bow options), `waterfront` (`stone_quay` replaces
  `crib_quay`).
- **Retired (reuse mandate):** `timber_roof.verge_boards` (folded into `linear_roof(verge="board")`, without the
  crossed horns) and `timber_finish` (folded into `composite_hidden_cull(parts=)` / `composite_decals(timber=,
  waterfront=)`).  Both files are now pointer stubs that raise `NotImplementedError` (deleting them was refused by the
  session's permission guard; the producer can delete them at the merge).  `waterfront.crib_quay` is removed.
- `floor_stack` is kept unchanged (clean; the ref4 hall has no jettied floor).

### Existing modules: new options (defaults keep the old behaviour)

| module | parameter / function | what it does |
|---|---|---|
| `linear_roof.GableRoof` | `ridge_sag=0, eave_sag=0, eave_sweep=0, sweep_len=1.0, verge_flare=0, flare_len=1.6, wave=0, wave_seed=33` | **note 17 soft lines as ONE vertical warp field** `warp_z(x, y)`: a parabolic ridge (and eave) sag, a bell-cast / swept eave (the lip lifted, fading quadratically over `sweep_len` m in from it, so the slope flattens toward the eave), an apex flare at every free verge (fading along the ridge and toward the eave: the verge line curves up to the apex), and a low-frequency +-`wave` out-of-true.  `to_world` adds it, `to_local` removes it, so every part `linear_roof` builds and every query (`keep_out`, `top_depth`, `under_soffit`, `eave_zone`) follows it.  All zero: `warped = False`, `to_world` / `to_local` bit-identical. |
| `linear_roof.GableRoof` | `warp_z(x, y)`, `under_z_world(P)` (new methods) | the warp, and the warped deck underside over world points (what walls / frames stop at) |
| `linear_roof._deck` | (warped roofs only) denser stations across and along the slope | the sarking deck follows the curved warp, so no shingle sinks into it |
| `linear_roof.linear_roof` | `verge=None` / `"board"` | the bargeboard of every free verge (`VERGE_BOARD`, `_verge_boards`; folded from the retired `timber_roof.verge_boards`, **no horns**), laid in the roof's local frame so it follows the warp: a sagging / flared roof gets the curved, apex-flared bargeboard of ref4; its eave foot curls up 5 cm -> `<P>_<roof>_verge` |
| `linear_roof.linear_roof` | `apex_finial=None` / `"turned"` | the village finial on each free gable apex: `finial.turned_finial` (the keep's turned / spike finial) on a `finial.lead_hat` fitted over the comb / covering / verge vertices under it (`_apex_finials`) -> `<P>_<roof>_apex_cap_collar`, `_apex_finial` |
| `linear_roof.linear_roof` | the plain (shingle / clumps) path now passes `rafter_skip` / `verge_apex` to `_rafters` when given | as on the thatch "courses" path; absent = the old call |
| `rubble_walls.path_stone_wall` | `base=None, clip_z=None` | the course base z (None = -0.10) and the finalize clip (None = the land clip): a quay wall stands on the harbour bed.  `None, None` runs the old literals. |
| `rubble_walls._quoin_courses` | `z0=-0.04` | the first quoin course's base (the same default) |
| `rubble_walls` | `RUBBLE_LARGE` (new constant) | a `cfg=` override with the larger courses / longer stones of the bible's range (~30 % fewer stones; README section 4's note-15 approach) |
| `wall_openings.build_opening` | `host=None` / `dict(...)` | **the timber host** (`TIMBER_HOST`, `_build_timber_opening`): the kit's ONE opening builder now also builds doors, windows and large boat / barn doors in timber walls -- jambs, heads, timber sills, the window frame and cross mullion, every leaf and shutter from `plank_doors.plank_leaf`, forged straps (`plank_doors.strap_widths`) on the leaves, the pooled `plank_doors.make_pintle` (linked duplicates, note 3) in the jamb, ledged-and-braced boat leaves, built-in stone steps, dark rooms.  `host=None`: the masonry opening, unchanged. |
| `wall_openings` | `TIMBER_HOST["head_rule"]` = `"clamp"` / `"trim"` | **a door / boat door never crosses the storey head**: "clamp" -- the clear height is clamped so the plate is the lintel (leaves 1 cm under it, no separate head beam; raises under 1.8 m / 2.0 m); "trim" -- the plate is cut between the jambs and the head beam replaces it flush at the plate's own depth and top (raises if the beam would be < 0.15 m); anything else raises.  The record's `z1` is the EFFECTIVE clear head, so the clearance guard reports it. |
| `board_belt.board_belt` | `body=None, gaps=(), foot_ring=False, openings=()` | the belt on a plain round body (`dict(center, r, z0, z1)`, `z1` may be callable(g)) on any frame -- e.g. the timber top storey of a `round_stone_body` tower under a `cone_roof` on a RoundFrame; window gaps; a second hewn ring (the timber sill band) round its foot; small cased windows from `wall_openings.build_opening(host=...)`.  `body=None`: the tier-family belt, unchanged. |
| `composite.composite_hidden_cull` | `parts=None` | only objects whose names contain one of these fragments are targets; `BACKED_PARTS` (new constant, folded from `timber_finish.CULL_PARTS` + the cone / quoin / ring parts) = the parts that always have a closed backing |
| `composite.composite_decals` | `timber=False, waterfront=False` | + `timber_anchors` (timber walls, cruck frames, board belts) and `waterfront_anchors` (damp / moss ONLY on quay water faces and piles, z -0.9 .. 0; lichen on the quay copings).  The old body is `_composite_decals`, called unchanged. |

### New module: `components/cruck.py`

- `cruck_frame(g, name, O, t, n, half, top_fn, z_pier, clear, spring=2.2, tie=0.28, member_w=(-0.28, 0.02), post=0.24,
  arch_t=0.24, blade=0.30, collar_at=0.50, collar=0.22, braces=True, pads=True, infill="plank", infill_w, backing_w,
  rough=True, seed=901)`: the cruck / arched-brace gable frame over a wide opening on stone piers -- a tie beam on
  the pier tops, jamb posts on dressed pad stones inside the stone jambs, two segmental ARCHED BRACES springing from
  the posts and meeting under the tie (round / segmental only, bible 1.8), a king strut, curved BLADES following the
  rake (`top_fn`: a warped roof gives curved blades) with an elbowed inner edge, a collar on CURVED BRACES, a king
  post at the apex, and ROUGH plank infill (the `timber_walls` board machinery) on a closed backing over the upper
  gable and the arch spandrels.  The opening is open (boats moor inside).  Publishes `g.CRUCKS`.
- **Why new:** nothing in the kit builds curved timber members, an arch framed in timber, or a gable frame over an
  opening (the keep's `hewn` / `timber` pieces are straight posts, plates and braces of the hut / keep families).

### Round-1 modules reworked

- **`timber_walls`**:
  - `_build_opening` (round 1: its own leaves, frames, shutters, steps, straps) is retired: openings call
    `wall_openings.build_opening(host=...)`, so the barn / boathouse doors are the village's doors.  The new
    wrapper `_build_opening` only builds the host dict.  Objects are now `<P>_<name>_frames`, `_ironwork`,
    `_blockers`, `_dressed` (wall_openings' names) + pooled `<P>_pintle_###`.
  - The plate is split at a "trim" door (`_plate_cut`).
  - `path_timber_wall(rough=None, bow=0.0, head_rule="clamp")`: `ROUGH` (board widths 0.16-0.40 m log-uniform with
    12 % fillets of 8-12 cm, +-1 deg out of true, sagging long rows / plates, 1.4 cm split arrises, +-1.5 cm uneven
    ends, 3.2-4.2 cm boards, +-5 mm depth jitter so leaning neighbours overlap in depth, never in one plane); `bow`
    m: every run bows out of true at mid-run (all pieces, the backing and the openings follow it).
  - Helpers `rough_opts`, `board_widths` (shared with `cruck`), `resolve_timber`; `wbox(tilt, sag, floor)` and the
    run frame's optional 4th element `bow(s)`; `roof_top_fn` reads `under_z_world` on a warped roof.
  - `boat_door(head_rule=None)`.
- **`waterfront`**: `stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, cfg=None, seed=651)` -- a quay edge
  of large blocks (`path_stone_wall` with `QUAY_BLOCKS`, `base=bed_z`); only the WATER runs are built (to the bed),
  land runs are left to the terrain (note 6: nothing deeper than 5 cm on land); `g.QUAYS` carries the water faces for
  the waterline anchors.  `crib_quay` removed.

### Known limitations (round 2)

- `GableRoof` warp: `ref_z` / `under_z` / `top_z` / `section_columns` stay the straight local profile (callers that
  need the warped deck use `under_z_world`); the warp is vertical only (no plan bow of the eave line).
- `cruck_frame` is symmetric about the gable centre; one opening per frame.
- `stone_quay` water runs end in open stone sections where the quay continues in the terrain.
- `board_belt(body=...)`: lookouts only (no doors); the window gaps cut whole boards.
- The eyebrow dormer, the curved stair round the tower and the small round store are not built (recipe choice).

---

## Round 1 (superseded where round 2 says so)

Only new modules: `timber_walls` (`path_timber_wall`, `boat_door`, `rect_path`, `side_s`, `rect_openings`,
`roof_top_fn`, `wbox`), `floor_stack` (`jetty_floor`, `timber_storeys`), `waterfront` (`pile`, `pile_deck`,
`crib_quay` -- removed in round 2, `ladder`), `timber_roof` (`verge_boards` -- retired in round 2), `timber_finish`
(`timber_hidden_cull`, `timber_decals` -- retired in round 2).  No existing module changed; no hash re-run needed.
