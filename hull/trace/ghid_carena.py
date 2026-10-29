# Guides for the keel (asked: now guides for sep_PS_carena), to the clean-line standard. Big side (top, z ZT): straight
# back at the old back y, straight sides (fitted on y SY0..SY1), slanted sides towards the tip (fitted on y DY0..DY1) meeting
# on the axis, corners rounded (back RB, side/slant RS, tip RT) - lines + tangent arcs, symmetric. Floor (z ZF): the same
# shape x SC (the keel's own rule: the big side the shape of the small one), placed as the current floor. Ribs (y = const,
# every PAS m) and the middle spine (x = 0): sections of the ruled solid between the two outlines - straight walls, open at
# the top (the keel is attached there). Usage: python ghid_carena.py <fund_contururi npz (carena_sus / carena_jos)> <out.npz>
# CAR_SUS=file:key the big side as given; JOS_Y0=y the floor's back there.
# env ZT=280 ZF=247 SC=0.6 RB=8 RS=20 RT=20 JOS_DY=0 SY0=0 SY1=190 DY0=265 DY1=335 PAS=40 DZ=0
import sys, os, numpy as np, trimesh
C = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
ZT, ZF, SC, RB, RS, RT, SY0, SY1, DY0, DY1, PAS, DZ = (e(k, d) for k, d in (("ZT", "280"), ("ZF", "247"), ("SC", "0.6"), ("RB", "8"), ("RS", "20"),
    ("RT", "20"), ("SY0", "0"), ("SY1", "190"), ("DY0", "265"), ("DY1", "335"), ("PAS", "40"), ("DZ", "0")))
S = C["carena_sus"]; J = C["carena_jos"]; R_ = S[S[:, 0] > 0]
CS = os.environ.get("CAR_SUS")                       # file:key - the big side taken as is (e.g. the rim's inner outline 10 m in)
YB = S[:, 1].min(); m1 = (R_[:, 1] > SY0) & (R_[:, 1] < SY1); b1, a1 = np.polyfit(R_[m1, 1], R_[m1, 0], 1)
m2 = (R_[:, 1] > DY0) & (R_[:, 1] < DY1); b2, a2 = np.polyfit(R_[m2, 1], R_[m2, 0], 1)
def seg(p, q, step=0.5): n = max(int(np.linalg.norm(q - p) / step), 2); return np.linspace(p, q, n)
def arc(c, r, a0, a1_):
    n = max(int(abs(a1_ - a0) / np.radians(3)) + 2, 3); tt = np.linspace(a0, a1_, n); return np.c_[c[0] + r * np.cos(tt), c[1] + r * np.sin(tt)]
def corner(P, d0, d1, r):
    th = np.arccos(np.clip(-d0 @ d1, -1, 1)); L = r / np.tan(th / 2); t0 = P - d0 * L; t1 = P + d1 * L
    bis = d1 - d0; bis /= np.linalg.norm(bis); c = P + bis * r / np.sin(th / 2)
    return t0, t1, arc(c, r, np.arctan2(t0[1] - c[1], t0[0] - c[0]), np.arctan2(t1[1] - c[1], t1[0] - c[0]))
