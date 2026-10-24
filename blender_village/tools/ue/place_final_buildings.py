"""Import the 4 final village buildings (Nanite, village materials) and place one copy of each in the prototype level.

Run it in YOUR editor:  save the level first (Ctrl+S), then Tools > Execute Python Script > this file
(ArtSource/VillageTextures/place_final_buildings.py).  Wait for the log line  "Village: DONE".
Works headless too:  UnrealEditor.exe <proj>.uproject -ExecCmds="py <path>/place_final_buildings.py" -unattended

Buildings (GLBs with the Mask as COLOR_0, made by export/ue_buildings/final):
    hilltop_keep, v2_tiered_hall, v5_harbour_house, wattle_roundhut
Folder with the GLBs: env VILLAGE_FINAL_DIR, else  ../Buildings_final  (next to this script's folder), else the repo's
export/ue_buildings/final.  Layout  <dir>/<id>/<id>.glb .

What it does (every step logs a "Village:" line):
  1. refuses to run if any level/package has unsaved changes (nothing is changed then); checks the MI_M_* instances exist;
  2. switches to an EMPTY untitled level (a long game-thread stall in a busy level once crashed a GPU), imports each GLB one at a
     time into /Game/Village/Buildings/<id>/ as ONE static mesh, Nanite ON at full quality (keep 100 % triangles, no trimming,
     small fallback mesh), assigns MI_<slot> by slot NAME, deletes the importer's placeholder materials, saves the mesh;
  3. reopens the target level (env VILLAGE_TARGET_LEVEL, default /Game/Levels/L_World_Prototype), deletes the actors of an earlier
     run (actor folder "VillageFinal" / tag VillageFinal: so running twice never duplicates), spawns one StaticMeshActor per
     building in a tidy row in front of the PlayerStart (or at the origin), doors turned towards the PlayerStart, Z snapped to the
     ground with a line trace (fallback Z 0 with a warning), folder VillageFinal, labels Village_<id>, and SAVES the level.
Optional env: VILLAGE_ANCHOR="x,y" (cm; row centre instead of the PlayerStart), VILLAGE_REIMPORT=1 (re-import even when the
mesh asset is already good), VILLAGE_ONLY="id1,id2", VILLAGE_NO_SAVE=1, VILLAGE_GAP_CM=3500.
"""
import math
import os
import sys
import time

import unreal

IDS = ["hilltop_keep", "v2_tiered_hall", "v5_harbour_house", "wattle_roundhut"]
MAT_DIR = "/Game/Village/Materials"
DEST_ROOT = "/Game/Village/Buildings"
FOLDER = "VillageFinal"
TAG = "VillageFinal"
TARGET_LEVEL = os.environ.get("VILLAGE_TARGET_LEVEL", "/Game/Levels/L_World_Prototype")
EAL = unreal.EditorAssetLibrary
_DONE = []          # filled when the job ends ("ok" or "error"); used by test drivers


def log(m):
    unreal.log("Village: " + str(m))


def warn(m):
    unreal.log_warning("Village: " + str(m))


try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()


def glb_dir():
    cands = [os.environ.get("VILLAGE_FINAL_DIR"), os.path.join(HERE, "..", "Buildings_final"),
             os.path.join(HERE, "..", "..", "export", "ue_buildings", "final"),
             r"C:\UnrealProjects\Prototype\ArtSource\Buildings_final"]
    for c in cands:
        if c and all(os.path.exists(os.path.join(c, i, i + ".glb")) for i in selected_ids()):
            return os.path.abspath(c)
    raise RuntimeError("Village: cannot find <dir>/<id>/<id>.glb for " + ", ".join(selected_ids()) +
                       " (set VILLAGE_FINAL_DIR). Nothing was changed.")


def selected_ids():
    only = os.environ.get("VILLAGE_ONLY")
    return [i for i in IDS if not only or i in only.split(",")]


# ------------------------------------------------------------------------------------------------ level helpers
def current_level():
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        return w.get_path_name().split(".")[0] if w else None
    except Exception:  # noqa
        return None


def editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def dirty_packages():
    try:
        return [str(p) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    except Exception:  # noqa
        return []


# ------------------------------------------------------------------------------------------------ import helpers
def start_import(path, bid):
    dest = f"{DEST_ROOT}/{bid}"
    if EAL.does_directory_exist(dest):
        EAL.delete_directory(dest)            # clean re-import (the importer would keep stale material slots otherwise)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", False)
    log(f"importing {path} -> {dest} ({os.path.getsize(path)/1e6:.0f} MB; about 1-3 minutes for 1 M triangles)")
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return dest


def find_meshes(dest):
    out = []
    if not EAL.does_directory_exist(dest):
        return out
    for a in EAL.list_assets(dest, recursive=True):
        if EAL.find_asset_data(a).asset_class_path.asset_name == "StaticMesh":
            out.append(a)
    return out


def apply_materials(mesh):
    ok, missing = [], []
    for i, sm in enumerate(mesh.static_materials):
        slot = str(sm.material_slot_name)
        mi = EAL.load_asset(f"{MAT_DIR}/MI_{slot}")
        if mi is None:
            missing.append(slot)
            continue
        mesh.set_material(i, mi)
        ok.append(slot)
    return ok, missing


NANITE_WANT = [          # (candidate python names, value): full quality, nothing trimmed
    (("enabled",), True),
    (("keep_percent_triangles", "percent_triangles"), 1.0),
    (("trim_relative_error",), 0.0),
    (("fallback_percent_triangles", "fallback_triangle_percent"), 0.05),
    (("preserve_area",), False),
    (("normal_precision",), 12),
]


def set_nanite_max(mesh):
    """Nanite on, keep 100 % of the triangles, no trimming, tiny fallback mesh (only used for ray tracing / non-Nanite)."""
    ns = mesh.get_editor_property("nanite_settings")
    for names, val in NANITE_WANT:
        for n in names:
            try:
                ns.set_editor_property(n, val)
                break
            except Exception:  # noqa
                continue
        else:
            warn(f"Nanite setting {names[0]} not available in this engine build (left at default)")
    mesh.set_editor_property("nanite_settings", ns)
    # full precision UVs (the metric UVs reach 20+ units), no lightmap UVs (Lumen), nothing else touched
    try:
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        bs = sub.get_lod_build_settings(mesh, 0)
        bs.set_editor_property("use_full_precision_u_vs", True)
        bs.set_editor_property("generate_lightmap_u_vs", False)
        sub.set_lod_build_settings(mesh, 0, bs)
    except Exception as e:  # noqa
        warn(f"build settings not changed ({e})")
    ns = mesh.get_editor_property("nanite_settings")
    return ns


def nanite_report(mesh):
    ns = mesh.get_editor_property("nanite_settings")
    d = {}
    for n in ("enabled", "keep_percent_triangles", "trim_relative_error", "fallback_percent_triangles", "preserve_area",
              "position_precision", "normal_precision"):
        try:
            d[n] = ns.get_editor_property(n)
        except Exception:  # noqa
            pass
    return d


def mesh_ok(mesh):
    """True when an already imported mesh needs no re-import."""
    try:
        if not mesh.get_editor_property("nanite_settings").enabled:
            return False
        for sm in mesh.static_materials:
            mi = sm.material_interface
            if mi is None or not mi.get_name().startswith("MI_"):
                return False
        return vertex_colours_present(mesh) is not False
    except Exception:  # noqa
        return False


def asset_tags(mesh):
    """Registry tags of the saved mesh: triangles, vertices, vertex colours, Nanite."""
    out = {}
    try:
        ad = EAL.find_asset_data(mesh.get_path_name().split(".")[0])
        for n in ("Triangles", "Vertices", "HasVertexColors", "NaniteEnabled", "LODs", "NaniteTriangles"):
            r = ad.get_tag_value(n)
            if isinstance(r, tuple):
                r = r[1] if r[0] else None
            if r not in (None, ""):
                out[n] = str(r)
    except Exception as e:  # noqa
        out["error"] = str(e)
    return out


def vertex_colours_present(mesh):
    t = asset_tags(mesh)
    if "HasVertexColors" in t:
        return t["HasVertexColors"].lower() in ("true", "1")
    try:
        return bool(mesh.get_editor_property("has_vertex_colors"))
    except Exception:  # noqa
        return None


def finish_mesh(dest, bid):
    paths = find_meshes(dest)
    meshes = [EAL.load_asset(p) for p in paths]
    meshes.sort(key=lambda m: -(m.get_bounding_box().max - m.get_bounding_box().min).length())
    if len(meshes) > 1:
        warn(f"{bid}: {len(meshes)} static meshes imported; using the biggest")
    mesh = meshes[0]
    bb = mesh.get_bounding_box()
    log(f"{bid}: imported {mesh.get_path_name().split('.')[0]}; size cm {bb.max - bb.min}, min z {bb.min.z:.0f}")
    ok, missing = apply_materials(mesh)
    log(f"{bid}: material slots assigned: {ok}")
    if missing:
        warn(f"{bid}: slots with no MI_ instance (left as imported): {missing}")
    set_nanite_max(mesh)
    mdir = dest + "/Materials"
    if EAL.does_directory_exist(mdir):
        EAL.delete_directory(mdir)             # importer placeholder materials are no longer used
    EAL.save_loaded_asset(mesh)
    log(f"{bid}: Nanite {nanite_report(mesh)}; vertex colours (Mask) present: {vertex_colours_present(mesh)}; "
        f"asset tags {asset_tags(mesh)}")
    try:
        ns = mesh.get_editor_property("nanite_settings")
        log(f"{bid}: all Nanite setting fields: {[p for p in dir(ns) if not p.startswith('_') and not callable(getattr(ns, p))]}")
    except Exception:  # noqa
        pass
    return mesh


# ------------------------------------------------------------------------------------------------ placement helpers
def all_actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())


