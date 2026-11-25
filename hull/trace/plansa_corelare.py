# New board blocks from the correlation: ZONE_084 (hull coloured by zone, one object per zone) and CORELARE (the aligned models
# on top of each other, one object per model, S half mirrored for the two that share the hull). Usage:
# blender -b <scene> --python plansa_corelare.py -- <dir npz> <x_zone> <x_corelare> <out.blend>
import bpy, sys, os, numpy as np
D, XZ, XC, OUT = sys.argv[sys.argv.index("--") + 1:][:4]; assert not os.path.exists(OUT)
COLS = {"CORP": (.75, .15, .12), "CORP etaj": (.95, .6, .1), "AI": (.1, .6, .65), "BJ": (.2, .35, .9), "H": (.65, .2, .8), "PI": (.3, .7, .25)}
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = (*c, 1); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c, 1); return m
def obj(col, n, T, x, m):
    V, I = np.unique(T.reshape(-1, 3).round(3), axis=0, return_inverse=True); F = I.reshape(-1, 3); F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    me = bpy.data.meshes.new(n); me.from_pydata(V.tolist(), [], F.tolist()); me.materials.append(m); o = bpy.data.objects.new(n, me); o.location.x = float(x); col.objects.link(o)
def coll(n): c = bpy.data.collections.new(n); bpy.context.scene.collection.children.link(c); return c
z = np.load(f"{D}/zone_084.npz"); cz = coll("ZONE_084")
for q in np.unique(z["zone"]): obj(cz, "zona_" + str(q).replace(" ", "_"), z["T"][z["zone"] == q], XZ, mat("zona_" + str(q), COLS[str(q)]))
def half(T): T = T[T[:, :, 0].min(1) < -.5].copy(); T[:, :, 0] = np.minimum(T[:, :, 0], 0); return np.concatenate([T, T[:, ::-1] * [-1, 1, 1]])
def load(f, hull=None):
    d = np.load(f"{D}/{f}.npz"); t = d["t"]; nn = list(d["n"])
    if hull: t = t[np.isin(d["o"], [nn.index(h) for h in hull])]
    return d["v"][t]
pi = half(load("REFERINTA", ["R005 146_C"])); obj(cz, "zona_PI", pi, XZ, mat("zona_PI", COLS["PI"]))
cc = coll("CORELARE")
obj(cc, "cor_binkley_084_S", half(load("REFERINTA", ["R001 084_D", "R005 146_C"])), XC, mat("cor_binkley", (.8, .12, .12)))
obj(cc, "cor_moreno_Cube_S", half(load("moreno_v17_al", ["Cube", "NurbsPath.038_Mesh.027"])), XC, mat("cor_moreno", (.1, .25, .85)))
obj(cc, "cor_grannyte", load("NAVA_REPO_XMF_al"), float(XC) - 1800, mat("cor_grannyte", (.15, .6, .2)))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("PLANSA", OUT, [(c.name, len(c.objects)) for c in (cz, cc)])
