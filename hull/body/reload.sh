#!/usr/bin/env bash
# Publish the working scene and reload it in the single remote Blender window with labels and overlay.
D=/home/adrian/Documents/Andromeda/2026-10-23-new-body
cp /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend "$D/"
echo "bpy.ops.wm.open_mainfile(filepath=\"$D/v_scene.blend\")" > /tmp/claude-1000/blender_cmd.py
sleep 4
cp /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/view/show.py /tmp/claude-1000/blender_cmd.py
sleep 5
tail -1 /tmp/claude-1000/blender_cmd.log
sleep 2
if [ "${SHOW_VERSIONS:-0}" = 1 ]; then cp /home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/versions/show_versions.py /tmp/claude-1000/blender_cmd.py; sleep 6; fi
