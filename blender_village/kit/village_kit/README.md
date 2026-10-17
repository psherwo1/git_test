# village_kit: the authoring toolbox for the Fjord Village buildings

**Kit 1.10.0** (2026-10-17; UV and Mask finishing, section 3a). History and per-release verification: `kit/CHANGELOG.md`; variant-era notes:
`kit/changes/*.md`; hash baselines of every kit building: `kit/baseline/`.

> **What the kit is for (client direction, producer notes 12-15).** The kit is an **authoring toolbox for 12-15
> curated, unique building designs** (note 14). The village's 40-50 placements come from instancing those designs
> (rotation, mirroring), PCG decals on the exported anchors, per-instance `Mask` variation, small kit add-ons and
> set dressing. There is no 40-50-building generator, and no promise that any arbitrary combination of modules is
> clean: each design is a curated recipe, reviewed on its own merits with the modularity rubric (note 12), and the
> junction fixes it needs go into the kit. Modularity over detail (note 12). No LED volume; offline renders in
> Unreal 5.8 with Nanite on an RTX 3060 12 GB / Ryzen 5 5600X / 16 GB desktop (note 13). **Every new structure is
> at most 1,000,000 triangles** (note 15).

- **Runtime.** Blender 5.1.2 as a Python module only:
  `C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe build_<id>.py`. A recipe starts with
  `sys.path.insert(0, ".../blender_village/kit")` and keeps its build under `if __name__ == "__main__":` (the
  hidden-geometry cull's spawn workers re-import the recipe).
- **Kit buildings today (7).** Heroes: `hilltop_keep`, `tower_windmill`, `wattle_roundhut`. Variants:
  `v1_stone_watchtower`, `v2_tiered_hall` (approved building 2), `v3_longhouse_roundend` (approved building 1),
  `v4_mixed` (the mill-house). Their recipes are in `buildings/` and `buildings/variants/`.

Contents: [1 Layout](#1-layout-the-shared-core-and-the-families) ·
[2 One API per concern](#2-one-public-api-per-concern-kit-180) ·
[3 Guard-rails](#3-guard-rails-on-by-default-kit-190) ·
[4 Note 15: LOD and density](#4-note-15-lod-and-density-controls) ·
[5 New building recipe](#5-a-new-building-recipe-guide-and-worked-example) ·
[6 Edit rules](#6-kit-edit-rules) · [7 Module reference](#7-module-reference)

---

## 1. Layout: the shared core and the families

Everything a building is made of goes through ONE shared core, so a fix made once reaches every building:

| Shared core module | Producer note | What it owns |
|---|---|---|
| `palette.py` | 7 | the 15 material slots; the ONLY place materials are created; `check()` raises on any other name |
| `mask.py` | 9 | the ONE `Mask` writer (CORNER byte colour, active + render; R per piece, G wear, B moss / damp) |
| `pools.py` | 3 | shared-mesh variant pools placed as linked duplicates (they become ISMs) |
| `stones.py`, `split_stones.py` | 3 | ONE stone generator `make_stone(style, rng, ...)`, plus the vectorised split-stone styles |
| `shingles.py` | - | ONE roofing scale `SIZE_TABLE` (chunky shingle, shake, board ...) and their generators |
| `core.py`, `geom.py`, `tmplmesh.py` | 1, 6, 11 | mesh accumulators (`core.Acc`, `geom.Acc`, `tmplmesh.BatchAcc`), Nanite hygiene, `DetailRule` (note 11), `visibility_cull` (note 6), template-instanced pieces |
| `decals.py`, `anchor_validate.py`, `anchor_audit.py`, `decal_gate.py` | 11 | decal anchors (`DECAL_ANCHORS` empties + `decal_anchors.json`), snapping, validation, audit |
| `assembly.py` | 2 | `Building` (the context `g` every component receives), `KitParams`, `build_building(spec)` |
| `compound.py` | 2 | `Wing` + `build_compound(spec)`: several frames in one building, one whole-building cull |
| `lod.py` | 15 | `tmpl_lod`: height-banded LOD of template-instanced pieces |
| `guards.py` | 6, 7 (bible) | the guard-rails, on by default (section 3) |

Each **family** is a frame (a `Building` subclass holding one building type's dimension table and the state its
components publish to each other) plus the components that read it. A component is a plain function
`component(g, ..., seed=...)` that builds its own `<PREFIX>_<part>` objects.

| Family (`g.FAMILY`) | Frame | Main components | Cull / decals (`finish` dispatch) | Built with it |
|---|---|---|---|---|
| round (hut) | `frame.RoundFrame` | `plinth.drystone_plinth`, `daub.round_daub_wall`, `round_wall.wall_plate`, `conical_roof.conical_roof`, `finial.finial`, `round_apex.turned_apex`, `doors.framed_door` / `door_step`, `interior.interior` | `frame.round_hidden_cull` / `round_decals.round_building_decals` | hut, v4 house wing |
| drum (mill, towers) | `drum_frame.DrumFrame` | `drum_wall.round_stone_drum`, `drum_wall_core`, `drum_door.entrance_step`, `smock_tower`, `shake_apron`, `mill_cap`, `fan_wheel`, `tail_vane.rear_tail_vane`, `raking_props`, `drum_finish`; crowns: `square_cabin` (+ `pyramid_roof`), `tower_roof.round_tower_roof` / `corbelled_parapet` / `drum_ceiling` | `drum_hidden_cull` / `drum_tower_decals_gated`; with a tower roof ("tower"): `tower_hidden_cull` / `round_tower_decals_gated` | mill, v1, v4 mill wing |
| oct (keep) | `oct_frame.OctFrame` | `oct_hall` walls / frame / threshold, `plank_doors`, `windows`, `oct_roof.skirt_roof`, `stone_cone` (collar, cone, lantern, cap), `annex.annex_walls`, `thatch` wing roof / comb / junctions, `turret.side_turret` | `oct_cull.oct_hidden_cull` / `oct_decals.oct_building_decals` | keep |
| tier | `tier_frame.TierFrame` (`declare_bodies`) | `stone_body` + `framed_openings` + `coping_ledge`, `tier_roof.bell_tier` / `roof_flashing` / `tier_finial`, `board_belt` | `tier_finish.tier_hidden_cull` (runs `seal_probe`) / `tier_decals` | v2 |
| composite / plan | `plan_frame.PlanFrame` (or a `RoundFrame` with path walls) | `rubble_walls.path_stone_wall` / `round_stone_body`, `wall_openings`, `linear_roof.GableRoof` + `linear_roof`, `composite.cone_roof` / `set_entrance` / `inside_box` / `inside_round` / `recenter`, `roof_junction.cone_abutment` / `round_eave_fill`, `ball_finial` | `composite.composite_hidden_cull` / `composite_decals` | v3, new rectangular designs |
| compound | `compound.build_compound` with one `Wing` per frame | `junctions.roof_tower_flashing`, `wall_tower_abutment`, `clip_at_tower`, `compound.configure`, `patches_by_azimuth` | ONE `compound_cull` over every wing; anchors re-audited on the whole building | v4 |

Not covered yet (planned, production plan phase 2 steps 3-4): the timber / rectangular / waterfront family (plank
and post-and-plank walls along a path, piles and decks, large boat doors), and the add-ons (lean-to, porch, chimney,
dormer, gable-gable valley).

---

## 2. One public API per concern (kit 1.8.0)

The families grew parallel versions of the same concern. Each concern now has ONE entry point; the family functions
behind it are unchanged, and every old name still exists as a thin wrapper or alias (the seven buildings rebuild
hash-identically through them).

| Concern | Entry point | Old names (kept as wrappers / aliases) |
|---|---|---|
| Frame for a new plan | `components.plan_frame.PlanFrame(prefix, footprint, entrance, entrance_r, entrance_h, detail_rule, hygiene, ground_skirt, **dims)`, `rect_frame(prefix, x0, x1, y0, y1, door=None)` | borrowing `RoundFrame` for a building with no round part |
| Openings | `components.openings.door(width, height, threshold, at)`, `window(width, height, sill, kind, at)`, `opening_spec(kind, ...)`; `spec.at(pos)`; `resolve(spec, family)`; `FAMILY_DEFAULTS` (None sizes = the family's old defaults) | `stone_body.opening`, `wall_openings.door_spec` / `window_spec`, `plank_doors.door_spec`, `windows.window_spec`, `drum_frame.window_spec` (= `drum_window_spec`) |
| Rubble bodies | `components.masonry.masonry_wall(g, name, path= / body= / round=, openings=, **kw)` (re-exports `door`, `window`, `PathMap`, `SurfMap`, `WALL_RUBBLE`, `BODY_RUBBLE`) | `rubble_walls.path_stone_wall`, `rubble_walls.round_stone_body`, `stone_body.stone_body` (three bodies behind one entry: their coursing tables differ) |
| Eave closure | `components.eave.eave_closure(g, r_b, mat, n_az, kind="ring" / "door" / "fill", **kw)`; `KINDS` | `round_roof_parts.eave_closure`, `tower_roof._eave_closure` ("ring"), `conical_roof.build_eave_closure` ("door"), `roof_junction.round_eave_fill` ("fill") |
| Polygonal bell-cast roof | `tier_roof.bell_tier(g, name, on, sides=N, engine=None)`: 8 sides -> `OctRoof`, any other N (or `engine="pyramid"`) -> `pyramid_roof` / `PyramidSurface`; both share one surface protocol (`n`, `tanh`, `phi`, `c`, `rot`, `p_lip`, `Pp`, `zb`, `surf`) so `roof_flashing`, `roof_clearance`, `stone_body(below=)`, `tier_finial`, `tier_decals` work on either | `pyramid_roof.pyramid_roof` (still public, e.g. `square_cabin(roof=)`) |
| Hidden-geometry cull | `components.finish.hidden_cull(g, family=None, **kw)` | the family culls in the table above |
| Decal recipe | `components.finish.building_decals(g, family=None, **kw)`; `family_of(g)` | the family decal recipes |
| Junction aprons | `junctions.wall_end_apron` (a lead plate on a WALL face at a cut eave lip), `roof_junction.cone_nose_apron` (over a linear roof's eave nose against a cone) | the two functions both called `end_apron` (deprecated aliases) |
| Keep-family proxy | `Building.activate()` (called before every step); `OctFrame` / `TierFrame` point `oct_frame.FR` at themselves | the single global `FR` (still read inside the keep family) |

Still separate on purpose (an identical merge would move every vertex of a signed-off building): `OctRoof` vs
`PyramidSurface` bodies, the three rubble bodies, the seven family culls and decal recipes, and the keep family's
`FR` reads (CHANGELOG 1.8.0 explains each).

---

## 3. Guard-rails, on by default (kit 1.9.0)

`build_building` and `build_compound` run these on every building (`village_kit/guards.py`). A recipe that cannot
pass one opts out **explicitly, per guard, with a reason** (a sentence; it is logged in every build as
`GUARD OPT-OUT ...`). An unknown guard name, an empty reason, or switching a guard off any other way raises.

| Guard | What it checks / does | When it runs | On failure |
|---|---|---|---|
| `clearance` | `guards.entrance_clearance`: for every entrance the door components published (`guards.entrances_of`: the hut family's framed door, a drum door, the keep's arched and annex doors, `stone_body` and `wall_openings` doors; or the spec's `entrances=`), rays go straight up from a 5 x 5 grid of stations across the clear width and 0.15-0.75 m in front of the face; the door's own parts (frame, lintel, leaf, step, ironwork, rooms behind) are passed through. The lowest hit is the eave lip over the doorway: it must be **>= 2.30 m** (art bible 7) **and >= the door head** | after the last step (after the cull, after `recenter`); in a compound per wing, before the wings are placed | `guards.ClearanceError` naming the building, the entrance, the lip height, the station and the object |
| `decal_validate` | `anchor_validate.validate_anchors` is APPLIED (snap, drop, de-duplicate; `validation` counts in the JSON) instead of only reporting. `decal_validate` absent = `True`; a recipe's dict still passes its own keywords | after the decal recipe | invalid anchors are dropped |
| `seal_probe` | `guards.junction_seal_probe` at every roof-through-body junction a kit module registered (`guards.register_junction`): `shake_apron` (apron / smock tower), `stone_cone.shake_collar` (collar / stone cone), `thatch.thatch_junctions` (wing thatch / turret, wing thatch / hall), `roof_junction.cone_abutment` (linear roof / round body), `junctions.roof_tower_flashing` (roof / tower, on the compound). Seeded exterior rays (24 azimuths x 10-80 deg) are aimed at targets 8 cm inside the covering within 0.6 m of the body face (away from eave lips, verges and comb tips); a ray that passes the target and reaches the sky, the interior under the roof or the hollow body is a leak. The tier family runs its own `seal_probe.through_seal_probe` from `tier_hidden_cull(seal=True)` | after the last step; in a compound after the whole-building cull, on the placed building | `seal_probe.SealError` naming the junction, the point, the ray and what it reached |
| `steep_cone_door` | `RoundFrame(steep_door="auto")`: a cone steeper than `frame.STEEP_CONE_DEG` (52 deg, the top of the bible's hut range) gets `DOOR_INFILL_DECK` and `EAVE_CLOSURE_DOOR_HALF_DEG = 1.0` (the v4 round-4 door-head fix) | frame construction | (flags set; cones <= 52 deg unchanged) |
| `lod_scope` | a `lod.tmpl_lod` rule is unregistered at the end of its building / compound wing (it can no longer leak into the next wing) | after the last step of each frame | (always on) |

Opting out:

```python
build_building(dict(..., opt_out=dict(clearance="<why this building cannot meet it>")))
build_building(dict(..., opt_out=dict(seal_probe={"shake collar / stone cone": "<why>"})))   # one junction only
Wing("mill", DrumFrame, "V4M", ..., opt_out=dict(decal_validate="<why>"))                   # one wing only
RoundFrame(..., steep_door=False)                                                           # + a comment saying why
```

Current opt-outs (all recorded in the recipes and in CHANGELOG 1.9.0): `hilltop_keep` -- `seal_probe` at
"shake collar / stone cone" (signed-off hero; 3 sub-pixel probe rays thread the jagged comb); `v4_mixed` --
`seal_probe` at "house roof / mill tower" (accepted variant; 13 of ~23k probe rays pass the trimmed roof beside the
drum). Both are queued for their family's next round; every other guard runs on all seven buildings.

`tools/guard_probe.py <file.blend> <building_id>` runs the clearance gate and the seal probe on an already-built
kit building, read-only, to see what the guards will say before a rebuild.

Other checks that were already on and stay on: `tier_frame.roof_clearance` (roof against roof, >= 0.5 m, every
tier), the drum family's rotor / tail clearances (`rotor_checks`, in `drum_finish`), the palette check, the decal
gates of the hut / keep / drum families, and `core.nanite_clean` / `geom.strict_clean` hygiene.

### 3a. UV and Mask finishing (kit 1.10.0, on by default)

After the guards and the decal anchors, `build_building` and `build_compound` run `uvgrain.finish_building` on the
whole building. It writes UVs and `Mask` B only (never a vertex, polygon or material: the geometry hash is unchanged):

- **Grain along the piece** (`uvgrain.regrain_mesh`): every face of `M_timber`, `M_timber_weathered`,
  `M_roof_shingle` and `M_roof_shake` is re-projected per piece (an edge-connected loose part, split by its Mask R
  byte). Timber: V runs along the piece's PCA long axis (continuous over the whole piece; U across the face, or
  wrapped round the axis for round / square poles; end grain gets a planar map). Shingles and shakes, and sloped
  timber sheets with no long axis (cone decks, apron soffits): V = height / sine of slope, so the grain runs up the
  slope on every face. About 1 UV unit per metre, with a per-piece offset. V is the grain axis because the wood
  textures' grain runs vertically in the image and the look-dev test (`lookdev/scripts/analyze_uv_grain.py`)
  measures dP/dv. `M_thatch` keeps its UVs.
- **No collapsed UVs**: any face (any slot) whose UV/3D area ratio is under 0.25 (first triangle or whole face) is
  re-mapped with the nearest rigid map at 1 UV unit per metre, centred on its old UV centre.
- **No moss on walked tops** (`mask.clear_walked_tops`): for every entrance (`guards.entrances_of` or the spec's
  `entrances=`; compound wings are transformed to world), up-facing faces (n.z > 0.7) within the clear width +
  0.1 m each side, from 1.0 m inside the wall face to 1.5 m out, at foot level, get Mask B <= 0.04 (byte 10).
  Step fronts, ends and outer edges keep their B. The entrances are saved as the scene property `kit_entrances`.

Measure with `tools/uv_audit.py <file.blend> <out.json>` (the look-dev rules over every object, plus the walked
tops) or `tools/uv_measure.ps1 -Step <step>`. `tools/uv_fix_preview.py <in.blend> <out.blend>` applies the UV part
to an existing build in seconds (for iterating). A recipe can switch the pass off only with `uv_finish=False`
(nothing does).

---

## 4. Note 15: LOD and density controls

Note 15's order: (1) drop hidden and near-hidden geometry, (2) coarsen stone and shingle tessellation on faces seen
only from mid-distance (above about 4 m, roof tops), (3) reuse pooled pieces. Never cut silhouette, entrance or
ground-contact detail. Measure with `tools/render_review.py` (`stats.json` `triangles`, the authority) or the build
log's last line.

| Control | Where | What it does | Example |
|---|---|---|---|
| `lod.tmpl_lod(g, z=1.2, step=2, parts=DRUM_LOD_PARTS, keep=None, keep_r=1.3, keep_z=2.6, bands=())` | first step of a frame whose parts are `tmplmesh.BatchAcc` pieces (drum family) | every piece of a listed part whose LOWEST point is above `z` is re-meshed on every `step`-th grid line of its template (same outline corners, arrises and placement; thinner face grid); `bands=[(z_b, step_b)]` coarser higher up; pieces in the entrance zone (`keep`, default the frame's door, r `keep_r`, below `keep_z`) and below `z` keep full density; `"pool_corbel*"` thins a pooled variant. Since 1.9.0 the rule ends with its wing / building | v4 mill: `dict(z=0.6, step=2, bands=[(3.0, 3)], parts=DRUM_LOD_PARTS + ("pool_corbel*",))` took v4 from 1.39 M to 0.94 M with no visible change |
| `lod.tmpl_lod_report(g)` | a step after the geometry | logs pieces thinned and triangles saved per part | |
| `DAUB_GRID=(H_S, H_Z, H_CR[, h_fine])` | `RoundFrame` attribute (set with `compound.configure` or a step) | the daub coat's grid spacing along / up the wall and at crack margins | v4 house `(0.075, 0.07, 0.035, 0.0125)` |
| `PLINTH_DENSE=f` | `RoundFrame` attribute | plinth boulders outside the entrance zone at `f` x the hero's mesh density | v4 house `0.55` |
| `SH_RING_STEP=m` | `RoundFrame` attribute | cone shingles get a cross-section ring every `m` above the butt (default 0.07 m; the butt rings stay) | v4 house `0.21` |
| `DrumFrame(rubble=dict(plain=dict(hr=(lo, hi), lr=(lo, hi))))` | drum frame parameter | larger courses / longer stones (within bible 3: courses 8-25 cm, lengths 20-70 cm) = fewer stones | v4 mill `hr=(0.10, 0.21), lr=(0.20, 0.68)`; v1 `hr=(0.10, 0.22), lr=(0.20, 0.70)` |
| `drum_wall_core(g, n_th=...)` | drum family step | the wall-core backing's angular resolution | v4 mill `n_th=96` |
| cull targets / views | `*_hidden_cull(g, targets=...)`, `Wing(cull_targets=...)`, `build_compound(cull_max_views=...)` | which parts the note-6 cull may thin (backed pieces only) and how many viewpoints it uses (build time) | v4 `cull_max_views=300` |

Not yet available (the next step for v1, which is still over the cap at 1,057,164): an equivalent of `tmpl_lod` for
the non-template stone and shingle paths (`stones.make_stone`, `conical_roof` shingles, `linear_roof` coverings),
and cross-building pooling (pools are per building).

---

## 5. A new building: recipe guide and worked example

1. **Pick the frame.** A rectangular or free-form plan: `PlanFrame` (or `rect_frame`). A round daub hut:
   `RoundFrame`. A stone drum / tower: `DrumFrame`. Stacked polygonal or round bodies under bell-cast tiers:
   `TierFrame` + `declare_bodies`. Two families side by side: `build_compound` with one `Wing` each.
2. **One dimension table.** Put every number in one `KitParams(...)` (unknown keys raise on `set`) or one dict per
   component; nothing hard-coded in steps. The principal entrance faces -Y; the base is centred on the origin
   (`recenter` as the last geometry step if the plan is not built centred).
3. **Openings.** `door(width=1.0, height=2.10)` / `window(width=0.5, sill=1.25)` from `components.openings`
   (also re-exported by `masonry`); place them by path distance `(s, spec)`, azimuth `(az_deg, spec)` or
   `spec.at(...)`. Clear doors 0.95-1.10 m x 2.05-2.30 m (bible 7).
4. **Walls, then roofs.** `masonry_wall(g, name, path= | round= | body=)`; then the roof (`linear_roof`,
   `conical_roof`, `bell_tier`, `pyramid_roof` ...). Plan the eave so that **the eave lip over every door is at
   least 2.30 m**: the clearance guard fails the build otherwise (a 45 deg roof with a 0.45 m overhang needs the
   deck at the wall face at about 3.0 m).
5. **Junctions.** Use the kit's junction modules (`roof_junction.cone_abutment`, `junctions.roof_tower_flashing`,
   `tier_roof.roof_flashing`, `composite.inside_box` / `inside_round` clips ...). If a pair you need has none, add it
   to the kit (and register it with `guards.register_junction` if a roof meets a body), not to the recipe.
6. **Finish.** `finish.hidden_cull` as the last step before `recenter` (note 6), `decals=finish.building_decals`
   (note 11). Leave the guard-rails on; opt out only with a reason.
7. **Build to a scratch path** through an output override (`<PREFIX>_OUT=...`), read the log (`clearance gate`,
   `seal probe`, `decal anchor check`, the triangle count), then `tools/render_review.py` for `stats.json`
   (triangles <= 1,000,000, hidden <= 15 %, palette, `Mask`) and the six review views.
8. **Fingerprint** with `tools/geom_hash.py`; a second build must give the same hashes (determinism).

**Worked example: a rubble barn under a shingle gable** (9.0 x 6.0 m, 45 deg roof, door in the -Y wall, two
windows at the back). It builds as written (kit 1.9.0: 373,425 triangles, 46 decal anchors, about 5 minutes with
the cull) and passes every guard; the recipe lives in `buildings/<id>/build_<id>.py`:

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kit"))
from village_kit.assembly import KitParams, build_building
from village_kit.components.composite import recenter
from village_kit.components.finish import building_decals, hidden_cull
from village_kit.components.linear_roof import GableRoof, linear_roof
from village_kit.components.masonry import door, masonry_wall, window
from village_kit.components.plan_frame import PlanFrame

KIT = KitParams(x=4.5, y=3.0, wall_z=3.0, pitch_deg=45.0, overhang=0.45)    # the ONE dimension table
X, Y = KIT["x"], KIT["y"]
ROOF = GableRoof(x0=-X, x1=X, half=Y, wall_z=KIT["wall_z"], pitch_deg=KIT["pitch_deg"],
                 overhang=KIT["overhang"], verge=(0.40, 0.40), name="roof")
PATH = [(-X, -Y), (X, -Y), (X, Y), (-X, Y), (-X, -Y)]          # counter-clockwise: interior on the left
OPENINGS = [(X, door(width=1.0, height=2.10)),                   # path distance s: the middle of the -Y wall
            (2 * X + 2 * Y + 2.5, window(width=0.5, sill=1.25)),  # two windows in the +Y wall
            (2 * X + 2 * Y + 6.5, window(width=0.5, sill=1.25))]

def top(x, y):                                                   # wall heads tuck 2 cm into the roof deck
    return float(ROOF.under_z(ROOF.to_local([[x, y, 0.0]])[0][1])) + 0.02

if __name__ == "__main__":                                       # spawn workers re-import this file
    out = os.environ.get("BARN_OUT", os.path.join(os.path.dirname(__file__), "rubble_barn.blend"))
    build_building(dict(
        prefix="BARN", collection="BARN", building_id="rubble_barn", frame=PlanFrame,
        params=dict(footprint=(-X, X, -Y, Y), entrance=(0.0, -Y)),
        steps=[(masonry_wall, dict(name="walls", path=PATH, top_fn=top, openings=OPENINGS, seed=11)),
               (linear_roof, dict(roof=ROOF, covering="shingle", seed=12)),
               hidden_cull, recenter],                           # note 6 cull (family "plan"), then centre the plan
        decals=building_decals,                                  # note 11 anchors; the decal gate is on by default
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json")))
```

What the guards say for it (build log): `clearance gate BARN walls_0: door head 2.22 m, eave lip over it 2.446 m
... on BARN_roof_rafters: PASS` -- with the deck at 2.55 m (the technical review's probe barn) the rafter feet would
hang at about 2.0 m and the build would stop with `ClearanceError`; `decal anchor check (applied)`: 59 checked, 13
dropped because their footprint leaves the wall, 46 kept; there is no roof-through-body junction to probe. A plan
with a cone, a tower or a tier gets the seal probe automatically from the module that builds the junction.

---

## 6. Kit edit rules

These rules apply to every agent that edits `kit/village_kit` (they are also at the top of `kit/CHANGELOG.md`):

1. **Add, do not change.** You may add modules, functions and optional parameters whose defaults keep the old
   behaviour. Never change the behaviour or the signature of an existing kit function another building uses.
   The only deliberate exceptions are guard-rail defaults approved by the client's plan (kit 1.9.0); such a change
   ships with an explicit, reasoned opt-out in every recipe it would otherwise alter, or with a real fix recorded
   per building.
2. **Prove it on all seven buildings.** After any kit edit, rebuild every kit building into a scratch step folder
   (`powershell -File tools/build_baseline.ps1 -Step <step>`: at most 3 builds at once, each to
   `kit/baseline/<step>/<id>/`), fingerprint them (`tools/geom_hash.py`, done by the script) and compare with the
   previous step (`tools/geom_diff.py`). Geometry, UV and mask hashes must be identical unless the change is meant
   to alter geometry; then list every changed object. Triangle counts of untouched buildings must not drift (the old
   +-0.5 % rule is the outer limit, hash identity is the target).
3. **Never overwrite deliverables while proving.** Build only to scratch paths through the output overrides
   (`KEEP_OUT`, `HUT_OUT`, `MILL_OUT`, `WATCH_OUT`, `HALL_OUT`, `LONG_OUT`, `V4_OUT`); never write a delivered
   `.blend` / `decal_anchors.json`, `buildings/*/signoff_phase1/` or `buildings/tower_windmill/signoff_kit_r08/`.
4. **Fixes go into modules, not recipes.** A recipe holds numbers and the step order; a junction or a module fix
   lives in the kit so every building gets it.
5. **Determinism.** Seeds are explicit parameters (`np.random` with fixed seeds, `crc32`-salted derivations, never
   `hash()`); two builds of one recipe give identical hashes.
6. **Document.** Record every kit change in `kit/CHANGELOG.md` under a new version heading (what changed, why,
   which buildings were rebuilt and their fingerprints). Keep module headers true: `tools/check_headers.py` reports
   documented signatures that no longer match the code. Keep this README current.
7. **Machine.** 16 GB RAM: at most 3 builds at once; a build takes 4-10 minutes. Never kill a python process you did
   not start.

---

## 7. Module reference

Conventions: metres, Z up, ground at Z = 0, base centred on the origin, principal entrance facing -Y. `az` is
measured from -Y toward +X (`core.az_pt`); a math angle `theta` has x = cos, y = sin (`cone.az2th`). Objects are
`<PREFIX>_<part>`; pooled linked duplicates `<PREFIX>_<part>_<nnn>` in `<PREFIX>_kit_instances`. One `Acc.add()`
call is one piece (Mask R and G per piece).

### Core

| Module | API |
|---|---|
| `core.py` | noise (`Noise`, `fbm`, `n2`, `ring_noise`, `smoothstep`); primitives (`tube`, `open_tube`, `rbox`, `lathe`, `slab` ...); `Acc(name, sharp, cull, moss, z_clamp, b_fn, hygiene)`; `nanite_clean`; `DetailRule(min_relief=0.02, entrance_relief=0.01, entrance, entrance_r=3, entrance_h=2.5)` (note 11); `visibility_cull(targets, extra_views, procs, objects, extra_by_target)` (note 6, Windows spawn pool, `VILLAGE_CULL_PROCS`); `ring_views`, `review_cameras`, `review_views`; `reset_scene`, `new_collection`, `count_triangles`, `save_blend`, `log` |
| `geom.py` | vectorised primitives (`rbox_v`, `obox`, `beam`, `sweep`, `lathe_rz`, `prof_*`), the keep's noise table, `strict_clean`, `Acc` / `finalize` |
| `tmplmesh.py` | template-instanced pieces (`tmpl_box`, `tmpl_rings`, `BatchAcc`, `mesh_tmpl`, `hewn_beam` ...); `LOD_HOOK` (set by `lod`) |
| `palette.py` | `PALETTE`, `material(name)`, `check(name)`, `slots_in_use(objects)` |
| `mask.py` | `write_mask(me, r, g, b, b_fn, moss)`; kit 1.10.0: `clear_walked_tops(objects, entrances, b_walk=0.04)`, `walk_zone_faces`, `WALK_*` |
| `uvgrain.py` | kit 1.10.0, the final UV writer: `finish_building(objects, entrances)`, `finish_uvs(objects)`, `regrain_mesh(me, M)`, `face_components`, `GRAIN_SLOTS`, `ROOF_SLOTS`, `FIX_RATIO` |
| `pools.py` | `Pools(prefix, collection)`: `g.pools.mesh(pool, k, make, sharp)`, `g.pools.place(mesh, part, R, t, scale)` |
| `stones.py` / `split_stones.py` | `make_stone(style, rng, half, **params)`: `rubble`, `dressed`, `voussoir`, `footing`, `plinth_*`, `pad`, `spall`, `chink`, `boulder`, `flag`, `hearth`, `coursed`, `coursed_poly`, `split_<style>`; `min_relief` (note 11) keeps the random draws |
| `shingles.py` | `SIZE_TABLE` (`shingle` 0.35-0.55 m wide, 0.30-0.40 m exposure; `shingle_apex`, `starter`, `shake`, `board`, `skirt_board`, `collar_shake`, `comb_shake`, `hip_board`, `shingle_small`); `shingle_mesh`, `shake_mesh`, `board_mesh`, `riven_shakes`, `course_widths` |
| `decals.py` | `DecalAnchors` (`add`, `add_hit`, `build_collection`, `export_json`), `SurfaceProbe(objects)`, placement helpers `base_ring`, `tops`, `below_points`, `above_opening`, `opening_corners`, `wall_scatter`; 40-120 anchors per building |
| `anchor_validate.py` | `validate_anchors(da, probe, apply, reach, offset, clear, min_sep, exclude_objects, ..., strict, walk_zones)`; `STRICT_R11` |
| `anchor_audit.py`, `decal_gate.py` | the director's anchor audit; door walk zones |
| `assembly.py` | `KitParams` (`set`, `variant`), `Building` (`acc`, `pools`, `decals`, `activate`, `FAMILY`), `build_building(spec)`: keys `prefix`, `collection`, `building_id`, `frame`, `params`, `steps`, `decals`, `decal_validate`, `opt_out`, `entrances`, `uv_finish` (1.10.0, default True), `out`, `decal_json`, `decal_meta` |
| `compound.py` | `Wing(name, frame, prefix, params, steps, at, yaw_deg, decals, decal_validate, cull_targets, reach, door, view_heights, crane_heights, solid, ring_n, eye_heights, opt_out, entrances)`; `build_compound(spec)`: `collection`, `building_id`, `wings`, `junctions`, `cull`, `cull_procs`, `cull_max_views`, `decal_audit`, `decal_max`, `opt_out`, `uv_finish` (1.10.0), `out`, `decal_json`, `decal_meta`; `configure(g, **attrs)`, `patches_by_azimuth` |
| `lod.py` | `tmpl_lod`, `tmpl_lod_report`, `register`, `unregister`, `DRUM_LOD_PARTS` |
| `guards.py` | `GUARDS`, `opt_outs`, `entrances_of`, `entrance_clearance`, `lip_over`, `ClearanceError`, `register_junction`, `junction_seal_probe`, `seal_junctions`, `probed_junctions`, `end_lod_scope`, `after_steps` |

### Components (by family; `components/`)

| Family | Modules |
|---|---|
| consolidated entry points | `openings`, `masonry`, `eave`, `finish`, `plan_frame` |
| round | `frame` (`RoundFrame`, `round_hidden_cull`, `HIDDEN_CULL_TARGETS`, `STEEP_CONE_DEG`), `plinth`, `daub`, `wattle`, `round_wall`, `cone`, `conical_roof`, `round_roof_parts`, `finial`, `round_apex`, `doors`, `timber`, `interior`, `round_decals` |
| drum | `drum_frame` (`DrumFrame`, `drum_finish`, `drum_hidden_cull`, `R_out`), `drum_wall`, `drum_band`, `drum_door`, `shake_apron`, `smock_tower`, `mill_cap`, `fan_wheel`, `tail_vane`, `raking_props`, `rotor_checks`, `drum_decals`, `tower_roof`, `tower_decals`, `square_cabin`, `pyramid_roof` |
| oct (keep) | `oct_frame` (`OctFrame`, `OctRoof`, envelope functions), `oct_hall`, `stone_wall`, `plank_doors`, `windows`, `oct_roof`, `stone_cone`, `annex`, `thatch`, `turret`, `hewn`, `oct_cull`, `oct_decals` |
| tier | `tier_frame` (`TierFrame`, `declare_bodies`, `roof_clearance`, `roof_z`), `stone_body`, `tier_roof`, `board_belt`, `tier_finish`, `seal_probe` |
| composite / plan | `rubble_walls`, `wall_openings`, `linear_roof`, `roof_junction`, `composite`, `ball_finial`, `windows` (`window_spec` family dicts) |
| compound junctions | `junctions` (`roof_tower_flashing`, `wall_tower_abutment`, `clip_at_tower`, `wall_end_apron`, `tower_of`, `round_wall_of`) |

Each module's header documents its public signatures (checked by `tools/check_headers.py`).
