# The PS's outline from above as an open V without shoulders (asked: the inner straight parts moved out to carry on the line
# from the tip, no two shoulders; the nose a V, open, not an ellipse; drawn on our PS and on R002 169_C with its own guides).
# Per side: a straight run from the tip to K (the outline at section y_k), a bend of radius RK there, then a straight run with
# the slope of the current straight sides (fitted between Y1 and Y2) out to the PS's end; the two sides joined at the tip by an
# arc of radius RT. Also the reference's own outline from above (R002 169_C, its axis at XREF). Planar, at z ZT.
# Usage: python ghid_v_ps.py <guides_ps.npz> <ref.npz> <out.npz> ; env V_YK=240 V_Y1=200 V_Y2=0 V_YEND=-45 V_RK=80 V_RT=15 V_XREF=-4.7
import sys, os, numpy as np
G = np.load(sys.argv[1]); RF = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
YK, Y1, Y2, YEND, RK, RT, XR = e("V_YK", "240"), e("V_Y1", "200"), e("V_Y2", "0"), e("V_YEND", "-45"), e("V_RK", "80"), e("V_RT", "15"), e("V_XREF", "-4.7")
C = G["contur_PS_sus"]; ZT = C[0, 2]; R = C[C[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xo = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
ytip = R[:, 1].max(); K = np.array([xo(YK), YK]); yy = np.linspace(Y2, Y1, 50); sl = np.polyfit(yy, xo(yy), 1)[0]   # dx/dy (< 0: wider back)
E = np.array([K[0] + sl * (YEND - YK), YEND]); T = np.array([0.0, ytip])
def bar(P0, Vc, P1, Rr, n=40):                         # two straight runs P0-Vc-P1 joined by an arc of radius Rr at Vc
    u1 = (P0 - Vc) / np.linalg.norm(P0 - Vc); u2 = (P1 - Vc) / np.linalg.norm(P1 - Vc); ph = np.arccos(np.clip(u1 @ u2, -1, 1)) / 2
    t = Rr / np.tan(ph); A1, A2 = Vc + u1 * t, Vc + u2 * t; Cc = Vc + (u1 + u2) / np.linalg.norm(u1 + u2) * Rr / np.sin(ph)
    b1, b2 = np.arctan2(*(A1 - Cc)[::-1]), np.arctan2(*(A2 - Cc)[::-1]); db = np.angle(np.exp(1j * (b2 - b1)))
    arc = Cc + Rr * np.c_[np.cos(b1 + np.linspace(0, db, n)), np.sin(b1 + np.linspace(0, db, n))]
    L = np.vstack([P0, arc, P1]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
    return np.c_[[np.interp(np.arange(0, d[-1], 1.0), d, L[:, i]) for i in (0, 1)]].T
right = bar(T, K, E, RK); left = right * [-1, 1]
tipL = np.array([-1e-3, 0]) + T; full = bar(right[min(30, len(right) - 1)] * [-1, 1], T, right[min(30, len(right) - 1)], RT)   # rounded tip
ang = np.degrees(np.arctan2(K[0] - T[0], T[1] - K[1])); ang2 = np.degrees(np.arctan(-sl))
print("V: varful y %.0f, latura din fata spre K (x %.1f, y %.0f) la %.1f grd de axa; dupa cot (R %.0f) latura dreapta la %.1f grd, pana la (x %.1f, y %.0f)" % (
    ytip, K[0], K[1], ang, RK, ang2, E[0], E[1]))
for y in (200, 120, 40, 0, -40):
    xv = np.interp(-y, -right[:, 1], right[:, 0]); print("   y %4.0f: V x %.1f, conturul PS acum x %.1f (mutat %+.1f m)" % (y, xv, xo(y), xv - xo(y)))
out = {"contur_V_D": np.c_[right, np.full(len(right), ZT)], "contur_V_S": np.c_[left, np.full(len(left), ZT)], "contur_V_varf": np.c_[full, np.full(len(full), ZT)]}
v = RF["R002 169_C__v"].astype(float); v[:, 0] -= XR; ref = []                  # the reference's outline from above (its own axis)
for y in np.arange(v[:, 1].max() - 1, YEND - 1, -2.0):
    s = v[np.abs(v[:, 1] - y) < 1.5]
    if len(s): ref.append((s[:, 0].max(), s[:, 0].min(), y))
ref = np.array(ref); zr = v[:, 2].max() + 4
out["ref_contur_169C"] = np.vstack([np.c_[ref[:, 0], ref[:, 2], np.full(len(ref), zr)], np.c_[ref[::-1, 1], ref[::-1, 2], np.full(len(ref), zr)]])
np.savez(OUT, **out); print("SALVAT", OUT)
