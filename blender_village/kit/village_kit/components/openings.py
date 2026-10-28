"""components.openings -- THE opening spec of the kit (kit 1.8.0 consolidation).

Before kit 1.8.0 every wall family had its own spec function, with its own dict layout and defaults:

    stone_body.opening(kind, th_deg, ...)           tier bodies (stone_body / framed_openings)       family "body"
    wall_openings.door_spec / window_spec(...)      path / round rubble walls (rubble_walls)          family "wall"
    plank_doors.door_spec / windows.window_spec     the keep annex (OctFrame WDOOR / WWIN)            family "annex"
    drum_frame.window_spec (drum_window_spec)       drum windows (DrumFrame WIN_SPEC)                 family "drum"

They are now built here, and the old names are thin wrappers that return exactly the dicts they always returned.
A recipe writes ONE spec, in one vocabulary, and hands it to any wall builder:

    from village_kit.components.openings import door, window
    DOOR = door(width=1.0, height=2.10)                      # threshold / frame sizes: the family defaults
    WIN = window(width=0.50, height=0.55, sill=1.25)
    stone_body(g, "hall", openings=[DOOR.at(270), WIN.at(225)])       # tier body: .at(plan angle, deg)
    path_stone_wall(g, "south", PATH, openings=[(2.4, DOOR), (5.1, WIN)])   # wall: (path distance s, spec)
    round_stone_body(g, "round", openings=[(38.0, WIN)])              # (azimuth deg, spec)
    OctFrame(..., WDOOR=DOOR.at(-5.05), WWIN=WIN.at(-7.4))            # annex: .at(x along the S wall)
    DrumFrame WIN_SPEC=[WIN, ...]                                     # drum: window(kind="slit" / "lookout")

    door(width=None, height=None, threshold=None, **detail)     -> Opening (kind "door")
    window(width=None, height=None, sill=None, kind="window", **detail)   -> Opening (kind "window" / "slit" /
                                                                    "lookout"; the last two are drum windows)
    opening_spec(kind, width, height, sill=None, threshold=None, at=None, **detail)  the general form
    Opening.at(position)                                        a copy placed: plan angle (deg) for a tier body,
                                                                x for the keep annex (other families place it by
                                                                the wall builder's (s, spec) / (azimuth, spec))
    resolve(spec, family)                                       the family dict a builder reads; any dict that is
                                                                not an Opening passes through unchanged (old specs)

None means the family default (FAMILY_DEFAULTS documents them; they differ because the families model different
openings: a tier body's door has an 18 cm jamb, a rubble wall's door a 20 x 24 cm hewn post).  `detail` keywords are
the family's own extras (jamb, lintel_min, proud, post, bearing, leaf_set, planks, frame, depth, lintel, room, fw,
splay, course_h ...); an unknown keyword for the family raises.
"""
import math

import numpy as np

FAMILIES = ("body", "wall", "annex", "drum")

FAMILY_DEFAULTS = dict(
    body=dict(door=dict(width=1.0, height=2.10, threshold=0.10), window=dict(width=1.0, height=2.10, sill=0.0)),
    wall=dict(door=dict(width=1.0, height=2.10, threshold=0.12), window=dict(width=0.50, height=0.55, sill=1.25)),
    annex=dict(door=dict(width=1.0, height=2.10, threshold=0.10), window=dict(width=0.45, height=0.55, sill=1.30)),
    drum=dict(window=dict(width=0.16, height=0.55, sill=1.30)),
)
"""clear width / height and threshold / sill per family and kind (the historic spec-function defaults)."""


class Opening(dict):
    """a family-neutral opening spec (see the module doc): kind, width, height, sill, threshold, at, detail."""

    def at(self, position):
        o = Opening(self)
        o["at"] = position
        return o


def opening_spec(kind, width=None, height=None, sill=None, threshold=None, at=None, **detail):
    """THE opening spec: kind 'door' / 'window' ('slit' / 'lookout': drum windows); None = family default."""
    if kind not in ("door", "window", "slit", "lookout"):
        raise ValueError(f"opening_spec: kind={kind!r}")
    return Opening(kind=kind, width=width, height=height, sill=sill, threshold=threshold, at=at, detail=dict(detail))


def door(width=None, height=None, threshold=None, at=None, **detail):
    """a door spec (clear width x height above the threshold top); see opening_spec."""
    return opening_spec("door", width, height, threshold=threshold, at=at, **detail)


def window(width=None, height=None, sill=None, kind="window", at=None, **detail):
    """a window spec (clear width x height above the clear sill height); see opening_spec."""
    return opening_spec(kind, width, height, sill=sill, at=at, **detail)


def _pick(o, fam, kind, key):
    v = o.get(key)
    return FAMILY_DEFAULTS[fam][kind][key] if v is None else v


def resolve(spec, family):
    """the dict family `family` reads, from an Opening; anything else (an old family dict) is returned unchanged."""
    if not isinstance(spec, Opening):
        return spec
    if family not in FAMILIES:
        raise ValueError(f"resolve: family={family!r}; one of {FAMILIES}")
    o = spec
    kind = "window" if o["kind"] in ("slit", "lookout") else o["kind"]
    if family == "drum":
        if kind != "window":
            raise ValueError("a drum takes windows only (its door is DrumFrame.door_params)")
        d = dict(o["detail"])
        return drum_window(_pick(o, "drum", "window", "width"), _pick(o, "drum", "window", "height"),
                           _pick(o, "drum", "window", "sill"),
                           kind=o["kind"] if o["kind"] in ("slit", "lookout") else d.pop("kind", "slit"), **d)
    w, h = _pick(o, family, kind, "width"), _pick(o, family, kind, "height")
    d = dict(o["detail"])
    if family == "body":
        if o.get("at") is None:
            raise ValueError("a tier-body opening needs its plan angle: spec.at(th_deg)")
        if kind == "door":
            return body_opening("door", o["at"], w, h, threshold=_pick(o, "body", "door", "threshold"), **d)
        return body_opening("window", o["at"], w, h, sill=_pick(o, "body", "window", "sill"), **d)
    if family == "wall":
        if kind == "door":
            return wall_door(w, h, threshold=_pick(o, "wall", "door", "threshold"), **d)
        return wall_window(w, h, sill=_pick(o, "wall", "window", "sill"), **d)
    # annex
    if o.get("at") is not None:
        d["xc"] = o["at"]
    if kind == "door":
        return annex_door(width=w, height=h, threshold=_pick(o, "annex", "door", "threshold"), **d)
    return annex_window(width=w, height=h, sill=_pick(o, "annex", "window", "sill"), **d)


