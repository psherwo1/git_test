# Resume prompt for the desktop session

## Before you paste: do these yourself on the desktop

The session cannot do these, because they have to happen before it exists.

1. **Install the tools.**
   - Python 3.13: already done, from the Microsoft Store.
   - Git for Windows (git-scm.com).
   - Claude Code (the Desktop app or the CLI), signed in.
   - An up-to-date NVIDIA driver for the RTX 3060.
2. **Clone to a short path.** In PowerShell or a terminal:
   ```
   mkdir C:\work
   cd C:\work
   git clone --depth 1 -b claude/blender-buildings-film-nfzv6a https://github.com/psherwo1/git_test.git
   ```
   - It is about 1 GB shallow, or 2.2 GB with full history.
   - Sign in to GitHub if asked, using an account that can push to psherwo1/git_test.
   - Leave 5 GB or more free.
3. **Open Claude Code in `C:\work\git_test`.**
   - Desktop app: start a new session on that folder.
   - Terminal: `cd C:\work\git_test` then `claude`.
   - Choose a permission mode that lets it run commands and edit files without asking each time (auto or accept edits). Otherwise the multi-hour run stalls while you are away.
4. **Paste the fenced block below.**

The session checks and fixes the rest itself (section PREFLIGHT in the prompt): long paths, Git push access, the GPU driver, sleep settings, disk space, the venv and bpy.

## The prompt

Copy everything inside the fence below.

