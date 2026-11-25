# Closes the smooth pieces: skin parts stitched ring to ring, inner walls stitched to the skin, the rest of the rings closed flat,
# triangles oriented together and outwards. Writes one closed S half (or whole, for the pieces on the axis) per piece, with the
# skin's own normals. Usage: python nava_solide.py <dir with neteda5.npz>  -> solide.npz
import sys, numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
D = sys.argv[1]; Z = np.load(f"{D}/neteda5.npz"); CENTRAL = {"CORP", "CORP etaj", "PI (ARCU)"}; OUT = {}
def weld(v, t, n=None, e=3):
    u, first, inv = np.unique(v.round(e), axis=0, return_index=True, return_inverse=True); inv = inv.ravel(); f = inv[t]; f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    f = f[np.unique(np.sort(f, 1), axis=0, return_index=True)[1]]; return v[first], f, None if n is None else n[first]
def area(v, t): return np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1) / 2
def islands(v, t):
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]]]); return connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))), directed=False)[1][t[:, 0]]
def sliver(v, t, n, tol=.06):                                               # very short edges collapsed, so the clipped borders have no needles
    for _ in range(4):
        e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]); l = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1); s = e[l < tol]
        if not len(s): break
        lab = connected_components(coo_matrix((np.ones(len(s)), (s[:, 0], s[:, 1])), shape=(len(v), len(v))), directed=False)[1]; rep = np.full(lab.max() + 1, -1); rep[lab[::-1]] = np.arange(len(v))[::-1]; t = rep[lab][t]; t = t[(t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])]
    t = t[np.unique(np.sort(t, 1), axis=0, return_index=True)[1]]; k = np.unique(t); m = np.full(len(v), -1); m[k] = np.arange(len(k)); return v[k], m[t], None if n is None else n[k]
def edges(t): e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1); return np.unique(e, axis=0, return_counts=True)
def loops(t):
    u, c = edges(t); b = u[c == 1]; adj = {}
    for x, y in b: adj.setdefault(x, []).append(y); adj.setdefault(y, []).append(x)
    used = set(); L = []
    for x, y in b:
        if (min(x, y), max(x, y)) in used: continue
        p = [x]; cur, prev = x, None
        while True:
            nx = [q for q in adj[cur] if (min(cur, q), max(cur, q)) not in used]
            if not nx: break
            q = nx[0]; used.add((min(cur, q), max(cur, q))); cur = q
            if cur == p[0]: break
            p.append(cur)
        if len(p) > 2: L.append(np.array(p))
    return L
def zipl(v, P, Q):                                                          # triangles between two close rings
    A, B = v[P], v[Q]; k = cKDTree(B).query(A[0])[1]; Q = np.roll(Q, -k); B = v[Q]; h = max(len(P) // 12, 1); j = cKDTree(B).query(A[::h])[1]; dj = np.diff(j); dj = np.where(dj < -len(Q) / 2, dj + len(Q), np.where(dj > len(Q) / 2, dj - len(Q), dj))
    if np.sum(np.sign(dj)) < 0: Q = np.r_[Q[:1], Q[:0:-1]]; B = v[Q]
    n, m = len(P), len(Q); tr = cKDTree(B); g = np.zeros(n + 1, int); cur = 0
    for q in range(1, n):                                                   # matching index on the other ring: nearest point within a window ahead, never back
        w = np.arange(cur, min(cur + 60, m)); dd = np.linalg.norm(B[w] - A[q], axis=1) + .02 * np.arange(len(w)); cur = int(w[np.argmin(dd)]); g[q] = cur
    g[n] = m; T = []; j = 0
    for i in range(n):
        while j < g[i + 1] and (np.linalg.norm(B[(j + 1) % m] - A[i]) < np.linalg.norm(B[(j + 1) % m] - A[(i + 1) % n])): T.append((P[i], Q[(j + 1) % m], Q[j % m])); j += 1
        T.append((P[i], P[(i + 1) % n], Q[j % m]))
        while j < g[i + 1]: T.append((P[(i + 1) % n], Q[(j + 1) % m], Q[j % m])); j += 1
    return np.array(T)
def orient(v, t):
    e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]); f = np.tile(np.arange(len(t)), 3); s = np.sort(e, 1); o = np.lexsort((s[:, 1], s[:, 0])); s, f, e = s[o], f[o], e[o]; k = np.where((s[1:] == s[:-1]).all(1))[0]; nb = {}
    for q in k: same = e[q][0] == e[q + 1][0]; nb.setdefault(f[q], []).append((f[q + 1], same)); nb.setdefault(f[q + 1], []).append((f[q], same))
    flip = np.full(len(t), -1); comp = np.zeros(len(t), int); c = 0
    for st in range(len(t)):
        if flip[st] >= 0: continue
        flip[st] = 0; stack = [st]
        while stack:
            x = stack.pop(); comp[x] = c
            for y, same in nb.get(x, ()):
                if flip[y] < 0: flip[y] = flip[x] ^ int(same); stack.append(y)
        c += 1
    t = t.copy(); t[flip == 1] = t[flip == 1][:, ::-1]
    for q in range(c):
        w = t[comp == q]; vol = np.einsum("ij,ij->i", v[w[:, 0]], np.cross(v[w[:, 1]], v[w[:, 2]])).sum() / 6
        if vol < 0: t[comp == q] = w[:, ::-1]
    return t, c, np.einsum("ij,ij->i", v[t[:, 0]], np.cross(v[t[:, 1]], v[t[:, 2]])).sum() / 6
