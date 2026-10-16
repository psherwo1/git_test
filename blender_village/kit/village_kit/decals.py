"""village_kit.decals -- producer note 11: decal anchors.

Sub-2 cm surface relief (daub shrinkage cracks, wood checks, chips, tooling, weathering) is NOT modelled.  Every
building instead exports the places where decals naturally belong, so Unreal PCG can place and vary them by seed:

  * in Blender: a collection DECAL_ANCHORS of empties DA_<type>_<nnn>.  Each empty's -Z axis points INTO the
    surface it decorates (+Z = outward surface normal), +Y is the decal's up direction, and it carries the custom
    properties decal_type, size_w, size_h (metres), surface (palette slot), probability (0-1), seed;
  * as a file: buildings/<id>/decal_anchors.json with the same data (position, normal, up, size, type, surface,
    probability, seed) and a header stating units and axes.

Placement is physically plausible; the helpers below encode the rules (all positions are found by ray-casting the
built meshes, so an anchor always sits ON a real surface and `surface` is the slot of the face it hit):
    base_ring()          damp_rise / moss round the base of a wall, more likely on north (+Y) faces
    tops()               moss / lichen on the up-facing tops of stones, ledges, sills, roof butts
    below_points()       water_streak under sills / drips / wheel and boom ends, rust_stain under ironwork
    above_opening()      soot above openings and smoke holes
    opening_corners()    crack at the corners of openings, under lintels, at settlement points
    wall_scatter()       plaster_patch / repair_patch / crack / grime scattered over a wall face
Aim for about 40-120 anchors per hero building.
"""
import json
import math

import numpy as np

DECAL_TYPES = ("crack", "damp_rise", "moss", "soot", "water_streak", "rust_stain", "plaster_patch",
               "repair_patch", "lichen", "grime")
# default chance PCG uses an anchor of each type
DEFAULT_PROB = {"crack": 0.55, "damp_rise": 0.75, "moss": 0.6, "soot": 0.7, "water_streak": 0.6,
                "rust_stain": 0.7, "plaster_patch": 0.45, "repair_patch": 0.35, "lichen": 0.5, "grime": 0.6}
COLLECTION = "DECAL_ANCHORS"


def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def decal_frame(normal, up_hint=(0.0, 0.0, 1.0)):
    """(right, up, normal) for an anchor: up = up_hint projected into the surface plane (world Z for walls); on
    horizontal surfaces (tops) the hint is replaced by the horizontal direction of the surface position, or +Y."""
    n = _unit(normal)
    u = np.asarray(up_hint, float)
    u = u - np.dot(u, n) * n
    if np.linalg.norm(u) < 1e-3:
        u = np.array([0.0, 1.0, 0.0]) - n[1] * n
        if np.linalg.norm(u) < 1e-3:
            u = np.array([1.0, 0.0, 0.0]) - n[0] * n
    u = _unit(u)
    return np.cross(u, n), u, n


