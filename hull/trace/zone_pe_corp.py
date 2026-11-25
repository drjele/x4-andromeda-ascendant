# The confirmed zones (names and limits) put on the reference hull 084: S half, triangles cut to at most EMAX m, each labelled by its
# place: BJ = outside its own inner edge (free-standing at both ends, straight in between), AI = between that edge and the corner
# line hull | wing (top corner to bottom corner of each section), CORP etaj = the hull above the profile limit, H = the recess.
# Usage: python zone_pe_corp.py <dir with npz>  -> zone_084.npz (v, t, zone; S half mirrored)
import sys, numpy as np
D = sys.argv[1]; EMAX = 10.0
d = np.load(f"{D}/REFERINTA.npz"); n = list(d["n"]); T = d["v"][d["t"][d["o"] == n.index("R001 084_D")]]
T = T[T[:, :, 0].min(1) < -.5].copy(); T[:, :, 0] = np.minimum(T[:, :, 0], 0)
while True:
    e = np.linalg.norm(T - np.roll(T, -1, 1), axis=2); k = e.max(1) > EMAX
    if not k.any(): break
    B, i = T[k], e[k].argmax(1); r = np.arange(len(B)); a, b, c = B[r, i], B[r, (i + 1) % 3], B[r, (i + 2) % 3]; m = (a + b) / 2
    T = np.concatenate([T[~k], np.stack([a, m, c], 1), np.stack([m, b, c], 1)])
C = T.mean(1); a, y, z = -C[:, 0], C[:, 1], C[:, 2]
# BJ inner edge measured where it stands alone (y > 110 and y < -440): smallest |x| of the outer lower component per 10 m
ys = np.r_[np.arange(-480, -440, 10), np.arange(120, 1000, 10)]; edge = []
for yy in ys:
    s = (abs(y - yy) < 8) & (a > 440) & (z < -100); edge.append(a[s].min() if s.any() else np.nan)
edge = np.array(edge); ok = ~np.isnan(edge); inner = np.interp(y, ys[ok], edge[ok]); print("BJ inner edge y -450 / 120:", round(float(np.interp(-450, ys[ok], edge[ok]))), round(float(np.interp(120, ys[ok], edge[ok]))))
zone = np.full(len(T), "CORP", dtype="<U10")
wing = (y < 70) & (y > -530)
hull = 172 + (212 - 172) * np.clip((z + 70) / 215, 0, 1)                     # corner line of the sections: bottom (172, -70) .. top (212, 145)
hull = np.where((y > -100) & (z > 20), 400, np.where(y > -75, np.maximum(hull, 420), hull))
etaj = (z > 20) & (y < 240) & (y > -800)
zone[etaj] = "CORP etaj"
zone[wing & (a > hull)] = "AI"
zone[wing & (y > -175) & (y < -85) & (a > 215) & (a < 425) & (z < 25) & (z > -80) & (y > -165) & (z < 110 - (a - 230) * .85)] = "H"   # below the wing top
zone[(a > inner - 1) & (z < -100)] = "BJ"; zone[(a > 430) & (z < -100) & (y > 70)] = "BJ"; zone[(a > 430) & (y < -470)] = "BJ"
M = T[:, ::-1] * [-1, 1, 1]; T = np.concatenate([T, M]); zone = np.r_[zone, zone]
np.savez(f"{D}/zone_084.npz", T=T, zone=zone)
for q in np.unique(zone):
    Q = T[zone == q]; A = np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1).sum() / 2; print(q, len(Q), "arie", round(A / 1e3), Q.min((0, 1)).round(), Q.max((0, 1)).round())
