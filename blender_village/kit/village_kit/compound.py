"""village_kit.compound -- one building assembled from SEVERAL kit frames (module families) placed side by side
(kit 1.7.0 candidate, variant v4_mixed).

assembly.build_building runs ONE frame (a RoundFrame hut, an OctFrame keep, a DrumFrame tower).  A mixed building
combines bodies from different families -- a daub roundhouse against a stone mill drum, a drum tower beside an
octagonal hall -- so build_compound runs several frames in one scene, each as a WING:

    from village_kit.compound import Wing, build_compound, configure
    house = Wing("house", RoundFrame, "V4H", params=dict(radius=2.85, ...), at=(-1.7, 0.15),
                 steps=[drystone_plinth, round_daub_wall, ...], decals=round_building_decals,
                 cull_targets=frame.HIDDEN_CULL_TARGETS, solid=(3.1, 2.4))
    mill = Wing("mill", DrumFrame, "V4M", params=dict(detail_rule=True), at=(2.82, 1.36),
                steps=[(round_stone_drum, dict(...)), ...], decals=drum_tower_decals_gated, ...)
    build_compound(dict(collection="V4", building_id="v4_mixed", wings=[house, mill],
                        junctions=[(roof_tower_flashing, dict(roof="house", tower="mill")), ...],
                        out=".../v4_mixed.blend", decal_json=".../decal_anchors.json"))

What build_compound does, in order:
  1. resets the scene and makes the top collection (`collection`);
  2. for each wing: instantiates its frame at the ORIGIN (every family component builds about its own origin, so
     no component changes), runs its steps, its decal recipe and (optional) its anchor gate exactly as
     build_building would, then parks the wing out of the way (components only read their own g.coll);
  3. places every wing (translation `at`, rotation `yaw_deg` about Z): single-user meshes get the transform
     applied (identity object matrices, art bible 8), pooled linked duplicates keep a placed matrix; the wing's
     decal anchors are transformed with it;
  4. runs the JUNCTION steps fn(c, **kw) with the compound context c (c.wing(name) -> the placed Wing with .g / .M,
     c.acc(part) -> a geom.Acc named <junction prefix>_<part>, c.coll, c.decals);
  5. runs ONE hidden-geometry cull (producer note 6) over every wing's cull targets with every wing's actor / door /
     crane rings (moved to where the wing stands; viewpoints inside another wing's solid body are dropped) plus the
     review cameras of the whole building -- so a junction can only hide more, never open a hole;
  6. merges all decal anchors, re-audits them against the WHOLE building (an anchor now covered by the neighbouring
     wing or a flashing is dropped: anchor_audit.audit_anchors), thins them to `decal_max` (per type, evenly,
     deterministic), builds DECAL_ANCHORS and writes decal_anchors.json;
  7. logs the triangle count and saves compressed.

Nothing in an existing family module is changed: a wing's steps are the same function calls a hero recipe makes.
"""
import math
import os

import numpy as np

from . import core
from .decals import DecalAnchors

PARK = 1000.0          # wings are parked PARK * (i + 1) m along +X while the next wing builds


