# The rear arms as their own pieces (asked: rebuilt whole - round, 10 % thicker, open at the ends, a slight funnel where they
# meet PS): a tube swept directly along a smooth centre line, ring by ring (no field, no voxels): the arm's straight middle
# (3D fit of the confirmed sections' middle), one smooth U (quintic, tangent to both) at the reference loop's bottom, the
# reference loop's far branch straight (3D fit) up to the tip. Round section, radius R = 1.1 x the equal-area radius of the
# old 86 x 49 ellipse; over the first FUN m from PS the radius eases up by +FUNK (the funnel). Frames carried without
# turning (parallel transport). Both ends open. Right arm built, left mirrored. Writes verts / quad faces per arm.
# BRAT_TURTIRE: the section near PS wider than tall (x factor, eased out with the funnel); BRAT_TAIETURA: the arm piece
# starts that far along (the joint ring, PS carries the part before it as a socket); the rings are written for PS.
# BRAT_PS_SECT=<ps.npz>,<y>: the arm starts as PS's exact section at y (its outline), leaves it along -y, eases into the round tube.
# Usage: python brate_tub.py <elipse_ghidaje.npz> <tub_corp.npz> <out.npz> [y_start] [lift]
import sys, os, numpy as np
R = np.load(sys.argv[1]); T = np.load(sys.argv[2]); OUT = sys.argv[3]; YS = float(sys.argv[4]) if len(sys.argv) > 4 else -40.0
LIFT = float(sys.argv[5]) if len(sys.argv) > 5 else 80.0; FUN, FUNK, NA, STEP = float(os.environ.get("BRAT_PALNIE_L", "200")), float(os.environ.get("BRAT_PALNIE", "0.2")), 72, 2.0
ex, ix, su, jo = R["br_ext"], R["br_int"], R["br_sus"], R["br_jos"]
TA, TB = (ex[-1, 0] - ix[-1, 0]) / 2, (su[-1, 2] - jo[-1, 2]) / 2; R0 = 1.1 * np.sqrt(TA * TB)
m = ex[:, 1] < -450; mid = np.stack([(ex[m, 0] + ix[m, 0]) / 2, ex[m, 1], (su[m, 2] + jo[m, 2]) / 2], 1)
def fit(P): c = P.mean(0); d = np.linalg.svd(P - c)[2][0]; return c, d / np.linalg.norm(d)
cA, dA = fit(mid); dA = dA if dA[1] < 0 else -dA
C = T["C"] * [-1, 1, 1]; kb = int(np.argmin(C[:, 1])); FB = C[kb:][(C[kb:, 1] > -1150) & (C[kb:, 1] < -560)]; cB, dB = fit(FB); dB = dB if dB[1] > 0 else -dB
on = lambda c, d, y: c + d * ((y - c[1]) / d[1])
yt = C[kb, 1] + LIFT; p0, p1 = on(cA, dA, yt), on(cB, dB, yt); dd = np.linalg.norm(p1 - p0); Lt = 1.7 * dd
zt_, zb_ = R["ps_sus"][np.argmin(R["ps_sus"][:, 1]), 2], R["ps_jos"][np.argmin(R["ps_jos"][:, 1]), 2]   # PS at its back: top, flat bottom
PSG = float(os.environ.get("PS_GROS", "1")); PSN = float(os.environ.get("PS_N", "2")); start = on(cA, dA, YS)
wps = R["ps_lat"][np.argmin(R["ps_lat"][:, 1]), 0]                      # PS's half width at its back; its height where the arm enters
hloc = (zt_ - zb_) * PSG * max(1 - (abs(start[0]) / wps) ** PSN, 0) ** (1 / PSN)   # (the arrowhead section thins to the sides)
RJ = hloc / 2 if os.environ.get("PS_FUND_PLAT") else None
if os.environ.get("BRAT_FUND"): zb_, RJ = float(os.environ["BRAT_FUND"]), float(os.environ["BRAT_RJ"])   # PS given directly (frustum)
start[2] = zb_ + RJ if RJ else (zt_ + zb_) / 2                          # the arm starts on PS's flat bottom, as thick as PS right there
dA = (p0 - start) / np.linalg.norm(p0 - start)
def herm(a, ta, b, tb, L, n):
    t = np.linspace(0, 1, n, endpoint=False)
    h = [1 - 10 * t ** 3 + 15 * t ** 4 - 6 * t ** 5, t - 6 * t ** 3 + 8 * t ** 4 - 3 * t ** 5, 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5, -4 * t ** 3 + 7 * t ** 4 - 3 * t ** 5]
    return np.outer(h[0], a) + np.outer(h[1], ta * L) + np.outer(h[2], b) + np.outer(h[3], tb * L)
