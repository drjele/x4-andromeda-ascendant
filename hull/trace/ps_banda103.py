# Components 103 (side strip) + 118/117 (blade) as ONE thin piece per side (same texture): sections in planes y = const;
# in each, the reference points of both pieces (the _S ones and the mirrored _D ones pooled: symmetric) ordered into one
# curve (the longest shortest path through the near-point graph; a gap between the two pieces is bridged at the nearest
# ends), resampled at equal arc length from the inner/top end to the outer/bottom end, smoothed across the section and
# along y with twicing (the piece's edges become continuous lines); the sheet = that curve +/- half the thickness, its
# long edges rounded (half circles), the two ends closed. _S side; the mesh builder mirrors it.
# Usage: python ps_banda103.py <esantion_punte.npz> <out.npz>
import sys, os, heapq, numpy as np
D = np.load(sys.argv[1]); OUT = sys.argv[2]
env = lambda k, d: float(os.environ.get(k, d))
T, NU, NE, DY = env("B103_GROSIME", "2"), 64, 8, 2.0
PIESE = os.environ.get("B_PIESE", "p103S,-p103D,p118S,-p117D").split(",")   # "-" = the _D piece, mirrored onto _S
A = np.vstack([D[k.lstrip("-")] * ([-1, 1, 1] if k.startswith("-") else [1, 1, 1]) for k in PIESE])
ys = np.arange(np.ceil(A[:, 1].min()) + 2, A[:, 1].max() - 1, DY)
def order(Q):                                                           # Q: 2-D points (x, z) -> ordered polyline
    if len(Q) > 700: Q = Q[np.random.default_rng(0).choice(len(Q), 700, replace=False)]
    d = np.linalg.norm(Q[:, None] - Q[None], axis=2); n = len(Q); R = 4.0
    adj = [[(j, d[i, j]) for j in np.nonzero((d[i] < R) & (d[i] > 0))[0]] for i in range(n)]
    comp = -np.ones(n, int); c = 0                                      # connect the components at their nearest points
    for i in range(n):
        if comp[i] >= 0: continue
        st = [i]; comp[i] = c
        while st:
            u = st.pop()
            for v, _ in adj[u]:
                if comp[v] < 0: comp[v] = c; st.append(v)
        c += 1
    while c > 1:
        a_ = comp == 0; dd = d[np.ix_(a_, ~a_)]; ia, ib = np.unravel_index(np.argmin(dd), dd.shape)
        i, j = np.nonzero(a_)[0][ia], np.nonzero(~a_)[0][ib]; adj[i].append((j, d[i, j])); adj[j].append((i, d[i, j]))
        comp[comp == comp[j]] = 0; c = len(np.unique(comp))
    def dij(s):
        dist = np.full(n, np.inf); prev = -np.ones(n, int); dist[s] = 0; h = [(0.0, s)]
        while h:
            dv, u = heapq.heappop(h)
            if dv > dist[u]: continue
            for v, w in adj[u]:
                if dv + w < dist[v]: dist[v] = dv + w; prev[v] = u; heapq.heappush(h, (dv + w, v))
        return dist, prev
    d0, _ = dij(0); a = int(np.argmax(d0)); da, pr = dij(a); b = int(np.argmax(da))
    path = [b]
    while path[-1] != a: path.append(pr[path[-1]])
    P = Q[path]; k = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); k /= k.sum()
    P = np.stack([np.convolve(np.r_[[P[0, i]] * 4, P[:, i], [P[-1, i]] * 4], k, "valid") for i in range(2)], 1)
    if P[0, 1] + 0.5 * P[0, 0] < P[-1, 1] + 0.5 * P[-1, 0]: P = P[::-1]   # start at the inner/top end
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.linspace(0, s[-1], NU)
    return np.stack([np.interp(u, s, P[:, i]) for i in range(2)], 1)
C = []
for y0 in ys:
    q = A[np.abs(A[:, 1] - y0) < 1.0][:, [0, 2]]; C.append(order(q) if len(q) > 20 else None)
ok = np.array([c is not None for c in C]); ys = ys[ok]; C = np.array([c for c in C if c is not None])   # (K, NU, 2)
def gs(X, sg, axis):
    n = int(3 * sg); k = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); k /= k.sum()
    pad = [(0, 0)] * X.ndim; pad[axis] = (n, n); Z = np.pad(X, pad, mode="edge")
    return np.apply_along_axis(lambda z: np.convolve(z, k, "valid"), axis, Z)
G = lambda X: gs(gs(X, env("B103_NET_Y", "4"), 0), env("B103_NET_U", "2"), 1)
C = 2 * G(C) - G(G(C))                                                  # twicing: smooth, no shrinking
tg = np.gradient(C, axis=1); tg /= np.linalg.norm(tg, axis=2)[..., None]; nr = np.stack([-tg[..., 1], tg[..., 0]], -1)
top, bot = C + nr * T / 2, C - nr * T / 2
th = np.linspace(0, np.pi, NE + 2)[1:-1]
endB = np.stack([C[:, -1:] + (np.cos(t) * nr[:, -1:] + np.sin(t) * tg[:, -1:]) * T / 2 for t in th], 1)[:, :, 0]
endA = np.stack([C[:, :1] - (np.cos(t) * nr[:, :1] + np.sin(t) * tg[:, :1]) * T / 2 for t in th], 1)[:, :, 0]
ring2 = np.concatenate([top, endB, bot[:, ::-1], endA], 1)                # (K, M, 2) closed around: x, z
X = np.stack([ring2[..., 0], np.repeat(ys[:, None], ring2.shape[1], 1), ring2[..., 1]], -1)
np.savez(OUT, X=X, ys=ys, C=C)
L = np.linalg.norm(np.diff(C, axis=1), axis=2).sum(1)
print("103+118: %d sectiuni y %.0f..%.0f, latimea foii %.0f..%.0f m, grosime %.1f m, %d puncte pe sectiune" % (len(ys), ys[0], ys[-1], L.min(), L.max(), T, X.shape[1]))
