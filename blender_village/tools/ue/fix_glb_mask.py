"""Make an existing building GLB carry the Mask as COLOR_0 (what Unreal's glTF/Interchange importer reads).

    python fix_glb_mask.py <in.glb> <out.glb>        (any python 3 with numpy not needed; plain stdlib)

The Blender glTF exporter wrote TWO colour sets: COLOR_0 = white (the "render" set the materials did not use) and COLOR_1 = Mask.
Unreal reads only COLOR_0, so the buildings come in with Mask = (1,1,1).  This copies the accessor of COLOR_1 into COLOR_0 for
every primitive and drops COLOR_1.  Geometry and binary data are untouched; the input file is not modified.
NOTE: COLOR_1 holds Blender's linear value of the byte colour (about value^2.2 of the raw Mask byte), so with this file keep
MaskGamma = 1 or try ~0.45 on the instances (see README).  Re-exporting with export_building_glb.py writes the raw Mask instead.
"""
import json
import struct
import sys


def main(src, dst):
    data = open(src, "rb").read()
    magic, ver, total = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a GLB"
    jl, jt = struct.unpack_from("<II", data, 12)
    j = json.loads(data[20:20 + jl])
    rest = data[20 + jl:]
    n = 0
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            a = p["attributes"]
            if "COLOR_1" in a:
                a["COLOR_0"] = a.pop("COLOR_1")
                n += 1
            a.pop("COLOR_2", None)
    js = json.dumps(j, separators=(",", ":")).encode("utf8")
    js += b" " * (-len(js) % 4)
    out = struct.pack("<III", magic, ver, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), jt) + js + rest
    open(dst, "wb").write(out)
    print(f"{src}: {n} primitives now use COLOR_1 (Mask) as COLOR_0 -> {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