```
You are taking over an in-progress production from a cloud Claude Code session. Work in this repository on branch claude/blender-buildings-film-nfzv6a. Use a workflow / multi-agent orchestration as described below. I am explicitly asking for it, as I did in the original session.

PROJECT
- Three hero buildings (hilltop keep, tower windmill, wattle roundhut) were modelled in Blender to match my concept art (blender_village/reference/).
- They are geometry only, for an Unreal Engine 5.8 Nanite LED-volume virtual production with real actors.
- Organisation:
  - One Art Director agent directs a team of builder agents and grades every round against the concept art.
  - An independent audit must uphold a passing grade.
  - My current pass mark is 8.2/10 with decimal grades.
- All three heroes are signed off (phase 1).
- Phase 2 is in progress: turning them into a modular kit (blender_village/kit/village_kit) for a 40-50 building village.

READ FIRST, IN THIS ORDER
- blender_village/HANDOFF.md (state, file map, all my decisions, setup).
- blender_village/director/production_plan.md (phases, decision rules, sign-off record).
- The producer notes 1-11 at the end of blender_village/director/art_bible.md (binding rules).
- blender_village/kit/village_kit/README.md and CHANGELOG.md (kit API and kit edit rules).
- The latest sections of blender_village/director/log_*.md, including every CLIENT CORRECTION.
Treat these files as the source of truth. Do not re-litigate decisions recorded there.

PREFLIGHT (check each item; fix what you can; ask me only for what needs me, such as an admin prompt or a GitHub sign-in)
P1. Location.
    - You should be running in C:\work\git_test, a clone of branch claude/blender-buildings-film-nfzv6a (possibly a shallow --depth 1 clone; that is fine).
    - If the clone is elsewhere, continue there, but warn me if the path is long (more than about 40 characters).
P2. Git.
    - git status is clean.
    - git pull works.
    - I can push: run `git push --dry-run origin claude/blender-buildings-film-nfzv6a`. If it fails, tell me how to authenticate (Git Credential Manager / GitHub sign-in).
    - Set `git config core.longpaths true` for this repo.
P3. Windows long paths.
    - Check HKLM\SYSTEM\CurrentControlSet\Control\FileSystem LongPathsEnabled.
    - If it is not 1, give me this one line to run in an Administrator PowerShell, and wait for me to confirm:
      New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
P4. GPU.
    - Run nvidia-smi and report the driver version and the RTX 3060.
    - If nvidia-smi is missing, or the driver looks very old (older than about a year), tell me to update it before relying on GPU renders. CPU renders still work meanwhile.
P5. Disk.
    - At least 5 GB must be free on the repo's drive. Warn me if not.
P6. Sleep.
    - The run takes several hours. Run `powercfg /change standby-timeout-ac 0` so the PC does not sleep on mains power.
    - Tell me you did it, and how to restore it later: `powercfg /change standby-timeout-ac <minutes>`.

SETUP TASKS (do these yourself, and report anything that needs me)
1. git pull, and confirm the branch is up to date.
2. Python.
   - I installed Python 3.13 from the Microsoft Store. It has no "py" launcher, so use python3.13.
   - Create the venv at the repo root: python3.13 -m venv .bpyenv
   - Install: .bpyenv\Scripts\python -m pip install bpy==5.1.2
   - If that fails (Store sandboxing, or Windows long-path errors), either enable long paths or use uv instead: winget install astral-sh.uv; uv venv .bpyenv --python 3.13; uv pip install --python .bpyenv\Scripts\python.exe bpy==5.1.2
   - Stay on bpy 5.1.2. Do NOT use my installed Blender 5.2 for the pipeline. It is fine for me to view files with.
3. Run .bpyenv\Scripts\python blender_village\tools\check_env.py.
   - It must print ALL CHECKS PASSED.
   - It rebuilds the roundhut and checks the result is identical.
   - Note the render_flags (expect "--device GPU --gpu-backend OPTIX" on my RTX 3060 12 GB), python and root it prints.
   - Then do a quick GPU test render with tools/render_review.py --views hero --samples 8 plus those flags, and confirm it rendered on the GPU.
4. Windows details.
   - Use the absolute Windows paths from check_env everywhere.
   - Build scripts and tools already use os.path and are portable.
   - If any script fails only because of a path or a shell difference, fix it minimally, re-verify the triangle counts against the latest stats.json, and commit.

RESUME THE PRODUCTION (phase 2)
5. Run the workflow script blender_village/workflows/kit_phase_resume.js with these args.
   - Fill in root/py/render_flags from check_env.
   - The rest is filled in from the handoff state:
     {
       "root": "<root from check_env.py>",
       "py": "<python from check_env.py>",
       "render_flags": "<render_flags from check_env.py, e.g. --device GPU --gpu-backend OPTIX>",
       "hero_results": [],
       "heroes_to_audit": [
         {
           "id": "hilltop_keep",
           "round": 7,
           "score": 8.3
         }
       ],
       "heroes_to_gate": [
         {
           "id": "tower_windmill",
           "round": 7
         }
       ],
       "heroes_to_fix": [
         {
           "id": "wattle_roundhut",
           "round": 9,
           "feedback": "The sign-off audit REJECTED kit round 8 (director 8.4). Read director/audit_wattle_roundhut_r8.md and the '## Round 8 — score 8.4/10' must-fix list in director/log_wattle_roundhut.md. Fix it in the KIT, so every building benefits: (1) Wire producer note 11's entrance exception into the daub component per vertex, using core.DetailRule.scale_v / min_at_v (added in kit 1.2.0). Within 3 m of the door and below 2.5 m, the coat must keep relief of 1 cm or more; restore the round-7 hand-dab relief there. (2) Apply the cone sag/wave per shingle (rigid per piece), not per vertex, so joints stop shearing open. Open-joint pixels must return to round-7 levels. (3) Fix decal-anchor placement in the kit helper: snap each anchor to the surface along -normal, drop any anchor with no surface within 5 cm, enforce outward normals, and remove duplicates (the keep also had 8 of 104 bad anchors). A previous round-9 fixer was interrupted. Its partial kit edits are saved in director/partial_fix_wattle_roundhut_r9.patch and were reverted from the kit; reuse whatever is sound. Follow the kit edit rules: re-run the keep and windmill builds and confirm their triangle counts."
         }
       ]
     }
6. The workflow does three things:
   - finishes the hero kit gates (grade, audit, fix rounds) so no hero falls below its signed-off quality;
   - builds and grades 4 kit variant buildings;
   - has the Art Director and a technical director each decide independently whether the kit is viable (kit_works / partial / not_viable).
   Monitor it. If it stalls, or an agent breaks a building, diagnose and resume. Use the workflow's resumeFromRunId only if call order is unchanged. Otherwise write a continuation from the saved state, as HANDOFF.md explains.
7. Concurrency. This machine is a Ryzen 5 5600X (6 cores / 12 threads) with an RTX 3060, so more agents can run at once than in the cloud. The GPU is shared, so if renders queue badly, reduce the parallel work.

AFTER THE KIT DECISION
8. Record the decision in production_plan.md, then follow its decision rule.
   - kit_works: start phase 3. Write a variant generator that can populate 40-50 buildings. Export the kit pieces and buildings for Unreal 5.8:
     - FBX or USD, centimetre scale, Nanite-ready;
     - instance layouts for Packed Level Actors / ISMs;
     - Mask as vertex colour;
     - decal_anchors.json for PCG.
     Also write Unreal import notes.
   - partial or not_viable: build the 3 approved new custom buildings with the same Art Director loop and all producer notes, reusing whatever kit parts work:
     1. the stone longhouse ending in a round building (ref1);
     2. the tiered great hall (ref2);
     3. the timber harbour house (ref2 / ref3).
   Ask me before starting phase 3 or the new buildings if anything in the decision is ambiguous.

WORKING CONVENTIONS (same as the original session)
- Commit and push progress to claude/blender-buildings-film-nfzv6a regularly. Commit messages are clear and descriptive.
- Never modify buildings/<id>/signoff_phase1/. Those are the fallback deliverables.
- Grades:
  - When a building is graded, send me the key screenshots (hero, plus the director's most telling close-ups), the score, and the main notes.
  - Tell me straight away when anything is signed off.
  - Give me your own honest read alongside the director's, including where you disagree.
- Keep me posted with short status updates. Ask me only for decisions that are genuinely mine.
```

## Handoff state

These values replace `__RESUME_ARGS__` above.

The arguments are already embedded in the prompt above. The state they encode is in HANDOFF.md section 4.
