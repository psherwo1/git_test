"""v10_net_loft_cottage (NETC) -- a fisher's cottage: a rubble ground storey under a WATTLE-AND-DAUB loft (timber posts
with daub between them, producer note 20), one rounded-hip thatch LOAF (producer note 19, "an oval on the
rectangle"), a thatch EYEBROW over the door (note 18), an attached ROUND wattle-and-daub oven / store house on a
dry-stone plinth at the front-east corner under its own shingle cone (the kit's only cone), and a rounded thatch
LEAN-TO on the back wall for drying nets.  A declarative RECIPE: every piece is a village_kit module (v7_cottage,
v3_longhouse_roundend, a1_longhouse_addons, wattle_roundhut / v4_mixed daub); r2 adds the optional straight-daub
cladding style "post_daub" of components.timber_walls (kit 1.17).

Run:  python -I build_v10_net_loft_cottage.py  -> v10_net_loft_cottage.blend + decal_anchors.json (next to this file)
      NETC_FAST=1 skips the hidden-geometry cull (quick looks only); NETC_OUT=<path.blend> writes elsewhere.

Plan (the round store's centre is the origin; the house lies to its north-west; the build is recentred at the end):
  main    8.0 x 5.0 m (path_stone_wall RUBBLE_LARGE) to Z_SPLIT, then path_timber_wall style "post_daub" (timber
          posts <= 1.5 m apart up to the roof line, daub between, odd exposed wattle patch) up to the deck on every
          side: the half-storey loft.  One thatch loaf: GableRoof(hips="both", crown), ridge sag, swept eaves,
          out-of-true wave; the thatch eyebrow (grid="thatch", profile="arch") over the front door
  store   ROUND WATTLE-AND-DAUB wall r 1.50 m (round_daub_wall: post ring, daub coat, exposed wattle patches) on a
          dry-stone plinth (drystone_plinth), pegged wall plate, framed door (az 0, -Y) with step; a shingle cone
          (40 deg); the loaf runs into the round WALL below the cone eave (roof_junction.wall_abutment)
  lean-to rounded-roof thatch lean-to on the back wall (lean_to.lean_to roof_ends="round") under a lifted host eave
"""
import os
import sys
from functools import partial

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.ball_finial import ball_finial  # noqa: E402
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull, cone_roof,  # noqa: E402
                                              inside_box, inside_round, recenter, set_entrance)
from village_kit.components.daub import round_daub_wall, wall_finish_r11  # noqa: E402
from village_kit.components.doors import door_step, framed_door  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.lean_to import lean_to, plane_wall  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, eyebrow, linear_roof  # noqa: E402
from village_kit.components.orient_fix import orient_closed_slabs, orient_open_islands  # noqa: E402
from village_kit.components.plinth import drystone_plinth  # noqa: E402
from village_kit.components.roof_addons import roofs_top_fn, straight_span  # noqa: E402
from village_kit.components.roof_junction import round_eave_fill, wall_abutment  # noqa: E402
from village_kit.components.round_wall import wall_plate  # noqa: E402
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall  # noqa: E402
from village_kit.components.timber_walls import path_timber_wall  # noqa: E402
from village_kit.components.wall_openings import door_spec, window_spec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v10_net_loft_cottage"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
DIM = KitParams(radius=1.50, eave_z=3.85, overhang=0.42, pitch_deg=40.0, collar_r=0.30,       # the round store's cone
                cone_age=age_defaults(**AGE_R10), detail_rule=True, wall_finish=wall_finish_r11())
R_FACE = 1.58                                   # the store's daub face radius (wall line 1.50 + 6 cm coat + posts)
HALF, XC, YC = 2.5, -5.0, 3.5                   # main: half width, ridge centre x, ridge line y (store centre = 0, 0)
X0, X1 = XC - 4.0, XC + 4.0                     # 8.0 m long
Y0, Y1 = YC - HALF, YC + HALF                   # front (-Y) and back faces
WALL_Z, Z_SPLIT = 3.05, 2.05                    # deck at the faces; stone ground storey height (r2: a 1.0 m daub loft)
DOOR_X, LEAN_X = -6.2, -5.4
LIFT_N = eave_lift(LEAN_X - XC, side=1, width=6.5, height=2.1, fade=2.6)    # local x: the host eave arch over the lean-to
LIFT_MAX = 0.08
BROW = eyebrow(DOOR_X - XC, side=-1, grid="thatch", profile="arch", respace=True, d=1.3, width=2.5, height=0.90,
               lip=0.22, plateau=0.15, fade=1.1, window=dict(width=0.60, height=0.36, sill=0.05), close_ends=True,
               span_rows=True, seed=3)
