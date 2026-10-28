"""Crop a pixel rectangle (x right, y down, full-res pixels) out of a PNG and save it, for close inspection.
python.exe -I jt_crop.py <in.png> <out.png> x0 y0 x1 y1"""
import sys

import bpy
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7])
im = bpy.data.images.load(src, check_existing=False)
im.colorspace_settings.name = "Non-Color"
w, h = im.size
a = np.empty(w * h * 4, np.float32)
im.pixels.foreach_get(a)
a = a.reshape(h, w, 4)[::-1][y0:y1, x0:x1].copy()
a[..., 3] = 1.0
oh, ow = a.shape[:2]
out = bpy.data.images.new("crop", ow, oh, alpha=False)
out.colorspace_settings.name = "Non-Color"
out.pixels.foreach_set(np.ascontiguousarray(a[::-1]).ravel())
out.filepath_raw = dst
out.file_format = "PNG"
out.save()
print("CROP", dst, ow, oh)
