"""village_kit.assembly -- how a kit building is put together.

A kit building is a short declarative assembly:

    from village_kit.assembly import KitParams, build_building
    KIT = KitParams(radius=3.5, eave_z=2.395, ...)            # the building's dimension table (kit_set convention)
    def kit_set(**kw): KIT.set(**kw)                          # publish component parameters (unknown keys raise)
    SPEC = dict(prefix="HUT", collection="HUT", frame=RoundFrame, params=KIT,
                steps=[(drystone_plinth, {}), (round_daub_wall, dict(patches=...)), (conical_roof, {}), ...],
                post=[...], decals=hut_decals, out=".../wattle_roundhut.blend",
                decal_json=".../decal_anchors.json")
    build_building(SPEC)

Building is the per-building context every component receives as its first argument (`g`): name prefix, the
top-level collection, the shared-mesh pools (village_kit.pools), the decal anchors (village_kit.decals) and
g.acc(name) -> a core.Acc named <PREFIX>_<name> with the building's ground cull and buried-skirt clamp.
Building types with a richer shared frame subclass it (components.frame.RoundFrame for round huts / towers).

kit_set convention (shared with the keep and the mill): each building script owns ONE parameter table; kit_set(**kw)
validates and publishes component parameters to it before the build, a <PREFIX>_KIT_VARIANT environment variable
selects an alternative table that builds a different building from the same components.
"""
import os

import numpy as np

from . import core
from .decals import DecalAnchors
from .pools import Pools


class KitParams(dict):
    """a building's dimension table.  set(**kw) only accepts known keys (typos raise instead of being ignored)."""

    def set(self, **kw):
        for k, v in kw.items():
            if k not in self:
                raise KeyError(f"unknown kit parameter {k!r}; known: {sorted(self)}")
            self[k] = v
        return self

    def variant(self, **kw):
        """a copy with some parameters changed (validated)."""
        return KitParams(self).set(**kw)


class Building:
    """per-building assembly context (see module doc).  Subclasses add their shared frame."""

    def __init__(self, prefix, collection=None, ground_cull=None, z_clamp=None, pool_moss=None):
        self.prefix = prefix
        self.coll = collection
        self.inst_coll = None
        self.pools = Pools(prefix, None, moss=pool_moss)
        self.decals = DecalAnchors(prefix)
        self._ground_cull = ground_cull
        self.z_clamp = z_clamp
        self.hygiene = False                 # run core.nanite_clean on every built mesh
        self.objects = {}

    def make_collections(self, name=None):
        """top-level collection <name or PREFIX> + <PREFIX>_kit_instances for the pooled linked duplicates."""
        self.coll = core.new_collection(name or self.prefix)
        self.inst_coll = core.new_collection(f"{self.prefix}_kit_instances", self.coll)
        self.pools.collection = self.inst_coll
        return self.coll

    def ground_cull(self, V):
        if self._ground_cull is None:
            import numpy as np
            return np.zeros(len(V), bool)
        return self._ground_cull(V)

    def acc(self, name, sharp=40.0, cull="ground", moss=None, b_fn=None, hygiene=None):
        """core.Acc named <PREFIX>_<name>.  cull='ground' -> the building's ground cull, None -> no cull,
        or any callable(V) -> bool per vertex."""
        if cull == "ground":
            cull = self.ground_cull
        if hygiene is None:
            hygiene = self.hygiene
        return core.Acc(f"{self.prefix}_{name}", sharp, cull=cull, moss=moss, z_clamp=self.z_clamp, b_fn=b_fn,
                        hygiene=hygiene)

    def triangles(self):
        return core.count_triangles(self.coll.all_objects)

    def activate(self):
        """kit 1.8.0: called before every step / decal recipe of this frame.  A no-op here; the keep-family frames
        (OctFrame, TierFrame) point the module proxy oct_frame.FR at themselves, so several of them can be built in
        one compound."""
        return self

    # kit 1.8.0: the family the generic hidden_cull / building_decals entry points dispatch to
    # (components.finish).  None = decide from the frame's state (see finish.family_of).
    FAMILY = None


