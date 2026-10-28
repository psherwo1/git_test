import sys, bpy, numpy as np, os
T = sys.argv[1]
def load(p, cs='Non-Color'):
    im = bpy.data.images.load(p); im.colorspace_settings.name = cs
    w, h = im.size; a = np.empty(w*h*4, np.float32); im.pixels.foreach_get(a)
    return a.reshape(h, w, 4)  # row 0 = bottom
mr = load(os.path.join(T, 'dirty_metal_rmmodbdp_2k_ue_mid/Textures/T_rmmodbdp_2K_MR.png'))
print('MR size', mr.shape)
for c in range(4): print(' ch', c, 'mean %.3f min %.3f max %.3f std %.3f' % (mr[...,c].mean(), mr[...,c].min(), mr[...,c].max(), mr[...,c].std()))
for name in ['lichened_rock_wall_visoeh2bw_2k/Lichened_Rock_Wall_visoeh2bw_2K', 'nordic_moss_se4rwei_2k/Nordic_Moss_se4rwei_2K', 'rusty_metal_sheet_tj4kedvcw_2k/Rusty_Metal_Sheet_tj4kedvcw_2K']:
    n = load(os.path.join(T, name + '_Normal.jpg'))[::2, ::2]
    b = load(os.path.join(T, name + '_Bump.jpg'))[::2, ::2, 0]
    # pixel arrays: row index increases UPWARD in blender (row 0 bottom)
    dhdx = np.gradient(b, axis=1); dhdy_up = np.gradient(b, axis=0)
    r = n[..., 0] - 0.5; g = n[..., 1] - 0.5
    cr = np.corrcoef(r.ravel(), dhdx.ravel())[0, 1]
    cg = np.corrcoef(g.ravel(), dhdy_up.ravel())[0, 1]
    print(name.split('/')[0], 'corr(R, dh/dx)=%.3f corr(G, dh/dy_up)=%.3f' % (cr, cg))
# polyhaven gl normal sanity
for name in ['rough_wood_2k/textures/rough_wood', 'riet_01_2k.blend/textures/riet_01', 'lichen_rock_2k.blend/textures/lichen_rock']:
    pass
