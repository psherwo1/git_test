# Handoff: continuing the village production (updated 2026-10-18, desktop session 2)

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

## 4. State at handoff (2026-10-18 ~11:45, end of desktop session 2; nothing running)

**Designs: 11 built, all accepted, final or signed off:**

| Design | State |
|---|---|
| tower_windmill | Signed off on the kit (r8, 9.0) |
| hilltop_keep, wattle_roundhut | Phase-1 versions are the deliverables; the kit builds are the references |
| v1_stone_watchtower | ACCEPTED (r5, 8.5, 937,933) |
| v2_tiered_hall | ACCEPTED by client decision (r7, 980,405), with the darker grimy turret lead in lookdev |
| v3_longhouse_roundend | ACCEPTED (r8 redesign, 8.3, 617,342) |
| v4_mixed | ACCEPTED (r4, 8.4, 938,453) |
| v5_harbour_house (approved building 3, ref4) | FINAL (r8, 8.6, 714,452). Snapshots `*_r04..r08_accepted.*` |
| v6_barn | ACCEPTED (r4 quick fix, director 8.4, audit upheld, 213,529) |
| v7_cottage (step-4 ROOF add-ons) | ACCEPTED BY CLIENT DECISION (r5, 8.1, 418,987): rounded-hip "oval" thatch roofs (note 19), a thatch eyebrow (note 18), a gabled dormer, a soft valley, a round chimney. Known limits in its log |
| a1_longhouse_addons (step-4 WALL add-ons: lean-to, porch, on a demo copy of v3) | ACCEPTED (r4, 8.2, re-audit upheld after the producer's one-line pad fix; 717,226) |

**Kit 1.20.0** (CHANGELOG fully merged through 1.20.0; the 8-building reference table is in 1.12.0). The retired stubs are deleted.
- The add-ons are reusable kit pieces:
  - the valley, chimney and gabled dormer (`roof_addons.py`);
  - the rounded-hip / soft-crown `GableRoof` and the thatch eyebrow (1.19.0);
  - the lean-to (incl. the rounded `RoundLean`) and the porch (1.20.0).
- `tools/build_baseline.ps1` rebuilds 8 buildings (incl. v5; reference `kit/baseline/7_v5_ref/`).

**Open kit items** (none blocks a design):
- **Inside-out RUBBLE_LARGE stone shells,** kit-wide (v3, v5, v7 stack). The fix is `orient_stones` by default, which needs a hash-checked baseline run.
- **Two rounded-roof implementations** (`RoundLean` and the 1.19.0 hipped `GableRoof`) should converge.
- **Eyebrow polish:** the shoulder and the window margin.
- **The v5 polish list:** eave corners, quay ends, ridge-comb slits, lead tabs.
- **Lookdev:** the flat daub on the roundhut / v4, the bark proxy texture, the v2 pale shingles, the heavy moss.

**Binding producer notes added this session:**
- 16: same builders, techniques and materials;
- 17: round structures and soft, organic lines;
- 18: a rectangular / square cottage has at least one eyebrow dormer;
- 19: square walls get rounded roofs (round hips + soft crown, "an oval on the rectangle").

**Client preferences:**
- Time matters: fold direction into the round in progress through the variant log, show early previews, skip avoidable work.
- Reuse existing modules.
- Rounds are capped; ask before going beyond the cap.

**Studies:**
- `lookdev/village_r2/`: all buildings textured, with contact sheets;
- `lookdev/harbour_house/`: the v5 look tests;
- `lookdev/vignette/`: a fjord-village vignette with measurements;
- `director/performance_assessment.md`: Lumen vs the path tracer, fog, memory. The measured Cycles path tracing is about 30 s / frame at 1080p with fog. The client should upgrade to 32 GB RAM.
- **Vignette takeaway:** too many conical towers; the next designs should be low and roofed.

**NEXT:**
1. More LOW, ROOFED designs toward 12-15, following notes 16-19 and using the add-ons. Cap the rounds, and show early previews.
2. The optional kit-wide `orient_stones` default, with a baseline run.
3. Step 5: the Unreal exporter, then the UE 5.8 lookdev test (it measures what the performance assessment estimates).
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
