"""python.exe -I render_vignette3.py <blend> <out_dir> --shots street,aerial [--samples N] [--preview] [--prefix preview_]
Opens the .blend (never saves).  --preview = 960x540."""
import os
import sys
import time

import bpy

argv = sys.argv[1:]
BLEND, RDIR = argv[0], os.path.abspath(argv[1])


def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d


SHOTS = arg("--shots", "street,aerial").split(",")
SAMPLES = int(arg("--samples", 128))
PREFIX = arg("--prefix", "")
PREVIEW = "--preview" in argv
os.makedirs(RDIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
scn = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scn.cycles.device = "GPU"
scn.cycles.use_adaptive_sampling = True
scn.cycles.use_denoising = True
scn.cycles.denoiser = "OPTIX"
scn.cycles.samples = SAMPLES
scn.render.resolution_x, scn.render.resolution_y = (960, 540) if PREVIEW else (1920, 1080)
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = "PNG"
scn.render.use_persistent_data = False
for shot in SHOTS:
    scn.camera = bpy.data.objects["CAM_" + shot]
    bpy.data.objects["VG_backdrop_street"].hide_render = shot != "street"
    bpy.data.objects["VG_backdrop_aerial"].hide_render = shot != "aerial"
    scn.render.filepath = os.path.join(RDIR, PREFIX + shot + ".png")
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print("RENDERED", shot, "seconds %.1f" % (time.perf_counter() - t0), flush=True)
print("ALL DONE", flush=True)

