"""UV grain / collapsed-UV / walked-top Mask audit of a building .blend (the queued kit UV fix, kit 1.10.0).

Adapted copy of lookdev/scripts/analyze_uv_grain.py and check_uv_stretch.py (the originals are unchanged): the
same per-face rules, vectorised, over EVERY rendered mesh object of the building, with arguments and a JSON report.

Usage:
    <python-with-bpy> blender_village/tools/uv_audit.py <file.blend> <out.json> [--entrances <audit.json>]

1. grain (analyze_uv_grain.py rules, unchanged): for every face of a wood slot (M_timber, M_timber_weathered,
   M_roof_shingle, M_roof_shake, M_thatch) the grain direction is dP/dv of its first three loops.  Pieces are the
   edge-connected loose parts; a part's long axis is its vertex PCA major axis, elongation sqrt(w2/w1).  On parts
   with elongation > 1.5 a face counts "along" when |grain . long axis projected into the face| > 0.7, "across" when
   < 0.3; the percentage is of the slot's WHOLE area (end grain and stubby parts stay in the denominator).  Faces
   with n.z > 0.2 count as roof area: "upslope" when grain . up-slope > 0.7, "downslope" when < -0.7.
   Added columns (not in the original): `judged_area` (faces the rule can judge: elongated parts, not end grain),
   `along_of_judged_pct`, `sheet_area` (faces on parts with elongation <= 1.5 -- decks, floors, ceilings, rings,
   backing and blocker sheets -- which the rule can never count as "along" whatever their UVs), and
   `piece_along_pct` (the same rule with loose parts split by the Mask R byte, i.e. per kit piece).
2. collapsed (check_uv_stretch.py rule, threshold 0.2 as in the fix brief): per object, the share of its area whose
   first-triangle UV/3D area ratio is < 0.2 (and < 0.3, the original script's print threshold).
3. walked tops: Mask B on up-facing faces (n.z > 0.7) inside each entrance's walking zone (clear width + 0.1 m each
   side, from 1.0 m inside the wall face to 1.5 m out, up to 0.9 m above the entrance origin).  Entrances come from
   the scene property `kit_entrances` (written by kit 1.10.0) or from another audit's JSON (--entrances), so a
   pre-fix build with identical geometry is judged on the same zones.  The gate figures count the building's own
   meshes; pooled linked duplicates in a zone (nail heads, pintles, hinge straps, pegs on the door: hardware, not
   walked pieces; the kit leaves their constant pool moss alone) are listed separately.
"""
import json
import sys

import bpy
import numpy as np

WOOD = ("M_timber", "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch")


def face_components(me):
    """edge-connected face components (label per polygon)."""
    npg = len(me.polygons)
    nl = len(me.loops)
    le = np.empty(nl, np.int64)
    me.loops.foreach_get("edge_index", le)
    lt = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_total", lt)
    lp = np.repeat(np.arange(npg), lt)
    order = np.argsort(le, kind="stable")
    les, lps = le[order], lp[order]
    same = les[1:] == les[:-1]
    a, b = lps[:-1][same], lps[1:][same]
    lab = np.arange(npg)
    if len(a) == 0:
        return lab
    for _ in range(1000):
        m = np.minimum(lab[a], lab[b])
        new = lab.copy()
        np.minimum.at(new, a, m)
        np.minimum.at(new, b, m)
        for _ in range(8):
            new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def mesh_arrays(o):
    me = o.data
    M = np.array(o.matrix_world)
    nv, npg, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    ls = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", lv)
    pm = np.empty(npg, np.int64)
    me.polygons.foreach_get("material_index", pm)
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.active
    uv = np.zeros(nl * 2)
    if uvl is not None:
        uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    return me, co, ls, lt, lv, pm, uv


def face_normals_areas(co, ls, lt, lv):
    """Newell normal + area per polygon (matches bmesh calc_area / normal for planar faces)."""
    lp = np.repeat(np.arange(len(ls)), lt)
    nxt = np.arange(len(lv)) + 1
    last = ls + lt - 1
    nxt[last] = ls
    P, Q = co[lv], co[lv[nxt]]
    cr = np.cross(P, Q)
    N = np.zeros((len(ls), 3))
    np.add.at(N, lp, cr)
    area = 0.5 * np.linalg.norm(N, axis=1)
    n = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-30)
    return n, area


