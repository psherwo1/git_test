"""one-off: splice the timber_walls openings section (round 2 refactor onto wall_openings.build_opening)."""
import io

F = r"C:\GitHubDesktop\git_test\blender_village\kit\village_kit\components\timber_walls.py"
s = io.open(F, encoding="utf-8").read()
SEP = "# " + "-" * 111 + "\n"
a = s.index("def _room(acc, F,")
b = s.index("def _sheet(")
s = s[:a] + s[b:]
o0 = s.index(SEP + "# openings\n")
o1 = s.index(SEP + "# the wall\n")
NEW = SEP + '''# openings: the kit's ONE opening builder, wall_openings.build_opening(host=...) (round 2: the private builder retired)
''' + SEP + '''def _opening_layout(sp, s_c, floor, st):
    """an opening's clear rect and the cladding block rect (the opening's own jambs, rails and head, cased)."""
    hw = sp["width"] / 2
    jw = sp["jamb"][0]
    if sp["kind"] == "window":
        cz0 = floor + sp["sill"]
        cz1 = cz0 + sp["height"]
        bot = cz0 - sp["rail"]
    else:
        cz0 = floor + sp["threshold"]
        cz1 = cz0 + sp["height"]
        bot = floor - 0.30                       # a door's block reaches through the sill line
    top = cz1 + sp["head"]
    clear = (s_c - hw, s_c + hw, cz0, cz1)
    block = (s_c - hw - jw - (0.04 if sp["kind"] != "window" else 0.0), s_c + hw + jw +
             (0.04 if sp["kind"] != "window" else 0.0), bot, top)
    return clear, block


def _plate_cut(sp, s_c, floor, plate_bot, head_rule):
    """(s0, s1) of the plate an opening cuts (head_rule 'trim', the opening taller than its storey), else None."""
    if sp["kind"] == "window":
        return None
    rule = sp.get("head_rule") or head_rule
    cz1 = floor + sp["threshold"] + sp["height"]
    if rule == "trim" and cz1 + sp["head"] > plate_bot + 1e-6:
        hw, jw = sp["width"] / 2, sp["jamb"][0]
        return (s_c - hw - jw, s_c + hw + jw)
    return None


def _build_opening(g, oaccs, F, sp, s_c, floor, head_max, st, rng, label, ground, plate_top=None, plate_w=None,
                   head_rule="clamp"):
    """one opening of a timber wall: wall_openings.build_opening with the timber host (see TIMBER_HOST there)."""
    from .wall_openings import build_opening
    O, t, n = F[0], F[1], F[2]
    bow = F[3] if len(F) > 3 else None
    w_off = 0.0 if bow is None else float(bow(s_c))
    host = dict(face=st["board"][1] if st["casing"] else 0.0, floor=floor, head_max=head_max, plate_top=plate_top,
                plate_w=plate_w, head_rule=head_rule, ground=ground, casing=st["casing"])
    return build_opening(g, sp, O + s_c * t + w_off * n, t, n, oaccs, rng, label=label, host=host)


'''
s = s[:o0] + NEW + s[o1:]
io.open(F, "w", encoding="utf-8", newline="\n").write(s)
print("spliced", len(s))
