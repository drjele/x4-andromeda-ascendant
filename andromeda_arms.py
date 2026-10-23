"""Rebuild the great arc and lower arm of the right side as parametric sweeps; see DEVELOPMENT.md."""

import math

import bmesh
import numpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

RING_POINTS = 72
TRACE_RAYS = 72
TRACE_REACH = 90.0
TRACE_STEP = 15.0
TIP_CAP_RINGS = 8
# The old arc and lower arm meet at the tip; everything there goes before the new tips are built.
TIP_CLEAR = 170.0
TIP_CLEAR_MIN_X = 300.0
CUT_MARGIN = 10.0
ISLAND_MARGIN = 60.0
ISLAND_FACES = 400
# The pod starts POD_SINK inside the arms and rises to POD_LIFT outside them, so no lip shows.
POD_BLEND = 2.0
POD_SINK = 3.0
POD_EMERGE = 0.2
POD_LIFT = 1.0
POD_BULGE = 5.0
POD_MARCH = 3.0
ARMS = (
    {
        "name": "arc",
        "seed": (600.0, 900.0, -97.0),
        "toward_tip": (0.0, 1.0, 0.3),
        "control": (
            (240.8, 14.0, 275.0),
            (380.2, 94.3, 235.2),
            (510.4, 222.1, 166.3),
            (604.9, 408.5, 84.0),
            (632.7, 615.7, 0.8),
            (614.4, 840.8, -78.8),
            (563.3, 1042.4, -140.7),
            (508.1, 1219.9, -197.4),
            (467.6, 1337.0, -229.2),
        ),
        # fraction from the root, width, thickness, inner taper (0 oval, 1 point), roll in degrees
        "stations": (
            (0.04, 171.2, 45.0, 0.0, 0.0),
            (0.28, 123.9, 45.0, 0.0, 0.0),
            (0.50, 88.5, 45.0, 0.5, 0.0),
            (0.72, 88.4, 45.0, 1.0, 0.0),
            (0.93, 60.0, 40.0, 1.0, 0.0),
        ),
        "rib": (8.0, 5.0),
        "samples": 140,
        "tip_cap": 70.0,
        "cut": 0.07,
        "blend": 70.0,
        "blend_rings": 10,
    },
    {
        "name": "lower",
        "seed": (620.0, 800.0, -257.0),
        "toward_tip": (0.0, 1.0, 0.0),
        "control": (
            (640.2, 215.8, -265.1),
            (648.1, 351.0, -270.0),
            (647.5, 516.1, -266.4),
            (642.7, 666.0, -261.1),
            (626.3, 800.0, -257.1),
            (594.8, 946.5, -249.4),
            (552.8, 1089.4, -230.7),
            (503.2, 1233.3, -208.7),
            (466.3, 1347.6, -230.3),
        ),
        "stations": (
            (0.04, 140.0, 60.0, 0.0, 0.0),
            (0.25, 90.0, 55.0, 0.0, 0.0),
            (0.50, 90.0, 48.0, 0.0, 0.0),
            (0.75, 85.0, 42.0, 0.0, 0.0),
            (0.95, 55.0, 32.0, 0.0, 0.0),
        ),
        "samples": 120,
        "tip_cap": 70.0,
        "cut": 0.14,
        "blend": 80.0,
        "blend_rings": 10,
    },
)


def frame(tangent):
    # Width runs level and outward, thickness up; both stay perpendicular to the path.
    tangent = tangent.normalized()
    width = tangent.cross(Vector((0.0, 0.0, 1.0)))
    width = width.normalized() if width.length > 1e-3 else Vector((1.0, 0.0, 0.0))
    if width.x < 0.0:
        width = -width
    return tangent, width, width.cross(tangent).normalized()


def catmull(points, per_span):
    padded = [points[0], *points, points[-1]]
    line = []
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1 : i + 3]
        for j in range(per_span):
            t = j / per_span
            line.append(
                0.5
                * (
                    2 * p1
                    + (p2 - p0) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                    + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t
                )
            )
    line.append(points[-1])
    return line


