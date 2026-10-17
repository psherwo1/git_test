"""Director smoke test: pyramid_roof on 3, 6 and 8 sides (reuse claim), off-centre, no cabin."""
import os
import sys
import types

import bpy

sys.path.insert(0, r"C:\GitHubDesktop\git_test\blender_village\kit")
from village_kit.components.pyramid_roof import pyramid_roof  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.data.collections.new("TEST")
bpy.context.scene.collection.children.link(coll)
for n, cx in ((3, -12.0), (6, 0.0), (8, 12.0)):
    g = types.SimpleNamespace(prefix=f"T{n}", coll=coll)
    rec = pyramid_roof(g, 2.4, 3.0, name="roof", sides=n, rot_deg=-90.0, cx=cx, cy=5.0, pitch_deg=50.0,
                       eave_out=0.6, bell_deg=22.0, bell_len=0.8, kick=0.05, seed=f"t{n}")
    print("SMOKE sides %d: objs %s  eave z %.2f corner %.2f apex %.2f tip %.2f shingles %d" % (
        n, sorted(rec["objs"]), rec["z_eave"], rec["z_eave_corner"], rec["apex"], rec["tip"], rec["n_shingles"]))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyr_smoke.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
