# Centre curve of the PS arm tube (_S half: V -> back loop -> outer branch -> free end), tracked along the tube instead of
# binned along one axis (the tube folds back on itself): from a start section, step along the tangent, take the reference
# vertices in a thin slab perpendicular to it, centre = middle of their extent in the slab plane (holes in the shell do
# not pull it like a centroid would), until no surface is left ahead. Then smoothed (gaussian ~40 m) and resampled 1 m.
# The shell has few, large faces, so it is sampled densely on its surface (area-weighted) first.
# Usage: python ps_centre.py <ps_v.npy> <ps_f.json> <out_dir> <start_y>
import sys, json, numpy as np
V = np.load(sys.argv[1]); F = json.load(open(sys.argv[2])); OUT = sys.argv[3]; Y0 = float(sys.argv[4])
T = np.array([[f[0], f[i], f[i + 1]] for f in F for i in range(1, len(f) - 1)]); A = V[T[:, 0]]; B = V[T[:, 1]]; Cc = V[T[:, 2]]
ar = np.linalg.norm(np.cross(B - A, Cc - A), axis=1) / 2; rng = np.random.default_rng(0); N = int(ar.sum() / 1.0)
idx = rng.choice(len(T), N, p=ar / ar.sum()); r1, r2 = rng.random(N), rng.random(N); sw = r1 + r2 > 1; r1[sw], r2[sw] = 1 - r1[sw], 1 - r2[sw]
P = A[idx] + (B[idx] - A[idx]) * r1[:, None] + (Cc[idx] - A[idx]) * r2[:, None]
P = P[P[:, 0] < 0]; print("puncte pe suprafata: %d" % len(P)); STEP, SLAB, RAD = 4.0, 3.0, 90.0
def centre(c, t):
    u = np.cross(t, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); v = np.cross(t, u)
    d = P - c; m = (np.abs(d @ t) < SLAB) & (np.linalg.norm(d, axis=1) < RAD)
    if m.sum() < 8: return None, 0
    a, b = d[m] @ u, d[m] @ v
    return c + u * (a.min() + a.max()) / 2 + v * (b.min() + b.max()) / 2, m.sum()
s0 = P[(np.abs(P[:, 1] - Y0) < 3) & (P[:, 0] > -300)]; c = np.array([(s0[:, 0].min() + s0[:, 0].max()) / 2, Y0, (s0[:, 2].min() + s0[:, 2].max()) / 2])
def track(c, t, n=2000, ymax=1e9):
    out = [c]
    for _ in range(n):
        q, k = centre(out[-1] + t * STEP, t)
        if q is None or q[1] > ymax: break
        tn = q - out[-1]; tn /= np.linalg.norm(tn); t = (0.7 * t + 0.3 * tn); t /= np.linalg.norm(t); out.append(q)
    return np.array(out)
c, _ = centre(c, np.array([0, -1.0, 0]))
fwd = track(c, np.array([0, -1.0, 0]))                                  # down the V, round the loop, up the outer branch
back = track(c, np.array([0, 1.0, 0]), 400, float(__import__("os").environ.get("PS_SUS_PANA", "-140")))   # up toward the deck's U
C = np.vstack([back[::-1], fwd[1:]])
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; L = seg[-1]
U = np.arange(0, L, 1.0); C1 = np.array([np.interp(U, seg, C[:, i]) for i in range(3)]).T
sig = 40.0; k = np.exp(-0.5 * (np.arange(-120, 121) / sig) ** 2); k /= k.sum()
pad = np.vstack([np.repeat(C1[:1], 120, 0) * 0 + (2 * C1[0] - C1[120:0:-1]), C1, 2 * C1[-1] - C1[-2:-122:-1]])   # odd reflection keeps the ends
G = lambda X: np.array([np.convolve(np.vstack([2 * X[0] - X[120:0:-1], X, 2 * X[-1] - X[-2:-122:-1]])[:, i], k, "valid") for i in range(3)]).T
Cs = 2 * G(C1) - G(G(C1))                                               # twicing: smooth without pulling the loop inward
dev = np.linalg.norm(Cs - C1, axis=1)
print("CENTRU PS: %d pasi inainte, %d inapoi, lungime %.0f m, capat liber la %s, abatere netezire max %.1f m" % (len(fwd), len(back), L, Cs[-1].round(0), dev.max()))
np.save(OUT + "/centru_ps.npy", Cs); np.save(OUT + "/centru_ps_brut.npy", C1)
