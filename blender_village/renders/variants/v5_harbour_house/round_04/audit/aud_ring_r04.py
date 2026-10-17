"""Auditor round-4 see-through ring for v5_harbour_house (read-only).  python -I aud_ring_r04.py -- <blend> <out_dir>
Renders a black-override / red-world twin from 16 eye-level (z 1.7) and 16 crane (z 6.0) cameras around the building,
finds red pixels NOT connected to the image border (seen THROUGH the building) and sizes each enclosed patch in
world units from the depth of its rim (BVH ray casts).  Also re-measures door clearance above the thresholds."""
import math
import os
import sys
from collections import deque

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off = [], [], [], 0
for i, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", co)
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co.reshape(-1, 3)); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(tv) // 3, i))
    off += len(m.vertices); o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)

# ---- door clearance, rays started above the threshold -----------------------------------------------------------
for nm, (dx, dy) in {"hall land door": (2.992, -5.773), "wing S door": (-5.908, -7.673)}.items():
    res = []
    for outd in np.arange(0.05, 1.21, 0.05):
        zmin, who = 99.0, None
        for ox in np.linspace(-0.55, 0.55, 12):
            h = bvh.ray_cast(Vector((dx + ox, dy - outd, 0.35)), Vector((0, 0, 1)), 30.0)
            if h[0] is not None and h[0].z < zmin:
                zmin, who = h[0].z, objs[OWN[h[2]]].name
        res.append(f"{outd:.2f}:{zmin:.3f}({who})" if who else f"{outd:.2f}:open")
    print("DOOR", nm, " | ".join(res), flush=True)

# ---- render set-up ------------------------------------------------------------------------------------------------
black = bpy.data.materials.new("_AUD_black"); black.use_nodes = True
bsdf = black.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1); bsdf.inputs["Specular IOR Level"].default_value = 0.0
scn.view_layers[0].material_override = black
for o in bpy.data.objects:
    if o.type == "LIGHT":
        o.hide_render = True
world = bpy.data.worlds.new("_AUD_world"); world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (1, 0, 0, 1)
bg.inputs["Strength"].default_value = 1.0; scn.world = world
scn.render.engine = "CYCLES"; scn.cycles.device = "CPU"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    if any(d.use for d in prefs.devices):
        scn.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device, flush=True)
W, H = 2560, 1440
scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = W, H, 100
scn.cycles.samples = 4; scn.cycles.use_denoising = False
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "Standard"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02
cam.data.lens = 24.0

C = Vector((0.6, -1.5, 0.0))
SHOTS = []
for k in range(16):
    a = math.radians(22.5 * k + 5.0)
    SHOTS.append((f"g{k:02d}", (C.x + 13.0 * math.cos(a), C.y + 13.0 * math.sin(a), 1.7), (C.x, C.y, 3.2)))
    SHOTS.append((f"c{k:02d}", (C.x + 11.0 * math.cos(a), C.y + 11.0 * math.sin(a), 6.0), (C.x, C.y, 4.0)))


def comps(mask):
    h, w = mask.shape; seen = np.zeros_like(mask); res = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; pts = []
        while q:
            y, x = q.popleft(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
        res.append(np.array(pts))
    return res


grand = 0
for name, loc, tgt in SHOTS:
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    f = os.path.join(out, name + "_red.png"); scn.render.filepath = f
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(f)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1]   # row 0 = top
    bpy.data.images.remove(img)
    red = (px[..., 0] > 0.5) & (px[..., 1] < 0.35) & (px[..., 2] < 0.35)
    seen = np.zeros_like(red); q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if red[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if red[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and red[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True; q.append((yy, xx))
    enc = red & ~seen
    fr = cam.data.view_frame(scene=scn)            # tr, br, bl, tl (camera local)
    tr, br, bl, tl = fr[0], fr[1], fr[2], fr[3]
    R = cam.matrix_world.to_3x3()
    pxw = (tr.x - tl.x) / abs(tl.z) / W          # metres per pixel per metre of depth

    def ray(u, v):
        d = tl + (tr - tl) * ((u + 0.5) / W) + (bl - tl) * ((v + 0.5) / H)
        return (R @ d).normalized()
    cl = comps(enc)
    rows = []
    for c in cl:
        y0, x0 = c.min(0); y1, x1 = c.max(0)
        # rim pixels: one pixel outside the bbox corners / mid-edges
        depths, pts = [], []
        for (u, v) in ((x0 - 2, (y0 + y1) // 2), (x1 + 2, (y0 + y1) // 2), ((x0 + x1) // 2, y0 - 2),
                       ((x0 + x1) // 2, y1 + 2)):
            h = bvh.ray_cast(cam.location, ray(u, v), 200.0)
            if h[0] is not None:
                depths.append(h[3]); pts.append(h[0])
        dd = float(np.median(depths)) if depths else 10.0
        ext = max(x1 - x0 + 1, y1 - y0 + 1) * pxw * dd
        wid = min(x1 - x0 + 1, y1 - y0 + 1) * pxw * dd
        P = sum(pts, Vector()) / len(pts) if pts else Vector()
        who = set()
        for (u, v) in ((x0 - 2, (y0 + y1) // 2), (x1 + 2, (y0 + y1) // 2)):
            h = bvh.ray_cast(cam.location, ray(u, v), 200.0)
            if h[0] is not None:
                who.add(objs[OWN[h[2]]].name)
        rows.append((len(c), ext, wid, (x0, y0, x1, y1), P, dd, sorted(who)))
    rows.sort(key=lambda r: -r[0])
    big = [r for r in rows if r[2] >= 0.02]
    grand += int(enc.sum())
    print(f"SHOT {name} loc {tuple(round(v, 1) for v in loc)} enclosed px {int(enc.sum())} patches {len(rows)} "
          f"patches >=2 cm wide {len(big)}", flush=True)
    for r in rows[:12]:
        print(f"   px {r[0]:6d} extent {r[1]*100:6.1f} cm  width {r[2]*100:5.1f} cm  bbox {r[3]}  depth {r[5]:.1f} m  "
              f"at ({r[4].x:.2f},{r[4].y:.2f},{r[4].z:.2f})  rim {r[6]}", flush=True)
print("TOTAL enclosed px", grand)
print("DONE")
