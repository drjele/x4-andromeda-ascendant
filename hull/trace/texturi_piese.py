# Textures on the new pieces (asked: put the textures on the new pieces too): the new front arms get the hull material the other
# pieces use (Material_8, image texture) with the same UVs as piesa_in_colectie.py (from above, x,y / 256); the new nacelles get the
# old nacelle's materials (dark / light red ribs), brought from a source .blend when they are not in the file. Materials kept with
# use_fake_user; packed images left as they are.
# Usage: blender -b <f.blend> --python texturi_piese.py -- <out.blend> <source.blend> <mat_hull> <obj,...> <mat_dark> <obj_dark,...> <mat_light> <obj_light,...>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SRC = a[0], a[1]; pairs = list(zip(a[2::2], a[3::2]))
need = [m for m, _ in pairs if m not in bpy.data.materials]
if need:
    with bpy.data.libraries.load(SRC, link=False) as (src, dst): dst.materials = [m for m in src.materials if m in need]
for mn, obs in pairs:
    m = bpy.data.materials[mn]; m.use_fake_user = True
    for on in obs.split(","):
        o = bpy.data.objects.get(on)
        if o is None: print("LIPSA", on); continue
        me = o.data; me.materials.clear(); me.materials.append(m)
        if any(n.type == "TEX_IMAGE" for n in (m.node_tree.nodes if m.use_nodes else [])):
            uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap"); v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
            li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); uv.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
        o.color = m.diffuse_color; print("TEXTURA", on, "<-", mn)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
