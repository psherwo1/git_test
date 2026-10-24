import sys, glob, os, bpy, numpy as np
d = sys.argv[-1]
def red(f):
    img = bpy.data.images.load(f); w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4); bpy.data.images.remove(img)
    return (px[..., 0] > 0.5) & (px[..., 1] < 0.35) & (px[..., 2] < 0.35), h
for f in sorted(glob.glob(os.path.join(d, "c0*_red.png"))):
    a, h = red(os.path.join(d, "cull_r05", os.path.basename(f))); b, _ = red(f)
    ys, xs = np.nonzero(a ^ b)
    print(f"CULLDIFF {os.path.basename(f)} r05 red {int(a.sum())} r06 red {int(b.sum())} differing px {len(xs)}",
          [(int(x), int(h - 1 - y)) for y, x in list(zip(ys, xs))[:8]])
