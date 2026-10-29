# The long guide lines of the ear cut where the vertebrae stop (asked: remove what is extra on the long lines, stop where
# the ribs stop): every non-vertebra line clipped to the vertebrae's y range (exact end points interpolated on y).
# Usage: python taie_linii_la_vertebre.py <guides npz> <out.npz>
import sys, numpy as np
G = dict(np.load(sys.argv[1])); V = [G[k] for k in G if k.startswith("vertebra")]
y0 = min(float(v[:, 1].min()) for v in V); y1 = max(float(v[:, 1].max()) for v in V)
def clip(P):
    keep = (P[:, 1] >= y0 - 1e-6) & (P[:, 1] <= y1 + 1e-6); out = []
    for i in range(len(P)):
        if keep[i]: out.append(P[i])
        if i + 1 < len(P) and keep[i] != keep[i + 1]:                       # crossing a limit: the exact point on it
            a, b = P[i], P[i + 1]; yy = y0 if min(a[1], b[1]) < y0 <= max(a[1], b[1]) else y1
            t = (yy - a[1]) / (b[1] - a[1]); out.append(a + t * (b - a))
    return np.array(out)
for k in list(G):
    if not k.startswith("vertebra"):
        n0 = len(G[k]); G[k] = clip(G[k]); print("TAIAT %-24s y %.0f..%.0f (%d -> %d puncte)" % (k, G[k][:, 1].min(), G[k][:, 1].max(), n0, len(G[k])))
np.savez(sys.argv[2], **G)