class Wing:
    """one body of a compound building: a kit frame + its steps, placed at `at` (x, y) rotated `yaw_deg` about Z.

    frame, prefix, params   the family frame class, the object-name prefix (unique per wing) and its parameters
    steps                   [fn or (fn, kw)] exactly as in a build_building spec (build order)
    decals / decal_validate the wing's decal recipe fn(g) and its assembly-style anchor gate (dict / True; kit 1.9.0:
                            None = the guard default True, report-only needs opt_out)
    opt_out                 kit 1.9.0 {guard: reason} for this wing (village_kit.guards.GUARDS)
    entrances               kit 1.9.0 explicit entrances for the wing's clearance gate (default: guards.entrances_of)
    cull_targets            object parts (without prefix) the compound cull may thin (backed pieces only)
    reach                   plan radius of the wing's body for its actor rings (default: from its bounds)
    door                    (x, y) of its door in wing-local coords (door views); None = none
    view_heights            ring heights for the near rings (m)
    solid                   (radius, z_top) of the wing's solid body: other wings' viewpoints inside it are dropped
    ring_n                  stations per near ring (fewer = a faster cull; the review rings are always added)
    eye_heights             kit 1.7 r4 (director v4 r3 must-fix): the actor eye-level heights of the near rings
                            (r + 0.4 m and r + 1.5 m) that compound_views keeps COMPLETE (every ring_n station,
                            never thinned), like the door views -- the close, low viewpoints that alone see a wall
                            band under a deep / low eave.  () = the r3 behaviour (all near rings thinned).
    """

    def __init__(self, name, frame, prefix, params=None, steps=(), at=(0.0, 0.0), yaw_deg=0.0, decals=None,
                 decal_validate=None, cull_targets=(), reach=None, door=None, view_heights=(0.3, 1.0, 1.65, 2.3),
                 crane_heights=(5.0, 9.0), solid=None, ring_n=24, eye_heights=(1.0, 1.65), opt_out=None,
                 entrances=None):
        self.name = name
        self.opt_out = dict(opt_out or {})        # kit 1.9.0: {guard: reason} (village_kit.guards)
        self.entrances = entrances                # kit 1.9.0: explicit clearance-gate entrances (wing-local)
        self.frame = frame
        self.prefix = prefix
        self.params = dict(params or {})
        self.steps = list(steps)
        self.at = (float(at[0]), float(at[1]))
        self.yaw = math.radians(yaw_deg)
        self.decals = decals
        self.decal_validate = decal_validate
        self.cull_targets = tuple(cull_targets)
        self.reach = reach
        self.door = door
        self.view_heights = tuple(view_heights)
        self.crane_heights = tuple(crane_heights)
        self.solid = solid
        self.ring_n = int(ring_n)
        self.eye_heights = tuple(eye_heights or ())
        self.g = None
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        self.M = np.array([[c, -s, 0, self.at[0]], [s, c, 0, self.at[1]], [0, 0, 1, 0], [0, 0, 0, 1.0]])

    # wing-local -> world
    def to_world(self, P):
        P = np.asarray(P, float)
        return P @ self.M[:3, :3].T + self.M[:3, 3]

    def dir_world(self, D):
        return np.asarray(D, float) @ self.M[:3, :3].T

    def to_local(self, P):
        P = np.asarray(P, float)
        return (P - self.M[:3, 3]) @ self.M[:3, :3]

    @property
    def center(self):
        return self.M[:3, 3].copy()

    def objects(self):
        return list(self.g.coll.all_objects) if self.g is not None else []

    def meshes(self):
        return [o for o in self.objects() if o.type == "MESH"]


class Compound:
    """the context junction steps receive (`c`)."""

    def __init__(self, coll, prefix, wings):
        self.coll = coll
        self.prefix = prefix
        self.wings = {w.name: w for w in wings}
        self.decals = DecalAnchors(prefix)
        self.objects = {}

    def wing(self, name):
        return self.wings[name]

    def acc(self, part, sharp=38.0):
        """a geom.Acc named <PREFIX>_<part> (world coordinates; finalize with geom.finalize(acc, c.coll))."""
        from .geom import Acc
        return Acc(f"{self.prefix}_{part}", sharp)

    def finalize(self, acc, smooth_deg=38.0):
        from .geom import finalize
        ob = finalize(acc, self.coll, smooth_deg=smooth_deg)
        if ob is not None:
            self.objects[ob.name] = ob
        return ob


# =================================================================================================================
# frame-option steps (generic helpers a recipe can list among a wing's steps)
# =================================================================================================================
def configure(g, strict=False, **attrs):
    """STEP: set frame attributes / opt-in switches on g (e.g. a DrumFrame's ENTRANCE_R8=True, a flag that is
    absent = False by default).  strict=True: only attributes the frame already has (typos raise)."""
    for k, v in attrs.items():
        if strict and not hasattr(g, k):
            raise KeyError(f"frame {type(g).__name__} has no attribute {k!r}")
        setattr(g, k, v)


def patches_by_azimuth(g, patches):
    """STEP (RoundFrame): the exposed-wattle patches given by azimuth -- [(az_deg, kind, cz, half_w, half_h, seed)],
    the same format as components.frame.DEFAULT_PATCHES_AZ -- so a round wall can keep its patches away from the
    side a neighbouring wing covers.  Run before round_daub_wall."""
    g.DAUB_PATCHES = [g.patch_at(*p) for p in patches]


