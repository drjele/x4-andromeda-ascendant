# Sheet of how the reference's underside joins its top: the exact cuts at the given y, each segment coloured by the part its
# face belongs to (top red / bottom blue, by the middle surface between the confirmed guides, as ref_sparge.py), and on each
# side the gap between the two parts' nearest ends (0 = joined) written next to it. Usage: python ref_sparge_plansa.py
# <ref.npz> <teren.npz> <out.png> <xc> <y,y,...>
import sys, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
Z = np.load(sys.argv[1]); T = np.load(sys.argv[2]); OUT, XC = sys.argv[3], float(sys.argv[4]); YS = [float(t) for t in sys.argv[5].split(",")]
v = Z["v"].astype(float).copy(); v[:, 0] -= XC; f = Z["f"]; tm = trimesh.Trimesh(v, f, process=False)
mid = (T["top"] + T["bot"]) / 2; x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"]); ny, nx = mid.shape
cc = v[f].mean(1); i = np.clip(((cc[:, 1] - y0) / C).astype(int), 0, ny - 1); j = np.clip(((cc[:, 0] - x0) / C).astype(int), 0, nx - 1)
lab = cc[:, 2] >= mid[i, j]
fig, ax = plt.subplots(len(YS), 1, figsize=(14, 2.6 * len(YS)))
for a, y in zip(ax, YS):
    seg, fi = trimesh.intersections.mesh_plane(tm, [0, 1, 0], [0, y, 0], return_faces=True)
    S = {True: [], False: []}
    for q, k in zip(seg, fi): a.plot(q[:, 0], q[:, 2], "-", color="r" if lab[k] else "b", lw=1.3); S[bool(lab[k])].append(q)
    txt = []
    for side in (-1, 1):
        t = [p for q in S[True] for p in q if p[0] * side > 0]; b = [p for q in S[False] for p in q if p[0] * side > 0]
        if t and b:
            t, b = np.array(t), np.array(b); d = np.min(np.linalg.norm(t[:, None, [0, 2]] - b[None, :, [0, 2]], axis=2))
            k = np.argmax(np.abs(t[:, 0])); a.annotate("%.0f m" % d, (t[k, 0], t[k, 2]), fontsize=8, color="darkgreen"); txt.append("%s %.0f m" % ("st" if side < 0 else "dr", d))
    a.set_title("y = %.0f: sus (rosu) / dedesubt (albastru); distanta dintre ele pe fiecare parte: %s" % (y, ", ".join(txt)), fontsize=9)
    a.set_aspect("equal"); a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(OUT, dpi=95); print("PLANSA", OUT)
