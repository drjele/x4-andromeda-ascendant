#!/usr/bin/env bash
# Compare the user's traces in the tracing scene with the parts: sheets and report in a timestamped folder.
# Usage: ./trace.sh [trace.blend]   (default: the copy the user works in)
set -e
T=/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace; SRC=${1:-/home/adrian/Documents/Andromeda/2026-10-24-trace/trace.blend}
OUT=$(dirname "$SRC")/compare-$(date +%H%M); mkdir -p "$OUT"
blender -b --python $T/trace_export.py -- "$SRC" "$OUT/export.npz" 2>&1 | grep -E "EXPORT|Error"
$T/../overlay/.venv/bin/python $T/compare_trace.py "$OUT/export.npz" "$OUT" >/dev/null && rm "$OUT/export.npz" && echo "$OUT"
