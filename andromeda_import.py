"""Build and optionally export the X4 Andromeda scene with Blender 4.2."""

import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SOURCE_DIRECTORY = Path.home() / "x4mod/source"
SOURCE_STEM = "XMC"
SHIP_LENGTH = 2700.0
MATERIAL_NAME = "andromeda.andromeda_hull"
LOD_RATIO = (
    ("part_main", 1.0),
    ("part_main.LOD1", 0.55),
    ("part_main.LOD2", 0.25),
    ("part_main.LOD3", 0.1),
)
SAMPLE_RADIUS = 0.035
DORSAL_FACING = (0.0, 0.0, 0.0)
HULL_CORE_FRACTION = 0.12
MAIN_WEAPON_TAGS = "combat extralarge andromeda weapon"
ENGINE_TAGS = "engine extralarge andromeda"
HULL_VERTEX_COLOUR = (0.18, 0.20, 0.22, 1.0)
HULL_TEXTURE_METRES = 120.0
FORWARD_FACING = (0.0, 0.0, 0.0)
ENGINE_SINK = 0.02
PAD_LIFT = 0.2
PAD_SEAT = 0.8
PAD_SKIRT = 3.0
PAD_SEGMENTS = 40
PAD_SMALL_SEGMENTS = 16
PAD_SMALL_REACH = 20.0
PAD_SQUARENESS = 5.0
PAD_FLARE = 1.5
PAD_FILLET_RINGS = 5
PAD_SMALL_FILLET_RINGS = 3
PAD_EMBED = 0.6
PAD_YAW_STEP = 7.5
# Half-extents across and along each mount: the vanilla socket footprint plus a rim.
PAD_HALF_EXTENTS = {
    "large turret": (36.0, 36.0),
    "medium turret": (4.0, 4.0),
    "medium shield": (5.0, 9.0),
    "extralarge shield": (52.0, 100.0),
}

# Stable names and stations from the first shipped component, in Blender axes / ship length.
MOUNTS = (
    (
        "con_shieldgen_xl_01",
        "extralarge shield standard",
        "group_front_up_mid",
        (0.0, 0.19284192592592592, 0.10209603703703703),
    ),
    (
        "con_shieldgen_xl_02",
        "extralarge shield standard",
        "group_mid_up_mid",
        (0.0, -0.07246274074074074, 0.11030114814814816),
    ),
    (
        "con_shieldgen_xl_03",
        "extralarge shield standard",
        "group_front_down_mid",
        (0.0, 0.19284192592592592, -0.06689570370370371),
    ),
    (
        "con_shieldgen_xl_04",
        "extralarge shield standard",
        "group_mid_down_mid",
        (0.0, -0.07246274074074074, -0.11051148148148147),
    ),
    (
        "con_turret_001",
        "turret large standard missile hittable combat",
        "group_front_up_mid",
        (0.0, 0.34, -0.0023738362962962964),
    ),
    (
        "con_turret_002",
        "turret large standard missile hittable combat",
        "group_front_down_mid",
        (0.0, 0.34, -0.056736999999999996),
    ),
    (
        "con_turret_003",
        "turret large standard missile hittable combat",
        "group_mid_up_mid",
        (0.0, 0.12, 0.11171074074074075),
    ),
    (
        "con_turret_004",
        "turret large standard missile hittable combat",
        "group_mid_down_mid",
        (0.0, 0.12, -0.07186159259259259),
    ),
    (
        "con_turret_005",
        "turret large standard missile hittable combat",
        "group_mid_up_mid",
        (0.0, -0.14, 0.0693942962962963),
    ),
    (
        "con_turret_006",
        "turret large standard missile hittable combat",
        "group_mid_down_mid",
        (0.0, -0.14, -0.041415074074074076),
    ),
    (
        "con_turret_007",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.1995515925925926, 0.42, -0.046933333333333334),
    ),
    (
        "con_turret_008",
        "turret medium standard missile hittable combat",
        "group_front_down_left",
        (-0.1995515925925926, 0.42, -0.09523974074074074),
    ),
    (
        "con_turret_009",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.19955151851851852, 0.42, -0.04693337037037037),
    ),
    (
        "con_turret_010",
        "turret medium standard missile hittable combat",
        "group_front_down_right",
        (0.19955151851851852, 0.42, -0.0952397037037037),
    ),
    (
        "con_turret_011",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.2355217777777778, 0.26, 0.010772437037037038),
    ),
    (
        "con_turret_012",
        "turret medium standard missile hittable combat",
        "group_front_down_left",
        (-0.2355217777777778, 0.26, -0.10729825925925927),
    ),
    (
        "con_turret_013",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.2355217037037037, 0.26, 0.010772407407407408),
    ),
    (
        "con_turret_014",
        "turret medium standard missile hittable combat",
        "group_front_down_right",
        (0.2355217037037037, 0.26, -0.10729825925925927),
    ),
    (
        "con_turret_015",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.25232133333333334, 0.08, 0.05372177777777778),
    ),
    (
        "con_turret_016",
        "turret medium standard missile hittable combat",
        "group_mid_down_left",
        (-0.25232133333333334, 0.08, -0.12699996296296295),
    ),
    (
        "con_turret_017",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.25232133333333334, 0.08, 0.05372177777777778),
    ),
    (
        "con_turret_018",
        "turret medium standard missile hittable combat",
        "group_mid_down_right",
        (0.25232133333333334, 0.08, -0.12699992592592593),
    ),
    (
        "con_turret_019",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.2607861851851852, -0.12, -0.053059444444444444),
    ),
    (
        "con_turret_020",
        "turret medium standard missile hittable combat",
        "group_mid_down_left",
        (-0.2607861851851852, -0.12, -0.10685518518518519),
    ),
    (
        "con_turret_021",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.2607861851851852, -0.12, -0.053059481481481485),
    ),
    (
        "con_turret_022",
        "turret medium standard missile hittable combat",
        "group_mid_down_right",
        (0.2607861851851852, -0.12, -0.10685518518518519),
    ),
    (
        "con_turret_023",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.22315318518518518, -0.3, -0.017474462962962962),
    ),
    (
        "con_turret_024",
        "turret medium standard missile hittable combat",
        "group_back_down_left",
        (-0.22315318518518518, -0.3, -0.056842148148148156),
    ),
    (
        "con_turret_025",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.22315322222222223, -0.3, -0.017474425925925928),
    ),
    (
        "con_turret_026",
        "turret medium standard missile hittable combat",
        "group_back_down_right",
        (0.22315322222222223, -0.3, -0.05684218518518518),
    ),
    (
        "con_turret_027",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.18413822222222223, -0.46, 0.08035837037037037),
    ),
    (
        "con_turret_028",
        "turret medium standard missile hittable combat",
        "group_back_down_left",
        (-0.18413822222222223, -0.46, -0.002666974074074074),
    ),
    (
        "con_turret_029",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.1841382962962963, -0.46, 0.08035833333333334),
    ),
    (
        "con_turret_030",
        "turret medium standard missile hittable combat",
        "group_back_down_right",
        (0.1841382962962963, -0.46, -0.0026669985185185188),
    ),
    (
        "con_turret_031",
        "turret medium standard missile hittable combat",
        "group_front_up_left",
        (-0.055, 0.3, -0.0009001925925925926),
    ),
    (
        "con_turret_032",
        "turret medium standard missile hittable combat",
        "group_front_up_right",
        (0.055, 0.3, -0.0009002251851851852),
    ),
    (
        "con_turret_033",
        "turret medium standard missile hittable combat",
        "group_mid_up_left",
        (-0.055, 0.0, 0.12699996296296295),
    ),
    (
        "con_turret_034",
        "turret medium standard missile hittable combat",
        "group_mid_up_right",
        (0.055, 0.0, 0.12699996296296295),
    ),
    (
        "con_turret_035",
        "turret medium standard missile hittable combat",
        "group_back_up_left",
        (-0.055, -0.32, 0.11818748148148148),
    ),
    (
        "con_turret_036",
        "turret medium standard missile hittable combat",
        "group_back_up_right",
        (0.055, -0.32, 0.11818751851851851),
    ),
    (
        "con_shieldgen_m_001",
        "medium shield hittable standard",
        "group_back_down_left",
        (-0.21515318518518517, -0.315, -0.056842148148148156),
    ),
    (
        "con_shieldgen_m_002",
        "medium shield hittable standard",
        "group_back_down_right",
        (0.21515322222222222, -0.315, -0.05684218518518518),
    ),
    (
        "con_shieldgen_m_003",
        "medium shield hittable standard",
        "group_back_up_left",
        (-0.21515318518518517, -0.315, -0.017474462962962962),
    ),
    (
        "con_shieldgen_m_004",
        "medium shield hittable standard",
        "group_back_up_right",
        (0.21515322222222222, -0.315, -0.017474425925925928),
    ),
    (
        "con_shieldgen_m_005",
        "medium shield hittable standard",
        "group_front_down_left",
        (-0.1915515925925926, 0.40499999999999997, -0.09523974074074074),
    ),
    (
        "con_shieldgen_m_006",
        "medium shield hittable standard",
        "group_front_down_right",
        (0.1915515185185185, 0.40499999999999997, -0.0952397037037037),
    ),
    (
        "con_shieldgen_m_007",
        "medium shield hittable standard",
        "group_front_up_left",
        (-0.1915515925925926, 0.40499999999999997, -0.046933333333333334),
    ),
    (
        "con_shieldgen_m_008",
        "medium shield hittable standard",
        "group_front_up_right",
        (0.1915515185185185, 0.40499999999999997, -0.04693337037037037),
    ),
    (
        "con_shieldgen_m_009",
        "medium shield hittable standard",
        "group_mid_down_left",
        (-0.24432133333333333, 0.065, -0.12699996296296295),
    ),
    (
        "con_shieldgen_m_010",
        "medium shield hittable standard",
        "group_mid_down_right",
        (0.24432133333333333, 0.065, -0.12699992592592593),
    ),
    (
        "con_shieldgen_m_011",
        "medium shield hittable standard",
        "group_mid_up_left",
        (-0.24432133333333333, 0.065, 0.05372177777777778),
    ),
    (
        "con_shieldgen_m_012",
        "medium shield hittable standard",
        "group_mid_up_right",
        (0.24432133333333333, 0.065, 0.05372177777777778),
    ),
    (
        "con_shieldgen_m_013",
        "medium shield hittable standard",
        "group_engine_left",
        (-0.018, -0.23, 0.0),
    ),
    (
        "con_shieldgen_m_014",
        "medium shield hittable standard",
        "group_engine_right",
        (0.018, -0.23, 0.0),
    ),
)

