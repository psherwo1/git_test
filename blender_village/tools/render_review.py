"""Standard review renders for a building .blend (geometry-only clay renders).

Usage:
    <python-with-bpy> blender_village/tools/render_review.py <building.blend> <out_dir> [--samples N] [--res W H] [--views hero,front,...] [--device GPU]

(<python-with-bpy> is /opt/bpyenv/bin/python in the cloud container, or the desktop venv's python.)

Every building is judged with the same lighting, clay shader, camera set and a
1.8 m human scale figure so the director compares like with like. Materials in
the file are overridden with a neutral clay; only geometry is evaluated.

Writes <out_dir>/<view>.png for each view plus <out_dir>/stats.json
(triangle count, object count, bounding box, material slots, and the estimated
share of hidden/buried triangles from hidden_tris.py, detailed in hidden.json, and
the mesh objects missing the mandatory "Mask" colour attribute).
"""
import argparse
import json
import math
import os
import subprocess
import sys

import bpy
from mathutils import Vector

VIEWS = {
    # name: (azimuth deg, elevation deg, distance factor, focal mm, look-at height factor)
    "hero": (-35, 8, 2.2, 35, 0.35),      # 3/4 eye-level-ish, like ref2's foreground
    "front": (0, 4, 2.4, 50, 0.4),
    "side": (90, 4, 2.4, 50, 0.4),
    "back": (180, 12, 2.4, 40, 0.4),
    "aerial": (-50, 38, 2.6, 40, 0.3),    # high 3/4, like ref3
    "actor_closeup": (-20, 2, 0.9, 28, 0.12),  # eye-height 1.65 m near the entrance
}


def parse():
    argv = sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("blend")
    p.add_argument("out_dir")
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--res", type=int, nargs=2, default=[1280, 720])
    p.add_argument("--views", default=",".join(VIEWS))
    p.add_argument("--device", choices=["CPU", "GPU"], default="CPU",
                   help="Cycles device. GPU uses --gpu-backend (OPTIX for NVIDIA RTX) and falls back to CPU.")
    p.add_argument("--gpu-backend", default="OPTIX", choices=["OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"])
    return p.parse_args(argv)


def scene_bounds(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def tri_count(depsgraph, objs):
    total = 0
    for o in objs:
        ev = o.evaluated_get(depsgraph)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is None:
            continue
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        ev.to_mesh_clear()
    return total


def add_scale_figure(location):
    """Simple 1.80 m mannequin (capsule body + head) for human scale."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=location + Vector((0, 0, 0.725)))
    body = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=location + Vector((0, 0, 1.68)))
    head = bpy.context.object
    for o in (body, head):
        o.name = "_REVIEW_scale_figure"
        o.data.materials.clear()
    return [body, head]


def main():
    a = parse()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
    scn = bpy.context.scene
    os.makedirs(a.out_dir, exist_ok=True)

    meshes = [o for o in scn.objects if o.type in {"MESH", "CURVE"} and not o.hide_render]
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = scene_bounds(meshes)
    stats = {
        "objects": len(meshes),
        "triangles": tri_count(dg, meshes),
        "bbox_min": list(lo),
        "bbox_max": list(hi),
        "size_m": list(hi - lo),
        "materials": sorted({s.material.name for o in meshes for s in o.material_slots if s.material}),
    }

    # Clay override
    clay = bpy.data.materials.new("_REVIEW_clay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
    bsdf.inputs["Roughness"].default_value = 0.65
    scn.view_layers[0].material_override = clay

    # Ground, lights, world
    center = (lo + hi) / 2
    size = max((hi - lo).x, (hi - lo).y, (hi - lo).z, 4.0)
    bpy.ops.mesh.primitive_plane_add(size=size * 12, location=(center.x, center.y, lo.z - 0.002))
    bpy.context.object.name = "_REVIEW_ground"
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.angle = math.radians(2.0)
    world = bpy.data.worlds.new("_REVIEW_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
    scn.world = world

    # Scale figure: in front of the building, slightly off-axis
    add_scale_figure(Vector((center.x + (hi - lo).x * 0.15, lo.y - 1.5, lo.z)))

    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    if a.device == "GPU":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = a.gpu_backend
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == a.gpu_backend
            if any(d.use for d in prefs.devices):
                scn.cycles.device = "GPU"
            else:
                print(f"render_review: no {a.gpu_backend} device found, rendering on CPU")
        except Exception as e:  # never block a review on device setup
            print("render_review: GPU setup failed, rendering on CPU:", e)
    scn.cycles.samples = a.samples
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = a.res
    scn.render.image_settings.file_format = "PNG"
    scn.view_settings.view_transform = "AgX"

    bpy.ops.object.camera_add()
    cam = bpy.context.object
    scn.camera = cam
    cam.data.clip_end = 5000

    for name in a.views.split(","):
        az, el, dist_f, lens, look_f = VIEWS[name]
        target = Vector((center.x, center.y, lo.z + (hi - lo).z * look_f))
        dist = size * dist_f * (lens / 35)
        if name == "actor_closeup":
            # Human eye height near the front, looking at the entrance zone
            target = Vector((center.x, lo.y, lo.z + 1.5))
            dist = max(size * 0.45, 4.0)
        d = Vector((
            math.sin(math.radians(az)) * math.cos(math.radians(el)),
            -math.cos(math.radians(az)) * math.cos(math.radians(el)),
            math.sin(math.radians(el)),
        ))
        cam.location = target + d * dist
        if name in ("hero", "front", "side", "actor_closeup"):
            cam.location.z = max(lo.z + 1.65, cam.location.z) if name == "actor_closeup" else cam.location.z
        cam.data.lens = lens
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        scn.render.filepath = os.path.join(os.path.abspath(a.out_dir), f"{name}.png")
        bpy.ops.render.render(write_still=True)

    # Hidden / buried triangle estimate on the untouched file (see hidden_tris.py)
    hidden_json = os.path.join(os.path.abspath(a.out_dir), "hidden.json")
    try:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hidden_tris.py"),
                        os.path.abspath(a.blend), "--samples", "8000", "--json", hidden_json],
                       check=True, capture_output=True, timeout=900)
        with open(hidden_json) as f:
            h = json.load(f)
        stats["est_hidden_pct"] = h["est_hidden_pct"]
        stats["est_hidden_triangles"] = h["est_hidden_triangles"]
    except Exception as e:  # never block the review on the estimate
        stats["est_hidden_pct"] = None
        print("hidden_tris failed:", e)
    stats["material_slot_count"] = len(stats["materials"])
    # Producer note 9: every mesh must carry a "Mask" colour attribute
    stats["mask_attribute_missing"] = sorted(
        o.name for o in meshes
        if o.type == "MESH" and not o.name.startswith("_REVIEW") and "Mask" not in o.data.color_attributes)

    with open(os.path.join(a.out_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print("REVIEW_STATS", json.dumps(stats))


if __name__ == "__main__":
    main()
