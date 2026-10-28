"""Auditor helper (read-only): print a file's blob at a commit from the raw .git store (loose + pack, no git binary).
python -I aud_gitshow.py <gitdir> <commit> <path/in/repo> <out>"""
import os
import struct
import sys
import zlib

gd, commit, path, out = sys.argv[1:5]


def loose(sha):
    p = os.path.join(gd, "objects", sha[:2], sha[2:])
    if not os.path.exists(p):
        return None
    d = zlib.decompress(open(p, "rb").read())
    h, _, body = d.partition(b"\0")
    return h.split(b" ")[0].decode(), body


PACKS = []
for f in os.listdir(os.path.join(gd, "objects", "pack")):
    if f.endswith(".idx"):
        idx = open(os.path.join(gd, "objects", "pack", f), "rb").read()
        assert idx[:4] == b"\xfftOc"
        fan = struct.unpack(">256I", idx[8:8 + 1024]); n = fan[-1]
        shas = idx[1032:1032 + 20 * n]
        o32 = 1032 + 20 * n + 4 * n
        offs = struct.unpack(f">{n}I", idx[o32:o32 + 4 * n])
        o64 = idx[o32 + 4 * n:]
        PACKS.append((os.path.join(gd, "objects", "pack", f[:-4] + ".pack"), shas, offs, o64, n))


def find_pack(sha):
    b = bytes.fromhex(sha)
    for pk, shas, offs, o64, n in PACKS:
        lo, hi = 0, n
        while lo < hi:
            m = (lo + hi) // 2
            s = shas[20 * m:20 * m + 20]
            if s < b:
                lo = m + 1
            elif s > b:
                hi = m
            else:
                off = offs[m]
                if off & 0x80000000:
                    k = off & 0x7fffffff
                    off = struct.unpack(">Q", o64[8 * k:8 * k + 8])[0]
                return pk, off
    return None


TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}


def read_at(fh, off):
    fh.seek(off)
    c = fh.read(1)[0]
    t = (c >> 4) & 7; size = c & 15; sh = 4
    while c & 0x80:
        c = fh.read(1)[0]; size |= (c & 0x7f) << sh; sh += 7
    if t == 6:
        c = fh.read(1)[0]; bo = c & 0x7f
        while c & 0x80:
            c = fh.read(1)[0]; bo = ((bo + 1) << 7) | (c & 0x7f)
        delta = zdec(fh)
        bt, base = read_at(fh, off - bo)
        return bt, apply(base, delta)
    if t == 7:
        ref = fh.read(20).hex(); delta = zdec(fh)
        bt, base = get(ref)
        return bt, apply(base, delta)
    return TYPES[t], zdec(fh)


def zdec(fh):
    d = zlib.decompressobj(); out = b""
    while not d.eof:
        out += d.decompress(fh.read(4096))
    return out


def apply(base, delta):
    i = 0

    def vint():
        nonlocal i
        r = 0; s = 0
        while True:
            c = delta[i]; i += 1; r |= (c & 0x7f) << s; s += 7
            if not c & 0x80:
                return r
    vint(); vint()
    out = bytearray()
    while i < len(delta):
        c = delta[i]; i += 1
        if c & 0x80:
            o = s = 0
            for k in range(4):
                if c & (1 << k):
                    o |= delta[i] << (8 * k); i += 1
            for k in range(3):
                if c & (1 << (4 + k)):
                    s |= delta[i] << (8 * k); i += 1
            out += base[o:o + (s or 0x10000)]
        else:
            out += delta[i:i + c]; i += c
    return bytes(out)


def get(sha):
    r = loose(sha)
    if r:
        return r
    fp = find_pack(sha)
    if fp is None:
        raise KeyError(sha)
    with open(fp[0], "rb") as fh:
        return read_at(fh, fp[1])


t, c = get(commit)
tree = c.split(b"\n")[0].split(b" ")[1].decode()
for part in path.split("/"):
    _, body = get(tree)
    i, found = 0, None
    while i < len(body):
        sp = body.index(b" ", i); nul = body.index(b"\0", sp)
        nm = body[sp + 1:nul].decode(); sha = body[nul + 1:nul + 21].hex(); i = nul + 21
        if nm == part:
            found = sha
    if found is None:
        raise SystemExit(f"not found: {part}")
    tree = found
open(out, "wb").write(get(tree)[1])
print("wrote", out, "blob", tree)