# =================================================================================================================
# the family dicts (moved here from the old spec functions, unchanged; the old names call these)
# =================================================================================================================
def body_opening(kind, th_deg, width=1.0, height=2.10, sill=0.0, jamb=0.18, lintel_min=0.22, depth=0.34, proud=0.06,
                 sill_h=0.12, threshold=0.10):
    """family "body" (stone_body.opening): kind 'door' (clear width x height above a `threshold` m threshold stone)
    or 'window' (clear width x height above the sill height `sill`); th_deg = plan angle of the opening's centre."""
    return dict(kind=kind, th=math.radians(th_deg), width=width, height=height, sill=sill, jamb=jamb,
                lintel_min=lintel_min, depth=depth, proud=proud, sill_h=sill_h, threshold=threshold)


def wall_door(width=1.0, height=2.10, threshold=0.12, post=(0.20, 0.24), lintel=0.24, bearing=0.25, leaf_set=0.07,
              planks=6):
    """family "wall" door (wall_openings.door_spec): a timber-framed plank door (clear width / height, threshold top
    above ground, post section (face, depth), lintel height, lintel bearing into the masonry each side, leaf set back
    behind the frame face)."""
    return dict(kind="door", width=width, height=height, threshold=threshold, post=post, lintel=lintel,
                bearing=bearing, leaf_set=leaf_set, planks=planks)


def wall_window(width=0.50, height=0.55, sill=1.25, frame=0.08, depth=0.22, lintel=0.16, room=1.3):
    """family "wall" window (wall_openings.window_spec): a small deep-set window (clear width / height, clear sill
    height, frame member size, reveal depth to the frame, lintel height, blocker-room depth)."""
    return dict(kind="window", width=width, height=height, sill=sill, frame=frame, depth=depth, lintel=lintel,
                room=room)


def annex_door(xc=-5.05, width=1.0, height=2.10, frame=0.18, depth=0.20, threshold=0.10):
    """family "annex" door (plank_doors.door_spec): rectangular plank door (clear width / height, frame section,
    set-back, threshold top), centred at x = xc on the keep annex's S wall."""
    return dict(xc=xc, hw=width / 2, z0=threshold, z1=threshold + height, fw=frame, depth=depth)


def annex_window(xc=-7.4, width=0.45, height=0.55, sill=1.30, frame=0.07, depth=0.16):
    """family "annex" window (windows.window_spec): small timber window (clear width / height, sill height, frame
    width, set-back in the reveal), centred at x = xc on the keep annex's S wall."""
    return dict(xc=xc, hw=width / 2, z0=sill, z1=sill + height, depth=depth, fw=frame)


DRUM_WINDOW_FW = dict(slit=[(0.17, 0.21), (0.21, 0.17)], lookout=[(0.20, 0.26), (0.26, 0.20)])
"""jamb-block face widths (left, right) per jamb course, alternating course by course (= drum_frame.WINDOW_FW)."""


def drum_window(clear_w=0.16, clear_h=0.55, sill=1.30, kind="slit", fw=None, lintel_h=None, course_h=0.30,
                splay=0.22, room=1.5):
    """family "drum" (drum_frame.window_spec, v1_stone_watchtower r2): a drum window of any size, as a dict
    build_slit_windows / hw_window / inside_clear / the wall core read.  clear_w x clear_h is the clear opening,
    `sill` its bottom (m above ground).  kind "slit": a splayed embrasure closed 0.62 m in (the mill's slit, `splay` =
    half width at the back); kind "lookout": a straight reveal through the wall and a closed dark room `room` m deep
    behind the face (producer note 6).  The jamb courses (about `course_h` each), the sill / lintel sizes and the
    rubble keep-out bands are derived from the clear size, so a slit, a stair light and a lookout come from one
    module."""
    cw = clear_w / 2.0
    z0, z1 = float(sill), float(sill) + clear_h
    n = max(2, int(round(clear_h / course_h)))
    jz = [float(z) for z in np.linspace(z0, z1, n + 1)]
    fw = fw or DRUM_WINDOW_FW["lookout" if kind == "lookout" else "slit"]
    fmax = max(max(p) for p in fw)
    lh = lintel_h if lintel_h is not None else (0.18 if kind == "slit" else 0.24)
    sill_w = 2 * (cw + fmax) + 0.04
    lintel_w = 2 * (cw + fmax) + 0.16
    return dict(kind=kind, cw=cw, z0=z0, z1=z1, jz=jz, fw=fw, splay=splay, room=room, sill_w=sill_w,
                lintel_w=lintel_w, lintel_h=lh, z_sill=z0 - 0.065, z_lintel=z1 + 0.005 + lh / 2,
                zb=z0 - 0.13, zt=z1 + lh + 0.015, hw_sill=sill_w / 2, hw_jamb=cw + fmax + 0.01, hw_lintel=lintel_w / 2)