def remove_old_actors():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in all_actors():
        try:
            if str(a.get_folder_path()) == FOLDER or TAG in [str(t) for t in a.tags]:
                sub.destroy_actor(a)
                n += 1
        except Exception:  # noqa
            continue
    log(f"removed {n} actors of an earlier run")
    return n


def find_anchor():
    """(x, y, forward_x, forward_y) of the row centre: 45 m in front of the PlayerStart, or the origin."""
    env = os.environ.get("VILLAGE_ANCHOR")
    if env:
        x, y = [float(v) for v in env.split(",")]
        log(f"anchor from VILLAGE_ANCHOR: {x}, {y}")
        return x, y, 0.0, 1.0
    for a in all_actors():
        if isinstance(a, unreal.PlayerStart):
            loc, rot = a.get_actor_location(), a.get_actor_rotation()
            yaw = math.radians(rot.yaw)
            fx, fy = math.cos(yaw), math.sin(yaw)
            log(f"PlayerStart '{a.get_actor_label()}' at ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f}) yaw {rot.yaw:.0f}")
            return loc.x + fx * 4500.0, loc.y + fy * 4500.0, fx, fy
    warn("no PlayerStart loaded in the level: the row is centred on the world origin")
    return 0.0, 0.0, 0.0, -1.0


def ground_z(x, y, z_hint):
    """Height of the ground below (x, y): line trace, then landscape height, else None."""
    world = editor_world()
    try:
        for trace_complex in (True, False):
            r = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z_hint + 500000.0),
                                                       unreal.Vector(x, y, z_hint - 500000.0),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, trace_complex, [],
                                                       unreal.DrawDebugTrace.NONE, True)
            hit = None
            if r:
                if isinstance(r, tuple):
                    ok, hit_result = r[0], r[-1] if len(r) > 1 else None
                    hit = hit_result if ok else None
                else:
                    hit = r
            if hit is not None:
                try:
                    loc = hit.get_editor_property("location")
                except Exception:  # noqa
                    loc = hit.to_tuple()[4] if hasattr(hit, "to_tuple") else None
                if loc is not None:
                    return float(loc.z)
    except Exception as e:  # noqa
        warn(f"line trace failed ({e})")
    try:
        for a in all_actors():
            if isinstance(a, unreal.LandscapeProxy):
                h = a.get_height_at_location(unreal.Vector(x, y, 0.0))
                if h is not None and not math.isnan(float(h)):
                    return float(h)
    except Exception as e:  # noqa
        warn(f"landscape height lookup failed ({e})")
    return None


