import sys, bpy, numpy as np
from collections import deque
f = sys.argv[-1]
img = bpy.data.images.load(f); w, h = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
red = (px[..., 0] > 0.5) & (px[..., 1] < 0.35) & (px[..., 2] < 0.35)
seen = np.zeros_like(red); q = deque()
for x in range(w):
    for y in (0, h - 1):
        if red[y, x]: seen[y, x] = True; q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if red[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
        yy, xx = y+dy, x+dx
        if 0 <= yy < h and 0 <= xx < w and red[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; q.append((yy, xx))
ys, xs = np.nonzero(red & ~seen)
print("ENC", [(int(x), int(h-1-y)) for y, x in zip(ys, xs)])
