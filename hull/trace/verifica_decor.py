# Check that decorations sit on the new pieces' surface, not under it (asked): per decoration vertex, its signed height along the
# nearest surface point's outward normal (outward = up for top surfaces, or away from a spine when one is given); reports the share
# under the surface and the depth.
# Usage: python verifica_decor.py <decor vertices npy|npz:key> <surface npz (v,n)> [spine npz:key]
import sys, numpy as np
from scipy.spatial import cKDTree
def load(spec):
    if ":" in spec: p, k = spec.rsplit(":", 1); return np.load(p)[k]
    return np.load(spec)
V = load(sys.argv[1]); SU = np.load(sys.argv[2]); SV, SN = SU["v"], SU["n"]
if len(sys.argv) > 3:
    SP = load(sys.argv[3]); o_ = SV - SP[cKDTree(SP).query(SV)[1]]; SN = SN * np.where(np.einsum("ij,ij->i", o_, SN)[:, None] < 0, -1, 1)
else: SN = SN * np.where(SN[:, 2:3] < 0, -1, 1)
i = cKDTree(SV).query(V)[1]; h = np.einsum("ij,ij->i", V - SV[i], SN[i])
print("VERIFICARE: %d varfuri; sub suprafata %.1f%% (cel mai adanc %.2f m); deasupra: mediana %.2f, max %.2f m" % (len(V), 100 * np.mean(h < -0.05), h.min(), np.median(h), h.max()))
