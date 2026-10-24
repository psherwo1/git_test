"""tools/ue/building_prep.py -- shared Blender-side preparation for the Unreal exporters
(export_building_fbx.py, export_building_glb.py).  Runs in bpy (python.exe -I, bpy 5.1.x).

prepare(blend, building_id) -> dict(obj=<ONE joined triangulated mesh object, world metres, Z up>, info=..., anchors=...)

What it does
  * opens the blend, collects the renderable building meshes and EXCLUDES helpers: DECAL_ANCHORS empties, objects hidden in
    viewport/render, collections or objects whose name looks like ground / scale figure / proxy / helper / lookdev;
  * bakes modifiers and pooled linked duplicates into real geometry in world space (first version: no instancing);
  * every palette slot name is checked against the 15 kit names (a ".001" suffix is stripped with a warning, anything else fails);
  * 'Mask' becomes the ONLY colour attribute (raw 0-1 data) and is the active + render colour;
  * one UV map; everything triangulated and joined into ONE object with the slots in PALETTE order.
"""
import json
import os
import re
import sys

import numpy as np

PALETTE = ("M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber",
           "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_earth", "M_moss")
EXCLUDE_NAME = re.compile(r"(ground|terrain|scale_?fig|figure|human|proxy|helper|lookdev|^LD_|_LD$|backdrop|sky|stage|ruler|"
                          r"turntable|camera)", re.I)
EXCLUDE_COLL = re.compile(r"(DECAL_ANCHORS|ground|helper|proxy|lookdev|scale|figure|hidden|stage|camera|light)", re.I)


def log(*a):
    print("[export]", *a, flush=True)


def stats_mask(me):
    n = len(me.attributes["Mask"].data)
    arr = np.zeros(n * 4, np.float32)
    me.attributes["Mask"].data.foreach_get("color_srgb" if me.attributes["Mask"].data_type == "BYTE_COLOR" else "color", arr)
    a = arr.reshape(-1, 4)
    out = {}
    for i, c in enumerate("RGB"):
        v = a[:, i]
        out[c] = dict(mean=round(float(v.mean()), 4), p5=round(float(np.percentile(v, 5)), 4),
                      p50=round(float(np.percentile(v, 50)), 4), p95=round(float(np.percentile(v, 95)), 4),
                      min=round(float(v.min()), 4), max=round(float(v.max()), 4))
    out["B_gt_0.5_fraction"] = round(float((a[:, 2] > 0.5).mean()), 4)
    out["corners"] = int(n)
    return out


def collect(scene):
    import bpy
    keep, skipped = [], []
    hidden_in_vl = set()
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        why = None
        if ob.hide_render or ob.hide_viewport:
            why = "hidden"
        else:
            try:
                if ob.hide_get():
                    why = "hidden in view layer"
            except Exception:  # noqa
                pass
        if why is None and EXCLUDE_NAME.search(ob.name):
            why = "helper/ground/figure name"
        if why is None and any(EXCLUDE_COLL.search(c.name) for c in ob.users_collection) and \
                not any(re.search(r"kit_instances$", c.name) for c in ob.users_collection):
            why = "helper collection " + ",".join(c.name for c in ob.users_collection)
        if why is None and len(ob.data.polygons) == 0:
            why = "no polygons"
        if why is None and ob.get("exclude_from_export"):
            why = "exclude_from_export"
        (skipped if why else keep).append((ob, why))
    return [o for o, _ in keep], [(o.name, w) for o, w in skipped]


