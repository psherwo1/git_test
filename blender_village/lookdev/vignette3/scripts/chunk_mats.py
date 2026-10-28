# ------------------------------------------------------------------ procedural set dressing (vignette3: textured materials)
def timg(path, cs="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = cs
    return im


WOOD_IMG = timg(TEX + r"\rough_wood_2k.blend\textures\rough_wood_diff_2k.jpg")
ROCK_IMG = timg(TEX + r"\lichened_rock_wall_visoeh2bw_2k\Lichened_Rock_Wall_visoeh2bw_2K_BaseColor.jpg")
METAL_IMG = timg(TEX + r"\rusty_metal_sheet_tj4kedvcw_2k\Rusty_Metal_Sheet_tj4kedvcw_2K_BaseColor.jpg")
MOSS_IMG = timg(TEX + r"\nordic_moss_se4rwei_2k\Nordic_Moss_se4rwei_2K_BaseColor.jpg")


def tex_mat(name, img, tint=(1, 1, 1), rough=0.85, scale=0.4, bump=0.35, vcol=None, noise_tint=0.0):
    """object-space box-projected texture * tint; optional vertex colour attribute multiplies in"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links.new
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    ti = nt.nodes.new("ShaderNodeTexImage")
    ti.image = img
    ti.projection = "BOX"
    ti.projection_blend = 0.25
    L(mp.outputs["Vector"], ti.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0
    mx.inputs["B"].default_value = (tint[0], tint[1], tint[2], 1)
    L(ti.outputs["Color"], mx.inputs["A"])
    last = mx.outputs["Result"]
    if vcol:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = vcol
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type = "RGBA"
        m2.blend_type = "MULTIPLY"
        m2.inputs["Factor"].default_value = 1.0
        L(last, m2.inputs["A"])
        L(at.outputs["Color"], m2.inputs["B"])
        last = m2.outputs["Result"]
    L(last, b.inputs["Base Color"])
    bm_ = nt.nodes.new("ShaderNodeBump")
    bm_.inputs["Strength"].default_value = bump
    bm_.inputs["Distance"].default_value = 0.05
    L(ti.outputs["Color"], bm_.inputs["Height"])
    L(bm_.outputs["Normal"], b.inputs["Normal"])
    return m


def flat(name, col, rough=0.8):
    return simple(name, col, rough)


MATS = {
    "wood": tex_mat("D_wood", WOOD_IMG, (0.55, 0.47, 0.40), 0.9, 0.55),
    "plank": tex_mat("D_plank", WOOD_IMG, (0.85, 0.72, 0.58), 0.85, 0.5),
    "stone": tex_mat("D_stone", ROCK_IMG, (1.1, 1.1, 1.05), 0.95, 0.30),
    "hay": simple("D_hay", (0.55, 0.42, 0.16), 0.95, 0.4),
    "tree": tex_mat("D_tree", MOSS_IMG, (0.5, 0.75, 0.42), 0.9, 0.9, 0.25, vcol="tcol"),
    "trunk": tex_mat("D_trunk", WOOD_IMG, (0.30, 0.22, 0.17), 0.95, 0.7),
    "hull": tex_mat("D_hull", WOOD_IMG, (0.75, 0.22, 0.12), 0.7, 0.6),
    "hull2": tex_mat("D_hull2", WOOD_IMG, (0.30, 0.24, 0.20), 0.7, 0.6),
    "hull3": tex_mat("D_hull3", WOOD_IMG, (0.55, 0.68, 0.72), 0.7, 0.6),
    "iron": tex_mat("D_iron", METAL_IMG, (0.35, 0.33, 0.32), 0.6, 0.5),
    "fig1": simple("D_fig1", (0.30, 0.13, 0.08), 0.9),
    "fig2": simple("D_fig2", (0.18, 0.16, 0.10), 0.9),
    "fig3": simple("D_fig3", (0.10, 0.14, 0.12), 0.9),
    "fig4": simple("D_fig4", (0.20, 0.22, 0.28), 0.9),
    "fig5": simple("D_fig5", (0.33, 0.27, 0.15), 0.9),
    "legs": simple("D_legs", (0.07, 0.06, 0.05), 0.9),
    "skin": simple("D_skin", (0.45, 0.30, 0.22), 0.7),
    "rock": tex_mat("D_rock", ROCK_IMG, (0.75, 0.72, 0.68), 0.95, 0.18, 0.7),
}
BM = {k: bmesh.new() for k in MATS}
BM["tree"].loops.layers.color.new("tcol")
SMOOTH = {"rock", "tree", "trunk", "wood", "hull", "hull2", "hull3", "fig1", "fig2", "fig3", "fig4", "fig5", "legs", "skin", "iron", "stone", "hay"}
