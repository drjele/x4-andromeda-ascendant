#!/usr/bin/env bash
# Every guide change carried to every block (asked: render everywhere - the welded guides, the assembled copy, the pieces
# with faces): guides redrawn at x -6000 (PS / hood / keel welded, arms loose), the assembled guide copy rebuilt at x -7700,
# the pieces rebuilt from the guides (assembled x -9400, exploded x -11200, rim = sep_PS_rama's mesh), then a render of each.
# CAMERE_G / URECHI_G=<npz>: the hood chambers' / little ears' guides (exploded offsets baked in); CAMERE=T,WM and URECHI=<npz>
# (assembled) passed on to the piece builder.
# PS_PIESE=<npz>: the PS guides the pieces are built from, when they differ from the drawn ones (the back rule re-applied).
# Usage: actualizeaza_tot.sh <in.blend> <out.blend> <ps.npz> <capac.npz (DZ 90)> <capac_asamblat.npz> <carena.npz (DZ -110)>
#        <carena_asamblat.npz> <brat.npz> <rama_baza.npz> <render prefix>
set -e
IN=$1; OUT=$2; PS=$3; CAP=$4; CAPA=$5; CAR=$6; CARA=$7; BR=$8; RAMA=$9; RP=${10}
T=$(dirname "$OUT")/tmp_act; PY=.temp/overlay/.venv/bin/python; D=.temp/trace/ghidaje_npz_draw.py
blender -b "$IN" --python $D -- $T.1.blend "$PS" -6000 GHIDAJE_PS_RAMA g_psr_sep_ g_psr_sep_ g_asamblat_ > /dev/null 2>&1
blender -b $T.1.blend --python $D -- $T.2.blend "$CAP" -6000 GHIDAJE_CAPAC g_cap_sep_ g_cap_sep_ g_ure_sep_ > /dev/null 2>&1
if [ -n "$CAMERE_G" ]; then blender -b $T.2.blend --python $D -- $T.2b.blend "$CAMERE_G" -6000 GHIDAJE_CAPAC g_cap_sep_cam_ g_cap_sep_cam_ > /dev/null 2>&1; mv $T.2b.blend $T.2.blend; fi
if [ -n "$URECHI_G" ]; then blender -b $T.2.blend --python $D -- $T.2b.blend "$URECHI_G" -6000 GHIDAJE_URECHIUSE g_ure_sep_ g_ure_sep_ > /dev/null 2>&1; mv $T.2b.blend $T.2.blend; fi
blender -b $T.2.blend --python $D -- $T.3.blend "$CAR" -6000 GHIDAJE_CARENA g_car_sep_ g_car_sep_ > /dev/null 2>&1
blender -b $T.3.blend --python $D -- $T.4.blend "$BR" -6000 GHIDAJE_BRATE g_br_sep_ g_br_sep_ > /dev/null 2>&1
SG_ASCUNDE=0 blender -b $T.4.blend --python .temp/trace/sudeaza_ghidaje.py -- $T.5.blend g_psr_sep_ghidaje_sudate GHIDAJE_PS_RAMA 2>&1 | grep SUDATE
SG_ASCUNDE=0 blender -b $T.5.blend --python .temp/trace/sudeaza_ghidaje.py -- $T.6.blend g_cap_sep_ghidaje_sudate GHIDAJE_CAPAC 2>&1 | grep SUDATE
SG_ASCUNDE=0 blender -b $T.6.blend --python .temp/trace/sudeaza_ghidaje.py -- $T.7.blend g_car_sep_ghidaje_sudate GHIDAJE_CARENA 2>&1 | grep SUDATE
blender -b $T.7.blend --python .temp/trace/asambleaza_ghidaje.py -- $T.8.blend 2>&1 | grep ASAMBLATE
$PY .temp/trace/piese_din_ghidaje.py "${PS_PIESE:-$PS}" "$RAMA" "$CARA" "$CAPA" "$BR" "${RP}_piese.npz" | grep -v rama
blender -b $T.8.blend --python-expr "
import bpy
for o in [o for o in bpy.data.objects if o.name.startswith(('gp_','gpe_'))]: bpy.data.objects.remove(o)
for n in ('PIESE_DIN_GHIDAJE_ASAMBLAT','PIESE_DIN_GHIDAJE_EXPLODAT'):
    c = bpy.data.collections.get(n)
    if c: bpy.data.collections.remove(c)
bpy.ops.wm.save_as_mainfile(filepath='$T.9.blend')" > /dev/null 2>&1
blender -b $T.9.blend --python .temp/trace/piese_din_ghidaje_blend.py -- $T.10.blend "${RP}_piese.npz" -9400 -11200 2>&1 | grep -E "PIESA" | grep -v rama
blender -b $T.10.blend --python-expr "
import bpy
src = bpy.data.objects['sep_PS_rama']
for n in ('gp_PS_rama', 'gpe_PS_rama'):
    o = bpy.data.objects[n]; old = o.data; o.data = src.data.copy(); bpy.data.meshes.remove(old)
bpy.ops.wm.save_as_mainfile(filepath='$OUT')" > /dev/null 2>&1
for k in 1 2 3 4 5 6 7 8 9 10; do rm -f "$T.$k.blend" "$T.$k.blend1"; done
blender -b "$OUT" --python .temp/trace/vedere_texturi.py > /dev/null 2>&1
blender -b "$OUT" --python .temp/trace/render_blocuri.py -- "$RP" 2>&1 | grep -c Saved
echo "ACTUALIZAT TOT -> $OUT"
