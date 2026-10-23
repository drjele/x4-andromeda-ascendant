#!/usr/bin/env bash
# Final review sheets into the Documents folder: overall views and joint close-ups (ours / overlaid / original)
# and the deviation map of the original against our surfaces.
set -e
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp; OUT=/home/adrian/Documents/Andromeda/2026-10-23-final; R=$T/view/final
mkdir -p "$R" "$OUT"; P=$T/overlay/.venv/bin/python
blender -b --python $T/view/final_views.py -- "$R" all abo 2>&1 | grep -iE "error|traceback" || true
blender -b --python $T/arms/dev_map.py 2>&1 | grep -iE "error|traceback" || true
for v in top under side front q_front q_rear q_under; do
    case $v in side|front) cols=1;; *) cols=3;; esac
    $P $T/view/sheet.py "$OUT/final_$v.png" $cols "$R/${v}_a.png" "$R/${v}_b.png" "$R/${v}_o.png"
done
J=(j_arc_root j_arc_root_top j_tip j_tip_under j_loop_rear j_wing_loop j_arm_outer j_uarch_end j_uarch_mid j_upper_arm j_upper_body j_link_root j_hangar j_vplate j_keel j_wing_front j_wing_arm_under)
n=1; for ((i = 0; i < ${#J[@]}; i += 3)); do
    files=(); for j in "${J[@]:i:3}"; do files+=("$R/${j}_a.png" "$R/${j}_b.png" "$R/${j}_o.png"); done
    $P $T/view/sheet.py "$OUT/final_joints_$n.png" 3 "${files[@]}"; n=$((n + 1))
done
$P $T/view/sheet.py "$OUT/final_deviation.png" 2 $T/arms/dev_top.png $T/arms/dev_bot.png $T/arms/dev_side.png $T/arms/dev_front.png
ls "$OUT"
