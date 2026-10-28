# ---- kit / pier assets
PIERPATH = ASSETS + r"\wooden_pier_picks.blend"
KITPATH = ASSETS + r"\kb3d_picks.blend"
with bpy.data.libraries.load(PIERPATH) as (src, dst):
    dst.objects = list(src.objects)
PIER = {o.name.replace("modular_wooden_pier_", ""): o for o in dst.objects if o}
for im in bpy.data.images:
    if im.source == "FILE" and "modular_wooden_pier" in im.name:
        im.filepath = os.path.join(ASSETS, "textures_pier", os.path.basename(im.filepath))
        im.reload()
with bpy.data.libraries.load(KITPATH) as (src, dst):
    dst.objects = list(src.objects)
KIT = {o.name[5:]: o for o in dst.objects if o}
print("PIER parts", sorted(PIER), "KIT picks", sorted(KIT), flush=True)
for me_ in (o.data for o in KIT.values()):
    pass
KMAP = {"BoatBodyPanelsDarkWornB": "hull2", "BoatBodyPanelsWhiteWornB": "hull3", "BoatBodyPanelsWornA": "hull"}
KMAT = {
    "hull": tex_mat("K_hull", WOOD_IMG, (0.62, 0.20, 0.11), 0.65, 1.8),
    "hull2": tex_mat("K_hull2", WOOD_IMG, (0.22, 0.17, 0.14), 0.65, 1.8),
    "hull3": tex_mat("K_hull3", WOOD_IMG, (0.70, 0.66, 0.55), 0.65, 1.8),
    "metal": tex_mat("K_iron", METAL_IMG, (0.30, 0.28, 0.27), 0.6, 1.5),
    "rope": simple("K_rope", (0.30, 0.22, 0.12), 0.95, 0.6),
    "net": simple("K_net", (0.10, 0.085, 0.06), 0.95),
    "wood": tex_mat("K_wood", WOOD_IMG, (0.55, 0.46, 0.38), 0.85, 1.5),
    "buoy": simple("K_buoy", (0.55, 0.12, 0.06), 0.7),
}
for k, o in KIT.items():
    me = o.data
    for i, sl in enumerate(list(me.materials)):
        n = sl.name.replace("KB3D_SOL_", "") if sl else ""
        if n in KMAP:
            nm = KMAP[n]
        elif "Rope" in n:
            nm = "rope"
        elif "Net" in n:
            nm = "net"
        elif "Metal" in n or "Steel" in n:
            nm = "metal"
        elif "Airship" in n:
            nm = "buoy"
        elif "Wood" in n:
            nm = "wood"
        else:
            nm = "hull2"
        me.materials[i] = KMAT[nm]
    for p in me.polygons:
        p.use_smooth = True


def kit_obj(key, loc, rz, sc, name=None):
    o = bpy.data.objects.new(name or "K_" + key, KIT[key].data)
    scn.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Diagonal((sc, sc, sc, 1.0))
    return o


def vminmax(me, ax):
    a = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3)
    return float(a[:, ax].min()), float(a[:, ax].max())


PS = 0.85          # pier scale: deck ~2.1 m wide
PDX = 0.97         # local x centre of the pier modules
PDZ = 2.68         # local z of the pier deck top
DECK = 1.0         # world deck height


def pier(base, rz, L, tall_at=None, name="PIER"):
    """modular wooden pier: section_01 (shore end), alternating 02/03, section_04 (tip); modules are chained by their y extents"""
    seq = ["section_01"]
    nmid = max(2, int(L / (PS * 2.95)) - 1)
    seq += ["section_02" if i % 2 == 0 else "section_03" for i in range(nmid)] + ["section_04"]
    cur = 0.0
    starts = []
    for i, s in enumerate(seq):
        y0, y1 = vminmax(PIER[s].data, 1)
        o = bpy.data.objects.new("%s_%02d" % (name, i), PIER[s].data)
        scn.collection.objects.link(o)
        o.matrix_world = (Matrix.Translation(base) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(PS, 4)
                          @ Matrix.Translation((-PDX, cur - y0, -PDZ)))
        starts.append(cur)
        cur += (y1 - y0) - 0.45
    if tall_at is not None and tall_at < len(seq):
        y0, _ = vminmax(PIER["section_05"].data, 1)
        o = bpy.data.objects.new(name + "_gate", PIER["section_05"].data)
        scn.collection.objects.link(o)
        o.matrix_world = (Matrix.Translation(base) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Scale(PS, 4)
                          @ Matrix.Translation((-PDX, starts[tall_at] - y0, -PDZ)))
    return cur * PS, starts


