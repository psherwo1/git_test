"""components.cone -- geometry of a round conical roof (no meshes): the reference surface (top of battens =
underside of the shingle stack) as a function of azimuth and slope distance from the eave.

Profile: pitch PITCH with a 4 deg flatter eave kick over the last 0.55 m, very slightly convex (+7 cm at mid-slope),
eave line wave (wave_z / wave_r), faceted between the N_RAFT rafters (facet()).  All functions take the round
frame `g` (components.frame.RoundFrame) that owns the roof numbers: R_EAVE, Z_EAVE, PITCH, N_RAFT, RAFT_AZ0,
RAFT_R, BATTEN_T and the sampled profile PS / PR / PZ / PA.
theta = math angle (x = cos, y = sin); az = azimuth from -Y toward +X; az2th converts.
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import nrm, ring_noise, smoothstep


def build_profile(g):
    ds = 0.004
    s_max = 6.4 if (g.R_EAVE - 0.18) / math.cos(g.PITCH) < 6.3 else (g.R_EAVE - 0.18) / math.cos(g.PITCH) + 0.3
    s = np.arange(0, s_max, ds)
    alpha = g.PITCH - math.radians(4.0) * (1 - smoothstep(0.0, 0.55, s))
    r = g.R_EAVE - np.concatenate([[0], np.cumsum(np.cos(alpha[:-1]) * ds)])
    z = g.Z_EAVE + np.concatenate([[0], np.cumsum(np.sin(alpha[:-1]) * ds)])
    s_top = float(np.interp(0.0, -r, s))         # where straight profile reaches the axis
    b = 0.07 * np.sin(np.pi * np.clip(s / (s_top * 0.92), 0, 1)) ** 1.2
    r = r + b * np.sin(alpha)
    z = z + b * np.cos(alpha)
    keep = r > 0.18
    return s[keep], r[keep], z[keep], alpha[keep]


AGE_DEFAULTS = dict(eave_wave=0.025, eave_wave_seed=33, sag=(0.014, 0.034), sag_seed=7177, sag_eave_fade=(0.15, 0.9))
"""the ensemble-review age pass for a hut cone (art bible 1.7 / 6): an extra low-frequency eave wave (k <= 4,
peak `eave_wave`, on top of the phase-1 +-2.5 cm wave -> +-3-5 cm overall), a 1-3 cm SAG of the shingle surface
between every pair of rafters (sin^1.5 across the bay, its own amplitude per bay, faded in over the eave
`sag_eave_fade` slope metres and out under the collar), and the finial's ~1 deg lean (components.finial)."""


AGE_R9 = dict(rigid_sag=True, rigid_tilt_deg=1.5, underlap=0.08, max_joint=0.015)
"""kit 1.3.0 (director r8 #2): opt-in keys of the cone age pass (age_defaults(**AGE_R9)).  rigid_sag: each shingle
takes the sag as a RIGID offset (evaluated at its centre, translated along the cone normal, tilted about its own
axis by <= rigid_tilt_deg), so the per-vertex shear no longer opens the side joints; underlap: a strip of covered
shingle (this half-width, m) is kept under every side joint of the course above, as the separate never-culled
object <PREFIX>_roof_underlap; max_joint: side-joint gaps capped at this width (m)."""


AGE_R10 = dict(AGE_R9, underlap_k0=True)
"""kit 1.5.0 (director r9 #3, the eave light leak over the door): AGE_R9 + under-lap strips also under the side
joints of the FIRST course (over the doubled starter), so no starter / course-1 joint pair is ever unbacked."""


def age_defaults(**kw):
    d = dict(AGE_DEFAULTS)
    d.update(kw)
    return d


def wave_z(theta, g=None):
    w = ring_noise(theta, 31, 7, 0.028)
    age = getattr(g, "cone_age", None)
    if age:
        w = w + age.get("eave_wave", 0.0) / 1.25 * ring_noise(theta, age.get("eave_wave_seed", 33), 4, 1.0)
    # keep the eave over the door from dipping (door at az 0 => theta = -pi/2)
    dd = np.angle(np.exp(1j * (theta + np.pi / 2)))
    if age:                 # the deeper aged wave must not pull the lip over the door below 2.40 m: flat-topped guard
        w = np.where(w < 0.0, w * (1.0 - np.exp(-(dd / 0.42) ** 4)), w)
    return w + 0.02 * np.exp(-(dd / 0.35) ** 2) * (w < 0.0) * np.abs(w) / 0.02


def wave_r(theta):
    return ring_noise(theta, 57, 6, 0.025)