# =================================================================================================================
# placement
# =================================================================================================================
def _move_objects(objs, M):
    from mathutils import Matrix
    Mm = Matrix(np.asarray(M).tolist())
    for ob in objs:
        if ob.parent is None:
            ob.matrix_world = Mm @ ob.matrix_world


def _apply_unique(objs):
    """bake the object matrix into single-user meshes (identity matrices, art bible 8); shared meshes keep theirs."""
    from mathutils import Matrix
    I = Matrix.Identity(4)
    for ob in objs:
        if ob.type != "MESH" or ob.parent is not None:
            continue
        if ob.data.users > 1:
            continue
        if ob.matrix_world == I:
            continue
        ob.data.transform(ob.matrix_world)
        ob.data.update()
        ob.matrix_world = I


def _transform_anchors(items, M):
    R, t = M[:3, :3], M[:3, 3]
    for it in items:
        it["pos"] = R @ np.asarray(it["pos"], float) + t
        for k in ("normal", "up", "right", "macro"):
            if k in it and it[k] is not None:
                v = np.asarray(it[k], float)
                if v.shape == (3,):
                    it[k] = R @ v


def _translate(x, y=0.0, z=0.0):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


# =================================================================================================================
# hidden-geometry cull over the whole compound (producer note 6)
# =================================================================================================================
def dedupe_views(V, sep, seed_views=None):
    """greedy thinning (kit 1.7 r2): keep a viewpoint only if no viewpoint kept before it (or in seed_views, kept
    anyway and not returned) lies within `sep` m.  Earlier rows have priority: list the viewpoints that matter most
    first (review cameras, door views, the near actor rings).  Deterministic."""
    V = np.asarray(V, float)
    cell = {}

    def key(p):
        return tuple(np.floor(p / sep).astype(int))

    def near(p):
        k = key(p)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for q in cell.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        if float(np.sum((q - p) ** 2)) < sep * sep:
                            return True
        return False
    if seed_views is not None:
        for p in np.asarray(seed_views, float):
            cell.setdefault(key(p), []).append(p)
    out = []
    for p in V:
        if not near(p):
            cell.setdefault(key(p), []).append(p)
            out.append(p)
    return np.array(out).reshape(-1, 3)


