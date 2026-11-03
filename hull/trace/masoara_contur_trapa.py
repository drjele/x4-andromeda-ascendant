# Measures how clean a hatch outline is (asked: clean lines on at_usa_spate_S and its cutout in at_brat_fata_S): the boundary loops of
# the arm's cutout (open edges of at_brat_fata_<sd> inside the hatch area) and of the hatch's closed-state underside, as seen from
# below (xy): per loop the length, the number of points, the max / mean turning angle between consecutive edges and how many sharp
# kinks (> 25 deg) there are. Usage: blender -b <scene.blend> --python masoara_contur_trapa.py -- <grup: spate|fata> <S|D>
import bpy, bmesh, sys, math, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; GK, SD = a[0], a[1]
bpy.context.scene.frame_set(1)
def loops(edges):
    adj = {}
    for e in edges:
        for v in e.verts: adj.setdefault(v, []).append(e)
    seen, out = set(), []
    for e0 in edges:
        if e0 in seen: continue
        v = e0.verts[0]; e = e0; L = [v]
        while e not in seen:
            seen.add(e); v = e.other_vert(v); L.append(v); nx = [x for x in adj[v] if x not in seen]
            if not nx: break
            e = nx[0]
        out.append(np.array([tuple(p.co) for p in L]))
    return out
def stats(nm, P):
    d = np.diff(P[:, :2], axis=0); ln = np.linalg.norm(d, axis=1); d = d[ln > 1e-3]; ln = ln[ln > 1e-3]
    if len(d) < 3: return
    ang = np.degrees(np.abs(np.arctan2(d[:-1, 0] * d[1:, 1] - d[:-1, 1] * d[1:, 0], (d[:-1] * d[1:]).sum(1))))
    kk = np.where(ang > 25)[0]; Pk = P[np.r_[True, np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1) > 1e-3]]
    print("CONTUR %s frangeri la: %s" % (nm, ", ".join("(%.0f, %.0f, %.0f) %.0f gr" % (*Pk[k + 1], ang[k]) for k in kk[:8])))
    print("CONTUR %s: %.0f m, %d puncte, unghi max %.1f, mediu %.2f grade, %d frangeri > 25 grade" % (nm, ln.sum(), len(P), ang.max(), ang.mean(), (ang > 25).sum()))
door = bpy.data.objects["at_usa_%s_%s" % (GK, SD)]; me = door.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
zs = np.array([v.co.z for v in bm.verts]); bot = [e for e in bm.edges if len(e.link_faces) == 2 and abs(e.link_faces[0].normal.z) > .2 and abs(e.link_faces[1].normal.z) < .5 and max(v.co.z for v in e.verts) < 1e9]
# outline of the hatch = edges between its underside skin and its side wall (the extruded rim), bottom side only
rim = [e for e in bm.edges if any(abs(f.normal.z) < .3 for f in e.link_faces) and any(abs(f.normal.z) >= .3 for f in e.link_faces)]
lp = sorted(loops(rim), key=len, reverse=True)
for k, P in enumerate(lp[:4]): stats("trapa %s bucla %d" % (door.name, k), P)
arm = bpy.data.objects["at_brat_fata_" + SD]; bm2 = bmesh.new(); bm2.from_mesh(arm.data)
cx = np.array(door.data.vertices[0].co[:]); bb = np.array([v.co[:] for v in door.data.vertices]); lo_, hi_ = bb.min(0) - 20, bb.max(0) + 20
ob = [e for e in bm2.edges if e.is_boundary and all((lo_ <= np.array(v.co[:])).all() and (np.array(v.co[:]) <= hi_).all() for v in e.verts)]
for k, P in enumerate(sorted(loops(ob), key=len, reverse=True)[:2]): stats("decupaj %s bucla %d" % (arm.name, k), P)
