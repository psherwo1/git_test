"""scratch (round 5): numeric check of the eyebrow bump on the recipe's MAIN roof (no build)."""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("recipe", os.path.join(HERE, "..", "build_v5_harbour_house.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
M = R.MAIN
B = M.BROWS[0]
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in B.items() if k != "window"})
print("U", round(M.U, 3), "Y", M.Y)
for d in (B["d_t"] - 0.05, B["d_t"] - 0.001, B["d_t"] + 0.001, B["d_t"] + 0.3, B["d_t"] + 0.8, B["d_t"] + 1.4):
    y = M.Y - d
    xs = np.array([B["x"] - 1.0, B["x"] - 0.6, B["x"] - 0.35, B["x"], B["x"] + 0.6])
    print(f"d {d:.3f}", np.round(M.warp_z(xs, np.full(5, y)) - M.warp_z(xs, np.full(5, y), brow={0: 0.0}), 3))
w = M.to_world(np.array([[B["x"], M.Y - B["d_t"], M.ref_z(M.Y - B["d_t"])]]))
print("front centre world (build coords)", np.round(w, 3))
print("old roof unchanged:", R.GableRoof(x0=0, x1=5, half=2, wall_z=3).BROWS == [])