def compound_views(c, wings, max_views=None):
    """actor rings round every wing (moved to where it stands), crane rings, door views, the review cameras of the
    whole building; viewpoints inside another wing's solid body are dropped.
    kit 1.7 r2 (director v4 r1 must-fix 3, build time): max_views -> the overlapping rings of the wings are thinned
    (dedupe_views, priority review cameras > door views > near rings > far / crane rings) so that, together with
    the review viewpoints visibility_cull always adds, at most max_views viewpoints remain.  The cull's cost is
    (hidden polygons) x (viewpoints), so this is the build-time lever.
    kit 1.7 r4 (director v4 r3 must-fix, producer note 6): each wing's near EYE-LEVEL rings (every ring_n station at
    r + 0.4 m and r + 1.5 m, z = Wing.eye_heights, default 1.0 / 1.65 m) go into the never-thinned head group with
    the review cameras and the door views; only the remaining near heights and the far / crane rings are thinned.
    Thinning the eye rings opened holes in a wall band seen only from close and low (under a low eave lip)."""
    from .core import review_cameras, review_views, ring_views
    if max_views:
        groups = {"door": [], "eye": [], "near": [], "far": []}
        for w in wings:
            r = w.reach
            if r is None:
                co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T
                                     + np.array(o.matrix_world)[:3, 3] for o in w.meshes()])
                r = 0.5 * float(max(np.ptp(co[:, 0]), np.ptp(co[:, 1])))
            cxy = w.center[:2]
            eye = [z for z in w.eye_heights]
            rest_h = [z for z in w.view_heights if all(abs(z - e) > 1e-6 for e in eye)]
            if eye:
                groups["eye"].append(ring_views(cxy, [r + 0.4], eye, n=w.ring_n))
                groups["eye"].append(ring_views(cxy, [r + 1.5], eye, n=w.ring_n, phase=0.87))
            if rest_h:
                groups["near"].append(ring_views(cxy, [r + 0.4], rest_h, n=w.ring_n))
                groups["near"].append(ring_views(cxy, [r + 1.5], rest_h, n=w.ring_n, phase=0.87))
            groups["far"].append(ring_views(cxy, [r + 3.5], list(w.view_heights), n=w.ring_n))
            groups["far"].append(ring_views(cxy, [r + 6.0], list(w.crane_heights), n=16, phase=0.11))
            if w.door is not None:
                dx, dy = w.door
                out = np.array([0.0, -1.0, 0.0]) if dy < 0 else np.array([0.0, 1.0, 0.0])
                loc = [(dx + x, dy + out[1] * d, z) for d in (0.5, 1.0, 2.0) for z in (0.4, 1.1, 1.7, 2.3)
                       for x in (-0.9, 0.0, 0.9)]
                groups["door"].append(w.to_world(np.array(loc)))
        obs = [o for o in c.coll.all_objects if o.type == "MESH"]
        co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T
                             + np.array(o.matrix_world)[:3, 3] for o in obs])
        lo, hi = co.min(0), co.max(0)
        cams = review_cameras(lo, hi)
        order = ("door", "eye", "near", "far")
        V = np.concatenate([cams] + [np.concatenate(groups[k]) for k in order if groups[k]])
        lab = np.concatenate([np.full(len(cams), -1)] + [np.full(sum(len(x) for x in groups[k]), i)
                                                          for i, k in enumerate(order) if groups[k]])
        keep = np.ones(len(V), bool)
        for w in wings:
            if w.solid is None:
                continue
            rs, zt = w.solid
            d = np.hypot(V[:, 0] - w.center[0], V[:, 1] - w.center[1])
            keep &= ~((d < rs) & (V[:, 2] < zt))
        V, lab = V[keep], lab[keep]
        base = review_views(lo, hi)
        in_head = lab <= 1                          # review cameras, door views, eye-level near rings: never thinned
        head, rest = V[in_head], V[~in_head]
        n_eye = int((lab == 1).sum())
        budget = max_views - len(base) - len(head)
        lo_s, hi_s = 0.05, 8.0
        best = rest if budget > 0 else rest[:0]
        for _ in range(30):                                 # smallest separation that fits the budget
            mid = 0.5 * (lo_s + hi_s)
            cand = dedupe_views(rest, mid, seed_views=base)
            if len(cand) > budget:
                lo_s = mid
            else:
                hi_s = mid
                best = cand
        core.log(f"  compound views: {len(V)} ring / door / camera viewpoints -> {len(head) + len(best)} "
                 f"(+{len(base)} review; {len(head)} kept whole incl. {n_eye} eye-level ring stations) at "
                 f"{hi_s:.2f} m separation")
        return np.concatenate([head, best])
    V = []
    for w in wings:
        r = w.reach
        if r is None:
            co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T
                                 + np.array(o.matrix_world)[:3, 3] for o in w.meshes()])
            r = 0.5 * float(max(np.ptp(co[:, 0]), np.ptp(co[:, 1])))
        cxy = w.center[:2]
        V.append(ring_views(cxy, [r + 0.4, r + 1.5, r + 3.5], list(w.view_heights), n=w.ring_n))
        V.append(ring_views(cxy, [r + 6.0], list(w.crane_heights), n=16, phase=0.11))
        if w.door is not None:
            dx, dy = w.door
            out = np.array([0.0, -1.0, 0.0]) if dy < 0 else np.array([0.0, 1.0, 0.0])
            loc = [(dx + x, dy + out[1] * d, z) for d in (0.5, 1.0, 2.0) for z in (0.4, 1.1, 1.7, 2.3)
                   for x in (-0.9, 0.0, 0.9)]
            V.append(w.to_world(np.array(loc)))
    V = np.concatenate(V)
    keep = np.ones(len(V), bool)
    for w in wings:
        if w.solid is None:
            continue
        rs, zt = w.solid
        d = np.hypot(V[:, 0] - w.center[0], V[:, 1] - w.center[1])
        keep &= ~((d < rs) & (V[:, 2] < zt))
    V = V[keep]
    obs = [o for o in c.coll.all_objects if o.type == "MESH"]
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in obs])
    return np.concatenate([V, review_cameras(co.min(0), co.max(0))])


