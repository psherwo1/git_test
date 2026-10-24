"""Run the kit 1.9.0 geometry guards (entrance clearance gate, junction seal probe) on an already-built kit
building .blend, read-only -- to see what the guards will say before a full rebuild.

Usage:
    <python-with-bpy> blender_village/tools/guard_probe.py <file.blend> <building_id>

building_id is one of the seven kit buildings (hilltop_keep, wattle_roundhut, tower_windmill, v1_stone_watchtower,
v2_tiered_hall, v3_longhouse_roundend, v4_mixed).  The entrances and junctions are rebuilt from the recipes'
parameter tables through the same frames and the same village_kit.guards functions the build runs; where a value is
only known during the build (a drum's door radius, v3's recentring shift) the value from the recipe / build log is
used.  Nothing is written.  Prints one line per entrance / junction, then GUARD_PROBE <json>.
"""
import importlib.util
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kit"))


def _recipe(rel):
    spec = importlib.util.spec_from_file_location("recipe_" + os.path.basename(rel)[:-3], os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Fake:
    def __init__(self, prefix, coll):
        self.prefix = prefix
        self.coll = coll


def lin(z0, r0, z1, r1):
    return lambda z: float(np.interp(z, [z0, z1], [r0, r1]))


def main(path, bid):
    import bpy
    from village_kit import guards
    bpy.ops.wm.open_mainfile(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
    ents, juncs, prefix = [], [], ""
    if bid == "wattle_roundhut":
        from village_kit.components.frame import RoundFrame
        m = _recipe("buildings/wattle_roundhut/build_wattle_roundhut.py")
        g = RoundFrame("HUT", **dict(m.KIT))
        g.coll = bpy.data.collections["HUT"]
        ents, prefix = guards.entrances_of(g), "HUT"
    elif bid == "hilltop_keep":
        from village_kit.components.oct_frame import OctFrame
        m = _recipe("buildings/hilltop_keep/build_hilltop_keep.py")
        g = OctFrame("KEEP", **dict(m.KIT))
        g.coll = bpy.data.collections["KEEP"]
        ents, prefix = guards.entrances_of(g), "KEEP"
        cover = tuple(f"KEEP_{p}" for p in ("wing_roof_thatch", "wing_roof_thatch_courses", "wing_roof_rolls"))
        juncs = [dict(name="shake collar / stone cone", covering=("KEEP_roof_collar_shakes",), center=(0.0, 0.0),
                      radius=lambda z: float(np.interp(z, g.CONE_ZF, g.CONE_RF)),
                      z_range=(float(g.CONE_ZF[0]), g.COLLAR_TOP_Z + 0.3), ring=(0.0, 0.6)),
                 dict(name="wing thatch / turret", covering=cover, center=g.TUR_C,
                      radius=lambda z: float(np.interp(z, g.TUR_ZF, g.TUR_RF)), z_range=(2.0, g.WALL_H + 3.0),
                      ring=(0.0, 0.6)),
                 dict(name="wing thatch / hall", covering=cover, center=(0.0, 0.0),
                      radius=lambda z: g.A0 - max(z, 0.0) * g.BAT, z_range=(2.0, g.WALL_H + 0.6), ring=(0.0, 0.6))]
    elif bid == "tower_windmill":
        prefix = "MILL"
        ents = [dict(name="drum_door", origin=(0.0, -2.60), out=(0, -1), width=1.05, head=0.14 + 1.65 + 0.525)]
        juncs = [dict(name="apron / smock tower", covering=("MILL_apron_shingles",), center=(0.0, 0.0),
                      radius=lin(5.95, 1.55, 11.45, 0.95), z_range=(6.0 - 0.9, 6.3), ring=(0.0, 0.6))]
    elif bid == "v1_stone_watchtower":
        prefix = "WATCH"
        ents = [dict(name="drum_door", origin=(0.0, -2.48), out=(0, -1), width=1.05, head=0.14 + 1.65 + 0.525)]
    elif bid == "v2_tiered_hall":
        prefix = "HALL"
        ents = [dict(name="hall_door", origin=(0.0, -5.0), out=(0, -1), width=1.0, head=2.20, d0=0.25)]
    elif bid == "v3_longhouse_roundend":
        from village_kit.components.frame import RoundFrame
        m = _recipe("buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py")
        g = RoundFrame("LONG", **dict(m.KIT))
        sh = np.array([4.608, -0.006])                          # the recentring shift (build log)
        prefix = "LONG"
        ents = [dict(name="body_door", origin=(m.DOOR_X + sh[0], -m.HALF + sh[1]), out=(0, -1), width=1.0, head=2.20)]
        pz, pr, rf = g.PZ, g.PR, g.R_WALL + 0.14
        juncs = [dict(name="body_roof / round body", covering=("LONG_body_roof_covering", "LONG_body_roof_eave_roll"),
                      center=sh, radius=lambda z: float(np.interp(z, pz, pr)) if z >= pz[0] else rf,
                      z_range=(2.3, 5.3), ring=(0.0, 0.6))]
    elif bid == "v4_mixed":
        from village_kit.components.frame import RoundFrame
        m = _recipe("buildings/variants/v4_mixed/build_v4_mixed.py")
        g = RoundFrame("V4H", **dict(m.HOUSE))
        hx, hy = m.HOUSE_AT
        mx, my = m.MILL_AT
        prefix = "V4"
        ents = [dict(name="house framed_door", origin=(hx, hy + g.FRONT_Y), out=(0, -1), width=g.DOOR_W, head=g.HEAD_Z),
                dict(name="mill drum_door", origin=(mx, my - 2.05), out=(0, -1), width=1.0, head=0.14 + 1.62 + 0.5)]
        juncs = [dict(name="house roof / mill tower", covering=("V4H_roof_shingles", "V4H_roof_starter"),
                      center=(mx, my), radius=lin(0.0, 2.05, 5.5, 1.70), z_range=(2.2, 4.0), ring=(0.0, 0.6)),
                 dict(name="apron / smock tower", covering=("V4M_apron_shingles",), center=(mx, my),
                      radius=lin(6.55, 1.30, 10.25, 0.925), z_range=(6.6 - 0.9, 6.9), ring=(0.0, 0.6))]
    else:
        raise SystemExit(f"unknown building {bid}")
    fake = Fake(prefix, None)
    res = dict(building=bid, clearance=[], seal=[])
    if ents:
        res["clearance"] = guards.entrance_clearance(fake, entrances=ents, fail=False, objects=meshes)
    if juncs:
        for j in juncs:
            j["shift0"] = np.zeros(3)
        res["seal"] = guards.junction_seal_probe(meshes, juncs, prefix=prefix, fail=False)
    print("GUARD_PROBE", json.dumps(res, default=str))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(args[0], args[1])
