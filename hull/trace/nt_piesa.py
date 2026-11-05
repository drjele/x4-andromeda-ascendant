# One reference piece rebuilt from guides, generically (the terrain method, on its own frame): welded, split in bodies; each body's
# frame = principal axes (y longest, z thinnest; central pieces keep the ship's axes and are mirrored about x = 0); read as terrain
# top / bottom (ref_teren.py), solid inside the smoothed outline (ps_din_ghidaje.py), remeshed + reduced (mesh_finisaj.py), back to
# ship coordinates. Up to 3 attempts (finer each time, sheet read on the 3rd); scored against the piece both ways. Fails -> the cleaned
# reference body itself (welded, no slivers). Writes <out>/<id>.npz (v,f,uv,methods) + <id>_g.npz (guides, polylines in ship coords).
# Usage: python nt_piesa.py <toate.npz> <out_dir> <id> <name> [name...]
import sys, os, json, subprocess, numpy as np, trimesh
from scipy.spatial import cKDTree as KD
HERE = os.path.dirname(os.path.abspath(__file__)); TOATE, OD, ID = sys.argv[1], sys.argv[2], sys.argv[3]; NAMES = sys.argv[4:]; Z = np.load(TOATE); PY = sys.executable; S_UV = 4720.0
W = os.path.join(OD, "w_" + ID); os.makedirs(W, exist_ok=True)
V, F, Mt = [], [], []; n = 0
for k in NAMES:
    k = k.replace(" ", "_"); v, f = Z[k + "__v"].astype(float), Z[k + "__f"]; V.append(v); F.append(f + n); n += len(v)
    Mt += list(Z[k + "__m"]) if len(Z[k + "__m"]) else [""] * len(f)
V, F = np.vstack(V), np.vstack(F)
xr = (V[:, 0].min(), V[:, 0].max()); cen_ = xr[0] < -0.5 * xr[1] and xr[1] > -0.5 * xr[0] and xr[1] > 0                 # the validated front arms were built from the S side: every base = the S
if cen_ or V[:, 0].mean() < 0: V = V * [-1, 1, 1]; F = F[:, ::-1]                                                     # half, read on the x > 0 side; a central piece's kept (right) half too
tm = trimesh.Trimesh(V, F, process=False); area = tm.area_faces; mats = {}
for a, m in zip(area, Mt): mats[str(m)] = mats.get(str(m), 0) + a
MAT = max(mats, key=mats.get) if mats else "Material_8"
# bodies = joined by shared vertices (welded at 1 cm), not by shared edges: this model's big shells have non-manifold seams an edge split would tear apart
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components as _cc
_k = np.round(V / 0.01).astype(np.int64); _u, _i, _inv = np.unique(_k, axis=0, return_index=True, return_inverse=True); _inv = _inv.ravel(); _V = V[_i]; _F = _inv[F]; _F = _F[(_F[:, 0] != _F[:, 1]) & (_F[:, 1] != _F[:, 2]) & (_F[:, 0] != _F[:, 2])]
_a = np.r_[_F[:, 0], _F[:, 1]]; _b = np.r_[_F[:, 1], _F[:, 2]]; _nc, _l = _cc(coo_matrix((np.ones(len(_a)), (_a, _b)), shape=(len(_V), len(_V))), directed=False); _fl = _l[_F[:, 0]]
bodies = [trimesh.Trimesh(_V, _F[_fl == c], process=False) for c in np.unique(_fl)]
for _b_ in bodies: _b_.remove_unreferenced_vertices()
BIG = [b for b in bodies if b.area > 1e-3]
if os.environ.get("NT_SHIP"):                                                 # bodies of a mixed piece that the validated ship already has: left out
    ks = KD(np.load(os.environ["NT_SHIP"])["p"]); B2 = []
    for b in BIG:
        d = ks.query(b.vertices)[0]
        if (d < 8).mean() < 0.6: B2.append(b)
    print("fara cele existente:", len(BIG), "->", len(B2)); BIG = B2
