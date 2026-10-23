"""Name the pieces the hull is assembled from, label every face with one and write them out as
separate objects for review; see DEVELOPMENT.md."""

import bmesh
import bpy

PIECES = ("hull", "crown", "wings", "loops", "arc", "lower", "pod", "nacelle", "lights", "pads")
COLOURS = {
    "hull": (0.62, 0.63, 0.66),
    "crown": (0.95, 0.85, 0.35),
    "wings": (0.35, 0.55, 0.85),
    "loops": (0.65, 0.4, 0.9),
    "arc": (0.95, 0.55, 0.15),
    "lower": (0.3, 0.75, 0.35),
    "pod": (0.85, 0.3, 0.3),
    "nacelle": (0.2, 0.8, 0.8),
    "lights": (1.0, 0.1, 0.5),
    "pads": (0.25, 0.25, 0.25),
}
LAYER = "piece"
# Regions of the source hull, on the right half: the aft loops behind LOOP_AFT and outboard of
# LOOP_OUTBOARD, the dorsal crown above CROWN_FLOOR within CROWN_HALF_WIDTH of the centre plane,
# and the side wings outboard of WING_OUTBOARD; the rest is the central hull.
LOOP_AFT = -350.0
LOOP_OUTBOARD = 230.0
CROWN_FLOOR = 150.0
CROWN_HALF_WIDTH = 260.0
WING_OUTBOARD = 280.0
# Neighbour votes that smooth the ragged edges of the geometric regions.
SMOOTHING_PASSES = 3


def tag(bm, faces, name):
    layer = bm.faces.layers.int.get(LAYER) or bm.faces.layers.int.new(LAYER)
    for face in faces:
        face[layer] = 1 + PIECES.index(name)


def region(centre):
    x = abs(centre.x)
    if centre.y < LOOP_AFT and LOOP_OUTBOARD < x:
        return "loops"
    if CROWN_FLOOR < centre.z and x < CROWN_HALF_WIDTH:
        return "crown"
    if WING_OUTBOARD < x:
        return "wings"
    return "hull"


def label(mesh_object):
    # Generated faces carry their piece already, lights and pads their own markers; the rest of the
    # source hull falls into regions, cleaned by neighbour votes that never relabel generated faces.
    bm = bmesh.new()
    bm.from_mesh(mesh_object.data)
    layer = bm.faces.layers.int.get(LAYER) or bm.faces.layers.int.new(LAYER)
    livery = bm.faces.layers.int.get("livery")
    pad = bm.faces.layers.int.get("pad")
    fixed = set()
    for face in bm.faces:
        if livery is not None and face[livery]:
            face[layer] = 1 + PIECES.index("lights")
        elif pad is not None and face[pad]:
            face[layer] = 1 + PIECES.index("pads")
        elif not face[layer]:
            face[layer] = 1 + PIECES.index(region(face.calc_center_median()))
            continue
        fixed.add(face)
    for _ in range(SMOOTHING_PASSES):
        votes = {}
        for face in bm.faces:
            if face in fixed:
                continue
            counts = {}
            for edge in face.edges:
                for other in edge.link_faces:
                    if other is not face and other not in fixed:
                        counts[other[layer]] = counts.get(other[layer], 0) + 1
            if counts:
                best = max(counts, key=counts.get)
                if counts[best] > counts.get(face[layer], 0):
                    votes[face] = best
        for face, value in votes.items():
            face[layer] = value
    bm.to_mesh(mesh_object.data)
    bm.free()
    mesh_object.data.update()


def drop_labels(mesh):
    if LAYER in mesh.attributes:
        mesh.attributes.remove(mesh.attributes[LAYER])


def write(mesh_object, path):
    # One object per piece in a scene of its own, saved beside the export so each can be reviewed.
    scene = bpy.data.scenes.new("pieces")
    values = [entry.value for entry in mesh_object.data.attributes[LAYER].data]
    made = []
    for index, name in enumerate(PIECES, 1):
        bm = bmesh.new()
        bm.from_mesh(mesh_object.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(
            bm, geom=[f for f in bm.faces if values[f.index] != index], context="FACES"
        )
        if not bm.faces:
            bm.free()
            continue
        mesh = bpy.data.meshes.new(f"piece_{name}")
        bm.to_mesh(mesh)
        bm.free()
        drop_labels(mesh)
        material = bpy.data.materials.new(f"piece_{name}")
        material.diffuse_color = (*COLOURS[name], 1.0)
        mesh.materials.clear()
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.material_index = 0
        piece = bpy.data.objects.new(f"piece_{name}", mesh)
        scene.collection.objects.link(piece)
        made.append((name, len(mesh.polygons)))
    bpy.data.libraries.write(str(path), {scene}, fake_user=True)
    for obj in list(scene.collection.objects):
        bpy.data.objects.remove(obj)
    bpy.data.scenes.remove(scene)
    return made
