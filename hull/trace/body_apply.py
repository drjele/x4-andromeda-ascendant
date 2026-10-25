# Put the outline-fitted body group (body_fit.py output, world vertices) into the working scene.
# Usage: blender -b --python body_apply.py -- <body_fit.npz>
import bpy, sys, numpy as np
from mathutils import Vector
F = np.load(sys.argv[sys.argv.index("--") + 1]); D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; done = []
for name in F.files:
    o = sc.objects.get(name)
    if o is None or len(o.data.vertices) != len(F[name]): print("SKIP", name); continue
    M = o.matrix_world.inverted()
    for v, p in zip(o.data.vertices, F[name]): v.co = M @ Vector(p.tolist())
    o.data.update(); done.append(name)
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("BODY APPLIED", len(done))
