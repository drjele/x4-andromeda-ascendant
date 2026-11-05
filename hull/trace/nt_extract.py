# One reference piece (or several, merged) from nt_ref_toate.npz to its own v,f npz. Usage: python nt_extract.py <toate.npz> <out.npz> name [name...]
import sys, numpy as np
Z = np.load(sys.argv[1]); V = []; F = []; n = 0
for k in sys.argv[3:]:
    k = k.replace(" ", "_"); v, f = Z[k + "__v"], Z[k + "__f"]; V.append(v); F.append(f + n); n += len(v)
np.savez(sys.argv[2], v=np.vstack(V), f=np.vstack(F))
