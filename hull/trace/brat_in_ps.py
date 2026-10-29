# The rear arm goes INTO the PS instead of meeting it edge to edge (asked: "dacă e grea întâlnirea ca pe muchie, închide
# tubul, fă cum a mers unde nu se vede muchia"): from its mouth the tube is carried on E m forward along its own direction,
# narrowing by ALFA degrees (so it dives into the PS at a clear angle and covers the PS's rounded back edge), and closed with
# a flat fan cap - the visible edge becomes the line where the arm enters the PS, like 103 / the front arm. The arm's faces
# (they faced inwards) are turned outwards. D built, S = mirror. Usage: python brat_in_ps.py <pieces.npz> <out.npz>
# env BPS_E=6 BPS_PAS=2 BPS_ALFA=30 (longer / gentler came out of the PS on the outer side); BPS_GULER=B (cuff over the PS's
# end, the arm grown B m over its last BPS_SPATE m, carried BPS_S1 m forward, then diving in - like the joints that don't show)
import sys, os, numpy as np, trimesh, igl
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); OUT = sys.argv[2]; MX = -1700.0
E, PAS, ALFA = float(os.environ.get("BPS_E", "6")), float(os.environ.get("BPS_PAS", "2")), np.radians(float(os.environ.get("BPS_ALFA", "30")))
v = D["brat_spate_D__v"].astype(float); f = D["brat_spate_D__f"][:, ::-1].astype(np.int64)    # faces turned outwards
Ed = np.sort(np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], 1); Ed, c = np.unique(Ed, axis=0, return_counts=True)
be = Ed[c == 1]; be = be[(v[be, 1] > -60).all(1)]                       # the mouth's edges
nb = {}
for a, b in be: nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
loop = [be[0, 0]]; prev = None
while True:
    nx = [q for q in nb[loop[-1]] if q != prev]
    if not nx or nx[0] == loop[0]: break
    prev = loop[-1]; loop.append(nx[0])
loop = np.array(loop); rim = v[loop]; cen = rim.mean(0)
y0 = rim[:, 1].mean(); back = (v[:, 1] < y0 - 8) & (v[:, 1] > y0 - 12); tb = cKDTree(v[back][:, [0, 2]])
d = rim - v[back][tb.query(rim[:, [0, 2]])[1]]; d /= np.linalg.norm(d, axis=1)[:, None]       # forward, along the arm
rad = rim - cen; rr = np.linalg.norm(rad, axis=1); rad /= rr[:, None]
B_, LB, S1 = float(os.environ.get("BPS_GULER", "0")), float(os.environ.get("BPS_SPATE", "40")), float(os.environ.get("BPS_S1", "10"))
if B_ > 0:                                              # a cuff: the arm grows B m over its last LB m, carries on S1 m over the
    E = S1 + (B_ + 6) / np.tan(ALFA)                    # PS's end, then dives into the PS at ALFA (6 m below its own size)
    sb = (y0 - v[:, 1]) / max(np.abs(d[:, 1]).mean(), 0.3); bk = (v[:, 1] < y0 + 0.5) & (sb < LB)
    tr = cKDTree(rim[:, [0, 2]]); jb = tr.query(v[bk][:, [0, 2]])[1]; u_ = np.clip(1 - sb[bk] / LB, 0, 1)
    v = v.copy(); v[bk] += rad[jb] * (B_ * u_ * u_ * (3 - 2 * u_))[:, None]; rim = v[loop]
off = lambda s: (B_ if s <= S1 else B_ - (s - S1) * np.tan(ALFA)) if B_ > 0 else -s * np.tan(ALFA)
K = int(np.ceil(E / PAS)); rings = [rim]
for k in range(1, K + 1):
    s = min(k * PAS, E); rings.append(rim + s * d + rad * off(s))
V = np.vstack([v] + rings[1:]); n0 = len(v); m = len(loop); F = [f]
idx = [loop] + [n0 + (k - 1) * m + np.arange(m) for k in range(1, K + 1)]
for k in range(K):
    a, b = idx[k], idx[k + 1]; a2, b2 = np.roll(a, -1), np.roll(b, -1)
    F.append(np.c_[a, a2, b2]); F.append(np.c_[a, b2, b])
cc = rings[-1].mean(0); V = np.vstack([V, cc]); ic = len(V) - 1; last = idx[-1]
F.append(np.c_[last, np.roll(last, -1), np.full(m, ic)]); F = np.vstack(F)
t = trimesh.Trimesh(V, F, process=False); trimesh.repair.fix_winding(t); F = np.asarray(t.faces)
fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); fc = V[F].mean(1); T = cKDTree(V)
smp = np.random.default_rng(0).choice(len(F), 2000, replace=False)
out_ = np.mean([(fn[i] @ (fc[i] - V[T.query_ball_point(fc[i], 45)].mean(0))) > 0 for i in smp])
if out_ < 0.5: F = F[:, ::-1]; out_ = 1 - out_
P = D["PS__v"].astype(float); PF = D["PS__f"].astype(np.int64)
ext = V[n0:]; sd = -igl.signed_distance(ext, P, PF, sign_type=igl.SIGNED_DISTANCE_TYPE_FAST_WINDING_NUMBER)[0]
print("BRAT IN PS: gura %d varfuri, prelungit %.0f m (pas %.0f, ingustat %.0f grd), capac; normale spre exterior %.0f%%" % (m, E, PAS, np.degrees(ALFA), 100 * out_))
for k in sorted({1, min(3, K), min(5, K), K}):
    seg = sd[(k - 1) * m:k * m]; print("   inel %.0f m: in PS %.0f%% (cel mai departe in afara %.1f m)" % (k * PAS, 100 * (seg > 0).mean(), max(-seg.min(), 0)))
S = V.copy(); S[:, 0] = 2 * MX - S[:, 0]
np.savez(OUT, v_d=V - [MX, 0, 0], f_d=F, v_s=S - [MX, 0, 0], f_s=F[:, ::-1])
