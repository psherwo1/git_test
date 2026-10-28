"""Export one finished kit building to a GLB for Unreal (glTF/Interchange route), Mask as the ONLY vertex colour.

    C:\\GitHubDesktop\\git_test\\.bpyenv\\Scripts\\python.exe -I tools\\ue\\export_building_glb.py <in.blend> <out_dir> [--id <id>] [--mask raw|linear]

Writes  <out_dir>/<id>.glb, decal_anchors.json (Unreal frame, cm), <id>_export.json.
Why this exists: the plain Blender glTF export writes TWO colour sets (COLOR_0 = white, COLOR_1 = Mask, sRGB-decoded) and
Unreal's importer only reads COLOR_0, so the material sees Mask = white (everything mossy / worn).  This script joins the building,
keeps only 'Mask' (copied as raw float data so the file holds exactly the bytes the kit wrote) and exports it as COLOR_0.
--mask raw    (default) COLOR_0 = the raw Mask values (R piece, G wear, B moss).
--mask linear COLOR_0 = Blender's usual srgb->linear conversion of the byte colour (what a plain export would write for COLOR_1).
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
    ap.add_argument("--mask", choices=("raw", "linear"), default="raw")
    a = ap.parse_args()
    import bpy
    os.makedirs(a.out_dir, exist_ok=True)
    res = bp.prepare(a.blend, a.id)
    obj, info = res["obj"], res["info"]
    me = obj.data
    if a.mask == "raw":
        src = me.color_attributes["Mask"]
        n = len(src.data)
        buf = np.zeros(n * 4, np.float32)
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
    glb = os.path.join(a.out_dir, info["id"] + ".glb")
    kw = dict(filepath=glb, export_format="GLB", use_selection=True, export_apply=False, export_yup=True,
              export_materials="EXPORT", export_image_format="NONE", export_vertex_color="ACTIVE",
              export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True, export_attributes=False,
              export_normals=True, export_tangents=False, export_texcoords=True, export_cameras=False,
              export_lights=False, export_animations=False, export_extras=False, export_draco_mesh_compression_enable=False)
    bpy.ops.export_scene.gltf(**kw)
    size = os.path.getsize(glb)
    bp.log(f"wrote {glb} ({size/1e6:.1f} MB)")
    extra = dict(format="glb", file=info["id"] + ".glb", file_mb=round(size / 1e6, 1), mask_encoding=a.mask,
                 units="glTF metres (Unreal's importer scales to cm); axes: Blender Z up -> glTF Y up",
                 ue_frame="UE = (x, -y, z) of Blender; see decal_anchors.json")
    bp.write_sidecars(a.out_dir, info["id"], info, res["anchors"], extra)


if __name__ == "__main__":
    main()