def pier_pt(base, rz, dist, side=0.0):
    d = Vector((-math.sin(rz), math.cos(rz), 0))
    s = Vector((math.cos(rz), math.sin(rz), 0))
    return Vector(base) + d * dist + s * side


def quad_from_dir(dx, dy):
    return math.atan2(-dx, dy)


# quay promenade deck (planks) + rounded bollards
for phi in range(100, 262, 5):
    x, y = pol(32.2, phi)
    box("plank", (x, y, 0.8), (3.0, 3.6, 0.3), math.radians(phi + 90))
    if phi % 10 == 0:
        px, py = pol(31.0, phi)
        cyl("wood", (px, py, -0.2), 0.17, 2.4, seg=10)
for phi in range(105, 258, 9):
    px, py = pol(31.5, phi)
    cyl("wood", (px, py, 1.22), 0.16, 0.55, seg=12)
    ell("wood", (px, py, 1.5), (0.2, 0.2, 0.15), seg=12)
    cyl("iron", (px, py, 1.12), 0.2, 0.05, seg=12)
# piers from the modular wooden pier
PIERS = [(205, 22.0, 0), (155, 16.5, 2), (235, 13.5, None), (125, 11.5, None)]
PIER_INFO = []
for k, (phi, L, tall) in enumerate(PIERS):
    d = (-math.cos(math.radians(phi)), -math.sin(math.radians(phi)))
    rz = quad_from_dir(*d)
    bx, by = pol(32.4, phi)
    ln, st = pier((bx, by, DECK), rz, L, tall_at=None if tall is None else 2 + tall, name="PIER%d" % k)
    PIER_INFO.append(((bx, by), rz, ln))
# fjord jetty on the south ribbon (runs east)
JB = (float(shore22(-48)) - 3.0, -48.0)
ln, st = pier((JB[0], JB[1], DECK), quad_from_dir(1.0, 0.0), 18.0, name="JETTY")
PIER_INFO.append((JB, quad_from_dir(1.0, 0.0), ln))
# rope ladders and buoys at pier tips
for (bx_by, rz, ln) in PIER_INFO:
    p = pier_pt((bx_by[0], bx_by[1], 0), rz, ln - 0.6, 1.15)
    kit_obj("ladder", (p.x, p.y, DECK - 1.25), rz, 0.42, "LADDER")
    for dd in (0.35, 0.7):
        p = pier_pt((bx_by[0], bx_by[1], 0), rz, ln * dd, 1.3)
        kit_obj("buoyA" if dd < 0.5 else "buoyB", (p.x, p.y, DECK + 0.3), rng.uniform(0, 6), 1.0, "BUOY")# kit boats (moored in the bay)
for (c, rz, sc, tint) in (((6.0, -11.0), 100, 0.32, "a"), ((-1.0, 13.0), 80, 0.28, "b"), ((20.0, -26.0), 70, 0.26, "c")):
    kit_obj("boat", (c[0], c[1], -0.8 + 3.76 * sc), math.radians(rz), sc, "KBOAT")
# netting racks + anchor on the quay
for phi in (128, 188, 246):
    x, y = pol(34.6, phi)
    z0 = 0.95
    tang = math.radians(phi + 90)
    for sd in (-1.5, 1.5):
        cyl("wood", (x + sd * math.cos(tang), y + sd * math.sin(tang), z0 + 1.0), 0.07, 2.0, seg=8)
    cyl("wood", (x, y, z0 + 1.95), 0.05, 3.2, rz=tang, rx=math.pi / 2 * 0, seg=8)
    BM["wood"]  # noqa
    n = kit_obj("netA" if phi != 188 else "netB", (x, y, z0 + 1.95 - 0.8), tang, 1.5, "NET")
ax, ay = pol(33.4, 150)
kit_obj("anchor", (ax, ay, 1.05), 0.7, 0.55, "ANCHOR")


