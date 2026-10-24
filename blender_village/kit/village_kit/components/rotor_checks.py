"""components.rotor_checks -- clearance checks of a mill rotor (spec G / I): rotation-swept clearance of the
wheel to the tower, cap, apron, props and tail, the tail's swept clearance at any cap yaw, blades vs arms.
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (lean)  # noqa: F401
from ..tmplmesh import (PI, chamfer_dt, log, part_samples, voxel_min_gap)  # noqa: F401


def rotor_internal_report(g, parts):
    """Blades vs wheel arms / arm straps (voxel proximity) and blade spacing."""
    def loc(V):
        d = V - g.HUB
        return np.stack([d @ g.E1, d @ g.E2, d @ g.S_AX], 1)
    bl = loc(part_samples(parts["wheel_blades"], 0.01))
    arms = np.concatenate([loc(part_samples(parts["wheel_arm_%s" % L], 0.01)) for L in "ABCD"])
    g1 = voxel_min_gap(bl, arms, 0.06)
    log("ROTOR wind-wheel blades vs arms: min gap %.3f m %s" % (g1, "(PASS)" if g1 > 0.015 else "(FAIL)"))
    for r in (2.5, g.BL_R1):
        s_ = np.clip((r - g.BL_R0) / (g.BL_R1 - g.BL_R0), 0, 1)
        w = g.BL_W0 + (g.BL_W1 - g.BL_W0) * s_
        log("WHEEL r=%.2f: blade width %.3f, pitch %.3f, gap %.3f m" % (r, w, 2 * PI * r / g.BL_N, 2 * PI * r / g.BL_N - w))
    return g1


def tail_clearance(g, parts, xf, res=0.02):
    """The tail turns with the cap about the (leaned) tower axis: collapse everything to (radius from the yaw
    axis, height along it) and measure the swept gap from the tail to the tower and the props at ANY yaw."""
    ax = g.LEAN_R @ np.array([0, 0, 1.0])

    def rz(V):
        d = V - g.LEAN_PIVOT
        h = d @ ax
        return np.linalg.norm(d - h[:, None] * ax, axis=1), h
    out = {}
    tail = np.concatenate([xf(parts[k], part_samples(parts[k], res)) for k in ("tail_boom", "tail_vane", "tail_iron")])
    tr, th = rz(tail)
    for k in ("tower_boards", "tower_frame", "tower_iron", "props", "prop_iron"):
        if not parts[k].V:          # kit 1.7 (v4_mixed): a part never built (a mill without props) is skipped
            continue
        sr, sh = rz(xf(parts[k], part_samples(parts[k], res)))
        best = 9.9
        for zlo in np.arange(th.min(), th.max(), 0.25):
            mt = (th >= zlo - 0.3) & (th < zlo + 0.55)
            ms = (sh >= zlo) & (sh < zlo + 0.25)
            if not ms.any() or not mt.any():
                continue
            # tail radii vs static radii in this height slab (yaw-swept: only radius and height matter)
            dr = np.abs(tr[mt][:, None] - sr[ms][None, ::max(1, ms.sum() // 400)])
            dh = np.abs(th[mt][:, None] - sh[ms][None, ::max(1, ms.sum() // 400)])
            best = min(best, float(np.sqrt(dr ** 2 + dh ** 2).min()))
        out[k] = best
    log("TAIL swept clearance at any cap yaw: " + ", ".join("%s %.3f m" % (k, v) for k, v in out.items()))
    return out


def clearance_report(g, rot_parts, static_parts, xf, res=0.02):
    """Rotation-swept clearance on FINAL (post-lean) positions: map everything to
    (w along the shaft, radius from the shaft). xf(part, V) -> final positions."""
    hub = lean(g, g.HUB[None])[0]
    sax = g.LEAN_R @ g.S_AX

    def to_rot(V):
        d = V - hub
        w = d @ sax
        rho = np.linalg.norm(d - w[:, None] * sax, axis=1)
        return w, rho
    RV = np.concatenate([xf(p, part_samples(p, res)) for p in rot_parts if p.V])
    w, rho = to_rot(RV)
    w0, w1, r1 = -3.0, 1.2, 6.4
    nw, nr = int((w1 - w0) / res) + 1, int(r1 / res) + 1
    G = np.zeros((nw, nr), bool)
    G[np.clip(((w - w0) / res).astype(int), 0, nw - 1), np.clip((rho / res).astype(int), 0, nr - 1)] = True
    DT = chamfer_dt(G, res)
    out = {}
    for p in static_parts:
        if not p.V:
            continue
        sw, sr = to_rot(xf(p, part_samples(p, res)))
        m = (sw > w0) & (sw < w1) & (sr < r1)
        if not m.any():
            out[p.name] = 9.9
            continue
        d = DT[((sw[m] - w0) / res).astype(int), (sr[m] / res).astype(int)]
        out[p.name] = float(d.min())
    return out


def rotor_clearance(g):
    """spec G / I: rotating parts vs tower, cap, apron, props and tail (>= 0.30 m), the tail's swept clearance at
    any cap yaw, and the blades vs the wheel arms.  Logs PASS / FAIL; returns the clearance table."""
    parts = g.parts
    rot = [p for k, p in parts.items() if k.startswith(("wheel_", "poll_end", "rotor_iron"))]
    stat = [parts[k] for k in ("tower_boards", "tower_frame", "tower_iron", "cap_frame", "cap_shingles", "cap_iron",
                               "apron", "curb", "props", "prop_anchors", "prop_iron", "tail_boom", "tail_vane",
                               "tail_iron")]

    def xf(p, V):
        return lean(g, V) if g.is_leaned(p) else V
    clr = clearance_report(g, rot, stat, xf)
    for k, v in sorted(clr.items(), key=lambda kv: kv[1]):
        log("CLEARANCE rotor -> %-24s %.3f m" % (k, v))
    lowest = min(lean(g, np.concatenate(p.V))[:, 2].min() for p in rot if p.V)
    log("lowest rotating point z = %.3f m (apron top %.2f m, ground 0)" % (lowest, g.AP_ZT))
    rotor_internal_report(g, parts)
    P = g.prefix
    # kit 1.7 (v4_mixed): a part that was never built (a mill without props) is absent from clr -> no constraint
    ok = min(clr.get(P + "_apron_shingles", 9.9), clr.get(P + "_props", 9.9), clr.get(P + "_tail_vane", 9.9)) >= 0.30
    log("CLEARANCE CHECK wheel vs apron/props/tail >= 0.30 m: %s" % ("PASS" if ok else "FAIL"))
    tail_clearance(g, parts, xf)
    g.clearance = dict(clr, lowest=lowest, ok=ok)
    return g.clearance
