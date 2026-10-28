"""Numpy-only core for the valley blockout.

Used by run_pipeline.py (standalone) and by blender_build.py (inside Blender,
whose bundled Python has numpy but not PIL or scipy). Nothing here imports bpy.

Conventions (one place, so the Blender script and the standalone pipeline agree):
  * Source raster: row r, column c  ->  map x = (c + 0.5) * 5 m, map y = (r + 0.5) * 5 m.
    Row 0 is the top (north); +y runs down the image (south). No flip, no transpose.
  * Blender world: X = map x, Y = MAP_SIZE - map y, Z = height. With that choice a
    top-down orthographic camera sees map y = 0 at the top of the render.
  * Mesh: 101 x 101 vertices at 25 m spacing. V[j, i] is the vertex at map x = 25 i,
    map y = 25 j (j = 0 is the north edge).
"""
import re
import struct

import numpy as np

MAP_SIZE = 2500.0
SRC_STEP = 5.0
MESH_STEP = 25.0
GRID_CELL = 100.0


# --------------------------------------------------------------------------- meta / input
def parse_scale(meta):
    """Pixel -> metres scale from the JSON. Cross-checks the formula string."""
    scale = float(meta["max_m"])
    m = re.search(r"/\s*65535\s*\*\s*([0-9.]+)", meta.get("pixel_to_metres", ""))
    if m and abs(float(m.group(1)) - scale) > 1e-9:
        raise ValueError("pixel_to_metres formula and max_m disagree")
    return scale


def u16_to_metres(a, meta):
    return a.astype(np.float64) / 65535.0 * parse_scale(meta)


# --------------------------------------------------------------------------- filtering
def gaussian_kernel(sigma_px):
    r = int(np.ceil(4.0 * sigma_px))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-0.5 * (x / sigma_px) ** 2)
    return k / k.sum()


def _conv_axis(a, k, axis):
    r = (len(k) - 1) // 2
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r, r)
    p = np.pad(a, pad, mode="reflect")
    out = np.zeros_like(a, dtype=np.float64)
    n = a.shape[axis]
    for i, w in enumerate(k):
        out += w * (p[i:i + n, :] if axis == 0 else p[:, i:i + n])
    return out


def gaussian_blur(a, sigma_px):
    k = gaussian_kernel(sigma_px)
    return _conv_axis(_conv_axis(a.astype(np.float64), k, 0), k, 1)


def masked_gaussian_blur(a, keep, sigma_px):
    """Blur using only pixels where keep is True (normalised convolution).

    Land is blurred without lake pixels, so the shoreline is not dragged down
    to the water level and the lake does not get pulled up by the bank.
    Pixels with keep == False get the nearest-valid fallback of 0 weight and
    must be overwritten by the caller.
    """
    w = keep.astype(np.float64)
    num = gaussian_blur(a * w, sigma_px)
    den = gaussian_blur(w, sigma_px)
    return np.where(den > 1e-9, num / np.maximum(den, 1e-9), 0.0)


