#!/usr/bin/env bash
# Rebuild the whole scene from its parameter files (body, V plate, arms, links, U arch, upper wings), then reload Blender.
set -e
cd /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body
B="blender -b --python"
../overlay/.venv/bin/python profile_plan.py >/dev/null && ../overlay/.venv/bin/python super_rings.py >/dev/null
true
for s in super_mesh fairing_mesh dome_mesh frame_mesh blade_mesh ridge_mesh path_mesh heightpart_mesh crescent_mesh deck_mesh gem_mesh; do
    $B $s.py 2>&1 | grep -iE "error|traceback" && { echo "FAILED in $s"; exit 1; } || true
done
( cd ../vtop && ../overlay/.venv/bin/python v_prep.py >/dev/null && blender -b --python v_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python vdeco_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
# the body fitted to the user's tablet outlines (width only; computed from V4's body, skipped if the generators changed
# its vertex count), the top decorations lifted onto the raised rear deck, the stern narrowed and the deck made flush
T=/home/adrian/Documents/Andromeda/2026-10-24-trace/tableta
blender -b --python ../trace/body_apply.py -- $T/body_fit_latime.npz 2>&1 | grep -E "BODY|SKIP"
blender -b --python ../trace/deck_lift.py 2>&1 | grep LIFTED
blender -b --python ../trace/rear_trim.py -- $T/hull.npz 2>&1 | grep TRIM
( cd ../arms && blender -b --python a_sweep.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_joints.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python a_joints_sdf.py >/dev/null && blender -b --python a_joints_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_scales.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_ribs.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_wing.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../links && blender -b --python l_body.py 2>&1 | grep -iE "error|traceback"; ../overlay/.venv/bin/python l_prep.py >/dev/null && blender -b --python l_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python l_sdf.py >/dev/null && blender -b --python l_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python h_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true   # wing decorations (W1 sockets, W2 ribs) removed at the user's request 2026-10-25
( cd ../uarch && blender -b --python g_sweep.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python g_sdf.py >/dev/null && blender -b --python g_mesh.py 2>&1 | grep -iE "error|traceback"; blender -b --python g_nacelle.py 2>&1 | grep -iE "error|traceback"; blender -b --python g_grille.py 2>&1 | grep -iE "error|traceback" ) || true
( cd ../upper && blender -b --python u_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python u_sdf.py >/dev/null && blender -b --python u_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
blender -b --python ../trace/list_parts.py 2>&1 | grep -E "MISSING|EXTRA"
./reload.sh
