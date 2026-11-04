# Clean lines audit of a block's pieces (asked: one more clean lines pass): per piece faces, free / non-manifold edges, degenerate
# faces, slivers, flipped-looking smooth shading (smooth edge with > SM degrees between its faces) and the feature lines (free edges and edges
# sharper than FE degrees) chained into polylines: per chain, kinks (turn > KINK degrees at a vertex of exactly 2 feature edges) and direction
# reversals in a row (zigzag). Writes the kink positions (world, frame 1) to a json. Usage: blender -b <scene> --python audit_linii.py -- <COL> <out.json> env FE=30 KINK=25 SM=30 MINL=.5
import bpy, bmesh, sys, os, json, math
a = sys.argv[sys.argv.index("--") + 1:]; COL, OUT = a[0], a[1]; E = lambda k, d: float(os.environ.get(k, d)); FE, KINK, SM = E("FE", 30), E("KINK", 25), E("SM", 30)
bpy.context.scene.frame_set(1); R = {}
print("AUDIT %-26s %7s %6s %6s %5s %6s %6s %5s %5s %5s" % ("piesa", "fete", "libere", "nemanf", "degen", "aschii", "smooth", "lanturi", "fransi", "zigzag"))
for o in sorted(bpy.data.collections[COL].objects, key=lambda x: x.name):
    if o.type != "MESH": continue
    if o.name.endswith("_D") and bpy.data.objects.get(o.name[:-1] + "S"): continue    # D = mirror of S, checked apart
    b = bmesh.new(); b.from_mesh(o.data); b.edges.ensure_lookup_table()
    free = [e for e in b.edges if e.is_boundary]; nm = [e for e in b.edges if len(e.link_faces) > 2]
    deg = [f for f in b.faces if f.calc_area() < 1e-4]
    sl = [f for f in b.faces if f.calc_area() >= 1e-4 and max(e.calc_length() for e in f.edges) ** 2 / f.calc_area() > 400]
    fe = set(free); sm = []
    for e in b.edges:
        if len(e.link_faces) == 2:
            ang = math.degrees(e.calc_face_angle(0))
            if ang > FE:
                if e.smooth and e.link_faces[0].smooth and e.link_faces[1].smooth: sm.append(e)
                fe.add(e)
    adj = {}
    for e in fe:
        for v in e.verts: adj.setdefault(v, []).append(e)
    # chains: walk through vertices of exactly 2 feature edges
    seen = set(); ch = 0; kinks = []; zz = 0
    for e0 in fe:
        if e0 in seen: continue
        ch += 1; st = [e0]; seen.add(e0)
        while st:
            e = st.pop()
            for v in e.verts:
                if len(adj[v]) == 2:
                    f = adj[v][0] if adj[v][1] is e else adj[v][1]
                    if f not in seen: seen.add(f); st.append(f)
    for v, L in adj.items():
        if len(L) != 2: continue
        p, q = L[0].other_vert(v).co - v.co, v.co - L[1].other_vert(v).co
        if p.length < 1e-5 or q.length < 1e-5: continue
        t = math.degrees(p.angle(q))
        if t > KINK: kinks.append((tuple(round(x, 2) for x in (o.matrix_world @ v.co)), round(t, 1), round(min(p.length, q.length), 2)))
    print("AUDIT %-26s %7d %6d %6d %5d %6d %6d %5d %5d" % (o.name, len(b.faces), len(free), len(nm), len(deg), len(sl), len(sm), ch, len(kinks)))
    R[o.name] = dict(fete=len(b.faces), libere=len(free), nemanifold=len(nm), degenerate=len(deg), aschii=len(sl), smooth=len(sm), lanturi=ch, kinks=kinks, nm=[tuple(round(x, 2) for x in (o.matrix_world @ ((e.verts[0].co + e.verts[1].co) / 2))) for e in nm], deg=[tuple(round(x, 2) for x in (o.matrix_world @ f.calc_center_median())) for f in deg], smoothe=[tuple(round(x, 2) for x in (o.matrix_world @ ((e.verts[0].co + e.verts[1].co) / 2))) for e in sm])
    b.free()
json.dump(R, open(OUT, "w"))
