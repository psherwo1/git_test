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

---

## Round 2

Again every change is a new option, key or function whose default takes the old code path (docstrings tag them
"kit 1.17"), so **the hash rule is not triggered** (no `v6r2_hash` run; see "Hash rule (round 2)" below). Proposed
CHANGELOG version 1.17.

### `components/linear_roof.py` (existing module: new options only)

| option | default | what it does when on |
|---|---|---|
| `linear_roof(..., verge_roll=True)` (or a dict overriding `VERGE_ROLL`) + `_verge_rolls`, `_verge_roll_path`, `_LocalAcc` | `False` | **one continuous rolled thatch edge** ("courses" thatch, two free verges): each slope's eave roll (the same `GableRoof.eave_roll` D section, `thatch.d_roll` swelling, calm rounded ends) is ONE sweep from the apex down the first rake, round the eave corner in one fillet (`rc` 0.28 m in the slope plane), along the whole eave and up the other rake. It is laid in the roof's local frame with the slope normal as the section's up, and warped vertex by vertex like the courses. The rake part's lip runs `out` 0.07 m outside the course ends, so its crest covers the course-end teeth (the saw-tooth verge). The verge face is clamped under the roll (`top` 1 cm over `T0 + step`) and starts `face_from` 0.35 m up the slope. The deck's two eave corners follow the fillet, and the verge rafters start above it (`_rafters(verge_u0=)`). The eave roll's end-cap blob at the verge (the old free end 5 cm past the face) no longer exists. Raises without two free verges. |
| `linear_roof(..., comb_step=0.75)` -> `_ridge_comb(step=)` | `0.92` | the comb shake pairs advance `step` x width (25 % overlap instead of 8 %). |
| `linear_roof(..., comb_backing=True)` -> `_ridge_comb(backing=True)` | `False` | a continuous comb backing board (M_roof_shake, 2.4 cm) stands in the saddle under the shakes' crossing, from inside the ridge roll to 1 cm under the crest. Together with `comb_step=0.75`, the red twin of the ridge skyline (d10) shows no slit. |
| `linear_roof(..., rafter_lift_max=0.08)` -> `_rafters(lift_max=)` + `GableRoof.lift_z(x, y)` | `None` | no rafter tail where an eave lift raises the roof more than `lift_max` at the wall face. Under the barn's lifted eave the arched boarded soffit (the deck underside) closes the eave on its own: no loose tails stuck on the rising boarding (b02 / s08). The rng draw per tail is kept, so the other tails do not move. |
| `GableRoof(ridge_seat=True)` binding spars (kit 1.16 option, barn only) | -- | each spar is laid on `_ridge_centre(x)` at its own x (the roll's wander in y and z), so it wraps the roll instead of floating off one end. Without `ridge_seat` the old constant-centre spars are built. |
| `_verge_faces(u_from=None, top_max=None)` (private) | `None` | the face's start up the slope and a cap on its top (used by `verge_roll`). |
| `_deck_slab`: `roof._deck_round` (private, set only by `verge_roll`) | unset | the deck's eave-corner vertices are pulled onto an arc inside the roll's fillet. |

### `components/composite.py` (existing module: new options only)

| option | default | what it does when on |
|---|---|---|
| `composite_decals(..., timber_soot=False)` -> `timber_anchors(soot=False)` | `True` | no soot over the TIMBER openings (a barn's cart, man and loft doors have no hearth behind them). The masonry openings keep theirs, so the kiln door keeps its soot. |

### Recipe-only changes (no kit change)

- **Moss on the thatch:** the barn's decal gate now uses v3's gate for stepped courses: `fp_skip_surfaces=("M_roof_shingle", "M_thatch")`, `normal_fp_dot=0.85`, `fp_ntol=0.12`, `fp_skip_need=6`. That is the course-mean normal test in place of the flat 3 x 3 footprint, which a 0.10 m course step on a 50 deg slope never passes. Result: 17 moss anchors on `M_thatch` (0 in round 1).
- **Kiln:** first rebuilt per the round-1 grade (`round_stone_body` r 2.50, cone eave 4.15, pitch 44, `ball_finial`), then REMOVED per the client direction of 19:40 (the archived build is in `buildings/variants/v6_barn/scratch/r02_kiln/`). The barn now uses a `PlanFrame`, and its round element is the cruck cart entry below.
- **Cart entry (client direction 19:40):** `cruck.cruck_frame` on dry land in the middle of the front long side: clear 4.0 m, posts on pads, a near-semicircular arch (spring 1.90, crown 3.26, R 1.74), tie 3.52-3.78, plank infill to the thatch. It is the harbour house's module with no change to its code paths. The front wall runs into the posts (an open path) and stops at the tie's bearing over the frame's width (the harbour house's `hall_top` pattern). Over it, `eave_lift` is widened to 10 m and 1.55 m high (the thatch eyelid).

### `components/cruck.py` (existing module: one new component, one record extended)

| change | default | what it does |
|---|---|---|
| `arched_doors(g, name, frame=None, leaves=2, setback=0.012, board_t, ledges=(0.45, 1.20), ledge, lap=0.06, seed, rough=True, strap=True)` (new KIT COMPONENT) | -- | **round-headed plank cart doors** filling a `cruck_frame`'s arched opening (a `g.CRUCKS` entry, default the last one). The leaves stand just behind the frame's inner face, each from the ground to the arch intrados + `lap` (their arched top edge hides behind the arch ring and the posts), split at the centre. They are rough vertical boards on a closed backing sheet (note 6), with ledges and forged strap hinges on the outer face. -> `<P>_<name>_leaves`, `_ledges`, `_backing`, `_ironwork`. |
| `g.CRUCKS` entries | -- | they also carry `a_in`, `R`, `zc` (the arch's springing half-width, radius and centre height), `member_w` and `post`, which `arched_doors` reads. These are record keys only: no geometry changes for the harbour house. |

### Hash rule (round 2)

Not triggered. No existing default changed:
- `linear_roof` / `_linear_roof_courses`: with `verge_roll=False`, `comb_step=0.92`, `comb_backing=False` and `rafter_lift_max=None`, the old calls are made with the old arguments. `x_lo` / `x_hi` are only computed earlier (pure arithmetic), and `x += w * step` with `step=0.92` is the same float operation as before.
- `_rafters`: `lift_max=None` skips the new test; `verge_u0=0.0` is the old start.
- `_deck_slab`: no `_deck_round` means no change. `_verge_faces` defaults keep the old `u_a` and envelope.
- The spar change is gated by `ridge_seat`, a kit 1.16 option that only the barn uses.
- `composite_decals`: `timber_soot=True` makes the old `timber_anchors` call, and the soot branch draws the same rng.

No rng draw was added or moved on any default path.

### Known limitations (round 2)

- `verge_roll`: the two rakes' roll ends meet under the capped ridge roll and the apex finial's lead hat (a small knot of roll ends there). The fillet radius is limited by the roll's visible inward depth (about 0.34 m): a larger `rc` leaves the course corner outside the roll.
- `comb_backing` is a plain board: it only shows where two shakes part.

## Round 3

The round-2 grade's three must-fixes, all as defaults-off options (proposed kit 1.18). No other kit change.

### `components/linear_roof.py` (existing module: new options only)

| change | default | what it does |
|---|---|---|
| `VERGE_ROLL["apex_bend"]` (`linear_roof(verge_roll=dict(apex_bend=r))`) and `_apex_bend()` | `None` = the round-2 path | **the apex joint of the rolled verge.** Each slope's rake roll now stops at the tangent point of a radius-`r` arc in the gable plane (`apex` = `r tan(pitch)` below the ridge) and runs on **over the apex** in one swept bend. The section turns with it: its up runs from the slope normal, through vertical, to the other slope's normal, so the section's inward side stays along the ridge. It ends `bend_over` m (default 0.24) past the ridge plane, where its rounded taper is buried in the other slope's roll. The two rolls cross in one closed knot under the ridge-roll end and the lead hat: no butts and no V. The barn uses `r` 0.22 and `bend_over` 0.12. At 0.24 the two full-size sections share about 0.24 m and their +-1 cm swelling interleaves; at 0.12 the seam is one clean taper line. |
| `VERGE_ROLL["bend_over"]` | 0.24 (read only with `apex_bend`) | how far each bend runs past the ridge plane. |

### `components/cruck.py` (existing module: new options only)

| change | default | what it does |
|---|---|---|
| `cruck_frame(pad_top=None)` | `None` = 0.0, the old pads (z -0.30..0) and posts from z 0 | **proud pad stones.** Each dressed pad is built from z -0.30 to `pad_top` with 3 cm arrises, and the jamb post starts 1 cm inside it, so the post visibly stands on a stone. The barn uses 0.13. |
| `cruck_frame(gate=None)` + `_gate()` | `None` = no check, no record | **the arched opening's clearance gate.** It takes a list of `(label, width, height)` envelopes, centred. Each envelope is checked against the clear half-width at 57 heights up to its top: the pads' inner nosing below `pad_top`, the posts' inner faces up to the springing, and the arch intrados above. A height over the crown fails. Each envelope is logged PASS / FAIL; a FAIL raises `guards.ClearanceError`. The result is stored in `g.CRUCKS[-1]["gate"]`, and the frame is appended to `g.CRUCK_ENTRANCES` (origin, out = `n`, width = the opening `2 a_in`, head = the crown). |

### `guards.py` (existing module: one new optional source)

- `entrances_of(g)` also reads `g.CRUCK_ENTRANCES` when it exists. Only `cruck_frame(gate=...)` sets it, and the recentre shift is applied as for the wall doors. So the kit's eave-lip gate (`entrance_clearance`) checks the roof over a gated arch like any door. No other building sets the attribute.

### Recipe-only changes (no kit change)

- **The arch** (must-fix 3): `clear` 4.0 -> **4.2** (opening between the posts 3.40 -> 3.60 m, R 1.74 -> 1.87). The spring stays 1.90 and the crown 3.26, so the arch stays near-semicircular. At 2.8 m the clear width is 2.449 m (2.36 before).
- `CART_GATE = [("cart", 2.4, 2.8), ("figure", 0.6, 1.8)]`.
- `pad_top` 0.13.
- The plinth's free ends now run 5 cm into the jamb posts (`PAD = clear/2 - 0.09`; before, 2 cm into the flush pads, 5 cm short of the post). The old end left a thin see-through slot between the last rubble stone and the post's outer face, under the sill. It is red in the d24 void twin in round 2, and in round 3's first full build (b07). A 1 cm run-in did not close it, because the rubble end stones stop short of the path end.

### Hash rule (round 3)

Not triggered; not run. No existing default changed:
- `cruck_frame` with `pad_top=None` makes the same post `wbox` call (z0 = `0.0 - 0.0`) and the same pad call. With `gate=None`, `_gate` is never called and no attribute is set. The rng draw order is unchanged, and the harbour house uses neither option.
- `entrances_of`: there is no `CRUCK_ENTRANCES` attribute without `gate`.
- `_verge_rolls` with `apex_bend=None` is the round-2 code path. The two new `VERGE_ROLL` keys are only read there, and `verge_roll` is barn-only (kit 1.17).

### Known limitations (round 3)

- The apex knot is two crossing sweeps, not one loop. Where the second roll's taper dies into the first, there is a soft seam line, under the lead hat's drip.
- The gate's envelopes are centred. It does not model door leaves (they open inward behind the frame), the hub-height bulge of a real cart, or a figure walking beside a cart.
- The arched cart doors' outer bottom corners stand 10 cm into the proud pads' inner nosing, behind the posts.

## Round 4 (quick fix: the post-head wedge)

The round-3 audit's one blocking issue only: the see-through wedge at both cruck post heads under the eyelid. One defaults-off option, after kit 1.12.0 (the producer assigns the version). `linear_roof.py` and `roof_junction.py` were not touched.

**Cause** (measured on a FAST build, `buildings/variants/v6_barn/scratch/r04_fast/diag2_posthead.py`):
- the frame's infill boards and backing rose to `top_fn` sampled over the frame plane (y -3.50). The eyelid soffit rises inward, so at their own depth (y -3.39 / -3.355) they stopped 3-5 cm under the soffit;
- the recipe's `wall_top` cut ran to `frame_half + 0.02` (2.32 m), 3 cm past the infill's edge (2.29 m). So the first wall board beyond it sloped from the tie height (3.52) and stood about 8 cm under the soffit.

### `components/cruck.py` (existing module: new option only)

| change | default | what it does |
|---|---|---|
| `cruck_frame(infill_soffit=False)` (+ the local `rake_w(s, w)`) | `False` = the old frame | the plank infill boards and their backing rise to `top_fn` sampled over **their own inner face** (`O + s t + w n`), minus the same 4 mm / 8 mm as before, not over the frame plane. Under a soffit that rises inward, the tops now tuck about 2 cm into the deck at the boards' depth. The board layout, the skip test and every rng draw are unchanged; only the tops move up. |

### Recipe-only changes

- `infill_soffit=True` on the cart entry.
- `wall_top`'s cut now ends at `end + 0.10` (2.00 m from the entry axis): only the front runs' open end posts (x 1.90-2.12) stop at the tie. The first boards (from x 2.12) run up to the soffit, lapping 17 cm in front of the infill's edge.

### Hash rule (round 4)

Not triggered; not run. With `infill_soffit=False`, `top_b(s)` is `rake(s) - 0.004` (the old clamp), `hi` is unchanged, and `rake_bk` is `rake` (the old backing `keep` / clamp). The rng draws are in the same order. So the default path makes the same calls with the same values. The harbour house does not pass the option.
