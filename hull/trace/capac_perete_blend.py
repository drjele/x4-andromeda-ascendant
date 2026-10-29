# Joins the cross-wall prisms (capac_perete.py) to the hood: each loop an n-gon at y0 extruded to y1, boolean union (exact)
# applied on the named object's mesh. Usage: blender -b <in.blend> --python capac_perete_blend.py -- <out.blend> <perete.npz> <obj>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, P, NAME = a[0], np.load(a[1]), a[2]
o = bpy.data.objects[NAME]; y0, y1 = P["y"]; bm = bmesh.new()
for k in [k for k in P.files if k.startswith("bucla_")]:
    q = P[k]; vs = [bm.verts.new((x, y0, z)) for x, z in q]; fc = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[fc]); bmesh.ops.translate(bm, vec=(0, y1 - y0, 0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.triangulate(bm, faces=bm.faces)
me = bpy.data.meshes.new("perete_tmp"); bm.to_mesh(me); w = bpy.data.objects.new("perete_tmp", me); bpy.context.scene.collection.objects.link(w)
w.matrix_world = o.matrix_world.copy()
n0 = len(o.data.polygons); mo = o.modifiers.new("perete", "BOOLEAN"); mo.operation = "UNION"; mo.object = w; mo.solver = "EXACT"
bpy.context.view_layer.objects.active = o
for ob in bpy.context.view_layer.objects: ob.select_set(ob == o)
if o.data.users > 1: o.data = o.data.copy()
bpy.ops.object.modifier_apply(modifier="perete"); bpy.data.objects.remove(w)
print("PERETE LIPIT pe %s: fete %d -> %d" % (NAME, n0, len(o.data.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
