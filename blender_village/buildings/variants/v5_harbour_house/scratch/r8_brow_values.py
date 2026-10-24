"""scratch (round 8): the eyebrow's numbers -- course spacing (3D arc between successive course butts on the bumped
section) at the crown and on the shoulders, with and without respace; the arch's shoulder steepness.
python -I r8_brow_values.py   (run from anywhere; reads ../build_v5_harbour_house.py)"""
import importlib.util
import math
import os

import numpy as np

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("recipe", os.path.join(HERE, "..", "build_v5_harbour_house.py"))
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    from village_kit.components.linear_roof import _brow_respace
    from village_kit.shingles import SIZE_TABLE
    M = R.MAIN
    B = M.BROWS[0]
    e = 0.5 * sum(SIZE_TABLE["shingle"]["exposure"])
    ue = B["u_t"] + B["plat_u"] + B["fade_u"]
    print(f"e {e:.3f}  u_lip {B['u_lip']:.3f} u_t {B['u_t']:.3f} fade end {ue:.3f} U {M.U:.3f} k_lip {B['k_lip']}")
    for dx in (0.0, 0.5, 0.875, 1.2):
        x = B["x"] + dx
        b = float(M.brow_bell(B, np.array([x]))[0])
        for rs in (False, True):
            ub = np.arange(B["k_lip"], 40) * e
            ub = ub[ub < ue + 2 * e]
            uu = _brow_respace(M, B, np.full(ub.shape, x), ub) if rs else ub
            P = M.to_world(M.surf(np.full(ub.shape, x), uu, B["sg"], 0.0), brow=1.0)
            gap = np.linalg.norm(np.diff(P, axis=0), axis=1) / e
            print(f"dx {dx:+.3f} bell {b:.3f} respace {rs!s:5s}: course spacing / e  min {gap.min():.2f} "
                  f"max {gap.max():.2f}  ", " ".join(f"{g:.2f}" for g in gap))
    xs = np.linspace(B["x"] - B["hw"], B["x"] + B["hw"], 2001)
    z = B["height"] * M.brow_bell(B, xs)
    g = np.gradient(z, xs)
    k = np.gradient(g, xs)
    i0 = int(np.argmin(np.abs(xs - B["x"])))
    print(f"arch: max flank gradient {np.abs(g).max():.2f} ({math.degrees(math.atan(np.abs(g).max())):.0f} deg); "
          f"crown curvature {abs(k[i0]):.2f} /m (radius {1 / max(abs(k[i0]), 1e-9):.2f} m); "
          f"lift at +-0.53 m {B['height'] * float(M.brow_bell(B, np.array([B['x'] + 0.53]))[0]):.3f} m")
    w = np.abs(xs - B["x"]) <= 0.53
    print(f"curvature over the window span: min {np.abs(k[w]).min():.2f} /m (never 0)")
