#!/usr/bin/env bash
# Review sheets for the organic pass: overall views (ours / overlaid / original), close-ups of the arc-root
# join, the U nose, the strap sections, every nacelle, the red wings, the W1 sockets and the body plateau,
# plus the deviation map and the body profile sheet.
set -e
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp; OUT=${1:-/home/adrian/Documents/Andromeda/2026-10-24-fable}; R=$T/view/fable
mkdir -p "$R" "$OUT"; P=$T/overlay/.venv/bin/python
blender -b --python $T/view/final_views.py -- "$R" overall abo 2>&1 | grep -iE "error|traceback" || true
blender -b --python $T/arms/dev_map.py 2>&1 | grep -iE "error|traceback" || true
C=("root_q:900,-500,900:280,50,250:45" "root_top:250,0,1500:250,0,250:50" "root_front:400,900,700:280,80,250:45"
   "unose_front:0,1200,-700:0,150,-290:50" "unose_under:300,700,-1100:0,100,-290:50" "unose_side:900,500,-500:0,150,-290:50"
   "strap_outer:1300,100,-200:700,0,-250:45" "strap_top:700,300,500:650,300,-250:45" "strap_loop:1100,-1700,500:430,-1250,120:45"
   "nac_loop:300,-1300,250:540,-920,-70:45" "nac_uarch:200,900,-800:0,150,-290:60" "nac_outer:1300,-900,-350:650,-620,-170:45"
   "wing_q:450,500,600:430,280,150:60" "wing_top:600,350,900:450,300,120:60" "wing_root:300,500,900:330,160,200:45"
   "socket:600,-100,700:340,-350,160:45" "socket_low:900,-700,350:340,-350,130:45"
   "plateau_side:2500,600,250:0,600,30:60" "plateau_q:1200,1500,700:0,650,30:50")
blender -b --python $T/view/closeup.py -- "$R" abo "${C[@]}" 2>&1 | grep -iE "error|traceback" || true
for v in top under side front q_front q_rear q_under; do
    case $v in side|front) cols=1;; *) cols=3;; esac
    $P $T/view/sheet.py "$OUT/fable_$v.png" $cols "$R/${v}_a.png" "$R/${v}_b.png" "$R/${v}_o.png"
done
sheet() { n=$1; shift; files=(); for j in "$@"; do files+=("$R/${j}_a.png" "$R/${j}_b.png" "$R/${j}_o.png"); done; $P $T/view/sheet.py "$OUT/fable_$n.png" 3 "${files[@]}"; }
sheet arc_root root_q root_top root_front
sheet u_nose unose_front unose_under unose_side
sheet straps strap_outer strap_top strap_loop
sheet nacelles nac_loop nac_uarch nac_outer
sheet red_wings wing_q wing_top wing_root
sheet sockets socket socket_low
sheet plateau plateau_side plateau_q
$P $T/view/sheet.py "$OUT/fable_deviation.png" 2 $T/arms/dev_top.png $T/arms/dev_bot.png $T/arms/dev_side.png $T/arms/dev_front.png
( cd $T/body && $P profile_sheet.py && cp profile_sheet.png "$OUT/corp_profil.png" && cp profile_plan.png "$OUT/corp_profil_plan.png" )
ls "$OUT"
