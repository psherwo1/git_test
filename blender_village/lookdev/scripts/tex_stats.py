"""Read-only: mean / percentiles of the linear colour of texture images (image files only).
Usage: python.exe -I tex_stats.py <img> [<img> ...]"""
import sys

import bpy
import numpy as np

for p in sys.argv[1:]:
    im = bpy.data.images.load(p, check_existing=False)
    im.colorspace_settings.name = "sRGB"
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(-1, 4)[:, :3]
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    print(p.split("\\")[-1], "mean", np.round(a.mean(0), 3), "lum p50 %.3f p95 %.3f p99 %.3f" % tuple(np.percentile(lum, [50, 95, 99])))
    bpy.data.images.remove(im)