def resample(line, count):
    lengths = [0.0]
    for a, b in zip(line, line[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    out = []
    for k in range(count):
        target = lengths[-1] * k / (count - 1)
        i = min(max(j for j in range(len(lengths)) if lengths[j] <= target), len(line) - 2)
        f = (target - lengths[i]) / max(1e-9, lengths[i + 1] - lengths[i])
        out.append(line[i].lerp(line[i + 1], f))
    return out


def station_value(stations, fraction, column):
    if fraction <= stations[0][0]:
        return stations[0][column]
    if fraction >= stations[-1][0]:
        return stations[-1][column]
    for a, b in zip(stations, stations[1:]):
        if a[0] <= fraction <= b[0]:
            u = (fraction - a[0]) / (b[0] - a[0])
            return a[column] + (b[column] - a[column]) * u * u * (3 - 2 * u)


def profile(width, thickness, taper, roll, rib=None, count=40):
    # Outer end a semicircle as thick as the arm; the inner end narrows with taper to a point.
    # A rib, (width, height), runs along the middle of the top.
    if width < thickness:
        width, thickness, roll = thickness, width, roll + 90.0
    outer = thickness / 2
    inner = max(1e-3, outer * (1 - taper))
    half = count // 2
    points = [
        (width / 2 - outer + outer * math.cos(a), outer * math.sin(a))
        for a in (-math.pi / 2 + math.pi * j / half for j in range(half + 1))
    ]
    if rib:
        ends = (width / 2 - outer, outer), (-width / 2 + inner, inner)

        def top(u):
            return ends[0][1] + (ends[1][1] - ends[0][1]) * (u - ends[0][0]) / (
                ends[1][0] - ends[0][0]
            )

        half_width, height = rib[0] / 2, rib[1]
        points += [
            (half_width, top(half_width)),
            (half_width / 2, top(half_width / 2) + height),
            (-half_width / 2, top(-half_width / 2) + height),
            (-half_width, top(-half_width)),
        ]
    points += [
        (-width / 2 + inner + inner * math.cos(a), inner * math.sin(a))
        for a in (math.pi / 2 + math.pi * j / half for j in range(half + 1))
    ]
    c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    return [(u * c - v * s, u * s + v * c) for u, v in points]


def angular(outline, count):
    # Resample a closed outline at equal angles around its centre, so rings of different shapes
    # line up point for point.
    cu = sum(p[0] for p in outline) / len(outline)
    cv = sum(p[1] for p in outline) / len(outline)
    edges = list(zip(outline, outline[1:] + outline[:1]))
    out = []
    for k in range(count):
        a = 2 * math.pi * k / count
        dx, dy = math.cos(a), math.sin(a)
        reach = 0.0
        for (x1, y1), (x2, y2) in edges:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            s = ((x1 - cu) * ey - (y1 - cv) * ex) / den
            u = ((x1 - cu) * dy - (y1 - cv) * dx) / den
            if 0.0 < s and 0.0 <= u <= 1.0:
                reach = max(reach, s)
        out.append((cu + dx * reach, cv + dy * reach))
    return out


def sweep(arm):
    path = resample(catmull([Vector(p) for p in arm["control"]], 12), arm["samples"])
    # The pointed tip ends where the path ends, so the ship keeps its length.
    remaining = 0.0
    while 2 < len(path) and remaining < arm["tip_cap"]:
        remaining += (path[-1] - path[-2]).length
        path.pop()
    rings = []
    for i, point in enumerate(path):
        tangent, width, up = frame(path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)])
        fraction = i / (arm["samples"] - 1)
        outline = profile(
            *(station_value(arm["stations"], fraction, c) for c in range(1, 5)), arm.get("rib")
        )
        rings.append((fraction, point, tangent, width, up, angular(outline, RING_POINTS)))
    _, point, tangent, width, up, outline = rings[-1]
    for j in range(1, TIP_CAP_RINGS):
        # A pointed tip: the section shrinks linearly to the point.
        scale = 1.0 - j / TIP_CAP_RINGS
        rings.append(
            (
                1.0,
                point + tangent * arm["tip_cap"] * j / TIP_CAP_RINGS,
                tangent,
                width,
                up,
                [(u * scale, v * scale) for u, v in outline],
            )
        )
    rings.append((1.0, point + tangent * arm["tip_cap"], tangent, width, up, None))
    return rings