# Zone mounts chosen with the user: flat, clear, mirror-symmetric sites, one group per zone,
# one medium shield beside each medium turret and two beside each large turret.
ZONE_MOUNTS = (
    (
        "con_turret_037",
        "turret medium standard missile hittable combat",
        "group_nose_up_mid",
        (0.002962962962962963, 0.38222222222222224, -0.014860794632523149),
    ),
    (
        "con_shieldgen_m_015",
        "medium shield hittable standard",
        "group_nose_up_mid",
        (0.005925925925925926, 0.3762962962962963, -0.01074191623263889),
    ),
    (
        "con_turret_038",
        "turret medium standard missile hittable combat",
        "group_nose_up_mid",
        (-0.002962962962962963, 0.38222222222222224, -0.014860794632523149),
    ),
    (
        "con_shieldgen_m_016",
        "medium shield hittable standard",
        "group_nose_up_mid",
        (-0.005925925925925926, 0.3762962962962963, -0.01074191623263889),
    ),
    (
        "con_turret_039",
        "turret medium standard missile hittable combat",
        "group_nose_up_mid",
        (0.0, 0.2903703703703704, 0.003523265697337963),
    ),
    (
        "con_shieldgen_m_017",
        "medium shield hittable standard",
        "group_nose_up_mid",
        (0.0, 0.29703703703703704, 0.0029230414496527776),
    ),
    (
        "con_turret_040",
        "turret medium standard missile hittable combat",
        "group_nose_up_mid",
        (0.011851851851851851, 0.24, -0.06719853153935185),
    ),
    (
        "con_shieldgen_m_018",
        "medium shield hittable standard",
        "group_nose_up_mid",
        (0.008888888888888889, 0.24592592592592594, -0.06828252721715856),
    ),
    (
        "con_turret_041",
        "turret medium standard missile hittable combat",
        "group_nose_up_mid",
        (-0.011851851851851851, 0.24, -0.06719853153935185),
    ),
    (
        "con_shieldgen_m_019",
        "medium shield hittable standard",
        "group_nose_up_mid",
        (-0.008888888888888889, 0.24592592592592594, -0.06828252721715856),
    ),
    (
        "con_turret_042",
        "turret medium standard missile hittable combat",
        "group_nose_down_mid",
        (0.0, 0.31851851851851853, -0.06126252916124132),
    ),
    (
        "con_shieldgen_m_020",
        "medium shield hittable standard",
        "group_nose_down_mid",
        (0.0, 0.3118518518518518, -0.06311477661132812),
    ),
    (
        "con_turret_043",
        "turret medium standard missile hittable combat",
        "group_nose_down_mid",
        (0.017777777777777778, 0.2814814814814815, -0.06293046174225984),
    ),
    (
        "con_shieldgen_m_021",
        "medium shield hittable standard",
        "group_nose_down_mid",
        (0.011851851851851851, 0.2814814814814815, -0.06513180202907987),
    ),
    (
        "con_turret_044",
        "turret medium standard missile hittable combat",
        "group_nose_down_mid",
        (-0.017777777777777778, 0.2814814814814815, -0.06293046174225984),
    ),
    (
        "con_shieldgen_m_022",
        "medium shield hittable standard",
        "group_nose_down_mid",
        (-0.011851851851851851, 0.2814814814814815, -0.06513180202907987),
    ),
    (
        "con_turret_045",
        "turret medium standard missile hittable combat",
        "group_nose_down_mid",
        (0.03259259259259259, 0.24296296296296296, -0.058443739149305556),
    ),
    (
        "con_shieldgen_m_023",
        "medium shield hittable standard",
        "group_nose_down_mid",
        (0.02962962962962963, 0.24888888888888888, -0.05976420649775752),
    ),
    (
        "con_turret_046",
        "turret medium standard missile hittable combat",
        "group_nose_down_mid",
        (-0.03259259259259259, 0.24296296296296296, -0.058443739149305556),
    ),
    (
        "con_shieldgen_m_024",
        "medium shield hittable standard",
        "group_nose_down_mid",
        (-0.02962962962962963, 0.24888888888888888, -0.05976420649775752),
    ),
    (
        "con_turret_047",
        "turret large standard missile hittable combat",
        "group_deck_up_mid",
        (0.0, 0.05925925925925926, 0.12749755859375),
    ),
    (
        "con_shieldgen_m_025",
        "medium shield hittable standard",
        "group_deck_up_mid",
        (0.02074074074074074, 0.06222222222222222, 0.1271970847800926),
    ),
    (
        "con_shieldgen_m_026",
        "medium shield hittable standard",
        "group_deck_up_mid",
        (-0.02074074074074074, 0.06222222222222222, 0.1271970847800926),
    ),
    (
        "con_turret_048",
        "turret medium standard missile hittable combat",
        "group_deck_down_mid",
        (0.0, 0.011851851851851851, 0.08506475943106193),
    ),
    (
        "con_shieldgen_m_027",
        "medium shield hittable standard",
        "group_deck_down_mid",
        (0.0, 0.018518518518518517, 0.08456195972583912),
    ),
    (
        "con_turret_049",
        "turret medium standard missile hittable combat",
        "group_deck_down_mid",
        (0.07111111111111111, -0.1274074074074074, 0.10774588125723379),
    ),
    (
        "con_shieldgen_m_028",
        "medium shield hittable standard",
        "group_deck_down_mid",
        (0.06814814814814815, -0.12148148148148148, 0.10703092221860533),
    ),
    (
        "con_turret_050",
        "turret medium standard missile hittable combat",
        "group_deck_down_mid",
        (-0.07111111111111111, -0.1274074074074074, 0.10774588125723379),
    ),
    (
        "con_shieldgen_m_029",
        "medium shield hittable standard",
        "group_deck_down_mid",
        (-0.06814814814814815, -0.12148148148148148, 0.10703092221860533),
    ),
    (
        "con_turret_051",
        "turret large standard missile hittable combat",
        "group_spine_up_mid",
        (0.0, -0.007407407407407408, 0.05368871618200231),
    ),
    (
        "con_shieldgen_m_030",
        "medium shield hittable standard",
        "group_spine_up_mid",
        (0.02074074074074074, -0.008888888888888889, 0.0511440587926794),
    ),
    (
        "con_shieldgen_m_031",
        "medium shield hittable standard",
        "group_spine_up_mid",
        (-0.02074074074074074, -0.008888888888888889, 0.0511440587926794),
    ),
    (
        "con_turret_052",
        "turret large standard missile hittable combat",
        "group_spine_down_mid",
        (0.0, -0.014814814814814815, -0.11877201786747685),
    ),
    (
        "con_shieldgen_m_032",
        "medium shield hittable standard",
        "group_spine_down_mid",
        (0.02074074074074074, -0.011851851851851851, -0.11886873598451968),
    ),
    (
        "con_shieldgen_m_033",
        "medium shield hittable standard",
        "group_spine_down_mid",
        (-0.02074074074074074, -0.011851851851851851, -0.11886873598451968),
    ),
    (
        "con_turret_053",
        "turret medium standard missile hittable combat",
        "group_aft_up_mid",
        (0.06222222222222222, -0.1688888888888889, -0.07608479252567997),
    ),
    (
        "con_shieldgen_m_034",
        "medium shield hittable standard",
        "group_aft_up_mid",
        (0.06518518518518518, -0.1748148148148148, -0.0728915461787471),
    ),
    (
        "con_turret_054",
        "turret medium standard missile hittable combat",
        "group_aft_up_mid",
        (-0.06222222222222222, -0.1688888888888889, -0.07608479252567997),
    ),
    (
        "con_shieldgen_m_035",
        "medium shield hittable standard",
        "group_aft_up_mid",
        (-0.06518518518518518, -0.1748148148148148, -0.0728915461787471),
    ),
    (
        "con_turret_055",
        "turret medium standard missile hittable combat",
        "group_aft_up_mid",
        (0.06814814814814815, -0.1688888888888889, 0.12179881908275463),
    ),
    (
        "con_shieldgen_m_036",
        "medium shield hittable standard",
        "group_aft_up_mid",
        (0.06518518518518518, -0.1748148148148148, 0.12127115885416667),
    ),
    (
        "con_turret_056",
        "turret medium standard missile hittable combat",
        "group_aft_up_mid",
        (-0.06814814814814815, -0.1688888888888889, 0.12179881908275463),
    ),
    (
        "con_shieldgen_m_037",
        "medium shield hittable standard",
        "group_aft_up_mid",
        (-0.06518518518518518, -0.1748148148148148, 0.12127115885416667),
    ),
    (
        "con_turret_057",
        "turret medium standard missile hittable combat",
        "group_aft_up_mid",
        (0.0, -0.21925925925925926, 0.05524441189236111),
    ),
    (
        "con_shieldgen_m_038",
        "medium shield hittable standard",
        "group_aft_up_mid",
        (0.0, -0.22592592592592592, 0.054610007957175924),
    ),
    (
        "con_turret_058",
        "turret medium standard missile hittable combat",
        "group_aft_down_mid",
        (0.07111111111111111, -0.1688888888888889, -0.08841913293909144),
    ),
    (
        "con_shieldgen_m_039",
        "medium shield hittable standard",
        "group_aft_down_mid",
        (0.07111111111111111, -0.1748148148148148, -0.08623816030996817),
    ),
    (
        "con_turret_059",
        "turret medium standard missile hittable combat",
        "group_aft_down_mid",
        (-0.07111111111111111, -0.1688888888888889, -0.08841913293909144),
    ),
    (
        "con_shieldgen_m_040",
        "medium shield hittable standard",
        "group_aft_down_mid",
        (-0.07111111111111111, -0.1748148148148148, -0.08623816030996817),
    ),
    (
        "con_turret_060",
        "turret medium standard missile hittable combat",
        "group_aft_down_mid",
        (0.07111111111111111, -0.17185185185185184, 0.12214642560040509),
    ),
    (
        "con_shieldgen_m_041",
        "medium shield hittable standard",
        "group_aft_down_mid",
        (0.06814814814814815, -0.1688888888888889, 0.10498878761574074),
    ),
    (
        "con_turret_061",
        "turret medium standard missile hittable combat",
        "group_aft_down_mid",
        (-0.07111111111111111, -0.17185185185185184, 0.12214642560040509),
    ),
    (
        "con_shieldgen_m_042",
        "medium shield hittable standard",
        "group_aft_down_mid",
        (-0.06814814814814815, -0.1688888888888889, 0.10498878761574074),
    ),
    (
        "con_turret_062",
        "turret medium standard missile hittable combat",
        "group_aft_down_mid",
        (0.0, -0.21925925925925926, -0.012543724907769097),
    ),
    (
        "con_shieldgen_m_043",
        "medium shield hittable standard",
        "group_aft_down_mid",
        (0.0, -0.22592592592592592, -0.01067598130967882),
    ),
    (
        "con_turret_063",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.1748148148148148, 0.49777777777777776, -0.07981562861689814),
    ),
    (
        "con_shieldgen_m_044",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.17777777777777778, 0.4918518518518519, -0.07585756655092593),
    ),
    (
        "con_turret_064",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.1748148148148148, 0.49777777777777776, -0.07981562861689814),
    ),
    (
        "con_shieldgen_m_045",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.17777777777777778, 0.4918518518518519, -0.07585756655092593),
    ),
    (
        "con_turret_065",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.2162962962962963, 0.36148148148148146, -0.03684606481481482),
    ),
    (
        "con_shieldgen_m_046",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.21037037037037037, 0.36148148148148146, -0.038011293764467595),
    ),
    (
        "con_turret_066",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.2162962962962963, 0.36148148148148146, -0.03684606481481482),
    ),
    (
        "con_shieldgen_m_047",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.21037037037037037, 0.36148148148148146, -0.038011293764467595),
    ),
    (
        "con_turret_067",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.2162962962962963, 0.30518518518518517, -0.09390273482711227),
    ),
    (
        "con_shieldgen_m_048",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.2162962962962963, 0.3111111111111111, -0.09143896032262731),
    ),
    (
        "con_turret_068",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.2162962962962963, 0.30518518518518517, -0.09390273482711227),
    ),
    (
        "con_shieldgen_m_049",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.2162962962962963, 0.3111111111111111, -0.09143896032262731),
    ),
    (
        "con_turret_069",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.2311111111111111, 0.2637037037037037, -0.0031129286024305556),
    ),
    (
        "con_shieldgen_m_050",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.22518518518518518, 0.2637037037037037, -0.0049300582320601855),
    ),
    (
        "con_turret_070",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.2311111111111111, 0.2637037037037037, -0.0031129286024305556),
    ),
    (
        "con_shieldgen_m_051",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.22518518518518518, 0.2637037037037037, -0.0049300582320601855),
    ),
    (
        "con_turret_071",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.2548148148148148, 0.2311111111111111, -0.09747282805266204),
    ),
    (
        "con_shieldgen_m_052",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.2518518518518518, 0.23407407407407407, -0.09294157805266204),
    ),
    (
        "con_turret_072",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.2548148148148148, 0.2311111111111111, -0.09747282805266204),
    ),
    (
        "con_shieldgen_m_053",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.2518518518518518, 0.23407407407407407, -0.09294157805266204),
    ),
    (
        "con_turret_073",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.2311111111111111, 0.16592592592592592, 0.03316514756944444),
    ),
    (
        "con_shieldgen_m_054",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.2311111111111111, 0.17185185185185184, 0.03136298285590278),
    ),
    (
        "con_turret_074",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.2311111111111111, 0.16592592592592592, 0.03316514756944444),
    ),
    (
        "con_shieldgen_m_055",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.2311111111111111, 0.17185185185185184, 0.03136298285590278),
    ),
    (
        "con_turret_075",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.22814814814814816, 0.14222222222222222, -0.09148547137225116),
    ),
    (
        "con_shieldgen_m_056",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.2311111111111111, 0.13925925925925925, -0.08692537660951967),
    ),
    (
        "con_turret_076",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.22814814814814816, 0.14222222222222222, -0.09148547137225116),
    ),
    (
        "con_shieldgen_m_057",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.2311111111111111, 0.13925925925925925, -0.08692537660951967),
    ),
    (
        "con_turret_077",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.21925925925925926, 0.08592592592592592, 0.05740360966435185),
    ),
    (
        "con_shieldgen_m_058",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.21333333333333335, 0.08592592592592592, 0.06247698748553241),
    ),
    (
        "con_turret_078",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.21925925925925926, 0.08592592592592592, 0.05740360966435185),
    ),
    (
        "con_shieldgen_m_059",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.21333333333333335, 0.08592592592592592, 0.06247698748553241),
    ),
    (
        "con_turret_079",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.14814814814814814, 0.056296296296296296, 0.08793289749710648),
    ),
    (
        "con_shieldgen_m_060",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.15703703703703703, 0.056296296296296296, 0.08653351960358796),
    ),
    (
        "con_turret_080",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.14814814814814814, 0.056296296296296296, 0.08793289749710648),
    ),
    (
        "con_shieldgen_m_061",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.15703703703703703, 0.056296296296296296, 0.08653351960358796),
    ),
    (
        "con_turret_081",
        "turret medium standard missile hittable combat",
        "group_arm_up_right",
        (0.24, 0.056296296296296296, -0.06611884223090278),
    ),
    (
        "con_shieldgen_m_062",
        "medium shield hittable standard",
        "group_arm_up_right",
        (0.23407407407407407, 0.05925925925925926, -0.06599627459490741),
    ),
    (
        "con_turret_082",
        "turret medium standard missile hittable combat",
        "group_arm_up_left",
        (-0.24, 0.056296296296296296, -0.06611884223090278),
    ),
    (
        "con_shieldgen_m_063",
        "medium shield hittable standard",
        "group_arm_up_left",
        (-0.23407407407407407, 0.05925925925925926, -0.06599627459490741),
    ),
    (
        "con_turret_083",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.1748148148148148, 0.49777777777777776, -0.0888820563422309),
    ),
    (
        "con_shieldgen_m_064",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.1748148148148148, 0.4918518518518519, -0.0919775503653067),
    ),
    (
        "con_turret_084",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.1748148148148148, 0.49777777777777776, -0.0888820563422309),
    ),
    (
        "con_shieldgen_m_065",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.1748148148148148, 0.4918518518518519, -0.0919775503653067),
    ),
    (
        "con_turret_085",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.22814814814814816, 0.3674074074074074, -0.04918828328450521),
    ),
    (
        "con_shieldgen_m_066",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.2222222222222222, 0.3674074074074074, -0.05261662235966435),
    ),
    (
        "con_turret_086",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.22814814814814816, 0.3674074074074074, -0.04918828328450521),
    ),
    (
        "con_shieldgen_m_067",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.2222222222222222, 0.3674074074074074, -0.05261662235966435),
    ),
    (
        "con_turret_087",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.2222222222222222, 0.3111111111111111, -0.10569123444733797),
    ),
    (
        "con_shieldgen_m_068",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.22518518518518518, 0.30518518518518517, -0.1067538791232639),
    ),
    (
        "con_turret_088",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.2222222222222222, 0.3111111111111111, -0.10569123444733797),
    ),
    (
        "con_shieldgen_m_069",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.22518518518518518, 0.30518518518518517, -0.1067538791232639),
    ),
    (
        "con_turret_089",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.21925925925925926, 0.2637037037037037, -0.01459507977520978),
    ),
    (
        "con_shieldgen_m_070",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.21925925925925926, 0.2696296296296296, -0.017811912254050925),
    ),
    (
        "con_turret_090",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.21925925925925926, 0.2637037037037037, -0.01459507977520978),
    ),
    (
        "con_shieldgen_m_071",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.21925925925925926, 0.2696296296296296, -0.017811912254050925),
    ),
    (
        "con_turret_091",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.24592592592592594, 0.23407407407407407, -0.10974088315610532),
    ),
    (
        "con_shieldgen_m_072",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.24296296296296296, 0.24, -0.11065101906105324),
    ),
    (
        "con_turret_092",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.24592592592592594, 0.23407407407407407, -0.10974088315610532),
    ),
    (
        "con_shieldgen_m_073",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.24296296296296296, 0.24, -0.11065101906105324),
    ),
    (
        "con_turret_093",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.24296296296296296, 0.16, 0.021718740110044127),
    ),
    (
        "con_shieldgen_m_074",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.24296296296296296, 0.16592592592592592, 0.01880536679868345),
    ),
    (
        "con_turret_094",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.24296296296296296, 0.16, 0.021718740110044127),
    ),
    (
        "con_shieldgen_m_075",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.24296296296296296, 0.16592592592592592, 0.01880536679868345),
    ),
    (
        "con_turret_095",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.2577777777777778, 0.13925925925925925, -0.10847462972005208),
    ),
    (
        "con_shieldgen_m_076",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.2518518518518518, 0.13925925925925925, -0.11385026719835069),
    ),
    (
        "con_turret_096",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.2577777777777778, 0.13925925925925925, -0.10847462972005208),
    ),
    (
        "con_shieldgen_m_077",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.2518518518518518, 0.13925925925925925, -0.11385026719835069),
    ),
    (
        "con_turret_097",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.2222222222222222, 0.08888888888888889, 0.05097856874819155),
    ),
    (
        "con_shieldgen_m_078",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.2222222222222222, 0.09481481481481481, 0.046342095269097223),
    ),
    (
        "con_turret_098",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.2222222222222222, 0.08888888888888889, 0.05097856874819155),
    ),
    (
        "con_shieldgen_m_079",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.2222222222222222, 0.09481481481481481, 0.046342095269097223),
    ),
    (
        "con_turret_099",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.14814814814814814, 0.056296296296296296, 0.07067283347800926),
    ),
    (
        "con_shieldgen_m_080",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.15407407407407409, 0.056296296296296296, 0.06877421626338252),
    ),
    (
        "con_turret_100",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.14814814814814814, 0.056296296296296296, 0.07067283347800926),
    ),
    (
        "con_shieldgen_m_081",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.15407407407407409, 0.056296296296296296, 0.06877421626338252),
    ),
    (
        "con_turret_101",
        "turret medium standard missile hittable combat",
        "group_arm_down_right",
        (0.21333333333333335, 0.056296296296296296, -0.09899102105034722),
    ),
    (
        "con_shieldgen_m_082",
        "medium shield hittable standard",
        "group_arm_down_right",
        (0.2074074074074074, 0.056296296296296296, -0.09510111490885417),
    ),
    (
        "con_turret_102",
        "turret medium standard missile hittable combat",
        "group_arm_down_left",
        (-0.21333333333333335, 0.056296296296296296, -0.09899102105034722),
    ),
    (
        "con_shieldgen_m_083",
        "medium shield hittable standard",
        "group_arm_down_left",
        (-0.2074074074074074, 0.056296296296296296, -0.09510111490885417),
    ),
    (
        "con_turret_103",
        "turret large standard missile hittable combat",
        "group_flank_up_right",
        (0.21481481481481482, 0.044444444444444446, -0.060448676215277775),
    ),
    (
        "con_shieldgen_m_084",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.20444444444444446, 0.02666666666666667, -0.05639404296875),
    ),
    (
        "con_shieldgen_m_085",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.19555555555555557, 0.035555555555555556, -0.05972461841724537),
    ),
    (
        "con_turret_104",
        "turret large standard missile hittable combat",
        "group_flank_up_left",
        (-0.21481481481481482, 0.044444444444444446, -0.060448676215277775),
    ),
    (
        "con_shieldgen_m_086",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.19555555555555557, 0.035555555555555556, -0.05972461841724537),
    ),
    (
        "con_shieldgen_m_087",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.20444444444444446, 0.02666666666666667, -0.05639404296875),
    ),
    (
        "con_turret_105",
        "turret large standard missile hittable combat",
        "group_flank_up_right",
        (0.24444444444444444, -0.06666666666666667, -0.059309262876157405),
    ),
    (
        "con_shieldgen_m_088",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.23703703703703705, -0.08592592592592592, -0.05529798719618056),
    ),
    (
        "con_shieldgen_m_089",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.22518518518518518, -0.07111111111111111, -0.05228954173900463),
    ),
    (
        "con_turret_106",
        "turret large standard missile hittable combat",
        "group_flank_up_left",
        (-0.24444444444444444, -0.06666666666666667, -0.059309262876157405),
    ),
    (
        "con_shieldgen_m_090",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.22518518518518518, -0.07111111111111111, -0.05228954173900463),
    ),
    (
        "con_shieldgen_m_091",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.23703703703703705, -0.08592592592592592, -0.05529798719618056),
    ),
    (
        "con_turret_107",
        "turret large standard missile hittable combat",
        "group_flank_up_right",
        (0.18518518518518517, -0.15555555555555556, -0.037341760706018516),
    ),
    (
        "con_shieldgen_m_092",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.20444444444444446, -0.15407407407407409, -0.045236002604166665),
    ),
    (
        "con_shieldgen_m_093",
        "medium shield hittable standard",
        "group_flank_up_right",
        (0.1985185185185185, -0.1688888888888889, -0.04715304904513889),
    ),
    (
        "con_turret_108",
        "turret large standard missile hittable combat",
        "group_flank_up_left",
        (-0.18518518518518517, -0.15555555555555556, -0.037341760706018516),
    ),
    (
        "con_shieldgen_m_094",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.1985185185185185, -0.1688888888888889, -0.04715304904513889),
    ),
    (
        "con_shieldgen_m_095",
        "medium shield hittable standard",
        "group_flank_up_left",
        (-0.20444444444444446, -0.15407407407407409, -0.045236002604166665),
    ),
    (
        "con_turret_109",
        "turret large standard missile hittable combat",
        "group_flank_down_right",
        (0.22962962962962963, 0.05185185185185185, -0.11685221354166667),
    ),
    (
        "con_shieldgen_m_096",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.24592592592592594, 0.047407407407407405, -0.12908321804470485),
    ),
    (
        "con_shieldgen_m_097",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.21925925925925926, 0.04148148148148148, -0.1016241455078125),
    ),
    (
        "con_turret_110",
        "turret large standard missile hittable combat",
        "group_flank_down_left",
        (-0.22962962962962963, 0.05185185185185185, -0.11685221354166667),
    ),
    (
        "con_shieldgen_m_098",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.21925925925925926, 0.04148148148148148, -0.1016241455078125),
    ),
    (
        "con_shieldgen_m_099",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.24592592592592594, 0.047407407407407405, -0.12908321804470485),
    ),
    (
        "con_turret_111",
        "turret large standard missile hittable combat",
        "group_flank_down_right",
        (0.2518518518518518, -0.05925925925925926, -0.11226860894097222),
    ),
    (
        "con_shieldgen_m_100",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.2725925925925926, -0.06222222222222222, -0.1118423122829861),
    ),
    (
        "con_shieldgen_m_101",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.23703703703703705, -0.06518518518518518, -0.09873609754774305),
    ),
    (
        "con_turret_112",
        "turret large standard missile hittable combat",
        "group_flank_down_left",
        (-0.2518518518518518, -0.05925925925925926, -0.11226860894097222),
    ),
    (
        "con_shieldgen_m_102",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.23703703703703705, -0.06518518518518518, -0.09873609754774305),
    ),
    (
        "con_shieldgen_m_103",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.2725925925925926, -0.06222222222222222, -0.1118423122829861),
    ),
    (
        "con_turret_113",
        "turret large standard missile hittable combat",
        "group_flank_down_right",
        (0.18518518518518517, -0.13333333333333333, -0.06644661232277199),
    ),
    (
        "con_shieldgen_m_104",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.20148148148148148, -0.1274074074074074, -0.07867083514178241),
    ),
    (
        "con_shieldgen_m_105",
        "medium shield hittable standard",
        "group_flank_down_right",
        (0.18666666666666668, -0.11259259259259259, -0.06858608669704862),
    ),
    (
        "con_turret_114",
        "turret large standard missile hittable combat",
        "group_flank_down_left",
        (-0.18518518518518517, -0.13333333333333333, -0.06644661232277199),
    ),
    (
        "con_shieldgen_m_106",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.18666666666666668, -0.11259259259259259, -0.06858608669704862),
    ),
    (
        "con_shieldgen_m_107",
        "medium shield hittable standard",
        "group_flank_down_left",
        (-0.20148148148148148, -0.1274074074074074, -0.07867083514178241),
    ),
    (
        "con_turret_115",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.11555555555555555, -0.2785185185185185, -0.029283673321759258),
    ),
    (
        "con_shieldgen_m_108",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.12148148148148148, -0.2785185185185185, -0.025024775752314814),
    ),
    (
        "con_turret_116",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.11555555555555555, -0.2785185185185185, -0.029283673321759258),
    ),
    (
        "con_shieldgen_m_109",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.12148148148148148, -0.2785185185185185, -0.025024775752314814),
    ),
    (
        "con_turret_117",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.07703703703703704, -0.2814814814814815, 0.11447550455729166),
    ),
    (
        "con_shieldgen_m_110",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.09481481481481481, -0.2814814814814815, 0.12114655671296297),
    ),
    (
        "con_turret_118",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.07703703703703704, -0.2814814814814815, 0.11447550455729166),
    ),
    (
        "con_shieldgen_m_111",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.09481481481481481, -0.2814814814814815, 0.12114655671296297),
    ),
    (
        "con_turret_119",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.24, -0.28444444444444444, -0.04288420500578704),
    ),
    (
        "con_shieldgen_m_112",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.23407407407407407, -0.2814814814814815, -0.037817563657407405),
    ),
    (
        "con_turret_120",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.24, -0.28444444444444444, -0.04288420500578704),
    ),
    (
        "con_shieldgen_m_113",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.23407407407407407, -0.2814814814814815, -0.037817563657407405),
    ),
    (
        "con_turret_121",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.17777777777777778, -0.32592592592592595, -0.016143482349537035),
    ),
    (
        "con_shieldgen_m_114",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.17777777777777778, -0.33185185185185184, -0.018466254340277776),
    ),
    (
        "con_turret_122",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.17777777777777778, -0.32592592592592595, -0.016143482349537035),
    ),
    (
        "con_shieldgen_m_115",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.17777777777777778, -0.33185185185185184, -0.018466254340277776),
    ),
    (
        "con_turret_123",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.11555555555555555, -0.3348148148148148, 0.10953016493055556),
    ),
    (
        "con_shieldgen_m_116",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.10962962962962963, -0.3348148148148148, 0.11336570457175926),
    ),
    (
        "con_turret_124",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.11555555555555555, -0.3348148148148148, 0.10953016493055556),
    ),
    (
        "con_shieldgen_m_117",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.10962962962962963, -0.3348148148148148, 0.11336570457175926),
    ),
    (
        "con_turret_125",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.21037037037037037, -0.397037037037037, -0.005537064163773148),
    ),
    (
        "con_shieldgen_m_118",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.2074074074074074, -0.40296296296296297, -0.0016895887586805556),
    ),
    (
        "con_turret_126",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.21037037037037037, -0.397037037037037, -0.005537064163773148),
    ),
    (
        "con_shieldgen_m_119",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.2074074074074074, -0.40296296296296297, -0.0016895887586805556),
    ),
    (
        "con_turret_127",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.10666666666666667, -0.4, 0.09835254810474538),
    ),
    (
        "con_shieldgen_m_120",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.10962962962962963, -0.4059259259259259, 0.09874620225694444),
    ),
    (
        "con_turret_128",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.10666666666666667, -0.4, 0.09835254810474538),
    ),
    (
        "con_shieldgen_m_121",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.10962962962962963, -0.4059259259259259, 0.09874620225694444),
    ),
    (
        "con_turret_129",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.1748148148148148, -0.4414814814814815, 0.017696940104166666),
    ),
    (
        "con_shieldgen_m_122",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.18074074074074073, -0.43851851851851853, 0.020416440610532407),
    ),
    (
        "con_turret_130",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.1748148148148148, -0.4414814814814815, 0.017696940104166666),
    ),
    (
        "con_shieldgen_m_123",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.18074074074074073, -0.43851851851851853, 0.020416440610532407),
    ),
    (
        "con_turret_131",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.13037037037037036, -0.45925925925925926, 0.08760271990740741),
    ),
    (
        "con_shieldgen_m_124",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.1362962962962963, -0.45925925925925926, 0.08983362268518519),
    ),
    (
        "con_turret_132",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.13037037037037036, -0.45925925925925926, 0.08760271990740741),
    ),
    (
        "con_shieldgen_m_125",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.1362962962962963, -0.45925925925925926, 0.08983362268518519),
    ),
    (
        "con_turret_133",
        "turret medium standard missile hittable combat",
        "group_loop_up_right",
        (0.17185185185185184, -0.4948148148148148, 0.054035780164930554),
    ),
    (
        "con_shieldgen_m_126",
        "medium shield hittable standard",
        "group_loop_up_right",
        (0.1688888888888889, -0.4948148148148148, 0.06054316767939815),
    ),
    (
        "con_turret_134",
        "turret medium standard missile hittable combat",
        "group_loop_up_left",
        (-0.17185185185185184, -0.4948148148148148, 0.054035780164930554),
    ),
    (
        "con_shieldgen_m_127",
        "medium shield hittable standard",
        "group_loop_up_left",
        (-0.1688888888888889, -0.4948148148148148, 0.06054316767939815),
    ),
    (
        "con_turret_135",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.07703703703703704, -0.2785185185185185, 0.11156235306351273),
    ),
    (
        "con_shieldgen_m_128",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.08296296296296296, -0.2785185185185185, 0.10688043665002893),
    ),
    (
        "con_turret_136",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.07703703703703704, -0.2785185185185185, 0.11156235306351273),
    ),
    (
        "con_shieldgen_m_129",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.08296296296296296, -0.2785185185185185, 0.10688043665002893),
    ),
    (
        "con_turret_137",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.11555555555555555, -0.2785185185185185, -0.039293300487377024),
    ),
    (
        "con_shieldgen_m_130",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.12148148148148148, -0.2814814814814815, -0.03929695129394531),
    ),
    (
        "con_turret_138",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.11555555555555555, -0.2785185185185185, -0.039293300487377024),
    ),
    (
        "con_shieldgen_m_131",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.12148148148148148, -0.2814814814814815, -0.03929695129394531),
    ),
    (
        "con_turret_139",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.24, -0.2785185185185185, -0.05277157253689236),
    ),
    (
        "con_shieldgen_m_132",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.23407407407407407, -0.2785185185185185, -0.055411755597149885),
    ),
    (
        "con_turret_140",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.24, -0.2785185185185185, -0.05277157253689236),
    ),
    (
        "con_shieldgen_m_133",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.23407407407407407, -0.2785185185185185, -0.055411755597149885),
    ),
    (
        "con_turret_141",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.17777777777777778, -0.32, -0.03520654183846933),
    ),
    (
        "con_shieldgen_m_134",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.18074074074074073, -0.31407407407407406, -0.035227203369140626),
    ),
    (
        "con_turret_142",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.17777777777777778, -0.32, -0.03520654183846933),
    ),
    (
        "con_shieldgen_m_135",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.18074074074074073, -0.31407407407407406, -0.035227203369140626),
    ),
    (
        "con_turret_143",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.11555555555555555, -0.33185185185185184, 0.10399202700014468),
    ),
    (
        "con_shieldgen_m_136",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.11555555555555555, -0.3377777777777778, 0.10158838342737268),
    ),
    (
        "con_turret_144",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.11555555555555555, -0.33185185185185184, 0.10399202700014468),
    ),
    (
        "con_shieldgen_m_137",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.11555555555555555, -0.3377777777777778, 0.10158838342737268),
    ),
    (
        "con_turret_145",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.19555555555555557, -0.39111111111111113, -0.020415429009331597),
    ),
    (
        "con_shieldgen_m_138",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.19555555555555557, -0.397037037037037, -0.018052522164803964),
    ),
    (
        "con_turret_146",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.19555555555555557, -0.39111111111111113, -0.020415429009331597),
    ),
    (
        "con_shieldgen_m_139",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.19555555555555557, -0.397037037037037, -0.018052522164803964),
    ),
    (
        "con_turret_147",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.10666666666666667, -0.397037037037037, 0.09442741111472801),
    ),
    (
        "con_shieldgen_m_140",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.10962962962962963, -0.39111111111111113, 0.09164043285228587),
    ),
    (
        "con_turret_148",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.10666666666666667, -0.397037037037037, 0.09442741111472801),
    ),
    (
        "con_shieldgen_m_141",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.10962962962962963, -0.39111111111111113, 0.09164043285228587),
    ),
    (
        "con_turret_149",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.19555555555555557, -0.4474074074074074, 0.011177902928105107),
    ),
    (
        "con_shieldgen_m_142",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.1925925925925926, -0.4533333333333333, 0.01208003008807147),
    ),
    (
        "con_turret_150",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.19555555555555557, -0.4474074074074074, 0.011177902928105107),
    ),
    (
        "con_shieldgen_m_143",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.1925925925925926, -0.4533333333333333, 0.01208003008807147),
    ),
    (
        "con_turret_151",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.13037037037037036, -0.4562962962962963, 0.07738178959599247),
    ),
    (
        "con_shieldgen_m_144",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.1362962962962963, -0.4562962962962963, 0.0749028636791088),
    ),
    (
        "con_turret_152",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.13037037037037036, -0.4562962962962963, 0.07738178959599247),
    ),
    (
        "con_shieldgen_m_145",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.1362962962962963, -0.4562962962962963, 0.0749028636791088),
    ),
    (
        "con_turret_153",
        "turret medium standard missile hittable combat",
        "group_loop_down_right",
        (0.1688888888888889, -0.4948148148148148, 0.04293641266999421),
    ),
    (
        "con_shieldgen_m_146",
        "medium shield hittable standard",
        "group_loop_down_right",
        (0.16296296296296298, -0.4948148148148148, 0.041011177345558446),
    ),
    (
        "con_turret_154",
        "turret medium standard missile hittable combat",
        "group_loop_down_left",
        (-0.1688888888888889, -0.4948148148148148, 0.04293641266999421),
    ),
    (
        "con_shieldgen_m_147",
        "medium shield hittable standard",
        "group_loop_down_left",
        (-0.16296296296296298, -0.4948148148148148, 0.041011177345558446),
    ),
)
LAYERED = {mount[0] for mount in ZONE_MOUNTS}
MOUNTS = MOUNTS + ZONE_MOUNTS


