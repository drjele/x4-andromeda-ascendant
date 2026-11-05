# Night board (asked: copy the validated assembly as the new ship, the guides one welded body per component): ASAMBLAT_NOU stays,
# NAVA_TERMINATA = linked copy of it DX further along X (same meshes, own object animation, location keys shifted), GHIDAJE_ASAMBLATE
# renamed GHIDAJE_NAVA, its loose guides welded per component as g_nt_<comp>_sudat (former names in "linii").
# Usage: blender -b <in> --python nt_plansa.py -- <out.blend>
import bpy, sys, re, json
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; DX = -4800.0
A = bpy.data.collections["ASAMBLAT_NOU"]; N = bpy.data.collections.new("NAVA_TERMINATA"); sc.collection.children.link(N)
for o in sorted(A.objects, key=lambda q: q.name):
    c = o.copy(); c.name = "nt_" + o.name[3:]; N.objects.link(c); c.location.x += DX
    if o.animation_data and o.animation_data.action:
        ac = o.animation_data.action.copy(); ac.name = c.name + "Action"
        for fc in ac.fcurves:
            if fc.data_path == "location" and fc.array_index == 0:
                for kp in fc.keyframe_points: kp.co[1] += DX; kp.handle_left[1] += DX; kp.handle_right[1] += DX
                fc.update()
        c.animation_data_create(); c.animation_data.action = ac
print("NT copie: %d obiecte" % len(N.objects))
G = bpy.data.collections["GHIDAJE_ASAMBLATE"]; G.name = "GHIDAJE_NAVA"
REN = {"g_as_bf_sudat_S": "g_nt_brat_fata_sudat_S", "g_as_bf_sudat_D": "g_nt_brat_fata_sudat_D", "g_as_bo_sudat_S": "g_nt_brat_spate_sudat_S", "g_as_bo_sudat_D": "g_nt_brat_spate_sudat_D",
       "g_as_nac_sudat_S": "g_nt_nacela_sudat_S", "g_as_nac_sudat_D": "g_nt_nacela_sudat_D", "g_aur_ghidaje_urechi_sudate": "g_nt_ureche_sudat"}
for a, b in REN.items():
    o = bpy.data.objects.get(a)
    if o: o.name = b; o.data.name = b
    else: print("NT lipsa", a)
for name, rx in (("g_nt_carena_sudat", r"g_as_car_.*"), ("g_nt_capac_sudat", r"g_as_cap_.*"), ("g_nt_PS_sudat", r"g_as_psr_.*"), ("g_nt_rama_sudat", r"g_as_rama_.*"), ("g_nt_urechiuse_sudat", r"g_as_ure_.*")):
    r = re.compile(rx); parts = sorted((o for o in G.objects if o.type == "CURVE" and r.fullmatch(o.name)), key=lambda o: o.name); names = []
    for o in parts: names += [o.name] * len(o.data.splines)
    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts, selected_objects=parts): bpy.ops.object.join()
    w = parts[0]; w.name = name; w.data.name = name; w["linii"] = json.dumps(names); print("NT sudat", name, len(set(names)), "ghidaje")
print("NT ghidaje:", sorted(o.name for o in G.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
