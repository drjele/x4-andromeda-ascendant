# Clean lines for the blue guides (asked: clean lines for the green and the blue ones): every rib re-drawn as one clean ellipse in
# its section plane (across the spine at the rib; the head rib in its own plane): its major axis exactly exterior -> interior (the
# green lines' crossings with the plane), centred between them; its minor radius from the rib as it is (median over its points away
# from the axis' ends) - for the open ribs (along the mouth) the one that puts the ellipse through the two lips, and the rib = the
# arc from one lip round the exterior to the other. Ribs whose plane the lines do not both cross (the snout) are left as they are.
# Usage: python vertebre_elipse.py <guides npz> <out npz> ; env CAP_SECT=49 NP=361
import sys, os, numpy as np
G = dict(np.load(sys.argv[1])); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d)); NP = int(e("NP", "361"))
SP, EX, IN = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior"))
BZ = G["buze_gura_brat_fata_D"]; iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))]))
HK = "sectiune_brat_fata_D_%02d" % int(e("CAP_SECT", "49")); CX = e("CAP_X", "nan")
if np.isfinite(CX):                                                        # (the head exactly in the plane x = CAP_X, across X: the lips'
    def to_x(L):                                                           # head ends and the green lines' cut / carried on to it)
        sd = (L[:, 0] - CX) * np.sign(L[len(L) // 2, 0] - CX)
        if sd[0] > 0: d = L[0] - L[1]; return np.vstack([L[0] + d * (sd[0] / max(abs(d[0]), 1e-9)), L])
        j = int(np.argmax(sd > 0)); q = L[j - 1] + (L[j] - L[j - 1]) * (-sd[j - 1]) / (sd[j] - sd[j - 1]); return np.vstack([q, L[j:]])
    A1, A2 = to_x(BZ[:iv + 1]), to_x(BZ[iv:][::-1]); BZ = np.vstack([A1, A2[::-1][1:]]); iv = len(A1) - 1
    G["buze_gura_brat_fata_D"] = BZ; G["buze_gura_brat_fata_S"] = BZ * [-1, 1, 1]
    for kk in ("spinare", "contur_exterior", "contur_interior"):
        L = to_x(G["%s_brat_fata_D" % kk]); L[0, 0] = CX; G["%s_brat_fata_D" % kk] = L; G["%s_brat_fata_S" % kk] = L * [-1, 1, 1]
    SP, EX, IN = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior"))
LIPS = (BZ[:iv + 1], BZ[iv:])
def cross(L, c, n, near=None, tol=1.0):
    sd = (L - c) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k):
        j = int(np.argmin(np.abs(sd))); return L[j] if abs(sd[j]) < tol else None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; ref = c if near is None else near
    return X[np.argmin(np.linalg.norm(X - ref, axis=1))]
rep = []
for k in sorted([k for k in G if k.startswith("sectiune_brat_fata_D")], key=lambda q: int(q.split("_")[-1])):
    X = G[k]; c0 = X.mean(0); opened = np.linalg.norm(X[0] - X[-1]) > 1
    if k == HK and np.isfinite(CX): n = np.array([1.0, 0, 0]); p = np.array([CX, c0[1], c0[2]]); X = X.copy(); X[:, 0] = CX
    elif k == HK or e("PLAN_PROPRIU", "1") > 0: n = np.linalg.svd(X - c0)[2][2]; p = c0   # (each rib in its own plane)
    else:
        j = int(np.argmin(np.linalg.norm(SP - c0, axis=1))); j = min(max(j, 1), len(SP) - 2); n = SP[j + 1] - SP[j - 1]; n /= np.linalg.norm(n)
        p = SP[j] + n * ((c0 - SP[j]) @ n)
    tl = 3.0 if k == HK else 2.0; E, I = cross(EX, p, n, c0, tl), cross(IN, p, n, c0, tl)
    if E is None or I is None or np.linalg.norm(E - I) < 8: rep.append((k[-2:], "lasata")); continue
    E, I = E - n * ((E - p) @ n), I - n * ((I - p) @ n)
    m = (E + I) / 2; a = np.linalg.norm(E - I) / 2; ex = (E - I) / (2 * a); ey = np.cross(n, ex); ey /= np.linalg.norm(ey)
    Q = X - m; x, y = Q @ ex, Q @ ey
    if opened:                                                             # (along the mouth the interior line is the lips' middle, inside
        Lp = [cross(L, p, n, X[0] if i == 0 else X[-1], 3.0 if k == HK else 2.0) for i, L in enumerate(LIPS)]   # the ellipse: its exterior end on the
        if any(q is None for q in Lp): rep.append((k[-2:], "fara buze")); continue           # exterior, its axis towards the interior,
        from scipy.optimize import least_squares                                             # a and b fitted to the rib, the lips held)
        uX, yX = (X - E) @ (-ex), (X - E) @ ey; uL = np.array([(q - E) @ (-ex) for q in Lp]); yL = np.array([(q - E) @ ey for q in Lp])
        def res(z):
            aa, bb = z; return np.r_[((uX - aa) / aa) ** 2 + (yX / bb) ** 2 - 1, 30 * (((uL - aa) / aa) ** 2 + (yL / bb) ** 2 - 1)]
        a, b = least_squares(res, [a, max(np.abs(yX).max(), 5.0)], bounds=([5, 2], [2000, 2000])).x
        m = E - ex * a; ang = [np.arctan2(yq / b, -(uq - a) / a) for uq, yq in zip(uL, yL)]
        a0, a1 = ang; d_ = (a1 - a0) % (2 * np.pi)                         # the arc through the exterior end (angle 0)
        t = np.linspace(a0, a0 + d_, NP) if (0 - a0) % (2 * np.pi) <= d_ else np.linspace(a0, a0 - (2 * np.pi - d_), NP)
        Y = m + np.outer(a * np.cos(t), ex) + np.outer(b * np.sin(t), ey)
        if np.linalg.norm(Y[0] - X[0]) + np.linalg.norm(Y[-1] - X[-1]) > np.linalg.norm(Y[-1] - X[0]) + np.linalg.norm(Y[0] - X[-1]): Y = Y[::-1]
        miss = max(min(np.linalg.norm(Y[0] - q) for q in Lp), min(np.linalg.norm(Y[-1] - q) for q in Lp))
    else:
        ok = np.abs(x) < 0.8 * a; b = float(np.median(np.abs(y[ok]) / np.sqrt(np.maximum(1 - (x[ok] / a) ** 2, 1e-4)))); miss = 0.0
        t = np.linspace(0, 2 * np.pi, NP); Y = m + np.outer(a * np.cos(t), ex) + np.outer(b * np.sin(t), ey)
    dv = np.min(np.linalg.norm(Y[:, None] - X[None], axis=2), axis=1).max()
    G[k] = Y; G[k.replace("_D_", "_S_")] = Y * [-1, 1, 1]; rep.append((k[-2:], "a %.0f b %.0f mutata %.1f%s" % (a, b, dv, (" buze %.2f" % miss) if opened else "")))
print("VERTEBRE elipse curate:\n  " + "\n  ".join("%s %s" % q for q in rep))
np.savez(OUT, **G)
