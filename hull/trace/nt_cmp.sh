#!/bin/bash
# cmp.sh scene outdir refregex ntregex [scale] [views]
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace; PY=$T/../nt_venv/bin/python; S=$1; OD=$2; RR=$3; NR=$4; SC=${5:-3000}; VW=${6:-jos,sus,lat,ojos,osus,spate}
cd /tmp; RES=600 CENTER0=${CENTER0-1} XO=0 timeout 500 blender -b $S --python $T/nt_render_set.py -- $OD $SC $VW "ref:$RR" 2>&1 | grep -E '^[A-Za-z]*Error' | grep -v waypoint
RES=600 CENTER0=${CENTER0-1} XO=-7200 COL=NAVA_TERMINATA timeout 500 blender -b $S --python $T/nt_render_set.py -- $OD $SC $VW "nt:$NR" 2>&1 | grep -E '^[A-Za-z]*Error' | grep -v waypoint
cd $OD; L=""; for r in ref nt; do for k in ${VW//,/ }; do L="$L ${r}_$k.png"; done; done; $PY $T/nt_sheet.py foaie.png 420 $(echo ${VW//,/ } | wc -w) $L 2>/dev/null
