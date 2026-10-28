"""prep_assets.py : builds assets/kb3d_picks.blend (kit objects, geometry only, no textures exist in the download) and
assets/wooden_pier_picks.blend (modular wooden pier, image paths remapped to assets/textures_pier).
Loads source .blend files with bpy.data.libraries.load only (objects/materials/images)."""
import bpy, os
A = r"C:\GitHubDesktop\git_test\blender_village\lookdev\vignette3\assets"
KIT = r"C:\Users\parke\AppData\Local\Temp\claude\C--GitHubDesktop-git-test-blender-village\03f38854-baaa-44de-99c6-7c7286cf14b9\scratchpad\luminara\kb3d_secretsoftheluminara-native.blend"
PIER = r"C:\Users\parke\AppData\Local\Temp\claude\C--GitHubDesktop-git-test-blender-village\03f38854-baaa-44de-99c6-7c7286cf14b9\scratchpad\pier\modular_wooden_pier_2k.blend"
PICKS = {"boat": "VehicBlimpShip_A_Boat", "netA": "VehicBlimpShip_A_FishingNetA", "netB": "VehicBlimpShip_A_FishingNetB",
         "ladder": "PropRopeLadder_A_Main", "anchor": "VehicBlimpShip_A_Anchor", "buoyA": "VehicBlimpShip_A_BuoysA",
         "buoyB": "VehicBlimpShip_A_BuoysB", "lifebuoy": "VehicBlimpShip_A_LifeBuoyA"}


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


sc = fresh()
with bpy.data.libraries.load(KIT) as (s, d):
    d.objects = ["KB3D_SOL_" + v for v in PICKS.values()]
col = bpy.data.collections.new("KB3D_PICKS")
sc.collection.children.link(col)
inv = {"KB3D_SOL_" + v: k for k, v in PICKS.items()}
for o in d.objects:
    o.parent = None
    o.location = (0, 0, 0)
    o.rotation_euler = (0, 0, 0)
    o.scale = (1, 1, 1)
    o.name = "PICK_" + inv[o.name]
    col.objects.link(o)
for im in list(bpy.data.images):
    bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A, "kb3d_picks.blend"), compress=True)
print("kit saved", [o.name for o in col.objects])

sc = fresh()
with bpy.data.libraries.load(PIER) as (s, d):
    d.objects = list(s.objects)
    d.materials = list(s.materials)
col = bpy.data.collections.new("PIER_PICKS")
sc.collection.children.link(col)
for o in d.objects:
    col.objects.link(o)
for im in bpy.data.images:
    if im.source == "FILE":
        nm = os.path.basename(im.filepath)
        im.filepath = os.path.join(A, "textures_pier", nm)
        print("img", im.filepath, os.path.exists(im.filepath))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(A, "wooden_pier_picks.blend"), compress=True, relative_remap=True)