MAIN = GableRoof(x0=-4.0, x1=4.0, half=HALF, wall_z=WALL_Z, pitch_deg=46.0, overhang=0.45, verge=(0.0, 0.0),
                 origin=(XC, YC), thick=0.28, name="roof", ridge_sag=0.15, eave_sag=0.04, eave_sweep=0.16,
                 sweep_len=1.0, wave=0.02, wave_seed=71, ridge_seat=True, hips="both", crown=0.5,
                 eyebrows=[BROW], eave_lifts=[LIFT_N])

# ---- plan: one path round the house, interior on the left, from the east wall's middle ---------------------------
PATH = [(X1, YC), (X1, Y1), (X0, Y1), (X0, Y0), (X1, Y0), (X1, YC)]
S_N, S_W, S_F = HALF, HALF + 8.0, HALF + 8.0 + 5.0       # path distance at the NE corner, NW corner, SW corner
WIN = window_spec(width=0.50, height=0.60, sill=1.05)
SMALL = window_spec(width=0.40, height=0.45, sill=1.20)
DOOR_S = S_F + (DOOR_X - X0)
OPENINGS = [(S_N + (X1 - (-8.0)), SMALL),                      # back, west of the lean-to
            (S_N + (X1 - LEAN_X), WIN),                        # back, inside the lean-to
            (S_W + HALF, SMALL),                               # west end
            (DOOR_S, door_spec(width=1.0, height=1.85)),       # the front door, under the eyebrow
            (S_F + (-2.9 - X0), SMALL),                        # front, east of the door
            (S_F + (-8.2 - X0), SMALL),                        # front, west
            (1.0, WIN)]                                        # east end, north half (clear of the store)
TOP = roofs_top_fn([MAIN])

# the loft band: on each side, the run over which the deck underside stands >= Z_SPLIT + 0.35
SIDES = dict(front=((X0, Y0), (X1, Y0)), back=((X0, Y1), (X1, Y1)), west=((X0, Y0), (X0, Y1)),
             east=((X1, Y0), (X1, Y1)))
CUT_E = -1.70       # the front / east bands stop short of the round store (its face reaches here)


def _span(p0, p1, lim=None):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    ss = np.linspace(0.0, 1.0, 400)
    pts = p0 + ss[:, None] * (p1 - p0)
    ok = [k for k in range(len(ss)) if TOP(*pts[k]) >= Z_SPLIT + 0.35
          and (lim is None or lim(pts[k]))]
    if not ok:
        return None
    return pts[ok[0]], pts[ok[-1]]


def _lim(name):
    if name == "east":          # r2: the store stands at the FRONT-east corner (its door faces -Y, clear of the house)
        return lambda p: p[1] >= -CUT_E
    if name == "front":
        return lambda p: p[0] <= CUT_E
    return None


BANDS = {n: _span(a, b, _lim(n)) for n, (a, b) in SIDES.items()}
BANDS = {n: v for n, v in BANDS.items() if v is not None}


def stone_top(x, y):
    z = TOP(x, y)
    for n, v in BANDS.items():
        (ax, ay), (bx, by) = SIDES[n]
        a, b = v
        d = np.array([bx - ax, by - ay])
        L = float(np.hypot(*d))
        u = d / L
        q = np.array([x - ax, y - ay])
        t, off = float(q @ u), abs(float(q @ np.array([-u[1], u[0]])))
        ta, tb = float((a - np.array([ax, ay])) @ u), float((b - np.array([ax, ay])) @ u)
        if off < 0.75 and ta - 0.2 <= t <= tb + 0.2:
            return min(z, Z_SPLIT)
    return z


def body_under(P):
    P = np.asarray(P, float)
    return MAIN.under_z_world(P)


def eave_fill_daub(g):
    """the masonry-free eave fill of the daub round wall: a band from just under the wall plate top up into the cone."""
    return round_eave_fill(g, r_off=0.0, z_bot=float(g.PLATE_TOP) - 0.12)


