# Blender village: hero buildings

These are the geometry-only hero buildings for an Unreal Engine 5.8 (Nanite) virtual production. They were modelled to match the concept art in `reference/`. An Art Director agent graded each build round against that art, and an independent audit had to uphold a building's grade before it was signed off.

## Signed-off buildings

| Building | File | Final round | Director score | Triangles | Hidden tris | Material slots |
|---|---|---|---|---|---|---|
| Tower windmill | `buildings/tower_windmill/tower_windmill.blend` | 6 | 9.1 | 1.21 M | 14.4 % | 10 |
| Hilltop keep | `buildings/hilltop_keep/hilltop_keep.blend` | 6 | 8.4 | 1.30 M | 13.9 % | 11 |
| Wattle roundhut | `buildings/wattle_roundhut/wattle_roundhut.blend` | 7 | 8.5 | 1.31 M | 13.7 % | 10 |

The ensemble review graded the three side by side and approved them at 8.4 as one coherent style. See `director/ensemble_log.md`.

## Conventions

These apply to every building. The full rules are the producer notes at the end of `director/art_bible.md`.

- **Units and placement:** real-world metres, Z up, base centred at the origin, ground at Z = 0.
- **Scale:** doors and steps are sized for real actors.
- **Materials:** each building uses only the shared material palette of 15 slots or fewer. Placeholder materials only; texturing comes later.
- **`Mask` colour attribute:** set as the active and render colour attribute on every mesh, so it exports as vertex colour.
  - **R:** a random value per piece.
  - **G:** wear.
  - **B:** moss, dirt and damp.
  - **A:** 1.
- **Hidden triangles:** 15 % or fewer. Culled areas have backing surfaces, so no culled area shows a hole.
- **Shared meshes:** repeated parts are shared-mesh linked duplicates, which become instanced static meshes in Unreal.
- **Ground dressing:** there is no loose rubble, path stones or ground apron. Terrain will be built in Unreal.

## Rebuilding and reviewing

The Python build scripts are the source of truth. They are deterministic and run on Blender 5.1 as a Python module (`pip install bpy==5.1.2`):

```
python buildings/<id>/build_<id>.py
python tools/render_review.py buildings/<id>/<id>.blend renders/<id>/check   # clay review renders + stats.json
python tools/hidden_tris.py  buildings/<id>/<id>.blend                         # hidden/buried triangle estimate
```

## Folders

| Folder | Contents |
|---|---|
| `director/` | art bible, per-building specs, grade logs, client corrections, the production plan and sign-off record |
| `renders/<id>/round_NN/` | review renders for every round, plus the director's close-ups in `director_extra/` |
| `renders/_ensemble/` | lineup renders |
| `scene/` | lineup assembly script and scene |
