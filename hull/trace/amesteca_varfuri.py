# Two versions of the same mesh (same vertex order) mixed along y: B between y_a and y_b, A elsewhere, blended over BL m
# (asked: undo, only the stretch between vertebra 14 and 15 was wrong - only there the newer one). World coordinates.
# AM_SUS=zm,b: B only above the median plane z = zm (blended over b m).
# Usage: python amesteca_varfuri.py <A.npz> <B.npz> <out.npz> <y_a> <y_b> [bl] [faces.npz:key]
import sys, os, numpy as np, trimesh
A = np.load(sys.argv[1])["v"].astype(float); B = np.load(sys.argv[2])["v"].astype(float); OUT = sys.argv[3]
ya, yb = sorted((float(sys.argv[4]), float(sys.argv[5]))); BL = float(sys.argv[6]) if len(sys.argv) > 6 else 6.0
y = A[:, 1]; w = np.clip(np.minimum(y - (ya - BL), (yb + BL) - y) / BL, 0, 1); w = w * w * (3 - 2 * w)
SUS = os.environ.get("AM_SUS")                         # zm,b: only above the median plane (B over z > zm, blended over b m)
if SUS:
    zm, bz = [float(q) for q in SUS.split(",")]; u = np.clip((A[:, 2] - zm) / bz, 0, 1); w = w * u * u * (3 - 2 * u)
V = (1 - w)[:, None] * A + w[:, None] * B
if len(sys.argv) > 7:
    fn, k = sys.argv[7].split(":"); f = np.load(fn)[k]; t = trimesh.Trimesh(V, f, process=False); a = np.degrees(t.face_adjacency_angles)
    print("AMESTEC: B intre y %.0f si %.0f (trecere %.0f m), %d varfuri din B; etans %s, falduri >120 grd %d, cute >60 grd %d" % (ya, yb, BL, (w > 0.5).sum(), t.is_watertight, (a > 120).sum(), (a > 60).sum()))
np.savez(OUT, v=V.astype(np.float32))
