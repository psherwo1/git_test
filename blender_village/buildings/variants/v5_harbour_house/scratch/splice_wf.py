"""one-off: replace waterfront.crib_quay by stone_quay (round 2)."""
import io

F = r"C:\GitHubDesktop\git_test\blender_village\kit\village_kit\components\waterfront.py"
s = io.open(F, encoding="utf-8").read()
a = s.index("def crib_quay(")
b = s.index("def ladder(")
NEW = '''QUAY_BLOCKS = dict(ch=(0.22, 0.42), ch_mix=[(0.30, 0.22, 0.28), (0.40, 0.28, 0.35), (0.30, 0.35, 0.42)],
                  len=(0.55, 1.15), foot_len=(0.80, 1.40), p_tall=0.04, p_double=0.0, p_long=0.10)
"""round 2: the quay's LARGE blocks (ref4) -- rubble_walls.path_stone_wall's coursing table with courses of 22-42 cm
and stones 0.55-1.15 m (the bible's through-stone end of the range): fewer, bigger stones (note 15)."""


def stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, cfg=None, seed=651, coping=True):
    """KIT COMPONENT (round 2; replaces the retired timber crib quay): a harbour quay edge of large rubble blocks
    (rubble_walls.path_stone_wall with QUAY_BLOCKS) along a plan polyline (interior = the land on the LEFT, so each
    face looks out over the water on the right).  water: the runs that are WATER faces -- a list of run indices of
    the path, or None (all): those run from the bed (bed_z) to the quay top; every other run is a LAND face, buried
    by the quay ground at the datum, and is not built (producer note 6: nothing deeper than 5 cm; the land side is
    terrain).  Each water run is laid as its own open stone wall, so its foot is the bed and its corners get quoins.
    coping: the top course is the wall's own top course at top_z (no separate coping object).
    Publishes g.QUAYS (dict(name, water=[PathMap ...], top_z, bed_z)) -- the waterline anchors
    (composite.waterfront_anchors) go only on these water faces, between -0.9 m and the datum."""
    from .rubble_walls import path_stone_wall
    A = [tuple(map(float, p)) for p in path]
    runs = list(range(len(A) - 1)) if water is None else sorted(int(i) for i in water)
    groups, cur = [], []
    for i in runs:                                    # consecutive water runs form one open wall (shared corners)
        if cur and i != cur[-1] + 1:
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    cfg_ = dict(QUAY_BLOCKS, **(cfg or {}))
    maps = []
    for k, grp in enumerate(groups):
        pts = [A[grp[0]]] + [A[i + 1] for i in grp]
        pm = path_stone_wall(g, f"{name}_{k}", pts, top=top_z, openings=(), seed=seed + 13 * k, cfg=cfg_,
                             base=bed_z, clip_z=bed_z - 0.01)
        maps.append(pm)
    if not hasattr(g, "QUAYS"):
        g.QUAYS = []
    g.QUAYS.append(dict(name=name, water=maps, top_z=top_z, bed_z=bed_z))
    log(f"  {g.prefix}_{name}: stone quay, {len(groups)} water face run(s) from the bed {bed_z:.2f} to {top_z:.2f} m; "
        f"{len(A) - 1 - len(runs)} land run(s) left to the terrain")
    return maps


'''
s = s[:a] + NEW + s[b:]
s = s.replace('__all__ = ["pile", "pile_deck", "crib_quay", "ladder"]',
              '__all__ = ["pile", "pile_deck", "stone_quay", "QUAY_BLOCKS", "ladder"]')
s = s.replace('''    crib_quay(g, name, rect, top_z=0.0, bed_z=-2.5, ...)   KIT COMPONENT: a timber crib / bulkhead quay block: posts at
        the faces, horizontal sheathing planks, a capping beam with crossed corners, a stone-fill top (M_earth) round
        whatever stands on it (hole = the inner rectangle left open) and a closed backing behind the sheathing.
        -> <P>_<name>_posts, _sheathing, _cap, _fill, _blocker''',
              '''    stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, ...)   KIT COMPONENT (round 2; the timber crib quay
        is retired): a quay edge of large rubble blocks (rubble_walls.path_stone_wall, QUAY_BLOCKS) whose WATER runs
        stand on the bed; land runs are terrain and are not built.  -> <P>_<name>_<k>_stones, _quoins, _mortar''')
io.open(F, "w", encoding="utf-8", newline="\n").write(s)
print("ok", "crib_quay" in s)