lim = float(os.environ.get("NT_LIM", "0.002")) * max(b.area for b in BIG); keep = [b for b in BIG if b.area >= lim]; rest = [b for b in BIG if b.area < lim]
central = cen_
def frame(b):
    if central: return np.eye(3), np.zeros(3)
    P = b.sample(4000) if b.area > 0 else b.vertices; c = (P.min(0) + P.max(0)) / 2; ev, U = np.linalg.eigh(np.cov((P - c).T))     # ascending: z thinnest, x middle, y longest
    R = np.stack([U[:, 1], U[:, 2], U[:, 0]], 0)
    if np.linalg.det(R) < 0: R[0] *= -1
    return R, c
def build(b, att):
    R, c = frame(b); lv = (b.vertices - c) @ R.T if not central else b.vertices.copy(); L = np.ptp(lv, axis=0); L1, L2, L3 = L[1], L[0], L[2]
    cell = float(np.clip(max(L1, L2) / 300 / (1.0 if att == 0 else 1.5 if att == 1 else 2.0), 0.2, 2.0))
    if (L1 / cell) * (L2 / cell) > 2.2e6: cell = float(np.sqrt(L1 * L2 / 2.2e6))
    sig = cell * (1.4 if att == 0 else 1.0); gap = float(np.clip(L3 / 5, 0.3, 4)); osig = float(np.clip(min(L1, L2) / 25, 0.4, 5)); rk = float(np.clip(L3 / 6, cell * 0.6, 3))
    if central and L[0] > 300: cell, sig, osig, rk, gap = (2.0, 1.5, 1.2)[att], (3.0, 2.0, 1.5)[att], 5.0, 3.0, 4.0
    ref = os.path.join(W, "ref.npz"); np.savez(ref, v=lv, f=b.faces); ter = os.path.join(W, "t.npz"); raw = os.path.join(W, "raw.npz"); fin = os.path.join(W, "fin.npz"); joc = os.path.join(W, "joc.npz")
    y0, y1 = lv[:, 1].min(), lv[:, 1].max(); x0, x1 = lv[:, 0].min(), lv[:, 0].max()
    ys = ",".join("%.2f" % t for t in np.linspace(y0, y1, max(4, min(14, int(L1 / 40) + 3)) + 2)[1:-1]); xs = ",".join("%.2f" % t for t in np.linspace(x0, x1, 5)[1:-1])
    if central: xs = ",".join("%.2f" % t for t in np.linspace(0, x1, 5)[:-1])
    e = dict(os.environ, TEREN_GAP="%g" % gap)
    if not central: e["FARA_OGLINDA"] = "1"
    if att >= 1 or L3 < 4: e["FOAIE_GROS"] = "%g" % max(0.8, 4 * cell)
    r = subprocess.run([PY, os.path.join(HERE, "ref_teren.py"), ref, ter, os.path.join(W, "t.png"), "0", ys, xs, "%g" % cell, "%g" % sig, ID, "%g" % osig], capture_output=True, text=True, env=e, timeout=900)
    if r.returncode: raise RuntimeError("teren " + r.stderr[-200:])
    Tt = np.load(ter); fo = Tt["foot"].astype(bool); th = float(np.median((Tt["top"] - Tt["bot"])[fo])) if fo.any() else 1.0   # the piece's real thickness (L3 includes its curvature)
    if not (central and L[0] > 300): rk = float(np.clip(th * 0.25, cell * 0.3, 3))
    e = dict(os.environ, PS_CELULA="%g" % (cell * 0.75), PS_RK_CONTUR="%g" % float(np.clip(th * 0.3, cell * 0.5, 3)))
    r = subprocess.run([PY, os.path.join(HERE, "ps_din_ghidaje.py"), ter, raw, "%g" % rk], capture_output=True, text=True, env=e, timeout=1200)
    if r.returncode: raise RuntimeError("solid " + r.stderr[-200:])
    faces = int(np.clip(b.area / (cell * 2.2) ** 2, 800, 220000))
    r = subprocess.run([PY, os.path.join(HERE, "mesh_finisaj.py"), raw, fin, joc, "%g" % (cell * 1.1), "4", "%d" % faces], capture_output=True, text=True, timeout=2400)
    if r.returncode: raise RuntimeError("finisaj " + r.stderr[-200:])
    q = np.load(joc); m = trimesh.Trimesh(q["v"].astype(float), q["f"], process=True); m = max(m.split(only_watertight=False), key=lambda t: len(t.faces))
    T = np.load(ter); G = {}
    for k in T.files:
        A = T[k]
        if k.startswith("sec_") or k.startswith("prof_"):
            if len(A) < 3: continue
            G[k + "_sus"] = A[:, [0, 1, 2]]; G[k + "_jos"] = A[:, [0, 1, 3]]
    if "outline" in T.files: G["contur"] = np.vstack([T["outline"], T["outline"][:1]])
    vw = m.vertices.copy() if central else m.vertices @ R + c
    G = {k: (a.copy() if central else a @ R + c) for k, a in G.items()}
    uv = (m.vertices[:, :2]) / S_UV + 0.5
    res = trimesh.Trimesh(vw, m.faces, process=False)
    Pa = b.sample(12000); Pb = res.sample(12000); da = KD(Pb).query(Pa)[0]; db = KD(Pa).query(Pb)[0]
    return dict(mesh=res, uv=uv, G=G, r95=float(np.percentile(da, 95)), n95=float(np.percentile(db, 95)), rm=float(da.mean()), nm=float(db.mean()), cell=cell, wt=bool(m.is_watertight), L=[float(L1), float(L2), float(L3)], att=att)
