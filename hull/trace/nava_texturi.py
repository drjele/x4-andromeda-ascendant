# The complete ship textured: own UV layer "uv1" on every piece (metres / tile, S half computed and mirrored): along the path and once
# around for the arms BS / BJ (seamless), around the hull's axis for CORP, box in the piece's own frame for the rest (the doors and the
# arm share one frame, so they continue when closed); colour attribute "Col" = slow variation (no visible repetition); PBR hull from the
# mod's own panel maps, dark lining for the hangar, the confirmed reds kept. Usage:
# blender -b <scene> --python nava_texturi.py -- <dir npz> <dir maps> <out.blend> [tile]
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from scipy_free import noise3
from mathutils.kdtree import KDTree
DN, MAPS, OUT = sys.argv[sys.argv.index("--") + 1:][:3]; A = sys.argv[sys.argv.index("--") + 4:]; TILE = float(A[0]) if A else 420.0; assert not os.path.exists(OUT); sc = bpy.context.scene; sc.frame_set(1); bpy.context.view_layer.update()
col = bpy.data.collections["NAVA_COMPLETA"]; root = bpy.data.objects["nava"]; OX = root.location.x; Z = np.load(f"{DN}/neteda5.npz")
def path_of(k, idx):
    R = [];
    for i in idx: v = Z[f"{k}|s{i}v"]; m = len(v) // 96; R.append(v[:m * 96].reshape(m, 96, 3).mean(1))
    P = np.vstack(R); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, s[-1], 3.0); return np.stack([np.interp(u, s, P[:, j]) for j in range(3)], 1)
pbs = path_of("BS", [0, 2]); pbj = path_of("BJ", [0, 2, 4]); ARM = {}
for k, P, s0 in (("BS", pbs, 0.0), ("BJ", pbj, None)):
    if s0 is None: s0 = len(pbs) * 3.0
    t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; e1 = np.array([1.0, 0, 0]) - t * t[:, :1]; e1 /= np.linalg.norm(e1, axis=1)[:, None]; kd = KDTree(len(P)); [kd.insert(q, i) for i, q in enumerate(P)]; kd.balance(); ARM[k] = (P, t, e1, np.cross(t, e1), kd, s0)
def arm_uv(k, v):
    P, t, e1, e2, kd, s0 = ARM[k]; i = np.array([kd.find(q)[1] for q in v]); r = v - P[i]; s = i * 3.0 + (r * t[i]).sum(1) + s0; return s / 270.0, np.arctan2((r * e2[i]).sum(1), (r * e1[i]).sum(1)) / (2 * np.pi)
FR = {"AI": ((0, 1, 0), (.77, 0, -.64)), "BF": ((.35, .94, 0), (.80, 0, -.60))}  # u along, v across (S half as +x); the third axis = their normal
def box_uv(v, t, frame):
    a, b = np.array(frame[0], float), np.array(frame[1], float); a /= np.linalg.norm(a); b -= a * (a @ b); b /= np.linalg.norm(b); c = np.cross(a, b); n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]; w = np.abs(np.stack([n @ a, n @ b, n @ c], 1)) * [.8, .9, 1.25]; k = w.argmax(1); U = v @ a, v @ b, v @ c; uv = np.empty((len(t), 3, 2))
    for ax, (p, q) in enumerate(((2, 1), (0, 2), (0, 1))): m = k == ax; uv[m] = np.stack([U[p][t[m]], U[q][t[m]]], -1) / TILE
    return uv
def hull_uv(v, t):
    y, r = v[:, 1], np.abs(v[:, 0]); zc = np.interp(y, [-790, -500, 0, 600, 1107], [55, 0, -60, -105, -95]); th = np.arctan2(r, v[:, 2] - zc) / np.pi; return np.stack([y[t] / TILE, (th * 1.5)[t]], -1)
def img(n, data): i = bpy.data.images.load(f"{MAPS}/{n}.png", check_existing=True); i.colorspace_settings.name = "Non-Color" if data else "sRGB"; i.pack(); return i
def hull_mat(name, tint, rough, metal, nstr):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]; L = nt.links; uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "uv1"
    def tex(n, data): x = nt.nodes.new("ShaderNodeTexImage"); x.image = img(n, data); L.new(uv.outputs[0], x.inputs[0]); return x
    d = tex("andromeda_panels_diff", False); at = nt.nodes.new("ShaderNodeVertexColor"); at.layer_name = "Col"
    m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1; L.new(d.outputs[0], m1.inputs[6]); L.new(at.outputs[0], m1.inputs[7]); m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1; L.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (*tint, 1); L.new(m2.outputs[2], b.inputs["Base Color"])
    s = tex("andromeda_panels_smooth", True); mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough[0]; mr.inputs[4].default_value = rough[1]; L.new(s.outputs[0], mr.inputs[0]); L.new(mr.outputs[0], b.inputs["Roughness"]); b.inputs["Metallic"].default_value = metal
    n = tex("andromeda_panels_normal", True); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.uv_map = "uv1"; nm.inputs[0].default_value = nstr; L.new(n.outputs[0], nm.inputs[1]); L.new(nm.outputs[0], b.inputs["Normal"]); m.diffuse_color = (*[.75 * x for x in tint], 1); m.metallic = metal; m.roughness = .4; return m