WALL_HEAD_PARTS = ("daub", "wall_plate", "posts", "wattle_rods")


def wall_head_views(w, wings, n=48, eye=1.65, parts=WALL_HEAD_PARTS):
    """kit 1.7 r4 (director v4 r3 must-fix, producer note 6): when a round wing's eave lip lies BELOW its wall head
    (frame Z_EAVE < PLATE_TOP: a steep cone on a short overhang), the wall band from the lip up to the plate top is
    seen only by an actor standing close to the wall.  Returns {object name: viewpoints} for the wing's wall parts:
    three eye-height rings, one under the eave (R_WALL + 0.45 m, `n` stations), one just outside the lip
    (R_EAVE + 0.25 m, `n`) and one at R_EAVE + 2.9 m (about 6 m out, 2n stations: past a neighbouring wing the band
    is seen at a grazing angle, under the lip, through a narrow window), plus a BAND-GUARD ring of 2n stations
    0.2 m in front of the wall at the band's mid height, which keeps every outward face of the band (a sliver of a
    face seen at a grazing angle may miss the cull's sample points; in a narrow re-entrant corner beside another wing
    no actor station fits).  Stations inside another wing's solid body are dropped.  {} for a wing without such a
    band (drums, keeps, a hut whose eave lip is above its wall head)."""
    from .core import ring_views
    g = w.g
    if g is None or not all(hasattr(g, a) for a in ("R_WALL", "R_EAVE", "Z_EAVE", "PLATE_TOP")):
        return {}
    if not float(g.Z_EAVE) < float(g.PLATE_TOP):
        return {}
    cxy = w.center[:2]
    z_band = 0.5 * (float(g.Z_EAVE) + float(g.PLATE_TOP))
    rings = [(ring_views(cxy, [float(g.R_WALL) + 0.45], [eye], n=n, phase=0.25), 0.15),
             (ring_views(cxy, [float(g.R_EAVE) + 0.25], [eye], n=n, phase=0.75), 0.15),
             (ring_views(cxy, [float(g.R_EAVE) + 2.9], [eye], n=2 * n, phase=0.5), 0.15),
             (ring_views(cxy, [float(g.R_WALL) + 0.2], [z_band], n=2 * n, phase=0.0), 0.0)]
    out = []
    for V, margin in rings:
        keep = np.ones(len(V), bool)
        for o in wings:
            if o is w or o.solid is None:
                continue
            rs, zt = o.solid
            d = np.hypot(V[:, 0] - o.center[0], V[:, 1] - o.center[1])
            keep &= ~((d < rs + margin) & (V[:, 2] < zt))
        out.append(V[keep])
    V = np.concatenate(out)
    core.log(f"  wall-head band views ({w.name}): eave lip {g.Z_EAVE:.2f} m < plate top {g.PLATE_TOP:.2f} m -> "
             f"{len(V)} stations ({len(out[-1])} band-guard at z {z_band:.2f}) for {', '.join(parts)}")
    return {f"{w.prefix}_{p}": V for p in parts}


def wall_head_band(w):
    """(z0, z1) of a round wing's wall-head band under a low eave lip (Z_EAVE - 5 cm .. PLATE_TOP + 2 cm), or None."""
    g = w.g
    if g is None or not all(hasattr(g, a) for a in ("R_WALL", "R_EAVE", "Z_EAVE", "PLATE_TOP")):
        return None
    if not float(g.Z_EAVE) < float(g.PLATE_TOP):
        return None
    return float(g.Z_EAVE) - 0.05, float(g.PLATE_TOP) + 0.02


