"""Count enclosed red pixels in the *_red.png twins: red pixels NOT 4-connected to the image border (i.e. holes seen
through the building, not open sky).  python -I dir_redcount_r04.py <dir>"""
import glob
import os
import sys

import bpy  # noqa: F401  (image loading)
import numpy as np
from collections import deque

d = sys.argv[-1]
for f in sorted(glob.glob(os.path.join(d, "*_red.png"))):
    img = bpy.data.images.load(f)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    red = (px[..., 0] > 0.5) & (px[..., 1] < 0.35) & (px[..., 2] < 0.35)
    seen = np.zeros_like(red)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if red[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if red[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and red[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True; q.append((yy, xx))
    enc = red & ~seen
    ys, xs = np.nonzero(enc)
    box = f"x {xs.min()}-{xs.max()} y(from top) {h - 1 - ys.max()}-{h - 1 - ys.min()}" if len(xs) else ""
    print(f"RED {os.path.basename(f):48s} total {int(red.sum()):7d} enclosed {int(enc.sum()):5d} {box}", flush=True)
    bpy.data.images.remove(img)
