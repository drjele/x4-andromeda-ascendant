# The two external reference models compared with each other, and the average proportions taken: each model sampled on
# its surface (area-weighted points), its robust extents (0.5-99.5 percentile) per axis measured, both brought to the
# average extents (per-axis scale, centred), the second aligned onto the first by ICP limited to a pitch and a shift along/up (the ships are symmetric), then the distance from every
# point of one to the other measured both ways (metres at the real size). Writes the stats, colour maps of the deviation
# from above / the side / behind for both models, both normalised models as OBJ, and our model scaled to the average.
# Usage: python ref_compare.py <a.obj> <b.obj> <ours.npz> <out_dir>
import sys, os, json, numpy as np, cv2
from scipy.spatial import cKDTree
A_OBJ, B_OBJ, OURS, OD = sys.argv[1:5]; os.makedirs(OD, exist_ok=True); rng = np.random.default_rng(0)
def load_obj(p):
    V, F = [], []
    for l in open(p):
        if l.startswith("v "): V.append(l.split()[1:4])
        elif l.startswith("f "): F.append([int(x.split("/")[0]) - 1 for x in l.split()[1:4]])
    return np.array(V, float), np.array(F, int)
def sample(V, F, n=400000):
    T = V[F]; a = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1); i = rng.choice(len(F), n, p=a / a.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1); return T[i, 0] * (1 - s)[:, None] + T[i, 1] * (s * (1 - r2))[:, None] + T[i, 2] * (s * r2)[:, None]
def ext(P): lo, hi = np.percentile(P, 0.5, 0), np.percentile(P, 99.5, 0); return lo, hi
Va, Fa = load_obj(A_OBJ); Vb, Fb = load_obj(B_OBJ); Pa, Pb = sample(Va, Fa), sample(Vb, Fb)
(la, ha), (lb, hb) = ext(Pa), ext(Pb); Ea, Eb = ha - la, hb - lb; Em = (Ea + Eb) / 2
prop = lambda E: {"L_W": round(E[1] / E[0], 3), "L_H": round(E[1] / E[2], 3), "W_H": round(E[0] / E[2], 3), "L_m": round(E[1], 1), "W_m": round(E[0], 1), "H_m": round(E[2], 1)}
def norm(P, lo, hi): return (P - (lo + hi) / 2) * (Em / (hi - lo))
Na, Nb = norm(Pa, la, ha), norm(Pb, lb, hb)
# rigid ICP of b onto a
ta = cKDTree(Na[::4]); R = np.eye(3); t = np.zeros(3); Q = Nb[::4].copy()
for it in range(30):
    d, j = ta.query(Q); keep = d < np.percentile(d, 90); X, Y = Q[keep], Na[::4][j[keep]]
    mx, my = X.mean(0), Y.mean(0); mx[0] = my[0] = 0                   # symmetric ships: only a pitch (about x) and a shift in y/z
    H2 = (X - mx)[:, 1:].T @ (Y - my)[:, 1:]; th = np.arctan2(H2[0, 1] - H2[1, 0], H2[0, 0] + H2[1, 1])
    r = np.array([[1, 0, 0], [0, np.cos(th), -np.sin(th)], [0, np.sin(th), np.cos(th)]]); tt = my - r @ mx; tt[0] = 0
    Q = Q @ r.T + tt; R = r @ R; t = r @ t + tt
Nb2 = Nb @ R.T + t; ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
dab, _ = cKDTree(Nb2).query(Na); dba, _ = cKDTree(Na).query(Nb2)
pc = lambda d: {p: round(float(np.percentile(d, p)), 1) for p in (50, 75, 90, 95, 99)}
stats = {"proportii_Binkley": prop(Ea), "proportii_morenostefanuto": prop(Eb), "proportii_medie": prop(Em),
         "ICP_rotatie_grade": round(float(ang), 2), "ICP_deplasare_m": np.round(t, 1).tolist(),
         "abatere_Binkley_fata_de_moreno_m": pc(dab), "abatere_moreno_fata_de_Binkley_m": pc(dba)}
