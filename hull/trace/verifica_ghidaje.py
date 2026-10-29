# Full check of the PS against its confirmed guides (asked: run a complete check against all the guides). 1) the median
# outline: every 2 m of y, per side, the widest point vs the guide, and anything sticking out past it (in plan, any height);
# 2) every vertebra: the PS's section at its y vs the vertebra curve (distance from the vertebra to the section, per side,
# outwards + / inwards -; VG_SUS=1 only the upper half); 3) creases along the length. Usage: python verifica_ghidaje.py <faces.npz:key> <ps.npz v> <ghid_median.npz> <vertebre.npz>
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
fn, k = sys.argv[1].split(":"); f = np.load(fn)[k]; V = np.load(sys.argv[2])["v"].astype(float) + [1700.0, 0, 0]
M = np.load(sys.argv[3]); VB = np.load(sys.argv[4]); t = trimesh.Trimesh(V, f, process=False)
Gm = M["contur_umar_median"]; ZM = Gm[0, 2]; R = Gm[Gm[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xg = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
y0, y1 = V[:, 1].min(), min(V[:, 1].max(), R[:, 1].max())
print("1) CONTUR MEDIAN (cel mai lat punct al fiecarei parti fata de ghidaj; iese = orice punct peste ghidaj, la orice inaltime)")
bad = []
for y in np.arange(np.floor(y1 / 2) * 2, y0, -2.0):
    row = []
    for sg in (1, -1):
        q = V[(np.abs(V[:, 1] - y) < 1) & (sg * V[:, 0] > 0)]
        if not len(q): continue
        d = np.abs(q[:, 0]).max() - xg(y); row.append(d)
    if row: bad.append((y, max(row, key=abs), *row))
bad = np.array(bad)
for a, b in ((470, 280), (280, 200), (200, 100), (100, 0), (0, -30), (-30, -60)):
    m = (bad[:, 0] <= a) & (bad[:, 0] > b)
    if m.any():
        i = np.argmax(np.abs(bad[m, 1])); print("   y %4d..%4d: abatere max %+.1f m la y %.0f (D %+.1f / S %+.1f); medie |%.1f|" % (
            a, b, bad[m, 1][i], bad[m, 0][i], bad[m, 2][i], bad[m, 3][i] if bad.shape[1] > 3 else 0, np.abs(bad[m, 1]).mean()))
o = bad[bad[:, 1] > 0.5]
print("   iese peste ghidaj > 0,5 m: %s" % (", ".join("y %.0f %+.1f" % (r[0], r[1]) for r in o) if len(o) else "nicaieri"))
print("2) VERTEBRE (sectiunea PS fata de vertebra: + PS in afara, - PS in interior; doar latura |x| >= 0,5 * latimea)")
for kv in VB.files:
    c = VB[kv]; y = c[0, 1]; s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: print("   %-14s y %4.0f: fara sectiune" % (kv, y)); continue
    S = np.vstack([q[:, [0, 2]] for q in s.discrete]); tr = cKDTree(S); C = c[:, [0, 2]]
    C = C[np.abs(C[:, 0]) >= 0.5 * np.abs(C[:, 0]).max()]
    if os.environ.get("VG_SUS", "0") == "1": C = C[C[:, 1] > ZM + 0.5]   # only the upper half
    d, j = tr.query(C)
    sgn = np.sign(np.abs(S[j, 0]) - np.abs(C[:, 0]) + 1e-9) * np.where(np.abs(S[j, 0] - C[:, 0]) > np.abs(S[j, 1] - C[:, 1]), 1, np.sign((np.abs(S[j, 0]) - np.abs(C[:, 0]))))
    sd = d * sgn; i = np.argmax(d)
    print("   %-14s y %4.0f: medie %.2f m, max %+.1f m (x %.0f, z %.0f); > 1 m: %d din %d puncte" % (kv, y, d.mean(), sd[i], C[i, 0], C[i, 1], (d > 1).sum(), len(d)))
a = np.degrees(t.face_adjacency_angles); cy = t.triangles_center[t.face_adjacency[:, 0], 1]
cy_all = t.triangles_center[t.face_adjacency[:, 0]]
print("3) CUTE (>30 / >45 / >60 grd) pe zone; etans %s" % t.is_watertight)
for a_, b_ in ((470, 280), (280, 200), (200, 100), (100, 0), (0, -30), (-30, -60)):
    m = (cy <= a_) & (cy > b_); mu = m & (cy_all[:, 2] > ZM)
    print("   y %4d..%4d: %d / %d / %d   (din ele sus: %d / %d / %d)" % (a_, b_, (a[m] > 30).sum(), (a[m] > 45).sum(), (a[m] > 60).sum(), (a[mu] > 30).sum(), (a[mu] > 45).sum(), (a[mu] > 60).sum()))
