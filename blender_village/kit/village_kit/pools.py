"""village_kit.pools -- shared-mesh variant pools and linked duplicates (producer note 3).

Repeated small parts (shingle / shake / stone variants, chinking, pegs, nails, hinge parts, balusters) are built
once per variant as a mesh and placed as linked-duplicate MESH objects (shared mesh data).  render_review counts
and frames them (they are real mesh objects), and in Unreal they become instanced static meshes.

    pools = Pools("HUT", collection)                 # one per building (core.Building creates it)
    me = pools.mesh("peg", k, make_peg, sharp=28)    # make(acc, k) fills a core.Acc in LOCAL coordinates
    pools.place(me, "peg", R, t)                     # object HUT_peg_###, matrix = [R*scale | t]

Pool mesh names: <PREFIX>_<pool>_v<k>; instance names: <PREFIX>_<part>_<running number>.
"""
import numpy as np


class Pools:
    def __init__(self, prefix, collection=None, moss=None, default_moss=0.2):
        self.prefix = prefix
        self.collection = collection          # where instances are linked (a "<PREFIX>_kit_instances" collection)
        self.meshes = {}
        self.moss = dict(moss or {})         # per-pool constant Mask B (pooled parts have no world position)
        self.default_moss = default_moss
        self.n_inst = 0
        self.hygiene = False

    def mesh(self, pool, k, make, sharp=40.0, moss=None):
        """k-th variant of a pool; make(acc, k) fills a core.Acc in local coords. Built once, reused."""
        from .core import Acc
        key = (pool, k)
        if key not in self.meshes:
            m_ = moss if moss is not None else self.moss.get(pool, self.default_moss)
            acc = Acc(f"{self.prefix}_{pool}_v{k:02d}", sharp, cull=None, moss=m_, hygiene=self.hygiene)
            make(acc, k)
            self.meshes[key] = acc.build_mesh(clamp=False)
        return self.meshes[key]

    def place(self, mesh, part, R=None, t=(0, 0, 0), scale=1.0):
        """linked duplicate (shared mesh data) placed with a rigid transform (+ uniform scale)."""
        import bpy
        from mathutils import Matrix
        M = np.eye(4)
        M[:3, :3] = (np.eye(3) if R is None else np.asarray(R, float)) * scale
        M[:3, 3] = t
        self.n_inst += 1
        ob = bpy.data.objects.new(f"{self.prefix}_{part}_{self.n_inst:03d}", mesh)
        ob.matrix_world = Matrix(M.tolist())
        self.collection.objects.link(ob)
        return ob

    def __len__(self):
        return len(self.meshes)
