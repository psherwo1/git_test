"""components.masonry -- THE coursed-rubble body module of the kit (kit 1.8.0 consolidation).

Two modules built coursed rubble bodies side by side:
    stone_body.stone_body          a DECLARED tier_frame Body (round / regular polygon, battered) with framed openings
    rubble_walls.path_stone_wall   a wall along ANY plan polyline (gable tops, quoins, openings at path distances)
    rubble_walls.round_stone_body  a battered round body on any frame (openings by azimuth)
All three lay the kit's ONE stone generator through components.stone_wall (layout_wall / fill_voids / polygonize /
lay_stones / mortar_sheet); they differ in the plan map (SurfMap / PathMap / round_map_factory), the coursing table
(stone_body.RUBBLE_CFG / rubble_walls.RUBBLE_CFG) and how the mortar body is cut, and every signed-off build depends on
those choices, so the three bodies stay three implementations behind this ONE entry point:

    masonry_wall(g, name, path=None, body=None, round=None, openings=(), **kw)        KIT COMPONENT
        exactly one of
          path=[(x, y), ...]          -> rubble_walls.path_stone_wall(g, name, path, openings=[(s, spec)], ...)
          body=True                   -> stone_body.stone_body(g, name, openings=[spec.at(th_deg)], ...): `name` is a
                                         body declared on a TierFrame (tier_frame.declare_bodies)
          round=dict(center, r_base, batter_deg, top)
                                      -> rubble_walls.round_stone_body(g, name, openings=[(az_deg, spec)], ...)
        openings: components.openings specs (door(...) / window(...)) or the family's own dicts; **kw go to the chosen
        builder unchanged (top / top_fn / clip / seed / cfg / quoins / hero_s; clip_by / below / coping / quoins ...).

    Re-exported so a recipe imports masonry from one place:
        PathMap, SurfMap, path_stone_wall, round_stone_body, stone_body, framed_openings, coping_ledge,
        WALL_RUBBLE (rubble_walls.RUBBLE_CFG), BODY_RUBBLE (stone_body.RUBBLE_CFG), door, window (components.openings)
"""
from .openings import door, opening_spec, resolve, window  # noqa: F401
from .rubble_walls import RUBBLE_CFG as WALL_RUBBLE  # noqa: F401
from .rubble_walls import PathMap, path_stone_wall, round_stone_body  # noqa: F401
from .stone_body import RUBBLE_CFG as BODY_RUBBLE  # noqa: F401
from .stone_body import SurfMap, coping_ledge, framed_openings, stone_body  # noqa: F401


def masonry_wall(g, name, path=None, body=None, round=None, openings=(), **kw):  # noqa: A002
    """KIT COMPONENT: the one coursed-rubble body entry point (see the module doc)."""
    picked = [k for k, v in (("path", path), ("body", body), ("round", round)) if v is not None and v is not False]
    if len(picked) != 1:
        raise ValueError(f"masonry_wall {name!r}: give exactly one of path= / body= / round= (got {picked or 'none'})")
    if path is not None:
        return path_stone_wall(g, name, path, openings=list(openings), **kw)
    if body is not None and body is not False:
        return stone_body(g, name, openings=list(openings), **kw)
    r = dict(round)
    return round_stone_body(g, name, center=r.pop("center", (0.0, 0.0)), r_base=r.pop("r_base", 3.6),
                            batter_deg=r.pop("batter_deg", 2.5), top=r.pop("top", None), openings=list(openings),
                            **dict(r, **kw))
