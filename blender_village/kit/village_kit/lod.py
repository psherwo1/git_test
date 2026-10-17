"""village_kit.lod -- height-banded grid LOD for template-instanced pieces (kit 1.7 r4, variant v4_mixed;
producer note 15: new structures at most 1,000,000 triangles).

Note 15 asks, in priority order, for (1) hidden geometry dropped, (2) "coarsen stone and shingle tessellation on faces
seen only from mid-distance (above about 4 m, roof tops)", (3) pooled pieces.  Most stone and dressed work of the drum
family is laid as template-instanced pieces (tmplmesh.tmpl_box grids: T_RUB3_XHI 17 x 11 face lines, T_RUB3_HI 13 x 9,
T_DRS3X 17 x 15 ...) whose density was chosen for the hero close-ups.  This module gives any frame a per-part LOD:

    from village_kit.lod import tmpl_lod
    steps=[(tmpl_lod, dict(z=1.2, step=2, parts=("base_stones", "base_dressed", "arcade_dressed")), ...]

Every piece of a listed part whose LOWEST vertex is above `z` (wing-local metres) is re-meshed on every `step`-th grid
line of its template, keeping both arris lines of every axis and the outward (y) lines whole.  The kept vertices are
the piece's own, already shaped vertices (outline cuts, facets, pillow, spalls), so the coarse piece is a sub-sampled
copy of the fine one: same outline corners, same arrises, same size and placement -- only the face grid between them
is thinner.  Pieces within `keep_r` (plan) of a keep point (default: the frame's entrance, note 4) and pieces below
`z` keep the full grid.

How it hooks in: tmplmesh.BatchAcc.add calls tmplmesh.LOD_HOOK (None by default -> every existing building is
unchanged) with the part name; tmpl_lod registers a rule for the frame's prefix and sets the hook.  Only tmpl_box
grids are thinned (lathes, sweeps, kit-mesh templates, templates with triangles or no_auto are left alone), and only
the parts listed (a part whose BatchAcc vertices are read back as a fixed template layout must not be listed).
"""
import numpy as np

from . import tmplmesh

RULES = {}                 # object-name prefix ("V4M_") -> rule dict
_CACHE = {}


def _lines(n, step):
    if n < 5 or step <= 1:
        return list(range(n))
    return sorted(set([0, 1, n - 2, n - 1] + list(range(1, n - 1, step))))


def coarse_template(T, step=2, axes=(0, 2)):
    """the sub-sampled template of a tmpl_box grid T: (Tc, vmap) with vmap[i] = the fine vertex of coarse vertex i.
    Lines kept per thinned axis: both outer lines, both arris lines and every `step`-th line between them."""
    key = (id(T), step, tuple(axes))
    hit = _CACHE.get(key)
    if hit is not None and hit[0] is T:
        return hit[1], hit[2]
    idx = np.asarray(T["idx"])
    n = [int(v) for v in T["n"]]
    K = [(_lines(n[a], step) if a in axes else list(range(n[a]))) for a in range(3)]
    fine_id = {tuple(map(int, c)): i for i, c in enumerate(idx)}
    # faces present in the fine template (axis, side) and the sign of their winding in index space
    faces = {}
    for q in np.asarray(T["quads"]):
        c = idx[q]
        for ax in range(3):
            for side in (0, n[ax] - 1):
                if (c[:, ax] == side).all():
                    nn = np.cross(c[1] - c[0], c[3] - c[0]).astype(float)
                    faces.setdefault((ax, side), float(np.sign(nn[ax])))
    quads, flat = [], []
    for (ax, side), sgn in sorted(faces.items()):
        a1, a2 = [a for a in range(3) if a != ax]
        for p in range(len(K[a1]) - 1):
            for q in range(len(K[a2]) - 1):
                cs = []
                for dp, dq in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    c = [0, 0, 0]
                    c[ax] = side
                    c[a1] = K[a1][p + dp]
                    c[a2] = K[a2][q + dq]
                    cs.append(tuple(c))
                P_ = np.array(cs, float)
                nn = np.cross(P_[1] - P_[0], P_[3] - P_[0])
                if np.sign(nn[ax]) != sgn:
                    cs = cs[::-1]
                quads.append(cs)
                flat.append(K[a1][p] >= 1 and K[a1][p + 1] <= n[a1] - 2 and
                            K[a2][q] >= 1 and K[a2][q + 1] <= n[a2] - 2)
    used = sorted({c for qd in quads for c in qd})
    cid = {c: i for i, c in enumerate(used)}
    vmap = np.array([fine_id[c] for c in used], np.int64)
    Tc = dict(idx=idx[vmap], n=np.array(n), quads=np.array([[cid[c] for c in qd] for qd in quads], np.int64),
              tris=np.zeros((0, 3), np.int64), qflat=np.array(flat, bool), tflat=np.zeros(0, bool),
              nv=len(used), yfront=T.get("yfront", False), lod_of=T, lod_step=step)
    _CACHE[key] = (T, Tc, vmap)
    return Tc, vmap


