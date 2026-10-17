"""Director: crop + upscale a region of an image with bpy (no PIL).  python -I dir_crop.py <src> <dst> x0 y0 x1 y1 scale
(pixel coords, origin top-left)."""
import sys
import bpy
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, sc = (int(v) for v in sys.argv[3:8])
im = bpy.data.images.load(src)
W, H = im.size
a = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1]
c = a[y0:y1, x0:x1]
c = np.repeat(np.repeat(c, sc, axis=0), sc, axis=1)
h, w = c.shape[:2]
out = bpy.data.images.new("crop", w, h, alpha=True)
out.pixels[:] = c[::-1].ravel()
out.filepath_raw = dst
out.file_format = "PNG"
out.save()
print("saved", dst, w, h)
