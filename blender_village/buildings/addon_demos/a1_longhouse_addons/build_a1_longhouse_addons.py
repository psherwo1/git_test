"""a1_longhouse_addons -- the WALL add-ons (kit 1.19: components.lean_to, components.porch) proved on a DEMO COPY of
the accepted v3 longhouse.  v3's recipe is IMPORTED unchanged (its plan, walls, thatch, round end, cone and finial);
this recipe only adds steps, plus the host settings the add-ons need:

  host eave   the thatch eave is lifted in one soft arch over the front door (GableRoof(eave_lifts=[eave_lift(...)]),
              the barn's "eyelid", kit 1.16) and a second over the lean-to on the back; the walls' heads follow the
              warped deck (under_z_world) and the rafter tails under the arches are dropped (rafter_lift_max, kit 1.17)
  lean-to     4.0 x 2.2 m on the back (north) long wall, taking in the east window: an open-fronted store in the
              village shingle (16 deg at its ends, its wall line arching up under the host's arch: ridge_sag < 0,
              swept eave), rubble end walls with quoined fronts, a hewn plate on a middle post (dressed pad, curved
              knee braces) with a 1.86 m clear opening, ledger + common rafters, lime flaunching and lead verge aprons
              against the stone; checked to stay under the host's eave
  porch       over the front door: an ARCHED, bell-cast shingle hood (its own eave_lift + eave_sweep) on two curved
              brackets (the barn's hoist-beam arm + curved knee brace), an arched front beam >= 2.32 m (art bible 7),
              ledger, rafters, flaunching and aprons; checked to stay under the lifted thatch soffit
Run:  python -I build_a1_longhouse_addons.py   -> a1_longhouse_addons.blend + decal_anchors.json (next to this file)
      A1_FAST=1 skips the hidden-geometry ray test (quick looks only); A1_OUT=<path.blend> writes elsewhere.
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "kit"))

from village_kit.assembly import build_building  # noqa: E402
from village_kit.components.composite import composite_decals, composite_hidden_cull, recenter  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.lean_to import lean_to, plane_wall  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, linear_roof  # noqa: E402
from village_kit.components.porch import porch  # noqa: E402

BID = "a1_longhouse_addons"
_spec = importlib.util.spec_from_file_location(
    "v3_recipe", os.path.join(ROOT, "buildings", "variants", "v3_longhouse_roundend", "build_v3_longhouse_roundend.py"))
V3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V3)                     # the accepted recipe, read only (its main() is never called)

# ---- host settings: the thatch eave lifted in one soft arch over the porch (front) and over the lean-to (back) ------
LIFT = eave_lift(V3.DOOR_X, side=-1, width=6.0, height=1.2, fade=2.5)          # front: over the door hood
LEAN_X = -5.9                                   # the lean-to's centre on the back wall (it takes in the east window)
LIFT_N = eave_lift(LEAN_X, side=1, width=8.0, height=1.2, fade=2.5)           # back: the lean-to dies in under it
ROOF = GableRoof(x0=V3.X_GABLE, x1=-0.6, half=V3.HALF, wall_z=V3.WALL_Z, pitch_deg=40.0, overhang=0.45,
                 verge=(0.40, 0.0), thick=0.30, step=0.10, exposure=0.30, name="body_roof", eave_lifts=[LIFT, LIFT_N])
LIFT_MAX = 0.08                                   # no host rafter tails where the arch lifts the eave more than this

def body_top(x, y):
    """v3's wall head (2 cm into the deck), on the WARPED deck: the front wall rises under the lifted eave."""
    return float(ROOF.under_z_world(np.array([[x, y]]))[0]) + 0.02


V3.ROOF = ROOF                                    # v3's steps() / body_top / under_deck read these module globals
V3.body_top = body_top

# ---- the add-ons ----------------------------------------------------------------------------------------------------
LEAN = dict(name="lean_to", W=plane_wall((LEAN_X, V3.HALF), (0.0, 1.0)), s0=-2.0, s1=2.0, depth=2.2,
            z_face=2.86, pitch_deg=16.0, overhang=0.30, verge=(0.18, 0.18), covering="shingle", ends="rubble",
            end_t=0.40, max_span=1.8,
            soft=dict(ridge_sag=-0.25, eave_sweep=0.06, sweep_len=0.6, wave=0.012),   # its wall line arches up
            below=ROOF, below_lift_max=LIFT_MAX, below_clear=0.08, seed=1901)   # 8 cm: the roll belly
PORCH = dict(name="porch", W=plane_wall((V3.DOOR_X, -V3.HALF), (0.0, -1.0)), width=2.1, depth=1.0, clear=2.32,
             pitch_deg=22.0, overhang=0.25, side=0.20, covering="shingle", brace=(0.65, 0.75),
             soft=dict(eave_sweep=0.08, sweep_len=0.5, wave=0.008,                # bell-cast lip
                       eave_lifts=[eave_lift(0.0, side=1, width=2.6, height=0.22, fade=1.0)]),   # arched hood
             below=ROOF, below_lift_max=LIFT_MAX, seed=1931)

def steps():
    st = []
    for step in V3.steps():
        fn, kw = step if isinstance(step, tuple) else (step, {})
        if fn is linear_roof:
            kw = dict(kw, rafter_lift_max=LIFT_MAX)
        if fn is composite_hidden_cull or fn is recenter:
            continue
        st.append((fn, kw) if kw or isinstance(step, tuple) else fn)
    st += [(lean_to, LEAN), (porch, PORCH)]
    return st + ([] if os.environ.get("A1_FAST") else [hidden_cull_host]) + [recenter]


ADDON_PARTS = ("_lean_to", "_porch")


def hidden_cull_host(g):
    """v3's hidden-geometry cull on the host only: the add-ons (open shed, door hood) are seen from under and
    inside, where the cull's viewpoint loops do not reach, and they are trimmed at the wall already."""
    from village_kit.components.composite import BACKING, _meshes
    targets = [o.name for o in _meshes(g) if o.data.users == 1 and not any(b in o.name for b in BACKING)
               and not any(p in o.name for p in ADDON_PARTS)]
    return composite_hidden_cull(g, targets=targets)


def main():
    from functools import partial
    out = os.environ.get("A1_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="A1L", collection="A1L", building_id=BID,
        frame=RoundFrame, params=V3.KIT,
        steps=steps(),
        decals=partial(composite_decals, moss_normal="slope"),
        decal_validate=V3.DECAL_VALIDATE,
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in V3.KIT.items() if k != "cone_age"},
                        host="v3_longhouse_roundend (recipe imported)", host_eave_lift=LIFT,
                        addons=dict(lean_to={k: v for k, v in LEAN.items() if k not in ("W", "below")},
                                    porch={k: v for k, v in PORCH.items() if k not in ("W", "below")})),
    ))


if __name__ == "__main__":
    main()
