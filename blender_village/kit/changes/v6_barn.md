# v6_barn: kit changes (variant builder)

Variant: `buildings/variants/v6_barn/build_v6_barn.py` -- the village barn (plan step 3, after the harbour house).
Recorded here for the producer to merge into `../CHANGELOG.md` (proposed version 1.16, with the 1.12-1.15 v5 entries).
Docstrings tag every change "kit 1.16".

---

## Round 1

Every change is a new option, function or spec key whose default takes the old code path, so **the hash rule is not
triggered** (no `v6r1_hash` run; see "Hash rule" below).

### `components/linear_roof.py` (existing module: new options only)

| option | default | what it does when on |
|---|---|---|
| `GableRoof(eave_lifts=[eave_lift(x, side, width, height, fade)])` + `eave_lift()` / `EAVE_LIFT` | `()` | **the lifted eave over a wide door**: the eave line sweeps up in one soft arch, a term of the roof's ONE warp field: `height x (1 - t^2)^2` along the eave (`t = |x - centre| / (width/2)`, a round crown and tangent feet) `x (1 - d/fade)^2` in from the lip (`d` = plan distance from the lip). There is no step, tear or front, so it works on **thatch** and shingle alike, and every part follows it: courses, eave roll, deck, rafters, verge, and the walls' `roof_top_fn` (the boarding rises with it above the plate). The barn uses it over its cart doors (6.4 m wide, 0.85 m lift, 2.5 m fade): the guard's "eave lip above the door head" rule is met by the roof's form, not by a lower door. Unknown keys raise. `()` leaves `warped` and `warp_z` bit-identical. |
| `GableRoof(ridge_seat=True)` | `False` | `_ridge_roll`: the thatch ridge roll's flanks run straight down from the arc's ends to 3 cm under the covering's mean top at `|y| = roll_w` (never less than the old 10 cm bury). On a steep (50 deg) thatch the slope falls away from the roll faster than the old fixed bury, which left a dark slot under the roll along the whole ridge (the "ridge slits"). `False` builds the old profile. |

### `components/timber_walls.py` (existing module: new options, keys and functions)

| option | default | what it does when on |
|---|---|---|
| `boat_door(..., to_ground=True, pad=None)` (`TIMBER_OPENING["boat"]["to_ground"]`, `["pad"]`) | `False` | **a cart door**: the clear opening starts at the wall's ground (`ground_z`), not on the sill beam. `path_timber_wall` cuts the sill beam between the door's pads (`_sill_cut`), and `wall_openings` stands each jamb on a dressed stone **pad** (`M_stone_dressed`, from 6 cm under the ground to the sill-beam top; `pad = (past the jamb, depth behind the face, proud of it)`, None = `(0.10, 0.42, 0.10)`). The plinth (`path_stone_wall`, split into two open paths) runs into the pads' backs. `boat_door()` without it passes no new detail key, so its spec is unchanged. |
| `window(..., gable=True)` (`TIMBER_OPENING["window"]["gable"]`) | `False` | **an opening in the gable**, above the plate: its jambs stand on the plate, its head is checked against the roof rake (`min(rake) - 3 cm` over its width, raises if it crosses), not against the plate (which used to raise); intermediate posts under it are kept; it is cased on the gable cladding's face (`_face_w`: the batten front of the gable style, rough or not), so its open leaves lie on the battens. Raises without a gable or with the jambs below the plate. |
| `window(..., lights=0)` (in `wall_openings._build_timber_opening`) | `4` | an OPEN timber opening: no glazing frame and no mullion (a loft door, a vent slit). With `shutters=True` the two plank leaves stand open on the face. |
| `loft_door(width=1.20, height=1.70, sill=2.60, ...)` (new spec helper) | -- | the hayloft door: `window(shutters=True, lights=0, gable=True)` with a tighter dark room (`room_pad=(0.20, 0.30, 0.20)`). |
| `hoist_beam(g, name, at, out, z, length=1.10, tail=0.45, section=(0.20, 0.22), brace=(0.55, 0.50), brace_t=(0.12, 0.13), block=True, lean=0.02)` (new KIT COMPONENT) | -- | **the hay-hoist beam** over a loft door: a hewn beam run out of a wall / gable face (its tail into the frame), ONE curved knee brace from the face below it (an arched brace, tangent to the face at its foot and to the beam at its head: the village's curved-timber language), a pulley block with a sheave on a forged eye and a hook at its outer end; the outer end droops `lean`. -> `<P>_<name>_frame` (M_timber / M_timber_weathered), `<P>_<name>_ironwork` (M_iron). |
| `_build_opening(..., face=None)`, `_opening_layout(..., ground=None)` (private) | `None` | the host face w for a gable opening; the cart door's clear rect from the ground. `None` = the old values. |
| backing rows (`path_timber_wall`) | -- | the backing's z rows are clamped at the sill line (`max(z, floor - dz - 0.02)`): identical for every existing opening (all clear rects start at or above the floor); a cart door's below-sill clear rect adds no backing strip under the sill. |

### `components/wall_openings.py` (existing module: the timber host only)

- `lights=0` skips the glazing frame / mullion / transom block (`lights` 4 and 2 unchanged).
- A boat door with `to_ground=True` opens at `host["ground"]`, gets the two pads and `rec["sill_cut"]`; the
  record's `threshold` / `z0` is the ground, so the clearance guard, the cull's door views and the decal recipes see
  the real opening. Without `to_ground` the boat branch is the old code.

### Reuse (no change)

`round_stone_body` (the kiln drum, `RUBBLE_LARGE`), `cone_roof` + `finial(style="spike")` + `round_eave_fill(z_bot="wall")`
on a `RoundFrame` (the kiln's cone), `wall_abutment` (the thatch running into the kiln's wall: it traced one run from
eave to eave round the drum's inner side, 0 seal-probe leaks), `path_stone_wall` (plinth; open paths ending in the kiln
and in the cart-door pads), `path_timber_wall(rough=True, bow=0.03)`, `linear_roof(covering="thatch",
apex_finial="turned")` with the soft `GableRoof` options (ridge sag, eave sag, swept eave, verge flare, wave),
`components.openings.door / window`, `wall_openings.door_spec / window_spec`, `composite_*`, `recenter`.

### Hash rule

Not triggered. No existing default changed:
- `GableRoof`: `eave_lifts=()` adds no warp term and does not set `warped`; `ridge_seat=False` keeps the old bury
  points.
- `path_timber_wall`: with no `to_ground` door the sill beam is the same single `wbox` call, first in its run, as
  before. The mid-post gaps filter only `gable` openings. The backing z rows are the same set. `_opening_layout`
  returns the same rects (`cz0 + height == floor + threshold + height`).
- `wall_openings`: `lights` 4 / 2 take the old boxes in the old order; the boat branch only branches on `to_ground`.
- No rng draw was added or moved on any default path.

### Known limitations (round 1)

- `eave_lift` is a vertical lift like the other warp terms; it should stay clear of a junction body (it fades to 0
  at +-width/2; on the barn the lift is about 3 cm where the eave meets the kiln's wall).
- `ridge_seat`: the seat depth is set from the straight profile at mid-slope; the roll's end caps (`fs` scaling)
  shrink the flanks over the last 16 cm before a verge face, which covers them.
- `gable=True` openings: one row; the head is checked against the rake, but a gable opening's dark room is not
  checked against the roof deck (keep `room_pad` small, as `loft_door` does).
- `hoist_beam`: straight beam on a straight face; no rope.
