# The complete ship with the reference's own texture: Material_8 laid on each piece exactly as on the reference piece it comes from
# (affine laws fitted on R001 084_D, R002 169_C, R004 022_S, R005 146_C, R030 158_S; S half, mirrored), the confirmed blue pieces, the
# red band, the blades and the launch tube with their own materials. Usage: blender -b <scene> --python nava_texturi_ref.py -- <out.blend>
import bpy, sys, os, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; assert not os.path.exists(OUT); sc = bpy.context.scene; sc.frame_set(1); bpy.context.view_layer.update(); col = bpy.data.collections["NAVA_COMPLETA"]; OX = bpy.data.objects["nava"].location.x; M8 = bpy.data.materials["Material_8"]
TINT = (.94, .9435, .963)                                                    # sRGB: the reference seen whole (its accents and facets) is darker and bluer: 154/155/162 against 164/165/168
def tinted(m):
    q = m.copy(); q.name = "nava_" + m.name; n_ = next(x for x in q.node_tree.nodes if x.type == "TEX_IMAGE"); i0 = n_.image; i1 = i0.copy(); i1.name = "nava_" + i0.name; px = np.array(i0.pixels[:]).reshape(-1, 4); px[:, :3] *= TINT; i1.pixels.foreach_set(px.ravel().astype(np.float32)); i1.update(); i1.pack(); n_.image = i1; return q
M8 = tinted(M8)
def cyan(n, c, e): m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = .5; b.inputs["Emission Color"].default_value = (*c, 1); b.inputs["Emission Strength"].default_value = e; m.diffuse_color = (*[x ** .7 for x in c], 1); return m
CY, CY0 = cyan("nacela_cyan", (.27, .64, .68), .9), cyan("nacela_cyan_fond", (.008, .035, .04), .0)
px = np.array(bpy.data.images["Image_13"].pixels[:]).reshape(-1, 4)[:, :3]; rr = px[px[:, 0] > 1.6 * np.maximum(px[:, 1], px[:, 2])]; RB = (rr if len(rr) > 50 else px).mean(0); RB = np.where(RB <= .04045, RB / 12.92, ((RB + .055) / 1.055) ** 2.4); print("ROSU referinta (liniar)", RB.round(3), len(rr))
def red(n, k): m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*(RB * k), 1); b.inputs["Roughness"].default_value = 1; m.diffuse_color = (*(RB * k) ** (1 / 1.6), 1); return m
BAND = {"nacela_deschis": red("banda_rosu", 1.9), "nacela_inchis": red("banda_rosu_inchis", 1.0)}
LAW = {  # per 1000 m: x (S side, negative), y, z, constant
    "084": ((-1.4571, -.0021, -.013, -2.3828), (.0006, .4771, -.0075, 373.4093)), "169": ((.126, .176, -.0016, 303.7201), (-.1855, .1195, -.0035, 429.7458)), "022": ((.383, -.0325, .0004, 283.9282), (-.0331, -.3781, .0087, 526.9804)),
    "146": ((.0016, .5843, -.1725, 609.0028), (-.3721, -.0005, -.0033, 519.3507)), "158": ((-.0016, 1.2647, -.0198, 1060.4577), (-.0112, .0195, 1.2411, 85.8778))}
def law(n):
    if n.startswith(("lama", "spinare", "nacela", "comp_055", "lacrima", "launchtube")): return None
    if n.startswith(("CORP", "AI", "BJ", "H_")): return "084"
    if n == "PI": return "146"
    if n.startswith("AS"): return "158"
    return "022" if any(q in n for q in ("brat_fata", "usa_fata", "usa_spate", "R060")) else "169"
for o in col.objects:
    if o.type != "MESH": continue
    n = o.name[5:]; k = law(n)
    for s in o.material_slots: s.link = "DATA"
    if n.startswith("nacela_cyan"): q = CY0 if "_fond" in n else CY; o.data.materials[0] = q; o.color = q.diffuse_color; continue
    q = next((BAND[b] for b in BAND if n.startswith(b)), None)
    if q:
        o.data = o.data.copy()
        for i in range(len(o.data.materials)): o.data.materials[i] = q
        o.color = q.diffuse_color; continue
    if k is None:
        m = o.data.materials[0] if o.data.materials else None; o.color = m.diffuse_color if m else (1, 1, 1, 1); continue
    o.data = o.data.copy(); me = o.data; M = np.array(o.matrix_world); co = np.empty(len(me.vertices) * 3); (me.shape_keys.key_blocks[0].data if me.shape_keys else me.vertices).foreach_get("co", co); v = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; v[:, 0] = -np.abs(v[:, 0] - OX); v = np.c_[v, np.ones(len(v))] / 1000; v[:, 3] = .001
    uv = np.stack([v @ np.array(c) for c in LAW[k]], 1); lv = np.empty(len(me.loops), int); me.loops.foreach_get("vertex_index", lv)
    for L in list(me.uv_layers): me.uv_layers.remove(L)
    me.uv_layers.new(name="UVMap").data.foreach_set("uv", uv[lv].ravel())
    if not me.materials: me.materials.append(M8)
    for i in range(len(me.materials)): me.materials[i] = M8
    o.color = (.72, .72, .74, 1)
lab = bpy.data.objects.get("eticheta_NAVA_COMPLETA_sus")
if lab: lab.data.body = "NAVA V2"
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True); sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.frame_set(100)
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.type = "MATERIAL"; sp.shading.show_xray = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("TEXREF", OUT)
