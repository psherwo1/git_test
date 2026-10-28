"""Compose the per-building thumbnails (T*_SW_*.png top row, T*_SE_*.png bottom row) into one montage.
blender -b --python dir_montage_r02.py -- <dir> <out.png>"""
import glob
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
d, outp = argv[0], argv[1]
rows = []
for tag in ("SW", "SE"):
    fs = sorted(glob.glob(os.path.join(d, f"T[0-9]_{tag}_*.png")))
    ims = []
    for f in fs:
        im = bpy.data.images.load(f)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        ims.append(a)
        print("TILE", os.path.basename(f), w, h)
    pad = np.ones((ims[0].shape[0], 6, 4), np.float32)
    row = []
    for a in ims:
        row += [a, pad]
    rows.append(np.concatenate(row[:-1], axis=1))
hp = np.ones((6, rows[0].shape[1], 4), np.float32)
full = np.concatenate([rows[1], hp, rows[0]], axis=0)   # pixels are bottom-up: SW ends on top
H, W = full.shape[:2]
img = bpy.data.images.new("montage", W, H, alpha=True)
img.pixels[:] = full.ravel()
img.filepath_raw = outp; img.file_format = "PNG"; img.save()
print("MONTAGE", outp, W, H)
