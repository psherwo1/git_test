import sys, os, bpy, numpy as np
from collections import deque
d = sys.argv[-1]
for n in ("x24_W_eave_lookup_red.png", "f04_roll_down_slope_from_ridge_side_red.png", "e04_brow_oblique_from_S_red.png"):
    img = bpy.data.images.load(os.path.join(d, n)); w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # row 0 = top
    red = (px[..., 0] > 0.5) & (px[..., 1] < 0.35) & (px[..., 2] < 0.35)
    lab = np.zeros((h, w), int); k = 0; out = []
    for y0 in range(h):
        for x0 in range(w):
            if red[y0, x0] and not lab[y0, x0]:
                k += 1; q = deque([(y0, x0)]); lab[y0, x0] = k; pts = []; border = False
                while q:
                    y, x = q.popleft(); pts.append((y, x))
                    if y in (0, h - 1) or x in (0, w - 1): border = True
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        yy, xx = y+dy, x+dx
                        if 0 <= yy < h and 0 <= xx < w and red[yy, xx] and not lab[yy, xx]:
                            lab[yy, xx] = k; q.append((yy, xx))
                if not border:
                    ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
                    out.append((len(pts), min(xs), max(xs), min(ys), max(ys)))
    print("CLUSTERS", n, len(out), sorted(out, reverse=True)[:12], flush=True)
