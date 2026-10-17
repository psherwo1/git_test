"""Independent re-measurement of the kit 1.10 UV fix (verification helper, 4_verify; reads only).

Usage: <bpy-python> uv_verify.py <file.blend> <out.json>

Re-implements, vectorised and over every rendered mesh object, the three acceptance rules of
director/queued_uv_fix.md, written from the brief and the two look-dev scripts (not from tools/uv_audit.py):
  1. grain: lookdev/scripts/analyze_uv_grain.py's rule (dP/dv of each face's first triangle against the long axis of
     its edge-connected loose part, judged on parts with elongation > 1.5; up-slope for faces with n.z > 0.2);
     reported both over the slot's whole area (the script's number) and over the area the rule can judge;
  2. collapsed: per object, the area whose UV/3D area ratio < 0.2 (first triangle, as check_uv_stretch.py, and the
     whole face);
  3. walked tops: Mask B of up-facing faces (n.z > 0.7) inside each entrance's walking zone (clear width + 0.1 m each
     side, 1.0 m inside to 1.5 m out), with a WIDER height band than the kit's (-0.3 .. +1.2 m) and pooled instances
     included.  Entrances from the scene property kit_entrances.
"""
import json
import sys

import bpy
import numpy as np

GRAIN = ("M_timber", "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch")


