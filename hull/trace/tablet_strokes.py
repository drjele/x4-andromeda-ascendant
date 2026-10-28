# The pen strokes of a tablet drawing made on an x4 sheet and sent back at sheet/4: scaled back onto the sheet, green and
# red ink picked by hue where the drawing differs from the sheet, each pen's connected strokes labelled (<pen>_mask.npy, <pen>_lab.npy) and drawn numbered.
# Usage: python tablet_strokes.py <drawing.jpg> <sheet_x4.png> <out_dir>
import sys, numpy as np, cv2
from scipy.ndimage import label
DR, SH, OD = sys.argv[1:4]; d = cv2.imread(DR); s = cv2.imread(SH); H, W = s.shape[:2]
hsv = cv2.cvtColor(cv2.resize(d, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2HSV); h, sat, v = cv2.split(hsv)
diff = np.abs(cv2.resize(d, (W, H), interpolation=cv2.INTER_CUBIC).astype(int) - s.astype(int)).sum(2)
ink = (sat > 60) & (v > 90) & (diff > 60)                                  # ink = saturated AND unlike the sheet (the reference's own red hatch is not a stroke)
pens = {"green": ink & (h > 35) & (h < 90), "red": ink & ((h < 12) | (h > 165))}
out = (s * 0.5).astype(np.uint8)
for pen, m in pens.items():
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
    lab, n = label(m, np.ones((3, 3))); sizes = np.bincount(lab.ravel()); keep = np.zeros(n + 1, bool); keep[1:] = sizes[1:] > 400
    lab[~keep[lab]] = 0; np.save(f"{OD}/{pen}_mask.npy", lab > 0); np.save(f"{OD}/{pen}_lab.npy", lab)
    col = (0, 255, 0) if pen == "green" else (60, 60, 255); out[lab > 0] = col
    for i in np.nonzero(keep)[0]:
        ys, xs = np.nonzero(lab == i); k = len(xs) // 3; p = (int(xs[k]), int(ys[k]))
        cv2.circle(out, p, 26, (255, 255, 255), -1); cv2.putText(out, str(i), (p[0] - 16, p[1] + 10), 0, 1.0, (0, 0, 0), 3)
    print(pen, [(int(i), int(sizes[i])) for i in np.nonzero(keep)[0]])
cv2.imwrite(f"{OD}/trase_numerotate.png", cv2.resize(out, None, fx=0.5, fy=0.5))