def read_anchors(scene):
    """DA_* empties -> dicts in building-local metres, Blender axes (Z up, entrance -Y)."""
    import bpy
    out = []
    coll = bpy.data.collections.get("DECAL_ANCHORS")
    objs = list(coll.all_objects) if coll else [o for o in scene.objects if o.type == "EMPTY" and o.name.startswith("DA_")]
    for e in sorted(objs, key=lambda o: o.name):
        if e.type != "EMPTY":
            continue
        M = e.matrix_world.to_3x3()
        n = (M @ __import__("mathutils").Vector((0, 0, 1))).normalized()
        up = (M @ __import__("mathutils").Vector((0, 1, 0))).normalized()
        r = (M @ __import__("mathutils").Vector((1, 0, 0))).normalized()
        out.append(dict(name=e.name, type=e.get("decal_type", ""), pos=list(e.matrix_world.translation), normal=list(n), up=list(up),
                        right=list(r), size=[float(e.get("size_w", 0.5)), float(e.get("size_h", 0.5))],
                        surface=e.get("surface", ""), probability=float(e.get("probability", 1.0)), seed=int(e.get("seed", 0))))
    return out


def prepare(blend, building_id=None, verbose=True):
    import bpy
    import bmesh
    from mathutils import Matrix

    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    scene = bpy.context.scene
    bid = building_id or os.path.splitext(os.path.basename(blend))[0]
    objs, skipped = collect(scene)
    if not objs:
        raise SystemExit("no renderable building meshes found")
    dg = bpy.context.evaluated_depsgraph_get()
    log(f"{bid}: {len(objs)} mesh objects, {len(skipped)} skipped; unit scale {scene.unit_settings.scale_length}")

    tmp_coll = bpy.data.collections.new("_EXPORT_TMP")
    scene.collection.children.link(tmp_coll)
    slot_names_all, pooled, warnings = set(), 0, []
    temp_objs, src_tris = [], 0
    mats = {n: bpy.data.materials.get(n) for n in PALETTE}
    for n in PALETTE:
        if mats[n] is None:
            mats[n] = bpy.data.materials.new(n)
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        if ob.data.users > 1:
            pooled += 1
        # slot -> palette index
        lut = []
        for s in ob.material_slots:
            nm = s.material.name if s.material else None
            if nm is None:
                raise SystemExit(f"{ob.name}: empty material slot")
            base = re.sub(r"\.\d{3}$", "", nm)
            if base != nm:
                warnings.append(f"{ob.name}: slot {nm} renamed to {base}")
            if base not in PALETTE:
                raise SystemExit(f"{ob.name}: material slot {nm!r} is not one of the 15 palette names")
            lut.append(PALETTE.index(base))
            slot_names_all.add(base)
        if not lut:
            raise SystemExit(f"{ob.name}: no material slots")
        lut = np.array(lut, np.int32)
        mi = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", mi)
        mi = lut[np.clip(mi, 0, len(lut) - 1)]
        me.materials.clear()
        for n in PALETTE:
            me.materials.append(mats[n])
        me.polygons.foreach_set("material_index", mi)
        # Mask only
        if "Mask" not in me.color_attributes:
            raise SystemExit(f"{ob.name}: no 'Mask' colour attribute (build with kit >= 1.10)")
        for ca in list(me.color_attributes):
            if ca.name != "Mask":
                me.color_attributes.remove(ca)
        # one UV map named UVMap
        while len(me.uv_layers) > 1:
            me.uv_layers.remove(me.uv_layers[-1])
        if len(me.uv_layers) == 0:
            raise SystemExit(f"{ob.name}: no UV map")
        me.uv_layers[0].name = "UVMap"
        M = ob.matrix_world.copy()
        me.transform(M)
        if M.determinant() < 0:
            me.flip_normals()
        # drop attributes that bloat / confuse the join (selection, point/face attributes other than sharp)
        for a in list(me.attributes):
            if a.name in ("Mask", "UVMap", "position", "sharp_edge", "sharp_face", "material_index") or a.name.startswith("."):
                continue
            try:
                me.attributes.remove(a)
            except Exception:  # noqa
                pass
        src_tris += sum(max(0, p.loop_total - 2) for p in me.polygons)
        o2 = bpy.data.objects.new("_tmp_" + ob.name, me)
        tmp_coll.objects.link(o2)
        temp_objs.append(o2)
    # join
    bpy.ops.object.select_all(action="DESELECT") if bpy.context.object else None
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    act = temp_objs[0]
    for o in temp_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = act
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = bid
    me = obj.data
    me.name = bid
    # triangulate (bmesh keeps loop attributes)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="SHORT_EDGE", ngon_method="EAR_CLIP")
    bm.to_mesh(me)
    bm.free()
    me.update()
    # Mask: only colour attribute, active + render, byte colour kept
    assert [c.name for c in me.color_attributes] == ["Mask"], [c.name for c in me.color_attributes]
    me.color_attributes.active_color = me.color_attributes["Mask"]
    me.color_attributes.render_color_index = 0
    mstats = stats_mask(me)
    tris = len(me.polygons)
    used = sorted(set(np.array([p.material_index for p in me.polygons], np.int32).tolist()))
    # drop unused slots? keep palette order but only used ones, remap, so UE gets only used slots
    mi = np.zeros(tris, np.int32)
    me.polygons.foreach_get("material_index", mi)
    remap = {old: new for new, old in enumerate(used)}
    mi2 = np.array([remap[v] for v in mi], np.int32)
    me.materials.clear()
    for old in used:
        me.materials.append(mats[PALETTE[old]])
    me.polygons.foreach_set("material_index", mi2)
    me.update()
    bb = np.array([obj.matrix_world @ __import__("mathutils").Vector(c) for c in obj.bound_box])
    anchors = read_anchors(scene)
    info = dict(id=bid, source_blend=os.path.abspath(blend).replace("\\", "/"), mesh_objects=len(objs), pooled_object_count=pooled,
                skipped_objects=skipped, warnings=warnings, triangles=tris, source_triangles=src_tris,
                slots=[PALETTE[o] for o in used], slot_triangles={PALETTE[o]: int((mi2 == remap[o]).sum()) for o in used},
                bounds_m=dict(min=[round(float(v), 4) for v in bb.min(0)], max=[round(float(v), 4) for v in bb.max(0)]),
                mask=mstats, decal_anchor_count=len(anchors), unit_scale_length=scene.unit_settings.scale_length)
    log(f"tris={tris} slots={info['slots']} bounds={info['bounds_m']}")
    return dict(obj=obj, info=info, anchors=anchors)


