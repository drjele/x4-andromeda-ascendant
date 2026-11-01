# The open ribs' ends put on the lips (asked: the open ribs, from _17 down and the head _49, must touch buze_gura): per open rib,
# where each lip crosses the rib's plane; the rib's end nearest that crossing moved onto it, the move eased (smoothstep) to nothing
# at the rib's middle, the rib kept in its plane. Right arm, the left one mirrored.
# Usage: python vertebre_pe_buze.py <guides npz> <out npz>
import sys, numpy as np
G = dict(np.load(sys.argv[1])); OUT = sys.argv[2]; sm = lambda w: w * w * (3 - 2 * w)
BZ = G["buze_gura_brat_fata_D"]; iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))]))
LIPS = (BZ[:iv + 1], BZ[iv:])
def cross(L, c, n):
    sd = (L - c) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k):                                                         # (the head: the lips end in its plane)
        j = int(np.argmin(np.abs(sd))); return L[j] if abs(sd[j]) < 0.5 else None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; return X[np.argmin(np.linalg.norm(X - c, axis=1))]
moved = []
for k in sorted([k for k in G if k.startswith("sectiune_brat_fata_D")], key=lambda q: int(q.split("_")[-1])):
    X = G[k].copy()
    if np.linalg.norm(X[0] - X[-1]) < 1: continue                         # closed ribs stay
    c = X.mean(0); n = np.linalg.svd(X - c)[2][2]; P = [cross(L, c, n) for L in LIPS]
    if any(p is None for p in P): print("  %s: o buza nu-i taie planul" % k); continue
    P = [p - n * ((p - c) @ n) for p in P]                                 # (in the rib's plane)
    e0, e1 = (P[0], P[1]) if np.linalg.norm(X[0] - P[0]) + np.linalg.norm(X[-1] - P[1]) <= np.linalg.norm(X[0] - P[1]) + np.linalg.norm(X[-1] - P[0]) else (P[1], P[0])
    m = len(X); h = m // 2; w0 = np.zeros(m); w1 = np.zeros(m)
    w0[:h + 1] = sm(1 - np.arange(h + 1) / h); w1[h:] = sm(np.arange(m - h) / (m - 1 - h))
    d0, d1 = e0 - X[0], e1 - X[-1]; X += np.outer(w0, d0) + np.outer(w1, d1); G[k] = X
    moved.append((k.split("_")[-1], np.linalg.norm(d0), np.linalg.norm(d1)))
    G[k.replace("_D_", "_S_")] = X * [-1, 1, 1]
print("VERTEBRE deschise pe buze: %d mutate; capete mutate max %.2f m (%s)" % (len(moved), max(max(a, b) for _, a, b in moved),
      ", ".join("%s %.1f/%.1f" % q for q in moved if max(q[1], q[2]) > 0.3)))
np.savez(OUT, **G)