def split_band(ob, z0, z1, center, inward=-0.2, solids=()):
    """move the polygons of `ob` whose centre lies in z0..z1 and that do not face the wing's axis (horizontal normal
    . radial > `inward`) into a new object <name>__band in the same collections; returns it (None if none).
    solids: [(centre xy, radius, z_top)] of other wings -- polygons inside them (buried in a neighbour) stay in the
    cull."""
    import bmesh
    import bpy
    me = ob.data
    Mw = np.array(ob.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    sel = []
    for f in bm.faces:
        cw = Mw[:3, :3] @ np.array(f.calc_center_median()) + Mw[:3, 3]
        if not (z0 <= cw[2] <= z1):
            continue
        if any(float(np.hypot(cw[0] - sc[0], cw[1] - sc[1])) < sr and cw[2] < sz for sc, sr, sz in solids):
            continue
        nw = Mw[:3, :3] @ np.array(f.normal)
        rad = cw[:2] - np.asarray(center[:2], float)
        rl = float(np.hypot(*rad))
        nl = float(np.hypot(nw[0], nw[1]))
        if rl < 1e-6 or nl < 1e-6 or float(nw[:2] @ rad) / (rl * nl) > inward:
            sel.append(f.index)
    if not sel:
        bm.free()
        return None
    keep = set(sel)
    bm2 = bm.copy()
    bm2.faces.ensure_lookup_table()
    bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in keep], context="FACES")
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sel], context="FACES")
    me2 = me.copy()
    me2.name = me.name + "__band"
    bm2.to_mesh(me2)
    bm2.free()
    bm.to_mesh(me)
    bm.free()
    me.update()
    me2.update()
    ob2 = bpy.data.objects.new(ob.name + "__band", me2)
    ob2.matrix_world = ob.matrix_world
    for col in ob.users_collection:
        col.objects.link(ob2)
    return ob2


def join_band(ob, ob2):
    """merge a split_band object back into `ob` and weld the split seam (coincident boundary vertices only)."""
    import bmesh
    import bpy
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.from_mesh(ob2.data)
    bnd = [v for v in bm.verts if v.is_boundary]
    if bnd:
        bmesh.ops.remove_doubles(bm, verts=bnd, dist=1e-6)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    me2 = ob2.data
    bpy.data.objects.remove(ob2, do_unlink=True)
    if me2.users == 0:
        bpy.data.meshes.remove(me2)


def compound_cull(c, wings, procs=4, max_views=None, wall_head=True):
    """ONE note-6 cull over every wing's targets.  kit 1.7 r2: max_views thins the viewpoints (compound_views) and
    `procs` spawn workers are allowed for this cull (VILLAGE_CULL_PROCS is set to it for the call only; art bible 8
    budgets a build on 4 shared cores).  A dying worker falls back to one process (core.visibility_cull).
    kit 1.7 r4: wall_head=True adds wall_head_views for the wall parts of every round wing whose eave lip is below
    its wall head (per-target viewpoints, so the extra stations cost only those parts' cull) AND protects that band:
    the outward polygons of the wall parts between the eave lip and the plate top are split off before the cull
    (split_band; they stay occluders) and merged back after it (join_band), so the cull can never open that band --
    a sliver of a face there, seen at a grazing angle beside a post, may miss every sample point of the cull."""
    from .core import visibility_cull
    names = [f"{w.prefix}_{t}" for w in wings for t in w.cull_targets]
    bands = []
    if wall_head:
        import bpy
        for w in wings:
            zb = wall_head_band(w)
            if zb is None:
                continue
            for p in WALL_HEAD_PARTS:
                ob = bpy.data.objects.get(f"{w.prefix}_{p}")
                if ob is None or ob.type != "MESH" or ob.name not in names or ob.data.users > 1:
                    continue
                n0 = len(ob.data.polygons)
                solids = [(o.center[:2], o.solid[0], o.solid[1]) for o in wings if o is not w and o.solid]
                ob2 = split_band(ob, zb[0], zb[1], w.center, solids=solids)
                if ob2 is not None:
                    bands.append((ob, ob2))
                    core.log(f"  wall-head band protected ({w.name}): {ob.name} {len(ob2.data.polygons)} of {n0} "
                             f"polygons at z {zb[0]:.2f}-{zb[1]:.2f} kept out of the cull")
    obs = [o for o in c.coll.all_objects if o.type == "MESH"]
    views = compound_views(c, wings, max_views=max_views)
    extra = {}
    if wall_head:
        for w in wings:
            extra.update(wall_head_views(w, wings))
    old = os.environ.get("VILLAGE_CULL_PROCS")
    os.environ["VILLAGE_CULL_PROCS"] = str(int(procs))
    try:
        n = visibility_cull(names, extra_views=views, procs=procs, objects=obs, extra_by_target=extra or None)
    finally:
        if old is None:
            os.environ.pop("VILLAGE_CULL_PROCS", None)
        else:
            os.environ["VILLAGE_CULL_PROCS"] = old
        for ob, ob2 in bands:
            join_band(ob, ob2)
    core.log(f"compound hidden-geometry cull: -{n} polygons")
    return n


