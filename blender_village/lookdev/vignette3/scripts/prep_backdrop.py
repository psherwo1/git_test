"""Crop the mountain/arch bands out of the two concept-art references (PLACEHOLDER backdrop) with a soft alpha fade at the
bottom (and a short fade on the sides) so the card blends into water/haze.  bpy + numpy only (no PIL in the venv).
python.exe -I prep_backdrop.py
"""
import os
import bpy
import numpy as np

REF = r"C:\GitHubDesktop\git_test\blender_village\lookdev\vignette2\ref"


def crop(src, dst, x1, y1, fade_bottom=0.30):
    im = bpy.data.images.load(os.path.join(REF, src))
    w, h = im.size
    a = np.empty(w * h * im.channels, dtype=np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, im.channels)[:, :, :3]
    a = a[::-1]                      # now top-down
    c = a[:y1, :x1].copy()
    ch, cw = c.shape[:2]
    # lift the bottom towards a pale haze colour before it fades out
    haze = np.array([0.62, 0.70, 0.74], dtype=np.float32)
    ys = np.linspace(0, 1, ch)[:, None]
    k = np.clip((ys - (1 - fade_bottom - 0.1)) / (fade_bottom + 0.1), 0, 1) ** 1.5 * 0.55
    c = c * (1 - k[..., None]) + haze * k[..., None]
    alpha = 1.0 - np.clip((ys - (1 - fade_bottom)) / fade_bottom, 0, 1) ** 1.3
    alpha = np.repeat(alpha, cw, axis=1)
    out = np.dstack([c, alpha])[::-1]      # back to bottom-up for bpy
    o = bpy.data.images.new(dst, cw, ch, alpha=True, float_buffer=False)
    o.colorspace_settings.name = "sRGB"
    o.pixels.foreach_set(np.ascontiguousarray(out, dtype=np.float32).ravel())
    o.filepath_raw = os.path.join(REF, dst)
    o.file_format = "PNG"
    o.save()
    print("SAVED", dst, cw, ch)


crop("ref_street.jpg", "backdrop_street.png", 985, 352)
crop("ref_aerial.jpg", "backdrop_aerial.png", 940, 292)
