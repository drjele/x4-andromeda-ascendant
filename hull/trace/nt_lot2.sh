#!/bin/bash
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace; PY=$T/../nt_venv/bin/python; P=/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese; N=$P/nt; D=$N/p; LOG=$N/lot2.log; cd $T
ram() { while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 12 ]; do sleep 60; done; }
export -f ram
one() { id=$1; nm=$2; [ -f "$N/p/$id.json" ] && exit 0; ram; nice -n 10 timeout 5400 $PY -u nt_piesa.py $P/nt_ref_toate.npz $D "$id" "$nm" 2>&1 | grep -E '^PIESA|^fara|Error' | cut -c1-500 >> $LOG; }
export -f one; export T PY P N D LOG
NT_ATT=1 SUS_INCHIDERE=16 bash -c 'one corp R001_084_D' &
cat $N/lista2.txt | xargs -P 3 -L 1 bash -c 'one "$0" "$1"'
wait; echo GATA_LOT2 >> $LOG