class SurfaceProbe:
    """ray-cast the built meshes (world space) and report the hit point, outward normal and palette slot."""

    def __init__(self, objects):
        from mathutils.bvhtree import BVHTree
        V, T, mats, names = [], [], [], []
        nv = 0
        for ob in objects:
            if ob.type != "MESH":
                continue
            me = ob.data
            me.calc_loop_triangles()
            co = np.zeros(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            M = np.array(ob.matrix_world)
            co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
            lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
            me.loop_triangles.foreach_get("vertices", lt)
            lm = np.zeros(len(me.loop_triangles), np.int64)
            me.loop_triangles.foreach_get("material_index", lm)
            slots = [m.name if m else "" for m in me.materials] or [""]
            V.append(co)
            T.append(lt.reshape(-1, 3) + nv)
            mats.extend(slots[min(i, len(slots) - 1)] for i in lm)
            names.extend([ob.name] * len(lm))
            nv += len(co)
        self.V = np.concatenate(V)
        self.T = np.concatenate(T)
        self.mats = mats
        self.names = names
        self.bvh = BVHTree.FromPolygons(self.V.tolist(), self.T.tolist(), all_triangles=True)

    def cast(self, origin, direction, dist=10.0):
        from mathutils import Vector
        d = _unit(direction)
        hit = self.bvh.ray_cast(Vector(tuple(map(float, origin))), Vector(tuple(map(float, d))), dist)
        if hit[0] is None:
            return None
        n = np.array(hit[1])
        if np.dot(n, d) > 0:                 # face seen from its back: report the side facing the ray
            n = -n
        return dict(pos=np.array(hit[0]), normal=n, surface=self.mats[hit[2]], object=self.names[hit[2]])


class DecalAnchors:
    def __init__(self, prefix=""):
        self.prefix = prefix
        self.items = []

    # ---------------------------------------------------------------------------------------------------------
    def add(self, decal_type, pos, normal, size=(0.5, 0.5), surface="M_stone", probability=None, seed=None,
            up=(0.0, 0.0, 1.0), offset=0.004):
        """one anchor; pos is lifted `offset` off the surface along the normal (no z-fight in previews)."""
        if decal_type not in DECAL_TYPES:
            raise ValueError(f"unknown decal type {decal_type!r}")
        from .palette import check
        check(surface)
        r, u, n = decal_frame(normal, up)
        p = np.asarray(pos, float) + n * offset
        if seed is None:
            seed = (len(self.items) * 7919 + 104729) % 2147483647
        self.items.append(dict(type=decal_type, pos=p, normal=n, up=u, right=r, size=(float(size[0]), float(size[1])),
                               surface=surface,
                               probability=float(DEFAULT_PROB[decal_type] if probability is None else probability),
                               seed=int(seed)))
        return self.items[-1]

    def add_hit(self, decal_type, hit, size, probability=None, seed=None, up=(0.0, 0.0, 1.0), surfaces=None,
                shift_down=0.0):
        """add from a SurfaceProbe hit (skipped if hit is None or its slot is not in `surfaces`).  shift_down moves
        the anchor down its own up axis (a streak hangs BELOW its source)."""
        if hit is None or (surfaces is not None and hit["surface"] not in surfaces):
            return None
        r, u, n = decal_frame(hit["normal"], up)
        return self.add(decal_type, hit["pos"] - u * shift_down, hit["normal"], size, hit["surface"], probability,
                        seed, up)

    def __len__(self):
        return len(self.items)

    def counts(self):
        out = {}
        for it in self.items:
            out[it["type"]] = out.get(it["type"], 0) + 1
        return out

    # ---------------------------------------------------------------------------------------------------------
    def build_collection(self, parent=None, name=COLLECTION):
        """the DECAL_ANCHORS collection of empties (see module doc); returns the number of anchors."""
        import bpy
        from mathutils import Matrix
        if not self.items:
            return 0
        coll = bpy.data.collections.new(name)
        (parent.children if parent is not None else bpy.context.scene.collection.children).link(coll)
        cnt = {}
        for it in self.items:
            cnt[it["type"]] = cnt.get(it["type"], 0) + 1
            ob = bpy.data.objects.new(f"DA_{it['type']}_{cnt[it['type']]:03d}", None)
            ob.empty_display_type = "SINGLE_ARROW"          # the arrow is +Z: it points OUT of the surface
            ob.empty_display_size = max(0.05, 0.5 * min(it["size"]))
            M = np.eye(4)
            M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = it["right"], it["up"], it["normal"], it["pos"]
            ob.matrix_world = Matrix(M.tolist())
            ob["decal_type"] = it["type"]
            ob["size_w"] = it["size"][0]
            ob["size_h"] = it["size"][1]
            ob["surface"] = it["surface"]
            ob["probability"] = it["probability"]
            ob["seed"] = it["seed"]
            coll.objects.link(ob)
            it["name"] = ob.name
        return len(self.items)

    def export_json(self, path, building="", extra=None):
        r6 = lambda v: [round(float(x), 5) for x in v]  # noqa: E731
        data = dict(
            format="village_kit decal anchors v1",
            building=building,
            units="metres",
            space="building-local: origin at the building base centre on the ground datum Z = 0",
            axes=("right-handed, Z up; the principal entrance faces -Y.  normal = outward surface normal (the "
                  "empty's +Z; its -Z points into the surface); up = decal up direction in the surface plane "
                  "(the empty's +Y); size = [width along right, height along up]"),
            decal_types=list(DECAL_TYPES),
            count=len(self.items),
            counts=self.counts(),
            anchors=[dict(name=it.get("name", f"DA_{it['type']}"), type=it["type"], position=r6(it["pos"]),
                          normal=r6(it["normal"]), up=r6(it["up"]), size=[round(it["size"][0], 4),
                                                                         round(it["size"][1], 4)],
                          surface=it["surface"], probability=round(it["probability"], 3), seed=it["seed"])
                     for it in self.items],
        )
        if extra:
            data.update(extra)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        return path


# =================================================================================================================
# placement helpers (physically plausible rules, producer note 11)
# =================================================================================================================
def _north_bias(normal, base, north_gain):
    return float(np.clip(base * (1.0 + north_gain * max(0.0, float(normal[1]))), 0.0, 1.0))


def base_ring(da, probe, center, r_out, azimuths, z, decal_type="damp_rise", size=(0.9, 0.45), surfaces=None,
              north_gain=0.6, rng=None, up_shift=None):
    """damp_rise / moss round the base of a round wall: horizontal rays from r_out toward the axis at height z
    (the anchor's lower edge sits at the wall foot: the decal is shifted up by half its height).  More likely on
    north (+Y) faces."""
    out = []
    for i, az in enumerate(azimuths):
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        zz = z(az) if callable(z) else z
        hit = probe.cast(np.array([center[0], center[1], zz]) + u * r_out, -u, r_out)
        if hit is None or (surfaces is not None and hit["surface"] not in surfaces):
            continue
        w = size[0] * (rng.uniform(0.8, 1.25) if rng is not None else 1.0)
        h = size[1] * (rng.uniform(0.8, 1.3) if rng is not None else 1.0)
        prob = _north_bias(hit["normal"], DEFAULT_PROB[decal_type], north_gain)
        p = hit["pos"] + np.array([0, 0, h / 2 if up_shift is None else up_shift])
        out.append(da.add(decal_type, p, hit["normal"], (w, h), hit["surface"], prob,
                          seed=None if rng is None else int(rng.randint(1 << 30))))
    return out


def tops(da, probe, points, decal_type="lichen", size=(0.3, 0.3), surfaces=None, north_gain=0.5, rng=None,
         min_up=0.5, h_from=0.6):
    """moss / lichen on up-facing tops (stone tops, ledges, sills, shingle butts): vertical rays down at the
    (x, y[, z]) points; accepted only where the surface faces up (normal.z >= min_up)."""
    out = []
    for p in points:
        p = np.asarray(p, float)
        z0 = p[2] + h_from if len(p) > 2 else 20.0
        hit = probe.cast((p[0], p[1], z0), (0, 0, -1), z0 + 1.0)
        if hit is None or hit["normal"][2] < min_up or (surfaces is not None and hit["surface"] not in surfaces):
            continue
        s = rng.uniform(0.75, 1.3) if rng is not None else 1.0
        radial = np.array([p[0], p[1], 0.0])
        prob = _north_bias(np.array([0, p[1] / max(np.hypot(p[0], p[1]), 1e-6), 0]), DEFAULT_PROB[decal_type],
                           north_gain)
        out.append(da.add(decal_type, hit["pos"], hit["normal"], (size[0] * s, size[1] * s), hit["surface"], prob,
                          seed=None if rng is None else int(rng.randint(1 << 30)),
                          up=radial if np.linalg.norm(radial) > 1e-6 else (0, 1, 0)))
    return out


def below_points(da, probe, points, out_dirs, decal_type="water_streak", size=(0.12, 0.6), surfaces=None,
                 drop=0.02, rng=None, reach=0.6):
    """water_streak / rust_stain hanging BELOW a source (sill drip, eave drip, wheel / boom end, hinge, nail,
    ring pull): a ray from `reach` outside the surface (along out_dir) back onto it, `drop` below the source; the
    decal's top edge is at the source (centre shifted down by half its height)."""
    out = []
    for p, od in zip(points, out_dirs):
        od = _unit(od)
        h = size[1] * (rng.uniform(0.8, 1.3) if rng is not None else 1.0)
        o = np.asarray(p, float) + np.array([0, 0, -drop]) + od * reach
        hit = probe.cast(o, -od, reach * 2)
        r = da.add_hit(decal_type, hit, (size[0], h), seed=None if rng is None else int(rng.randint(1 << 30)),
                       surfaces=surfaces, shift_down=h / 2)
        if r is not None:
            out.append(r)
    return out


def above_opening(da, probe, center, out_dir, width, head_z, decal_type="soot", size=None, surfaces=None,
                  rng=None, reach=0.6):
    """soot above an opening (door head, window head, smoke hole): the decal's lower edge sits on the head."""
    od = _unit(out_dir)
    w, h = size if size is not None else (width * 0.9, 0.55)
    o = np.array([center[0], center[1], head_z + h / 2]) + od * reach
    hit = probe.cast(o, -od, reach * 2)
    r = da.add_hit(decal_type, hit, (w, h), seed=None if rng is None else int(rng.randint(1 << 30)),
                   surfaces=surfaces)
    return [r] if r is not None else []


def opening_corners(da, probe, corners, out_dir, decal_type="crack", size=(0.25, 0.35), surfaces=None, rng=None,
                    reach=0.6):
    """cracks starting at the corners of an opening / under a lintel end / at a settlement point; corners are
    world points on (or just in front of) the wall."""
    od = _unit(out_dir)
    out = []
    for c in corners:
        hit = probe.cast(np.asarray(c, float) + od * reach, -od, reach * 2)
        s = rng.uniform(0.8, 1.25) if rng is not None else 1.0
        r = da.add_hit(decal_type, hit, (size[0] * s, size[1] * s),
                       seed=None if rng is None else int(rng.randint(1 << 30)), surfaces=surfaces)
        if r is not None:
            out.append(r)
    return out


def wall_scatter(da, probe, center, r_out, n, z_range, decal_type="plaster_patch", size=((0.3, 0.6), (0.25, 0.5)),
                 surfaces=None, rng=None, az_range=(0.0, 2 * math.pi), avoid=(), min_sep=0.6, tries=40):
    """scatter anchors over a round wall face (horizontal rays toward the axis at random azimuth / height),
    keeping min_sep from each other and from the `avoid` points."""
    rng = rng if rng is not None else np.random.RandomState(1)
    out = []
    placed = [np.asarray(a, float) for a in avoid]
    for _ in range(n * tries):
        if len(out) >= n:
            break
        az = rng.uniform(*az_range)
        z = rng.uniform(*z_range)
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        hit = probe.cast(np.array([center[0], center[1], z]) + u * r_out, -u, r_out)
        if hit is None or (surfaces is not None and hit["surface"] not in surfaces):
            continue
        if any(np.linalg.norm(hit["pos"] - q) < min_sep for q in placed):
            continue
        w = rng.uniform(*size[0])
        h = rng.uniform(*size[1])
        out.append(da.add(decal_type, hit["pos"], hit["normal"], (w, h), hit["surface"],
                          seed=int(rng.randint(1 << 30))))
        placed.append(hit["pos"])
    return out
