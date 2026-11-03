# The front arm's welded guides (g_as_bf_sudat_S) and the nacelle's (g_as_nac_sudat_S) exported line by line in SHIP coordinates
# (GHIDAJE_ASAMBLATE sits at x -3100) to an npz, keyed by the original line names; plus the atelier arm mesh (at_brat_fata_S, ship
# coords) as <name>__v / __f. Usage: blender -b <scene> --python exporta_ghidaje_brat.py -- <out.npz>
import bpy, sys, json, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; D = {}
for gn in ("g_as_bf_sudat_S", "g_as_nac_sudat_S"):
    g = bpy.data.objects[gn]; LN = json.loads(g["linii"])
    for k, sp in enumerate(g.data.splines):
        D[LN[k]] = np.array([(g.matrix_world @ p.co.xyz)[:] for p in sp.points]) + [3100, 0, 0]
a = bpy.data.objects["at_brat_fata_S"]; me = a.data
D["at_brat_fata_S__v"] = np.array([v.co[:] for v in me.vertices]); D["at_brat_fata_S__f"] = np.array([list(p.vertices) for p in me.polygons], dtype=object) if any(len(p.vertices) != 3 for p in me.polygons) else np.array([list(p.vertices) for p in me.polygons])
np.savez(OUT, **D); print("EXPORT", len(D), "chei", OUT)