def section(tree, point, width, up):
    hits = []
    for k in range(TRACE_RAYS):
        a = 2 * math.pi * k / TRACE_RAYS
        hit, _, _, _ = tree.ray_cast(point, width * math.cos(a) + up * math.sin(a), TRACE_REACH)
        hits.append(None if hit is None else ((hit - point).dot(width), (hit - point).dot(up)))
    return hits


def recentre(tree, point, tangent):
    _, width, up = frame(tangent)
    hits = section(tree, point, width, up)
    found = [h for h in hits if h is not None]
    if len(found) < 0.9 * TRACE_RAYS:
        return None
    u = 0.5 * (max(h[0] for h in found) + min(h[0] for h in found))
    v = 0.5 * (max(h[1] for h in found) + min(h[1] for h in found))
    return point + width * u + up * v


def trace(tree, arm):
    # Walk the existing arm from a seed inside it, both ways, recentring in each section.
    def walk(point, tangent, limit):
        line = []
        for _ in range(limit):
            for _ in range(3):
                centre = recentre(tree, point, tangent)
                if centre is None:
                    return line
                point = centre
            line.append(point.copy())
            ahead = recentre(tree, point + tangent.normalized() * TRACE_STEP, tangent)
            if ahead is None:
                return line
            tangent = ahead - point
            point = ahead
        return line

    seed, toward = Vector(arm["seed"]), Vector(arm["toward_tip"])
    fore = walk(seed, toward, 80)
    aft = walk(seed, -toward, 200)
    line = list(reversed(aft)) + fore[1:]
    stations = []
    for i, point in enumerate(line):
        tangent, width, up = frame(line[min(i + 1, len(line) - 1)] - line[max(i - 1, 0)])
        stations.append(
            (point, tangent, width, up, [h for h in section(tree, point, width, up) if h])
        )
    return stations


def inside_arm(stations, centre, margin):
    point, tangent, width, up, hits = min(stations, key=lambda s: (centre - s[0]).length)
    if abs((centre - point).dot(tangent)) > TRACE_STEP:
        return False
    u, v = (centre - point).dot(width), (centre - point).dot(up)
    cu = sum(h[0] for h in hits) / len(hits)
    cv = sum(h[1] for h in hits) / len(hits)
    ru = max(abs(h[0] - cu) for h in hits) + margin
    rv = max(abs(h[1] - cv) for h in hits) + margin
    return ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 <= 1.0


