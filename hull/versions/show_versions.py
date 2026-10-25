# Run inside the remote window after show.py: append the frozen versions beside the working build, each offset
# sideways with a label above it, so nothing is lost between rebuilds (V0 = ca23115, V1 = ref-01 pass, V2 = organic,
# V3 = original-only elements; the working build stays at x = 0).
import bpy, os
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/versions"
sc = bpy.context.window_manager.windows[0].scene
OFFS = {"V0": -6600, "V1": -4400, "V2": -2200, "V3": 2200}
def label(text, x):
    c = bpy.data.curves.new(text, "FONT"); c.body = text; c.size = 260; c.align_x = "CENTER"
    o = bpy.data.objects.new(text, c); o.location = (x, 1700, 400); o.rotation_euler = (1.5708, 0, 0); sc.collection.objects.link(o)
for name, x in OFFS.items():
    f = f"{D}/{name}.blend"
    if not os.path.exists(f) or name in bpy.data.collections: continue
    with bpy.data.libraries.load(f) as (src, dst): dst.collections = [name]
    col = bpy.data.collections[name]; sc.collection.children.link(col)
    for o in col.objects: o.location.x += x
    label(name, x)
label("LUCRU (build curent)", 0)
