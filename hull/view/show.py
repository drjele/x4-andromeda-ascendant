# Run inside the remote window after a file is loaded: colour the parts, keep the source as a wire overlay.
import json
sc = bpy.data.scenes["seg"]; w = bpy.context.window_manager.windows[0]; w.scene = sc
P = json.load(open("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/parts.json"))
for name, (label, rgb) in P.items():
    ob = sc.objects.get(name) or sc.objects.get(f"{label}_{name}")
    if ob is None: continue
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1)
    ob.data.materials.clear(); ob.data.materials.append(m); ob.name = f"{label}_{name}"
    # put the origin on the right-hand half of the part so its name shows on it
    from mathutils import Vector, Matrix
    pts = [v.co for v in ob.data.vertices if v.co.x >= -0.5] or [v.co for v in ob.data.vertices]
    c = ob.matrix_world @ (sum(pts, Vector()) / len(pts))
    ob.data.transform(Matrix.Translation(-(ob.matrix_world.inverted() @ c))); ob.location = c
    ob.show_name = True; ob.show_in_front = False
src = sc.objects["source"]; src.hide_set(True); src.display_type = "WIRE"   # the user works without the original overlay; src.color = (0.25, 0.25, 0.3, 1)
if "source_edited" in sc.objects: sc.objects["source_edited"].hide_set(True)
src.hide_select = True; src.name = "SURSA_overlay"
for a in w.screen.areas:
    if a.type == "VIEW_3D":
        s = a.spaces.active; s.clip_start, s.clip_end = 1.0, 30000.0; s.shading.type = "SOLID"; s.shading.color_type = "MATERIAL"
        s.shading.wireframe_color_type = "OBJECT"
        s.overlay.show_extras = True; s.overlay.show_overlays = True
        r = next(x for x in a.regions if x.type == "WINDOW")
        with bpy.context.temp_override(window=w, area=a, region=r): bpy.ops.view3d.view_all()
