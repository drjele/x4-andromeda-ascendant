# Per rebuilt piece: guide lines' distance to the piece and their kinks (deg, resampled every 0.5 m), dihedral creases over 60 deg per piece; markdown table + totals. Usage: python nt_ghid_metrici.py <p_dir> <out.md>
import sys, os, glob, json, numpy as np, trimesh
D, OUT = sys.argv[1], sys.argv[2]; rows = []; allk = []
for jp in sorted(glob.glob(D + "/*.json")):
    j = json.load(open(jp)); i = j["id"]; Z = np.load(os.path.join(D, i + ".npz")); m = trimesh.Trimesh(Z["v"].astype(float), Z["f"], process=False); G = np.load(os.path.join(D, i + "_g.npz")); dist = []; kink = []
    for k in G.files:
        L = G[k].astype(float); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
        if s[-1] < 2: continue
        u = np.arange(0, s[-1], 0.5); Q = np.stack([np.interp(u, s, L[:, a]) for a in range(3)], 1); d = np.diff(Q, axis=0); n = np.linalg.norm(d, axis=1); ok = n > 1e-6; d = d[ok] / n[ok, None]; kink.append(np.degrees(np.arccos(np.clip(np.sum(d[1:] * d[:-1], 1), -1, 1))))
        q = L[:: max(1, len(L) // 25)]; dist.append(trimesh.proximity.ProximityQuery(m).on_surface(q)[1])
    fa = m.face_adjacency_angles; cr = int((np.degrees(fa) > 60).sum())
    kk = np.concatenate(kink) if kink else np.zeros(1); dd = np.concatenate(dist) if dist else np.zeros(1)
    allk.append(kk); ms = sorted(set(r["metoda"] for r in j["rows"])); rw = j["rows"]
    rows.append(dict(id=i, ref=",".join(j["names"]), metoda="+".join(ms), fete=len(m.faces), corpuri=j["corpuri"], mici=j["mici"], r95=max([r.get("r95") or 0 for r in rw] or [0]), n95=max([r.get("n95") or 0 for r in rw] or [0]), gh_p95=round(float(np.percentile(dd, 95)), 2), gh_max=round(float(dd.max()), 2), kink_p99=round(float(np.percentile(kk, 99)), 2), kink3=round(float(100 * (kk > 3).mean()), 2), cute60=cr, mat=j["mat"]))
    print(i, rows[-1]["metoda"], rows[-1]["gh_p95"], rows[-1]["kink3"], cr, flush=True)
K = np.concatenate(allk); gr = [r for r in rows if r["metoda"] == "ghidaje"]
head = "Din ghidaje %d, amestec %d, din referință %d. Frângeri ghidaje peste 3°/0,5 m: %.2f %% din pași (p99 %.2f°). Ghidaj–piesă p95 maxim %.2f m. Cute >60° pe piesele din ghidaje: %d.\n\n" % (len(gr), sum("+" in r["metoda"] for r in rows), sum(r["metoda"] == "referinta" for r in rows), 100 * (K > 3).mean(), np.percentile(K, 99), max(r["gh_p95"] for r in gr), sum(r["cute60"] for r in gr))
t = "| piesă (`nt_<id>`) | referință | metodă | fețe | corpuri (+mici) | r95 m | n95 m | ghidaj p95 m | frângeri >3° % | cute >60° | material |\n|---|---|---|---|---|---|---|---|---|---|---|\n"
for r in sorted(rows, key=lambda q: -q["fete"]): t += "| %(id)s | %(ref)s | %(metoda)s | %(fete)d | %(corpuri)d+%(mici)d | %(r95).2f | %(n95).2f | %(gh_p95).2f | %(kink3).2f | %(cute60)d | %(mat)s |\n" % r
open(OUT, "w").write(head + t); print(head)
