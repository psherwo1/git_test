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
    decals / decal_validate the wing's decal recipe fn(g) and optional assembly-style anchor gate (dict / True)
    cull_targets            object parts (without prefix) the compound cull may thin (backed pieces only)
    reach                   plan radius of the wing's body for its actor rings (default: from its bounds)
    door                    (x, y) of its door in wing-local coords (door views); None = none
    view_heights            ring heights for the near rings (m)
    solid                   (radius, z_top) of the wing's solid body: other wings' viewpoints inside it are dropped
    ring_n                  stations per near ring (fewer = a faster cull; the review rings are always added)
    """

    def __init__(self, name, frame, prefix, params=None, steps=(), at=(0.0, 0.0), yaw_deg=0.0, decals=None,
                 decal_validate=None, cull_targets=(), reach=None, door=None, view_heights=(0.3, 1.0, 1.65, 2.3),
                 crane_heights=(5.0, 9.0), solid=None, ring_n=24):
        self.name = name
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
def compound_views(c, wings):
    """actor rings round every wing (moved to where it stands), crane rings, door views, the review cameras of the
    whole building; viewpoints inside another wing's solid body are dropped."""
    from .core import review_cameras, ring_views
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


def compound_cull(c, wings, procs=4):
    from .core import visibility_cull
    names = [f"{w.prefix}_{t}" for w in wings for t in w.cull_targets]
    obs = [o for o in c.coll.all_objects if o.type == "MESH"]
    n = visibility_cull(names, extra_views=compound_views(c, wings), procs=procs, objects=obs)
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
    from .assembly import _validate_decals
    import bpy
    core.reset_scene()
    top = core.new_collection(spec["collection"])
    wings = spec["wings"]
    for i, w in enumerate(wings):
        core.log(f"== wing {w.name} ({w.frame.__name__}, prefix {w.prefix})")
        g = w.frame(w.prefix, **w.params)
        g.make_collections(f"{spec['collection']}_{w.name}")
        bpy.context.scene.collection.children.unlink(g.coll)
        top.children.link(g.coll)
        w.g = g
        for step in w.steps:
            fn, kw = step if isinstance(step, tuple) else (step, {})
            core.log(f"-- {w.name}: {getattr(fn, '__name__', fn)}")
            fn(g, **kw)
        if w.decals:
            w.decals(g)
        if w.decal_validate is not None or w.decals:
            _validate_decals(g, w.decal_validate)
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
        compound_cull(c, wings, procs=spec.get("cull_procs", 4))
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
    tris = core.count_triangles(top.all_objects)
    core.log(f"objects {len(top.all_objects)} triangles {tris}")
    c.triangles = tris
    c.da = da
    if spec.get("out"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["out"])), exist_ok=True)
        core.save_blend(spec["out"])
    return c
