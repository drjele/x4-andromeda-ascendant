# The ear drawn from its guides (asked: now draw the ear on the other side): every vertebra (its C + the straight level
# runs into the body) closed by a vertical line inside the body = one closed section; sections lofted (extra rows every DY m,
# linear), and at both ends narrowed in plan (heights kept: the faces stay on their planes) to a vertical edge at the margin's
# extended end points (front into the PS, back into the arm); with the edge / end guide lines in the npz the ends are
# instead carried on to the margin's ends lying on every guide line (open ends, capped flat inside the body)
# - every row's tip laid on the margin at its y (the piece follows the guide); one closed piece; mirrored to the left side. Usage: python ureche_din_vertebre.py <vertebre npz> <out.npz> ; env DY=2 NT=8
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; DY, NT = float(os.environ.get("DY", "2")), int(os.environ.get("NT", "8"))
ks = sorted((q for q in G.files if q.startswith("vertebra")), key=lambda q: -G[q][0, 1]); A = [G[q] for q in ks]
n = min(len(a) for a in A); A = [a[np.linspace(0, len(a) - 1, n).round().astype(int)] for a in A]
M = G["contur_margine_D"]; Mf = M[np.argmax(M[:, 1])]; Mb = M[np.argmin(M[:, 1])]            # the margin's ends (in the body)
rows = []
def toward(Sct, P, s):                                                 # the section narrowed (in plan) towards P, its heights kept
    Q = Sct.copy(); Q[:, :2] = P[:2] + s * (Sct[:, :2] - P[:2]); return Q
PV_ = os.environ.get("PANA_LA_VERTEBRE", "0") == "1"                  # the ear only between the end vertebrae (flat ends there)
GL = all(q in G.files for q in ("linie_muchie_sus_D", "linie_capat_sus_D", "linie_capat_jos_D"))
def along(Sct, y, ends=True):                                                    # the end section carried on at y, laid on the guides there: tip on the
    Ms_ = M[np.argsort(M[:, 1])]; xm2 = np.interp(y, Ms_[:, 1], Ms_[:, 0])                      # margin, edge on the edge lines (top / bottom
    def edge(k):                                                                                # each its own), inner ends on the end lines
        Es = G[k]; Es = Es[np.argsort(Es[:, 1])]; return np.interp(y, Es[:, 1], Es[:, 0]) if Es[:, 1].min() <= y <= Es[:, 1].max() else -1e9
    def lin(k): q = G[k]; q = q[np.argsort(q[:, 1])]; q = q[:3] if y < q[0, 1] else q[-3:]; b, a = np.polyfit(q[:, 1], q[:, 0], 1); return a + b * y
    zt, zb = Sct[:, 2].max(), Sct[:, 2].min(); xm = Sct[:, 0].max(); Q = Sct.copy(); Q[:, 1] = y
    for zz, ke, km in ((zt, "linie_capat_sus_D", "linie_muchie_sus_D"), (zb, "linie_capat_jos_D", "linie_muchie_jos_D")):
        xb2 = edge(km)
        if xb2 < -1e8 and not ends: xb2 = Sct[np.abs(Sct[:, 2] - zz) < 1e-3, 0].max()   # past the edge line's end: the row's own edge
        fl = np.abs(Sct[:, 2] - zz) < 1e-3; xe, xb = Sct[fl, 0].min(), Sct[fl, 0].max(); xe2 = lin(ke) if ends else xe
        xb3 = min(max(xb2, xe2 + 1e-3), xm2) if xm2 > xe2 else xe2; xe2 = min(xe2, xm2)   # narrow ends: the edge from the inner plane
        Q[fl, 0] = xe2 + (Sct[fl, 0] - xe) * (xb3 - xe2) / max(xb - xe, 1e-6)
        cv = (~fl) & ((Sct[:, 2] >= ZMID - 1e-3) if zz == zt else (Sct[:, 2] <= ZMID + 1e-3))   # the tip in both (same x)
        Q[cv, 0] = xb3 + (Sct[cv, 0] - xb) * (xm2 - xb3) / max(xm - xb, 1e-6)
    return Q
ZMID = float(np.median(M[:, 2]))
if GL and not PV_:                                                     # GUIDES: the ends carried on to the margin's ends along every guide line
    for y in np.arange(Mf[1], A[0][0, 1], -DY): rows.append(along(A[0], y))
elif not PV_:
  for t in np.linspace(0, 1, NT, endpoint=False):                                                # front taper: an edge at the margin's end -> the first section
    s = t * t * (3 - 2 * t); rows.append(toward(A[0], Mf, s))
for a, b in zip(A[:-1], A[1:]):
    m = max(int(abs(a[0, 1] - b[0, 1]) / DY), 1)
    for t in np.linspace(0, 1, m, endpoint=False): rows.append((1 - t) * a + t * b)
if PV_: rows.append(A[-1].copy())
elif GL:
    rows.append(A[-1].copy())
    for y in np.arange(A[-1][0, 1] - DY, Mb[1] - 1e-6, -DY): rows.append(along(A[-1], y))
    if rows[-1][0, 1] > Mb[1] + 1e-3: rows.append(along(A[-1], Mb[1]))
elif not PV_:
  for t in np.linspace(0, 1, NT + 1):                                                            # back taper: the last section -> an edge at the margin's end
    s = t * t * (3 - 2 * t); rows.append(toward(A[-1], Mb, 1 - s))
if GL: rows = [along(Q, Q[0, 1], ends=False) for Q in rows]                                    # every row: tip on the margin, edge on the edge lines
Mo = M[np.argsort(M[:, 1])]                                                                    # every row's tip put on the margin at its y:
for i, Q in enumerate(rows if not GL else []):                                                                   # the row stretched in x about its inner end
    it = int(np.argmax(Q[:, 0])); yt = Q[it, 1]; xt = float(np.interp(yt, Mo[:, 1], Mo[:, 0])); x0 = Q[:, 0].min()
    if Q[it, 0] - x0 > 1e-6: Q = Q.copy(); Q[:, 0] = x0 + (Q[:, 0] - x0) * (xt - x0) / (Q[it, 0] - x0); rows[i] = Q
R = np.array(rows); nr = len(R); F = []
for r in range(nr - 1):
    for j in range(n):                                                                         # closed ring: the vertical inner line closes it
        j2 = (j + 1) % n; a_, b_, c_, d_ = r * n + j, r * n + j2, (r + 1) * n + j2, (r + 1) * n + j; F += [[a_, b_, c_], [a_, c_, d_]]
V = R.reshape(-1, 3); F = np.array(F)
np.savez(OUT, ureche_D__v=V, ureche_D__f=F, ureche_S__v=V * [-1, 1, 1], ureche_S__f=F[:, ::-1])
print("URECHE din %d vertebre (%d randuri la ~%.0f m, capete ascutite in PS / brat): y %.0f..%.0f, x %.0f..%.0f, z %.1f..%.1f" % (
    len(A), nr, DY, V[:, 1].min(), V[:, 1].max(), V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max()))