def mesh_arrays(o):
    me = o.data
    nv, nl, npo = len(me.vertices), len(me.loops), len(me.polygons)
    co = np.zeros(nv * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world)
    co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    lv = np.zeros(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
    le = np.zeros(nl, np.int64); me.loops.foreach_get("edge_index", le)
    ps = np.zeros(npo, np.int64); me.polygons.foreach_get("loop_start", ps)
    pt = np.zeros(npo, np.int64); me.polygons.foreach_get("loop_total", pt)
    pm = np.zeros(npo, np.int64); me.polygons.foreach_get("material_index", pm)
    uv = None
    if me.uv_layers.active:
        u = np.zeros(nl * 2); me.uv_layers.active.data.foreach_get("uv", u); uv = u.reshape(-1, 2)
    mk = None
    ca = me.color_attributes.get("Mask")
    if ca is not None and ca.domain == "CORNER":
        c = np.zeros(len(ca.data) * 4); ca.data.foreach_get("color", c); mk = c.reshape(-1, 4)
    mats = [m.name if m else None for m in me.materials]
    return co, lv, le, ps, pt, pm, uv, mk, mats


def face_geom(co, lv, ps, pt):
    nl = len(lv)
    poly_of_loop = np.repeat(np.arange(len(ps)), pt)
    i = np.arange(nl) - ps[poly_of_loop]
    sel = (i >= 1) & (i <= pt[poly_of_loop] - 2)
    j = np.nonzero(sel)[0]
    p0 = co[lv[ps[poly_of_loop[j]]]]
    cr = np.cross(co[lv[j]] - p0, co[lv[j + 1]] - p0)
    S = np.zeros((len(ps), 3))
    np.add.at(S, poly_of_loop[j], cr)
    area = 0.5 * np.linalg.norm(S, axis=1)
    nrm = S / np.maximum(np.linalg.norm(S, axis=1), 1e-15)[:, None]
    cen = np.zeros((len(ps), 3))
    np.add.at(cen, poly_of_loop, co[lv])
    cen /= pt[:, None]
    return area, nrm, cen, poly_of_loop


def components(le, poly_of_loop, npo):
    order = np.argsort(le, kind="stable")
    e_s = le[order]; p_s = poly_of_loop[order]
    same = e_s[1:] == e_s[:-1]
    a = p_s[:-1][same]; b = p_s[1:][same]
    lab = np.arange(npo)
    while True:
        m = np.minimum(lab[a], lab[b])
        old = lab.copy()
        np.minimum.at(lab, a, m); np.minimum.at(lab, b, m)
        for _ in range(4):
            lab = lab[lab]
        if np.array_equal(lab, old):
            break
    _, comp = np.unique(lab, return_inverse=True)
    return comp.ravel()


def measure(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    ents = json.loads(sc.get("kit_entrances") or "[]")
    grain = {}
    coll = {}
    walk = [dict(name=e["name"], area=0.0, faces=0, b_max=0.0, bad_area=0.0, bad=[] , objs={}) for e in ents]
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render or len(o.data.polygons) == 0:
            continue
        co, lv, le, ps, pt, pm, uv, mk, mats = mesh_arrays(o)
        area, nrm, cen, pol = face_geom(co, lv, ps, pt)
        npo = len(ps)
        # ---- collapsed UVs (any slot)
        if uv is not None:
            l0, l1, l2 = ps, ps + 1, ps + 2
            e1 = co[lv[l1]] - co[lv[l0]]; e2 = co[lv[l2]] - co[lv[l0]]
            d1 = uv[l1] - uv[l0]; d2 = uv[l2] - uv[l0]
            a3 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
            a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
            r_first = a2 / np.maximum(a3, 1e-12)
            # whole-face UV area (shoelace over the loop ring)
            nxt = np.arange(len(lv)) + 1
            last = ps + pt - 1
            nxt[last] = ps
            cr = uv[:, 0] * uv[nxt, 1] - uv[nxt, 0] * uv[:, 1]
            ua = np.zeros(npo); np.add.at(ua, pol, cr)
            r_face = 0.5 * np.abs(ua) / np.maximum(area, 1e-12)
            tot = float(area.sum())
            if tot > 0:
                coll[o.name] = dict(area=tot, first_lt02=float(area[r_first < 0.2].sum()),
                                    face_lt02=float(area[r_face < 0.2].sum()))
        else:
            coll[o.name] = dict(area=float(area.sum()), first_lt02=float(area.sum()), face_lt02=float(area.sum()),
                                no_uv=True)
        # ---- grain
        slot = np.array([mats[i] if i < len(mats) else None for i in pm], dtype=object)
        gsel = np.isin(slot, GRAIN)
        if gsel.any() and uv is not None:
            comp = components(le, pol, npo)
            nc = comp.max() + 1
            # unique (component, vertex) pairs -> PCA per component
            cv = np.unique(np.column_stack([comp[pol], lv]), axis=0)
            P = co[cv[:, 1]]
            cnt = np.bincount(cv[:, 0], minlength=nc).astype(float)
            mu = np.zeros((nc, 3)); np.add.at(mu, cv[:, 0], P); mu /= np.maximum(cnt, 1)[:, None]
            C = P - mu[cv[:, 0]]
            cov = np.zeros((nc, 3, 3)); np.add.at(cov, cv[:, 0], C[:, :, None] * C[:, None, :])
            w, V = np.linalg.eigh(cov)
            elong = np.sqrt(w[:, 2] / np.maximum(w[:, 1], 1e-9))
            long_ax = V[:, :, 2]
            l0, l1, l2 = ps, ps + 1, ps + 2
            e1 = co[lv[l1]] - co[lv[l0]]; e2 = co[lv[l2]] - co[lv[l0]]
            d1 = uv[l1] - uv[l0]; d2 = uv[l2] - uv[l0]
            det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
            okd = np.abs(det) >= 1e-12
            dPdv = (e2 * d1[:, :1] - e1 * d2[:, :1]) / np.where(okd, det, 1.0)[:, None]
            ln = np.linalg.norm(dPdv, axis=1)
            ok = gsel & okd & (ln >= 1e-9)
            gv = dPdv / np.maximum(ln, 1e-15)[:, None]
            LA = long_ax[comp]
            la = LA - nrm * np.sum(LA * nrm, axis=1)[:, None]
            lal = np.linalg.norm(la, axis=1)
            judge = ok & (elong[comp] > 1.5) & (lal > 1e-6)
            cA = np.abs(np.sum(gv * la, axis=1) / np.maximum(lal, 1e-15))
            up = np.array([0, 0, 1.0]) - nrm * nrm[:, 2:3]
            upl = np.linalg.norm(up, axis=1)
            roof = ok & (nrm[:, 2] > 0.2) & (upl > 1e-6)
            cU = np.sum(gv * up, axis=1) / np.maximum(upl, 1e-15)
            for s in GRAIN:
                fs = ok & (slot == s)
                if not fs.any():
                    continue
                d = grain.setdefault(s, dict(area=0.0, judge=0.0, along=0.0, across=0.0, roof=0.0, up=0.0,
                                             down=0.0, scale=[]))
                d["area"] += float(area[fs].sum())
                j = fs & judge
                d["judge"] += float(area[j].sum())
                d["along"] += float(area[j & (cA > 0.7)].sum())
                d["across"] += float(area[j & (cA < 0.3)].sum())
                r = fs & roof
                d["roof"] += float(area[r].sum())
                d["up"] += float(area[r & (cU > 0.7)].sum())
                d["down"] += float(area[r & (cU < -0.7)].sum())
                d["scale"].append(np.median(ln[fs]))
                po = d.setdefault("per_obj", {})
                po[o.name] = [round(float(area[fs].sum()), 3), round(float(area[j].sum()), 3),
                              round(float(area[j & (cA > 0.7)].sum()), 3), round(float(area[r].sum()), 3),
                              round(float(area[r & (cU > 0.7)].sum()), 3)]
        # ---- walked tops
        if mk is not None and ents:
            fb = np.zeros(npo); np.maximum.at(fb, pol, mk[:, 2])
            for k, e in enumerate(ents):
                O = np.array(e["origin"], float); n = np.array(e["out"], float); n[2] = 0; n /= np.linalg.norm(n)
                t = np.array([-n[1], n[0], 0.0])
                rel = cen - O
                a = rel @ n; c = rel @ t; dz = rel[:, 2]
                z = ((np.abs(c) <= e["width"] / 2 + 0.10) & (a >= -1.0) & (a <= 1.5) & (dz >= -0.3) & (dz <= 1.2)
                     & (nrm[:, 2] > 0.7))
                if not z.any():
                    continue
                W = walk[k]
                W["area"] += float(area[z].sum()); W["faces"] += int(z.sum())
                W["b_max"] = max(W["b_max"], float(fb[z].max()))
                bad = z & (fb > 0.05 + 1e-6)
                W["objs"][o.name] = dict(area=round(float(area[z].sum()), 4), b_max=round(float(fb[z].max()), 4),
                                         z_max=round(float(cen[z, 2].max()), 3))
                if bad.any():
                    W["bad_area"] += float(area[bad].sum())
                    W["bad"].append((o.name, round(float(area[bad].sum()), 4), round(float(fb[bad].max()), 3),
                                     round(float(cen[bad, 2].min()), 3), round(float(cen[bad, 2].max()), 3)))
    for s, d in grain.items():
        d["scale"] = float(np.median(d.pop("scale")))
        d["along_pct_of_slot"] = 100 * d["along"] / max(d["area"], 1e-9)
        d["along_pct_of_judged"] = 100 * d["along"] / max(d["judge"], 1e-9)
        d["across_pct_of_judged"] = 100 * d["across"] / max(d["judge"], 1e-9)
        d["unjudged_area"] = d["area"] - d["judge"]
        d["up_pct"] = 100 * d["up"] / max(d["roof"], 1e-9)
        d["down_pct"] = 100 * d["down"] / max(d["roof"], 1e-9)
    worst = sorted(((v["first_lt02"] / max(v["area"], 1e-12), k) for k, v in coll.items()), reverse=True)
    n_over = sum(1 for f, _ in worst if f >= 0.01)
    worst_face = sorted(((v["face_lt02"] / max(v["area"], 1e-12), k) for k, v in coll.items()), reverse=True)
    return dict(file=path, entrances=ents, grain=grain,
                collapsed=dict(objects_ge_1pct=n_over, worst=[(k, round(100 * f, 3)) for f, k in worst[:5]],
                               objects_ge_1pct_wholeface=sum(1 for f, _ in worst_face if f >= 0.01),
                               worst_wholeface=[(k, round(100 * f, 3)) for f, k in worst_face[:3]]),
                walk=walk)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    r = measure(a[0])
    with open(a[1], "w") as f:
        json.dump(r, f, indent=1, default=str)
    print("UVV", a[0])
    for s, d in r["grain"].items():
        print(f"  {s:20s} area {d['area']:8.1f}  along {d['along_pct_of_slot']:5.1f}% of slot, "
              f"{d['along_pct_of_judged']:5.1f}% of judged (unjudged {d['unjudged_area']:.1f} m2), across "
              f"{d['across_pct_of_judged']:4.1f}%  | roof {d['roof']:.1f} m2 up {d['up_pct']:5.1f}% down "
              f"{d['down_pct']:4.1f}%  | m/UV {d['scale']:.2f}")
        un = sorted(((v[0] - v[1], k, v) for k, v in d["per_obj"].items()), reverse=True)[:4]
        print("      most unjudged [area, judged, along, roof, up]:", [(k, v) for _, k, v in un if _ > 0.5])
    print("  collapsed:", r["collapsed"])
    for w in r["walk"]:
        print(f"  walk {w['name']}: {w['faces']} faces {w['area']:.2f} m2 B max {w['b_max']:.3f} bad {w['bad_area']:.3f} m2 {w['bad'][:4]}")