# =================================================================================================================
# decal anchors over the whole compound
# =================================================================================================================
def thin_anchors(items, n_max):
    """keep at most n_max anchors: every type keeps a share proportional to its count (at least 1), picked evenly
    through its list (deterministic)."""
    if n_max is None or len(items) <= n_max:
        return list(items)
    by = {}
    for i, it in enumerate(items):
        by.setdefault(it["type"], []).append(i)
    tot = len(items)
    quota = {t: max(1, int(math.floor(n_max * len(ix) / tot))) for t, ix in by.items()}
    spare = n_max - sum(quota.values())
    for t in sorted(by, key=lambda t: -len(by[t])):           # hand out the rounding remainder
        if spare <= 0:
            break
        if quota[t] < len(by[t]):
            quota[t] += 1
            spare -= 1
    keep = set()
    for t, ix in by.items():
        q = min(quota[t], len(ix))
        sel = np.unique(np.round(np.linspace(0, len(ix) - 1, q)).astype(int))
        keep.update(ix[j] for j in sel)
    return [it for i, it in enumerate(items) if i in keep]


def _final_anchor_gate(c, da, audit=True, n_max=120):
    from .decals import SurfaceProbe
    n0 = len(da.items)
    bad = []
    if audit:
        from .anchor_audit import audit_anchors
        probe = SurfaceProbe([o for o in c.coll.all_objects if o.type == "MESH"])
        kw = dict(audit) if isinstance(audit, dict) else {}
        bad = audit_anchors(da, probe, drop=True, **kw)
    n1 = len(da.items)
    da.items = thin_anchors(da.items, n_max)
    core.log(f"compound decal anchors: {n0} placed, {n0 - n1} dropped by the whole-building audit "
             f"(covered by a neighbouring wing / junction), {n1 - len(da.items)} thinned -> {len(da.items)}")
    for b in bad[:40]:
        core.log("    " + b)
    return dict(placed=n0, dropped_audit=n0 - n1, thinned=n1 - len(da.items), kept=len(da.items))


