# The 103 band built from its confirmed guides (bumerang_v.py with BV_TRAPEZ): along the spine, every metre, the section
# = upper rail -> the small vertical side on the spine (TH m) -> lower rail, closed along the side against PS / the arm;
# consecutive sections joined by quads, both ends capped flat - one watertight, separate piece (ship coordinates, centred).
# B103_SUS_DZ=m raises the top (upper rail + top of the spine side) by m metres, the bottom stays (asked: 103 "un pic mai
# groase" to come over the front arms from above).
# B103_LATURA_MICA=m the small outer side (default th + dz); B103_SUS_CA_SPINAREA=1 the top edge bent like the spine, its rear
# end kept; B103_SUS_COT_Z=m the top edge bent down in z like the spine (front tip m lower); B103_JOS_COT_Z=m the
# bottom edge bent up the same way; B103_CAPETE=front,rear metres the ends carried on into the PS / the arm; B103_IMBINARE=<npz> inner edges on the drawn joint lines. Usage: [B103_SUS_DZ=8] python bumerang_piesa.py <guides.npz> <out.npz> [th]
import sys, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; TH = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
Ru, Rj, S = G["sina_sus"], G["sina_jos"], G["spinare"]
n0 = int(np.argmin(np.linalg.norm(S[:, :2] - G["v_00"][1, :2], axis=1)))   # where the rails' stations start on the (lengthened) spine
sp = S[n0:n0 + len(Ru)]
import os
DZ = float(os.environ.get("B103_SUS_DZ", "0")); LAT = float(os.environ.get("B103_LATURA_MICA", TH + DZ))   # small outer side, m
if os.environ.get("B103_SUS_CA_SPINAREA"):            # top edge bent like the spine: the spine moved onto the edge's rear end
    Ru = np.c_[sp[:, :2] + (Ru[-1, :2] - sp[-1, :2]), Ru[:, 2]]   # (towards the arms), same height
COTZ = float(os.environ.get("B103_SUS_COT_Z", "0"))   # top edge kept in its plane, bent down in z like the spine bends in plan:
if COTZ:                                               # the spine seen with its rear run along the edge, scaled so the front
    q = sp[:, :2]; u = q[330] - q[-1]; u /= np.linalg.norm(u); w = np.array([-u[1], u[0]]); off = (q - q[-1]) @ w   # tip drops
    Ru = Ru.copy(); Ru[:, 2] -= COTZ * off / off[0]   # COTZ m; the rear end (towards the arms) stays
JDZ = float(os.environ.get("B103_JOS_DZ", "0")); Rj = Rj - [0, 0, JDZ]   # the bottom edge lowered (thicker at the bottom)
JZ = float(os.environ.get("B103_JOS_COT_Z", "0"))   # the bottom edge the same way, bent up (front tip JZ m higher)
if JZ:
    q = sp[:, :2]; u = q[330] - q[-1]; u /= np.linalg.norm(u); w = np.array([-u[1], u[0]]); off = (q - q[-1]) @ w
    Rj = Rj.copy(); Rj[:, 2] += JZ * off / off[0]
LJ = float(os.environ.get("B103_LATURA_JOS", "0"))  # the small outer side carried LJ m lower too
Ru = Ru + [0, 0, DZ]; DZ = 0
IMB = os.environ.get("B103_IMBINARE")                 # inner edges put exactly on the confirmed joint lines drawn on the PS
if IMB:                                                # (npz contur_imbinare_sus_D / _jos_D); behind the PS's end the old
    Lz = np.load(IMB); BL = float(os.environ.get("B103_IMBINARE_TRECERE", "60"))   # edges, blended over BL m
    for key, Rr in (("contur_imbinare_sus_D", "Ru"), ("contur_imbinare_jos_D", "Rj")):
        Ln = Lz[key]; Ln = Ln[np.argsort(Ln[:, 1])]; old_ = Ru if Rr == "Ru" else Rj; new_ = old_.copy()
        y = old_[:, 1]; yy = np.clip(y, Ln[0, 1], Ln[-1, 1])
        new_[:, 0] = np.interp(yy, Ln[:, 1], Ln[:, 0]); new_[:, 2] = np.interp(yy, Ln[:, 1], Ln[:, 2])
        for e_, sl_ in ((0, slice(0, 15)), (-1, slice(-15, None))):   # past the line's ends: carried on straight (no kink)
            q_ = Ln[sl_]; g_ = np.polyfit(q_[:, 1], q_[:, [0, 2]], 1)[0]; out_ = (y < Ln[0, 1]) if e_ == 0 else (y > Ln[-1, 1])
            new_[out_, 0] = Ln[e_, 0] + g_[0] * (y[out_] - Ln[e_, 1]); new_[out_, 2] = Ln[e_, 2] + g_[1] * (y[out_] - Ln[e_, 1])
        t = np.clip((y - (Ln[0, 1] - BL)) / BL, 0, 1); t = t * t * (3 - 2 * t)          # 0 behind, 1 on the line
        AD = float(os.environ.get("B103_IMBINARE_ADANC", "0"))   # edge sunk AD m into the PS (top down, bottom up): the faces
        new_[:, 2] += -AD if Rr == "Ru" else AD                   # then leave the PS in one clean line, not flickering on it
        mixed = old_ + t[:, None] * (new_ - old_)
        if Rr == "Ru": Ru = mixed
        else: Rj = mixed
        print("IMBINARE %s: pe linie pentru y >= %.0f, trecere %.0f m" % (key, Ln[0, 1], BL))
