# Finishing of the body built from the field (sectiuni_corp_tot.py), with PyMeshLab: isotropic remeshing (even triangles of
# EDGE m), Taubin smoothing (no shrinking) to take out the marching-cubes grain, then a game version by quadric edge
# collapse to LOD faces (shape kept, normals preserved). Distance of each result to the input measured (Hausdorff, % bbox).
# Usage: python mesh_finisaj.py <corp_tot.npz> <out.npz> <out_lod.npz> [edge] [taubin_steps] [lod_faces]
import sys, numpy as np, pymeshlab as ml
Z = np.load(sys.argv[1]); OUT, OUTL = sys.argv[2], sys.argv[3]
EDGE = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0; STEPS = int(sys.argv[5]) if len(sys.argv) > 5 else 30; LOD = int(sys.argv[6]) if len(sys.argv) > 6 else 60000
ms = ml.MeshSet(); ms.add_mesh(ml.Mesh(Z["v"].astype(np.float64), Z["f"].astype(np.int32)), "in")
ms.add_mesh(ml.Mesh(Z["v"].astype(np.float64), Z["f"].astype(np.int32)), "lucru")
ms.meshing_isotropic_explicit_remeshing(targetlen=ml.PureValue(EDGE), iterations=4)
ms.apply_coord_taubin_smoothing(lambda_=0.5, mu=-0.53, stepsmoothnum=STEPS)
def dist(i):
    r = ms.get_hausdorff_distance(sampledmesh=i, targetmesh=0, samplenum=200000); return r["mean"], r["RMS"], r["max"]
m = ms.current_mesh(); np.savez(OUT, v=m.vertex_matrix().astype(np.float32), f=m.face_matrix().astype(np.int32))
print("FINISAJ: %d fete (muchie %.1f m, Taubin %d); fata de intrare medie %.2f / RMS %.2f / max %.2f m" % (m.face_number(), EDGE, STEPS, *dist(1)))
ms.add_mesh(ml.Mesh(m.vertex_matrix(), m.face_matrix()), "lod")
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=LOD, preservenormal=True, preservetopology=True, qualitythr=0.5, optimalplacement=True, planarquadric=True)
l = ms.current_mesh(); np.savez(OUTL, v=l.vertex_matrix().astype(np.float32), f=l.face_matrix().astype(np.int32))
print("JOC: %d fete; fata de intrare medie %.2f / RMS %.2f / max %.2f m" % (l.face_number(), *dist(2)))