json.dump(stats, open(f"{OD}/comparatie.json", "w"), indent=1)
json.dump({"Em": Em.tolist(), "la": la.tolist(), "ha": ha.tolist(), "lb": lb.tolist(), "hb": hb.tolist(), "R": R.tolist(), "t": t.tolist()}, open(f"{OD}/transformari.json", "w")); print(json.dumps(stats, indent=1))
# colour maps: points coloured by deviation (blue 0 m -> red >= 60 m), drawn far to near per view
def cmap(d, top=60.0):
    x = np.clip(d / top, 0, 1); return np.stack([255 * (1 - x), 80 + 100 * (1 - abs(x - 0.5) * 2), 255 * x], 1).astype(np.uint8)
def view(P, d, i, j, depth, sgn, W=700):
    lo, hi = Em * -0.55, Em * 0.55; s = W / (hi[i] - lo[i]); H = int((hi[j] - lo[j]) * s); img = np.full((H, W, 3), 245, np.uint8)
    o = np.argsort(P[:, depth] * sgn); u = ((P[o, i] - lo[i]) * s).astype(int); v = (H - 1 - (P[o, j] - lo[j]) * s).astype(int); ok = (u >= 0) & (u < W) & (v >= 0) & (v < H)
    img[v[ok], u[ok]] = cmap(d[o])[ok]; return img
rows = []
for P, d, lab in ((Na, dab, "Binkley (abatere fata de morenostefanuto)"), (Nb2, dba, "morenostefanuto (abatere fata de Binkley)")):
    t1 = view(P, d, 0, 1, 2, 1); t2 = view(P, d, 1, 2, 0, -1); t3 = view(P, d, 0, 2, 1, -1)
    h = max(t.shape[0] for t in (t1, t2, t3)); pad = lambda t: np.vstack([t, np.full((h - t.shape[0], t.shape[1], 3), 245, np.uint8)])
    r = np.hstack([pad(t1), pad(t2), pad(t3)]); cv2.putText(r, lab + "  (sus | profil | spate)", (10, 30), 0, 0.8, (0, 0, 0), 2); rows.append(r)
bar = np.full((60, rows[0].shape[1], 3), 245, np.uint8)
for k in range(400): bar[15:40, 20 + k] = cmap(np.array([k / 400 * 60]))[0]
cv2.putText(bar, "0 m", (20, 56), 0, 0.6, (0, 0, 0), 1); cv2.putText(bar, "60+ m", (390, 56), 0, 0.6, (0, 0, 0), 1)
cv2.imwrite(f"{OD}/abateri.png", np.vstack(rows + [bar]))
# normalised references and our model at the average proportions, as OBJ
def write(path, V, F, lo, hi, M=np.eye(3), tt=np.zeros(3)):
    W_ = ((V - (lo + hi) / 2) * (Em / (hi - lo))) @ M.T + tt
    with open(path, "w") as f:
        f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in W_)); f.write("".join("f %d %d %d\n" % tuple(x + 1) for x in F))
write(f"{OD}/Binkley_medie.obj", Va, Fa, la, ha); write(f"{OD}/morenostefanuto_medie.obj", Vb, Fb, lb, hb, R, t)
z = np.load(OURS); names = [k[2:] for k in z.files if k.startswith("v|") and not k.startswith("v|SRC")]
Vo = np.vstack([z["v|" + n] for n in names]).astype(float); lo, hi = ext(Vo)
with open(f"{OD}/noi_V17_medie.obj", "w") as f:
    off = 0
    for n in names:
        v = (z["v|" + n].astype(float) - (lo + hi) / 2) * (Em / (hi - lo)); t_ = z["t|" + n].astype(int)
        f.write("o %s\n" % n.replace("|", "_")); f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in v)); f.write("".join("f %d %d %d\n" % tuple(x + 1 + off) for x in t_)); off += len(v)
print("noi V17 inainte", prop(hi - lo))
