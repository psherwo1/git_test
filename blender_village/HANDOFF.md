# Handoff: continuing the village production on a desktop

This file lets a new Claude Code session, for example on the client's RTX desktop, pick up the work with full continuity. Everything the production depends on is in this repository on branch `claude/blender-buildings-film-nfzv6a`.

## 1. What this project is

The client is building geometry-only hero buildings for an **Unreal Engine 5.8 (Nanite) LED-volume virtual production with real actors**. They are modelled in Blender to match the concept art in `reference/`.

**The team structure.** The client asked for one **Art Director agent** directing a team of builder agents. The director grades every round against the concept art. An **independent audit** must uphold a passing grade before sign-off. The client's current pass mark is **8.2/10**, set "for now".

The village will need **40–50 buildings**. Phase 2 is turning the three signed-off heroes into a **modular kit**.

## 2. Where everything is

| Path | What |
|---|---|
| `director/art_bible.md` | Style guide, grading rubric and **producer notes 1–11** (binding client rules, at the end) |
| `director/production_plan.md` | Phases, decision rules, client approvals and the **sign-off record** |
| `director/spec_<id>.md`, `director/log_<id>.md` | Per-building spec, plus the director's round-by-round grades and **CLIENT CORRECTION** sections |
| `director/ensemble_log.md`, `director/log_variants.md`, `director/kit_feasibility.md` | Ensemble review, variant grades and the kit decision (once written) |
| `buildings/<id>/build_<id>.py` | Deterministic build script, the source of truth. It saves `<id>.blend`, `decal_anchors.json` and `kit_variant/` |
| `buildings/<id>/signoff_phase1/` | The signed-off phase-1 version. **Never modify it.** It is the fallback deliverable |
| `kit/village_kit/` | The shared modular kit: README.md (the API), CHANGELOG.md (the **kit edit rules**) |
| `tools/render_review.py` | Standard clay review renders and `stats.json` / `hidden.json`. Pass `--device GPU` on an NVIDIA RTX machine |
| `tools/hidden_tris.py` | Hidden or buried triangle estimate |
| `tools/check_env.py` | Checks that a new machine can continue (bpy, GPU, kit, deterministic rebuild) |
| `workflows/kit_phase_resume.js` | Portable workflow that resumes phase 2 from saved state |
| `workflows/kit_phase_original_cloud.js` | The original phase-2 workflow, for reference |
| `renders/` | Every round's review renders. The director's close-ups are in `director_extra/` |

## 3. Client decisions and corrections (all binding)

The full text is in the art bible's producer notes and the per-building logs.

**Target and scale**
- Unreal 5.8 with Nanite. No manual LODs.
- 40–50 buildings, built as a modular kit.
- At most about 3 buildings within 10 m of actors.

**Pass mark**
- 8.2 (lowered from 10 → 9 → 8.2), with decimal grades.

**Geometry rules**
- Hidden triangles **≤ 15%**.
- When hidden geometry is culled, put **backing surfaces** behind it so no holes open.
- Shared **15-slot material palette**, and no other material names.
- A mandatory **`Mask` colour attribute**:

  | Channel | Meaning |
  |---|---|
  | R | per-piece random |
  | G | wear |
  | B | moss / dirt / damp |
  | A | 1 |

- **No ground dressing.** No loose stones, rubble, paths or aprons; they are not scored either.
- **Producer note 11 (detail-scale rule).** Keep relief under about 2 cm out of geometry; the entrance exception keeps it down to 1 cm near entrances. Put weathering in decals. Export **DECAL_ANCHORS** and `decal_anchors.json` for Unreal PCG.

**Windmill**
- The board sail is a **fixed tail vane on a rear boom** behind the fan wheel.
- The sloping "buttress" in the art is terrain, so it has been **removed**.

**Roundhut**
- Exterior is **mostly intact daub** (80–90%), with only small patches of exposed wattle.

**Fallback approved**
- If the kit is not viable, build **3 new custom buildings**:
  1. the stone longhouse with a round end (ref1);
  2. the tiered great hall (ref2);
  3. the timber harbour house (ref2/ref3).

**Texturing plan (context only)**
- Jointless Megascans surfaces with world-aligned projection in Unreal, driven by `Mask`.

## 4. State at handoff

*(Filled in at the moment of handoff. See section 7.)*

## 5. Desktop setup (one time)

Tested target: Windows 10/11, AMD Ryzen 5 5600X, RTX 3060 12 GB.

**Blender version.** Keep the installed Blender 5.2 for viewing. The pipeline runs on **Blender 5.1.2 as a Python module** in its own venv, which does not touch the 5.2 install. 5.1.2 keeps the builds bit-identical to the signed-off versions.
- 5.1.2 files open fine in 5.2.
- Moving the pipeline to 5.2 later is a separate, deliberate task: rebuild everything and diff the results.

1. **Install Git, and Python 3.13 (64-bit).** `bpy` 5.1 is built only for Python 3.13; Python 3.11 will not work. 3.13 installs side by side with any existing 3.11.
   - Either run `winget install Python.Python.3.13`, or use the python.org installer. Afterwards `py -0` lists the installed versions.
   - Or use `uv`, which avoids touching the system Python:
     ```
     winget install astral-sh.uv
     uv venv .bpyenv --python 3.13
     uv pip install --python .bpyenv\Scripts\python.exe bpy==5.1.2
     ```
     This replaces step 3.
2. **Clone the branch:**
   ```
   git clone -b claude/blender-buildings-film-nfzv6a https://github.com/psherwo1/git_test.git
   cd git_test
   ```
3. **Create a venv with Blender as a module:**
   ```
   py -3.13 -m venv .bpyenv            (Microsoft Store Python has no py launcher: use python3.13 -m venv .bpyenv)
   .bpyenv\Scripts\python -m pip install bpy==5.1.2
   ```
   On Linux/macOS, use `python3.13 -m venv .bpyenv` and `.bpyenv/bin/python`.
4. **Check the environment.** It rebuilds the roundhut and must report ALL CHECKS PASSED:
   ```
   .bpyenv\Scripts\python blender_village\tools\check_env.py
   ```
   Note the `render_flags`, `python` and `root` values it prints. With an RTX 3060 the flags should be `--device GPU --gpu-backend OPTIX`.
5. **Start Claude Code in the `git_test` folder**, either with the Claude Desktop app or `claude` in a terminal. Paste the resume prompt from section 7.

## 6. How the workflow is resumed

`workflows/kit_phase_resume.js` contains the same Art Director, builder, audit and grading prompts as the cloud run. It takes these arguments:
- `root`: absolute path to `blender_village`;
- `py`: absolute path to the venv python;
- `render_flags`: from check_env;
- `hero_results`: what is already done;
- `heroes_to_gate`: any hero whose kit regrade still needs to run, as `[{"id": ..., "round": N}]`. The gate starts by grading that round's existing renders.

It then runs:
1. the hero gates, if any;
2. the four kit variants, with director grades and up to 3 fix rounds;
3. the kit feasibility decision, by the director and a technical director independently.

After the decision, follow `director/production_plan.md`:
- if the kit **works**: phase 3, the variant generator and Unreal export;
- if it does **not work**: the 3 approved new buildings through the same director loop.

## 7. Resume prompt

See `RESUME_PROMPT.md`. Paste its fenced block into the desktop session.
