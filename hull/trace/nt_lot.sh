#!/bin/bash
# Night batch: the hull and the keel first, then every listed piece (3 at a time, low priority, waits while RAM is short), the mixed scraps last.
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace; PY=$T/../nt_venv/bin/python; P=/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese; N=$P/nt; D=$N/p; LOG=$N/lot.log; cd $T
ram() { while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 12 ]; do sleep 60; done; }
export -f ram
one() { id=$1; nm=$2; [ -f "$N/p/$id.json" ] && exit 0; ram; nice -n 10 timeout 5400 $PY nt_piesa.py $P/nt_ref_toate.npz $D "$id" "$nm" 2>&1 | grep -E '^PIESA|^fara|Error' | cut -c1-600 >> $LOG; }
export -f one; export T PY P N D LOG
bash -c 'one 146 R005_146_C'
grep -v -E '^146 ' $N/lista.txt | xargs -P 3 -L 1 bash -c 'one "$0" "$1"'
NT_SHIP=$N/nava_pts.npz NT_LIM=0.02 bash -c 'one marunte R006_marunte_mijloc_S'
echo GATA_LOT >> $LOG
