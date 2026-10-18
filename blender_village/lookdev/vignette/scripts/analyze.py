"""Collate render measurements -> renders/measurements_auto.md (raw tables; renders/measurements.md is the
hand-edited write-up of these numbers).  Run after run_final.ps1; uses bpy only to read PNGs.

python.exe -I analyze.py
"""
import datetime as dtm
import json
import os
import time

import bpy
import numpy as np

V = r"C:\GitHubDesktop\git_test\blender_village\lookdev\vignette"
R = os.path.join(V, "renders")


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


recs = jl(os.path.join(R, "measurements.jsonl")) + jl(os.path.join(R, "b512", "measurements_b512.jsonl"))
gpu = []
for line in open(os.path.join(V, "logs", "gpu.csv")):
    p = [s.strip() for s in line.split(",")]
    if len(p) < 4:
        continue
    try:
        t = time.mktime(dtm.datetime.strptime(p[0], "%Y/%m/%d %H:%M:%S.%f").timetuple()) + float("0." + p[0].split(".")[-1])
        gpu.append((t, float(p[1].split()[0]), float(p[2].split()[0]), float(p[3].split()[0])))
    except ValueError:
        continue
gpu = np.array(gpu)
base = float(gpu[:4, 1].min()) if len(gpu) else float("nan")


def gpu_during(r):
    if not len(gpu) or "t_start" not in r:
        return None
    m = (gpu[:, 0] >= r["t_start"] - 0.25) & (gpu[:, 0] <= r["t_end"] + 0.25)
    return float(gpu[m, 1].max()) if m.any() else None


def png(p):
    im = bpy.data.images.load(p)
    a = np.empty(im.size[0] * im.size[1] * im.channels, dtype=np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(im.size[1], im.size[0], im.channels)[:, :, :3]
    bpy.data.images.remove(im)
    return a


cmp = {}
for s in ("s1_B", "s2_B", ):
    a, b = os.path.join(R, s + ".png"), os.path.join(R, "b512", s + ".png")
    if os.path.exists(a) and os.path.exists(b):
        d = (png(a) - png(b)) * 255
        cmp[s] = (float(np.sqrt((d ** 2).mean())), float((np.abs(d).max(2) > 6).mean() * 100))

frames = [r for r in recs if "seconds" in r]
noise = {r["shot"][:-6]: r for r in recs if r["shot"].endswith("_noise")}
L = []
L.append("# Vignette render measurements\n")
L.append("Machine: Windows 11, RTX 3060 12 GB, 16 GB RAM. bpy 5.1.2, Cycles OptiX GPU, 1920x1080, OptiX denoiser, "
         "adaptive sampling (threshold 0.01), max bounces 8, volume bounces 0, persistent data OFF (every render "
         "re-syncs the scene and re-builds the BVH, so each time below includes scene sync + BVH + textures + "
         "path tracing + denoise + PNG save).  Scene built by scripts/build_vignette.py, rendered by "
         "scripts/render_vignette.py via scripts/run_final.ps1.\n")
L.append("GPU baseline (nvidia-smi, before the render process loaded, includes other processes on the GPU): "
         "%.0f MiB of %.0f MiB.\n" % (base, gpu[0, 2] if len(gpu) else float("nan")))
L.append("| render | light | samples | wall-clock s | Cycles 'Mem' (stats) MB | GPU used during render (nvidia-smi, all processes) MiB | process working set after / peak MB | system RAM used before -> after GB (of 15.9) |")
L.append("|---|---|---|---|---|---|---|---|")
for r in frames:
    g = gpu_during(r)
    L.append("| %s%s | %s | %d | %.1f | %.0f | %s | %d / %d | %.2f -> %.2f |" % (
        r["shot"], " (512)" if "b512" in r["file"] else "", r["light"], r["samples"], r["seconds"], r["cycles_mem_mb"],
        "%.0f" % g if g else "-", r["proc_ws_mb"], r["proc_peak_ws_mb"], r["sys_used_gb_before"], r["sys_used_gb_after"]))
L.append("")
by = {(r["shot"], "b512" in r["file"]): r for r in frames}
L.append("## A (no fog) vs B (fog) at the same 128 samples\n")
for s in ("s1", "s2"):
    a, b = by.get((s + "_A", False)), by.get((s + "_B", False))
    if a and b:
        ga, gb = gpu_during(a), gpu_during(b)
        L.append("- %s: time %.1f s -> %.1f s (x%.2f, +%.1f s); Cycles Mem %.0f -> %.0f MB (+%.0f MB); GPU used %s -> %s MiB." % (
            s, a["seconds"], b["seconds"], b["seconds"] / a["seconds"], b["seconds"] - a["seconds"], a["cycles_mem_mb"],
            b["cycles_mem_mb"], b["cycles_mem_mb"] - a["cycles_mem_mb"], "%.0f" % ga if ga else "-", "%.0f" % gb if gb else "-"))
L.append("")
L.append("## Noise\n")
L.append("Method: a 480x270 full-resolution crop (centre-upper part of the frame: haze over the village) rendered three "
         "times with adaptive sampling OFF: denoised at N, raw at N, raw at 4N.  sigma = RMS(raw_N - raw_4N)/sqrt(1.25) "
         "is the raw per-pixel noise at N in 8-bit display levels; 'samples for clean' = N x (sigma / 1.5 levels)^2, i.e. "
         "the samples at which the image would be clean WITHOUT a denoiser (1/sqrt(N) scaling).\n")
L.append("| crop | N | raw noise sigma (8-bit levels) at N | at 4N | raw vs denoised RMS | samples for clean without denoiser | crop render s (dn / raw / raw4x, incl. ~3.5 s sync) |")
L.append("|---|---|---|---|---|---|---|")
for s, r in noise.items():
    cs = r["crop_seconds"]
    L.append("| %s | %d | %.2f | %.2f | %.2f | ~%d | %.1f / %.1f / %.1f |" % (
        s, r["samples"], r["sigma_raw_8bit"], r["sigma_raw4x_8bit"], r["rms_raw_vs_denoised"],
        r["samples_needed_no_denoise_1p5lvl"], cs["dn"], cs["raw"], cs["raw4x"]))
L.append("")
for s, (rms, frac) in cmp.items():
    L.append("- %s denoised 128 spp vs denoised 512 spp (full frame): RMS difference %.2f 8-bit levels, %.2f %% of "
             "pixels differ by more than 6 levels." % (s, rms, frac))
open(os.path.join(R, "measurements_auto.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
