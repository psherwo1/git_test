#!/usr/bin/env python3
"""Standalone (no Blender) run of the blockout + bake pipeline.

Produces the same numbers the Blender script is meant to produce, writes the
EXR / 16-bit PNG / bake_meta.json, runs the four-point check and renders previews.

    python3 run_pipeline.py [--sigma 15] [--open-radius 4]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import terrain_common as tc

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = [  # name, map x, map y, expected metres (from the brief)
    ("waterfall base", 542, 1932, 12.9),
    ("terrace hamlet", 337, 1882, 195.6),
    ("North town", 737, 537, 5.6),
    ("East town", 1737, 1417, 3.0),
]
EXR_N, PNG_N = 2048, 2017


def shoelace(p):
    p = np.asarray(p)
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # old Pillow
        return ImageFont.load_default()


# ----------------------------------------------------------------------------- previews
def hillshade(z, step, azimuth=315.0, altitude=45.0, exag=1.5):
    gy, gx = np.gradient(z * exag, step)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(360 - azimuth + 90), np.radians(altitude)
    s = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(az - aspect)
    return np.clip(s, 0, 1)


def tint(z):
    stops = [(0, (96, 140, 84)), (25, (150, 172, 100)), (80, (196, 178, 118)),
             (160, (170, 150, 128)), (260, (150, 146, 142)), (389, (246, 246, 248))]
    zs = np.array([s[0] for s in stops], float)
    out = np.zeros(z.shape + (3,))
    for ch in range(3):
        out[..., ch] = np.interp(z, zs, [s[1][ch] for s in stops])
    return out


def shade_map(z, step, lake=None):
    hs = hillshade(z, step)
    rgb = tint(z) * (0.35 + 0.75 * hs[..., None])
    if lake is not None:
        rgb[lake] = np.array([70, 120, 190]) * (0.85 + 0.15 * hs[lake][:, None])
    return np.clip(rgb, 0, 255).astype(np.uint8)


def draw_grid(im, labels=True, major=tc.GRID_CELL):
    d = ImageDraw.Draw(im)
    W = im.size[0]
    s = W / tc.MAP_SIZE
    for k in range(26):
        p = k * major * s
        d.line([(p, 0), (p, W)], fill=(20, 20, 20), width=1)
        d.line([(0, p), (W, p)], fill=(20, 20, 20), width=1)
    if labels:
        f = font(max(9, int(major * s * 0.2)))
        for i in range(25):
            for j in range(25):
                d.text(((i + 0.5) * major * s, (j + 0.5) * major * s), f"{tc.col_letter(i)}{j + 1}",
                       fill=(255, 255, 255), font=f, anchor="mm", stroke_width=1, stroke_fill=(0, 0, 0))


def draw_points(im, results):
    d = ImageDraw.Draw(im)
    s = im.size[0] / tc.MAP_SIZE
    f = font(16)
    for k, (name, x, y, exp) in enumerate(CHECKS, 1):
        cx, cy = x * s, y * s
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=(255, 40, 40), width=3)
        d.text((cx + 13, cy - 11), f"{k} {name}", fill=(255, 255, 255), font=f,
               stroke_width=2, stroke_fill=(150, 0, 0))


def oblique(V, lake_v, path, yaw=28.0, elev=33.0, zex=1.6, size=(1800, 1150)):
    a, e = np.radians(yaw), np.radians(elev)
    u = np.array([np.sin(a), np.cos(a)])      # depth axis (away from camera), world X east / Y north
    r = np.array([np.cos(a), -np.sin(a)])
    n = V.shape[0]
    xs = np.arange(n) * tc.MESH_STEP
    X, Yn = np.meshgrid(xs, tc.MAP_SIZE - xs)  # world coords
    sx = X * r[0] + Yn * r[1]
    dep = X * u[0] + Yn * u[1]
    sy = dep * np.sin(e) + V * zex * np.cos(e)
    scale = 0.40
    ox = -sx.min() * scale + 40
    oy = size[1] - 60 + sy.min() * scale
    P = np.stack([ox + sx * scale, oy - sy * scale], -1)
    light = np.array([-0.5, 0.6, 0.62]); light /= np.linalg.norm(light)
    im = Image.new("RGB", size, (28, 32, 40))
    d = ImageDraw.Draw(im)
    quads = []
    for j in range(n - 1):
        for i in range(n - 1):
            zc = V[j:j + 2, i:i + 2].mean()
            dx = (V[j, i + 1] + V[j + 1, i + 1] - V[j, i] - V[j + 1, i]) / (2 * tc.MESH_STEP)
            dy = (V[j, i] + V[j, i + 1] - V[j + 1, i] - V[j + 1, i + 1]) / (2 * tc.MESH_STEP)  # +y north
            nrm = np.array([-dx * zex, -dy * zex, 1.0]); nrm /= np.linalg.norm(nrm)
            lam = max(0.0, float(nrm @ light))
            water = lake_v[j:j + 2, i:i + 2].all()
            col = (np.array([70, 120, 190]) if water else tint(np.array([zc]))[0]) * (0.4 + 0.7 * lam)
            depth = (i + 0.5) * tc.MESH_STEP * u[0] + (tc.MAP_SIZE - (j + 0.5) * tc.MESH_STEP) * u[1]
            quads.append((depth, [tuple(P[j, i]), tuple(P[j, i + 1]), tuple(P[j + 1, i + 1]), tuple(P[j + 1, i])],
                          tuple(int(c) for c in np.clip(col, 0, 255))))
    quads.sort(key=lambda q: -q[0])
    for _, poly, col in quads:
        d.polygon(poly, fill=col, outline=col)
    d.text((16, 14), f"Blockout, oblique view from the south-south-west (heights x{zex}); 25 m mesh, lakes flat",
           fill=(235, 235, 235), font=font(22))
    im.save(path)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma", type=float, default=15.0, help="Gaussian sigma in metres")
    ap.add_argument("--open-radius", type=int, default=4, help="lake/river split radius in 5 m pixels")
    args = ap.parse_args()
    inp, out, prev = (os.path.join(HERE, d) for d in ("inputs", "outputs", "previews"))
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    meta = json.load(open(os.path.join(inp, "valley_heightmap_meta.json")))
    raw = np.array(Image.open(os.path.join(inp, "valley_heightmap_16bit.png")))
    assert raw.dtype == np.uint16 and raw.shape == (meta["height_samples"], meta["width_samples"]), raw.dtype
    assert meta["width_samples"] * meta["metres_per_sample"] == meta["map_size_m"] == tc.MAP_SIZE
    h = tc.u16_to_metres(raw, meta)

    # ---- lakes
    lk = tc.find_lakes(h, args.open_radius)
    level = lk["level"]
    px_area = tc.SRC_STEP ** 2
    names = ["West Lake", "East Lake"]
    assert len(lk["lakes"]) == 2, f"expected 2 lakes, found {len(lk['lakes'])}"
    lakes = []
    for nm, m in zip(names, lk["lakes"]):
        ys, xs = np.nonzero(m)
        lakes.append({"name": nm, "water_level_m": level, "area_m2": float(m.sum() * px_area),
                      "area_ha": float(m.sum() * px_area / 1e4),
                      "centroid_xy_m": [float((xs.mean() + .5) * 5), float((ys.mean() + .5) * 5)],
                      "bbox_xy_m": [int(xs.min() * 5), int(ys.min() * 5), int((xs.max() + 1) * 5), int((ys.max() + 1) * 5)]})
    river_px = int(lk["river"].sum())
    poly = json.load(open(os.path.join(inp, "valley_map_polygons.json")))
    poly_area = shoelace(poly["water_outer_incl_river"]) - shoelace(poly["water_island_hole"])
    body_area = float(lk["body"].sum() * px_area)
    # land pixels at the level that are flat-but-not-water would show up here; the island is the only hole
    water_report = {"level_m": level, "lakes": lakes, "river_and_shore_px": river_px,
                    "river_and_shore_m2": float(river_px * px_area), "water_body_m2": body_area,
                    "valley_map_polygon_m2": float(poly_area),
                    "other_flat_patches_note": "flat patches at 1.2, 2.8 and 2.9 m exist (meadows/town flats); not water"}

    # ---- blockout mesh
    V, lake_v, smooth = tc.build_blockout(h, lk["union"], level, args.sigma)
    np.save(os.path.join(out, "blockout_vertices_101x101_m.npy"), V.astype(np.float32))
    np.savetxt(os.path.join(out, "blockout_vertices_101x101_m.csv"), V, fmt="%.3f", delimiter=",")

    # ---- bake
    hmin, hmax = 0.0, float(meta["max_m"])          # fixed to the source scale so PNG and EXR match the JSON mapping
    n_exr, z_exr = tc.bake_raster(V, lk["union"], level, EXR_N, hmin, hmax)
    n_png, z_png = tc.bake_raster(V, lk["union"], level, PNG_N, hmin, hmax)
    exr_path = os.path.join(out, "valley_blockout_height_2048.exr")
    png_path = os.path.join(out, "valley_blockout_height_2017_16bit.png")
    tc.write_exr_rgb_f32(exr_path, np.repeat(n_exr[..., None], 3, axis=2))
    back = tc.read_exr_rgb_f32(exr_path)
    assert np.array_equal(back[..., 0], n_exr) and np.array_equal(back[..., 2], n_exr)
    u16 = np.clip(np.round(n_png * 65535.0), 0, 65535).astype(np.uint16)
    Image.fromarray(u16).save(png_path)
    chk = np.array(Image.open(png_path))
    assert chk.dtype == np.uint16 and chk.shape == (PNG_N, PNG_N) and np.array_equal(chk, u16)

    bake_meta = tc.make_bake_meta(
        hmin, hmax, level, (z_png.min(), z_png.max()), args.sigma,
        os.path.basename(exr_path), os.path.basename(png_path), EXR_N, PNG_N,
        produced_by="run_pipeline.py (numpy). NOT a Blender render; see REPORT.md")
    json.dump(bake_meta, open(os.path.join(out, "bake_meta.json"), "w"), indent=2)

    # ---- checks
    rows = []
    for name, x, y, exp in CHECKS:
        c, r = int(x // 5), int(y // 5)
        row = {"name": name, "x": x, "y": y, "expected_m": exp,
               "source_m": float(h[r, c]),
               "blockout_m": float(tc.surface_at(V, np.array(float(x)), np.array(float(y)), lk["union"], level)),
               "exr_m": tc.sample_bake(back[..., 0], x, y, hmin, hmax),
               "png_m": tc.sample_bake(chk.astype(np.float32) / 65535.0, x, y, hmin, hmax)}
        row["diff_exr_m"] = row["exr_m"] - exp
        row["diff_png_m"] = row["png_m"] - exp
        row["pass"] = abs(row["diff_exr_m"]) < 3 and abs(row["diff_png_m"]) < 3
        rows.append(row)

    # ---- smoothing quality / playable area
    land = ~lk["union"]
    err = z_exr[::4, ::4] - tc.bilinear(h, (np.arange(0, EXR_N, 4) + .5) * tc.MAP_SIZE / EXR_N / 5 - .5,
                                         (np.arange(0, EXR_N, 4) + .5)[:, None] * tc.MAP_SIZE / EXR_N / 5 - .5)
    pm = Image.new("L", (500, 500), 0)
    ImageDraw.Draw(pm).polygon([(px / 5, py / 5) for px, py in poly["playable_edge"]], fill=1)
    pm = np.array(pm).astype(bool)
    stats = {"source_min_m": float(h.min()), "source_max_m": float(h.max()),
             "playable_area_max_source_m": float(h[pm].max()), "playable_area_max_smoothed_m": float(smooth[pm].max()),
             "playable_area_km2": float(pm.sum() * 25 / 1e6),
             "blockout_min_m": float(V.min()), "blockout_max_m": float(V.max()),
             "bake_vs_source_rms_m": float(np.sqrt(np.mean(err ** 2))), "bake_vs_source_p95_abs_m": float(np.percentile(np.abs(err), 95)),
             "bake_vs_source_max_abs_m": float(np.abs(err).max()),
             "lake_vertices": int(lake_v.sum()), "mesh_vertices": int(V.size)}
    results = {"water": water_report, "bake_meta": bake_meta, "checks": rows, "stats": stats}
    json.dump(results, open(os.path.join(out, "pipeline_results.json"), "w"), indent=2)

    # ---- previews
    W = 1500
    px = (np.arange(W) + .5) * tc.MAP_SIZE / W
    gx, gy = np.meshgrid(px, px)
    surf = tc.surface_at(V, gx, gy, lk["union"], level)
    big = Image.fromarray(shade_map(surf, tc.MAP_SIZE / W, lake=surf <= level + 1e-6)).convert("RGB")
    draw_grid(big)
    draw_points(big, rows)
    banner = Image.new("RGB", (W, 44), (20, 20, 20))
    ImageDraw.Draw(banner).text((14, 10), "Blockout, top down: 100 m grid A-Y x 1-25 (row 1 = north), lakes blue, checkpoints red",
                                fill=(235, 235, 235), font=font(22))
    framed = Image.new("RGB", (W, W + 44))
    framed.paste(banner, (0, 0))
    framed.paste(big, (0, 44))
    big = framed
    big.save(os.path.join(prev, "01_topdown_grid_checkpoints.png"))

    half = 900
    xs = (np.arange(half) + .5) * tc.MAP_SIZE / half
    xx, yy = np.meshgrid(xs, xs)
    orig = shade_map(tc.bilinear(h, xx / 5 - .5, yy / 5 - .5), tc.MAP_SIZE / half)
    blk = tc.surface_at(V, xx, yy, lk["union"], level)
    blk_img = shade_map(blk, tc.MAP_SIZE / half, lake=blk <= level + 1e-6)
    sbs = Image.new("RGB", (half * 2 + 10, half + 40), (20, 20, 20))
    sbs.paste(Image.fromarray(orig), (0, 40))
    sbs.paste(Image.fromarray(blk_img), (half + 10, 40))
    d = ImageDraw.Draw(sbs)
    d.text((10, 8), "Original 5 m heightmap (reference)", fill=(235, 235, 235), font=font(22))
    d.text((half + 20, 8), f"Blockout: 25 m mesh, sigma {args.sigma:g} m, flat lakes", fill=(235, 235, 235), font=font(22))
    sbs.save(os.path.join(prev, "02_original_vs_blockout.png"))

    oblique(V, lake_v, os.path.join(prev, "03_oblique.png"))
    Image.fromarray((np.clip(n_exr, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024)).save(
        os.path.join(prev, "04_bake_preview_8bit.png"))

    print(json.dumps({"water": water_report, "checks": rows, "stats": stats}, indent=2))


if __name__ == "__main__":
    main()