def place_all(meshes):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ax, ay, fx, fy = find_anchor()
    rx, ry = -fy, fx                                    # row direction: perpendicular to the view direction
    yaw = math.degrees(math.atan2(fx, -fy))             # building door (UE +Y) turned towards the PlayerStart
    gap = float(os.environ.get("VILLAGE_GAP_CM", "3500"))
    half = []
    for bid, m in meshes:
        bb = m.get_bounding_box()
        half.append(max(bb.max.x - bb.min.x, bb.max.y - bb.min.y) * 0.5)
    centres, pos = [], 0.0
    for i, h in enumerate(half):
        pos += (0.0 if i == 0 else max(5000.0, half[i - 1] + h + gap))
        centres.append(pos)
    mid = (centres[0] + centres[-1]) * 0.5
    placed = []
    for (bid, m), c in zip(meshes, centres):
        x, y = ax + rx * (c - mid), ay + ry * (c - mid)
        z = ground_z(x, y, 0.0)
        if z is None:
            warn(f"{bid}: no ground found below ({x:.0f}, {y:.0f}) (level part not loaded / no collision): Z = 0")
            z = 0.0
        actor = sub.spawn_actor_from_object(m, unreal.Vector(x, y, z), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        actor.set_actor_label(f"Village_{bid}")
        actor.set_folder_path(FOLDER)
        actor.tags = [TAG]
        log(f"placed Village_{bid} at ({x:.0f}, {y:.0f}, {z:.0f}) yaw {yaw:.0f} in folder {FOLDER}")
        placed.append(actor)
    return placed


def save_level():
    if os.environ.get("VILLAGE_NO_SAVE") == "1":
        warn("VILLAGE_NO_SAVE=1: level not saved")
        return
    try:
        ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        log(f"level saved: {ok}")
        if not ok:
            raise RuntimeError("save_current_level returned False")
    except Exception as e:  # noqa
        warn(f"save_current_level failed ({e}); trying save_dirty_packages")
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        log("dirty packages saved")


# ------------------------------------------------------------------------------------------------ the job (generator)
def job(done_flag):
    ids = selected_ids()
    d = glb_dir()
    log(f"GLB folder: {d}; level {TARGET_LEVEL}; buildings {ids}")
    dp = dirty_packages()
    if dp:
        raise RuntimeError("Village: the open level has unsaved changes - save it (Ctrl+S) and run the script again. "
                           f"Nothing was changed. ({dp[:3]})")
    if not EAL.does_asset_exist(f"{MAT_DIR}/MI_M_stone"):
        raise RuntimeError("Village: /Game/Village/Materials/MI_M_* not found - run build_village_materials.py first")
    if not EAL.does_asset_exist(TARGET_LEVEL):
        raise RuntimeError(f"Village: target level {TARGET_LEVEL} not found (VILLAGE_TARGET_LEVEL)")
    reimport = os.environ.get("VILLAGE_REIMPORT") == "1"
    todo = []
    for bid in ids:
        dest = f"{DEST_ROOT}/{bid}"
        paths = find_meshes(dest)
        if paths and not reimport:
            m = EAL.load_asset(paths[0])
            if len(paths) == 1 and mesh_ok(m):
                log(f"{bid}: mesh already imported and good ({paths[0]}): import skipped (VILLAGE_REIMPORT=1 forces it)")
                continue
        todo.append(bid)
    if todo:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        log("switched to an empty level for the imports")
        yield 2.0
    for bid in todo:
        dest = start_import(os.path.join(d, bid, bid + ".glb"), bid)
        t0, seen = time.time(), None
        while True:
            yield 3.0
            have = bool(find_meshes(dest))
            busy = unreal.AssetRegistryHelpers.get_asset_registry().is_loading_assets()
            if have and not busy:
                seen = seen or time.time()
                if time.time() - seen > 5.0:
                    break
            else:
                seen = None
            if time.time() - t0 > 1800:
                raise RuntimeError(f"Village: import of {bid} timed out (30 min)")
            log(f"waiting for the {bid} import... {time.time() - t0:.0f} s (mesh found={have})")
        finish_mesh(dest, bid)
        unreal.SystemLibrary.collect_garbage()
        yield 3.0
    meshes = []
    for bid in ids:
        p = find_meshes(f"{DEST_ROOT}/{bid}")
        if not p:
            raise RuntimeError(f"Village: no static mesh for {bid} under {DEST_ROOT}/{bid}")
        m = EAL.load_asset(p[0])
        ok, missing = apply_materials(m)           # idempotent; also covers skipped imports
        meshes.append((bid, m))
        log(f"{bid}: ready; slots {ok}; Nanite {nanite_report(m)}; vertex colours {vertex_colours_present(m)}; tags {asset_tags(m)}")
    log(f"opening {TARGET_LEVEL}")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(TARGET_LEVEL)
    yield 8.0
    log(f"level now: {current_level()}")
    remove_old_actors()
    yield 1.0
    place_all(meshes)
    yield 2.0
    save_level()
    yield 1.0
    log("DONE: 4 buildings imported, placed in folder VillageFinal and the level saved" if len(ids) == 4 else "DONE")
    done_flag.append(True)


def main():
    gen = job(_DONE)
    st = {"wait": 0.0, "t": time.time(), "h": None}

    def tick(dt):
        if st.get("busy") or time.time() - st["t"] < st["wait"]:
            return                       # new_blank_map / load_level pump ticks re-entrantly: never re-enter the generator
        st["busy"] = True
        try:
            st["wait"] = next(gen)
            st["t"] = time.time()
        except StopIteration:
            unreal.unregister_slate_post_tick_callback(st["h"])
        except Exception as e:  # noqa
            unreal.unregister_slate_post_tick_callback(st["h"])
            unreal.log_error(f"Village: ERROR {e}")
            _DONE.append("error")
            try:
                if current_level() and current_level().startswith("/Temp/") and EAL.does_asset_exist(TARGET_LEVEL):
                    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(TARGET_LEVEL)
                    log(f"reopened {TARGET_LEVEL} after the error")
            except Exception:  # noqa
                pass
        finally:
            st["busy"] = False
            st["t"] = time.time()

    # run the preflight synchronously so a refusal shows up immediately in the Output Log
    st["h"] = unreal.register_slate_post_tick_callback(tick)


if os.environ.get("VILLAGE_NO_AUTORUN") != "1":
    main()
