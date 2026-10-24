"""scratch: run the kit's anchor audit (village_kit.anchor_audit) on a built blend + its decal_anchors.json."""
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, r"C:\GitHubDesktop\git_test\blender_village\kit")
from village_kit.anchor_audit import audit_anchors  # noqa: E402
from village_kit.decals import DecalAnchors, SurfaceProbe  # noqa: E402

blend, js = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
data = json.load(open(js))
da = DecalAnchors("HARB")
for a in data["anchors"]:
    da.items.append(dict(type=a["type"], pos=np.array(a["position"]), normal=np.array(a["normal"]),
                         up=np.array(a["up"]), size=tuple(a["size"]), surface=a["surface"],
                         probability=a["probability"], seed=a["seed"], name=a["name"]))
probe = SurfaceProbe([o for o in bpy.data.objects if o.type == "MESH"])
bad = audit_anchors(da, probe)
print("ANCHOR_AUDIT", len(da.items), "anchors,", len(bad), "failures", data.get("counts"))
for b in bad[:20]:
    print("   ", b)