def _hook(name, Vw, T, Pl, wear):
    """tmplmesh.LOD_HOOK: None (no change) or [(Vw, T, Pl, wear)] sub-batches for BatchAcc.add."""
    rule = None
    anyz = False
    for pre, r in RULES.items():
        if not name.startswith(pre):
            continue
        part = name[len(pre):]
        if part in r["parts"]:
            rule = r
            break
        # "pool_corbel*": a pooled variant modelled in LOCAL coordinates (village_kit.pools) -- thinned whatever its
        # local z, so list only pools whose every placement is above the rule's z (e.g. cornice corbels)
        if any(p.endswith("*") and part.startswith(p[:-1]) for p in r["parts"]):
            rule, anyz = r, True
            break
    if rule is None or "idx" not in T or "n" not in T or T.get("no_auto") or T.get("lod_of") is not None:
        return None
    if len(T.get("tris", ())) or len(T["quads"]) == 0:
        return None
    Vw = np.asarray(Vw, float)
    if Vw.ndim == 2:
        Vw = Vw[None]
    N = len(Vw)
    if N == 0:
        return None
    if anyz:
        sel = np.ones(N, bool)
        steps = np.full(N, rule["step"])
        keep = None
    else:
        sel = Vw[:, :, 2].min(1) > rule["z"]
        keep = rule["keep"] if rule["keep"] is not None else _entrance_keep(rule)
    if keep:
        cxy = Vw[:, :, :2].mean(1)
        zlo = Vw[:, :, 2].min(1)
        for k in keep:
            kx, ky, kr = k[:3]
            kz = k[3] if len(k) > 3 else 1e9
            sel &= (np.hypot(cxy[:, 0] - kx, cxy[:, 1] - ky) > kr) | (zlo > kz)
    if not sel.any():
        return None
    # the step per piece: `step` above z, and every (z_b, step_b) of `bands` above z_b (the highest band wins)
    zmin = Vw[:, :, 2].min(1)
    if not anyz:
        steps = np.where(sel, rule["step"], 1)
        for zb, sb in rule.get("bands", ()):
            steps = np.where(sel & (zmin > zb), sb, steps)
    Pl_ = Vw if Pl is None else (Pl[None] if np.asarray(Pl).ndim == 2 else np.asarray(Pl))
    w_ = None if wear is None else np.broadcast_to(np.asarray(wear, float), (N,))
    out = []
    lo = steps == 1
    if lo.any():
        out.append((Vw[lo], T, Pl_[lo], None if w_ is None else w_[lo]))
    for st in sorted(set(int(s) for s in steps[~lo])):
        m = steps == st
        Tc, vmap = coarse_template(T, st)
        if Tc["nv"] >= T["nv"]:
            out.append((Vw[m], T, Pl_[m], None if w_ is None else w_[m]))
            continue
        out.append((Vw[m][:, vmap], Tc, Pl_[m][:, vmap], None if w_ is None else w_[m]))
        k = int(m.sum())
        rule["n_pieces"] += k
        rule["saved_quads"] += k * (len(T["quads"]) - len(Tc["quads"]))
        bp = rule.setdefault("by_part", {}).setdefault(name, [0, 0, 0])
        bp[0] += k
        bp[1] += k * len(T["quads"])
        bp[2] += k * len(Tc["quads"])
    if len(out) == 1 and out[0][1] is T:
        return None
    return out


