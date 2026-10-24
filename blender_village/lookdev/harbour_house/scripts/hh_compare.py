"""Side-by-side compare sheets r05 | r06 (left = round 5 accepted, right = round 6) for every shot PNG in r05.
python.exe -I hh_compare.py <r05_dir> <r06_dir> <out_dir> [scale]
Each render is scaled by `scale` (default 0.75), 12 px white gap, label bar drawn as blocks (r05 one bar, r06 two)."""
import os
import sys

import bpy
import numpy as np

A, B, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SC = float(sys.argv[4]) if len(sys.argv) > 4 else 0.75
os.makedirs(OUT, exist_ok=True)


def load(p):
    im = bpy.data.images.load(p, check_existing=False)
    im.colorspace_settings.name = "Non-Color"
    w, h = im.size
    im.scale(int(w * SC), int(h * SC))
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)


def mark(a, n):
    # n small white bars with black outline at the top-left: 1 = r05, 2 = r06 (image rows are bottom-up)
    h = a.shape[0]
    for i in range(n):
        x0 = 16 + i * 30
        a[h - 46:h - 14, x0 - 2:x0 + 20, :3] = 0.0
        a[h - 44:h - 16, x0:x0 + 18, :3] = 1.0


for f in sorted(os.listdir(A)):
    if not f.endswith(".png") or not os.path.exists(os.path.join(B, f)):
        continue
    a, b = load(os.path.join(A, f)), load(os.path.join(B, f))
    mark(a, 1)
    mark(b, 2)
    h, w = a.shape[:2]
    gap = 12
    sheet = np.ones((h, w * 2 + gap, 4), np.float32)
    sheet[:, :w] = a
    sheet[:, w + gap:] = b
    sheet[..., 3] = 1.0
    out = bpy.data.images.new("sheet", sheet.shape[1], h, alpha=False)
    out.colorspace_settings.name = "Non-Color"
    out.pixels.foreach_set(np.ascontiguousarray(sheet).ravel())
    dst = os.path.join(OUT, f.replace(".png", "_r05_vs_r06.jpg"))
    out.filepath_raw = dst
    out.file_format = "JPEG"
    scn = bpy.context.scene
    scn.render.image_settings.quality = 90
    out.save()
    bpy.data.images.remove(out)
    print("SHEET", dst)
