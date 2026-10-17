# Resume prompt (desktop session 2)

The machine is already set up (see HANDOFF.md section 6). Open Claude Code in `C:\GitHubDesktop\git_test` and paste:

```
You are taking over an in-progress production from a previous Claude Code session on this same desktop. Work in C:\GitHubDesktop\git_test on branch claude/blender-buildings-film-nfzv6a. Use workflows / multi-agent orchestration as before. I am explicitly asking for it, as in the earlier sessions.

READ FIRST: blender_village/HANDOFF.md (the full state, all my decisions, machine notes), then the files it lists in section 2. Treat them as the source of truth and do not re-litigate recorded decisions.

FIRST, check the two jobs that were running when the last session ended (HANDOFF section 4, "Running when this session ended"):
1. The longhouse redesign (v3) was stopped at the handoff, early in round 8. Relaunch it as HANDOFF section 4 describes (kit_close_variants.js, only v3, from fix round 8), then report each grade and the acceptance to me.
2. (Done.) The textured junction test is in lookdev/junction_test/REPORT.md, and I accepted the tiered hall (v2) as it stands. No more work on it.

THEN continue my approved plan (HANDOFF section 3): merge the kit/changes notes into the CHANGELOG, then step 3: the timber / rectangular / waterfront kit family through the timber harbour house (approved building 3), then a boathouse or barn; then add-ons; then the Unreal exporter and UE 5.8 lookdev.

WORKING CONVENTIONS:
- Commit and push progress regularly with clear messages.
- Send me key screenshots, the scores, the main notes and your own honest read whenever a building is graded.
- Tell me straight away when anything is accepted or signed off.
- Keep me posted with short status updates, and ask me only for decisions that are genuinely mine.
```
