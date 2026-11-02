# Measures how far a front arm sticks out past its lip guide, along the lip (asked: the V zone of the lip, still up to 0.48 m
# past the guide after v202): per lip sample the outward direction as in buza_fara_ureche.py; arm vertices within 25 m binned
# by lip arc length, max excess per bin; the V = the lip point farthest from its two ends. Reads the guide out of a welded body.
# Usage: blender -b <scene> --python masoara_buza_V.py -- <piece> <welded guide> <guide name> [BIN=10] ; env X0=1600 GX=3100
import bpy, sys, os, json, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]; PIECE, WG, GN = a[0], a[1], a[2]; BIN = float(a[3]) if len(a) > 3 else 10
X0, GX = float(os.environ.get("X0", 1600)), float(os.environ.get("GX", 3100))
gc = bpy.data.objects[WG]; names = json.loads(gc["linii"]); sp = gc.data.splines[names.index(GN)]
G = np.array([gc.matrix_world @ p.co.xyz + Vector((GX, 0, 0)) for p in sp.points])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(G, axis=0), axis=1))]; t = np.arange(0, s[-1], .25)
G = np.c_[tuple(np.interp(t, s, G[:, i]) for i in range(3))]
def kd(P):
    k = KDTree(len(P))
    for i, p in enumerate(P): k.insert(p, i)
    k.balance(); return k
kg = kd(G); src = bpy.data.objects[PIECE]; mw = src.matrix_world
V = np.array([mw @ v.co + Vector((X0, 0, 0)) for v in src.data.vertices]); kv = kd(V)
NIN = np.zeros_like(G)
for j in range(len(G)):
    p = G[j]; T = G[min(j + 8, len(G) - 1)] - G[max(j - 8, 0)]; T /= np.linalg.norm(T)
    nb = np.array([V[i] for _, i, _ in kv.find_range(p, 25)])
    if not len(nb): continue
    D = nb - p; m = np.abs(D @ T) < 1.5; D = D[m] - np.outer(D[m] @ T, T); f = D[np.linalg.norm(D, axis=1) > 12]
    if len(f): n = -f.mean(0); NIN[j] = n / np.linalg.norm(n)
jv = int(np.argmax(np.minimum(np.linalg.norm(G - G[0], axis=1), np.linalg.norm(G - G[-1], axis=1))))
print("BUZA %s: %.1f m, V la s %.1f m, punct %s (in nava, x fara GX)" % (GN, t[-1], t[jv], np.round(G[jv] - [X0, 0, 0], 1)))
E = {}
for p in V:
    _, j, d = kg.find(p)
    if d < 25: b = int(t[j] // BIN); E[b] = max(E.get(b, -9), (p - G[j]) @ NIN[j])
for b in sorted(E):
    tag = " <- V" if b == int(t[jv] // BIN) else ""
    print("  s %6.0f..%6.0f  exces max %6.2f m%s" % (b * BIN, b * BIN + BIN, E[b], tag))
