# The workshop's work put on the assembled ship (asked: the doors on the assembled ship, to validate once more): every at_ piece of
# ATELIER_LAME that differs from its an_ twin in ASAMBLAT_NOU (mesh with materials / UV / shape keys, transform, animation) is copied
# over it, the missing ones created; object location keys shifted by the blocks' X distance, shape key actions copied. First the
# materials the carena and its doors lost in usi_carena.py (Material_8 from the ship's carena). Checks at sample frames: each an_
# piece = its at_ twin + DX, each _D = the mirror of its _S. Usage: blender -b <scene> --python pe_nava.py -- <out.blend>
import bpy, sys, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.frame_set(1)
TA, NO = bpy.data.collections["ATELIER_LAME"], bpy.data.collections["ASAMBLAT_NOU"]
mat = bpy.data.objects["an_PS_carena"].data.materials[0]
for o in TA.objects:
    if o.name == "at_PS_carena" or o.name.startswith("at_usa_carena_"):
        o.data.materials.clear(); o.data.materials.append(mat); print("NAVA material %s -> %s" % (o.name, mat.name))
DX = bpy.data.objects["an_PS"].location.x - bpy.data.objects["at_PS"].location.x
def same(a, t):
    if len(a.data.vertices) != len(t.data.vertices) or len(a.data.polygons) != len(t.data.polygons) or a.animation_data or t.animation_data or t.data.shape_keys: return False
    P = np.empty(3 * len(a.data.vertices)); Q = P.copy(); a.data.vertices.foreach_get("co", P); t.data.vertices.foreach_get("co", Q)
    return np.abs(P - Q).max() < 1e-4 and abs(a.location.x - t.location.x - DX) < 1e-4
PAIRS = []; kept = 0
for t in sorted(TA.objects, key=lambda o: o.name):
    if t.type != "MESH": continue
    n = "an_" + t.name[3:]; a = bpy.data.objects.get(n)
    PAIRS.append(n)
    if a and same(a, t): kept += 1; continue
    me = t.data.copy(); me.name = n
    if a is None: a = bpy.data.objects.new(n, me); NO.objects.link(a); st = "nou"
    else:
        old = a.data; a.animation_data_clear(); a.data = me; st = "inlocuit"
        if old.users == 0: bpy.data.meshes.remove(old)
    a.rotation_mode = t.rotation_mode; a.location = t.location; a.location.x += DX; a.rotation_euler = t.rotation_euler; a.rotation_quaternion = t.rotation_quaternion; a.scale = t.scale
    a.color = t.color
    if t.animation_data and t.animation_data.action:
        ac = t.animation_data.action.copy(); ac.name = n + "Action"
        for fc in ac.fcurves:
            if fc.data_path == "location" and fc.array_index == 0:
                for kp in fc.keyframe_points: kp.co[1] += DX; kp.handle_left[1] += DX; kp.handle_right[1] += DX
                fc.update()
        a.animation_data_create(); a.animation_data.action = ac
    k0, k1 = t.data.shape_keys, me.shape_keys
    if k0 and k0.animation_data and k0.animation_data.action:
        k1.animation_data_create(); k1.animation_data.action = k0.animation_data.action.copy(); k1.animation_data.action.name = n + "KeyAction"
    print("NAVA %s %s: %d fete%s%s" % (n, st, len(me.polygons), ", animat" if a.animation_data else "", ", chei de forma" if k1 else ""))
print("NAVA neschimbate (identice): %d" % kept)
def world(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); P = np.empty(3 * len(m.vertices)); m.vertices.foreach_get("co", P); e.to_mesh_clear()
    P = P.reshape(-1, 3); M = np.array(o.matrix_world); return P @ M[:3, :3].T + M[:3, 3]
FR = (1, 12, 30, 50, 84, 112, 130, 146, 160, 168); wa = wm = 0.0; Cn = NO.objects["an_PS"].location.x; bad = []
for f in FR:
    sc.frame_set(f)
    for n in PAIRS:
        a, t = bpy.data.objects[n], bpy.data.objects["at_" + n[3:]]; A = world(a); d = np.abs(A - world(t) - np.array((DX, 0, 0))).max(); wa = max(wa, d)
        if d > 1e-3: bad.append((f, n, round(float(d), 3)))
        if n.endswith("_S"):
            D = world(bpy.data.objects[n[:-1] + "D"]); S = A.copy(); S[:, 0] = 2 * Cn - S[:, 0]; D_, S_ = D[np.lexsort(D.round(3).T)], S[np.lexsort(S.round(3).T)]
            d2 = np.abs(D_ - S_).max() if len(D) == len(S) else 1e9; wm = max(wm, d2)
            if d2 > 1e-2: bad.append((f, "S/D " + n, round(float(d2), 3)))
print("NAVA verificare: an = at + %.0f abatere max %.4f m; D = oglinda S abatere max %.4f m; probleme: %s" % (DX, wa, wm, bad[:12] or "niciuna"))
sc.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)
