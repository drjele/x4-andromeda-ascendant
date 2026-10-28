# The rebuilt hood and front plate (capac_deal.py, finished) put in place of piesa_comp_086_tutie / piesa_comp_086_fata
# (their meshes replaced, materials kept, UVs from the reference hood R082 086_S by nearest face), the launch tube boxes set
# to the new hangars. Ship coordinates: built centred, placed at DX. Usage: blender -b <f.blend> --python capac_inlocuieste.py
# -- <out.blend> <capac_h.npz> <capac_f.npz> <capac_deal.npz>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; H, Fp, D = np.load(a[1]), np.load(a[2]), np.load(a[3]); DX = -1700.0
src = bpy.data.objects["R082 086_S"]
def put(name, Z):
    o = bpy.data.objects[name]; mat = o.data.materials[0] if o.data.materials else None
    me = bpy.data.meshes.new(name); me.from_pydata((Z["v"].astype(float) + [DX, 0, 0]).tolist(), [], Z["f"].tolist()); me.validate()
    b = bmesh.new(); b.from_mesh(me); bmesh.ops.recalc_face_normals(b, faces=b.faces[:]); fb = sum(1 for e in b.edges if e.is_boundary); b.to_mesh(me); b.free()
    if mat: me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    o.data = me; me.uv_layers.new(name="UVMap")
    c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
    md = o.modifiers.new("uv", "DATA_TRANSFER"); md.object = c; md.use_object_transform = True; md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(c)
    print("INLOCUIT %s: %d fete, muchii libere %d" % (name, len(me.polygons), fb))
put("piesa_comp_086_tutie", H); put("piesa_comp_086_fata", Fp)
for i, bx in enumerate(D["tuburi"]):
    o = bpy.data.objects.get("launchtube_s_%02d" % (i + 1))
    if not o: continue
    x0, x1, y0, y1, z0, z1 = bx[:6]; dr = bx[6] if len(bx) > 6 else 0.0; x0 += DX; x1 += DX   # dr: the back end (y0) lower
    V = [(x0, y0, z0 - dr), (x1, y0, z0 - dr), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1 - dr), (x1, y0, z1 - dr), (x1, y1, z1), (x0, y1, z1)]
    me = o.data
    if len(me.vertices) == 8:
        for v, p in zip(me.vertices, V): v.co = p
    else:
        mesh = bpy.data.meshes.new(o.name); mesh.from_pydata(V, [], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]); o.data = mesh
    o.location = (0, 0, 0); print("TUB %s: x %.0f..%.0f y %.0f..%.0f" % (o.name, x0 - DX, x1 - DX, y0, y1))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
