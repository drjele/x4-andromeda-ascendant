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
# the top decorations lifted onto the raised rear deck; the outline width fit (body_apply.py) and the stern narrowing
# (rear_trim.py) are off since V7: they left waves and a waist, the user wants V4's plain body in plan
blender -b --python ../trace/deck_lift.py 2>&1 | grep LIFTED
# V7: the deck rebuilt with the crescent as its front (C16 removed), C4 aft, C12 inside C8, C13 rings
blender -b --python ../trace/v7_body.py 2>&1 | grep "V7 BODY"
( cd ../arms && blender -b --python a_sweep.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_joints.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python a_joints_sdf.py >/dev/null && blender -b --python a_joints_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_scales.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_ribs.py 2>&1 | grep -iE 'error|traceback'; blender -b --python a_wing.py 2>&1 | grep -iE 'error|traceback' ) || true
( cd ../links && blender -b --python l_body.py 2>&1 | grep -iE "error|traceback"; ../overlay/.venv/bin/python l_prep.py >/dev/null && blender -b --python l_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python l_sdf.py >/dev/null && blender -b --python l_mesh.py 2>&1 | grep -iE 'error|traceback'; blender -b --python h_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true   # wing decorations (W1 sockets, W2 ribs) removed at the user's request 2026-10-25
( cd ../uarch && blender -b --python g_sweep.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python g_sdf.py >/dev/null && blender -b --python g_mesh.py 2>&1 | grep -iE "error|traceback"; blender -b --python g_nacelle.py 2>&1 | grep -iE "error|traceback"; blender -b --python g_grille.py 2>&1 | grep -iE "error|traceback" ) || true
( cd ../upper && blender -b --python u_vox.py 2>&1 | grep -iE 'error|traceback'; ../overlay/.venv/bin/python u_sdf.py >/dev/null && blender -b --python u_mesh.py 2>&1 | grep -iE 'error|traceback' ) || true
# every surface evened out last (Taubin, per group passes in smooth_all.json)
cp ../vtop/v_scene.blend ../vtop/v_scene_presmooth.blend      # to retune smooth_all.json without a full rebuild
blender -b --python ../trace/smooth_all.py 2>&1 | grep -oE "^SMOOTH .{0,80}"
blender -b --python ../trace/list_parts.py 2>&1 | grep -E "MISSING|EXTRA"
./reload.sh
