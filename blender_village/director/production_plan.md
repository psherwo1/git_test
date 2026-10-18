# Production plan: village buildings

## Phase 1: hero buildings (COMPLETE: all three signed off, ensemble approved at 8.4 on 2026-10-16)

**Buildings:**
- hilltop keep
- tower windmill
- wattle roundhut

**Pass rule:** 9/10 from the Art Director, confirmed by an independent sign-off audit.

**Binding client producer notes:**
- Unreal 5.8 / Nanite target
- modular-kit-ready code
- shared or instanced mesh data
- hidden triangles ≤ 15%, with backing surfaces so culling opens no holes
- the shared 15-slot material palette
- the mandatory `Mask` colour attribute

After the three heroes pass, there is an ensemble review for one coherent style.

## Phase 2: kit feasibility decision (after phase 1)

> **CLIENT DIRECTION (2026-10-16, producer note 14): the kit is reframed as an AUTHORING TOOLBOX for 12-15 curated, unique building designs.** The village's 40-50 placements come from instancing those designs (rotation, mirroring), PCG decals on the exported anchors, per-instance material variation through `Mask`, small kit add-ons (lean-to, porch, chimney, roof-covering swaps) and set dressing. The goal of "any combination of modules is clean" and the 40-50-building variant generator are **dropped**. Each design is a curated recipe, reviewed as a building on its own merits; junctions are fixed as each design needs them, and the fixes stay reusable in the kit. **The kit decision below is judged on that basis:** can the kit author the remaining curated designs efficiently and consistently at the pass mark? It is not judged on whether any arbitrary combination is clean. Client's words, accepting the producer's recommendation: "Yes reframe it" (to: "keep the kit as an authoring toolbox for 12-15 curated designs, drop the 40-50 generator goal").

Target: populate a village of 40-50 buildings from 12-15 unique curated designs (see the direction above).

**Assessment.** The director and a technical reviewer assess whether the three hero build scripts break apart into a usable modular kit. A usable kit has:
- parameterised components: walls (stone and wattle, several radii), roofs (conical, bell-cast skirt, tiered, hipped mill cap, thatch), doors and windows, finials and caps, turrets, plinths, timber frames and braces, mill rotor and tail vane;
- assembly into convincing variants at the same 9/10 quality bar;
- correct seams and junctions between parts.

**Proof of concept.** Generate 3-5 variants from the kit. The director grades them against the concept art.

**Decision rule (client-approved):**
- **The kit works:** proceed with the kit, variant generator and Unreal export. *Reframed by note 14:* author the remaining curated designs from the kit (12-15 in total; the 3 heroes and the 4 variants already exist), then export with instance layouts and placement-variation tooling instead of a 40-50 generator.
- **The kit does NOT break apart into a usable kit (or only partly):** build **3 new custom hero buildings**. Client permission was given on 2026-10-16. They go through the same director-led loop and the same producer notes, and reuse any kit parts that do work.

**KIT DECISION (2026-10-17, judged under notes 12-15).** Full texts: `director/kit_feasibility_director.md` and `director/kit_feasibility_technical.md`.