def rowboat(c, rz, L, key):
    """lofted open rowing boat with thickness, thwarts and two oars"""
    bm = bmesh.new()
    N, J = 12, 4
    rows_ = []
    for i in range(N + 1):
        u = i / N * 2 - 1
        w = 0.5 * L * 0.30 * max(1e-3, (1 - abs(u) ** 2.2)) ** 0.6
        hg = 0.34 * (1 + 0.5 * u ** 2 * (1.3 if u > 0 else 1.0))
        dp = 0.34 * (1 - 0.8 * abs(u) ** 3)
        r = []
        for j in range(-J, J + 1):
            s = j / J
            r.append(bm.verts.new((u * L / 2, s * w, (hg - dp) + dp * abs(s) ** 1.5 + 0.0 * s)))
        rows_.append(r)
    for i in range(N):
        for j in range(2 * J):
            try:
                bm.faces.new((rows_[i][j], rows_[i + 1][j], rows_[i + 1][j + 1], rows_[i][j + 1]))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.04)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Rotation(math.radians(rz), 4, "Z"), verts=bm.verts[:])
    tmp = bpy.data.meshes.new("tmp")
    bm.to_mesh(tmp)
    bm.free()
    BM[key].from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    ang = math.radians(rz)
    ca, sa = math.cos(ang), math.sin(ang)
    for off in (-0.45, 0.2):
        wx = L * 0.15
        box("plank", (c[0] + off * ca, c[1] + off * sa, c[2] + 0.34 * 0.9), (0.22, wx * 2.2, 0.04), ang)
    for sd in (-1, 1):
        cyl("wood", (c[0] - 0.12 * ca - sd * 0.62 * sa, c[1] - 0.12 * sa + sd * 0.62 * ca, c[2] + 0.55), 0.02, 2.0, rz=ang, rx=0.5 * sd, seg=6)


# row boats (several kinds)
rows = [((-3.5, -22.0), 75), ((-10.0, -17.5), 55), ((29.0, -44.0), 95), ((34.0, -53.0), 80), ((-6.5, -2.0), 70), ((-13.5, -19.0), 60), ((-9.0, 24.0), 110),
        ((8.0, 30.0), 100), ((20.0, 14.0), 85), ((-26.0, 1.5), 12), ((-22.5, -12.0), 40)]
for i, (c, rz) in enumerate(rows):
    rowboat((c[0], c[1], 0.12), rz, float(rng.uniform(3.6, 4.6)), ("hull", "hull2", "hull3")[i % 3])
for c, rz in (((70.0, 70.0), 80), ((95.0, 160.0), 100), ((60.0, 230.0), 75)):
    rowboat((c[0], c[1], 0.12), rz, 4.0, "hull2")
# hay, woodpiles, well, crates
for (R, phi) in ((92, 130), (95, 160), (95, 212), (90, 240), (98, 180), (96, 118)):
    x, y = pol(R, phi)
    z = gz(x, y)
    cyl("hay", (x, y, z + 1.0), 1.4, 2.0, r2=1.2, seg=14)
    cyl("hay", (x, y, z + 2.5), 1.2, 1.4, r2=0.05, seg=14)
for (x, y, rz) in ((-30.0, -27.0, 0.3), (-41.0, 19.0, 1.0), (-14.0, -34.5, 0.3), (-16.0, -55.0, 0.5), (-45.0, -2.0, 2.0), (-12.0, 49.0, 0.2), (3.0, 66.0, 1.2)):
    z = gz(x, y)
    for row, n in enumerate((6, 5, 4)):
        for k in range(n):
            lx = (k - (n - 1) / 2) * 0.28
            cyl("wood", (x + lx * math.cos(rz), y + lx * math.sin(rz), z + 0.17 + row * 0.26), 0.13, 1.5, rz=rz + math.pi / 2, rx=math.pi / 2, seg=8)
wx, wy = pol(35.0, 168)
wz = gz(wx, wy)
cyl("stone", (wx, wy, wz + 0.45), 1.0, 0.9, seg=16)
for sx in (-0.9, 0.9):
    box("plank", (wx + sx, wy, wz + 1.5), (0.14, 0.14, 2.0))
box("plank", (wx, wy, wz + 2.5), (2.2, 0.16, 0.14))
cyl("plank", (wx, wy, wz + 2.9), 1.5, 0.7, seg=4, r2=0.05, rz=math.pi / 4)
# barrels / crates on the quay
for k in range(14):
    phi = rng.uniform(112, 248)
    x, y = pol(rng.uniform(32.5, 34.3), phi)
    if k % 2:
        cyl("wood", (x, y, 0.95 + 0.4), 0.32, 0.8, seg=12)
        for zz in (0.2, 0.62):
            cyl("iron", (x, y, 0.95 + zz), 0.335, 0.05, seg=12)
    else:
        box("plank", (x, y, 0.95 + 0.3), (0.7, 0.7, 0.6), rng.uniform(0, 3))


