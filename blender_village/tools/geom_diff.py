"""Per-object diff of two geom_hash.py fingerprints (A = new build, B = reference).

Usage:  python blender_village/tools/geom_diff.py <A.json> <B.json>
Prints objects present in only one file and, for every shared object whose triangles or geometry / uv / mask hash
differ, the triangle delta and the changed channels.
"""
import json
import sys

b = json.load(open(sys.argv[1]))["objects"]
d = json.load(open(sys.argv[2]))["objects"]
print("only in A", sorted(set(b) - set(d)))
print("only in B", sorted(set(d) - set(b)))
for k in sorted(set(b) & set(d)):
    x, y = b[k], d[k]
    ch = [c for c in ("geometry", "uv", "mask") if x[c] != y[c]]
    if ch or x["tris"] != y["tris"]:
        print(k, "tris B", y["tris"], "-> A", x["tris"], "delta", x["tris"] - y["tris"], "changed:", ch)