def anchors_to_ue(anchors):
    """Blender metres (x, y, z) -> Unreal centimetres (x, -y, z).  Both exporters mirror Y exactly like Unreal's own
    importer does (right-handed Z-up -> left-handed Z-up): Blender +X -> UE +X, Blender +Y -> UE -Y, Z unchanged, so a
    building whose door faces Blender -Y has its door facing UE +Y."""
    def v(p, s):
        return [round(p[0] * s, 3), round(-p[1] * s, 3), round(p[2] * s, 3)]
    return [dict(a, pos_cm=v(a["pos"], 100.0), normal=v(a["normal"], 1.0), up=v(a["up"], 1.0), right=v(a["right"], 1.0),
                 size_cm=[a["size"][0] * 100.0, a["size"][1] * 100.0], pos_blender_m=[round(c, 5) for c in a["pos"]])
            for a in anchors]


def write_sidecars(out_dir, bid, info, anchors, extra):
    ue = anchors_to_ue(anchors)
    for a in ue:
        a.pop("pos", None)
        a.pop("size", None)
    data = dict(format="village_kit decal anchors, Unreal frame", building=bid, units="centimetres",
                space="UE static-mesh local space of the imported building mesh (origin = building base centre, ground Z = 0)",
                conversion="UE = (x, -y, z) of Blender metres (x100 for positions). Directions: (x, -y, z). Door faces -Y in Blender = +Y in UE. "
                           "normal = outward surface normal, up = decal up, right = decal width axis (all unit vectors in the UE frame).",
                count=len(ue), anchors=ue)
    with open(os.path.join(out_dir, "decal_anchors.json"), "w") as f:
        json.dump(data, f, indent=1)
    info = dict(info, **extra)
    with open(os.path.join(out_dir, bid + "_export.json"), "w") as f:
        json.dump(info, f, indent=1)
    return info