def facet(g, theta):
    d = 2 * np.pi / g.N_RAFT
    th_az = theta + np.pi / 2          # theta (math angle) -> azimuth from -Y
    ph = np.mod(th_az - g.RAFT_AZ0, d) - d / 2
    return math.cos(d / 2) / np.cos(ph)


def sag_at(g, theta, s):
    """age pass: inward (into the roof) displacement of the reference surface between the rafters (m); 0 on the
    rafter lines, so the rafters, the plate height and the eave lip over the rafters are unchanged."""
    age = getattr(g, "cone_age", None)
    theta, s = np.broadcast_arrays(np.asarray(theta, float), np.asarray(s, float))
    if not age or not age.get("sag"):
        return np.zeros(theta.shape)
    if "_sag_amp" not in g.__dict__:
        rs = np.random.RandomState(age.get("sag_seed", 7177))
        g._sag_amp = rs.uniform(age["sag"][0], age["sag"][1], g.N_RAFT)
        g._sag_mod = rs.uniform(0, 2 * np.pi, g.N_RAFT)
        g._sag_s1 = float(np.interp(-(g.COLLAR_R + 0.15), -g.PR, g.PS))
    d = 2 * np.pi / g.N_RAFT
    q = np.mod(theta + np.pi / 2 - g.RAFT_AZ0, 2 * np.pi) / d
    k = np.floor(q).astype(int) % g.N_RAFT
    u = q - np.floor(q)
    f0, f1 = age.get("sag_eave_fade", (0.15, 0.9))
    env = smoothstep(f0, f1, s) * (1 - smoothstep(g._sag_s1 - 1.2, g._sag_s1 - 0.1, s))
    along = 0.8 + 0.2 * np.sin(s * 1.3 + g._sag_mod[k])            # a purlin-less span sags unevenly
    span = 2 * np.pi * np.interp(s, g.PS, g.PR) / g.N_RAFT              # a short span (near the apex) sags less
    return g._sag_amp[k] * along * np.clip(span / 0.8, 0.0, 1.0) * np.sin(np.pi * u) ** 1.5 * env


def surf(g, theta, s, sag=True):
    """theta: math angle (x=cos, y=sin). s: slope distance from the eave.  sag=False: without the age-pass sag
    between the rafters (kit 1.3.0: rigid_sag shingles take it as a per-shingle offset, see conical_roof)."""
    theta, s = np.broadcast_arrays(np.asarray(theta, float), np.asarray(s, float))
    R = np.interp(s, g.PS, g.PR)
    Z = np.interp(s, g.PS, g.PZ)
    fade = 1 - 0.75 * smoothstep(0.0, 3.5, s)
    R = R * facet(g, theta) + wave_r(theta) * fade
    # extrapolate below the eave along the eave tangent
    ext = np.minimum(s, 0.0)
    a0 = g.PA[0]
    R = R - ext * math.cos(a0)
    Z = Z + ext * math.sin(a0) + wave_z(theta, g) * fade
    if sag and getattr(g, "cone_age", None):
        sg = sag_at(g, theta, s)
        al = np.interp(s, g.PS, g.PA)
        R = R - sg * np.sin(al)
        Z = Z - sg * np.cos(al)
    return np.stack([R * np.cos(theta), R * np.sin(theta), Z], -1)


def surf_frame(g, theta, s, sag=True):
    P = surf(g, theta, s, sag)
    eps_s, eps_t = 2e-3, 2e-4
    ts = nrm(surf(g, theta, s + eps_s, sag) - surf(g, theta, s - eps_s, sag))
    tt = nrm(surf(g, theta + eps_t, s, sag) - surf(g, theta - eps_t, s, sag))
    n = nrm(np.cross(tt, ts))
    return P, ts, tt, n


def az2th(az):
    return np.asarray(az, float) - np.pi / 2


def s_at_r(g, r):
    return float(np.interp(-r, -g.PR, g.PS))


def rafter_center(g, theta, s):
    P, ts, tt, n = surf_frame(g, theta, s)
    return P - n * (g.BATTEN_T + g.RAFT_R), ts, tt, n


def rafter_underside_z_at_r(g, r):
    th = az2th(g.RAFT_AZ0)
    ss = np.linspace(0, 3.0, 600)
    C, ts, tt, n = rafter_center(g, np.full_like(ss, th), ss)
    rr = np.hypot(C[:, 0], C[:, 1])
    zc = np.interp(-r, -rr, C[:, 2])
    nz = np.interp(-r, -rr, n[:, 2])
    return zc - g.RAFT_R / max(nz, 0.3)
