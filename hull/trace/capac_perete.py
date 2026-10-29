# A cross wall inside the 086 hood (asked: at the middle, inside, a wall perpendicular to the current middle one). The hood
# has two closed chambers either side of a lengthwise middle wall (x = 0, 4 m thick); the new wall runs across (plane
# y = const) at the chambers' middle length, as thick as the middle one: at that y each chamber's section (a closed loop in
# x-z) is offset OVERLAP m out (into the hood's own shell, never through it) and extruded over the wall's thickness -
# prisms that fill the chambers there; Blender then joins them to the hood (boolean union).
# Usage: python capac_perete.py <hood.npz v,f (local)> <out.npz> ; env CP_Y=mid CP_GROS=4 CP_OVERLAP=0.5
import sys, os, numpy as np, trimesh
d = np.load(sys.argv[1]); t = trimesh.Trimesh(d["v"], d["f"], process=False); OUT = sys.argv[2]
GROS, OV = float(os.environ.get("CP_GROS", "4")), float(os.environ.get("CP_OVERLAP", "0.5"))
def inner(y):
    s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: return []
    L = [q[:, [0, 2]] for q in s.discrete]; big = max(L, key=lambda q: np.ptp(q[:, 0]) * np.ptp(q[:, 1]))
    return [q for q in L if q is not big]
ys = [y for y in np.arange(t.vertices[:, 1].min() + 1, t.vertices[:, 1].max(), 1.0) if len(inner(y)) == 2]
Y = float(os.environ.get("CP_Y", "nan")); Y = (min(ys) + max(ys)) / 2 if np.isnan(Y) else Y
out = {}
for i, q in enumerate(inner(Y)):
    q = q[:-1] if np.allclose(q[0], q[-1]) else q
    a = 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]); sg = 1 if a > 0 else -1   # orientation
    tg = np.roll(q, -1, 0) - np.roll(q, 1, 0); nrm = sg * np.c_[tg[:, 1], -tg[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    p = q + OV * nrm
    out["bucla_%d" % i] = p
    print("CAMERA %d la y %.1f: x %.1f..%.1f, z %.1f..%.1f (%d puncte), marita %.1f m spre peretii ei" % (i, Y, q[:, 0].min(), q[:, 0].max(), q[:, 1].min(), q[:, 1].max(), len(q), OV))
out["y"] = np.array([Y - GROS / 2, Y + GROS / 2])
print("PERETE TRANSVERSAL: camere pe y %.0f..%.0f -> perete la y %.1f..%.1f (grosime %.1f m, ca peretele de la mijloc)" % (min(ys), max(ys), Y - GROS / 2, Y + GROS / 2, GROS))
np.savez(OUT, **out)
