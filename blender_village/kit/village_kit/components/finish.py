"""components.finish -- ONE hidden-geometry cull and ONE decal entry point for every frame (kit 1.8.0 consolidation).

Each module family grew its own producer-note-6 cull and note-11 decal recipe.  They stay (their view sets, targets
and placement rules are tuned per family and every signed-off build depends on them), but a recipe no longer has to
know which one belongs to its frame:

    hidden_cull(g, family=None, **kw)        KIT STEP: the family's hidden-geometry cull
    building_decals(g, family=None, **kw)    KIT DECALS: the family's decal recipe (the gated form where one exists)
    family_of(g)                             the family name the two dispatch on

    family       frame / state                                    cull                         decals
    "round"      RoundFrame (hut family)                          frame.round_hidden_cull       round_decals.round_building_decals
    "composite"  any frame with path walls / linear roofs         composite.composite_hidden_cull  composite.composite_decals
                 (g.WALL_FACES or g.LINEAR_ROOFS published)
    "plan"       plan_frame.PlanFrame                             composite.composite_hidden_cull  composite.composite_decals
    "drum"       DrumFrame (mill family)                          drum_frame.drum_hidden_cull   drum_decals.drum_tower_decals_gated
    "tower"      DrumFrame with a tower roof (g.ROOF published)   tower_roof.tower_hidden_cull  tower_decals.round_tower_decals_gated
    "oct"        OctFrame (keep family)                           oct_cull.oct_hidden_cull      oct_decals.oct_building_decals
    "tier"       TierFrame (tier modules)                         tier_finish.tier_hidden_cull  tier_finish.tier_decals

family=... overrides the choice; **kw go to the family function unchanged.  A compound building (village_kit.compound)
keeps its own whole-building cull (compound_cull, run by build_compound); its wings' decal recipes can be this
building_decals.  Existing recipes that call a family function directly build exactly as before.
"""
import importlib

CULLS = dict(round=("frame", "round_hidden_cull"), composite=("composite", "composite_hidden_cull"),
             plan=("composite", "composite_hidden_cull"), drum=("drum_frame", "drum_hidden_cull"),
             tower=("tower_roof", "tower_hidden_cull"), oct=("oct_cull", "oct_hidden_cull"),
             tier=("tier_finish", "tier_hidden_cull"))
DECALS = dict(round=("round_decals", "round_building_decals"), composite=("composite", "composite_decals"),
              plan=("composite", "composite_decals"), drum=("drum_decals", "drum_tower_decals_gated"),
              tower=("tower_decals", "round_tower_decals_gated"), oct=("oct_decals", "oct_building_decals"),
              tier=("tier_finish", "tier_decals"))


def family_of(g):
    """the family a frame's cull / decals belong to (see the module doc)."""
    fam = getattr(type(g), "FAMILY", None) or getattr(g, "FAMILY", None)
    if fam == "drum" and getattr(g, "ROOF", None):
        return "tower"
    if fam == "round" and (getattr(g, "WALL_FACES", None) or getattr(g, "LINEAR_ROOFS", None)):
        return "composite"
    if fam is None:
        if getattr(g, "WALL_FACES", None) or getattr(g, "LINEAR_ROOFS", None) or getattr(g, "OPENINGS", None):
            return "composite"
        raise ValueError(f"finish: cannot tell the family of frame {type(g).__name__}; pass family=")
    return fam


def _fn(table, fam):
    if fam not in table:
        raise ValueError(f"finish: unknown family {fam!r}; one of {sorted(table)}")
    mod, name = table[fam]
    return getattr(importlib.import_module(f"{__package__}.{mod}"), name)


def hidden_cull(g, family=None, **kw):
    """KIT STEP (after every mesh is built): the hidden-geometry cull of g's family (producer note 6)."""
    return _fn(CULLS, family or family_of(g))(g, **kw)


def building_decals(g, family=None, **kw):
    """KIT DECALS (the build spec's `decals`): the decal-anchor recipe of g's family (producer note 11)."""
    return _fn(DECALS, family or family_of(g))(g, **kw)