# --------------------------------------------------------------------------- morphology
def _disc(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def erode(m, r):
    k = _disc(r)
    p = np.pad(m, r, constant_values=False)
    out = np.ones_like(m, dtype=bool)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            if k[dy, dx]:
                out &= p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
    return out


def dilate(m, r):
    k = _disc(r)
    p = np.pad(m, r, constant_values=False)
    out = np.zeros_like(m, dtype=bool)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            if k[dy, dx]:
                out |= p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
    return out


def label(mask):
    """4-connected component labelling. Returns (labels, count); labels start at 1."""
    lab = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    h, w = mask.shape
    for r, c in zip(*np.nonzero(mask)):
        if lab[r, c]:
            continue
        n += 1
        lab[r, c] = n
        stack = [(r, c)]
        while stack:
            y, x = stack.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
    return lab, n


# --------------------------------------------------------------------------- lakes
def find_lakes(h, open_radius_px=4, tol_m=1e-6):
    """Lakes = the large flat regions at the lowest elevation.

    1. Water level  = the global minimum of the data, accepted only if a large
       plateau sits exactly on it (checked by the caller from the pixel count).
    2. Water body   = every pixel within tol_m of that level.
    3. Lakes        = morphological opening of the body with a disc of
       open_radius_px (20 m by default). That removes channels narrower than
       about 2 * radius, i.e. the river, and keeps the broad basins.
    Returns dict with level, body mask, lake masks (West first), river mask.
    """
    level = float(h.min())
    body = np.abs(h - level) <= tol_m
    lakes_all = dilate(erode(body, open_radius_px), open_radius_px) & body
    lab, n = label(lakes_all)
    sizes = np.bincount(lab.ravel())[1:]
    order = [i for i in np.argsort(sizes)[::-1] if sizes[i] >= 200]  # ignore specks
    comps = []
    for i in order:
        m = lab == (i + 1)
        cx = np.nonzero(m)[1].mean() * SRC_STEP
        comps.append((cx, m))
    comps.sort(key=lambda t: t[0])  # west -> east
    masks = [m for _, m in comps]
    union = np.zeros_like(body)
    for m in masks:
        union |= m
    return {"level": level, "body": body, "lakes": masks, "union": union,
            "river": body & ~union}


# --------------------------------------------------------------------------- mesh sampling
def bilinear(field, u, v):
    """Sample field at fractional pixel coords (u = column, v = row), edge-clamped."""
    h, w = field.shape
    u = np.clip(u, 0, w - 1)
    v = np.clip(v, 0, h - 1)
    u0 = np.minimum(np.floor(u).astype(int), w - 2)
    v0 = np.minimum(np.floor(v).astype(int), h - 2)
    fu, fv = u - u0, v - v0
    a = field[v0, u0] * (1 - fu) + field[v0, u0 + 1] * fu
    b = field[v0 + 1, u0] * (1 - fu) + field[v0 + 1, u0 + 1] * fu
    return a * (1 - fv) + b * fv


def build_blockout(h, lake_union, level, sigma_m=15.0):
    """Smoothed 101 x 101 vertex heights (metres) plus the lake-vertex mask.

    Land is smoothed with a lake-masked Gaussian (sigma_m), sampled at the mesh
    vertices, and every vertex whose 25 m neighbourhood is mostly lake is pinned
    to exactly the water level.
    """
    smooth = masked_gaussian_blur(h, ~lake_union, sigma_m / SRC_STEP)
    n = int(MAP_SIZE / MESH_STEP) + 1
    coords = np.arange(n) * MESH_STEP / SRC_STEP - 0.5  # pixel-centre convention
    uu, vv = np.meshgrid(coords, coords)
    V = bilinear(smooth, uu, vv)
    # lake fraction in a ~25 m footprint around each vertex
    frac = gaussian_blur(lake_union.astype(np.float64), MESH_STEP / 2 / SRC_STEP)
    lake_v = bilinear(frac, uu, vv) >= 0.5
    V = np.where(lake_v, level, V)
    return V, lake_v, smooth


def surface_at(V, x, y, lake_union=None, level=None):
    """Height of the blockout (displaced grid) at map coords, bilinear per quad.
    Where a lake plane exists the higher of terrain and plane wins, which is
    what a top-down render of terrain + lake plane would show."""
    z = bilinear(V, x / MESH_STEP, y / MESH_STEP)
    if lake_union is not None:
        c = np.clip((x / SRC_STEP).astype(int), 0, lake_union.shape[1] - 1)
        r = np.clip((y / SRC_STEP).astype(int), 0, lake_union.shape[0] - 1)
        z = np.where(lake_union[r, c], np.maximum(z, level), z)
    return z


def bake_raster(V, lake_union, level, n, hmin, hmax):
    """Normalised (0..1) height raster as an orthographic camera would see it:
    n x n pixels over exactly MAP_SIZE, pixel centres at (i + 0.5) * MAP_SIZE / n,
    row 0 = map y 0 (north)."""
    px = (np.arange(n) + 0.5) * MAP_SIZE / n
    x, y = np.meshgrid(px, px)
    z = surface_at(V, x, y, lake_union, level)
    return ((z - hmin) / (hmax - hmin)).astype(np.float32), z


def sample_bake(norm, x_m, y_m, hmin, hmax):
    n = norm.shape[0]
    c = min(int(x_m / MAP_SIZE * n), n - 1)
    r = min(int(y_m / MAP_SIZE * n), n - 1)
    return float(norm[r, c]) * (hmax - hmin) + hmin


# --------------------------------------------------------------------------- lake mesh
def lake_plane_mesh(mask, level):
    """Flat quad mesh covering the True cells of a 5 m mask, in Blender world
    coords (X = map x, Y = MAP_SIZE - map y). Returns (verts, faces)."""
    h, w = mask.shape
    rows, cols = np.nonzero(mask)
    vid = -np.ones((h + 1, w + 1), dtype=np.int64)
    for dr, dc in ((0, 0), (0, 1), (1, 1), (1, 0)):  # CCW seen from +Z
        vid[rows + dr, cols + dc] = 0
    used = np.argwhere(vid == 0)
    vid[vid == 0] = np.arange(len(used))
    verts = [(c * SRC_STEP, MAP_SIZE - r * SRC_STEP, level) for r, c in used]
    faces = []
    for r, c in zip(rows, cols):
        # map y grows downward, Blender Y grows upward, so reverse the winding
        faces.append((int(vid[r + 1, c]), int(vid[r + 1, c + 1]),
                      int(vid[r, c + 1]), int(vid[r, c])))
    return verts, faces


def make_bake_meta(hmin, hmax, water_level, actual_range, sigma_m, exr_name, png_name,
                   exr_n=2048, png_n=2017, produced_by=""):
    return {
        "map_width_m": MAP_SIZE,
        "map_height_m": MAP_SIZE,
        "min_height_m": hmin,
        "max_height_m": hmax,
        "pixel_size_m": MAP_SIZE / png_n,
        "pixel_size_m_note": "pixel_size_m is for the %d px PNG (the UE import). The EXR value is under exports.exr." % png_n,
        "encoding": "value_normalised = (height_m - min_height_m) / (max_height_m - min_height_m); "
                    "height_m = value * (max - min) + min",
        "same_scale_as_source": "min/max equal the source heightmap scale (metres = pixel16/65535*389.0)",
        "blockout_actual_height_range_m": [float(actual_range[0]), float(actual_range[1])],
        "water_level_m": water_level,
        "orientation": "row 0 = map y 0 (north, top). Column 0 = map x 0 (west). No flip needed.",
        "sampling": "pixel centres at (i + 0.5) * map_width_m / pixels",
        "exports": {
            "exr": {"file": exr_name, "pixels": exr_n, "bit_depth": 32, "channels": "RGB (R=G=B)",
                    "pixel_size_m": MAP_SIZE / exr_n, "colour_space": "linear / Non-Color, no view transform"},
            "png": {"file": png_name, "pixels": png_n, "bit_depth": 16, "channels": "grayscale",
                    "pixel_size_m": MAP_SIZE / png_n,
                    "vertex_spacing_if_corner_aligned_m": MAP_SIZE / (png_n - 1),
                    "vertex_spacing_note": "if imported as a %d-vertex landscape (%d quads) spanning the full map, "
                                           "spacing is map_width/%d" % (png_n, png_n - 1, png_n - 1)},
        },
        "smoothing": {"method": "lake-masked Gaussian, then bilinear sample at 25 m mesh vertices",
                      "sigma_m": sigma_m, "mesh_spacing_m": MESH_STEP},
        "produced_by": produced_by,
    }


def col_letter(i):
    return chr(ord("A") + i)


# --------------------------------------------------------------------------- EXR writer
def write_exr_rgb_f32(path, rgb):
    """Uncompressed, scanline, 32-bit float OpenEXR, channels B, G, R.
    rgb: float32 array (H, W, 3). No dependencies; format per the OpenEXR file layout doc."""
    hgt, wid, _ = rgb.shape

    def attr(name, typ, payload):
        return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<i", len(payload)) + payload

    chans = b""
    for nm in ("B", "G", "R"):  # must be alphabetical
        chans += nm.encode() + b"\0" + struct.pack("<i", 2) + bytes([0, 0, 0, 0]) + struct.pack("<ii", 1, 1)
    chans += b"\0"
    box = struct.pack("<iiii", 0, 0, wid - 1, hgt - 1)
    header = b"".join([
        attr("channels", "chlist", chans),
        attr("compression", "compression", bytes([0])),          # NO_COMPRESSION
        attr("dataWindow", "box2i", box),
        attr("displayWindow", "box2i", box),
        attr("lineOrder", "lineOrder", bytes([0])),              # INCREASING_Y
        attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<ff", 0.0, 0.0)),
        attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
    ]) + b"\0"
    pre = bytes([0x76, 0x2F, 0x31, 0x01]) + struct.pack("<i", 2)
    line_bytes = wid * 4 * 3
    block = 4 + 4 + line_bytes
    start = len(pre) + len(header) + 8 * hgt
    offsets = b"".join(struct.pack("<Q", start + y * block) for y in range(hgt))
    out = bytearray(pre + header + offsets)
    data = rgb.astype("<f4")
    for y in range(hgt):
        out += struct.pack("<ii", y, line_bytes)
        for ch in (2, 1, 0):  # B, G, R
            out += data[y, :, ch].tobytes()
    with open(path, "wb") as f:
        f.write(out)


def read_exr_rgb_f32(path):
    """Reader for the exact layout write_exr_rgb_f32 produces (round-trip test only)."""
    b = open(path, "rb").read()
    assert b[:4] == bytes([0x76, 0x2F, 0x31, 0x01])
    p = 8
    dw = None
    while b[p] != 0:
        e = b.index(b"\0", p)
        name = b[p:e].decode()
        p = e + 1
        e = b.index(b"\0", p)
        p = e + 1
        (size,) = struct.unpack_from("<i", b, p)
        p += 4
        if name == "dataWindow":
            dw = struct.unpack_from("<iiii", b, p)
        p += size
    p += 1
    wid, hgt = dw[2] + 1, dw[3] + 1
    p += 8 * hgt
    img = np.zeros((hgt, wid, 3), dtype=np.float32)
    for y in range(hgt):
        yy, sz = struct.unpack_from("<ii", b, p)
        p += 8
        assert yy == y
        for ch in (2, 1, 0):
            img[y, :, ch] = np.frombuffer(b, dtype="<f4", count=wid, offset=p)
            p += wid * 4
    return img
