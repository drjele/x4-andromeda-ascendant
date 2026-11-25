# Big labels over every block of the board, so each one reads at a glance from above: flat text above the block's far end, plus the same text standing up, facing the front view.
# Usage: blender -b <in> --python etichete_plansa.py -- <out.blend> "<text>|<collection or ^object regex>" ...   env SIZE=110
import bpy, sys, re, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; SZ = float(os.environ.get("SIZE", "110"))
col = bpy.data.collections.get("ETICHETE") or bpy.data.collections.new("ETICHETE")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
mat = bpy.data.materials.get("eticheta_galben") or bpy.data.materials.new("eticheta_galben"); mat.diffuse_color = (1.0, .85, .05, 1); mat.use_nodes = True
em = mat.node_tree.nodes.get("Emission") or mat.node_tree.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, .85, .05, 1); em.inputs[1].default_value = 3.0
mat.node_tree.links.new(em.outputs[0], mat.node_tree.nodes["Material Output"].inputs[0])
for spec in a[1:]:
    txt, sel, *sz = spec.split("|"); c = bpy.data.collections.get(sel); sz = float(sz[0]) if sz else SZ           # optional third field: letter size
    obs = [o for o in (c.all_objects if c else bpy.data.objects) if (c or re.search(sel, o.name)) and o.type in ("MESH", "CURVE") and o.name not in col.objects]
    p = [o.matrix_world @ Vector(b) for o in obs for b in o.bound_box]; xc = (min(q.x for q in p) + max(q.x for q in p)) / 2; y1 = max(q.y for q in p); z1 = max(q.z for q in p)
    for k, (loc, rot) in enumerate((((xc, y1 + 0.6 * sz, z1 + 20), (0, 0, 0)), ((xc, y1 + 0.3 * sz, z1 + 0.6 * sz), (1.5708, 0, 3.1416)))):
        cu = bpy.data.curves.new("et", "FONT"); cu.body = txt.replace("\\n", "\n"); cu.size = sz; cu.align_x = "CENTER"; cu.align_y = "BOTTOM"; cu.extrude = 4; cu.materials.append(mat)
        o = bpy.data.objects.new("eticheta_%s_%s" % (re.sub(r"\W+", "_", txt.split("\\n")[0])[:30], "sus" if k == 0 else "fata"), cu); col.objects.link(o); o.location = loc; o.rotation_euler = rot
    print("ETICHETA", txt.split("\\n")[0], "x %.0f" % xc, len(obs), "obiecte")
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SALVAT", OUT)
