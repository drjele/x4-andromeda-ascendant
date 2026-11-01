# Polish: degenerate faces removed (asked: validate, then polish): per named object, vertices closer than DIST merged and zero-area
# faces dissolved (bmesh), UVs and materials kept. Usage: blender -b <f.blend> --python curata_degenerate.py -- <out.blend> <obj,...> ; env DIST=0.005
import bpy, sys, os, bmesh
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; D = float(os.environ.get("DIST", "0.005"))
for nm in a[1].split(","):
    o = bpy.data.objects.get(nm)
    if o is None: print("LIPSA", nm); continue
    bm = bmesh.new(); bm.from_mesh(o.data); n0 = len(bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=D); bmesh.ops.dissolve_degenerate(bm, dist=D, edges=bm.edges)
    deg = [f for f in bm.faces if f.calc_area() < 1e-6]
    if deg: bmesh.ops.delete(bm, geom=deg, context="FACES")
    bm.to_mesh(o.data); o.data.update(); print("CURAT", nm, n0, "->", len(bm.faces), "degenerate ramase", sum(1 for f in bm.faces if f.calc_area() < 1e-6)); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
