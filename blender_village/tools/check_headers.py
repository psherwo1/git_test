"""check_headers.py -- report stale signatures in the village_kit module headers (kit 1.8.0 tool).

Every kit module documents its public API in its module docstring as `name(arg, arg=default, ...)`.  This tool
parses each documented call whose name is a function or class of the same module (by AST, no import, no bpy) and
reports the documented arguments that the real signature does not have, and the real REQUIRED arguments the header
leaves out.  `...` in a header means "and more" and silences the missing-argument check for that line.

    python tools/check_headers.py [kit/village_kit]        exit code 1 when anything is stale
"""
import ast
import os
import re
import sys


def _sig(node):
    if isinstance(node, ast.ClassDef):
        for b in node.body:
            if isinstance(b, ast.FunctionDef) and b.name == "__init__":
                node = b
                break
        else:
            return None
    a = node.args
    names = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs]
    if names and names[0] == "self":
        names = names[1:]
    n_def = len(a.defaults)
    pos = [x.arg for x in a.posonlyargs + a.args]
    if pos and pos[0] == "self":
        pos = pos[1:]
    required = pos[:len(pos) - n_def] if n_def else pos
    required += [k.arg for k, d in zip(a.kwonlyargs, a.kw_defaults) if d is None]
    defaults = {}
    for k, d in list(zip(pos[len(pos) - n_def:], a.defaults)) + [(k.arg, d) for k, d in zip(a.kwonlyargs, a.kw_defaults)
                                                                   if d is not None]:
        try:
            defaults[k] = ast.literal_eval(d)
        except Exception:
            pass
    return dict(names=set(names), required=required, var=bool(a.vararg or a.kwarg), defaults=defaults,
                optional=[k for k in names if k not in required])


def _split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out if x.strip()]


def check_file(path):
    src = open(path, encoding="utf-8-sig").read()
    tree = ast.parse(src)
    doc = ast.get_docstring(tree) or ""
    defs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    issues = []
    for m in re.finditer(r"(?<![\w.])([A-Za-z_]\w*)\(", doc):
        name = m.group(1)
        if name not in defs:
            continue
        i, depth = m.end(), 1
        while i < len(doc) and depth:
            depth += {"(": 1, ")": -1}.get(doc[i], 0)
            i += 1
        body = doc[m.end():i - 1]
        sig = _sig(defs[name])
        if sig is None:
            continue
        # a usage EXAMPLE, not a signature: an assignment (`x = name(`), or a positional argument that is not a
        # plain lower-case parameter name (a literal, a call, an UPPER-CASE constant, a class)
        line_start = doc.rfind("\n", 0, m.start()) + 1
        if "=" in doc[line_start:m.start()]:
            continue
        pos_args = [a for a in _split_args(re.sub(r"\s+", " ", body)) if not re.match(r"[A-Za-z_]\w*\s*=", a)
                    and not a.startswith("*") and not a.startswith("...")]
        if any(not re.fullmatch(r"[a-z_][a-z0-9_]*|[A-Z]|[A-Z]\w*_[a-z]\w*|P|V|T", a) for a in pos_args):
            continue
        doc_args = []
        doc_defaults = {}
        ellipsis = False
        for a in _split_args(re.sub(r"\s+", " ", body)):
            if a in ("...", "…") or a.startswith("..."):
                ellipsis = True
                continue
            if a.startswith("*"):
                ellipsis = True
                continue
            k = re.split(r"[=\s:]", a, maxsplit=1)[0].strip()
            if not re.fullmatch(r"[A-Za-z_]\w*", k or ""):
                continue
            doc_args.append(k)
            if "=" in a:
                try:
                    v = ast.literal_eval(a.split("=", 1)[1].strip())
                    if v is not Ellipsis:
                        doc_defaults[k] = v
                except Exception:
                    pass
        if not doc_args and not body.strip():
            continue
        unknown = [a for a in doc_args if a not in sig["names"] and not sig["var"]]
        missing = [] if ellipsis else [a for a in sig["required"] if a not in doc_args]
        wrong = [f"{k}={doc_defaults[k]!r} (is {sig['defaults'][k]!r})" for k in doc_defaults
                 if k in sig["defaults"] and doc_defaults[k] != sig["defaults"][k]]
        # a header written as a full signature (>= 5 documented defaults, no ...) must list every parameter
        omitted = [] if ellipsis or len(doc_defaults) < 5 else [k for k in sig["optional"] if k not in doc_args]
        if unknown or missing or wrong or omitted:
            line = doc[:m.start()].count("\n") + 2
            issues.append((line, name, unknown, missing, wrong, omitted))
    return issues


def main(root):
    bad = 0
    for dp, _, fs in os.walk(root):
        if "__pycache__" in dp:
            continue
        for f in sorted(fs):
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f)
            for line, name, unknown, missing, wrong, omitted in check_file(p):
                bad += 1
                rel = os.path.relpath(p, root)
                msg = []
                if unknown:
                    msg.append("header has " + ", ".join(unknown) + " (not in the signature)")
                if missing:
                    msg.append("header omits required " + ", ".join(missing))
                if wrong:
                    msg.append("stale default " + ", ".join(wrong))
                if omitted:
                    msg.append("full-signature header omits " + ", ".join(omitted))
                print(f"{rel}:{line}: {name}(): " + "; ".join(msg))
    print(f"{bad} stale header signature(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "kit", "village_kit")))
