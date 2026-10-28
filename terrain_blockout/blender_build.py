"""Blender build: valley blockout + top-down height bake.

    blender -b --factory-startup -P blender_build.py -- [--inputs DIR] [--out DIR] [--sigma 15]

Written for Blender 3.6 - 4.x, headless. 1 Blender unit = 1 metre.
Blender world: X = map x (east), Y = 2500 - map y (north up), Z = height, so a top-down
orthographic camera sees map y = 0 at the top of the image.

Geometry, lake detection, smoothing and the bake sampling come from terrain_common.py,
which is also what run_pipeline.py uses, so both paths give the same numbers.
NOTE: this script has not been executed in Blender by its author (no Blender was available).
It prints a check table at the end; read that before trusting the files.
"""
import argparse
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import terrain_common as tc  # noqa: E402

CHECKS = [("waterfall base", 542, 1932, 12.9), ("terrace hamlet", 337, 1882, 195.6),
          ("North town", 737, 537, 5.6), ("East town", 1737, 1417, 3.0)]
EXR_N, PNG_N = 2048, 2017


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=os.path.join(HERE, "inputs"))
    ap.add_argument("--out", default=os.path.join(HERE, "outputs_blender"))
    ap.add_argument("--sigma", type=float, default=15.0)
    ap.add_argument("--open-radius", type=int, default=4)
    return ap.parse_args(argv)


# ----------------------------------------------------------------------------- helpers
def read_image_rows_top_first(path):
    """Load an image as Non-Color float and return an (H, W, 4) array with row 0 = TOP.
    Blender stores image rows bottom-up, hence the flip."""
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    arr = buf.reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(img)
    return arr


