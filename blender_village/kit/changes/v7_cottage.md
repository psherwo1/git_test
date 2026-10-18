# v7_cottage: kit changes (roof add-ons builder, plan step 4)

Variant: `buildings/variants/v7_cottage/build_v7_cottage.py` -- a low L-plan thatched cottage that proves the ROOF
add-ons (valley, chimney, gabled dormer). Proposed CHANGELOG version **1.19**; docstrings tag every change "kit 1.19".

---

## Round 1

Every change to an EXISTING module is a new option whose default takes the old code path, so **the hash rule is not
triggered** (no `v7r1_hash` run; see "Hash rule" below). The add-ons themselves live in ONE new module.

### NEW `components/roof_addons.py`

| function | what it is |
|---|---|
| `roof_valley(g, main, wing, name=None, width=(0.34, 0.34), crown=0.16, bury=(0.10, 0.10), dy=0.03, comb_clear=0.22, var=0.06, seed=0, taper=0.30, end_out=0.10, smooth=2, foot="crest")` | **KIT COMPONENT: the gable-to-gable valley** (L / T plans, any angle, any yaw; also a dormer roof into its host). Traces the true line where the wing's covering top meets the main roof's top (`valley_line`: up one valley, over the wing's ridge roll, down the other) and sweeps ONE soft **rolled thatch valley** along it (`_crease_roll`: buried keel, a skirt `width` out on each covering ending `bury` under it, a rounded back `crown` over the crease, +-6 % low-frequency swelling, tapered rounded ends). `foot="crest"` stops the line just past the wing's eave-roll crest (the two eave rolls cross under its end; no twisted section over the roll noses). Drops the wing's comb units within `comb_clear` of the main top. No metal gutter. -> `<P>_<name>` (M_thatch); `g.VALLEYS`. |
| `solid_clip(roof, under=True)` / `deck_clip(roof)` / `any_clip(*clips)` | the clips that make two roofs yield to each other at a valley: `linear_roof(clip=solid_clip(other), deck_clip=deck_clip(other))` -- coverings, rolls, ridge, comb and rafters are culled inside / under the other roof's solid; the decks are kept up to the line where the two DECKS cross, so the backing under the valley is closed. |
| `roofs_top_fn(roofs, tuck=0.02)` | wall `top_fn` under several roofs (an L plan): the highest deck underside over the point. |
| `top_world(roof, P)`, `top_normal(roof, P)` | the roof solid's world top / normal over plan points (warp included). |
| `GabledDormer(main, x, side=-1, d=0.55, width=1.30, pitch=50, overhang=0.22, verge=0.28, thick=0.24, step=0.08, window=None, plate_gap=0.10, soft=None, back_run=0.30, name="dormer", ...)` | the **gabled dormer** spec (sibling of `GableRoof(eyebrows=)`): its own small soft `GableRoof` (`.roof`, yaw +90 deg to the host, `DORMER_SOFT` sag / sweep / flare / wave), the front frame line `d` m in from the host wall face, the cheeks' run back into the host roof, the host clips `.clip_main()` / `.deck_clip_main()`. The window sill is raised (logged) until it clears the host thatch; raises if the dormer ridge comes within 0.15 m of the host ridge. |
| `gabled_dormer(g, D, seed=81, covering="thatch", finial=True, foot_roll=True, valley=None, walls=None, verge_roll=None)` | **KIT COMPONENT**: the dormer's walls (`timber_walls.path_timber_wall`, board_batten, rough, the kit window centred in the front), its roof (`linear_roof`, thatch, yielding to the host, comb backing, lead hat + turned finial at the front apex, optional `verge_roll` -- the rolled thatch hood), the valley into the host (`roof_valley`) and a rolled thatch **foot roll** round the cheeks and the front where the host thatch meets the boards (`_dormer_foot_roll`, the same crease sweep; front corners rounded). `g.DORMERS`. Thatch only in 1.19. |
| `chimney(g, name="chimney", center, r_base=0.62, batter_deg=2.0, top=None, roof=None, over_ridge=0.85, clip=None, cfg=None, seed=51, crown="louvre", cap=None, parts=None, louvre=None, pot=None, abut=None, shoulder=None)` | **KIT COMPONENT: the round chimney**: a battered rubble stack (`rubble_walls.round_stone_body`, the village rubble); `shoulder=dict(z, r_base, batter_deg, h)` gives a broad base, a rounded dressed-stone **weathered offset** (`<P>_<name>_weathering`) and a narrower upper stack. With `roof=` the roof is trimmed at the stack face and flaunched with the v3 / v5 junction (`roof_junction.wall_abutment(radius=<upper stack>)`: lime-mortar fillet on the true line, lead end aprons, seal-probe registration) when the roof meets part of the stack (a gable stack), or with a closed ring of flaunching (`_ring_abutment`, `junctions.ride_fillet` on a closed `_ring_trace`) when the roof surrounds it (through a slope / the ridge -- not yet proven on a build). A softly out-of-round dressed drip-course cap (`CHIMNEY_CAP`), a dark closed flue cup (`_flue_blocker`), and a round crown: `"pot"` (a round dressed-stone pot) or `"louvre"` (dressed posts under a little lead cone, `finial.lead_hat`, with the turned finial; dark smoke chamber `_louvre_blocker`). `g.CHIMNEYS`. |
| `chimney_decals(g, seed=1701)` | soot on each stack head (stone faces only) and lichen on the cap -- call it in the recipe's decals step. |

### `components/linear_roof.py` (existing module: new options only)

| option | default | what it does when on |
|---|---|---|
| `linear_roof(..., deck_clip=fn)` -> `_linear_roof_courses(deck_clip=)` | `None` = `clip(V, margin=0.10)` (old) | the deck's own cull (two roofs in a valley keep their decks up to the deck-to-deck line: closed backing). |
| `linear_roof(..., apex_ends=("lo",))` -> `_roof_edges(apex_ends=)` | `None` = every free verge (old) | the apex finial only on the listed free gables (a chimney stands at the other). |
| `linear_roof(verge_roll=...)` with ONE free verge; `_verge_roll_path(lo_free=, hi_free=)` | both `True` (old) | the rolled verge on a roof whose other end runs into another body (a cross wing, a dormer): the eave roll runs straight on to the buried end (no fillet, no rake, no apex bend there); the deck rounds only the free corners. Before 1.19 this raised; with two free verges the old calls are made with the old arguments. |

### Hash rule

Not triggered; not run. No existing default changed:
- `deck_clip=None` keeps `deck.cull = lambda V: clip(V, margin=0.10)` (same branch, same lambda) on the courses path; the plain path is untouched.
- `apex_ends=None` calls `_roof_edges` / `_apex_finials` exactly as before.
- `verge_roll` with two free verges: `kfr = {}` (the old `_verge_roll_path` arguments), both apex bends prepended / appended in the old order, `_deck_round["corners"]` the same two tuples in the same order. Only a roof with one free verge (which used to raise) takes the new branch.
- No rng draw was added or moved on any default path. The new module is only imported by v7.

### Known limitations (round 1)

- Valley: thatch only (the shingle laced / swept valley is not built; a shingle roof would need course lacing). At each re-entrant eave corner the two eave rolls cross under the valley's rounded foot; under them a small closed dark pocket remains in the corner soffit (no see-through: red twin clean).
- Valley over the wing ridge: a small shadowed notch under the roll's arch where the comb stops (comb units within 0.22 m dropped).
- Dormer: the dormer valley's skirts meet the host's cut course ends with some short ragged edges near the dormer eave ends. The dormer roof's rolled hood is large on a 1.3 m dormer (VERGE_ROLL section is the eave roll's).
- Chimney through a slope / the ridge (`_ring_abutment`): written, not proven on a build. A gable stack is the proven case.
- The rubble-wall windows (existing kit `window_spec`) let interior rays out at the sill line (40-65 mm pinch, `round_01/builder_extra/probe_interior_r01.txt`, ROOMS); not an add-on junction, every building has the same window.

