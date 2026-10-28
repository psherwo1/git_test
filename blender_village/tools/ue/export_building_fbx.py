"""Export one finished kit building to a single FBX for Unreal (alternative to the GLB route; import_building.py takes either).

    C:\\GitHubDesktop\\git_test\\.bpyenv\\Scripts\\python.exe -I tools\\ue\\export_building_fbx.py <in.blend> <out_dir> [--id <id>]

Centimetres (1 uu = 1 cm: FBX unit scale applied), Z up, Blender -Y forward mapped to Unreal +Y like the importer does, tangents,
'Mask' (raw values, FLOAT colour written 'LINEAR' = unchanged) as the only vertex colour, one mesh, one slot per palette name.
STATUS: written to the same preparation code as the GLB exporter; the GLB route is the one tested end to end in Unreal 5.8.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import building_prep as bp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blend")
    ap.add_argument("out_dir")
    ap.add_argument("--id")
    ap.add_argument("--no-tangents", action="store_true", help="smaller file; Unreal recomputes MikkTSpace on import")
    a = ap.parse_args()
    import bpy
    os.makedirs(a.out_dir, exist_ok=True)
    res = bp.prepare(a.blend, a.id)
    obj, info = res["obj"], res["info"]
    me = obj.data
    src = me.color_attributes["Mask"]
    buf = np.zeros(len(src.data) * 4, np.float32)
    src.data.foreach_get("color_srgb" if src.data_type == "BYTE_COLOR" else "color", buf)
    me.color_attributes.remove(src)
    dst = me.color_attributes.new("Mask", "FLOAT_COLOR", "CORNER")
    dst.data.foreach_set("color", buf)
    me.color_attributes.active_color = dst
    me.color_attributes.render_color_index = 0
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    fbx = os.path.join(a.out_dir, info["id"] + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_ALL", global_scale=1.0, axis_forward="-Z", axis_up="Y",
                             use_mesh_modifiers=False, mesh_smooth_type="OFF", use_tspace=not a.no_tangents,
                             colors_type="LINEAR", prioritize_active_color=True, use_custom_props=False, add_leaf_bones=False,
                             bake_anim=False, path_mode="AUTO", embed_textures=False)
    size = os.path.getsize(fbx)
    bp.log(f"wrote {fbx} ({size/1e6:.1f} MB)")
    bp.write_sidecars(a.out_dir, info["id"], info, res["anchors"],
                      dict(format="fbx", file=info["id"] + ".fbx", file_mb=round(size / 1e6, 1), mask_encoding="raw",
                           units="centimetres (FBX unit scale applied)", ue_frame="UE = (x, -y, z) of Blender; see decal_anchors.json"))


if __name__ == "__main__":
    main()
