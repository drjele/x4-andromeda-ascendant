# PS's sockets cut at the joint ring (so PS and the arm butt together on the same section, like a pipe joint): for each side
# the piece is cut by the plane through the arm's joint ring (brate_tub.py: centre P[ks], normal T[ks], mirrored for _S) and
# what lies past it near the arm's axis is removed; the rim left open, matching the arm's open start.
# Usage: blender -b <f.blend> --python ps_prize_taie.py -- <out.blend> <brate.npz> [piece]
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, B = a[0], np.load(a[1]); NAME = a[2] if len(a) > 2 else "piesa_169_C_PS"
o = bpy.data.objects[NAME]; ks = int(B["ks"]); P, T, A = B["centru"][ks], B["T"][ks], float(max(B["Ak"][ks], B["Bk"][ks]))
bm = bmesh.new(); bm.from_mesh(o.data)
for sg in (1, -1):
    c = Vector(P * [sg, 1, 1]); n = Vector(T * [sg, 1, 1]); n.normalize()
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=c, plane_no=n)
    gone = []
    for f in bm.faces:
        m = f.calc_center_median(); d = (m - c).dot(n)
        if d > 1e-4 and ((m - c) - n * d).length < 1.8 * A: gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
fb = sum(1 for e in bm.edges if e.is_boundary); bm.to_mesh(o.data); bm.free()
print("PRIZE taiate la inelul %d (s %.0f m): margini libere %d (cele doua guri)" % (ks, B["s"][ks], fb))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
