#!/usr/bin/env bash
# Rebuild the whole scene from its parameter files (body, V plate, arms, links, U arch, upper wings), then reload Blender.
set -e
cd /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body
B="blender -b --python"
../overlay/.venv/bin/python super_rings.py >/dev/null
true
for s in super_mesh fairing_mesh dome_mesh frame_mesh blade_mesh ridge_mesh path_mesh heightpart_mesh crescent_mesh gem_mesh; do
    $B $s.py 2>&1 | grep -iE "error|traceback" && { echo "FAILED in $s"; exit 1; } || true
done
( cd ../vtop && ../overlay/.venv/bin/python v_prep.py >/dev/null && blender -b --python v_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python vdeco_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../arms && blender -b --python a_sweep.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python a_sdf.py >/dev/null && blender -b --python a_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_scales.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_nacelle.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_ribs.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../links && blender -b --python l_body.py 2>&1 | grep -iE "error|traceback"; ../overlay/.venv/bin/python l_prep.py >/dev/null && blender -b --python l_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python l_sdf.py >/dev/null && blender -b --python l_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python h_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python wdeco_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../uarch && blender -b --python g_sweep.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python g_sdf.py >/dev/null && blender -b --python g_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../upper && blender -b --python u_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python u_sdf.py >/dev/null && blender -b --python u_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
blender -b --python /tmp/claude-1000/list.py 2>&1 | grep OBJ | awk '{print $2}' | tr '\n' ' '; echo
./reload.sh
