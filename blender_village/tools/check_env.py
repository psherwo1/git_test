"""Check that this machine can continue the village production.

Usage:
    <python-with-bpy> blender_village/tools/check_env.py

What it checks:
- Blender (bpy) is importable, and its version.
- Which Cycles GPU devices it can see.
- That village_kit imports.
- That the roundhut rebuilds to the triangle count recorded in its latest review
  stats (proves the build is deterministic on this machine).

It prints PASS or FAIL per check, and the --render_flags to use with the workflows.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def report(name, passed, detail=""):
    global ok
    ok &= passed
    print(f"[{'PASS' if passed else 'FAIL'}] {name}{': ' + detail if detail else ''}")


try:
    import bpy
    report("bpy import", True, bpy.app.version_string)
except Exception as e:  # noqa: BLE001
    report("bpy import", False, str(e))
    sys.exit(1)

flags = ""
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    found = []
    for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            devs = [d.name for d in prefs.devices if d.type == backend]
            if devs:
                found.append((backend, devs))
        except TypeError:
            pass
    if found:
        report("Cycles GPU", True, "; ".join(f"{b}: {', '.join(d)}" for b, d in found))
        flags = f"--device GPU --gpu-backend {found[0][0]}"
    else:
        report("Cycles GPU", True, "none found, renders will use the CPU")
except Exception as e:  # noqa: BLE001
    report("Cycles GPU", False, str(e))

sys.path.insert(0, os.path.join(ROOT, "kit"))
try:
    import village_kit  # noqa: F401
    report("village_kit import", True)
except Exception as e:  # noqa: BLE001
    report("village_kit import", False, str(e))

# Deterministic rebuild check on the roundhut (the fastest build).
hut = os.path.join(ROOT, "buildings", "wattle_roundhut")
stats = sorted(glob.glob(os.path.join(ROOT, "renders", "wattle_roundhut", "round_*", "stats.json")))
if stats:
    expected = json.load(open(stats[-1]))["triangles"]
    tmp_blend = os.path.join(hut, "wattle_roundhut.blend")
    before = os.path.getmtime(tmp_blend) if os.path.exists(tmp_blend) else None
    r = subprocess.run([sys.executable, os.path.join(hut, "build_wattle_roundhut.py")],
                       cwd=hut, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        report("roundhut rebuild", False, r.stderr[-400:])
    else:
        bpy.ops.wm.open_mainfile(filepath=tmp_blend)
        dg = bpy.context.evaluated_depsgraph_get()
        tris = 0
        for o in bpy.context.scene.objects:
            if o.type == "MESH" and not o.hide_render:
                me = o.evaluated_get(dg).to_mesh()
                me.calc_loop_triangles()
                tris += len(me.loop_triangles)
                o.evaluated_get(dg).to_mesh_clear()
        report("roundhut rebuild is deterministic", abs(tris - expected) <= expected * 0.005,
               f"{tris:,} tris vs {expected:,} in {os.path.relpath(stats[-1], ROOT)}")
else:
    report("roundhut rebuild", False, "no review stats found")

print()
print("render_flags for the workflows:", repr(flags))
print("python for the workflows:", repr(sys.executable))
print("root for the workflows:", repr(ROOT))
print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