| Reviewer | Verdict | Core reasoning |
|---|---|---|
| Art Director | **partial** | The architecture is real: 4 families plus a compound layer, short declarative recipes, deterministic, with working kit checks. But only v4 is fully accepted, and the vocabulary is only half covered: everything is round or stone, with **no timber or rectangular family** (harbour and waterfront houses, gabled timber halls, boathouses, jettied buildings), no L/T plans and no dormers. About 12-14 designs are possible, in about 8 silhouette families. |
| Technical director | **kit_works** | The architecture is proven: 4 new types from 22-104-line recipes, all passing the director, every fix in a reusable module, rebuilds identical. The TD also built a new rubble barn in about 30 lines that worked first time (332k tris). The weak points are coverage (timber and waterfront, add-ons, pairwise junctions) and consolidation (duplicate frames, culls, decal recipes, eave closures, opening APIs; the keep family's global FR proxy; unsafe opt-in defaults; README stuck at 1.2.0; no exporter). All of them are fixed by adding to the kit, not by rebuilding it. About 12 designs are possible today. |

**Both reviewers recommend the same course:**
- proceed with the kit as the note-14 toolbox, and do **not** fall back to bespoke custom heroes (approved buildings 1 and 2 already exist as kit variants v3 and v2);
- build approved building 3, the timber harbour house, as a new **timber, rectangular and waterfront kit family**;
- **consolidate** the kit and turn its guard-rails on by default;
- add the note-14 add-ons (lean-to, porch, chimney, dormer, gable valley);
- close v1, v2 and v3 through audits (v1 under 1 M triangles);
- update the README;
- build the exporter, then the UE lookdev test.

**Client decision (2026-10-17): "Yes proceed"** with the recommended kit plan, in this order:
1. Kit consolidation, guard-rails on by default, README, and the queued UV fix.
2. Close v1, v2 and v3 through audits (v1 under 1 M triangles).
3. The timber, rectangular and waterfront family through the harbour house (approved building 3), then a boathouse or barn.
4. Add-ons: lean-to, porch, chimney, dormer, gable valley.
5. Unreal exporter, then the UE 5.8 lookdev test.

**Approved new buildings**, chosen to widen the village's vocabulary and taken from the concept art (client-confirmed on 2026-10-16):
1. the stone longhouse ending in a round building with a mossy conical shingle roof (ref1, lower middle);
2. the tall tiered great hall with stacked conical roofs and dormer turrets (ref2 centre);
3. a timber harbour house or boathouse on the waterfront (ref2 / ref3 right side).

**Client decision (2026-10-16): the decal and detail-scale rule (producer note 11) applies in phase 2.** Every migrated hero and every kit variant must follow it and export decal anchors.

**Signed-off phase-1 heroes are preserved** in `buildings/<id>/signoff_phase1/`. If a migrated hero cannot get back to a signed-off pass, the phase-1 version stays the deliverable.

## Phase 3: delivery

- **Note 14 scope:** the 12-15 curated designs. Existing: 3 heroes and 4 variants (v1 watchtower, v2 tiered hall = approved building 2, v3 longhouse with round end = approved building 1, v4 mill-house). Still to author, for example: the timber harbour house (approved building 3), smaller and larger roundhuts, a store or barn, a boathouse and a gatehouse using `square_cabin`. Placement variation: rotation and mirroring, PCG decals, per-instance `Mask` material parameters, kit add-ons and set dressing.
- Export kit pieces and/or buildings for Unreal 5.8: FBX or USD, centimetre scale, Nanite-ready.
- Supply instance layouts for Packed Level Actors.
- Write import notes covering texturing with jointless Megascans surfaces, world-aligned projection and the `Mask` attribute.

## Sign-off record

| Building | Round | Director score | Sign-off audit | Date |
|---|---|---|---|---|
| tower_windmill | 6 | 9.1 | upheld | 2026-10-16 |
| hilltop_keep | 6 | 8.4 | upheld | 2026-10-16 |
| wattle_roundhut | 7 | 8.5 | upheld (round 6 at 8.3 was rejected) | 2026-10-16 |

Sign-off rules in force: pass mark 8.2 (client, "for now"), producer notes 1-10, and all client corrections.

### Phase 2 kit sign-offs (the kit version replaces the phase-1 deliverable)

| Building | Kit round | Director score | Sign-off audit | Date | Snapshot |
|---|---|---|---|---|---|
| tower_windmill | 8 | 9.0 | upheld (round 7 at 8.8 was rejected) | 2026-10-16 | `buildings/tower_windmill/signoff_kit_r08/` (1,146,243 tris, 13.3 % hidden, 106 anchors) |

Rules in force for phase-2 sign-offs: pass mark 8.2, producer notes 1-11, all client corrections.

### Phase 2 kit variants (modularity rubric, note 12; pass mark 8.2 plus an independent audit)

| Variant | Last round | Director | Audit | Triangles | Status |
|---|---|---|---|---|---|
| v4_mixed (mill-house) | 4 | 8.4 | **upheld** | 938,453 | **ACCEPTED** 2026-10-17 |
| v3_longhouse_roundend (approved building 1) | 8 (client-approved redesign: the thatch abuts the raised drum wall below the cone eave) | 8.3 | **upheld** | 617,342 | **ACCEPTED** 2026-10-17. The client had first cleared round 6 (director 8.1) for this stage, then allowed round 8 to finish within a 45-minute cap; it passed inside it. Round 6 is archived in `buildings/variants/v3_longhouse_roundend/round06_archive/`. Non-blocking: eave-end aprons read as stuck-on plates; cone eave 0.24 m over the comb end; the raised drum reads more tower than ref1's low round house |
| v2_tiered_hall (approved building 2) | 7 | 8.2 | rejected (turret masonry through the lead apron upstands) | 980,405 | **ACCEPTED BY CLIENT DECISION** 2026-10-17: "Honestly I think it's fine and my audience won't notice or care. Not worth wasting effort on." The textured junction test (`lookdev/junction_test/REPORT.md`) showed the remaining defects are invisible from the ground except the pale lead apron on a sunlit turret flank. No more work on it. Session 2: the client chose the lookdev mitigation, darker grimier lead on the turret aprons (`apply_lookdev.py`, `OBJECT_GRIME`). |
| v5_harbour_house (approved building 3, the client's ref4 concept) | 8 | 8.6 | **upheld** | 714,452 | **ACCEPTED, FINAL (client)** 2026-10-17 (round 8: the eyelid is one continuous arch, `eyebrow(profile="arch", respace=True)`; round 7 (8.5) was the middle setting). Round 4 (8.3) accepted the hall; round 5 (8.4) added the client's ref4 eyebrow dormer (kit option `GableRoof(eyebrows=)`); round 6 (8.4) made it bigger and bolder; after a textured look test the client chose the middle setting, round 7 (3.5 m wide, 0.90 m lift, a two-light window). Rounds 4-6 are kept as `*_r0N_accepted.*`. Lookdev: darker grime on the tower abutments (lead and mortar). Rubble boat hall with a cruck water gable over a 5.0 m boat arch, a round tower with a timber top under a mossy cone, a broad slumped swept roof (7.0 m, 49 deg, 0.50 m sag: client direction), a stone quay and a jetty. New kit family: `path_timber_wall`, `cruck_frame`, `stone_quay`, `pile_deck`, soft `GableRoof` options; a 30-line barn smoke recipe. Nice-to-haves carried to the boathouse: eave/verge corners, quay free ends, ridge-comb slits, lead tabs |
| v6_barn | 4 | 8.4 | **upheld** (round 4 quick fix closed the post-head wedge: 0 interior rays in 328,320) | 213,529 | **ACCEPTED** 2026-10-17. A thatch barn with a round-arched cruck cart entry under a thatch eyelid; low plinth (client) |
| a1_longhouse_addons (step-4 WALL add-ons: lean-to, porch, on a demo copy of v3) | 4 | 8.2 | **upheld** (re-audit after the producer's one-line pad fix in lean_to.py) | 717,226 | **ACCEPTED** 2026-10-18. `lean_to` (a rounded-hip 'oval' outshot, note 19, in village thatch) and `porch` (a soft hood on curved brackets, also proved on v5) are reusable kit add-ons. The accepted v3 is untouched |
| v1_stone_watchtower (client's square cabin) | 5 | 8.5 | **upheld** | 937,933 | **ACCEPTED** 2026-10-17 (kit 1.10.1; round-4 audit had rejected 8.3) |

### Client direction, 2026-10-16: hero gates closed, modularity first (producer note 12)

The client stopped the hero detail rounds: "we don't need more detail at this point, we need reusable modules that can be combined to complete entirely unique structures". Surface detail waits for materials and textures. Kit variants are graded on the modularity rubric in the art bible (note 12), pass mark 8.2.

Hero outcomes when the gates closed:

| Building | Last kit round | Director | Audit | Deliverable |
|---|---|---|---|---|
| tower_windmill | 8 | 9.0 | upheld | **kit r8** (`signoff_kit_r08/`) |
| wattle_roundhut | 11 | 8.9 | not run (gates closed); r9 8.6 and r10 8.8 were rejected | phase 1 stays the signed-off deliverable; the kit r11 build is the kit's reference hut |
| hilltop_keep | 9 | 8.6 | rejected (wing thatch note 11 / macro-form); r7 8.3 and r8 8.5 were also rejected | phase 1 stays the signed-off deliverable; the kit r9 build is the kit's reference keep |

The interrupted keep round-10 fixer's kit edits are saved in `director/partial_fix_hilltop_keep_r10.patch` and were reverted from the kit.

**Client correction (2026-10-16, producer note 13):** there is no LED volume. This is an amateur hobby production aiming for a high level of polish, in Unreal 5.8 with Nanite, on the client's RTX 3060 12 GB / 16 GB RAM desktop. Final frames can be rendered offline.

**Memory estimate for a 45-building village (measured 2026-10-16).** Instancing saves only 1-6 % today, so each building is about 1 M **unique** triangles: about 45 M unique triangles if every building is unique, roughly 0.7-1.1 GB of Nanite data on disk. At runtime Nanite streams only what is on screen: a streaming pool of about 0.5-1 GB. The 8 downloaded 2K texture sets come to about 100-150 MB compressed, shared by every building through the palette slots. Expected total GPU memory is about 1.5-2.5 GB, to be measured in UE 5.8 with `stat Nanite` / `memreport` after the first export. Levers, largest first: reuse whole buildings (12-15 unique designs placed 3-4 times each); a "background" density preset; true instancing of stones and shingles.

**Texturing readiness (checked 2026-10-16 on the signed-off kit windmill):** every unique mesh has one `UVMap` (box projection at real-world scale, about 1 UV unit per metre, no zero-area UV faces), `Mask` everywhere and the 15-slot palette. Still to do before a texturing pass: check that wood grain (U axis) follows the long axis of planks, shingles and rafters; choose UV0 tiling versus world-aligned in Unreal; build the export (FBX/USD, cm, custom normals, `Mask` as vertex colour); and run one lookdev test in UE 5.8 on the signed-off windmill before any further modelling detail.

Ensemble review 1: 8.4/10, APPROVED. These non-blocking consistency items carry into phase 2:
- **Shared shingle size table.** The keep's turret and lantern caps go up to the chunky 0.35-0.55 m scale.
- **Age passes.** Roughen the windmill's drum masonry and balusters. Add an age pass to the roundhut cone.
- **Shared module.** Merge the stone, shingle and Mask code into one module.
- **Roundhut kit entry point.** Add one to the roundhut.