def new_collection(scene, name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(col)
    return col


def new_mesh_object(name, verts, faces, collection, edges=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], list(edges), [tuple(f) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def height_material(hmin, hmax):
    """Emission shader whose colour is the normalised world-space Z (grey 0..1).
    Pure emission: no lighting, so the render is the data."""
    mat = bpy.data.materials.new("HeightEmission")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.clamp = True
    rng.inputs["From Min"].default_value = hmin
    rng.inputs["From Max"].default_value = hmax
    rng.inputs["To Min"].default_value = 0.0
    rng.inputs["To Max"].default_value = 1.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    L = nt.links.new
    L(geo.outputs["Position"], sep.inputs["Vector"])
    L(sep.outputs["Z"], rng.inputs["Value"])
    L(rng.outputs["Result"], em.inputs["Color"])
    L(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def grid_quads(n):
    """Face index tuples for an n x n vertex grid, vertex id = j * n + i, j = map row (north first).
    Wound counter-clockwise seen from +Z in Blender world."""
    f = []
    for j in range(n - 1):
        for i in range(n - 1):
            f.append(((j + 1) * n + i, (j + 1) * n + i + 1, j * n + i + 1, j * n + i))
    return f


def world(x_m, y_m, z):
    return (x_m, tc.MAP_SIZE - y_m, z)


# ----------------------------------------------------------------------------- build
def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    meta = json.load(open(os.path.join(args.inputs, "valley_heightmap_meta.json")))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = "ValleyBlockout"
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = "METERS"

    # --- 2. load heightmap (Non-Color, row 0 = top) and convert with the JSON formula
    rgba = read_image_rows_top_first(os.path.join(args.inputs, "valley_heightmap_16bit.png"))
    h = rgba[..., 0].astype(np.float64) * tc.parse_scale(meta)   # float image already holds pixel16 / 65535
    assert h.shape == (meta["height_samples"], meta["width_samples"])
    for name, x, y, exp in CHECKS:  # axis / scale / colour-space guard on the raw data
        got = h[int(y // 5), int(x // 5)]
        if abs(got - exp) > 0.5:
            raise RuntimeError(f"source heightmap check failed at {name}: {got:.2f} m vs {exp} m "
                               "(flipped/transposed rows, or the PNG was colour-managed)")

    # --- 3/4. lakes + blockout heights
    lk = tc.find_lakes(h, args.open_radius)
    level = lk["level"]
    V, lake_v, _ = tc.build_blockout(h, lk["union"], level, args.sigma)
    hmin, hmax = 0.0, float(meta["max_m"])

    # --- 6. collections
    col_block = new_collection(sc, "Blockout")
    col_lakes = new_collection(sc, "Lakes")
    col_grid = new_collection(sc, "Grid")
    col_lines = new_collection(sc, "Grid_Lines", col_grid)
    col_cells = new_collection(sc, "Grid_Cells", col_grid)
    col_labels = new_collection(sc, "Grid_Labels", col_grid)
    col_ref = new_collection(sc, "Reference")
    col_bake = new_collection(sc, "Bake")

    mat = height_material(hmin, hmax)

    # --- 3. blockout: plain editable mesh, NO modifiers
    n = V.shape[0]
    xs = np.arange(n) * tc.MESH_STEP
    verts = [world(xs[i], xs[j], V[j, i]) for j in range(n) for i in range(n)]
    terrain = new_mesh_object("Blockout_Terrain", verts, grid_quads(n), col_block)
    terrain.data.polygons.foreach_set("use_smooth", [True] * len(terrain.data.polygons))
    terrain.data.materials.append(mat)
    terrain["mesh_spacing_m"] = tc.MESH_STEP
    terrain["smoothing_sigma_m"] = args.sigma
    terrain.color = (0.45, 0.55, 0.32, 1.0)

    # --- 4. lakes: flat planes at the water level, built from the 5 m mask (shoreline not smoothed)
    lake_info = []
    for nm, mask in zip(["Lake_West", "Lake_East"], lk["lakes"]):
        vs, fs = tc.lake_plane_mesh(mask, level)
        ob = new_mesh_object(nm, vs, fs, col_lakes)
        ob.data.materials.append(mat)
        ob.color = (0.27, 0.47, 0.75, 1.0)
        ob["water_level_m"] = level
        ob["area_m2"] = float(mask.sum() * 25)
        lake_info.append({"name": nm, "water_level_m": level, "area_m2": float(mask.sum() * 25)})

    # --- 5. grid overlay: 25 x 25 cells of 100 m, A-Y across (west->east), 1-25 down (north->south)
    zlift = 1.0
    gl_verts, gl_edges = [], []
    per = 4  # mesh vertices per 100 m
    for k in range(26):
        for horizontal in (False, True):
            base = len(gl_verts)
            for t in range(n):
                i, j = (t, k * per) if horizontal else (k * per, t)
                gl_verts.append(world(xs[i], xs[j], V[j, i] + zlift))
            gl_edges += [(base + t, base + t + 1) for t in range(n - 1)]
    lines = new_mesh_object("Grid_100m_Lines", gl_verts, [], col_lines, edges=gl_edges)
    lines.color = (0.05, 0.05, 0.05, 1.0)
    lines.hide_render = True
    for ci in range(25):
        for rj in range(25):
            label = f"{tc.col_letter(ci)}{rj + 1}"
            cv = []
            for jj in range(per + 1):
                for ii in range(per + 1):
                    i, j = ci * per + ii, rj * per + jj
                    cv.append(world(xs[i], xs[j], V[j, i] + zlift * 0.5))
            cf = grid_quads(per + 1)
            cell = new_mesh_object(f"Cell_{label}", cv, cf, col_cells)
            cell.display_type = "WIRE"
            cell.hide_render = True
            cell["cell"] = label
            cell["x0_m"], cell["x1_m"] = ci * tc.GRID_CELL, (ci + 1) * tc.GRID_CELL
            cell["y0_m"], cell["y1_m"] = rj * tc.GRID_CELL, (rj + 1) * tc.GRID_CELL
            cx, cy = (ci + 0.5) * tc.GRID_CELL, (rj + 0.5) * tc.GRID_CELL
            zc = float(tc.bilinear(V, np.array(cx / tc.MESH_STEP), np.array(cy / tc.MESH_STEP)))
            cu = bpy.data.curves.new(f"Label_{label}", "FONT")
            cu.body = label
            cu.size = 18.0
            cu.align_x, cu.align_y = "CENTER", "CENTER"
            lb = bpy.data.objects.new(f"Label_{label}", cu)
            lb.location = world(cx, cy, zc + 3.0)
            lb.hide_render = True
            lb["cell"] = label
            col_labels.objects.link(lb)
    col_grid.hide_render = True   # never part of the bake

    # --- 6. reference: original unsmoothed 5 m heightmap, hidden
    hh, ww = h.shape
    rverts = [world((c + 0.5) * 5, (r + 0.5) * 5, h[r, c]) for r in range(hh) for c in range(ww)]
    ref = new_mesh_object("Reference_Unsmoothed_5m", rverts, grid_quads(ww), col_ref)
    ref["note"] = "original 500x500 heightmap at 5 m, vertex at sample centres, not smoothed, lakes/river included"
    ref.hide_viewport = True
    ref.hide_render = True
    ref.hide_set(True)
    col_ref.hide_render = True

    # --- 7. bake: orthographic camera over exactly 2500 x 2500 m
    cam_d = bpy.data.cameras.new("BakeCam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = tc.MAP_SIZE
    cam_d.clip_start, cam_d.clip_end = 1.0, 3000.0
    cam_d.sensor_fit = "AUTO"
    cam = bpy.data.objects.new("BakeCam", cam_d)
    cam.location = (tc.MAP_SIZE / 2, tc.MAP_SIZE / 2, 1500.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)          # looks straight down -Z, image up = +Y = north
    col_bake.objects.link(cam)
    sc.camera = cam

    world_d = bpy.data.worlds.new("Black")
    world_d.use_nodes = True
    bg = world_d.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0, 0, 0, 1)
    bg.inputs["Strength"].default_value = 0.0
    sc.world = world_d

    r = sc.render
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.filter_width = 0.01          # point sample at the pixel centre, no blur of the data
    sc.cycles.max_bounces = 0
    r.film_transparent = False
    r.dither_intensity = 0.0
    r.use_compositing = False
    r.use_sequencer = False
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0
    r.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.view_settings.use_curve_mapping = False
    sc.display_settings.display_device = "sRGB"
    sc.sequencer_colorspace_settings.name = "Non-Color"

    exr_path = os.path.join(args.out, "valley_blockout_height_2048.exr")
    png_path = os.path.join(args.out, "valley_blockout_height_2017_16bit.png")

    # 32-bit EXR 2048: scene-linear float, view transform does not touch EXR
    r.resolution_x = r.resolution_y = EXR_N
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    r.image_settings.color_mode = "RGB"
    r.image_settings.exr_codec = "ZIP"           # lossless
    r.use_file_extension = True
    r.filepath = exr_path
    bpy.ops.render.render(write_still=True)

    # 16-bit PNG 2017: PNG is display-referred, so use the Raw view transform for this one render.
    # With Standard the sRGB curve would be baked into the heights. Restored afterwards.
    r.resolution_x = r.resolution_y = PNG_N
    r.image_settings.file_format = "PNG"
    r.image_settings.color_depth = "16"
    r.image_settings.color_mode = "BW"
    r.image_settings.compression = 15
    sc.view_settings.view_transform = "Raw"
    r.filepath = png_path
    bpy.ops.render.render(write_still=True)
    sc.view_settings.view_transform = "Standard"
    r.resolution_x = r.resolution_y = EXR_N
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    r.image_settings.color_mode = "RGB"

    # --- 8. bake_meta.json
    actual = (float(V.min()), float(V.max()))
    bake_meta = tc.make_bake_meta(hmin, hmax, level, actual, args.sigma, os.path.basename(exr_path),
                                  os.path.basename(png_path), EXR_N, PNG_N,
                                  produced_by="blender_build.py (Blender %s, Cycles 1 spp, emission)" % bpy.app.version_string)
    json.dump(bake_meta, open(os.path.join(args.out, "bake_meta.json"), "w"), indent=2)

    # --- 9. check the real renders back from disk
    exr = read_image_rows_top_first(exr_path)[..., 0]
    png = read_image_rows_top_first(png_path)[..., 0]
    rows = []
    print("\n%-16s %-12s %9s %9s %9s %9s %9s" % ("point", "(x, y)", "expected", "EXR", "PNG", "dEXR", "dPNG"))
    for name, x, y, exp in CHECKS:
        e = tc.sample_bake(exr, x, y, hmin, hmax)
        p = tc.sample_bake(png, x, y, hmin, hmax)
        rows.append({"name": name, "x": x, "y": y, "expected_m": exp, "exr_m": e, "png_m": p,
                     "diff_exr_m": e - exp, "diff_png_m": p - exp,
                     "pass": abs(e - exp) < 3 and abs(p - exp) < 3})
        print("%-16s %-12s %9.2f %9.2f %9.2f %+9.2f %+9.2f  %s" % (
            name, f"({x},{y})", exp, e, p, e - exp, p - exp, "ok" if rows[-1]["pass"] else "OUTSIDE 3 m"))
    json.dump({"checks": rows, "lakes": lake_info, "water_level_m": level},
              open(os.path.join(args.out, "blender_checks.json"), "w"), indent=2)

    blend = os.path.join(args.out, "valley_blockout.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    print("saved", blend)

    # --- screenshots (Workbench). Wrapped so a preview problem cannot lose the deliverables above.
    try:
        previews(sc, args.out, col_grid)
    except Exception as exc:  # noqa: BLE001
        print("preview rendering skipped:", exc)


def previews(sc, out, col_grid):
    r = sc.render
    r.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "OBJECT"
    r.image_settings.file_format = "PNG"
    r.image_settings.color_depth = "8"
    r.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Standard"
    r.resolution_x, r.resolution_y = 1600, 1600
    col_grid.hide_render = False
    for ob in col_grid.all_objects:
        ob.hide_render = ob.name.startswith("Cell_")
    top = bpy.data.cameras.new("PrevTop")
    top.type, top.ortho_scale = "ORTHO", tc.MAP_SIZE * 1.02
    c1 = bpy.data.objects.new("PrevTop", top)
    c1.location = (tc.MAP_SIZE / 2, tc.MAP_SIZE / 2, 1500)
    sc.collection.objects.link(c1)
    sc.camera = c1
    r.filepath = os.path.join(out, "preview_topdown_grid.png")
    bpy.ops.render.render(write_still=True)
    for ob in col_grid.all_objects:
        ob.hide_render = True
    ob_cam = bpy.data.cameras.new("PrevObl")
    ob_cam.lens, ob_cam.clip_end = 35, 20000
    c2 = bpy.data.objects.new("PrevObl", ob_cam)
    c2.location = (-1400, -2800, 2600)       # south-west of the map, aimed at its centre
    c2.rotation_euler = (np.radians(61.8), 0, np.radians(-33.2))
    sc.collection.objects.link(c2)
    sc.camera = c2
    r.resolution_x, r.resolution_y = 1800, 1100
    r.filepath = os.path.join(out, "preview_oblique.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