ring = np.stack([Ru + [0, 0, DZ], sp + [0, 0, LAT - TH / 2], sp - [0, 0, TH / 2 + LJ], Rj], 1)   # 4 corners per section
CE = [float(x_) for x_ in os.environ.get("B103_CAPETE", "0,0").split(",")]
CI = [float(x_) for x_ in os.environ.get("B103_CAPETE_IN", "0,0").split(",")]
CU = float(os.environ.get("B103_FATA_SUS", "0"))      # ... and the front one bent CU m up (its corner into the PS)   # ... bending CI m inwards (towards the rails) by the end   # ends carried on straight (front into the PS,
if CE[0] > 0:                                          # rear into the arm), every metre, along the end's direction
    t0 = ring[0, 1] - ring[3, 1]; t0[2] = 0; t0 /= np.linalg.norm(t0)
    k_ = np.arange(int(CE[0]), 0, -1)[:, None, None]; nin = ring[0, 0] - ring[0, 1]; nin[2] = 0; nin -= (nin @ t0) * t0; nin /= np.linalg.norm(nin)
    tc = ring[0] - ring[3]; tc[:, 2] = 0; tc /= np.linalg.norm(tc, axis=1)[:, None]   # each edge carried on in ITS own direction
    ring = np.concatenate([ring[0][None] + k_ * tc[None] + CI[0] * (k_ / CE[0]) ** 2 * nin + CU * (k_ / CE[0]) ** 2 * np.array([0, 0, 1.0]), ring])   # (no kink)
if CE[1] > 0:
    t1 = ring[-1, 1] - ring[-4, 1]; t1[2] = 0; t1 /= np.linalg.norm(t1)
    k_ = np.arange(1, int(CE[1]) + 1)[:, None, None]; nin = ring[-1, 0] - ring[-1, 1]; nin[2] = 0; nin -= (nin @ t1) * t1; nin /= np.linalg.norm(nin)
    tc = ring[-1] - ring[-4]; tc[:, 2] = 0; tc /= np.linalg.norm(tc, axis=1)[:, None]   # each edge its own direction
    ring = np.concatenate([ring, ring[-1][None] + k_ * tc[None] + CI[1] * (k_ / CE[1]) ** 2 * nin])
CJ = [float(x_) for x_ in os.environ.get("B103_FATA_COLT_JOS", "0,35,40").split(",")]   # the front's outer top corner lowered
if CJ[0]:                                              # CJ m (it showed above the PS's thin nose): full over the first CJ[1]
    i_ = np.arange(len(ring)); t_ = np.clip((i_ - CJ[1]) / CJ[2], 0, 1); w_ = 1 - t_ * t_ * (3 - 2 * t_)   # sections, fading over CJ[2]
    ring = ring.copy(); ring[:, 1, 2] -= CJ[0] * w_
V = ring.reshape(-1, 3); n = len(ring); F = []
for i in range(n - 1):
    for a in range(4):
        b = (a + 1) % 4; F.append([i * 4 + a, (i + 1) * 4 + a, (i + 1) * 4 + b, i * 4 + b])
F.append([3, 2, 1, 0]); F.append([(n - 1) * 4 + 0, (n - 1) * 4 + 1, (n - 1) * 4 + 2, (n - 1) * 4 + 3])
F = np.array(F); T = np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
v = V; e1 = v[T[:, 1]] - v[T[:, 0]]; e2 = v[T[:, 2]] - v[T[:, 0]]; vol = np.einsum("ij,ij->i", v[T[:, 0]], np.cross(e1, e2)).sum() / 6
if vol < 0: T = T[:, ::-1]; vol = -vol                                   # faces facing out
import trimesh                                                          # one consistent outward winding (the caps came out mixed)
tm = trimesh.Trimesh(V, T, process=True); trimesh.repair.fix_winding(tm); trimesh.repair.fix_normals(tm); V, T, vol = tm.vertices, tm.faces, tm.volume
np.savez(OUT, v=V.astype(np.float32), f=T.astype(np.int32))
print("PIESA 103: %d sectiuni (din metru in metru), %d varfuri, %d triunghiuri, volum %.0f m3; latura mica %.0f m; x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (
    n, len(V), len(T), vol, LAT, V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
