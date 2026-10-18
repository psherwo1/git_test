import sys
v=r"C:\GitHubDesktop\git_test\blender_village\lookdev\vignette3\scripts"
L=open(v+r"\build_vignette3.py",encoding="utf8").read().split("\n")
mats=open(v+r"\chunk_mats.py",encoding="utf8").read().split("\n")
dress=open(v+r"\chunk_dress.py",encoding="utf8").read().split("\n")
# 1-indexed ranges: 541-558 -> mats ; 604-757 -> dress
out=L[:540]+mats+L[558:603]+dress+L[757:]
open(v+r"\build_vignette3.py","w",encoding="utf8").write("\n".join(out))
