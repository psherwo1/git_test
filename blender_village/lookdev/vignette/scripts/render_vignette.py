"""Render the vignette shots and record time / memory.

python.exe -I render_vignette.py <vignette.blend> <render_dir> --shots s1_A,s1_B,... [--samples-a 128] [--samples-b 256]
                                 [--preview] [--noise] [--log measurements.jsonl]
    Opens the .blend (never saves it).  Shot names are <shot>_<light>, light A = r2 day (inherited LD_sun + sky),
    B = cinematic (low golden sun, hazier sky, VG_fog homogeneous Principled Volume domain Z -2..25).
    --preview: 25 % resolution, 16 samples (camera layout only; not logged as measurements).
    --noise:   for the listed B/A shots also renders a 480x270 full-resolution crop un-denoised at the same samples
               and at 4x samples (adaptive off) and writes RMS noise estimates (see measurements).
"""
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
import re
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[1:]
BLEND, RDIR = argv[0], os.path.abspath(argv[1])


def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d


SHOTS = arg("--shots", "s1_A,s1_B,s2_A,s2_B,s3_A,s4_A").split(",")
SA, SB = int(arg("--samples-a", 128)), int(arg("--samples-b", 128))
PREVIEW = "--preview" in argv
NOISE = "--noise" in argv
LOG = arg("--log", os.path.join(RDIR, "measurements.jsonl"))
os.makedirs(RDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
scn = bpy.context.scene
vl = bpy.context.view_layer


# ---------------------------------------------------------------- process memory (Windows psapi)
class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def proc_mem():
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wt.HANDLE
        k32.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        k32.K32GetProcessMemoryInfo.restype = wt.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            print("GetProcessMemoryInfo failed", ctypes.get_last_error(), flush=True)
        return pmc.WorkingSetSize / 2**20, pmc.PeakWorkingSetSize / 2**20, pmc.PagefileUsage / 2**20
    except Exception as ex:  # noqa
        print("proc_mem failed", ex, flush=True)
        return (None, None, None)


class MS(ctypes.Structure):
    _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def sys_mem():
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return (m.ullTotalPhys - m.ullAvailPhys) / 2**30, m.ullTotalPhys / 2**30


# ---------------------------------------------------------------- render stats capture
STATS = {"peak": 0.0, "mem": 0.0, "last": ""}
num = re.compile(r"([\d.]+)([KMG])")


def to_mb(s):
    m = num.match(s)
    if not m:
        return 0.0
    v = float(m.group(1))
    return v * {"K": 1 / 1024, "M": 1.0, "G": 1024.0}[m.group(2)]


def on_stats(s):
    STATS["last"] = s
    if "Mem" in s or "Peak" in s:
        STATS["last_mem"] = s
    mp = re.search(r"Peak[: ]+([\d.]+[KMG])", s)
    mm = re.search(r"Mem[: ]+([\d.]+[KMG])", s)
    if mp:
        STATS["peak"] = max(STATS["peak"], to_mb(mp.group(1)))
    if mm:
        STATS["mem"] = max(STATS["mem"], to_mb(mm.group(1)))


bpy.app.handlers.render_stats.append(on_stats)

# ---------------------------------------------------------------- device / render settings
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scn.cycles.device = "GPU" if any(d.use for d in prefs.devices) else "CPU"
print("DEVICE", scn.cycles.device, [d.name for d in prefs.devices if d.use], flush=True)
scn.cycles.use_adaptive_sampling = True
scn.cycles.use_denoising = True
try:
    scn.cycles.denoiser = "OPTIX"
except TypeError:
    pass
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = 25 if PREVIEW else 100
scn.render.image_settings.file_format = "PNG"
scn.render.use_persistent_data = False
scn.render.use_border = False
print("CYCLES max_bounces", scn.cycles.max_bounces, "volume_bounces", scn.cycles.volume_bounces,
      "adaptive_threshold", scn.cycles.adaptive_threshold, "view", scn.view_settings.view_transform,
      scn.view_settings.look, "exposure", scn.view_settings.exposure, flush=True)

cd = bpy.data.cameras.new("VG_cam")
cd.sensor_width = 36.0
cd.sensor_fit = "HORIZONTAL"
cd.clip_start = 0.05
cd.clip_end = 3000.0
cam = bpy.data.objects.new("VG_cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam

sun = bpy.data.objects["LD_sun"]
sky = next(n for n in scn.world.node_tree.nodes if n.type == "TEX_SKY")
bgn = next(n for n in scn.world.node_tree.nodes if n.type == "BACKGROUND")
fog = bpy.data.objects["VG_fog"]
A_STATE = dict(rot=tuple(sun.rotation_euler), energy=sun.data.energy, color=tuple(sun.data.color),
               elev=sky.sun_elevation, srot=sky.sun_rotation, bg=bgn.inputs["Strength"].default_value,
               sky={a: getattr(sky, a) for a in ("air_density", "aerosol_density", "dust_density", "ozone_density")
                    if hasattr(sky, a)})
print("LIGHT_A", json.dumps(A_STATE), "sky_type", sky.sky_type, flush=True)

B_ELEV = math.radians(10.0)
B_AZ = Vector((-0.97, -0.25, 0.0)).normalized()       # sun low in the W (slightly S, clear of the keep rise)
FOG_D = float(arg("--fog-density", 0.0025))
B_SUN = float(arg("--b-sun", 9.0))


def light(k):
    if k == "A":
        sun.rotation_euler = A_STATE["rot"]
        sun.data.energy, sun.data.color = A_STATE["energy"], A_STATE["color"]
        sky.sun_elevation, sky.sun_rotation = A_STATE["elev"], A_STATE["srot"]
        bgn.inputs["Strength"].default_value = A_STATE["bg"]
        for a, v in A_STATE["sky"].items():
            setattr(sky, a, v)
        fog.hide_render = True
    else:
        v = Vector((B_AZ.x * math.cos(B_ELEV), B_AZ.y * math.cos(B_ELEV), math.sin(B_ELEV)))
        sun.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
        sun.data.energy = B_SUN
        sun.data.color = (1.0, 0.56, 0.28)
        sky.sun_elevation = B_ELEV
        sky.sun_rotation = math.atan2(B_AZ.x, B_AZ.y)
        for a, val in (("air_density", 1.5), ("aerosol_density", 6.0), ("dust_density", 6.0)):
            if hasattr(sky, a):
                setattr(sky, a, val)
        bgn.inputs["Strength"].default_value = 0.12
        fog.hide_render = False
        pv = next(n for n in fog.material_slots[0].material.node_tree.nodes if n.type == "PRINCIPLED_VOLUME")
        pv.inputs["Density"].default_value = FOG_D


dg = bpy.context.evaluated_depsgraph_get()


def ground_z(x, y):
    hit, loc, *_ = scn.ray_cast(dg, Vector((x, y, 300.0)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0


# name: (cam xy or xyz, target xyz, lens, eye_height or None)
CAMS = {
    "s1": ((-52.0, -118.0, 46.0), (4.0, 2.0, 3.0), 40.0, None),
    "s2": ((-1.0, -13.0), (-9.0, 20.0, 7.0), 30.0, 1.7),
    "s3": ((22.0, -62.0, 0.45), (-7.0, -32.0, 5.0), 30.0, None),
    "s4": ((50.0, -27.0, 7.0), (14.0, 8.0, 6.0), 50.0, None),
    "top": ((0.0, 2.0, 250.0), (0.0, 2.0, 0.0), 0.0, None),
}


def set_cam(s):
    p, t, lens, eh = CAMS[s]
    if eh is not None:
        p = (p[0], p[1], ground_z(p[0], p[1]) + eh)
    p, t = Vector(p), Vector(t)
    cam.location = p
    if s == "top":
        cd.type = "ORTHO"
        cd.ortho_scale = 175.0
        cam.rotation_euler = (0, 0, 0)
    else:
        cd.type = "PERSP"
        cd.lens = lens
        cam.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    return p


def read_png(path):
    im = bpy.data.images.load(path)
    a = np.empty(im.size[0] * im.size[1] * im.channels, dtype=np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(im.size[1], im.size[0], im.channels)[:, :, :3]
    bpy.data.images.remove(im)
    return a


def render(path):
    STATS.update(peak=0.0, mem=0.0, last="", last_mem="")
    scn.render.filepath = path
    t0 = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    return time.perf_counter() - t0


def log(rec):
    print("MEASURE", json.dumps(rec), flush=True)
    if not PREVIEW:
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")


for shot in SHOTS:
    s, k = shot.split("_") if "_" in shot else (shot, "A")
    light(k)
    p = set_cam(s)
    smp = 16 if PREVIEW else (SA if k == "A" else SB)
    scn.cycles.samples = smp
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.use_denoising = True
    scn.render.use_border = False
    out = os.path.join(RDIR, ("prev_" if PREVIEW else "") + shot + ".png")
    sm0 = sys_mem()
    t_start = time.time()
    dt = render(out)
    t_end = time.time()
    wm, pk, pf = proc_mem()
    sm1 = sys_mem()
    rec = dict(shot=shot, light=k, fog_density=(FOG_D if k == "B" else 0), b_sun=(B_SUN if k == "B" else None), samples=smp, adaptive=True, seconds=round(dt, 1),
               cycles_mem_mb=round(STATS["mem"], 1), cycles_peak_mb=round(STATS["peak"], 1),
               proc_ws_mb=round(wm or 0), proc_peak_ws_mb=round(pk or 0), proc_commit_mb=round(pf or 0),
               sys_used_gb_before=round(sm0[0], 2), sys_used_gb_after=round(sm1[0], 2), sys_total_gb=round(sm1[1], 1),
               cam=[round(v, 2) for v in p], lens=CAMS[s][2], stats_last=STATS["last"],
               stats_mem=STATS.get("last_mem", ""), t_start=round(t_start, 2), t_end=round(t_end, 2), file=out)
    log(rec)
    if NOISE and not PREVIEW:
        # 480x270 full-res crop in the middle-upper third (fog / haze over the village), un-denoised
        scn.render.use_border = True
        scn.render.use_crop_to_border = True
        scn.render.border_min_x, scn.render.border_max_x = 0.375, 0.625
        scn.render.border_min_y, scn.render.border_max_y = 0.5, 0.75
        crops = {}
        for tag, n, dn in (("dn", smp, True), ("raw", smp, False), ("raw4x", smp * 4, False)):
            scn.cycles.samples = n
            scn.cycles.use_adaptive_sampling = False
            scn.cycles.use_denoising = dn
            cp = os.path.join(RDIR, "noise", "%s_crop_%s.png" % (shot, tag))
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            ct = render(cp)
            crops[tag] = (read_png(cp), ct, n)
        ref = crops["dn"][0]
        r1 = float(np.sqrt(np.mean((crops["raw"][0] - ref) ** 2)))
        r4 = float(np.sqrt(np.mean((crops["raw4x"][0] - ref) ** 2)))
        # noise vs the 4x render (independent of the denoiser): var(raw - raw4x) = s^2 (1 + 1/4)
        r14 = float(np.sqrt(np.mean((crops["raw"][0] - crops["raw4x"][0]) ** 2)))
        sigma_n = r14 / math.sqrt(1.25)
        target = 1.0 / 255.0 * 1.5     # "clean without a denoiser": ~1.5 8-bit levels RMS
        need = smp * (sigma_n / target) ** 2
        log(dict(shot=shot + "_noise", light=k, samples=smp, crop="480x270 @ x 37.5-62.5 %, y 50-75 %",
                 rms_raw_vs_denoised=round(r1 * 255, 2), rms_raw4x_vs_denoised=round(r4 * 255, 2),
                 sigma_raw_8bit=round(sigma_n * 255, 2), sigma_raw4x_8bit=round(sigma_n * 255 / 2, 2),
                 samples_needed_no_denoise_1p5lvl=int(round(need)),
                 crop_seconds={t: round(v[1], 1) for t, v in crops.items()}))
        scn.render.use_border = False
print("ALL DONE", flush=True)