bend = herm(p0, dA, p1, dB, Lt, max(int(2.5 * dd), 40))
def line(p, q): n = max(int(np.linalg.norm(q - p) / STEP), 1); return p + np.outer(np.arange(n) / n, q - p)
end = on(cB, dB, -427.0)
PSS = os.environ.get("BRAT_PS_SECT")                                    # the start = PS's own section at y YP (cut from its mesh):
if PSS:                                                                 # the line leaves it straight back (-y), then joins the arm line
    import trimesh
    fps, YP = PSS.split(","); YP = float(YP); Z_ = np.load(fps); tm = trimesh.Trimesh(Z_["v"], Z_["f"], process=False)
    sec = tm.section(plane_origin=[0, YP, 0], plane_normal=[0, 1, 0]); segs = sec.discrete
    seg = max([q for q in segs if q[:, 0].mean() > 0], key=len); seg = seg[:, [0, 2]]
    c0 = np.array([seg[:, 0].mean(), YP, seg[:, 1].mean()]); LJ = float(os.environ.get("BRAT_PS_LEG", "160"))
    q = start + dA * ((YP - LJ - start[1]) / dA[1])                     # on the arm line LJ m behind the section
    P = np.vstack([herm(c0, np.array([0, -1.0, 0]), q, dA, 0.8 * LJ, int(LJ / STEP)), line(q, p0), bend, line(p1, end), [end]]); start = c0
else:
    P = np.vstack([line(start, p0), bend, line(p1, end), [end]])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, s[-1], STEP); P = np.stack([np.interp(u, s, P[:, i]) for i in range(3)], 1)
for _ in range(3):                                                     # the joins of line and curve evened out (tiny moves)
    P[1:-1] = P[1:-1] + 0.25 * (P[:-2] + P[2:] - 2 * P[1:-1])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
Tn = np.gradient(P, axis=0); Tn /= np.linalg.norm(Tn, axis=1)[:, None]
sd = np.cross(Tn[0], [0, 0, 1.0]); sd /= np.linalg.norm(sd); F1 = []
for k in range(len(P)):                                                # parallel transport (double reflection)
    if k:
        v1 = P[k] - P[k - 1]; c1 = v1 @ v1; rL = sd - (2 / c1) * (v1 @ sd) * v1; tL = Tn[k - 1] - (2 / c1) * (v1 @ Tn[k - 1]) * v1
        v2 = Tn[k] - tL; c2 = v2 @ v2; sd = rL - (2 / c2) * (v2 @ rL) * v2 if c2 > 1e-12 else rL; sd /= np.linalg.norm(sd)
    F1.append(sd.copy())
F1 = np.array(F1); F2 = np.cross(F1, Tn)
w = np.clip(1 - s / FUN, 0, 1); w = w * w * (3 - 2 * w); Rk = R0 * (1 + FUNK * w) if RJ is None else R0 + (RJ - R0) * w   # from PS's
                                                                       # thickness at the joint, flowing into the arm's own
