# Welds guide curves into one body per group (asked: weld the arms' and the nacelles' guides, each one body; the back arms'
# g_as_bo_* too, another body): every curve object whose name matches the group's regex is joined into one curve object (one
# spline per former guide, same points, place, bevel and materials); nothing is moved. The former names, in spline order, are
# kept on the welded object as the custom property "linii" (JSON) so they can be taken apart again by name.
# Usage: blender -b <in> --python sudeaza_ghidaje.py -- <out.blend> <welded name>=<regex> [<welded name>=<regex>] ...
import bpy, sys, re, json
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
for spec in a[1:]:
    name, rx = spec.split("=", 1); r = re.compile(rx)
    parts = sorted((o for o in bpy.data.objects if o.type == "CURVE" and r.fullmatch(o.name)), key=lambda o: o.name)
    if not parts: print("SUDAT %s: nimic pentru %s" % (name, rx)); continue
    names = []
    for o in parts: names += [o.name] * len(o.data.splines)
    col = parts[0].users_collection[0]; n_sp = sum(len(o.data.splines) for o in parts)
    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts, selected_objects=parts):
        bpy.ops.object.join()
    w = parts[0]; w.name = name; w.data.name = name; w["linii"] = json.dumps(names)
    print("SUDAT %s: %d ghidaje -> 1 corp (%d linii, %d puncte), colectia %s"
          % (name, len(set(names)), len(w.data.splines), sum(len(s.points) for s in w.data.splines), col.name))
    assert len(w.data.splines) == n_sp
bpy.ops.wm.save_as_mainfile(filepath=OUT)