def audit(path, ent_override=None):
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    ents = ent_override
    if ents is None and "kit_entrances" in sc.keys():
        ents = json.loads(sc["kit_entrances"])
    stats = {}
    obj_grain = {}
    collapsed = {}
    walked = []
    for o in sorted((o for o in sc.objects if o.type == "MESH" and not o.hide_render), key=lambda o: o.name):
        me, co, ls, lt, lv, pm, uv = mesh_arrays(o)
        if len(ls) == 0:
            continue
        mats = [m.name if m else None for m in me.materials]
        n, area = face_normals_areas(co, ls, lt, lv)
        ok3 = lt >= 3
        l0, l1, l2 = ls, ls + 1, ls + 2
        l1 = np.where(ok3, l1, ls)
        l2 = np.where(ok3, l2, ls)
        p0, p1, p2 = co[lv[l0]], co[lv[l1]], co[lv[l2]]
        u0, u1, u2 = uv[l0], uv[l1], uv[l2]
        e1, e2 = p1 - p0, p2 - p0
        d1, d2 = u1 - u0, u2 - u0
        # ---- collapsed (check_uv_stretch rule)
        a3 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
        a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
        r = a2 / np.maximum(a3, 1e-12)
        tot = float(area[ok3].sum())
        b2 = float(area[ok3 & (r < 0.2)].sum())
        b3 = float(area[ok3 & (r < 0.3)].sum())
        mat_of = np.array([mats[i] if i < len(mats) else None for i in pm], dtype=object)
        rec = collapsed.setdefault(o.data.name, dict(objects=[], area=round(tot, 3), lt02=round(b2, 4),
                                                     lt03=round(b3, 4), pct02=round(100 * b2 / max(tot, 1e-12), 3),
                                                     by_mat={}))
        rec["objects"].append(o.name)
        if len(rec["objects"]) == 1:
            for mname in sorted(set(x for x in mat_of if x)):
                s = ok3 & (mat_of == mname)
                ta = float(area[s].sum())
                rec["by_mat"][mname] = round(100 * float(area[s & (r < 0.2)].sum()) / max(ta, 1e-12), 3)
        # ---- grain (analyze_uv_grain rules)
        wood = np.isin(mat_of.astype(str), WOOD) & ok3
        if wood.any():
            det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
            good = wood & (np.abs(det) >= 1e-12)
            dPdv = (e2 * d1[:, :1] - e1 * d2[:, :1]) / np.where(np.abs(det) < 1e-12, 1, det)[:, None]
            L = np.linalg.norm(dPdv, axis=1)
            good &= L >= 1e-9
            gv = dPdv / np.maximum(L, 1e-30)[:, None]
            comp = face_components(me)
            lp = np.repeat(np.arange(len(ls)), lt)

            def judge_by(label):
                """per-label PCA over its vertices (a vertex shared by two labels counts in both, as in the
                original); -> (along, across) bool per face."""
                _, lab = np.unique(label, return_inverse=True)
                lab = lab.ravel()
                pairs = np.unique(lab[lp] * (len(co) + 1) + lv)
                pc, vi = pairs // (len(co) + 1), pairs % (len(co) + 1)
                K = lab.max() + 1
                cnt = np.bincount(pc, minlength=K).astype(float)
                mean = np.zeros((K, 3))
                np.add.at(mean, pc, co[vi])
                mean /= np.maximum(cnt, 1)[:, None]
                C = co[vi] - mean[pc]
                cov = np.zeros((K, 3, 3))
                np.add.at(cov, pc, C[:, :, None] * C[:, None, :])
                w, V = np.linalg.eigh(cov)
                elong = np.sqrt(w[:, 2] / np.maximum(w[:, 1], 1e-9))
                fa = V[:, :, 2][lab]
                fe = elong[lab]
                la = fa - n * (fa * n).sum(1, keepdims=True)
                lal = np.linalg.norm(la, axis=1)
                c = np.abs((gv * la).sum(1)) / np.maximum(lal, 1e-30)
                judge = good & (fe > 1.5) & (lal > 1e-6)
                return judge & (c > 0.7), judge & (c < 0.3), judge, good & (fe <= 1.5)

            along, across, judged, sheet = judge_by(comp)
            # the same rule per PIECE: loose parts split by the Mask R byte (one R per kit piece), so pieces the
            # Nanite clean-up welded into one loose part (a rafter ring, a frame) are judged on their own axis
            ca_ = me.color_attributes.get("Mask")
            rb = np.zeros(len(ls), np.int64)
            if ca_ is not None and ca_.domain == "CORNER":
                cc = np.empty(len(me.loops) * 4, np.float32)
                ca_.data.foreach_get("color_srgb" if ca_.data_type == "BYTE_COLOR" else "color", cc)
                rb = np.round(cc.reshape(-1, 4)[ls, 0] * 255).astype(np.int64)
            along_p, across_p, _, _ = judge_by(comp * 256 + rb)
            up = np.stack([-n[:, 0] * n[:, 2], -n[:, 1] * n[:, 2], 1 - n[:, 2] * n[:, 2]], 1)
            upl = np.linalg.norm(up, axis=1)
            roof = good & (n[:, 2] > 0.2) & (upl > 1e-6)
            cu = (gv * up).sum(1) / np.maximum(upl, 1e-30)
            for mname in WOOD:
                s = good & (mat_of == mname)
                if not s.any():
                    continue
                blank = dict(area=0.0, along=0.0, across=0.0, along_p=0.0, across_p=0.0, judged=0.0, sheet=0.0,
                             roofarea=0.0, upslope=0.0, downslope=0.0, scale=[])
                for tgt in (stats.setdefault(mname, dict(blank, scale=[])),
                            obj_grain.setdefault(o.name + "|" + mname, dict(blank, scale=[]))):
                    tgt["area"] += float(area[s].sum())
                    tgt["along"] += float(area[s & along].sum())
                    tgt["across"] += float(area[s & across].sum())
                    tgt["judged"] += float(area[s & judged].sum())
                    tgt["sheet"] += float(area[s & sheet].sum())
                    tgt["along_p"] += float(area[s & along_p].sum())
                    tgt["across_p"] += float(area[s & across_p].sum())
                    tgt["roofarea"] += float(area[s & roof].sum())
                    tgt["upslope"] += float(area[s & roof & (cu > 0.7)].sum())
                    tgt["downslope"] += float(area[s & roof & (cu < -0.7)].sum())
                    tgt["scale"].append(L[s])
        # ---- walked tops: Mask B in the entrance zones
        if ents:
            ca = me.color_attributes.get("Mask")
            if ca is None:
                continue
            col = np.empty(len(me.loops) * 4)
            ca.data.foreach_get("color_srgb" if ca.data_type == "BYTE_COLOR" else "color", col)
            Bl = col.reshape(-1, 4)[:, 2]
            cen = np.zeros((len(ls), 3))
            lp = np.repeat(np.arange(len(ls)), lt)
            np.add.at(cen, lp, co[lv])
            cen /= lt[:, None]
            upf = n[:, 2] > 0.7
            for e in ents:
                O = np.asarray(e["origin"], float)
                if O.shape == (2,):
                    O = np.array([O[0], O[1], 0.0])
                out = np.asarray(e["out"], float)[:2]
                out = out / max(np.linalg.norm(out), 1e-9)
                t = np.array([-out[1], out[0]])
                d = cen[:, :2] - O[:2]
                along_out = d @ out
                across_d = d @ t
                dz = cen[:, 2] - O[2]
                zone = (np.abs(across_d) <= e["width"] / 2 + 0.1) & (along_out >= -1.0) & (along_out <= 1.5) & \
                       (dz >= -0.3) & (dz <= 0.9) & upf
                if not zone.any():
                    continue
                fl = zone[lp]
                bmax_f = np.zeros(len(ls))
                np.maximum.at(bmax_f, lp[fl], Bl[fl])
                fi = np.flatnonzero(zone)
                walked.append(dict(entrance=e["name"], object=o.name, faces=int(len(fi)), pooled=me.users > 1,
                                   area=round(float(area[fi].sum()), 4),
                                   b_max=round(float(bmax_f[fi].max()), 4),
                                   b_mean=round(float((bmax_f[fi] * area[fi]).sum() / max(area[fi].sum(), 1e-12)), 4),
                                   area_over_005=round(float(area[fi][bmax_f[fi] > 0.05 + 1e-6].sum()), 4)))
    out = dict(file=path, entrances=ents, grain={}, grain_by_object={}, collapsed=collapsed, walked=walked)
    for k, s in list(stats.items()) + [("|" + k, v) for k, v in obj_grain.items()]:
        sc_ = np.concatenate(s["scale"]) if s["scale"] else np.zeros(1)
        rec = dict(area=round(s["area"], 3), along_pct=round(100 * s["along"] / max(s["area"], 1e-9), 1),
                   across_pct=round(100 * s["across"] / max(s["area"], 1e-9), 1),
                   judged_area=round(s["judged"], 3), sheet_area=round(s["sheet"], 3),
                   along_of_judged_pct=round(100 * s["along"] / max(s["judged"], 1e-9), 1),
                   piece_along_pct=round(100 * s["along_p"] / max(s["area"], 1e-9), 1),
                   piece_across_pct=round(100 * s["across_p"] / max(s["area"], 1e-9), 1),
                   roofarea=round(s["roofarea"], 3),
                   upslope_pct=round(100 * s["upslope"] / max(s["roofarea"], 1e-9), 1),
                   downslope_pct=round(100 * s["downslope"] / max(s["roofarea"], 1e-9), 1),
                   m_per_uv_median=round(float(np.median(sc_)), 3))
        if k.startswith("|"):
            out["grain_by_object"][k[1:]] = rec
        else:
            out["grain"][k] = rec
    return out