def _entrance_keep(rule):
    """the frame's entrance, read when the pieces are laid (a DrumFrame's drum radius is set by its drum step):
    a drum door at (0, -R_BASE0), a round wall's at (0, -R_WALL)."""
    g = rule.get("g")
    if g is None:
        return []
    for a in ("R_BASE0", "R_WALL"):
        if hasattr(g, a):
            return [(0.0, -float(getattr(g, a)), rule["keep_r"], rule["keep_z"])]
    return []


def register(prefix, parts, z=1.2, step=2, keep=(), g=None, keep_r=1.3, keep_z=2.6, bands=()):
    """register a LOD rule for the BatchAcc parts <prefix>_<part> (see the module doc) and switch the hook on.
    keep: [(x, y, r[, z_top])] -- pieces whose plan centre is within r of (x, y) and whose lowest point is below
    z_top stay at full density.  keep=None with a frame g: the frame's entrance zone (radius keep_r, up to keep_z).
    bands: [(z_b, step_b)] -- coarser steps for pieces whose lowest point is above z_b (e.g. [(3.0, 3)])."""
    RULES[prefix] = dict(parts=tuple(parts), z=float(z), step=int(step),
                         bands=sorted((float(a), int(b)) for a, b in bands),
                         keep=None if keep is None else [tuple(map(float, k)) for k in keep], g=g,
                         keep_r=float(keep_r), keep_z=float(keep_z), n_pieces=0, saved_quads=0)
    tmplmesh.LOD_HOOK = _hook
    return RULES[prefix]


def unregister(prefix):
    RULES.pop(prefix, None)
    if not RULES:
        tmplmesh.LOD_HOOK = None


DRUM_LOD_PARTS = ("base_stones", "base_dressed", "arcade_dressed", "arcade_backs", "tower_boards", "tower_frame",
                  "apron_rafters", "cap_frame", "wheel_blades")
"""the drum family's template-instanced parts whose vertex layout nothing reads back (not the door / window parts,
not cap_shingles, which mill_cap filters by template layout)."""


def tmpl_lod(g, z=1.2, step=2, parts=DRUM_LOD_PARTS, keep=None, keep_r=1.3, keep_z=2.6, bands=()):
    """STEP (any frame whose parts are tmplmesh.BatchAcc): height-banded grid LOD for the listed parts (module doc).
    Run it FIRST among the wing's steps.  keep: [(x, y, r[, z_top])] zones kept at full density; default the
    frame's entrance zone ((0, -R_BASE0) of a DrumFrame, (0, -R_WALL) of a RoundFrame, read when the pieces are
    laid; plan radius keep_r, up to keep_z: producer note 4).  bands: [(z_b, step_b)] coarser steps higher up
    (note 15: mid-distance faces above about 4 m)."""
    from .core import log
    r = register(g.prefix + "_", parts, z=z, step=step, keep=keep, g=g, keep_r=keep_r, keep_z=keep_z, bands=bands)
    g.TMPL_LOD = r
    log(f"  tmpl_lod {g.prefix}: parts {', '.join(parts)} above z {z:.2f} m on every {step}th grid line"
        f"{''.join(f', above {zb:.1f} m every {sb}th' for zb, sb in r['bands'])} "
        f"(full density in {'the entrance zone' if keep is None else keep}: r {keep_r:.1f} m, z < {keep_z:.1f} m)")
    return r


def tmpl_lod_report(g):
    """STEP: log how many pieces the wing's LOD rule thinned (run after the geometry, e.g. before the finish)."""
    from .core import log
    r = RULES.get(g.prefix + "_")
    if r:
        log(f"  tmpl_lod {g.prefix}: {r['n_pieces']} pieces thinned, -{2 * r['saved_quads']} triangles")
        for nm, (n, q0, q1) in sorted(r.get("by_part", {}).items()):
            log(f"    {nm}: {n} pieces, {2 * q0} -> {2 * q1} triangles")
