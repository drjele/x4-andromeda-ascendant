# Outline of the at_PS_carena doors (asked: the carena gets doors in front of the blades, sliding inwards towards its middle axis;
# then: the back one a single piece, both going in exactly their own width, no deeper), S side, seen from below, from the blade /
# column footprint (urma_lame_carena.py): inner side a straight line MG m inside the footprint's innermost x, the ends on the carena
# notch ends (the compartments' cut), outer side XO (past the notch edge: the bay goes there; the door itself stops at XD, under the
# arm's flat PS end), inner corners rounded RC m. Slide inwards = the door's width (inner line - DSEAM .. XD) + SM.
# Saves the outlines (closed polylines), the slid outlines and the parameters. Usage: blender -b --python usi_carena_contur.py --
# <urma.npz> <out.npz>   env MG=2 RC=4 XO=-100 XD=-60.1 DSEAM=.15 SM=.5
import sys, os, math, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; U = np.load(a[0]); OUT = a[1]; E = lambda k, d: float(os.environ.get(k, d))
MG, RC, XO, XD, DSEAM, SM = E("MG", 2.0), E("RC", 4.0), E("XO", -100.0), E("XD", -60.1), E("DSEAM", .15), E("SM", .5)
def rbox(x0, x1, y0, y1, r):                                              # x0 inner (larger x), x1 outer; rounded only at the inner corners
    P = [(x0, y1 - r)] + [(x0 - r + r * math.cos(math.radians(t)), y1 - r + r * math.sin(math.radians(t))) for t in np.linspace(0, 90, 12)] + [(x1, y1), (x1, y0)] + \
        [(x0 - r + r * math.cos(math.radians(t)), y0 + r + r * math.sin(math.radians(t))) for t in np.linspace(-90, 0, 12)]
    return np.array(P)
NOTCH = {"F": (86.1, 134.1), "B": (-2.6, 57.6)}
XIN = {"F": U["fata"][:, 0].max() + MG, "B": U["spate"][:, 0].max() + MG}
doors = {k: rbox(XIN[k], XO, *NOTCH[k], RC) for k in NOTCH}
SL = {k: (XIN[k] - DSEAM - XD) + SM for k in NOTCH}
moved = {k: rbox(XIN[k] - DSEAM, XD, *NOTCH[k], RC - DSEAM) + np.array([SL[k], 0]) for k in NOTCH}
for k in doors:
    print("USA_CARENA %s: interior x %.1f, exterior usa x %.1f, capete y %.1f..%.1f; culisare +x %.2f m (latimea + %.1f)" % (k, XIN[k], XD, *NOTCH[k], SL[k], SM))
np.savez(OUT, **{k: doors[k] for k in doors}, **{k + "_mutat": moved[k] for k in doors}, **{"par_" + k: np.array((XIN[k], XO, *NOTCH[k], RC)) for k in doors},
         SL=np.array([SL[k] for k in doors]), DY=np.zeros(len(doors)), NUME=np.array(list(doors)))