ang = np.linspace(0, 2 * np.pi, NA, endpoint=False)
FLT = float(os.environ.get("BRAT_TURTIRE", "1"))                        # flatter near PS (wider than tall), round further on
Ak, Bk = Rk * (1 + (FLT - 1) * w), Rk.copy()
SPL = float(os.environ.get("BRAT_TAIETURA", "0")); ks = int(np.searchsorted(s, SPL))   # the arm piece starts at the joint cut
SA = os.environ.get("BRAT_START")                                       # the start shaped like PS there (a rounded slab: half width,
if SA:                                                                  # half height, exponent), easing into the round tube
    a0, b0, n0 = [float(t) for t in SA.split(",")]; Ak, Bk = R0 + (a0 - R0) * w, R0 + (b0 - R0) * w; NK = 2 + (n0 - 2) * w
else: NK = np.full(len(P), 2.0)
ca_, sa_ = np.cos(ang)[None, :], np.sin(ang)[None, :]
cx_ = np.sign(ca_) * np.abs(ca_) ** (2 / NK[:, None]); sx_ = np.sign(sa_) * np.abs(sa_) ** (2 / NK[:, None])   # superellipse points
if PSS:                                                                 # PS's section's radius by angle in the start frame, blended
    d2 = np.stack([(seg[:, 0] - c0[0]) * F1[0, 0] + (seg[:, 1] - c0[2]) * F1[0, 2], (seg[:, 0] - c0[0]) * F2[0, 0] + (seg[:, 1] - c0[2]) * F2[0, 2]], 1)
    th = np.arctan2(d2[:, 1], d2[:, 0]); rr = np.linalg.norm(d2, axis=1); o_ = np.argsort(th)
    rP = np.interp(ang, th[o_], rr[o_], period=2 * np.pi)              # (into the tube's circle over the funnel)
    rad = w[:, None] * rP[None, :] + (1 - w[:, None]) * R0
    V = (P[ks:, None] + (rad * np.cos(ang)[None, :])[ks:, :, None] * F1[ks:, None] + (rad * np.sin(ang)[None, :])[ks:, :, None] * F2[ks:, None]).reshape(-1, 3)
    Ak = Bk = rad.max(1); print("BRAT start = sectiunea PS la y %.0f: centru (%.0f, %.0f), %.0f x %.0f m" % (YP, c0[0], c0[2], np.ptp(seg[:, 0]), np.ptp(seg[:, 1])))
else:
    V = (P[ks:, None] + (Ak[:, None] * cx_)[ks:, :, None] * F1[ks:, None] + (Bk[:, None] * sx_)[ks:, :, None] * F2[ks:, None]).reshape(-1, 3)
K = len(P) - ks; Fq = np.array([(k * NA + i, k * NA + (i + 1) % NA, (k + 1) * NA + (i + 1) % NA, (k + 1) * NA + i) for k in range(K - 1) for i in range(NA)])
Vl = V * [-1, 1, 1]; Fl = Fq[:, ::-1]
np.savez(OUT, v_d=V.astype(np.float32), f_d=Fq.astype(np.int32), v_s=Vl.astype(np.float32), f_s=Fl.astype(np.int32), centru=P,
         F1=F1, F2=F2, Ak=Ak, Bk=Bk, s=s, ks=ks, T=Tn)                    # the rings (for PS's sockets) and the cut ring
tn = np.diff(Tn, axis=0); kap = np.linalg.norm(tn, axis=1) / np.diff(s)
print("BRATE tub: raza %.1f m (diametru %.0f; elipsa veche %.0f x %.0f), la imbinare raza %.1f, pe %d m; linie %.0f m, %d inele x %d; raza minima de curbura a liniei %.0f m; start (%.0f, %.0f, %.0f), capat (%.0f, %.0f, %.0f), deschise la capete" % (
    R0, 2 * R0, 2 * TA, 2 * TB, Rk[0], FUN, s[-1], K, NA, 1 / kap.max(), *start, *end))