def _validate_decals(g, opt):
    """kit 1.3.0: the decal-anchor gate (village_kit.anchor_validate).  opt True / dict -> applied (snap, drop,
    outward normals, de-duplicate); None / False -> report only (anchors unchanged, counts in the build log)."""
    if not g.decals.items:
        return None
    from .anchor_validate import validate_anchors
    from .decals import SurfaceProbe
    kw = dict(opt) if isinstance(opt, dict) else {}
    apply = bool(opt)
    try:
        probe = SurfaceProbe([o for o in g.coll.all_objects if o.type == "MESH"])
        rep = validate_anchors(g.decals, probe, apply=apply, **kw)
    except Exception as e:                             # report mode must never break a build
        if apply:
            raise
        core.log(f"decal anchor check skipped: {e!r}")
        return None
    core.log(f"decal anchor check ({'applied' if apply else 'report only'}): " +
             ", ".join(f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}" for k, v in rep.items() if k != "bad"))
    for nm, why in rep["bad"]:
        core.log(f"    {nm}: {why}")
    return rep


def decal_gate_option(opt, value, who):
    """kit 1.9.0: the effective decal_validate option under the guard default.  Not opted out: absent -> True
    (applied); True / dict -> as given; a falsy value without an opt-out reason raises.  Opted out: the given value
    (None / False -> report only, as before 1.9.0)."""
    if "decal_validate" in opt:
        return value or None
    if value is None:
        return True
    if not value:
        raise ValueError(f"{who}: decal_validate={value!r} switches the decal guard off; use "
                         f"opt_out=dict(decal_validate='<reason>') instead")
    return value


def build_building(spec):
    """run a declarative building spec:
        prefix, frame (Building subclass, called with **params), params (KitParams),
        steps: [(component(g, **kw), kw), ...]   in order (components publish what later ones need on g),
        decals: optional fn(g) adding decal anchors, out: .blend path, decal_json: optional path,
        decal_validate: (kit 1.3.0) True / dict of anchor_validate.validate_anchors keywords -> the anchors
            are snapped and validated.  kit 1.9.0: absent = True (guard default); report-only needs an opt-out.
        opt_out: kit 1.9.0 {guard: reason} (village_kit.guards.GUARDS) -- the guard-rails run by default after the
            last step (entrance clearance, junction seal probe) and on the anchors (decal_validate);
        entrances: optional explicit entrance list for the clearance gate (default: what the door components
            published, guards.entrances_of).
    Returns the frame g.  Starts from an empty factory scene, saves compressed."""
    from . import guards
    opt = guards.opt_outs(spec, spec["prefix"])
    core.reset_scene()
    g = spec["frame"](spec["prefix"], **dict(spec.get("params", {})))
    g.make_collections(spec.get("collection"))
    try:
        for step in spec["steps"]:
            fn, kw = step if isinstance(step, tuple) else (step, {})
            core.log(f"-- {getattr(fn, '__name__', fn)}")
            g.activate()                               # kit 1.8.0: scoped frame proxy (no-op for most frames)
            fn(g, **kw)
    finally:
        guards.end_lod_scope(g)                        # kit 1.9.0: a tmpl_lod rule never outlives its building
    core.log("-- guards")
    guards.after_steps(g, opt, entrances=spec.get("entrances"))
    if spec.get("decals"):
        g.activate()
        spec["decals"](g)
    _validate_decals(g, decal_gate_option(opt, spec.get("decal_validate"), spec["prefix"]))
    n = g.decals.build_collection()
    core.log(f"decal anchors: {n}")
    if spec.get("decal_json"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["decal_json"])), exist_ok=True)
        extra = dict(spec.get("decal_meta") or {})
        if getattr(g.decals, "validation", None):      # kit 1.3.0: the anchor gate's counts (decal_validate)
            extra["validation"] = g.decals.validation
        g.decals.export_json(spec["decal_json"], building=spec.get("building_id", spec["prefix"]),
                             extra=extra or spec.get("decal_meta"))
    if spec.get("uv_finish", True):                    # kit 1.10.0: grain / collapsed UVs + walked-top Mask B
        from . import uvgrain
        ents = guards.entrances_of(g) if spec.get("entrances") is None else [
            e if isinstance(e.get("origin"), np.ndarray) else guards._ent(**e) for e in spec["entrances"]]
        uvgrain.finish_building(g.coll.all_objects, ents, log=core.log)
    tris = g.triangles()
    core.log(f"objects {len(g.coll.all_objects)} (instances {g.pools.n_inst}, pooled meshes {len(g.pools)}) "
             f"triangles {tris}")
    if spec.get("out"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["out"])), exist_ok=True)
        core.save_blend(spec["out"])
    return g
