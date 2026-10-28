# Deck sections sheet: reference shell points (grey PS, orange 086, blue 103) in planes y = const with the new deck
# section (red, both halves) on top, to check the envelope against the reference.
# Usage: python ps_deck_sheet.py <esantion_punte.npz> <punte.npz> <out.png>
import sys, numpy as np, cv2
D = np.load(sys.argv[1]); N = np.load(sys.argv[2]); OUT = sys.argv[3]
ys_, s, E, T, B = N["ys"], N["s"], N["edge"], N["top"], N["bot"]
col = {k: {"ps": (110, 110, 110), "p086": (0, 140, 255), "p118S": (0, 200, 230), "p117D": (0, 200, 230)}.get(k, (220, 80, 0)) for k in D.files}
H_, SC_, Z0_ = (int(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (300, 2.0, 200)
Y = [int(v) for v in __import__("os").environ.get("FOI_Y", "460,420,380,340,300,260,220,180,140,100,60,30,10,2").split(",")]; tiles = []
for y0 in Y:
    im = np.full((H_, 900, 3), 250, np.uint8); sc = SC_
    f = lambda x, z: (int(450 + x * sc), int(Z0_ - (z - 300) * sc))
    for n, c in col.items():
        q = D[n][np.abs(D[n][:, 1] - y0) < 0.8]
        for p in q[::2]: cv2.circle(im, f(p[0], p[2]), 1, c, -1)
    k = np.argmin(np.abs(ys_ - y0)); x0_ = N["x0"][k] if "x0" in N.files else 0.0; x = x0_ + s * (E[k] - x0_)
    for sg in (1, -1):
        pts = np.r_[np.c_[sg * x, T[k]], np.c_[sg * x[::-1], B[k][::-1]]]
        cv2.polylines(im, [np.array([f(a, b) for a, b in pts], np.int32)], False, (0, 0, 230), 2)
    cv2.putText(im, "y = %d" % y0, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2); tiles.append(im)
tiles += [np.full_like(tiles[0], 250)] * (-len(tiles) % 2)
sheet = np.vstack([np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)])
cv2.putText(sheet, "rosu = sectiunea noua a puntii; gri PS, portocaliu 086, albastru 103 (scara %.1f px/m)" % SC_ + "", (10, sheet.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
cv2.imwrite(OUT, sheet)
