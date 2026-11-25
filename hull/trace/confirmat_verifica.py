# Checks that a scene still carries the confirmed pieces untouched: same names, meshes and places as in the hash file.
# Usage: blender -b <scene> --python confirmat_verifica.py -- <hash.json> [collection]
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from confirmat_hash import hash_col
A = sys.argv[sys.argv.index("--") + 1:]; D = json.load(open(A[0])); bpy.context.scene.frame_set(1); N = hash_col(A[1] if len(A) > 1 else D["colectie"]); V = D["obiecte"]
for k in sorted(V):
    if N.get(k) != V[k]: print("VERIF", "LIPSA" if k not in N else "SCHIMBAT", k)
print("VERIF identice", sum(N.get(k) == V[k] for k in V), "din", len(V), "| in plus", len(set(N) - set(V)))
