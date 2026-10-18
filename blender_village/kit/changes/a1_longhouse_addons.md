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
| `lean_to(g, name, W, s0, s1, depth=1.8, z_face=2.25, pitch_deg=20, overhang=0.30, verge=(0.18, 0.18), covering="shingle", ends="rubble", end_t=0.40, front="open", post=0.20, max_span=1.8, braces=True, soft=None, below=None, seed=1901, end_seed=None, **mono_roof keys)` | **KIT COMPONENT**: the lean-to. A `mono_roof` on its own supports. `ends="rubble"`: two rubble end walls (`rubble_walls.path_stone_wall` on a thin U path: outer face, quoined front end, inner face; heads tucked 2 cm under the warped deck; starting 10 cm inside the host wall, stones behind the face dropped). `ends="open"`: a post at each front corner. The front plate is carried by posts where the clear span exceeds `max_span`: hewn posts on dressed pad stones, with curved knee braces to the plate. -> `<P>_<name>_*` (mono_roof), `_end0/_end1_stones / _quoins / _mortar`, `_posts`, `_pads`. |

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
