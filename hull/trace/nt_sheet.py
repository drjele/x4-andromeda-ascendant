# Sheet of PNGs: python nt_sheet.py out.png size cols a.png b.png ...
import sys, cv2, numpy as np
O, S, C = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); I = []
for p in sys.argv[4:]:
    m = cv2.imread(p); m = np.zeros((S, S, 3), np.uint8) if m is None else cv2.resize(m, (S, S)); cv2.putText(m, p.split("/")[-1][:-4], (6, 22), 0, .6, (255, 255, 255), 2); I.append(m)
while len(I) % C: I.append(np.zeros((S, S, 3), np.uint8))
cv2.imwrite(O, np.vstack([np.hstack(I[i:i + C]) for i in range(0, len(I), C)]))