def clear_scene():
    for item in list(bpy.data.objects):
        bpy.data.objects.remove(item, do_unlink=True)


def import_source():
    bpy.ops.wm.obj_import(
        filepath=str(SOURCE_DIRECTORY / f"{SOURCE_STEM}.obj"), forward_axis="Y", up_axis="Z"
    )
    imported = [item for item in bpy.context.scene.objects if "MESH" == item.type]
    bpy.ops.object.select_all(action="DESELECT")
    for item in imported:
        item.select_set(True)
    if not imported:
        raise ValueError("OBJ contains no mesh objects")
    bpy.context.view_layer.objects.active = imported[0]
    if 1 < len(imported):
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def normalize(mesh_object):
    corner = [vertex.co for vertex in mesh_object.data.vertices]
    low = Vector((min(c.x for c in corner), min(c.y for c in corner), min(c.z for c in corner)))
    high = Vector((max(c.x for c in corner), max(c.y for c in corner), max(c.z for c in corner)))
    length = high.y - low.y
    if 0.0 == length:
        raise ValueError("source mesh has no length along the forward axis")
    factor = SHIP_LENGTH / length
    center = (low + high) * 0.5
    for vertex in mesh_object.data.vertices:
        vertex.co = (vertex.co - center) * factor
    mesh_object.data.update()
    return factor, center


