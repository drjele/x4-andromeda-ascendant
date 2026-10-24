#!/usr/bin/env bash
# Pass-2 review sheets: the pass-1 sheets plus neutral-grey renders beside the series references and cross-sections.
set -e
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp; OUT=${1:-/home/adrian/Documents/Andromeda/2026-10-24-fable/pass3}; R=$T/view/fable2
REF=/home/adrian/Documents/Andromeda/references; P=$T/overlay/.venv/bin/python
mkdir -p "$R" "$OUT"
$T/view/fable.sh "$OUT" >/dev/null
blender -b --python $T/view/closeup.py -- "$R" abo "slats:700,900,-200:200,230,-60:50" "ovals:500,300,700:120,60,150:50" "vplate:350,900,650:80,300,300:50" "wing_sec:700,330,420:580,350,110:70" "unose_q:500,900,-800:0,120,-290:50" 2>&1 | grep -iE "error|traceback" || true
sheet() { n=$1; shift; files=(); for j in "$@"; do files+=("$R/${j}_a.png" "$R/${j}_b.png" "$R/${j}_o.png"); done; $P $T/view/sheet.py "$OUT/fable_$n.png" 3 "${files[@]}"; }
sheet new_parts slats ovals vplate; sheet wing_nose wing_sec unose_q
blender -b --python $T/view/grey.py -- "$R" 2>&1 | grep -iE "error|traceback" || true
for n in 02:02_Andromeda_Ascendant.jpg 10:10_Sideviewofandromeda.jpg 13:13_Andromedaorthographicbottom.jpg 14:14_Andromedaorthographictop.jpg 15:15_Andromedaorthographicfront.jpg 16:16_Andromedaorthographicside.jpg; do
    $P $T/view/sheet.py "$OUT/grey_${n%%:*}.png" 1 "$REF/${n#*:}" "$R/${n%%:*}_grey.png"
done
blender -b --python $T/view/section.py -- "$R/sections.json" root_y:y:141 root_x:x:301 strap:y:-101 plateau:y:601 plateau_top:y:601 socket:y:-351 socket_x:x:341 wing:y:351 unose:x:1 2>&1 | grep -iE "SECTIONS|error|traceback" || true
$P $T/view/section_draw.py "$R/sections.json" "$R" root_y:0,480,120,400 root_x:-60,360,100,400 strap:0,860,-400,400:1.2 plateau:-260,260,-260,120:2:corp plateau_top:-200,200,-20,80:4:corp socket:230,460,40,260:3:link_r,wing_socket_r socket_x:-440,-260,60,240:3:link_r,wing_socket_r wing:420,720,20,220 unose:60,300,-350,-220
$P $T/view/sheet.py "$OUT/sections.png" 2 $R/sec_root_y.png $R/sec_root_x.png $R/sec_strap.png $R/sec_plateau.png $R/sec_plateau_top.png $R/sec_socket.png $R/sec_socket_x.png $R/sec_wing.png $R/sec_unose.png
ls "$OUT"