def daub_door(g):
    """the store door's head infill is daub, not boards (kit 1.17 DOOR_INFILL_DAUB)."""
    g.DOOR_INFILL_DAUB = True


def steps():
    in_round = inside_round((0.0, 0.0), R_FACE, depth=0.12)
    at_round = inside_round((0.0, 0.0), R_FACE, depth=-0.10)
    in_drum = inside_round((0.0, 0.0), R_FACE, depth=0.10)
    st = [
        (set_entrance, dict(xy=(DOOR_X, Y0))),
        # ---- the round oven / store house: dry-stone plinth, wattle-and-daub wall, pegged plate, framed door
        drystone_plinth,
        round_daub_wall,
        wall_plate,
        (path_stone_wall, dict(name="walls", path=PATH, top_fn=stone_top, openings=OPENINGS, clip=in_round,
                               cfg=RUBBLE_LARGE, hero_s=(DOOR_S - 2.5, DOOR_S + 2.5), seed=31)),
    ]
    for k, (n, (a, b)) in enumerate(BANDS.items()):
        st.append((path_timber_wall, dict(name=f"loft_{n}", path=[tuple(a), tuple(b)], z0=Z_SPLIT - 0.08,
                                          top=Z_SPLIT + 0.30, top_fn=TOP, style="post_daub",
                                          gable_style="post_daub", bay_max=1.5, rough=True, seed=331 + k)))
    st += [
        (linear_roof, dict(roof=MAIN, covering="thatch", clip=in_drum, seed=71, comb=False, rafter_skip=at_round,
                           rafter_lift_max=LIFT_MAX)),
        (wall_abutment, dict(roof=MAIN, center=(0.0, 0.0),
                             radius=lambda z: np.full_like(np.asarray(z, float), R_FACE - 0.01))),
        (cone_roof, dict(seed=606)),
        (ball_finial, dict(seed=5, hat_seg=96, fit=True)),
        eave_fill_daub,
        door_step,
        daub_door,
        framed_door,
        (lean_to, dict(name="lean_to", W=plane_wall((LEAN_X, Y1), (0.0, 1.0)), s0=-1.9, s1=1.9, depth=2.0,
                       z_face=3.28, pitch_deg=16.0, overhang=0.22, verge=(0.18, 0.18), covering="shingle",
                       ends="rubble", end_t=0.40, max_span=1.8, brace=(0.36, 0.28), headroom=(2.10, 1.95),
                       soft=dict(ridge_sag=-0.15, eave_sweep=0.06, sweep_len=0.6, wave=0.012, verge_flare=0.06,
                                 flare_len=0.5, eave_lifts=[eave_lift(0.0, side=1, width=4.4, height=0.18, fade=1.5)]),
                       verge_board=dict(below=0.025, above=0.0), below=MAIN, below_lift_max=LIFT_MAX,
                       below_clear=0.08, below_roll=0.10, seed=1901, roof_ends="round",
                       round_kw=dict(end_over=0.45, hip=0.55, ne=3.0, bulge=0.04, arch_wall=0.15, arch_eave=0.18,
                                     wave=0.012, thatch=(0.22, 0.08), course=0.30, eave_roll={}, decals=True))),
        (orient_open_islands, dict(parts=("_stones",))),
        (orient_closed_slabs, dict(parts=("_deck",))),
    ]
    return st + ([] if os.environ.get("NETC_FAST") else [composite_hidden_cull]) + [recenter]


def decals(g):
    with straight_span(MAIN):
        composite_decals(g, moss_normal="slope", timber=True, timber_soot=False)


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_blockers", "_deck", "_mortar", "_reveals", "_backing",
                                       "_roof_blocker", "_cap_collar", "_abutment", "_eave_fill", "_roof_underlap",
                                       "_apex_blocker", "_daub_interior", "_door_panel_backing", "_floor"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("NETC_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="NETC", collection="NETC", building_id=BID, frame=RoundFrame, params=DIM,
        steps=steps(), decals=decals, decal_validate=DECAL_VALIDATE, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in DIM.items() if k not in ("cone_age", "wall_finish")},
                        main=dict(x=(X0, X1), y=(Y0, Y1), wall_z=WALL_Z, z_split=Z_SPLIT, pitch_deg=46.0))))


if __name__ == "__main__":
    main()
