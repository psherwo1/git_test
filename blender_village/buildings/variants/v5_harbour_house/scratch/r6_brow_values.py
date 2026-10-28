import importlib.util, os, math
spec = importlib.util.spec_from_file_location("recipe", os.path.abspath("build_v5_harbour_house.py"))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
M = R.MAIN; B = M.BROWS[0]; cp = math.cos(M.p)
print({k: round(v, 3) for k, v in B.items() if isinstance(v, float)}, B["k_lip"])
end = B["u_t"] + B["plat_u"] + B["fade_u"]
print("U", round(M.U, 3), "fade end u", round(end, 3), "to ridge slope m", round(M.U - end, 3), "plan", round((M.U - end) * cp, 3))
print("max fade grad", round(1.5 * B["height"] / B["fade"], 3), "tan p", round(math.tan(M.p), 3))
