# Keep the largest connected body only (marching-cubes crumbs out). Usage: python nt_curata.py in.npz out.npz
import sys, numpy as np, trimesh
Z = np.load(sys.argv[1]); m = trimesh.Trimesh(Z["v"], Z["f"], process=True); s = m.split(only_watertight=False); b = max(s, key=lambda q: len(q.faces))
np.savez(sys.argv[2], v=b.vertices.astype(np.float32), f=b.faces.astype(np.int32)); print("CURAT", len(m.faces), "->", len(b.faces), "etans", b.is_watertight, "bucati", len(s))