def repair_winding(mesh_object):
    mesh = mesh_object.data
    opposite = []
    for polygon in mesh.polygons:
        average = sum((mesh.corner_normals[i].vector for i in polygon.loop_indices), Vector())
        if polygon.normal.dot(average) < 0:
            opposite.append(polygon.index)
    if opposite:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in opposite])
        bm.to_mesh(mesh)
        bm.free()
        print(f"andromeda: repaired {len(opposite)} faces from a legacy OBJ")
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    mesh.update()


def prepare_channels(mesh_object):
    mesh = mesh_object.data
    for layer in list(mesh.uv_layers):
        mesh.uv_layers.remove(layer)
    uv = mesh.uv_layers.new(name="uv1")
    for polygon in mesh.polygons:
        dominant = max(range(3), key=lambda axis: abs(polygon.normal[axis]))
        axes = ((1, 2), (0, 2), (0, 1))[dominant]
        for index in polygon.loop_indices:
            position = mesh.vertices[mesh.loops[index].vertex_index].co
            uv.data[index].uv = tuple(position[axis] / HULL_TEXTURE_METRES for axis in axes)
    for existing in list(mesh.color_attributes):
        mesh.color_attributes.remove(existing)
    for name, value in (
        ("col", HULL_VERTEX_COLOUR),
        ("idcode", (0.5, 0.5, 0.5, 1.0)),
        ("paintmodmask", (0.0, 0.0, 0.0, 1.0)),
    ):
        colour = mesh.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
        for entry in colour.data:
            entry.color = value
    mesh_object.data.materials.clear()
    mesh_object.data.materials.append(
        (bpy.data.materials.get(MATERIAL_NAME) or bpy.data.materials.new(MATERIAL_NAME))
    )
    for polygon in mesh_object.data.polygons:
        polygon.use_smooth = True