# =================================================================================================================
# the build
# =================================================================================================================
def build_compound(spec):
    """run a compound building spec (see the module doc).  Keys:
        collection, building_id, wings [Wing], junctions [fn(c, **kw) or (fn, kw)], junction_prefix (default
        <collection>J), cull (True), cull_procs (4), decal_audit (True or audit_anchors kwargs), decal_max (120),
        out, decal_json, decal_meta.
    Returns the Compound context."""
    from .assembly import _validate_decals, decal_gate_option
    from . import guards
    import bpy
    opt = guards.opt_outs(spec, spec["collection"])
    core.reset_scene()
    top = core.new_collection(spec["collection"])
    wings = spec["wings"]
    for i, w in enumerate(wings):
        core.log(f"== wing {w.name} ({w.frame.__name__}, prefix {w.prefix})")
        wopt = dict(opt)
        wopt.update(guards.opt_outs(w, f"{spec['collection']}/{w.name}"))
        g = w.frame(w.prefix, **w.params)
        g.make_collections(f"{spec['collection']}_{w.name}")
        bpy.context.scene.collection.children.unlink(g.coll)
        top.children.link(g.coll)
        w.g = g
        try:
            for step in w.steps:
                fn, kw = step if isinstance(step, tuple) else (step, {})
                core.log(f"-- {w.name}: {getattr(fn, '__name__', fn)}")
                g.activate()                           # kit 1.8.0: scoped frame proxy (no-op for most frames)
                fn(g, **kw)
        finally:
            guards.end_lod_scope(g)                    # kit 1.9.0: the wing's tmpl_lod rule ends with the wing
        if "clearance" not in wopt:                    # kit 1.9.0 guard (wing-local, the wing's own meshes)
            guards.entrance_clearance(g, entrances=w.entrances)
        if w.decals:
            g.activate()
            w.decals(g)
        dv = decal_gate_option(wopt, w.decal_validate, f"{spec['collection']}/{w.name}")
        if dv is not None or w.decals:
            _validate_decals(g, dv)
        core.log(f"   wing {w.name}: {len(g.coll.all_objects)} objects, {g.triangles()} triangles, "
                 f"{len(g.decals.items)} anchors")
        _move_objects(w.objects(), _translate(PARK * (i + 1)))
    # place every wing
    for i, w in enumerate(wings):
        _move_objects(w.objects(), w.M @ _translate(-PARK * (i + 1)))
        _apply_unique(w.objects())
        _transform_anchors(w.g.decals.items, w.M)
    bpy.context.view_layer.update()
    # junctions
    jc = core.new_collection(f"{spec['collection']}_junctions", top)
    c = Compound(jc, spec.get("junction_prefix", spec["collection"] + "J"), wings)
    c.top = top
    for step in spec.get("junctions", []):
        fn, kw = step if isinstance(step, tuple) else (step, {})
        core.log(f"-- junction: {getattr(fn, '__name__', fn)}")
        fn(c, **kw)
    c.coll = top                               # from here on c.coll is the whole building
    if spec.get("cull", True):
        compound_cull(c, wings, procs=spec.get("cull_procs", 4), max_views=spec.get("cull_max_views", 260),
                      wall_head=spec.get("cull_wall_head", True))
    # kit 1.9.0 guard seal_probe: every registered roof-through-body junction (the compound's junction steps and
    # each wing's own modules), on the whole placed building after its one cull
    all_meshes = [o for o in top.all_objects if o.type == "MESH"]
    js = guards.probed_junctions(getattr(c, "SEAL_JUNCTIONS", None), opt)
    if js:
        guards.junction_seal_probe(all_meshes, js, prefix=c.prefix)
    for w in wings:
        wopt = {k: v for k, v in opt.items() if not isinstance(v, dict)}   # per-junction opt-outs name their level
        wopt.update(w.opt_out)
        js = guards.probed_junctions(getattr(w.g, "SEAL_JUNCTIONS", None), wopt)
        if js:
            guards.seal_junctions(w.g, junctions=js, objects=all_meshes,
                                  transform=lambda xy, w=w: w.to_world(np.array([xy[0], xy[1], 0.0]))[:2])
    # decal anchors: every wing's (already in world coordinates) + the junctions', audited on the whole building
    da = DecalAnchors(spec["collection"])
    for w in wings:
        da.items.extend(w.g.decals.items)
    da.items.extend(c.decals.items)
    rep = _final_anchor_gate(c, da, audit=spec.get("decal_audit", True), n_max=spec.get("decal_max", 120))
    n = da.build_collection()
    core.log(f"decal anchors: {n}")
    if spec.get("decal_json"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["decal_json"])), exist_ok=True)
        extra = dict(spec.get("decal_meta") or {})
        extra["validation"] = rep
        extra["wings"] = {w.name: dict(frame=w.frame.__name__, prefix=w.prefix, at=list(w.at),
                                       yaw_deg=round(math.degrees(w.yaw), 3)) for w in wings}
        da.export_json(spec["decal_json"], building=spec.get("building_id", spec["collection"]), extra=extra)
    if spec.get("uv_finish", True):                    # kit 1.10.0: grain / collapsed UVs + walked-top Mask B
        from . import uvgrain
        ents = []
        for w in wings:                                # each wing's entrances, wing-local -> world
            for e in (guards.entrances_of(w.g) if w.entrances is None else
                      [e if isinstance(e.get("origin"), np.ndarray) else guards._ent(**e) for e in w.entrances]):
                o3 = np.asarray(e["origin"], float)
                o3 = np.array([o3[0], o3[1], 0.0 if o3.shape == (2,) else o3[2]])
                ents.append(dict(e, name=f"{w.prefix} {e['name']}", origin=w.to_world(o3),
                                 out=w.dir_world(np.asarray(e["out"], float))))
        uvgrain.finish_building(top.all_objects, ents, log=core.log)
    tris = core.count_triangles(top.all_objects)
    core.log(f"objects {len(top.all_objects)} triangles {tris}")
    c.triangles = tris
    c.da = da
    if spec.get("out"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["out"])), exist_ok=True)
        core.save_blend(spec["out"])
    return c
