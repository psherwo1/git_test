"""scratch (round 5): see-through probe of the eyebrow (the wave's eave, the timber front, the deck opening).
python -I r5_brow_probe.py <blend> [shift_x shift_y]   (recentre shift of the build log; default -1.808 -5.973)
Rays are aimed from outside at a 3 cm grid over the whole front arch (from the lower roof to 15 cm over the wave's
eave, across the full wave width), from 15 directions (square-on, +-25 / +-50 deg yaw, -15 / +15 / +35 deg pitch).  A
ray LEAKS if it hits nothing or its first hit lies more than 0.70 m behind the front face (past the window's dark
room): i.e. it went through the dormer into the hall."""
import importlib.util
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[1:]
blend = argv[0]
sh = np.array([float(argv[1]), float(argv[2])]) if len(argv) > 2 else np.array([-1.808, -5.973])
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("recipe", os.path.join(HERE, "..", "build_v5_harbour_house.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
M = R.MAIN
B = M.BROWS[0]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
dg = bpy.context.evaluated_depsgraph_get()
scn = bpy.context.scene
sg = B["sg"]
d_face = B["d_t"] - B["set_back"]
y_f = sg * (M.Y - d_face)
n_out = M.dir_world(np.array([0.0, float(sg), 0.0]))
t_w = M.dir_world(np.array([1.0, 0.0, 0.0]))
dirs = []
for yaw in (0, 25, -25, 50, -50):
    for pit in (0, -15, 15, 35) if yaw == 0 else (0, 15):
        if yaw == 0 and pit == 0 and dirs:
            continue
        a, p = math.radians(yaw), math.radians(pit)
        h = -n_out * math.cos(a) + t_w * math.sin(a)
        d = np.array([h[0] * math.cos(p), h[1] * math.cos(p), math.sin(p)])
        dirs.append(((yaw, pit), d / np.linalg.norm(d)))
dirs = dirs[:15]
n_ray = n_leak = n_room = 0
hist = np.zeros(16, int)                      # first-hit depth behind the face, 0.1 m bins from -0.5 m
leaks = {}
deep = []
for x in np.arange(B["x"] - B["hw"], B["x"] + B["hw"] + 1e-6, 0.03):
    lo = M.ref_z(y_f) + float(M.warp_z(np.array([x]), np.array([y_f]), brow={0: 0.0})[0])
    hi = M.ref_z(y_f) + float(M.warp_z(np.array([x]), np.array([y_f]), brow={0: 1.0})[0]) + 0.15
    pw = M.to_world(np.array([[x, y_f]]))[0]
    for z in np.arange(lo, hi, 0.03):
        P = np.array([pw[0] + sh[0], pw[1] + sh[1], z])
        for key, d in dirs:
            o = P - d * 3.0
            ok, loc, nrm, idx, ob, mtx = scn.ray_cast(dg, Vector(o), Vector(d), distance=6.0)
            n_ray += 1
            depth = None if not ok else float((np.array(loc) - P) @ (-n_out))
            if ok:
                hist[min(int(max(depth, -0.5) * 10 + 5), 15)] += 1
                if "blockers" in ob.name:
                    n_room += 1
            if not ok or depth > 0.70:
                n_leak += 1
                leaks[key] = leaks.get(key, 0) + 1
                if len(deep) < 12:
                    deep.append((round(x - B["x"], 2), round(z - lo, 2), key, None if not ok else ob.name,
                                 None if depth is None else round(depth, 2)))
print(f"EYEBROW PROBE: {n_ray} rays over the front arch (x {B['x'] - B['hw']:.2f}..{B['x'] + B['hw']:.2f} local), "
      f"{n_leak} leak(s)")
print("leaks by direction:", leaks)
print(f"rays ending on the window's dark room: {n_room}; first-hit depth histogram (0.1 m bins from -0.5 m):",
      hist.tolist())
for d_ in deep:
    print("  leak (dx, z over the lower roof, (yaw, pitch), first hit, depth):", d_)
