# a1_longhouse_addons: kit changes (the WALL add-ons, plan step 4)

Track: `director/log_addons_lean_porch.md`. Demo recipe: `buildings/addon_demos/a1_longhouse_addons/build_a1_longhouse_addons.py`
(imports the accepted v3 recipe, adds steps). Docstrings tag every change "kit 1.19" (proposed CHANGELOG 1.19; the
other track, v7_cottage, may claim 1.19 too: the producer numbers them at the merge).

---

## Round 1

Two NEW modules and one new optional argument in an existing module (default = the old code path), so **the hash
rule is not triggered** (no `a1_r1_hash` run; see "Hash rule").

### New module `components/lean_to.py`

| function | what it does |
|---|---|
| `plane_wall(origin, out, R=2000.0)` | a straight outer wall face: a point on it and its outward plan normal -> `dict(O, n, t, R)` (`t` = run direction, n turned -90 deg, so the add-on's local +y is n). `R` is the radius of the circle whose face stands in for the plane in the round-wall junction pieces (sagitta < 1 mm over +-1.9 m). |
| `wall_field(W, s_mid)` | the `junctions` "tower" dict of that face (centre `R` behind the run's middle), so `junctions.clip_at_tower`, `ride_fillet`, `tower_field` work on a straight wall unchanged. |
| `behind(W, P)` | plan distance of points behind the face (> 0 inside the host). |
| `mono_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=20, overhang=0.30, verge=(0.18, 0.18), covering="shingle", ridge_in=0.30, soft=None, seed=1901, trim=None, fillet=(0.07, 0.10), apron=(0.12, 0.30), ledger=(0.15, 0.17), rafters=None, plate=(0.17, 0.18), below=None, below_clear=0.03, below_lift_max=None, thatch=(0.22, 0.08), register=True)` | **KIT COMPONENT, the shared core of every wall add-on**: a mono-pitch roof against `W`. It is a `GableRoof` whose ridge lies `ridge_in` behind the face, built by `linear_roof` (the village's shingle or thatch courses, deck, bargeboards, eave roll, and the soft-line warp: `soft` takes `eave_sag`, `eave_sweep` / `sweep_len`, `ridge_sag`, `verge_flare`, `wave`). The far slope is clipped and every part is TRIMMED at the face (`ROOF_PARTS` depths, 2-3 cm, behind the rubble's recessed mortar). Framing: a hewn **ledger** let 3 cm into the wall, common **rafters** (the kit's 0.11 x 0.15 section) from the ledger to the eave, a **plate / front beam** at the support line; all laid in the roof's local frame, so they follow its warp. Junction: the covering / wall line is ray-traced, a lime-mortar **flaunching** rides on it (`junctions.ride_fillet`), and a closed **lead apron** (`junctions.wall_end_apron`) closes each verge end against the stone (the v3 longhouse's roof-into-wall language). The junction is registered for the seal-probe guard. `below=<host GableRoof>`: a ValueError if the flaunching crease (at the face) or the covering (under the host's lip line) comes within `below_clear` of the host's eave (its rafter tails, or its soffit where an eave lift > `below_lift_max` dropped them). Publishes `g.ADDONS`. |
| `knee_brace(acc, foot, head, w=(0.11, 0.12), mat="M_timber")` | a curved knee brace: an elliptical quarter from a post or wall face (tangent vertical) to under a beam (tangent horizontal), the hoist beam's / cruck's curve as a free piece. |
| `lean_to(g, name, W, s0, s1, depth=1.8, z_face=2.25, pitch_deg=20, overhang=0.30, verge=(0.18, 0.18), covering="shingle", ends="rubble", end_t=0.40, front="open", post=0.20, max_span=1.8, braces=True, soft=None, below=None, seed=1901, end_seed=None, **mono_roof keys)` | **KIT COMPONENT**: the lean-to. A `mono_roof` on its own supports. `ends="rubble"`: two rubble end walls (`rubble_walls.path_stone_wall` on a thin U path: outer face, quoined front end, inner face; heads tucked 2 cm under the warped deck; starting 10 cm inside the host wall, stones behind the face dropped). `ends="open"`: a post at each front corner. The front plate is carried by posts where the clear span exceeds `max_span`: hewn posts on dressed pad stones, with curved knee braces to the plate. The end walls' coarse mortar sheet is clamped 1.5 cm over the deck underside (`_clamp_under`: `path_stone_wall` keeps 0.3 m mortar cells by their centre, which let the sheet stand through the deck and covering over a nearly level head). -> `<P>_<name>_*` (mono_roof), `_end0/_end1_stones / _quoins / _mortar`, `_posts`, `_pads`. |

### New module `components/porch.py`

| function | what it does |
|---|---|
| `porch(g, name, W, width=2.2, depth=1.0, clear=2.32, pitch_deg=22, overhang=0.25, side=0.25, covering="shingle", beam=(0.16, 0.18), arm=(0.16, 0.20), arm_out=0.12, arm_tail=0.20, brace=(0.55, 0.60), soft=None, below=None, below_lift_max=None, seed=1931, **mono_roof keys)` | **KIT COMPONENT**: a door hood over any door (`W`'s origin = the door centre on the face). It is a `mono_roof` (no plate) whose front beam's underside is at `clear` (art bible 7: >= 2.30 m); `z_face` follows from the pitch. The beam sits on two CURVED BRACKETS, each the barn's `timber_walls.hoist_beam(block=False)` (a hewn arm run out of the wall on one curved knee brace), `width` apart. The roof runs `side` past each bracket on the verge rafters. -> `<P>_<name>_*` (mono_roof), `_beam`, `_arm0_frame`, `_arm1_frame`. |

### `guards.py` (existing module: one new optional argument)

| change | default | what it does |
|---|---|---|
| `register_junction(..., arc=None)` | `None` = the whole circle (old) | `arc=(th0, th1)`: the seal probe samples only this azimuth range about the junction's centre, with the point count scaled to the arc length. A straight wall is registered as the face of a very large circle (`lean_to.plane_wall`), the arc spanning the roof's run. |
| `junction_seal_probe` | -- | reads `j.get("arc")`; a record without it takes the old `n` and the old `rng.uniform(0, 2 pi, n)` draw. |

### Reuse (no change)

`linear_roof.GableRoof` + `linear_roof` (shingle courses, deck, `verge="board"`, soft warp, `rafter_skip`), the host's
`eave_lift` (kit 1.16) + `rafter_lift_max` (kit 1.17), `junctions.clip_at_tower`, `ride_fillet`, `wall_end_apron`,
`_bvh`, `_smooth_up`, `rubble_walls.path_stone_wall` (quoins, mortar body, `top_fn`, `clip`),
`timber_walls.hoist_beam`, `geom.beam / obox / sweep`, `guards.register_junction`, `composite_hidden_cull(targets=)`,
`composite_decals` (the add-on roofs join `g.LINEAR_ROOFS`, the end walls `g.WALL_FACES`).

### Recipe patterns (no kit change)

- **A host lift for the add-on**: the host `GableRoof` gets `eave_lifts=[...]` (an arch over the porch; a second
  arch over the lean-to). Its wall heads follow `under_z_world`, and `linear_roof(rafter_lift_max=0.08)` drops the
  tails under the arch. On a low (2.4 m) eave this is what makes room for a walk-in lean-to and a hood with 2.30 m
  clearance. The soft arches are the add-ons' note-17 line.
- **Soft add-on roofs** through `soft=`: the porch uses its own `eave_lifts` (an arched hood and front beam) and
  `eave_sweep` (a bell-cast lip). The lean-to uses `ridge_sag < 0` (its wall line arches up under the host's arch),
  `eave_sweep` and `wave`.
- **Hidden cull on the host only**: `composite_hidden_cull(targets=<host objects>)`. The open shed and the hood
  are seen from inside and from below, where the cull's viewpoint loops do not reach. A full cull removed rafter
  and covering faces that are visible from there (round-1 probe, before the fix).

### Hash rule

Not triggered; not run. No existing default changed:
- `register_junction` without `arc` stores the same record (no `arc` key).
- `junction_seal_probe` without `arc` computes the same `n` and makes the same rng draw, in the same order.
- No other existing module was edited (`linear_roof.py` and `roof_junction.py` belong to the other track and were not
  touched).

### Known limitations (round 1)

- Thatch coverings are wired (`covering="thatch"`, a thinner `thatch=(0.22, 0.08)` build-up) but not proved. Against
  a 2.4 m eave a thatched lean-to has no room under the host's eave.
- `front="rubble"` (a closed outshot) and a rough-boarded front are not built (only `"open"` on a plate / posts).
- The `below` check models the host's deck underside and rafter tails, not its eave roll's belly. At the demo's
  porch the roll is 0.17 m clear (by inspection).
- The straight-wall "circle" is a stand-in: the seal probe's interior test is "behind the face plane", and walls
  over about 4 m long need a larger `R`.

## Round 2 (a1 round 2, the Art Director's must-fixes; parameters and options only, no new module)

Only `components/lean_to.py` changed (the new kit-1.19 module of this track; `porch.py` unchanged, it passes the new
mono_roof keys through `**kw`). Every new key below is optional. Where a round-1 default moved, it is noted; these
modules are not in the baseline set and nothing else in the kit was edited.

| change | where | default |
|---|---|---|
| `wall_R(L)` = max(2000, L^2 / 0.008): the stand-in circle's radius, so the sagitta over the run is <= 1 mm | lean_to | new helper |
| `plane_wall(origin, out, R=None, run=None)`: R None is sized from `run` when given, else from the add-on's own covering length inside `mono_roof` (`resolve_wall`); an explicit R that bows > 1 mm over the run raises | lean_to | R 2000 -> None (any run up to 4 m still gives R 2000) |
| `mono_roof(below_roll=0.10)`: with `below`, the host's BUILT thatch eave roll (`<P>_<host>_eave_roll`) must clear every out-from-the-wall vertex of the add-on's covering / verge / roll by this much, measured straight up (`_roll_gap`), or ValueError; None = off | lean_to | new (on) |
| `mono_roof(verge_board=None)`: VERGE_BOARD overrides for the bargeboards (set on the GableRoof as `verge_kw`, which `linear_roof._roof_edges` already reads); `dict(below=0.025, above=0.0)` = a 0.12 m board cut to the covering line | lean_to | None = kit board |
| `lean_to(brace=(0.45, 0.48))`: (reach, drop) of the knee braces | lean_to | old values |
| `lean_to(headroom=(2.10, 1.95))` GUARD: the plate underside over the open front >= 2.10 m and every knee-brace foot >= 1.95 m (art bible 7), or `guards.ClearanceError`; None = off; the record gets `headroom` | lean_to | new (on) |
| `lean_to(gate=True)`: the open front is published on `g.CRUCK_ENTRANCES` (the opt-in list `guards.entrances_of` already reads), so `entrance_clearance` checks the eave lip over it (>= 2.30 m and >= the plate) | lean_to | new (on) |

The soft lines used in the demo are existing GableRoof options through `soft=`: `verge_flare` / `flare_len` (both
add-ons) and, on the lean-to, its own `eave_lifts=[eave_lift(0, side=1, width=4.6, height=0.18, fade=1.5)]` (the plate
and the eave arch together, the plate being laid through `to_world`).

### Hash rule (round 2)

Not triggered; not run. No baseline building calls `lean_to.py` (it is new in this track), and no existing module
was edited this round (`guards.py`, `linear_roof.py`, `roof_junction.py`, `junctions.py` untouched).

### Known limitations (round 2)

- `_roll_gap` is vertical only (rays straight up from the add-on's vertices); a roll passing beside a verge is
  not measured. It needs the host's eave roll built before the add-on (true for every recipe that adds steps).
- `gate=True` uses the cruck module's entrance list name (`CRUCK_ENTRANCES`) because `guards.py` was not to be
  edited; a neutral `g.GATED_ENTRANCES` list is a later guards change.
- Still from round 1: thatch coverings unproved, no closed front, straight walls only.

## Round 3 (a1 round 3, the last round: the Art Director's round-2 must-fixes, and the CLIENT DIRECTION of 2026-10-18 00:22 -- the lean-to's rounded roof, producer note 19)

No new module. Every new key is optional; a default that moved is noted. `lean_to.py` / `porch.py` are this track's
new kit-1.19 modules (no baseline building uses them). One existing module, `rubble_walls.py`, gained two NEW
functions and nothing else (no existing function or default touched).

| change | where | default |
|---|---|---|
| `orient_stones(g, name, parts=("_stones",), frac=0.3)`: turns back out every stone of the path wall `name` whose FRONT points into the wall. The stones are open shells (front + sides, no back), so `finalize`'s `recalc_face_normals` has to guess their side and now and then turns a whole stone inside out; an open shell's area vector (sum of normal x area) must point along the outward normal of the path run it stands on (the PathMap the wall publishes on `g.WALL_FACES`). Logs the count before / after. (`_inward_stones` is the test.) | rubble_walls | NEW function; nothing calls it by default |
| `lean_to(orient=True)`: `orient_stones` on both end walls | lean_to | new (on); False = round 2 |
| `mono_roof(below_roll_near=True)` GUARD: `_roll_gap` also takes the NEAREST distance (`bvh.find_nearest`, reach `ROLL_NEAR_REACH` 2.0 m) from the same add-on vertices to the host's built eave roll, under the same `below_roll` rule, so a roll passing BESIDE a verge is caught; both numbers are logged | lean_to | new (on); False = the round-2 vertical check only |
| `_roll_gap(..., near=True)` returns (vertical gap, point, nearest distance, point) | lean_to | internal |
| `lean_to(roof_ends="square", round_kw=None)`: `"round"` = `round_lean_roof` (CLIENT DIRECTION 2026-10-18 00:22, producer note 19 "an oval on the rectangle"): a softly CONVEX thatch slope whose two free ends curve round as ROUNDED HIPS over the square shed, no verges, no hip crease | lean_to | new; "square" = round 2 |
| `RoundLean(W, s0, s1, depth, z_face, pitch_deg, overhang, end_over=0.45, hip=0.55, ridge_in=0.30, ne=3.0, bulge=0.04, arch_wall=0.15, arch_eave=0.18, wave=0.012)`: the surface. The fall is one normalised radius from the spine (the high line `ridge_in` behind the face, from s0 + hip to s1 - hip): on the straight run y / Ey, past each spine end a superellipse quarter ((dx / Ex)^ne + (y / Ey)^ne)^(1/ne), Ex = hip + end_over, Ey = ridge_in + depth + overhang, so the eave runs round each front corner in one tangent curve and back to the wall. z = z0 - H rho + 4 bulge rho (1 - rho) + the arch (1 - t^2)^2 (arch_wall at the wall line .. arch_eave at the eave) + wave. Duck-types `under_z_world` / `to_world`, so the end walls, the mortar clamp and the posts use it unchanged | lean_to | new class |
| `round_lean_roof(g, name, W, s0, s1, depth, z_face, ..., thatch=(0.08, 0.05), course=0.26, hip_rafters=(22, 45, 68), ...)`: deck (closed slab, M_timber_weathered), continuous thatch course sheets round the whole contour (M_thatch; rounded butts, the eave course's nose wrapped under the deck edge; each course out of true), common rafters from the ledger, radial rafters fanning round each hip from the end-wall head, the plate; trimmed into the wall and sealed with the SAME junction code as mono_roof | lean_to | new |
| `_wall_junction(...)`: mono_roof's traced line / flaunching / aprons / `below` + roll guards / seal registration moved into one helper (mono_roof calls it with the same arguments; the a1 porch logs the same numbers before and after: face 0.246, lip 0.429, roll 0.415 / 0.319 m); `trim_ends=True` keeps only the stretch where the covering meets the face (the rounded hips meet the wall on two raking lines) | lean_to | refactor, same behaviour |

**Found by the new guard on its first run:** the a1 porch's E verge corner was only 0.216 m beside the lifted thatch
roll (vertical 0.304 m passed). The demo's front arch was widened 6.0 -> 7.0 m (recipe parameter): 0.319 m lateral,
0.415 m vertical.

**Kit-wide finding (record, not changed):** inside-out open stone shells are not an add-on fault. The accepted v3
longhouse's `LONG_body_wall_stones` has about 6 of them (area-vector test, `scratch/r03/probe_facing.py`); the a1
demo's host wall had 5-11 (its head follows the warped deck, so the layout differs). Calling `orient_stones` inside
`path_stone_wall` (and the round body) by default would fix every rubble building, but it changes their geometry,
so it is a later, hash-checked kit change (proposed: `path_stone_wall(orient=False)` first, then flip the default
with a baseline run).

### Hash rule (round 3)

Not triggered; not run. The only edit to an existing module is two new functions in `rubble_walls.py` that no
existing code calls; `lean_to.py` / `porch.py` are not used by any baseline building.

### Demo-only (recipe-local) pieces, candidates for the kit later

- `seal_wall_head` (a1 recipe): a mortar bedding band (M_mortar, 0.035-0.085 m behind the outer face, 0.30 m deep,
  1.2 cm into the deck) along a rubble wall head under a lifted eave arch. On the arch's flanks the deck rises along
  the wall faster than a flat-topped head stone follows it, so 1-2 cm wedge slits open (round-2 `i06`). A kit
  version would be a `path_stone_wall(head_seal=...)` option or a `wall_head_bedding(g, wall, roof)` component.
- Second host: `buildings/addon_demos/a1_longhouse_addons/smoke_v5/build_smoke_v5_porch.py`, the a1 porch call on
  the accepted v5 harbour house's land-gable door, with no host eave lift.

### Known limitations (round 3)

- The rounded lean-to roof is thatch only (note 19: thatch first); its decal anchors (moss) are not generated, because composite_decals reads `g.LINEAR_ROOFS` (GableRoof records).
- Still open: a round-wall `W` (a porch on a drum or roundhut door); `flashing="lead"` for timber hosts (the lime
  flaunching is fixed); a host-arch helper (recipes still choose `eave_lift` for low-eaved hosts); the neutral
  entrance list (`CRUCK_ENTRANCES`); a stop / pintle under the porch brace feet; thatch coverings unproved; no
  closed lean-to front.
- A lean-to under a 3.35 m eave without an eave lift (v5's eave walls: the crease must stay about 3.0 m) cannot
  reach the 2.10 m plate at a store's 1.8-2.0 m depth and a shingle pitch of 14 deg or more (about 1.9 m): the
  headroom guard would refuse it, so the second-host smoke shows the porch only.