## Round 2 (kit 1.19 r2): `roof_addons.py` only. It is a new module used only by v7, so the hash rule is not triggered; `linear_roof.py` is untouched this round

| change | what |
|---|---|
| `_crease_roll(sink=, n_tuck=4)` | Each end is now a **rounded tuck**: 4 rings on a quarter circle `end_out` past the end, shrinking to a point and diving `sink` under the bisector, closed by triangle fans. This replaces the flat, non-planar n-gon cap. |
| `_continuous`, `_smooth_rows` | In `roof_valley`, the skirt directions a / b stay continuous station to station; the per-station probe is only a majority vote. The normals and skirts are smoothed, so the foot section no longer twists and the arch has no folded lip. |
| `roof_valley(end_out=0.16, sink=0.06, ridge_cut=0.12, corner="auto")` | **ridge_cut**: `_cut_ridge_under_arch` bisects the wing's ridge roll and comb 0.12 m on the wing side of the arch crest, deletes the part toward the main roof and fills the cut, so the roll ends closed under the arch. **corner** ("auto" = eaves within 0.3 m of one height): `_corner_close` at each re-entrant eave corner does three things: drops rafter tails whole within 0.35 m of the other roof's plan columns; adds a closed boarded soffit slab (M_timber) between the wall faces and lips, under the lower deck; and adds a rounded thatch closing knot where the two eave rolls cross. |
| `_ring_trace` | Starts low (`z_guess = roof.z_lip`, where the battered face is widest). Round 1 started above the ridge, inside the trimmed hole, so it never hit. Gaps under 15 % are interpolated. `_ring_abutment` is now **registered for the seal probe** ("<roof> / stack ring"). |
| `DORMER_SOFT` | `ridge_seat=True`. |
| `dormer_verge_roll(hw, ...)` / `gabled_dormer(verge_roll="auto")` | The hood is scaled to the dormer: rc 0.18 hw, apex_bend 0.155 hw, bend_over 0.12 hw. A recipe dict is capped at 0.20 hw / 0.17 hw. |
| `_dormer_foot_roll(under_eave=0.16, taper=0.40, sink=0.10)` | Each end stops further under the dormer eave and tucks into the host thatch under the dormer valley's skirt. |
| `chimney(crown="pot")` | The default crown is now the round pot. `"louvre"` is opt-in, with h 0.24 by default and clamped to 0.30 m, and no finial by default (`finial=None`). |