def figure(x, y, z, kk, hat=True):
    cyl("legs", (x, y, z + 0.42), 0.13, 0.84, seg=8, r2=0.11)
    cyl(kk, (x, y, z + 1.12), 0.21, 0.55, seg=10, r2=0.17)
    ell(kk, (x, y, z + 1.42), (0.17, 0.17, 0.12), seg=10)
    ell(kk, (x, y, z + 0.84), (0.21, 0.21, 0.1), seg=10)
    ell("skin", (x, y, z + 1.62), (0.105, 0.105, 0.125), seg=10)
    if hat:
        ell("legs", (x, y, z + 1.68), (0.115, 0.115, 0.07), seg=8)
    ang = float(rng.uniform(0, 6.28))
    for sd in (-1, 1):
        cyl(kk, (x + sd * 0.25 * math.cos(ang), y + sd * 0.25 * math.sin(ang), z + 1.2), 0.05, 0.6, seg=6)


FIGS = ["fig1", "fig2", "fig3", "fig4", "fig5"]
for i, (x, y) in enumerate(((-12.5, -26.5), (-2.5, -25.5), (-16.0, -33.0), (-21.5, -9.0), (-27.5, -4.0), (-20.0, -20.0), (-26.0, 14.0), (-3.5, -28.0))):
    figure(x, y, gz(x, y), FIGS[i % 5])
