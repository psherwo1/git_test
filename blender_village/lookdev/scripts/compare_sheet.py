"""Before / after sheets and crop measurements for the look tests (Blender as a Python module, no PIL).

Usage:
    python.exe -I compare_sheet.py sheet <before.png> <after.png> <out.jpg> [--width 960]
        left = before, right = after, each scaled to --width, with a 6 px gap.
    python.exe -I compare_sheet.py measure <img.png> x0 y0 x1 y1 [<img2.png> ...]
        mean display value (0-1, the PNG's own encoding) and mean Rec.709 luma inside the pixel rectangle
        (x right, y DOWN from the top-left, in full-resolution pixels), for each image.
"""
import sys

import bpy
import numpy as np


def load(path):
    im = bpy.data.images.load(path, check_existing=False)
    im.colorspace_settings.name = "Non-Color"  # keep the PNG's display-encoded values as they are
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1]  # top row first


def resize(a, width):
    h, w = a.shape[:2]
    nh = int(round(h * width / w))
    ys = (np.arange(nh) + 0.5) * h / nh
    xs = (np.arange(width) + 0.5) * w / width
    # box filter by averaging the source block around each target pixel
    fy, fx = max(1, int(h / nh)), max(1, int(w / width))
    out = np.zeros((nh, width, 4), np.float32)
    for dy in range(fy):
        for dx in range(fx):
            yy = np.clip((ys - fy / 2 + dy + 0.5).astype(int), 0, h - 1)
            xx = np.clip((xs - fx / 2 + dx + 0.5).astype(int), 0, w - 1)
            out += a[yy][:, xx]
    return out / (fy * fx)


def save(a, path):
    h, w = a.shape[:2]
    im = bpy.data.images.new("sheet", w, h, alpha=False)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(np.ascontiguousarray(a[::-1]).ravel())
    im.filepath_raw = path
    im.file_format = "JPEG"
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    im.save_render(path, scene=scene)


def main(argv):
    if argv[0] == "sheet":
        b, a, out = argv[1], argv[2], argv[3]
        width = int(argv[argv.index("--width") + 1]) if "--width" in argv else 960
        B, A = resize(load(b), width), resize(load(a), width)
        h = max(B.shape[0], A.shape[0])
        sheet = np.ones((h, width * 2 + 6, 4), np.float32)
        sheet[:B.shape[0], :width] = B
        sheet[:A.shape[0], width + 6:] = A
        sheet[..., 3] = 1.0
        save(sheet, out)
        print("SHEET", out)
    elif argv[0] == "measure":
        x0, y0, x1, y1 = map(int, argv[2:6])
        for p in [argv[1]] + argv[6:]:
            a = load(p)[y0:y1, x0:x1, :3]
            luma = a @ np.array([0.2126, 0.7152, 0.0722])
            print("MEASURE %s mean_rgb %s luma %.4f sd %.4f p95 %.4f p99 %.4f" % (
                p, np.round(a.reshape(-1, 3).mean(0), 4), luma.mean(), luma.std(), np.percentile(luma, 95),
                np.percentile(luma, 99)))


if __name__ == "__main__":
    main(sys.argv[1:])