**Proofs:**
- `buildings/variants/v7_cottage/scratch/ring_stack.py` is a FAST build: the cottage plus an r 0.52 stack through the back slope.
  - Ring flaunching: seal probe "roof / stack ring" 0 leaks in 57,961 rays.
  - `round_02/builder_extra` r01 / r02 void and i09 red: 0 red inside the attic.

## Round 3 (kit 1.19 r3)

`linear_roof.py` (existing module) gains ONE optional parameter with the old default; the rest is in the new `roof_addons.py` (used only by v7).

| change | what |
|---|---|
| `linear_roof(eave_roll=None)` -> `_linear_roof_courses(eave_roll=)` | NEW option: a dict of `GableRoof.eave_roll` keywords (radius / proud / drop / front / tail) for the "courses" thatch's eave-roll SECTION, which the verge roll / hood also sweeps. `None` calls `roof.eave_roll()` exactly as before (old behaviour, hash rule not triggered). |
| `GabledDormer(thick=0.13, step=0.05, deck_t=0.025, roll=None)` | The dormer's thatch is thinner and its roll section is scaled to it: `roll` defaults to `dict(radius=0.15 * hw, proud=0.02, drop=0.015)` and `gabled_dormer` passes it as `linear_roof(eave_roll=D.roll)`. The hood section is now about a fifth of the dormer's width (it was the host's 0.16 m roll on a 0.24 m thatch: the "pretzel"). |
| `dormer_verge_roll` docstring | Corrected: `rc` is the hood's eave-corner fillet and `apex_bend` the bend over the apex; the section comes from `GabledDormer(roll=)`. |
| `_corner_close(corner_r=0.25, cut=0.13, past=-0.05)` | The r2 ball knot is replaced by `_corner_roll`: ONE swept internal-corner roll, the eave roll's own D section (`main.roll_section()`, x 1.05) carried round the re-entrant lip corner on a 0.25 m plan fillet with 0.30 m runs along both lips, lip height and up-vector blended from one slope to the other, its ends tapered inside the straight rolls. The two straight eave rolls are cut back 0.13 m past the fillet's tangent points (`_drop_faces`), so their open ends lie inside it. The soffit slab now spans from 1.5 cm under the lower deck underside to just over the HIGHER deck top and stops 5 cm inside the lips, so the two decks' cut board ends where they cross are buried in it (no X of boards). -> `<P>_<name>_roll` replaces `<P>_<name>_knot`. |
| `roof_valley(foot_back=None, ridge_bury=0.12, ridge_bury_w=0.35)` | At a closed corner the line stops `foot_back` = 0.22 m short of the wing roll's crest (off the round nose where the section twisted), and each foot tuck runs on >= 0.26 m and sinks crown + 8 cm into the corner roll. Over the wing's ridge roll the skirts bury up to 0.12 m deeper, the wing skirt is steered onto the ridge axis and its END dives vertically (`_crease_roll(bury_dir=)`): the radial dive over the tight ridge-roll bend folded the skirt end back on itself (the two dark wedges). |
| `_crease_roll(bury=(array, array), bury_dir=(dA, dB))` | Per-station bury and an optional dive direction per skirt; defaults unchanged. |
| `_cut_ridge_under_arch` | The fill faces of the cut ridge roll / comb are oriented out of the kept part. |
| `valley_line(foot_back=0.0)` | New option, default old. |

**Hash rule:** not triggered. The only existing-module change is `linear_roof(eave_roll=None)`, whose default path is the old call; every other change is inside `roof_addons.py`, which only v7 imports.