Ptip = np.array([0.0, -a2 / b2]); Pk = np.array([0.0, 0.0]); yk = (a2 - a1) / (b1 - b2); Pk = np.array([a1 + b1 * yk, yk]); Pb = np.array([a1 + b1 * YB, YB])
# right half, clockwise from the tip: tip -> slant -> knee -> side -> back corner -> back edge -> axis
dT = (Pk - Ptip) / np.linalg.norm(Pk - Ptip); dS = (Pb - Pk) / np.linalg.norm(Pb - Pk); dB = np.array([-1.0, 0.0])
dTin = np.array([1.0, 0.0]) if False else None
# tip round: between the mirror slant (coming in) and this slant (going out)
dM = np.array([dT[0], -dT[1]]) * [1, -1] if False else np.array([dT[0], dT[1]]) * [1, 1]
dIn = np.array([dT[0], -dT[1]]); dIn = np.array([-(-dT[0]), -dT[1]]) * 0 + np.array([dT[0], -dT[1]]) * [1, 1]
# incoming direction at the tip from the left slant: the mirror of the right slant's outgoing, reversed
dIn = -np.array([-dT[0], dT[1]])
t0, t1, ta = corner(Ptip, dIn, dT, RT); k0, k1, ka = corner(Pk, dT, dS, RS); c0, c1, ca = corner(Pb, dS, dB, RB)
mid = ta[len(ta) // 2:] if False else ta
half = np.vstack([ta[np.argmin(np.abs(ta[:, 0])):], seg(t1, k0)[1:], ka[1:], seg(k1, c0)[1:], ca[1:], seg(c1, np.array([0.0, YB]))[1:]])
top = np.vstack([half, (half[::-1] * [-1, 1])[1:-1]])
if CS:
    fn_, kk_ = CS.split(":"); top = np.load(fn_)[kk_][:, :2]; top = top[:-1] if np.allclose(top[0], top[-1]) else top
    S = top; YB = top[:, 1].min()
y0j, y1j = S[:, 1].min(), S[:, 1].max(); flo = np.c_[top[:, 0] * SC, y1j - (y1j - top[:, 1]) * SC - (1 - SC) * (y1j - y0j) / 2]
flo[:, 1] += (J[:, 1].min() - flo[:, 1].min()) + e("JOS_DY", "0")   # placed like the current floor, moved JOS_DY m (same size)
if os.environ.get("JOS_Y0"): flo[:, 1] += float(os.environ["JOS_Y0"]) - flo[:, 1].min()   # floor's back at that y
out = {"contur_carena_sus": np.c_[np.vstack([top, top[:1]]), np.full(len(top) + 1, ZT)], "contur_carena_jos": np.c_[np.vstack([flo, flo[:1]]), np.full(len(flo) + 1, ZF)]}
N = len(top); V = np.vstack([np.c_[top, np.full(N, ZT)], np.c_[flo, np.full(N, ZF)], [[0, top[:, 1].mean(), ZT], [0, flo[:, 1].mean(), ZF]]])
F = [[i, (i + 1) % N, N + (i + 1) % N] for i in range(N)] + [[i, N + (i + 1) % N, N + i] for i in range(N)]
F += [[2 * N, (i + 1) % N, i] for i in range(N)] + [[2 * N + 1, N + i, N + (i + 1) % N] for i in range(N)]
t = trimesh.Trimesh(V, np.array(F), process=False)
def open_section(L, keep):                            # the loop without its top edge (z = ZT), as one open line
    L = L[:-1] if np.allclose(L[0], L[-1]) else L; top_ = np.abs(L[:, 2] - ZT) < 1e-3
    if not top_.any(): return L
    i = np.where(top_)[0]; k_ = i[np.argmax(L[i, keep])]; R2 = np.roll(L, -k_, 0)
    j = np.where(np.abs(R2[:, 2] - ZT) < 1e-3)[0]; jl = j[np.argmin(R2[j, keep])] if len(j) else len(R2) - 1
    seg_a = R2[: jl + 1]; seg_b = np.r_[R2[jl:], R2[:1]]
    return seg_a if (seg_a[:, 2] < ZT - 0.1).sum() > (seg_b[:, 2] < ZT - 0.1).sum() else seg_b
k = 0
for y in np.arange(np.ceil((YB + 2) / PAS) * PAS, top[:, 1].max() - 2, PAS):
    s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    L = max(s.discrete, key=len); out["sectiune_carena_%02d" % k] = open_section(L, 0); k += 1
s = t.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0]); out["spinare_carena_mijloc"] = open_section(max(s.discrete, key=len), 1)
for kk in out: out[kk] = out[kk] + [0, 0, DZ]
d_ = np.diff(top, axis=0); ang = np.degrees(np.abs(np.angle(np.exp(1j * (np.arctan2(d_[1:, 1], d_[1:, 0]) - np.arctan2(d_[:-1, 1], d_[:-1, 0]))))))
print("CARENA GHIDAJE: sus (z %.0f) spate y %.1f +-%.1f, laturi x = %.1f %+.3f y, oblice x = %.1f %+.3f y, varf y %.1f (R %.0f), cot R %.0f, colt R %.0f; frangere max %.1f grd" % (
    ZT, YB, Pb[0], a1, b1, a2, b2, top[:, 1].max(), RT, RS, RB, ang.max()))
print("   jos (z %.0f) aceeasi forma x%.1f: x +-%.1f, y %.1f..%.1f; %d nervuri (y = const, la %.0f m) + spinarea, din solidul dintre ele (pereti drepti); volum %.0f m3" % (
    ZF, SC, flo[:, 0].max(), flo[:, 1].min(), flo[:, 1].max(), k, PAS, abs(t.volume)))
np.savez(OUT, **out)
