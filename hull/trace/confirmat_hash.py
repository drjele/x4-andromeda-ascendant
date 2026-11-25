import bpy, hashlib, numpy as np
def hash_col(col):
    out = {}
    for o in sorted(bpy.data.collections[col].all_objects, key=lambda o: o.name):
        h = hashlib.sha1(np.round(np.array(o.matrix_world), 4).tobytes())
        if o.type == "MESH":
            me = o.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
            lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
            h.update(co.tobytes()); h.update(lv.tobytes())
        elif o.type == "CURVE":
            for s in o.data.splines:
                for p in list(s.points) + list(s.bezier_points): h.update(np.round(np.array(p.co), 4).tobytes())
        out[o.name] = h.hexdigest()
    return out
