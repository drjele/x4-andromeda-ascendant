#!/usr/bin/env bash
# Rebuild the whole body scene from its parameter files, then reload Blender.
set -e
cd /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body
B="blender -b --python"
../overlay/.venv/bin/python super_rings.py >/dev/null
true
for s in super_mesh fairing_mesh dome_mesh frame_mesh blade_mesh ridge_mesh path_mesh heightpart_mesh crescent_mesh gem_mesh; do
    $B $s.py 2>&1 | grep -iE "error|traceback" && { echo "FAILED in $s"; exit 1; } || true
done
( cd ../vtop && ../overlay/.venv/bin/python v_prep.py >/dev/null && blender -b --python v_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python vdeco_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
blender -b --python /tmp/claude-1000/list.py 2>&1 | grep OBJ | awk '{print $2}' | tr '\n' ' '; echo
./reload.sh
