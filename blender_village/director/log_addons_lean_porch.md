# a1_longhouse_addons: the WALL add-ons (lean-to, porch), proved on the longhouse (plan step 4)

## CLIENT DIRECTION (2026-10-17, session 2)

- Plan step 4 (client "Yes proceed"): the add-ons. The client said: "Move forward with the quick fix, the housekeeping, and the add ons. Make sure the add ons stick with the theme of the village".
- **This track builds the WALL add-ons:**
  - a **lean-to** (a mono-pitch roof against any wall);
  - a **porch / canopy** over any door.
- The other track (log_variant_v7_cottage.md) builds the valley, chimney and dormer at the same time.
- Team method: builder, Art Director (modularity rubric, pass 8.2), independent audit, **at most 3 rounds**. Time matters.

**Village theme (client: "Make sure the add ons stick with the theme of the village"; producer notes 16 and 17 are binding):**
- **Same builders, techniques and materials** as the village (note 16): the shared palette only, the village rubble and lime mortar, rough old timber, the village shingle and thatch courses, iron straps and pintles, and lead flashing dressed like the harbour house's and the longhouse's. Re-use the kit's existing detail modules for these.
- **Round structures and soft, organic lines** (note 17), as in `reference/ref4_harbour_boathouse_concept.jpg`:
  - swept or bell-cast eaves and gently sagging ridges (the `GableRoof` soft options);
  - rolled verges and eaves;
  - curved braces and brackets (the `cruck` family's curves);
  - battered, softened stone;
  - round elements where they fit, for example a round chimney pot or a round smoke louvre under a little cone.
  
  Nothing ruler-straight or generic.
- **Every add-on is a reusable kit module** with old-behaviour defaults: a short call in any recipe attaches it to any wall or roof of any design. Its junctions are closed, flashed or covered, with no see-through and no light leaks: they become visible beams in fog (`director/performance_assessment.md`).
- Low and working, not more towers: the vignette showed the village already has many conical turrets.

## Brief

**The host:** prove both add-ons on the **v3 longhouse**, without touching its accepted files.
- Write a demo recipe uildings/addon_demos/a1_longhouse_addons/build_a1_longhouse_addons.py. It re-uses v3's recipe (import its parameters / steps, or a thin copy that only adds steps) and adds:
  - one **lean-to** on the back long wall of the longhouse body;
  - one **porch** over the longhouse's front door.
- Output: 1_longhouse_addons.blend + decal_anchors.json in that folder.
- **Never modify** uildings/variants/v3_longhouse_roundend/ or any accepted file.

**The new kit add-ons:**
1. **lean_to:** a mono-pitch soft roof against any wall run.
   - It follows the host covering (thatch or shingle), with the soft options: sag, a swept eave, a rolled verge.
   - It sits on a low rubble or rough-boarded wall, or on posts.
   - It is sealed into the host wall (an abutment flashing / mortar fillet, re-using the wall_abutment pieces where they fit) and kept below the host eave.
   - It is a reusable component in a NEW module (e.g. components/lean_to.py).
2. **porch:** a small canopy or porch over any door.
   - Curved timber brackets or a small cruck-arched frame (re-use the cruck curves).
   - A soft swept roof in the host covering.
   - Sealed to the wall, with door clearance >= 2.30 m.
   - A new module (e.g. components/porch.py).

**File ownership while both tracks run:** this track must NOT edit linear_roof.py or oof_junction.py, because the other track owns them. Subclass, wrap or call them from the new modules. If something truly needs a change there, record it in the builder entry as a request for later and work around it.
## PRODUCER NOTE (2026-10-17, session 2, 23:10): early-preview feedback, apply in round 1 (the village theme)

From `round_01/preview/` (the first FAST build):
1. **Keep the eave lift over the front door.** The thatch waving up over the porch is exactly on theme.
2. **The porch hood is not yet on theme.** It is a flat, ruler-straight shingle canopy on square brackets under soft thatch.
   - Make it **soft**: a swept / bell-cast or gently arched hood (the `GableRoof` soft options, or a curved hood profile), in the host's covering or the village shingle with a rolled or flared edge.
   - Carry it on **curved timber brackets** (the `cruck` curves) or a small cruck-arched frame.
   - Seat it sealed into the wall.
   - Door clearance >= 2.30 m.
3. **The lean-to must read as a lean-to:** a real mono-pitch shed (a store or byre) against the back long wall. About 4-6 m along the wall and 2-3 m deep, low walls (rubble or rough boarding) or posts, its soft roof dying into the host wall under the host eave, with a door or opening of its own. It must not be a small canopy.

## a1_longhouse_addons round 1 — builder entry

**Built:** two new kit modules for the WALL add-ons, `components/lean_to.py` and `components/porch.py`, proved on a demo copy of the v3 longhouse. The demo recipe is `buildings/addon_demos/a1_longhouse_addons/build_a1_longhouse_addons.py`. It IMPORTS v3's recipe file (read only; nothing under `buildings/variants/v3_longhouse_roundend/` was touched), adds two steps and overrides only the host settings listed below. Outputs: `a1_longhouse_addons.blend` (19.7 MB) and `decal_anchors.json`, next to the recipe. Kit notes: `kit/changes/a1_longhouse_addons.md` (proposed kit 1.19).

**Producer note 23:10 (applied in this round, after the early preview in `round_01/preview/`):**
1. The eave lift over the front door is kept.
2. The porch hood is now SOFT:
   - its own arched eave (`eave_lift`, 0.22 m over 2.6 m), so the hood and its front beam arch like the thatch above;
   - a bell-cast lip (`eave_sweep` 0.08 over 0.5 m) and bargeboards with a curled foot;
   - larger curved brackets: the barn's hoist-beam arm with a 0.65 x 0.75 m curved knee brace;
   - sealed into the wall with a lime flaunching and lead verge aprons;
   - front-beam underside 2.32 m at the brackets, rising to the crown; clearance guard PASS (2.76 m over the door).
3. The lean-to is now a real shed:
   - 4.0 m along the back wall x 2.2 m deep, taking in the east north window;
   - rubble end walls with quoined fronts, an open front bay (1.86 m clear under the plate) on one dressed-pad post with curved knee braces;
   - the soft roof dies into the host wall along an ARCHED line (`ridge_sag` -0.25), under a second thatch eave arch (`eave_lift` 1.2 m over 8 m, back side);
   - checked by the module to stay under the host's eave: 0.15 m at the face, 0.14 m under the lip line.
   - Preview of the revised FAST build: `round_01/preview_b/`.

**The add-ons' API (every key optional except the wall and the run):**

| call | key parameters | what it builds |
|---|---|---|
| `plane_wall(origin, out)` | a point on the outer face, the outward normal | the wall frame (`O`, `n`, `t`) every wall add-on attaches to |
| `mono_roof(g, name, W, s0, s1, depth, z_face, ...)` | `pitch_deg`, `overhang`, `verge`, `covering` ("shingle" / "thatch"), `soft` (any GableRoof soft key: `eave_sweep`, `eave_sag`, `ridge_sag`, `eave_lifts`, `wave`...), `ridge_in`, `fillet`, `apron`, `ledger`, `plate`, `rafters`, `below=<host GableRoof>`, `below_clear`, `below_lift_max` | the shared core: a GableRoof clipped to one slope and trimmed at the face; ledger, common rafters, plate; traced lime flaunching and lead verge aprons; seal-probe registration; the under-the-host-eave check (raises) |
| `lean_to(g, name, W, s0, s1, depth, z_face, ...)` | `ends` ("rubble" / "open"), `end_t`, `front` ("open"), `post`, `max_span`, `braces`, + all mono_roof keys | rubble U-path end walls (quoins, mortar clamped under the deck), posts on dressed pads with curved knee braces |
| `porch(g, name, W, width, depth, clear, ...)` | `pitch_deg`, `overhang`, `side`, `beam`, `arm`, `arm_out`, `arm_tail`, `brace`, `soft`, `below`, `below_lift_max` | door hood on two curved brackets (`hoist_beam(block=False)`), front beam at `clear`, z at the wall derived |
| `knee_brace(acc, foot, head)` | `w` | the curved quarter-arc brace as a free piece |

The demo calls are two lines each, `LEAN` / `PORCH` dicts in the recipe: `lean_to(..., W=plane_wall((-5.9, 2.6), (0, 1)), s0=-2, s1=2, depth=2.2, z_face=2.86, pitch_deg=16, ...)` and `porch(..., W=plane_wall((-7.0, -2.6), (0, -1)), width=2.1, depth=1.0, clear=2.32, pitch_deg=22, ...)`.

**Host settings in the demo:**
- `ROOF` is v3's GableRoof with `eave_lifts=[front 1.2 m / 6 m at the door, back 1.0 -> 1.2 m / 8 m over the lean-to]`.
- `body_top` reads `under_z_world`, so the walls rise under the arches.
- `linear_roof(rafter_lift_max=0.08)`.
- The hidden cull runs on the host's objects only (see "known gaps").

**Reuse table:**

| piece | reused from (unchanged) |
|---|---|
| add-on roofs: shingle courses, deck, bargeboards (curled foot), soft warp, eave lifts | `linear_roof.GableRoof` + `linear_roof` (kit 1.12 / 1.16) |
| trim at the wall, flaunching, verge aprons | `junctions.clip_at_tower`, `ride_fillet`, `wall_end_apron`, `_bvh`, `_smooth_up` (the v3 round-wall language, on a straight wall as a 2 km circle) |
| end walls, quoins, mortar | `rubble_walls.path_stone_wall` |
| porch brackets | `timber_walls.hoist_beam(block=False)` (the barn's curved brace) |
| posts, pads, ledger, plate, rafters | `geom.beam / obox / sweep`, the kit's rafter section |
| host arches | `eave_lift` (kit 1.16), `rafter_lift_max` (kit 1.17) |
| seal guard, clearance guard, decals | `guards.register_junction(arc=)` (new optional key), `entrance_clearance`, `composite_decals` (the add-on roofs and end walls are picked up through `LINEAR_ROOFS` / `WALL_FACES`) |

**Stats (full build, `round_01/stats.json`):**
- 719,671 triangles (cap 1,000,000); est. hidden 14.3 % (≤ 15); 10 material slots; Mask on every mesh.
- 56 objects; bbox 17.77 x 9.45 x 11.34 m; 117 decal anchors (validated); build 9.6 min.
- Guards:
  - clearance PASS (2.76 m over the door, on the porch framing);
  - seal probe 0 leaks on all three junctions: lean_to / wall 66,876 rays, porch / wall 36,442, v3 body_roof / round wall 106,092.

**Junction checks (`round_01/builder_extra/`):**
- 13 add-on close-ups (`L01-L07`, `P01-P06`); 11 of them have a `_red` see-through twin (L07 and P02 are elevations). There is no red at either junction.
- The interior-volume ray probe `bx_seethru_r01.py` (adapted from the barn auditor's `aud_seethru_r03.py`) writes `seethru/seethru_r01.json` and `seethru/probe_img/`.
- Probe results at the add-ons:
  - 0 leaks through either junction.
  - The leaks it lists are the host's own: window dark rooms (`_blockers`), and the drum and thatch inside the coarse interior proxy. The same counts appear on the accepted v3 blend at the same cameras (checked).
  - The voids are kit-wide shingle-butt specks, plus pre-existing v3 stone voids beside the east north window lintel (identical on v3).
- One real seam was found and fixed this round: the end walls' coarse mortar sheet stood through the lean-to's deck and covering at its front corners (952 void px). It is now clamped under the deck (5 px).

**Hash rule:** not triggered, not run. `linear_roof.py` and `roof_junction.py` were not edited. The only existing-module edit is `guards.register_junction(arc=None)` plus its read in `junction_seal_probe`. A record without `arc` takes the old point count and the old rng draw.

**Known gaps:**
- `covering="thatch"` is wired but not proved; a rubble or boarded closed front (`front="rubble"`) is not built.
- The `below` check models the host deck and rafter tails, not the eave roll's belly (the lean-to uses `below_clear` 0.08 to cover it).
- The hidden cull skips the add-ons. With the cull's viewpoint loops, a full cull removed rafter and covering faces that are seen from inside the shed and under the hood. As a result, the add-ons' hidden faces are not culled either.
- The porch's bargeboards read heavy (a 0.2 m board on a small hood).
- The host's lifted eave roll passes close over the porch's east verge corner (0.12-0.17 m).
- A thin line of the raised wall head shows under the front arch (a few back-face px).
- Requests for the other track, for later: none needed (no `linear_roof` change was required).

## a1_longhouse_addons round 1 — score 7.8/10

Art Director, modularity rubric (note 12, pass 8.2), notes 15-17. The v3 host is accepted; this grades the lean-to, the porch and their junctions with the host. No producer or client entry after 23:10 was found before writing.

**What I looked at:**
- the six views, `preview/`, `preview_b/`, all 13 builder close-ups and their red twins, the probe output, the recipe, `components/lean_to.py`, `components/porch.py` and `kit/changes/a1_longhouse_addons.md`;
- 20 director shots in `round_01/director_extra/` (`dir_render_r01.py`, copied from v7 r1). There are 8 interior-volume red checks (`i01`-`i08`), 8 exterior junction void twins (`x01`-`x08`), two actor approaches and two thumbnails.
- One host comparison: the same interior cameras on the accepted v3 file (`v3_compare/`, `dir_render_r01_v3cmp.py`).
- One note-16 line-up: `lineup/`, with v3, a1, v5 r08, v6 r04 and the roundhut (`dir_lineup_r01.py`).

**Sealing (verified):**
- The add-ons let in no daylight.
  - `i01` (shed, up to the wall crease), `i02` (shed, west end-wall head), `i04` (host room, north head) and `i08` (under the hood, up to the crease) all read 0 red.
  - `i03`: its 415 px are the open front at the frame edge, so not a leak.
  - `i06` (host attic, behind the lean-to): 1 px.
- `i05` / `i07` (host room and attic behind the porch) read 45 / 533 red. All of it is v3's own door: gaps between the planks and the door head. The accepted v3 file at the same cameras reads 52 / 491, so this is not the add-on's.
- The void twins show only the kit-wide yellow at the shingle butts; there is no red at any add-on junction. The flaunching is continuous along both arched crease lines, and the end-wall heads are closed under the deck.
- Note: the host's inner wall faces are culled, so from inside the host the lean-to ledger and rafter heads are visible through the culled wall (`i06`, `i07`). There is no light path, and this is host-wide behaviour, not an add-on fault.

| axis | score | notes |
|---|---|---|
| 1 Silhouette and massing | 8.1 | Both thatch arches are on theme, and the front arch echoes the barn's eyelid in the line-up. The lean-to reads as a real outshot under its own arch (L07, `x11`). Against that: its front eave and plate are ruler-straight, and the porch looks crammed into its arch from the front (`front.png`, P05, `x09`). |
| 2 Proportion and actor scale | **7.4** | The lean-to opening is 1.86 m clear under the plate, below the village's 2.05-2.15 m door height. The knee braces drop to about 1.38 m, 0.45 m each side of the post. The eave lip over the opening is about 2.0 m, against art bible 7's 2.30 m. Next to the 1.8 m figure (`x10`) the plate is at head height. The porch is fine (2.32 m beam, 2.76 m over the door). |
| 3 Construction logic | 8.0 | Load paths read: brackets carry the beam, posts sit on dressed pads, end walls carry the plate, the ledger is let into the wall. Weak points: the porch bargeboards stand up as square "ears" above the covering (P02, `x09`). The thatch roll passes 0.12-0.17 m over the porch's east verge (P05, `x05`). The bracket brace feet stop on bare wall with no stop or corbel (`x08`, minor). |
| 4 Seams and junctions | 8.6 | See "Sealing" above. The mortar-through-deck seam fix holds (`x01`, `x02`). |
| 5 Distinctness, reuse, village theme | 8.0 | Strong reuse: GableRoof soft options, the junctions' flaunching and aprons, `path_stone_wall` quoins, the barn's `hoist_beam`, the village shingle, lead and lime, all on the 10-slot palette. Same hands as v3, v5 and v6 (line-up). Below 8.2 because of: the lean-to's straight eave and plate and square verge board (note 17 asks for rolled or flared verges and soft eaves); straight walls only, in a village of drums and roundhuts; hand-tuned coupling to the host's arch; the mortar flaunching is fixed even on a timber host; proved on one host only. |
| 6 Technical compliance | 8.8 | 719,671 triangles (cap 1,000,000), hidden 14.3 % (≤ 15), 10 slots, Mask on every mesh, 117 validated anchors, seeded. The add-ons are left out of the hidden cull, which is acceptable while the total stays ≤ 15 %. |

**Verdict: NOT PASSED (7.8; the lowest axis is 7.4).** A short round 2 that changes only parameters and options, no new modules. The sealing work is the strongest part of the round, and both add-ons are already genuinely kit-built and on the village's materials.

**Strengths:**
- An open shed and a door hood with zero add-on light leaks, checked from inside the shed, under the hood and from inside the host.
- `mono_roof` is a good shared core: one call gives the covering, framing, flaunching, aprons, guard registration and the under-the-host-eave check.
- The thatch arches over both add-ons are the round's best note-17 move, and they read as one village with the barn.
- The porch reuses the barn's curved bracket arm unchanged.
- The builder found and fixed the mortar seam honestly, and logged the known gaps candidly.

**Must-fix (round 2):**
1. **Lean-to headroom (art bible 7):**
   - plate underside at least 2.10 m;
   - eave lip over the opening at least 2.30 m;
   - no knee brace below 1.95 m in a walking bay: shorten the brace drop to about 0.25-0.30 m, or replace post plus braces with a cambered or arched plate (see 2).
   - Get there by raising or widening the host's back arch (`LIFT_N`, e.g. 1.5 m over 9-10 m), a pitch of 18-20° and/or a depth of about 2.0 m.
   - The `below` check must still pass. Add the opening's clearance as a guard, like the porch's `entrance_clearance`.
2. **Lean-to soft lines (note 17):** no ruler-straight eave or plate. Give the lean-to its own small arch or sag, as the porch has: `soft.eave_lifts` (about 0.15-0.2 m over the run) or `eave_sag`. The plate and the front eave then curve together and echo the host arch.
3. **Rolled or flared verges on both add-ons (note 17):**
   - Replace the plain square verge board with a flared verge (`verge_flare`) or a rolled edge.
   - On the porch, cut the bargeboards to the covering line and slim them to about 0.12 m, so the "ears" go.
4. **Porch under the thatch:**
   - At least 0.25 m everywhere between the lifted thatch roll's underside and the hood, verges included: raise the front `LIFT` to about 1.4 m, or trim `side` / `overhang`.
   - Extend the `below` check to model the eave roll's belly, so the guard catches this rather than inspection (the builder's own known gap).
5. **Straight-wall limit:** `plane_wall` must size `R` from the run (sagitta ≤ 1 mm, e.g. `R = max(2000, L²/0.008)`) or accept a `run=` length. The 4 m ceiling goes, and a 6 m lean-to works without a hidden failure.

**Should-fix (only if cheap; otherwise record as known limits):**
- A `flashing="lead"` option on `mono_roof`, for timber or boarded hosts (barn, harbour house upper storey), where a lime fillet is wrong.
- A small recipe helper that returns the host `eave_lift` a lean-to or porch needs, so recipes stop hand-tuning `LIFT` / `LIFT_N`.
- A round-wall `W` (the porch on a drum or roundhut door). The junction pieces are already circular, but the straight ledger would gap on a small radius, so this is a later item.
- A dressed stop or pintle under each porch brace foot.
- One FAST smoke call of `porch` on a second host's door (e.g. v6 barn or v7 cottage), one render, to show reuse beyond v3.

**Housekeeping (director):** my first render run used relative paths, and Blender wrote it under `C:\renders\...`. All PNGs were moved into `round_01/director_extra/`. An empty `C:\renders\addon_demos\...` folder tree is left outside the repo (removal was blocked by the sandbox) and can be deleted by hand.

## a1_longhouse_addons round 2 — builder entry

**Scope:** parameters and options only, no new module. I checked the log before starting and again before writing: there is no CLIENT DIRECTION or PRODUCER NOTE newer than the round-1 grade. Edited files:
- `kit/village_kit/components/lean_to.py` (new optional keys; `porch.py` is unchanged and passes them through);
- the demo recipe;
- `kit/changes/a1_longhouse_addons.md` (a "Round 2" section).

Nothing under `buildings/variants/` and no accepted file was touched. `guards.py`, `linear_roof.py`, `roof_junction.py` and `junctions.py` were not edited.

**Must-fixes:**

| # | fix | how | result (full build, `round_02/build_full.log`) |
|---|---|---|---|
| 1 | lean-to headroom | host back arch `LIFT_N` 1.2 m / 8 m -> **1.5 m / 9.5 m, fade 2.8**, centred on the lean-to at x -6.2 (the east north window), so the arch is about 0.07 m at the round end's x -2; lean-to depth 2.2 -> **1.9 m**, overhang 0.30 -> 0.22, z_face 2.86 -> 3.08, pitch 16; knee braces `brace=(0.36, 0.28)` (drop 0.48 -> 0.28) | plate underside **2.235 m at the ends, 2.337 m in the middle** (rule >= 2.10); lowest brace foot **2.057 m** (>= 1.95); eave lip over the opening **2.413 m** (>= 2.30, gate PASS); new GUARDS `lean_to(headroom=(2.10, 1.95))` and `gate=True` (the open front published to the clearance gate) |
| 2 | lean-to soft lines | its own `soft.eave_lifts` (0.18 m over 4.6 m, fade 1.5) plus `ridge_sag` -0.15, `eave_sweep`, `wave`; the plate is laid through `to_world`, so it arches with the eave | the front eave and the plate curve together under the host arch (L02, L08, L09) |
| 3 | rolled / flared verges | `verge_flare` on both (lean-to 0.06 / 0.5 m, porch 0.05 / 0.45 m); new `mono_roof(verge_board=dict(below=0.025, above=0.0))` gives a **0.12 m** bargeboard cut to the covering line on both | the porch's square "ears" are gone (P02, P07). The small upright plates left at the porch's wall corners are the lead verge aprons, not boards. |
| 4 | porch under the thatch | front `LIFT` 1.2 -> **1.4 m**; new `mono_roof(below_roll=...)` guard: rays straight up from every out-from-the-wall vertex of the add-on's covering, verge and roll, against the host's BUILT eave roll (its belly) | porch **0.304 m** smallest gap (rule 0.25, verges included); lean-to 0.234 m (rule 0.10). Spec checks: porch face 0.176 / lip 0.322 m, lean-to face 0.162 / lip 0.231 m. |
| 5 | straight-wall limit | `plane_wall(R=None, run=None)`. R is sized from the run by `wall_R(L) = max(2000, L^2/0.008)`: from `run=` when given, else from the add-on's covering length inside `mono_roof` (`resolve_wall`). An explicit R that bows more than 1 mm over the run raises. | Runs up to 4 m keep R 2000. The demo's 4.36 m covering gets R 2376, and a 6 m lean-to gets R 4500. |

**Stats (full build):**
- 719,805 triangles (cap 1,000,000); est. hidden **12.5 %** (round 1: 14.3); 10 material slots; Mask on every mesh.
- 56 objects; bbox 17.77 x 9.05 x 11.39 m; 111 validated decal anchors; build 9.0 min.
- Seal probe: 0 leaks on all three junctions (lean_to / wall 68,020 rays, porch / wall 36,467, body_roof / round wall 106,397).
- Clearance gate PASS at both the front door (2.759 m) and the lean-to front (2.413 m).

**Renders:**
- `round_02/`: the six views, `stats.json` and `hidden.json`.
- `round_02/builder_extra/` (`bx_render_r02.py`, a copy of r01 with the round-2 coordinates, shift +4.606 / -0.253, and a 1.8 m figure under the lean-to brace):
  - L01-L07 and P01-P06 again;
  - new: `L08_leanto_figure_headroom`, `L09_leanto_front_eave_arch` and `P07_porch_E_verge_vs_roll` (+ red twin).
- Red counts are the same as round 1 shot for shot: 0 at L03-L06, P04 and P06; P01 42 px against 2,246. The large counts at L01, L02, P03, P05 and P07 are sky in frame (checked on the P07 twin).
- `round_02/fast/`: the FAST iteration build and its look shots (scratch).

**Not done (should-fix list, recorded as known limits):**
- `flashing="lead"` for timber hosts;
- a host-arch helper;
- a round-wall `W`;
- a stop under the porch brace feet;
- a second-host smoke test.

**Known gaps:**
- `_roll_gap` is vertical only.
- The gate uses the cruck entrance list (`CRUCK_ENTRANCES`), because `guards.py` was not edited.
- Publishing the lean-to front as an entrance also lets the kit's "walked tops" Mask pass mark the end-wall and pad tops at that front as worn (about 300 faces). This is plausible wear, but it is new.
- The host back slope's arch is bigger (1.5 m), and the back thatch now swells over most of the slope behind the lean-to.

**Hash rule:** not triggered, not run. No existing module was edited, and `lean_to.py` is not used by any baseline building.

## a1_longhouse_addons round 2 — score 8.1/10

Art Director, modularity rubric (note 12, pass 8.2), notes 15-17. The v3 host is accepted; this grades the lean-to, the porch and their junctions with the host, including host settings the demo changed for them. I checked the log before starting and again before writing: there is no CLIENT DIRECTION or PRODUCER NOTE after the round-1 grade.

**What I looked at:**
- the six views, all 16 builder close-ups and their red twins, `fast/cu/`, `build_full.log`, `stats.json`, the recipe, `components/lean_to.py`, `components/porch.py` and the "Round 2" section of `kit/changes/a1_longhouse_addons.md`;
- 31 director shots in `round_02/director_extra/` (`dir_render_r02.py`, the r01 script with round-2 coordinates):
  - 9 interior-volume red checks (`i01`-`i09`; `i09` is new: the shed's W front corner and the plate seat);
  - 11 exterior void twins (`x01`-`x08`, plus new `x13` lean-to W verge vs the roll, `x14` porch wall-corner apron, `x15` lean-to E quoin and plate seat);
  - three actor shots (`x09`, `x10`, new `x16` with the figure under the knee brace), two thumbnails and four zooms (`z01`-`z04`);
  - `dir_pick_r02.py` / `.log`, which ray-picks the object and face behind given pixels.
- One note-16 line-up: `lineup/` (`dir_lineup_r02.py`), with v3, a1, v5 r08, v6 r04 and the roundhut.

**Sealing (verified):**
- **The add-ons themselves are sealed.**
  - Shed: `i01` and `i04` read 0 red. The red in `i02`, `i03` and `i09` is the open front at the frame edge (checked on the clay frames), so not a leak.
  - Under the hood: `i08` reads 0 red.
  - From outside: every void twin reads 0 red. The yellow is the kit-wide shingle butts and v3's window rooms.
  - Front of the host: `i05` / `i07` read 51 / 430 red. This is still v3's own door; round 1 read 45 / 533 and the accepted v3 491.
- **New leak, host attic behind the lean-to.** `i06` reads 186 red, against 1 px in round 1.
  - The picks miss all geometry at `i06` pixels (430-507, 355) and (1012, 354). They are open sky seen from inside the host attic, through three 1-2 cm slits between the host wall head and the deck under the enlarged back arch.
  - One ray passes the outer stone skin at (-2.23, 2.38, 3.71) world straight to SKY.
  - This came from this round's `LIFT_N` 1.2 m / 8 m -> 1.5 m / 9.5 m. It is a light path into a closed volume, so it would show as a fog beam in UE.
- **Inverted-normal stone.** One stone of `A1L_lean_to_end1_stones` (faces 6994-6995, at world (0.414, 2.48-2.51, 2.55-2.60)) renders back-facing on the outer face of the E end wall, 0.13-0.16 m out from the host wall (`z01`, `x02`).
  - It is a flipped stone, not a cut end: it is well clear of the `in_host` clip.
  - Clay hides it. With one-sided materials in UE it would read as a hole or an inside-out stone at the corner a visitor walks past.
  - The pick also found one back-facing host face, `A1L_body_wall_stones` face 99666 at (0.65, 2.352, 2.705). This is probably v3's own.

| axis | score | notes |
|---|---|---|
| 1 Silhouette and massing | 8.3 | The lean-to's plate and front eave now arch together (L09, `x16`). Flared verges and slim boards on both. The porch "ears" are gone (P02). The line-up still reads as one village with the barn's eyelid. Against: the back arch is now 1.5 m over 9.5 m and swells most of the back slope (back.png, L07), so front and back repeat one motif (an eyebrow over a small mono-pitch). The lean-to stands under its arch with about 0.8 m of bare wall above, rather than dying in under the eave. |
| 2 Proportion and actor scale | 8.4 | All of art bible 7 is met and guarded: plate 2.235-2.337 m, lowest brace foot 2.057 m, eave lip 2.413 m. The 1.8 m figure clears the brace by a hand (`x16`, L08). The porch beam is 2.32 m, with 2.759 m over the door. The lean-to is 1.9 m deep, a little under the brief's 2-3 m for a store or byre. |
| 3 Construction logic | 8.3 | The plate is seated on the quoin heads (`i09`, `x15`), the post stands on a dressed pad, and the ledger is let in under the rafter heads. The porch brackets carry the beam (P06). Weak points: the host roll passes close beside the lean-to's W verge at the wall (`x13`), which the vertical-only `_roll_gap` does not measure. The porch brace feet still stop on bare wall (minor). |
| 4 Seams and junctions | **8.0** | The add-on / wall junctions are excellent: 0 red from inside the shed, under the hood and in every void twin, and 0 seal-probe leaks. Two real defects pull it down: the new host wall-head slits under the enlarged back arch (`i06`, 186 px), and the inverted-normal end-wall stone (`z01`). |
| 5 Distinctness, reuse, village theme | 8.1 | **Theme: yes.** The add-ons use only the village's shingle, rubble with quoins, lime flaunching, lead aprons and hewn timber, on 10 palette slots. They carry curved knee braces and the barn's hoist-beam bracket unchanged, arched plates and eaves, sag, sweep and flared verges, all as module options (note 17 satisfied). They read as the same hands as v3, v5 and v6 in the line-up. **Reuse: genuine in the API, not yet shown.** `mono_roof` is one honest core for both. Any straight wall of any length works (`plane_wall` / `wall_R`). The guards (below, below_roll, headroom, gate) make a bad placement fail loudly rather than silently. But both add-ons are still proved on one host only. On low-eaved hosts they depend on a hand-tuned host `eave_lift`. The lean-to has `ends="rubble" / front="open"` only, and there is still no round-wall `W` in a village of drums. |
| 6 Technical compliance | 8.7 | 719,805 triangles (cap 1,000,000); hidden 12.5 % (≤ 15); 10 slots; Mask on every mesh; 111 validated anchors; seeded; 9.0 min build. One inverted-normal stone counts against Nanite hygiene (see axis 4). |

**Verdict: NOT PASSED (8.1; the lowest axis is 8.0, rounded up by 0.1).** This is a clear step up from 7.8. Every round-1 must-fix is met and guarded, and the add-ons are on theme. The two seam defects are small and local. Round 3 is the last allowed round, so it should change parameters and small options only.

**Strengths:**
- All five round-1 must-fixes landed as reusable, guarded module options, not demo tweaks. Examples: `headroom`, `gate`, `below_roll`, `verge_board`, `wall_R` / `resolve_wall`. The guards fail loudly and name the fix.
- The lean-to now reads as a working village outshot: an arched hewn plate on quoined rubble cheeks, one post on a dressed pad, short curved knees and real headroom.
- The porch hood is now on theme: an arched, bell-cast hood with flared verges, slim cut-to-line bargeboards and the barn's curved bracket, sitting 0.30 m clear under a lifted thatch eyebrow.
- Hidden geometry fell from 14.3 to 12.5 %, with the triangle count flat.

**Must-fix (round 3, parameters and small options only):**
1. **Close the host wall-head slits under the back arch (`i06`).**
   - The host's wall head must stay closed to the deck along the whole lifted back eave. There are rays to the sky at about (-2.23, 2.35, 3.70) world, and two more along the crown near x -2.1 and -0.6.
   - Either lower or shorten `LIFT_N` to what the lean-to's guards actually need (the margins are 0.11-0.23 m, so e.g. 1.35-1.4 m over 7.5-8 m, which also cuts the back-slope swell), or close the wall head under the warped deck in the recipe (the stones' top course / mortar to the deck underside).
   - Re-run my `i06` camera (`dir_render_r02.py i06`): it must read ≤ 5 red px.
2. **Fix the inverted-normal stone** in `A1L_lean_to_end1_stones` (faces about 6994-6995, the E end wall's outer face beside the host wall).
   - Make the lean-to's end walls come out with consistent outward normals, for example a normals-consistency pass on the `_end<k>_stones` objects in `lean_to`, or the U-path orientation fixed for `end1`.
   - Show 0 back-facing stone faces on both end walls: the void twins `x01` / `x02` / `z01` with no stone-sized yellow, or a face-normal count in the log.
   - Check whether host face 99666 at (0.65, 2.352, 2.705) is also in v3. If it is, record it only.
3. **Show reuse on a second host (cheap, no new module).**
   - One FAST smoke call of `porch` on another accepted design's door (v6 barn or v5 harbour house), recipe-local, with no accepted file touched.
   - Deliver one render, its guard lines (below, below_roll, clearance) and the call itself: a few lines, with no host `eave_lift` hand-tuning if that host's eave allows.
   - If a `lean_to` call fits on the same host in the same run, add it.
4. **Lateral roll clearance.** `_roll_gap` must also catch a roll passing BESIDE a verge (`x13`): add a nearest-distance check (`bvh.find_nearest` from the same vertices) with the same rule, and log both numbers.

**Should-fix (only if cheap; otherwise record as known limits):**
- Lean-to depth back to 2.0 m if the headroom guards still pass after must-fix 1.
- A dressed stop or pintle under each porch brace foot.
- The neutral entrance list name, a host-arch helper, `flashing="lead"` and a round-wall `W` stay as later kit items. Record them, do not build them now.

## CLIENT DIRECTION (2026-10-18, session 2, 00:22): rounded roofs on square walls (producer note 19) applies to the LEAN-TO

Client's words: "if the walls be square and angular we should counterbalance with rounded roofs. Not just /\ An oval on the rectangle". The client chose **"Rounded hips + soft crown"**. Read producer note 19 at the end of `director/art_bible.md`.
- **The lean-to** is a rectangular shed. Its mono-pitch roof gets:
  - a **softly convex** slope (it bulges gently instead of being a flat plane);
  - its **free end(s) curving round** as a half-cone hip, a rounded catslide end, rather than a square verge.
- Re-use the cottage track's rounded-roof module when it exists. Until then, build the rounded end as a lean-to option in `lean_to.py` (this track may not edit `linear_roof.py` / `roof_junction.py`).
- The porch hood is already to be soft and swept (the 23:10 note).
- **Art Director:** a lean-to with a flat plane and square ends cannot pass; give at most 8.1.
- **The next fixer:** do it first.