OUTV, OUTF, OUTU = [], [], []; GG = {}; rows = []; n = 0
for i, b in enumerate(sorted(keep, key=lambda t: -t.area)):
    best = None; err = ""
    for att in range(int(os.environ.get("NT_ATT", "3"))):
        try: r = build(b, att)
        except Exception as ex: err = str(ex)[-160:]; print("incercare", att, "esuata", err[-90:].replace(chr(10), " ")); continue
        print("incercare", att, "cell %.2f r95 %.2f n95 %.2f etans %s" % (r["cell"], r["r95"], r["n95"], r["wt"]))
        tolr = max(1.2, 3 * r["cell"], 0.01 * r["L"][0], min(3.0, 0.05 * r["L"][0]), float(os.environ.get("NT_TOLR", "0"))); toln = max(3.0, 0.25 * r["L"][1], 0.1 * r["L"][0]);   # n95 is mostly the holes the solid fills, so looser
        r["ok"] = r["wt"] and r["r95"] <= tolr and r["n95"] <= toln
        if best is None or (r["ok"], -r["r95"]) > (best["ok"], -best["r95"]): best = r
        if r["ok"]: break
    if best is not None and best["ok"]:
        m = best["mesh"]; OUTV.append(m.vertices); OUTF.append(m.faces + n); OUTU.append(best["uv"]); n += len(m.vertices)
        for k, a in best["G"].items(): GG["%d_%s" % (i, k)] = a
        rows.append(dict(corp=i, metoda="ghidaje", fete=len(m.faces), r95=round(best["r95"], 2), n95=round(best["n95"], 2), rm=round(best["rm"], 2), cell=round(best["cell"], 2), incercare=best["att"], L=[round(t) for t in best["L"]]))
    else:
        c = b.copy(); c.update_faces(c.nondegenerate_faces()); c.remove_unreferenced_vertices(); c.fix_normals(); OUTV.append(c.vertices); OUTF.append(c.faces + n); OUTU.append(c.vertices[:, :2] / S_UV + 0.5); n += len(c.vertices)
        rows.append(dict(corp=i, metoda="referinta", fete=len(c.faces), r95=round(best["r95"], 2) if best else None, n95=round(best["n95"], 2) if best else None, eroare=err))
for b in rest:
    OUTV.append(b.vertices); OUTF.append(b.faces + n); OUTU.append(b.vertices[:, :2] / S_UV + 0.5); n += len(b.vertices)
meth = sorted(set(r["metoda"] for r in rows))
np.savez(os.path.join(OD, ID + ".npz"), v=np.vstack(OUTV).astype(np.float32), f=np.vstack(OUTF).astype(np.int32), uv=np.vstack(OUTU).astype(np.float32), mat=MAT, central=central)
np.savez(os.path.join(OD, ID + "_g.npz"), **{k: a.astype(np.float32) for k, a in GG.items()})
json.dump(dict(id=ID, names=NAMES, mat=MAT, central=bool(central), corpuri=len(keep), mici=len(rest), rows=rows), open(os.path.join(OD, ID + ".json"), "w"), ensure_ascii=False)
print("PIESA", ID, MAT, "centrala" if central else "", "corpuri", len(keep), "+", len(rest), json.dumps(rows)[:400])
import shutil; shutil.rmtree(W, ignore_errors=True)
