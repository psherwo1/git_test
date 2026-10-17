"""components.plan_frame -- a PLAIN building frame for rectangular / free-form plans (kit 1.8.0 consolidation).

New recipes whose plan has no round part (a barn, a store, a gabled house, an L-plan) used to borrow RoundFrame
for its context only, which dragged in a hut's derived dimensions (R_EAVE, a door frame at -Y, a cone profile) and
made composite_decals lay cone moss where there is no cone.  PlanFrame holds only what the generic modules read:

    PlanFrame(prefix="PLAN", footprint=None, entrance=(0.0, -3.0), entrance_r=3.0, entrance_h=2.5, detail_rule=True,
              hygiene=True, ground_skirt=0.04, **dims)

      footprint     the plan outline [(x, y), ...] (closed implicitly) or (x0, x1, y0, y1) for a rectangle; None =
                    unknown.  Published as g.FOOTPRINT (an (n, 2) array, counter-clockwise) and g.BOUNDS.
      entrance      (x, y) of the principal door (producer note 11's entrance zone, g.ENTRANCE / g.detail); a recipe
                    may still call composite.set_entrance to move it
      detail_rule   True -> core.DetailRule at the entrance; False -> DetailRule.off(); or a DetailRule
      hygiene       core.nanite_clean on every g.acc() mesh and pooled variant
      ground_skirt  vertices more than this far below Z = 0 are culled by g.acc() meshes (producer note 10)
      **dims        any recipe dimensions (published as upper-case attributes: wall_h=2.55 -> g.WALL_H), so a
                    recipe's parameter table can travel on the frame like a RoundFrame's

    Published empty, for the generic modules to fill: g.OPENINGS (wall_openings), g.WALL_FACES (rubble_walls),
    g.LINEAR_ROOFS (linear_roof), g.openings (stone_body-style records).

The generic modules that run on it unchanged: rubble_walls.path_stone_wall (and round_stone_body with top=),
wall_openings, linear_roof (without abut_cone), pyramid_roof, composite.set_entrance / inside_box / inside_round /
recenter / composite_hidden_cull / composite_decals, and the dispatchers components.finish.hidden_cull /
building_decals (family "plan" -> the composite cull and decals).
"""
from functools import partial

import numpy as np

from ..assembly import Building
from ..core import DetailRule


def _below_ground(skirt, V):
    return V[:, 2] < -skirt


class PlanFrame(Building):
    """a plain rectangular / free-form building frame (see the module doc)."""

    FAMILY = "plan"

    def __init__(self, prefix="PLAN", footprint=None, entrance=(0.0, -3.0), entrance_r=3.0, entrance_h=2.5,
                 detail_rule=True, hygiene=True, ground_skirt=0.04, **dims):
        super().__init__(prefix)
        self.Z_MIN = -float(ground_skirt) - 0.005
        self.GROUND_SKIRT = float(ground_skirt)
        self.z_clamp = None
        self._ground_cull = partial(_below_ground, self.GROUND_SKIRT)
        self.hygiene = bool(hygiene)
        self.pools.hygiene = bool(hygiene)
        ent = (float(entrance[0]), float(entrance[1]))
        self.ENTRANCE = ent
        if detail_rule is True:
            self.detail = DetailRule(entrance=ent, entrance_r=entrance_r, entrance_h=entrance_h)
        elif isinstance(detail_rule, DetailRule):
            self.detail = detail_rule
        else:
            self.detail = DetailRule.off()
        self.FOOTPRINT, self.BOUNDS = self._footprint(footprint)
        for k, v in dims.items():
            setattr(self, k.upper(), v)
        self.OPENINGS = []
        self.WALL_FACES = []
        self.LINEAR_ROOFS = {}
        self.openings = []
        self.subs = {}

    @staticmethod
    def _footprint(fp):
        if fp is None:
            return None, None
        if len(fp) == 4 and np.ndim(fp[0]) == 0:
            x0, x1, y0, y1 = (float(v) for v in fp)
            P = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        else:
            P = np.asarray(fp, float)
        area = 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))
        if area < 0:
            P = P[::-1].copy()
        return P, (float(P[:, 0].min()), float(P[:, 0].max()), float(P[:, 1].min()), float(P[:, 1].max()))

    def sub(self, name):
        """sub-collection <PREFIX>_<name> of the building collection (created on first use)."""
        from ..core import new_collection
        if name not in self.subs:
            self.subs[name] = new_collection(f"{self.prefix}_{name}", self.coll)
        return self.subs[name]

    def name(self, part):
        return f"{self.prefix}_{part}"

    def min_relief(self, P):
        """note-11 relief threshold (m) at world points P (..., 3): entrance_relief in the entrance zone."""
        return self.detail.min_at_v(P)

    def inside_plan(self, P, margin=0.0):
        """plan points P (..., 2+) inside the footprint, deeper than margin (False everywhere without one)."""
        P = np.asarray(P, float)
        if self.FOOTPRINT is None:
            return np.zeros(P.shape[:-1], bool)
        from ..geom import inside_poly
        x, y = P[..., 0].ravel(), P[..., 1].ravel()
        ins = inside_poly(x, y, self.FOOTPRINT)
        if margin > 0 and ins.any():
            A, B = self.FOOTPRINT, np.roll(self.FOOTPRINT, -1, 0)
            d = np.full(len(x), np.inf)
            for a, b in zip(A, B):
                ab = b - a
                t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(float(ab @ ab), 1e-12), 0, 1)
                d = np.minimum(d, np.hypot(x - a[0] - t * ab[0], y - a[1] - t * ab[1]))
            ins &= d > margin
        return ins.reshape(P.shape[:-1])

    def extent(self):
        """largest plan distance of the footprint from the origin (for view rings); 3 m without a footprint."""
        if self.FOOTPRINT is None:
            return 3.0
        return float(np.max(np.hypot(self.FOOTPRINT[:, 0], self.FOOTPRINT[:, 1])))


def rect_frame(prefix, x0, x1, y0, y1, door=None, **kw):
    """a PlanFrame on a rectangle; door = (x, y) of the principal door (default: the middle of the -Y side)."""
    door = door if door is not None else (0.5 * (x0 + x1), y0)
    return PlanFrame(prefix, footprint=(x0, x1, y0, y1), entrance=door, **kw)


__all__ = ["PlanFrame", "rect_frame"]
