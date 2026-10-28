# The 103 band built from its confirmed guides (bumerang_v.py with BV_TRAPEZ): along the spine, every metre, the section
# = upper rail -> the small vertical side on the spine (TH m) -> lower rail, closed along the side against PS / the arm;
# consecutive sections joined by quads, both ends capped flat - one watertight, separate piece (ship coordinates, centred).
# Usage: python bumerang_piesa.py <guides.npz> <out.npz> [th]
import sys, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; TH = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
Ru, Rj, S = G["sina_sus"], G["sina_jos"], G["spinare"]
n0 = int(np.argmin(np.linalg.norm(S[:, :2] - G["v_00"][1, :2], axis=1)))   # where the rails' stations start on the (lengthened) spine
sp = S[n0:n0 + len(Ru)]
ring = np.stack([Ru, sp + [0, 0, TH / 2], sp - [0, 0, TH / 2], Rj], 1)   # 4 corners per section
V = ring.reshape(-1, 3); n = len(ring); F = []
for i in range(n - 1):
    for a in range(4):
        b = (a + 1) % 4; F.append([i * 4 + a, (i + 1) * 4 + a, (i + 1) * 4 + b, i * 4 + b])
F.append([3, 2, 1, 0]); F.append([(n - 1) * 4 + 0, (n - 1) * 4 + 1, (n - 1) * 4 + 2, (n - 1) * 4 + 3])
F = np.array(F); T = np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
v = V; e1 = v[T[:, 1]] - v[T[:, 0]]; e2 = v[T[:, 2]] - v[T[:, 0]]; vol = np.einsum("ij,ij->i", v[T[:, 0]], np.cross(e1, e2)).sum() / 6
if vol < 0: T = T[:, ::-1]; vol = -vol                                   # faces facing out
import trimesh                                                          # one consistent outward winding (the caps came out mixed)
tm = trimesh.Trimesh(V, T, process=True); trimesh.repair.fix_winding(tm); trimesh.repair.fix_normals(tm); V, T, vol = tm.vertices, tm.faces, tm.volume
np.savez(OUT, v=V.astype(np.float32), f=T.astype(np.int32))
print("PIESA 103: %d sectiuni (din metru in metru), %d varfuri, %d triunghiuri, volum %.0f m3; latura mica %.0f m; x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (
    n, len(V), len(T), vol, TH, V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
