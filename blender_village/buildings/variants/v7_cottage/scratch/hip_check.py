"""v7 round 4 scratch: numeric checks of GableRoof(hips=, crown=) (bend round trip, nose seam, apex)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import build_v7_cottage as R  # noqa: E402

if __name__ == "__main__":
    for roof in (R.MAIN, R.WING):
        H = roof.HIPS
        print(roof.name, "xa xb", round(roof.xa, 3), round(roof.xb, 3), "hips", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in H.items()})
        rng = np.random.default_rng(1)
        L = np.stack([rng.uniform(roof.xa, roof.xb, 2000), rng.uniform(-roof.Y, roof.Y, 2000), rng.uniform(2, 7, 2000)], 1)
        W = roof.to_world(L)
        L2 = roof.to_local(W)
        print("  round trip max err", float(np.abs(L2 - L).max()))
        for sg in (-1, 1):
            for xe in (roof.xa, roof.xb):
                P = roof.to_world(roof.surf(np.full(5, xe), np.linspace(0, roof.U, 5), sg, 0.0))
                print("  nose", sg, round(xe, 2), np.round(P[[0, 2, 4]], 3).tolist())
        # apex: all virtual x past a hip centre at y = 0 -> one point
        c = H["c_hi"] if H["hi"] else H["c_lo"]
        s = 1 if H["hi"] else -1
        A = roof.to_world(np.stack([c + s * np.linspace(0, H["Q"], 5), np.zeros(5), np.full(5, 6.0)], 1))
        print("  apex spread", float(np.ptp(A, axis=0).max()))
        print("  under_z_world over the end wall", [round(float(roof.under_z_world(roof.to_world(np.array([[x, 0.0, 0.0]]))[:, :2])[0]), 2) for x in (roof.x0, roof.x1)])
    print("brow", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in R.MAIN.BROWS[0].items() if k not in ("window",)})
    print("U", R.MAIN.U, "z_ridge", R.MAIN.z_ridge, "z_lip", R.MAIN.z_lip)
    print("corner deck under", R.MAIN.under_z_world([[R.X1, R.HALF], [R.X0, -R.HALF], [R.X1, 0.0]]))
