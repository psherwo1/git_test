# Handoff: continuing the village production (updated 2026-10-17, desktop session 1 -> session 2)

This file lets a new Claude Code session pick up the work with full continuity. Everything is in this repository on branch `claude/blender-buildings-film-nfzv6a`. **Treat the director files as the source of truth and do not re-litigate recorded client decisions.**

## 1. What this project is (as corrected by the client)

- A **hobby film production** aiming for a **high level of polish** (producer note 13). It targets **Unreal Engine 5.8 with Nanite**, renders offline (Movie Render Queue / path tracing), and has **no LED volume**.
- Reference machine (the client's desktop): Ryzen 5 5600X, **16 GB RAM**, RTX 3060 12 GB, Windows 11. Repo at `C:\GitHubDesktop\git_test`.
- A medieval **fjord village of 40-50 placements**, built from **12-15 curated unique designs** (note 14). The shared kit is the **authoring toolbox** for those designs. Variety across placements comes from instancing, rotation and mirroring, PCG decals on the exported anchors, per-instance `Mask` material variation, kit add-ons and set dressing.
- **New structures are at most 1,000,000 triangles** (note 15, a hard requirement). The heroes keep their counts.
- **Team method (the client asked for it explicitly):**
  - one **Art Director** agent grades every round;
  - an **independent audit** must uphold a pass;
  - the pass mark is **8.2**, with decimal grades;
  - building **variants** are graded on the note-12 **modularity rubric**: silhouette, proportion, construction, seams and junctions, distinctness and reuse, technical.

## 2. Read first, in this order

1. `director/production_plan.md`: phases, the sign-off record, the **variant table**, the **KIT DECISION**, and the client's approved plan.
2. `director/art_bible.md`: the producer notes at the end, **1-15**, all binding. Note 12: modularity over detail. Note 13: no LED volume. Note 14: 12-15 curated designs. Note 15: 1 M triangle cap.
3. `kit/village_kit/README.md` (rewritten for kit 1.9-1.10) and `kit/CHANGELOG.md`. The CHANGELOG holds the kit edit rules, the **HASH RULE** and the **reference fingerprint table at kit 1.10.1**.
4. `director/kit_feasibility_director.md` and `director/kit_feasibility_technical.md`: the kit decision and the missing-module lists.
5. The latest entries of `director/log_variant_*.md`. Every CLIENT DIRECTION and PRODUCER NOTE in them is binding.
6. `director/megascans_shortlist.md`: the free texture set. The client downloaded the zips into `materials/`.

## 3. Client decisions (all binding; full text in the files above)

- Pass mark 8.2 with an independent audit; geometry only. No ground dressing (note 10). Detail rules (note 11) and decal anchors.
- **Note 12:** no more detail rounds; reusable modules that combine; modularity rubric.
- **Note 13:** no LED volume; hobby production; high polish.
- **Note 14:** the kit is a toolbox for 12-15 curated designs; the any-combination generator is dropped.
- **Note 15:** new structures are at most 1 M triangles.
- **Kit decision:** the Art Director said "partial" and the technical director "kit_works", recommending the same course. The client said **"Yes proceed"** to this plan, in order:
  1. consolidation, guard-rails, README and the UV fix (**DONE**);
  2. close v1, v2 and v3 through their audits (**done or decided, see section 4**);
  3. **the timber, rectangular and waterfront kit family, built through the timber harbour house** (approved building 3), then a boathouse or barn (**NEXT**);
  4. add-ons: lean-to, porch, chimney, dormer, gable-to-gable valley;
  5. the Unreal exporter (FBX/USD, cm, Nanite, `Mask` as vertex colour, decal_anchors.json, Packed Level Actor / ISM layouts), then a UE 5.8 lookdev test.
- **Watchtower:** the client's square-cabin crown design (accepted).
- **Longhouse:** the client approved a **redesign**: raise the round end so the thatch abuts the drum WALL below the cone eave, so the eaves no longer cross. See the CLIENT DIRECTION at the end of `director/log_variant_v3_longhouse_roundend.md`.
- **The client asked for a textured check** of whether the remaining junction defects are visible at ground level or in a quick pan.
- Never modify `buildings/*/signoff_phase1/` or `buildings/tower_windmill/signoff_kit_r08/`.

## 4. State at handoff (2026-10-17)

**Designs (7 of 12-15):**

| Design | State |
|---|---|
| tower_windmill | **Signed off on the kit** (round 8, 9.0, audit upheld); snapshot in `signoff_kit_r08/` |
| hilltop_keep | Phase-1 version is the signed-off deliverable. The kit build (1,166,874 tris) is the reference |
| wattle_roundhut | Phase-1 version is the signed-off deliverable. The kit build (878,355 tris) is the reference |
| v4_mixed (mill-house) | **ACCEPTED** (round 4, 8.4, 938,453 tris) |
| v1_stone_watchtower (square cabin) | **ACCEPTED** (round 5, 8.5, 937,933 tris) |
| v2_tiered_hall (approved building 2) | **ACCEPTED by client decision** (round 7, director 8.2, 954,925 tris): the remaining junction defects are judged not worth more effort after the textured test (lookdev/junction_test/REPORT.md). Optional lookdev polish: darker, textured lead on the turret aprons |
| v3_longhouse_roundend (approved building 1) | **Redesign IN PROGRESS** (see below). The last complete build is round 6 (director 8.1) |

**Kit: 1.10.1.**
- **1.8.0:** consolidation. One API per concern (eave closure, polygon roofs with any number of sides, masonry, openings); `PlanFrame`; single cull and decal dispatch.
- **1.9.0:** guard-rails on by default (`guards.py`: clearance, decal_validate, seal probe, steep-cone door flags, LOD scope) and a README rewrite.
- **1.10.0:** the UV fix (`uvgrain.py`: grain along pieces, shingles up-slope, no collapsed UVs, no moss on walked tops).
- **1.10.1:** deterministic needle repair. It fixed the keep's turret cap flipping winding.
- **Afterwards:** variant builders added `tier_flashing`, `tier_cull`, `level_probe`, `square_cabin` and `pyramid_roof` upgrades (records in `kit/changes/*.md`). They are **not yet merged into the CHANGELOG**: merge them.
- **Tools:**
  - `tools/build_baseline.ps1`: rebuild buildings, at most 2-3 at once. From PowerShell use `-Only @('id1','id2')`; a comma list via `-File` does not work.
  - `tools/geom_hash.py` (geometry, uv and mask hashes), `tools/geom_diff.py`, `tools/uv_audit.py`, `tools/check_headers.py`.
  - The canonical (order-independent) hasher: `kit/baseline/4_verify/verify_tools/canon_hash.py`.

**Texturing.**
- Lookdev script: `lookdev/scripts/apply_lookdev.py` (`--look r2`). Renders: `lookdev/renders_r2/`, with compare sheets.
- The keep looks good.
- **To tune:**
  - the roundhut's plaster: the trowel pattern still shows up close, so consider a less patterned clay texture;
  - the longhouse's moss: too heavy and uniform;
  - the dressed stone: slightly bright.

**Running when this session ended. Check the results; do NOT relaunch blindly.**
1. **Longhouse redesign workflow** (`workflows/kit_close_variants.js`, only v3, from fix round 8, up to round 10). Journal: `C:\Users\parke\.claude\projects\C--GitHubDesktop-git-test-blender-village\8c996e45-b510-4dd2-9e8e-52ff37fff4ab\subagents\workflows\wf_d6ca71b9-1b3\journal.jsonl`. Progress is visible in `director/log_variant_v3_longhouse_roundend.md`: round 8+ builder entries and score headings. If it was stopped before finishing, write a continuation from the log state, as the earlier continuation scripts did: copy any audit verdicts from the journal into the log first, because fixers read the log.
2. ~~Textured junction test~~ **DONE**: `lookdev/junction_test/REPORT.md`. The client then accepted the tiered hall as it stands.

## 5. Practical notes for this machine

- **Git:** there is no system git. Use GitHub Desktop's bundled git: `C:\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe`. Push auth works.
  - In Windows PowerShell 5.1, commit messages containing double quotes break; use `git commit -F <file>`, written without a BOM (`[IO.File]::WriteAllText`).
  - Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Python:** `C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe` (bpy 5.1.2; `check_env.py` passed). Render flags: `--device GPU --gpu-backend OPTIX`. Do not use the installed Blender 5.2 for the pipeline.
- **Memory:** builds take 4-10 min each. 16 GB RAM means at most 2-3 builds at once. On Windows the cull uses spawn workers, capped at 2 per build (`VILLAGE_CULL_PROCS`), and a dead worker fails over to single-process.
- **Workflow agents:** a chat message the client sends mid-turn is relayed into running workflow agents. Every workflow prompt therefore starts with an AUTH preamble quoting the client's approvals; keep it. Send client direction to agents through the variant logs, **never** by SendMessage to a workflow agent: that spawned a second, conflicting builder once.
- **Large files:** texture zips, extracted textures, lookdev .blend files, `kit/baseline/**/*.blend` and `lookdev/junction_test/src/` are git-ignored.

## 6. One-time setup (DONE on the client's desktop; kept for reference)

Python 3.13 (Microsoft Store), venv `.bpyenv` with `bpy==5.1.2`, `tools/check_env.py` ALL CHECKS PASSED, GPU OptiX confirmed. Sleep on AC is disabled; to restore it, run `powercfg /change standby-timeout-ac <minutes>`. LongPathsEnabled is still 0; the client chose to skip it for now.

## 7. Resume prompt

See `RESUME_PROMPT.md`.
