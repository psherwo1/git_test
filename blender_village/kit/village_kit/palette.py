"""village_kit.palette -- the shared 15-slot material palette (producer note 7).

This module is the ONLY place in the kit (and in any kit building) where materials are created.  Placeholder
materials only (named slots + a flat clay-ish base colour); texturing happens in Unreal.  Do not invent new slot
names: map anything new onto the closest entry below.
"""
PALETTE = ("M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber",
           "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead",
           "M_earth", "M_moss")
assert len(PALETTE) == 15

# what goes on each slot (producer note 7 table)
USAGE = {
    "M_stone": "stone", "M_stone_dressed": "dressed stone", "M_rubble": "rubble", "M_mortar": "mortar, chinking",
    "M_daub": "daub, plaster", "M_wattle": "wattle rods", "M_timber": "timber",
    "M_timber_weathered": "weathered timber", "M_roof_shingle": "shingles", "M_roof_shake": "shakes",
    "M_thatch": "thatch", "M_iron": "iron", "M_lead": "lead", "M_earth": "earth, apron, path",
    "M_moss": "moss clumps, if modelled",
}

# viewport / placeholder base colours (linear)
COLOR = {
    "M_stone": (0.52, 0.50, 0.46), "M_stone_dressed": (0.66, 0.64, 0.60), "M_rubble": (0.50, 0.48, 0.44),
    "M_mortar": (0.60, 0.58, 0.52), "M_daub": (0.70, 0.66, 0.58), "M_wattle": (0.30, 0.24, 0.17),
    "M_timber": (0.33, 0.24, 0.16), "M_timber_weathered": (0.42, 0.39, 0.35),
    "M_roof_shingle": (0.36, 0.38, 0.27), "M_roof_shake": (0.42, 0.37, 0.30), "M_thatch": (0.50, 0.43, 0.28),
    "M_iron": (0.10, 0.10, 0.11), "M_lead": (0.30, 0.31, 0.33), "M_earth": (0.36, 0.31, 0.24),
    "M_moss": (0.25, 0.35, 0.15),
}


def check(name):
    """raise if `name` is not a palette slot (the director treats any other slot as a must-fix)."""
    if name not in PALETTE:
        raise ValueError(f"material slot {name!r} is not in the 15-slot kit palette")
    return name


def material(name):
    """the bpy material for a palette slot, created on first use (idempotent across calls and after a
    factory reset: it looks the datablock up by name first)."""
    import bpy
    check(name)
    m = bpy.data.materials.get(name)
    if m is None:
        col = COLOR[name]
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*col, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*col, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
    return m


def slots_in_use(objects):
    """sorted palette slots used by a set of objects, plus any foreign slot names (should be empty)."""
    used, foreign = set(), set()
    for ob in objects:
        for s in getattr(ob, "material_slots", ()):
            if s.material:
                (used if s.material.name in PALETTE else foreign).add(s.material.name)
    return sorted(used), sorted(foreign)