def apply_modifiers(mesh_object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(mesh_object.evaluated_get(depsgraph))
    previous = mesh_object.data
    mesh_object.data = baked
    mesh_object.modifiers.clear()
    bpy.data.meshes.remove(previous)


def correct_shading(mesh_object):
    mesh = mesh_object.data
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for _ in range(10):
        wrong = []
        for polygon in mesh.polygons:
            average = sum((mesh.corner_normals[i].vector for i in polygon.loop_indices), Vector())
            if polygon.normal.dot(average) <= 0:
                wrong.append(polygon)
        if not wrong:
            return
        for polygon in wrong:
            polygon.use_smooth = False
        mesh.update()
    raise ValueError(f"{mesh_object.name}: could not produce consistent shading normals")


def build_parts(source):
    made = []
    for name, ratio in LOD_RATIO:
        mesh = source.data.copy()
        mesh_object = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(mesh_object)
        if 1.0 > ratio:
            modifier = mesh_object.modifiers.new(name="decimate", type="DECIMATE")
            modifier.ratio = ratio
            apply_modifiers(mesh_object)
        correct_shading(mesh_object)
        mesh_object.data.name = name
        made.append(mesh_object)
    wreck = bpy.data.objects.new("part_main.wreck", made[1].data.copy())
    bpy.context.scene.collection.objects.link(wreck)
    return made


def add_connection(name, tags, location, size=1.0, facing=None, group=None):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = SHIP_LENGTH * 0.012 * size
    empty.location = location
    if None is not facing:
        empty.rotation_euler = facing
    bpy.context.scene.collection.objects.link(empty)
    empty["extratags"] = tags
    if None is not group:
        empty["group_name"] = group
    if hasattr(empty, "groups") and group is not None:
        empty.groups = group
    return empty


def station_name(y_value):
    if y_value > SHIP_LENGTH * 0.15:
        return "front"
    if y_value < -SHIP_LENGTH * 0.15:
        return "back"
    return "mid"


def side_name(x_value):
    if x_value > SHIP_LENGTH * 0.02:
        return "right"
    if x_value < -SHIP_LENGTH * 0.02:
        return "left"
    return "mid"


def group_for(location, upward):
    vertical = "up" if True == upward else "down"
    return f"group_{station_name(location[1])}_{vertical}_{side_name(location[0])}"


class HullSurface:
    def __init__(self, mesh):
        self.tree = BVHTree.FromPolygons(
            [v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons]
        )
        self.height = max(abs(v.co.z) for v in mesh.vertices) + SHIP_LENGTH

    def nearest_layer(self, start, sign, height):
        # Surfaces stack under decks and arms; take the outward one nearest the seed height.
        best = (None, None)
        origin, direction = start.copy(), Vector((0, 0, -sign))
        while True:
            hit, normal, _, _ = self.tree.ray_cast(origin, direction, 2 * self.height)
            if hit is None:
                return best
            if normal.z * sign > 0 and (
                best[0] is None or abs(hit.z - height) < abs(best[0].z - height)
            ):
                best = (hit.copy(), normal.copy())
            origin = hit + direction * 0.05

    def at(self, seed, upward, name, layered=False):
        sign = 1.0 if upward else -1.0
        start = Vector((seed[0], seed[1], sign * self.height))
        hit, normal, _, _ = self.tree.ray_cast(start, Vector((0, 0, -sign)), 2 * self.height)
        if layered:
            hit, normal = self.nearest_layer(start, sign, seed[2])
        if hit is None:
            candidates = [
                entry
                for entry in self.tree.find_nearest_range(Vector(seed), SHIP_LENGTH * SAMPLE_RADIUS)
                if entry[1].z * sign > 0
            ]
            if candidates:
                hit, normal, _, _ = min(candidates, key=lambda entry: entry[3])
            if hit is not None:
                print(f"andromeda: {name} snapped to nearby surface at {tuple(hit)}")
        if hit is None or normal.z * sign <= 0:
            raise ValueError(f"{name}: no outward-facing hull surface near {tuple(seed)}")
        return hit, normal.normalized()


def longitudinal_facing(normal):
    normal = normal.normalized()
    forward = Vector((0, 1, 0))
    forward -= normal * forward.dot(normal)
    if forward.length < 1e-6:
        raise ValueError("mount normal leaves no longitudinal direction on the hull")
    forward.normalize()
    right = forward.cross(normal).normalized()
    return Matrix((right, forward, normal)).transposed().to_euler()


def pad_extents(tags):
    words = set(tags.split())
    for kind, extents in PAD_HALF_EXTENTS.items():
        if set(kind.split()) <= words:
            return extents
    raise ValueError(f"no pad size for mount tags {tags!r}")


def pad_outline(right, forward, half_extents, segments):
    outline = []
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        across, along = (
            math.copysign(abs(value) ** (2.0 / PAD_SQUARENESS), value)
            for value in (math.cos(angle), math.sin(angle))
        )
        outline.append(right * across * half_extents[0] + forward * along * half_extents[1])
    return outline


def smooth_ring(values, half_width):
    count = len(values)
    return [
        sum(values[(i + k) % count] for k in range(-half_width, half_width + 1))
        / (2 * half_width + 1)
        for i in range(count)
    ]


def yawed(frame, degrees):
    right, forward, normal = (frame.col[axis].normalized() for axis in range(3))
    angle = math.radians(degrees)
    turned = right * math.cos(angle) + forward * math.sin(angle)
    return Matrix((turned, normal.cross(turned), normal)).transposed()


def pad_roughness(surface, point, frame, half_extents):
    right, forward, normal = (frame.col[axis].normalized() for axis in range(3))
    reach = max(half_extents) * PAD_FLARE
    heights = []
    for offset in pad_outline(right, forward, half_extents, PAD_SMALL_SEGMENTS):
        for scale in (0.5, 1.0, PAD_FLARE):
            hit, _, _, _ = surface.tree.ray_cast(
                point + offset * scale + normal * reach, -normal, 2 * reach
            )
            if hit is not None:
                heights.append((hit - point).dot(normal))
    return max(heights) - min(heights) if heights else 0.0


def best_yaw(surface, point, frame, half_extents, centred):
    # A square only stays mirror-symmetric on the centre plane when straight or diagonal.
    angles = (0.0, 45.0) if centred else [i * PAD_YAW_STEP for i in range(int(90 / PAD_YAW_STEP))]
    return min(
        angles,
        key=lambda angle: (
            pad_roughness(surface, point, yawed(frame, angle), half_extents),
            abs(angle),
        ),
    )


def add_pad(bm, surface, point, frame, half_extents, top=None):
    right, forward, normal = (frame.col[axis].normalized() for axis in range(3))
    reach = max(half_extents) * PAD_FLARE
    small = max(half_extents) < PAD_SMALL_REACH
    segments = PAD_SMALL_SEGMENTS if small else PAD_SEGMENTS
    rings_count = PAD_SMALL_FILLET_RINGS if small else PAD_FILLET_RINGS
    outline = pad_outline(right, forward, half_extents, segments)

    def height(offset):
        hit, _, _, _ = surface.tree.ray_cast(point + offset + normal * reach, -normal, 2 * reach)
        return None if hit is None else (hit - point).dot(normal)

    inner = sorted(
        h for h in map(height, outline + [entry * 0.5 for entry in outline]) if h is not None
    )
    if None is top:
        seat = inner[int(PAD_SEAT * (len(inner) - 1))] if inner else 0.0
        top = max(seat, 0.0) + PAD_LIFT
    fallback = (inner[0] if inner else 0.0) - PAD_SKIRT
    # Shorten the flank where it would run past the hull edge, so every foot lands on hull.
    reaches = []
    for offset in outline:
        flare = PAD_FLARE
        while 1.0 < flare and height(offset * flare) is None:
            flare -= 0.05
        reaches.append(max(flare, 1.0))
    centre = bm.verts.new(point + normal * top)
    rings = []
    for step in range(rings_count + 1):
        t = step / rings_count
        blend = t * t * (3.0 - 2.0 * t)
        scales = [1.0 + (reach_i - 1.0) * t for reach_i in reaches]
        raw = [height(offset * scale) for offset, scale in zip(outline, scales)]
        known = [h for h in raw if h is not None]
        raw = [(fallback if not known else min(known)) if h is None else h for h in raw]
        ground = smooth_ring(raw, max(1, segments // 10))
        if step == rings_count:
            ground = [min(a, b) for a, b in zip(ground, raw)]
        ring = []
        for offset, scale, level in zip(outline, scales, ground):
            level = min(top + (level - PAD_EMBED * t - top) * blend, top)
            ring.append(bm.verts.new(point + offset * scale + normal * level))
        rings.append(ring)
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((centre, rings[0][i], rings[0][j]))
        for high, low in zip(rings, rings[1:]):
            bm.faces.new((high[i], low[i], low[j]))
            bm.faces.new((high[i], low[j], high[j]))
    return top


def mirror_partners():
    partners = {}
    for name, _, _, coordinates in MOUNTS:
        if 0.0 <= coordinates[0]:
            continue
        mirrored = Vector((-coordinates[0], coordinates[1], coordinates[2]))
        for other, _, _, candidate in MOUNTS:
            if (Vector(candidate) - mirrored).length < 1e-6:
                partners[name] = other
    return partners


def mount_frames(surface):
    partners = mirror_partners()
    found = {}
    for name, _, group, coordinates in sorted(MOUNTS, key=lambda mount: -mount[3][0]):
        partner = partners.get(name)
        if None is not partner:
            point, normal = (Vector((-v.x, v.y, v.z)) for v in found[partner])
        else:
            upward = "_up_" in group or group.startswith("group_engine_")
            point, normal = surface.at(
                Vector(coordinates) * SHIP_LENGTH, upward, name, name in LAYERED
            )
            if 0.0 == coordinates[0]:
                point.x = 0.0
                normal.x = 0.0
                normal.normalize()
        found[name] = (point, normal)
    frames = []
    for name, tags, group, _ in MOUNTS:
        point, normal = found[name]
        facing = (
            longitudinal_facing(normal)
            if "shield" in tags.split()
            else normal.to_track_quat("Z", "Y").to_euler()
        )
        frames.append((name, tags, group, point, facing))
    return frames


def add_pads(mesh_object, surface, frames):
    bm = bmesh.new()
    bm.from_mesh(mesh_object.data)
    partners = mirror_partners()
    tops = {}
    yaws = {}
    placed = {}
    # Right-hand mounts first, so each mirrored pad reuses its partner's height.
    for name, tags, group, point, facing in sorted(frames, key=lambda entry: entry[0] in partners):
        normal = facing.to_matrix().col[2].normalized()
        frame = longitudinal_facing(normal).to_matrix()
        if "turret" in tags.split():
            partner = partners.get(name)
            yaw = (
                -yaws[partner]
                if None is not partner
                else best_yaw(surface, point, frame, pad_extents(tags), abs(point.x) < 1e-6)
            )
            yaws[name] = yaw
            frame = yawed(frame, yaw)
        top = add_pad(bm, surface, point, frame, pad_extents(tags), tops.get(partners.get(name)))
        tops[name] = top
        placed[name] = (name, tags, group, point + normal * top, facing)
    bm.to_mesh(mesh_object.data)
    bm.free()
    mesh_object.data.update()
    return [placed[entry[0]] for entry in frames]


def place_mounts(placed):
    for name, tags, group, point, facing in placed:
        add_connection(name, tags, point, 1.0, facing, group)


def arm_tips(vertex):
    half_width = max(abs(c.x) for c in vertex)
    tips = []
    for side in (-1.0, 1.0):
        arm = [c for c in vertex if 0.0 < c.x * side and abs(c.x) > 0.5 * half_width]
        if 0 == len(arm):
            continue
        tips.append(max(arm, key=lambda c: c.y))
    return tips


def hull_core(vertex):
    half_width = max(abs(c.x) for c in vertex)
    core = [c for c in vertex if abs(c.x) < HULL_CORE_FRACTION * half_width]
    return core if 0 < len(core) else vertex


def place_fixed(vertex, points, factor, center, surface):
    core = hull_core(vertex)
    core_aft = min(c.y for c in core)
    core_fore = max(c.y for c in core)
    bridge, _ = surface.at((0.0, core_fore * 0.55, 0.0), True, "con_cockpit")
    add_connection("con_cockpit", "cockpit cockpit_visible", bridge, 1.0, DORSAL_FACING)
    add_connection("con_playercontrol", "playercontrol", bridge, 1.0, DORSAL_FACING)
    add_connection("con_storage01", "storage", (0.0, 0.0, 0.0), 2.0, None, "group_mid_up_mid")
    add_connection("con_shiptrader", "shiptrader", (0.0, core_aft * 0.3, 0.0))
    engine_x = SHIP_LENGTH * 0.018
    for engine_index, side in enumerate((-1.0, 1.0)):
        add_connection(
            f"con_engine_{engine_index + 1:02d}",
            ENGINE_TAGS,
            (side * engine_x, core_aft + SHIP_LENGTH * ENGINE_SINK, 0.0),
            1.6,
            None,
            f"group_engine_{'left' if 0.0 > side else 'right'}",
        )
    for weapon_index, tip in enumerate(arm_tips(vertex)):
        add_connection(
            f"con_weapon_xl_{weapon_index + 1:02d}",
            MAIN_WEAPON_TAGS,
            tip,
            2.0,
            FORWARD_FACING,
            None,
        )
    for cm_index, side in enumerate((-1.0, 1.0, -1.0, 1.0)):
        add_connection(
            f"con_countermeasure_{cm_index + 1:02d}",
            "countermeasures",
            (side * SHIP_LENGTH * 0.03, core_aft * (0.6 if 2 > cm_index else 0.25), 0.0),
            1.0,
            None,
            f"group_back_down_{'left' if 0.0 > side else 'right'}",
        )
    dock_index = 0
    for entry in points:
        if "Hangar" != entry["name"]:
            continue
        dock_index += 1
        location = (Vector(entry["position"]) - center) * factor
        add_connection(
            f"con_dockingbay_{dock_index:02d}",
            "dockingbay",
            location,
            2.0,
            None,
            group_for(location, True),
        )
    return dock_index


def main():
    global SOURCE_DIRECTORY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE_DIRECTORY)
    parser.add_argument("--export", action="store_true")
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    option = parser.parse_args(arguments)
    SOURCE_DIRECTORY = option.source
    if option.export and "[assets]" not in str(option.target):
        raise ValueError("Egosoft export requires [assets] in the target path")
    if bpy.app.version[:2] != (4, 2):
        raise ValueError("use Blender 4.2 with the Egosoft extensions")
    clear_scene()
    source = import_source()
    repair_winding(source)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from andromeda_turrets import TAGS, remove_from_hull

    turret_stations = remove_from_hull(source)
    factor, center = normalize(source)
    surface = HullSurface(source.data)
    vertex = [v.co.copy() for v in source.data.vertices]
    placed = add_pads(source, surface, mount_frames(surface))
    prepare_channels(source)
    made = build_parts(source)
    bpy.data.objects.remove(source, do_unlink=True)
    points = json.loads(
        (SOURCE_DIRECTORY / f"{SOURCE_STEM}_points.json").read_text(encoding="utf-8")
    )
    place_mounts(placed)
    for index, (pivot, frame) in enumerate(turret_stations, 1):
        location = (pivot - center) * factor
        add_connection(
            f"con_turret_integrated_{index:02d}",
            TAGS,
            location,
            facing=frame.to_euler(),
            group=group_for(location, frame[2][2] > 0),
        )
    docks = place_fixed(vertex, points, factor, center, surface)
    if hasattr(bpy.context.scene, "classAttr"):
        bpy.context.scene.classAttr = "ship_xl"
    elif option.export:
        raise RuntimeError("enable the Egosoft extensions before exporting")
    option.target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(option.target))
    print(f"andromeda: {SHIP_LENGTH:.0f} m, scale {factor:.4f}")
    print(
        f"andromeda: {len(MOUNTS)} standard mounts, 4 integrated twin turrets, {docks} docking bays"
    )
    for item in made:
        print(f"  {item.name}: {len(item.data.polygons)} faces")
    if option.export:
        for item in bpy.context.scene.objects:
            if item.get("group_name"):
                item.groups = item["group_name"]
        dae = option.target.with_name(option.target.stem + "_data.dae")
        xml = option.target.with_suffix(".xml")
        for output in (dae, xml):
            if output.exists():
                output.unlink()
        bpy.ops.ego_tools.export_data(write_xml=True)
        if not dae.is_file() or not xml.is_file():
            raise RuntimeError("Egosoft exporter did not produce both DAE and component XML")


if "__main__" == __name__:
    main()
