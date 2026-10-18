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