for (phi, R) in ((150, 33.0), (183, 34.0), (214, 33.4)):
    px, py = pol(R, phi)
    figure(px, py, 0.95, FIGS[(phi // 7) % 5])
# fences
FENCES = [[pol(98, p) for p in range(120, 252, 6)], [pol(112, p) for p in range(125, 240, 6)], [(11.5, 47), (11.5, 57)],
          [(-22, -58), (-16, -56), (-12, -57)], [(-20, 30), (-30, 37), (-38, 38)]]
for fl in FENCES:
    for a, b in zip(fl[:-1], fl[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 2.2))
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for k in range(n + 1):
            t = k / n
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            cyl("wood", (px, py, gz(px, py) + 0.55), 0.06, 1.1, seg=6)
        for zz in (0.45, 0.85):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            box("plank", (mx, my, gz(mx, my) + zz), (L, 0.05, 0.08), ang)


# rocks: displaced subdivided icospheres with the lichened rock texture (smooth shaded)
def rock2(c, r, sub=2, flat_=0.6):
    ph = rng.uniform(0, 6.28, 6)
    res = bmesh.ops.create_icosphere(BM["rock"], subdivisions=sub, radius=1.0)
    sx, sy = rng.uniform(0.8, 1.5), rng.uniform(0.8, 1.4)
    rz = float(rng.uniform(0, 6.28))
    for v in res["verts"]:
        p = v.co.copy()
        d = (1 + 0.28 * math.sin(2.3 * p.x + ph[0]) * math.sin(2.1 * p.y + ph[1]) + 0.16 * math.sin(4.7 * p.z + ph[2] + 3 * p.x)
             + 0.07 * math.sin(9.0 * p.x + ph[3]) * math.sin(8.0 * p.y + ph[4]) + rng.uniform(-0.03, 0.03))
        q = p * d
        q.z = max(q.z, -0.45) * flat_
        v.co = Matrix.Rotation(rz, 3, "Z") @ Vector((q.x * sx * r, q.y * sy * r, q.z * r)) + Vector(c)


for k in range(70):
    phi = rng.uniform(95, 265)
    x, y = pol(rng.uniform(30.0, 33.5), phi)
    rock2((x, y, gz(x, y) + 0.05), rng.uniform(0.25, 0.7), 2, 0.7)
for k in range(110):
    y = rng.uniform(-100, 420)
    x = float(shoreE(y)) + rng.uniform(-4, 16)
    zg = gz(x, y)
    rock2((x, y, zg + 0.2), rng.uniform(1.0, 6.0) * (1.0 + 1.5 * (rng.rand() < 0.15)), 3, 0.65)
for k in range(60):     # boulders up the cliff face
    y = rng.uniform(-60, 380)
    x = float(shoreE(y)) + rng.uniform(15, 110)
    rock2((x, y, gz(x, y) + 0.5), rng.uniform(3.0, 12.0), 3, 0.6)
for k in range(25):
    y = rng.choice([-1, 1]) * rng.uniform(40, 110)
    x = float(shore22(y)) - rng.uniform(0, 4)
    rock2((x, y, gz(x, y) + 0.1), rng.uniform(0.5, 1.6), 2, 0.65)
# trees (merged mesh, per-tree tint via the 'tcol' attribute, 3 species)
pts = []
avoid = np.array([(p[1], p[2]) for p in PL])
fcent = np.array([(f[0], f[1]) for f in FIELDS])


def ok_tree(x, y):
    if np.min(np.hypot(avoid[:, 0] - x, avoid[:, 1] - y)) < 11:
        return False
    if np.min(np.hypot(fcent[:, 0] - x, fcent[:, 1] - y)) < 17:
        return False
    if math.hypot(x - BX, y - BY) < 68:
        return False
    return True


tries = 0
while len(pts) < 1700 and tries < 50000:
    tries += 1
    r = rng.rand()
    if r < 0.62:
        x, y = rng.uniform(-340, -100), rng.uniform(-200, 600)
        if x > -135 and rng.rand() < 0.5 and y < 130:
            continue
    elif r < 0.82:
        x, y = rng.uniform(-110, 8), rng.uniform(135, 560)
    elif r < 0.9:
        x, y = rng.uniform(-120, -60), rng.uniform(-190, -110)
    else:
        x, y = rng.uniform(EAST + 1, EAST + 60), rng.uniform(-150, 560)
    if not ok_tree(x, y):
        continue
    z = gz(x, y)
    if z < 1.2 or z > 80:
        continue
    pts.append((x, y, z))
colL = BM["tree"].loops.layers.color["tcol"]


def paint(verts, col):
    for v in verts:
        for lp in v.link_loops:
            lp[colL] = (col[0], col[1], col[2], 1.0)


for (x, y, z) in pts:
    sp = rng.rand()
    sc_ = float(np.exp(rng.normal(0, 0.28)))
    sc_ = min(max(sc_, 0.55), 1.7)
    hgt = rng.uniform(6.0, 13.0) * (1.0 + 0.4 * smooth(-100, -250, x)) * sc_
    lean = Vector((rng.normal(0, 0.04), rng.normal(0, 0.04), 0))
    if sp < 0.60:        # spruce, 3-5 tiers
        w = hgt * rng.uniform(0.18, 0.32)
        g = rng.uniform(0.75, 1.3)
        col = (0.55 * g, 0.9 * g, 0.55 * g)
        cyl("trunk", (x, y, z + hgt * 0.1), 0.16 * hgt / 8, hgt * 0.2, seg=6)
        nt_ = int(rng.integers(3, 6))
        for t in range(nt_):
            zb = z + hgt * (0.1 + 0.8 / nt_ * t)
            rr = w * (1.0 - 0.75 * t / nt_)
            vc = len(BM["tree"].verts)
            bmesh.ops.create_cone(BM["tree"], cap_ends=False, cap_tris=False, segments=int(rng.integers(7, 11)), radius1=rr, radius2=0.04 * rr, depth=hgt * 0.8 / nt_ * 1.5,
                                  matrix=M((x + lean.x * t, y + lean.y * t, zb + hgt * 0.5 / nt_), float(rng.uniform(0, 6.28))))
            paint(list(BM["tree"].verts)[vc:], col)
    elif sp < 0.72:      # tall narrow fir
        w = hgt * 0.11
        g = rng.uniform(0.6, 0.95)
        cyl("trunk", (x, y, z + hgt * 0.07), 0.12 * hgt / 8, hgt * 0.14, seg=5)
        vc = len(BM["tree"].verts)
        bmesh.ops.create_cone(BM["tree"], cap_ends=False, cap_tris=False, segments=7, radius1=w, radius2=0.03, depth=hgt * 0.95, matrix=M((x, y, z + hgt * 0.55)))
        paint(list(BM["tree"].verts)[vc:], (0.45 * g, 0.75 * g, 0.5 * g))
    else:                # broadleaf: trunk + clustered blobs
        hh = hgt * 0.75
        cyl("trunk", (x, y, z + hh * 0.3), 0.2 * hh / 6, hh * 0.6, seg=6, r2=0.12 * hh / 8)
        k_ = rng.rand()
        col = (1.0, 1.15, 0.5) if k_ < 0.4 else ((1.5, 0.95, 0.3) if k_ < 0.55 else (0.8, 1.2, 0.6))
        col = tuple(c * rng.uniform(0.8, 1.2) for c in col)
        for bl in range(int(rng.integers(3, 6))):
            rr = hh * rng.uniform(0.2, 0.32)
            off = Vector((rng.normal(0, 0.18 * hh), rng.normal(0, 0.18 * hh), rng.uniform(0.62, 0.95) * hh))
            vc = len(BM["tree"].verts)
            res = bmesh.ops.create_icosphere(BM["tree"], subdivisions=2, radius=1.0, matrix=M((x + off.x, y + off.y, z + off.z), 0, (rr, rr, rr * 0.8)))
            for v in res["verts"]:
                v.co += Vector(rng.uniform(-0.12, 0.12, 3)) * rr
            paint(res["verts"], col)
print("TREES", len(pts), flush=True)

