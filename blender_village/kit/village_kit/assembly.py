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


def build_building(spec):
    """run a declarative building spec:
        prefix, frame (Building subclass, called with **params), params (KitParams),
        steps: [(component(g, **kw), kw), ...]   in order (components publish what later ones need on g),
        decals: optional fn(g) adding decal anchors, out: .blend path, decal_json: optional path.
    Returns the frame g.  Starts from an empty factory scene, saves compressed."""
    core.reset_scene()
    g = spec["frame"](spec["prefix"], **dict(spec.get("params", {})))
    g.make_collections(spec.get("collection"))
    for step in spec["steps"]:
        fn, kw = step if isinstance(step, tuple) else (step, {})
        core.log(f"-- {getattr(fn, '__name__', fn)}")
        fn(g, **kw)
    if spec.get("decals"):
        spec["decals"](g)
    n = g.decals.build_collection()
    core.log(f"decal anchors: {n}")
    if spec.get("decal_json"):
        g.decals.export_json(spec["decal_json"], building=spec.get("building_id", spec["prefix"]),
                             extra=spec.get("decal_meta"))
    tris = g.triangles()
    core.log(f"objects {len(g.coll.all_objects)} (instances {g.pools.n_inst}, pooled meshes {len(g.pools)}) "
             f"triangles {tris}")
    if spec.get("out"):
        os.makedirs(os.path.dirname(os.path.abspath(spec["out"])), exist_ok=True)
        core.save_blend(spec["out"])
    return g