SILVER = hull_mat("nava_argint", (.86, .88, .93), (.52, .26), .85, .55); DARK = hull_mat("nava_inchis", (.20, .22, .28), (.6, .35), .8, .6); MID = hull_mat("nava_gri", (.55, .58, .66), (.5, .28), .85, .55)
def plain(n, c, r, me): m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = r; b.inputs["Metallic"].default_value = me; m.diffuse_color = (*c, 1); return m
RED = plain("nava_rosu", (.42, .012, .03), .38, .35); BLADE = plain("nava_rosu_lama", (.36, .010, .022), .34, .45); RED2 = plain("nava_rosu_inchis", (.22, .006, .018), .42, .35)
for o in list(col.objects):
    if o.type != "MESH": continue
    n = o.name[5:]; side = -1 if n.endswith("_S") else 1
    if "lama" in n or "spinare" in n:                                       # blades: the band's red, their black edge kept
        o.data = o.data.copy()
        for i, mm in enumerate(o.data.materials):
            if mm and mm.name.startswith("lame_rosu"): o.data.materials[i] = BLADE
        o.color = BLADE.diffuse_color; continue
    o.data = o.data.copy(); me = o.data; me.calc_loop_triangles(); M = np.array(o.matrix_world); co = np.empty(len(me.vertices) * 3)
    (me.shape_keys.key_blocks[0].data if me.shape_keys else me.vertices).foreach_get("co", co); v = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; v[:, 0] -= OX; w = v.copy(); w[:, 0] = np.abs(w[:, 0]) if side == 1 and not n.endswith("_D") else w[:, 0] * side
    lt = np.empty(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get("loops", lt); vt = np.empty(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get("vertices", vt); lt, vt = lt.reshape(-1, 3), vt.reshape(-1, 3)
    if n[:2] in ("BS", "BJ"):
        u, a = arm_uv(n[:2], w); uv = np.stack([u[vt], a[vt]], -1); d = uv[:, :, 1] - uv[:, :1, 1]; uv[:, :, 1] -= np.round(d)
    elif n == "CORP": uv = hull_uv(w, vt)
    else: uv = box_uv(w, vt, FR["AI"] if n[:2] == "AI" or n[:2] == "H_" else FR["BF"] if any(x in n for x in ("brat_fata", "usa_fata", "usa_spate", "R060")) else ((0, 1, 0), (1, 0, 0)))
    if n[-2:] not in ("_S", "_D") and n != "CORP":                          # triangles across the axis: true x, so nothing is folded over itself
        x = v[vt][:, :, 0]; k = (x.min(1) < -.05) & (x.max(1) > .05); uv[k] = box_uv(v, vt[k], ((0, 1, 0), (1, 0, 0)))
    for L in list(me.uv_layers): me.uv_layers.remove(L)
    lay = me.uv_layers.new(name="uv1"); arr = np.zeros((len(me.loops), 2)); arr[lt.ravel()] = uv.reshape(-1, 2); lay.data.foreach_set("uv", arr.ravel())
    c = .80 + .20 * noise3(w + 5000, 420, 1) * .6 + .20 * noise3(w + 9000, 130, 2) * .4; at = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "POINT"); at.data.foreach_set("color", np.stack([c, c, c, np.ones_like(c)], 1).ravel())
    m = DARK if n[:2] == "H_" or "launchtube" in n else RED if "nacela_deschis" in n else RED2 if "nacela_inchis" in n else MID if any(x in n for x in ("comp_055", "lacrima_capac", "R109")) else SILVER
    if not me.materials: me.materials.append(m)
    for i, sl in enumerate(o.material_slots): sl.link = "DATA"; me.materials[i] = m
    o.color = m.diffuse_color
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.frame_set(100); lab = bpy.data.objects.get("eticheta_NAVA_COMPLETA_sus")
if lab: lab.data.body = "NAVA V1 + TEXTURI"
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.type = "MATERIAL"; sp.shading.show_xray = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("TEXTURI", OUT, len(col.objects))