def summary(res):
    lines = []
    for k in WOOD:
        if k in res["grain"]:
            s = res["grain"][k]
            lines.append(f"GRAIN {k:20s} area {s['area']:8.1f}  along {s['along_pct']:5.1f}%  across {s['across_pct']:5.1f}%"
                         f"  [of judged {s['along_of_judged_pct']:5.1f}%; sheets {s['sheet_area']:6.1f}]"
                         f"  (per piece: along {s['piece_along_pct']:5.1f}%)"
                         f"  | roof {s['roofarea']:7.1f}: up {s['upslope_pct']:5.1f}%  down {s['downslope_pct']:5.1f}%"
                         f"  | m/UV {s['m_per_uv_median']:.2f}")
    bad = sorted(((v["pct02"], k) for k, v in res["collapsed"].items() if v["pct02"] >= 1.0), reverse=True)
    lines.append(f"COLLAPSED objects >= 1% area at ratio<0.2: {len(bad)} of {len(res['collapsed'])}; worst max "
                 f"{bad[0][0] if bad else max([v['pct02'] for v in res['collapsed'].values()] or [0]):.2f}%")
    for p, k in bad[:40]:
        lines.append(f"   {k:40s} {p:6.2f}%  {res['collapsed'][k]['by_mat']}")
    if res["walked"]:
        ws = [w for w in res["walked"] if not w.get("pooled")]
        wp = [w for w in res["walked"] if w.get("pooled")]
        tot = sum(w["area"] for w in ws)
        over = sum(w["area_over_005"] for w in ws)
        bmax = max([w["b_max"] for w in ws] or [0.0])
        lines.append(f"WALKED tops in door zones: area {tot:.3f} m2, B max {bmax:.3f}, area with B > 0.05: {over:.3f} m2"
                     f"  (pooled door hardware in the zones, not walked pieces: {len(wp)} objects, "
                     f"{sum(w['area'] for w in wp):.4f} m2, B max {max([w['b_max'] for w in wp] or [0.0]):.3f})")
        for w in ws:
            lines.append(f"   {w['entrance']:16s} {w['object']:32s} faces {w['faces']:5d} area {w['area']:7.3f} "
                         f"B max {w['b_max']:.3f} mean {w['b_mean']:.3f} >0.05 {w['area_over_005']:.3f}")
    else:
        lines.append("WALKED: no entrances known (pass --entrances <audit.json of a kit 1.10 build>)")
    return "\n".join(lines)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ent = None
    if "--entrances" in args:
        i = args.index("--entrances")
        ent = json.load(open(args[i + 1]))["entrances"]
        args = args[:i] + args[i + 2:]
    res = audit(args[0], ent)
    if len(args) > 1:
        with open(args[1], "w") as f:
            json.dump(res, f, indent=1)
    print(summary(res))
