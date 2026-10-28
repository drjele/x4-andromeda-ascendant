# A fitted line network tidied for zoning: short loops (hand bumps), short branches hanging free at one end (forks at a
# stroke's end, a letter touching a line) and the longer of two short branches between the same two points (a letter
# written over a line makes a bubble: the line is the shorter way) dropped; free ends that stop short of a vertical
# centreline carried on to it, straight across, so the line and its mirror twin meet.
# Usage: python network_tidy.py <network.json> <axis_x> <max_short_px> <reach_px> [max_bubble_px] [drop.json]
#        drop.json = midpoints [[x, y], ...] of pieces to drop by hand (letter strokes the rules cannot tell from a line)
import sys, json, numpy as np
F, AX, SH, RE = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]); BB = float(sys.argv[5]) if len(sys.argv) > 5 else 0
d = [np.array(c) for c in json.load(open(F))]; n0 = len(d)
if len(sys.argv) > 6:
    DP = np.array(json.load(open(sys.argv[6])), float).reshape(-1, 2)
    d = [c for c in d if np.min(np.hypot(*(DP - c[len(c) // 2]).T)) > 6]
L = lambda c: np.sum(np.hypot(*np.diff(c, axis=0).T))
def free(i, e): return all(np.min(np.hypot(*(c - d[i][e]).T)) > 6 for j, c in enumerate(d) if j != i)
for _ in range(1):                                                         # one pass: a cascade would eat real lines that end on a letter
    drop = set()
    for i, c in enumerate(d):
        if L(c) < SH and (np.hypot(*(c[0] - c[-1])) < 8 or free(i, 0) or free(i, -1)): drop.add(i)
    for i in range(len(d)):
        for j in range(i + 1, len(d)):
            a, b = d[i], d[j]
            same = (np.hypot(*(a[0] - b[0])) < 10 and np.hypot(*(a[-1] - b[-1])) < 10) or (np.hypot(*(a[0] - b[-1])) < 10 and np.hypot(*(a[-1] - b[0])) < 10)
            if same and max(L(a), L(b)) < BB: drop.add(i if L(a) > L(b) else j)
    if not drop: break
    d = [c for k, c in enumerate(d) if k not in drop]
carried = 0
for i, c in enumerate(d):
    for e in (0, -1):
        p = c[e]; gap = AX - p[0] if p[0] < AX else p[0] - AX
        if 2 < gap < RE and free(i, e):
            q = np.array([AX, p[1]]); seg = np.linspace(p, q, 12)[1:]; d[i] = c = np.vstack([c, seg]) if e == -1 else np.vstack([seg[::-1], c]); carried += 1
json.dump([c.tolist() for c in d], open(F, "w")); print("TIDY %d -> %d lines, %d ends carried to the axis" % (n0, len(d), carried))
