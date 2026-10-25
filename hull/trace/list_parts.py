# The working scene against parts.json: which parts failed to build (MISSING) and what is there unlisted (EXTRA).
import bpy, json
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); P = json.load(open(f"{D}/body/parts.json"))
names = {o.name for o in bpy.data.scenes["seg"].objects if o.type == "MESH"}
# merged into other objects or removed at the user's request
skip = {"hangar_slats_r", "hangar_slats_l", "wing_socket_r", "wing_socket_l", "wing_rib_r", "wing_rib_l", "dorsal_crescent", "dorsal_shoulder", "flank_blade", "rear_shoulder"}
print("MISSING", sorted(set(P) - names - skip)); print("EXTRA", sorted(names - set(P) - {"source", "source_edited"}))