def remove_old_arm(bm, stations, cut, tangent):
    doomed = [
        f
        for f in bm.faces
        if 0 < (f.calc_center_median() - cut).dot(tangent)
        and inside_arm(stations, f.calc_center_median(), CUT_MARGIN)
    ]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    # Fins and plates that stood on the old arm would float; drop small islands around it.
    seen = set()
    for face in list(bm.faces):
        if face in seen or not face.is_valid:
            continue
        island, stack = [], [face]
        seen.add(face)
        while stack:
            current = stack.pop()
            island.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        if len(island) < ISLAND_FACES and all(
            0 < (f.calc_center_median() - cut).dot(tangent)
            and inside_arm(stations, f.calc_center_median(), ISLAND_MARGIN)
            for f in island
        ):
            bmesh.ops.delete(bm, geom=island, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    return len(doomed)


def ring_points(ring):
    _, point, _, width, up, outline = ring
    if outline is None:
        return [point]
    return [point + width * u + up * v for u, v in outline]


def signed_distance(points, polygon):
    # Negative inside.
    a = polygon
    b = numpy.roll(polygon, -1, axis=0)
    edge = b - a
    rel = points[:, None, :] - a[None]
    t = numpy.clip((rel * edge).sum(2) / numpy.maximum((edge * edge).sum(1), 1e-9), 0.0, 1.0)
    gap = rel - t[..., None] * edge
    distance = numpy.sqrt((gap * gap).sum(2)).min(1)
    y = points[:, 1, None]
    crossing = ((a[None, :, 1] > y) != (b[None, :, 1] > y)) & (
        points[:, 0, None]
        < (b[None, :, 0] - a[None, :, 0])
        * (y - a[None, :, 1])
        / numpy.where(b[:, 1] - a[:, 1] == 0, 1e-9, b[:, 1] - a[:, 1])[None]
        + a[None, :, 0]
    )
    return numpy.where(crossing.sum(1) % 2 == 1, -distance, distance)


def smooth_union(points, first, second, blend):
    d1, d2 = signed_distance(points, first), signed_distance(points, second)
    h = numpy.clip(0.5 + 0.5 * (d2 - d1) / blend, 0.0, 1.0)
    return d2 * (1.0 - h) + d1 * h - blend * h * (1.0 - h)


def build_pod(bm, arc, lower):
    stations = []
    for ring in arc:
        mate = min(lower, key=lambda r: (r[1] - ring[1]).length)
        centre = (ring[1] + mate[1]) * 0.5
        if ring[5] is None:
            # The farther tip, so neither arm's point pokes out of the pod.
            stations.append((max(ring[1], lower[-1][1], key=lambda p: p.y), None))
            break
        _, width, up = frame(ring[2] + mate[2])

        def flat(r):
            return numpy.array(
                [((p - centre).dot(width), (p - centre).dot(up)) for p in ring_points(r)]
            )

        first, second = flat(ring), flat(mate)
        if len(second) < 3:
            second = first
        thinnest = min(min(numpy.ptp(q[:, 0]), numpy.ptp(q[:, 1])) for q in (first, second))
        blend = max(0.5, POD_BLEND * 0.5 * thinnest)
        middle = (first.mean(0) + second.mean(0)) * 0.5
        bridge = middle[None] + numpy.linspace(-0.4, 0.4, 9)[:, None] * (
            second.mean(0) - first.mean(0)
        )
        if not stations and 0.0 < smooth_union(bridge, first, second, blend).max():
            continue
        stations.append((centre, (width, up, first, second, blend, middle)))
    start, tip = stations[0][0], stations[-1][0]
    rows = []
    angles = numpy.linspace(0.0, 2 * math.pi, RING_POINTS, endpoint=False)
    rays = numpy.stack((numpy.cos(angles), numpy.sin(angles)), 1)
    for centre, data in stations:
        if data is None:
            rows.append([centre])
            continue
        width, up, first, second, blend, middle = data
        q = (centre - start).length / max(1e-6, (tip - start).length)
        rise = min(1.0, q / POD_EMERGE)
        rise = rise * rise * (3 - 2 * rise)
        offset = -POD_SINK + (POD_SINK + POD_LIFT) * rise + POD_BULGE * math.sin(math.pi * q)
        reach = numpy.abs(numpy.vstack((first, second)) - middle).max() * 1.6 + offset + blend
        steps = numpy.arange(0.0, reach, POD_MARCH)
        grid = middle[None, None] + rays[:, None] * steps[None, :, None]
        field = smooth_union(grid.reshape(-1, 2), first, second, blend).reshape(len(angles), -1)
        row = []
        for k in range(RING_POINTS):
            outside = numpy.nonzero(field[k] > offset)[0]
            j = outside[0] if len(outside) else len(steps) - 1
            lo, hi = steps[max(j - 1, 0)], steps[j]
            for _ in range(8):
                mid = 0.5 * (lo + hi)
                value = smooth_union((middle + rays[k] * mid)[None], first, second, blend)[0]
                lo, hi = (mid, hi) if value <= offset else (lo, mid)
            u, v = middle + rays[k] * hi
            row.append(centre + width * u + up * v)
        rows.append(row)
    verts = [[bm.verts.new(p) for p in row] for row in rows]
    made = []
    for a, b in zip(verts, verts[1:]):
        if len(b) == 1:
            made += [
                bm.faces.new((a[k], a[(k + 1) % RING_POINTS], b[0])) for k in range(RING_POINTS)
            ]
            continue
        for k in range(RING_POINTS):
            made.append(
                bm.faces.new((a[k], a[(k + 1) % RING_POINTS], b[(k + 1) % RING_POINTS], b[k]))
            )
    middle = len(verts) // 2
    centre = sum((v.co for v in verts[middle]), Vector()) / len(verts[middle])
    probe = made[middle * RING_POINTS]
    probe.normal_update()
    if probe.normal.dot(probe.calc_center_median() - centre) < 0:
        for face in made:
            face.normal_flip()
    return made


def rebuild_arms(mesh_object):
    bm = bmesh.new()
    bm.from_mesh(mesh_object.data)
    original = BVHTree.FromBMesh(bm)
    traces = {arm["name"]: trace(original, arm) for arm in ARMS}
    tip = traces["arc"][-1][0]
    clear = [
        f
        for f in bm.faces
        if TIP_CLEAR_MIN_X < f.calc_center_median().x
        and (f.calc_center_median() - tip).length < TIP_CLEAR
    ]
    bmesh.ops.delete(bm, geom=clear, context="FACES")
    report = {"tip": len(clear)}
    fresh = set()
    joins = []
    for arm in ARMS:
        stations = traces[arm["name"]]
        lengths = [0.0]
        for a, b in zip(stations, stations[1:]):
            lengths.append(lengths[-1] + (b[0] - a[0]).length)
        icut = min(range(len(lengths)), key=lambda j: abs(lengths[j] - arm["cut"] * lengths[-1]))
        cut, _, width, up, _ = stations[icut]
        tangent = (stations[icut + 1][0] - cut).normalized()
        outline = [h for h in section(original, cut, width, up) if h]
        start = [cut + width * u + up * v for u, v in angular(outline, RING_POINTS)]
        reach = 1.3 * max(math.hypot(u, v) for u, v in outline)
        near = [f for f in bm.faces if any((v.co - cut).length < reach for v in f.verts)]
        geom = list({e for f in near for e in f.edges}) + list({v for f in near for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom + near, dist=0.01, plane_co=cut, plane_no=tangent)
        report[arm["name"]] = remove_old_arm(bm, stations[icut:], cut, tangent)
        joins.append((arm, start, (lengths[icut] + arm["blend"]) / lengths[-1]))
    # Every old arm goes before any new one is built, so no removal can cut into a new arm.
    for arm, start, begin in joins:
        rings = [r for r in sweep(arm) if r[0] >= begin]
        rows = []
        for j in range(arm["blend_rings"] + 1):
            s = j / arm["blend_rings"]
            s = s * s * (3 - 2 * s)
            _, point, _, w, h, outline = rings[0]
            rows.append([a.lerp(point + w * u + h * v, s) for a, (u, v) in zip(start, outline)])
        rows += [
            [point + w * u + h * v for u, v in outline]
            for _, point, _, w, h, outline in rings[1:-1]
        ]
        verts = [[bm.verts.new(p) for p in row] for row in rows]
        made = []
        for a, b in zip(verts, verts[1:]):
            for k in range(RING_POINTS):
                made.append(
                    bm.faces.new((a[k], a[(k + 1) % RING_POINTS], b[(k + 1) % RING_POINTS], b[k]))
                )
        point = bm.verts.new(rings[-1][1])
        for k in range(RING_POINTS):
            made.append(bm.faces.new((verts[-1][k], verts[-1][(k + 1) % RING_POINTS], point)))
        middle = len(verts) // 2
        centre = sum((v.co for v in verts[middle]), Vector()) / RING_POINTS
        probe = made[middle * RING_POINTS]
        probe.normal_update()
        if probe.normal.dot(probe.calc_center_median() - centre) < 0:
            for face in made:
                face.normal_flip()
        fresh.update(e for f in made for e in f.edges)
    pod = build_pod(bm, *(sweep(arm) for arm in ARMS))
    report["pod"] = len(pod)
    fresh.update(e for f in pod for e in f.edges)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if 4 < len(f.verts)])
    bmesh.ops.dissolve_degenerate(bm, dist=0.01, edges=[e for e in fresh if e.is_valid])
    bmesh.ops.delete(
        bm,
        geom=[f for f in bm.faces if f.calc_area() < 1e-4 and any(e in fresh for e in f.edges)],
        context="FACES",
    )
    bm.normal_update()
    bm.to_mesh(mesh_object.data)
    bm.free()
    mesh_object.data.update()
    return report