for k in Z["names"]:
    k = str(k); V, T, N, S = [], [], [], []; off = 0; parts = [(Z[f"{k}|s{i}v"], Z[f"{k}|s{i}t"], Z[f"{k}|s{i}n"], True) for i in range(int(Z[f"{k}|ns"]))] + [(Z[f"{k}|w{i}v"], Z[f"{k}|w{i}t"], None, False) for i in range(int(Z[f"{k}|nw"]))]
    if k == "H": v, t, n, _ = parts[0]; v, t, n = weld(v, t, n); v, t, n = sliver(v, t, n); parts = [(v, t, n, True), (v - n * 5.0, t, None, False)]      # the hangar lining: a 5 m shell into the wing
    for v, t, n, sk in parts:
        if not len(t): continue
        if k in CENTRAL:
            v = v.copy(); v[np.abs(v[:, 0]) < 1e-3, 0] = 0; m = len(v); t = np.concatenate([t, t[:, ::-1] + m]); v = np.vstack([v, v * [-1, 1, 1]]); n = None if n is None else np.vstack([n, n * [-1, 1, 1]])
        v, t, n = weld(v, t, n); v, t, n = sliver(v, t, n); lab = islands(v, t); ar = np.bincount(lab, weights=area(v, t)); keep = ar[lab] > (30 if sk else 60); t = t[keep]
        u = np.unique(t); mp = np.full(len(v), -1); mp[u] = np.arange(len(u)); v, t = v[u], mp[t]; n = np.zeros_like(v) if n is None else n[u]; V.append(v); T.append(t + off); N.append(n); S.append(np.full(len(t), sk)); off += len(v)
    v, t, n, skin = np.vstack(V), np.concatenate(T), np.vstack(N), np.concatenate(S); own = np.concatenate([np.full(len(q), i) for i, q in enumerate(V)]); L = loops(t); pairs = []
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            if own[L[i][0]] == own[L[j][0]]: continue
            a, b = v[L[i]], v[L[j]]
            if np.linalg.norm(a.mean(0) - b.mean(0)) > 30: continue
            d = (cKDTree(a).query(b)[0].mean() + cKDTree(b).query(a)[0].mean()) / 2
            if d < (9 if k == "H" else 4): pairs.append((d, i, j))
    done = set(); new = []; info = []; nsk = []
    for d, i, j in sorted(pairs):
        if i in done or j in done: continue
        done |= {i, j}; new.append(zipl(v, L[i], L[j])); nsk.append(np.full(len(new[-1]), bool(np.linalg.norm(n[L[i]], axis=1).min() > .5 and np.linalg.norm(n[L[j]], axis=1).min() > .5 and k != "H"))); info.append(round(d, 2))
    rest = [l for i, l in enumerate(L) if i not in done]; fan = []
    for l in rest:
        c = v[l].mean(0); v = np.vstack([v, c]); n = np.vstack([n, [0, 0, 0]]); new.append(np.stack([np.full(len(l), len(v) - 1), l, np.roll(l, -1)], 1)); nsk.append(np.zeros(len(l), bool)); P = v[l]; fan.append((round(float(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1).sum())), c.round().tolist()))
    if new: q = np.concatenate(new); t = np.concatenate([t, q]); skin = np.r_[skin, np.concatenate(nsk)]
    ok = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2]); t, skin = t[ok], skin[ok]; lb_ = islands(v, t); big = np.bincount(lb_)[lb_] > 1000; t, skin = t[big], skin[big]
    for _ in range(8):                                                      # an edge shared by more than two triangles: its end points merged, small rings closed again
        u, c = edges(t); b = u[c > 2]
        if len(b): x, y = b[0]; t = np.where(t == y, x, t)
        q = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2]); t, skin = t[q], skin[q]; w, i, cn = np.unique(np.sort(t, 1), axis=0, return_index=True, return_counts=True); i = np.sort(i[cn == 1]); t, skin = t[i], skin[i]
        for l in loops(t):
            if len(l) == 3: q = l[None]
            else: v = np.vstack([v, v[l].mean(0)]); n = np.vstack([n, [0, 0, 0]]); q = np.stack([np.full(len(l), len(v) - 1), l, np.roll(l, -1)], 1)
            t = np.concatenate([t, q]); skin = np.r_[skin, np.zeros(len(q), bool)]
        u, c = edges(t)
        if (c == 2).all(): break
    lab = islands(v, t); cnt = np.bincount(lab); u, c = edges(t); t0, nc, vol = orient(v, t)
    print(f"{k:10s} fete {len(t)} | inele cusute {len(info)} {info} | inchise drept {fan} | margini libere {(c == 1).sum()} ne-manifold {(c > 2).sum()} | corpuri {nc} {sorted(cnt[cnt > 0])[::-1][:4]} | volum {vol / 1e6:.2f} mil")
    OUT[k + "|v"], OUT[k + "|t"], OUT[k + "|n"], OUT[k + "|s"] = v, t0, n, skin
OUT.update({k: Z[k] for k in Z.files if k.startswith("NAC|")}); OUT.update({k: Z[k] for k in ("tip_p", "tip_t") if k in Z.files}); OUT["names"], OUT["cut_p"], OUT["cut_t"] = Z["names"], Z["cut_p"], Z["cut_t"]; np.savez(f"{D}/solide.npz", **OUT)
