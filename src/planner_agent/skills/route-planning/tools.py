"""Route-planning tools for the `route-planning` ADK Skill.

NOT IN THE CODELAB
------------------
The codelab loads `plan_marathon_route` from this file but never provides its
code. This is a self-contained reference implementation with no external APIs,
so the Planner has a real tool to call:

1. Build a synthetic road network (a street grid every ~0.5 km) centered on
   the city.
2. Place waypoints on a loop around the center.
3. Join consecutive waypoints with the shortest path (Dijkstra's algorithm).
4. Adjust the distance with an out-and-back segment to hit exactly 42.195 km.
5. Return a GeoJSON FeatureCollection (route + start/finish + landmarks +
   water stations + medical tents).

It is intentionally simple: a good extra exercise is replacing the synthetic
network with real data (OpenStreetMap, Google Maps Routes API, etc.).
"""

from __future__ import annotations

import heapq
import math
import re
import unicodedata
from typing import Any

MARATHON_KM = 42.195
KM_PER_MILE = 1.609344

# Approximate city centers (lat, lng), keyed by normalized name (lowercase, no
# accents). Any other city uses DEFAULT_CENTER unless explicit coordinates are
# passed, and the result says so in "location_source".
CITY_CENTERS: dict[str, tuple[float, float]] = {
    "las vegas": (36.1147, -115.1728),
    "austin": (30.2672, -97.7431),
    "new york": (40.7128, -74.0060),
    "chicago": (41.8781, -87.6298),
    "madrid": (40.4168, -3.7038),
    "barcelona": (41.3874, 2.1686),
    "mexico city": (19.4326, -99.1332),
    "ciudad de mexico": (19.4326, -99.1332),
    "tegucigalpa": (14.0723, -87.1921),
    "san pedro sula": (15.5050, -88.0250),
    "san salvador": (13.6929, -89.2182),
    "la ceiba": (15.78, -86.79),  # Exercise 4
    "bogota": (4.7110, -74.0721),
    "buenos aires": (-34.6037, -58.3816),
    "lima": (-12.0464, -77.0428),
    "santiago": (-33.4489, -70.6693),
}
CITY_ALIASES: dict[str, str] = {
    "sps": "san pedro sula",
    "tegus": "tegucigalpa",
    "cdmx": "ciudad de mexico",
    "nyc": "new york",
    "new york city": "new york",
}
DEFAULT_CITY = "san pedro sula"
DEFAULT_CENTER = CITY_CENTERS[DEFAULT_CITY]


def _normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation: 'Bogotá, D.C.' -> 'bogota d c'."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def resolve_city(city: str) -> tuple[str | None, tuple[float, float]]:
    """Find a known city inside free text the model may produce.

    Accepts "San Pedro Sula", "san pedro sula, Honduras", "SPS", "Bogotá"...
    Returns (matched_city or None, center).
    """
    norm = _normalize(city or "")
    if norm in CITY_ALIASES:
        norm = CITY_ALIASES[norm]
    if norm in CITY_CENTERS:
        return norm, CITY_CENTERS[norm]
    padded = f" {norm} "
    # Longest name first, so "san pedro sula" wins over any shorter match.
    for name in sorted([*CITY_CENTERS, *CITY_ALIASES], key=len, reverse=True):
        if f" {name} " in padded:
            name = CITY_ALIASES.get(name, name)
            return name, CITY_CENTERS[name]
    return None, DEFAULT_CENTER

GRID_STEP_KM = 0.5
GRID_HALF_SIZE = 16  # 33x33 nodes → ~16 km x 16 km


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def _offset(center: tuple[float, float], dx_km: float, dy_km: float) -> tuple[float, float]:
    lat, lng = center
    dlat = dy_km / 110.574
    dlng = dx_km / (111.320 * math.cos(math.radians(lat)))
    return (lat + dlat, lng + dlng)


# ---------------------------------------------------------------------------
# Synthetic road network + Dijkstra
# ---------------------------------------------------------------------------

Node = tuple[int, int]


def _build_grid(center: tuple[float, float]) -> tuple[dict[Node, tuple[float, float]], dict[Node, list[tuple[Node, float]]]]:
    coords: dict[Node, tuple[float, float]] = {}
    for i in range(-GRID_HALF_SIZE, GRID_HALF_SIZE + 1):
        for j in range(-GRID_HALF_SIZE, GRID_HALF_SIZE + 1):
            coords[(i, j)] = _offset(center, i * GRID_STEP_KM, j * GRID_STEP_KM)

    graph: dict[Node, list[tuple[Node, float]]] = {n: [] for n in coords}
    for (i, j) in coords:
        for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):  # calles + diagonales (avenidas)
            nb = (i + di, j + dj)
            if nb in coords:
                w = _haversine_km(coords[(i, j)], coords[nb])
                graph[(i, j)].append((nb, w))
                graph[nb].append(((i, j), w))
    return coords, graph


def _dijkstra(graph: dict[Node, list[tuple[Node, float]]], src: Node, dst: Node) -> tuple[list[Node], float]:
    dist: dict[Node, float] = {src: 0.0}
    prev: dict[Node, Node] = {}
    pq: list[tuple[float, Node]] = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if d > dist.get(u, math.inf):
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return path[::-1], dist[dst]


def _nearest_node(coords: dict[Node, tuple[float, float]], dx_km: float, dy_km: float) -> Node:
    i = max(-GRID_HALF_SIZE, min(GRID_HALF_SIZE, round(dx_km / GRID_STEP_KM)))
    j = max(-GRID_HALF_SIZE, min(GRID_HALF_SIZE, round(dy_km / GRID_STEP_KM)))
    return (i, j)


def _points_along(line: list[tuple[float, float]], every_km: float) -> list[tuple[float, tuple[float, float]]]:
    """Return (km, (lat, lng)) every `every_km` along a polyline."""
    out, acc, target = [], 0.0, every_km
    for a, b in zip(line, line[1:]):
        seg = _haversine_km(a, b)
        while seg > 0 and acc + seg >= target:
            t = (target - acc) / seg
            out.append((round(target, 3), (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)))
            target += every_km
        acc += seg
    return out


def _point_feature(latlng: tuple[float, float], **props: Any) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(latlng[1], 6), round(latlng[0], 6)]},
        "properties": props,
    }


# ---------------------------------------------------------------------------
# Public tools (the ones the agent sees)
# ---------------------------------------------------------------------------

def plan_marathon_route(
    city: str,
    landmarks: list[str] | None = None,
    theme: str = "scenic",
    start_lat: float | None = None,
    start_lng: float | None = None,
    water_interval_km: float = 5.0,
) -> dict[str, Any]:
    """Generate a certified 42.195 km (26.2 mi) marathon loop as GeoJSON.

    Args:
        city: City where the marathon takes place (e.g. "San Pedro Sula").
        landmarks: Ordered landmark names the route should pass (optional).
        theme: "scenic" (wider loop past landmarks) or "fast" (compact, flatter loop).
        start_lat: Optional latitude of the start/finish line.
        start_lng: Optional longitude of the start/finish line.
        water_interval_km: Distance between water stations. 5 km is the usual
            standard; use 2.5 km for hot or tropical cities.

    Returns:
        dict with distance_km, distance_miles, waypoints, summary,
        water_station_km and medical_tent_km (the km mark of each station),
        location_source ("coordinates", "known_city" or "default_center") and
        a GeoJSON FeatureCollection under "geojson".
    """
    landmarks = [l for l in (landmarks or []) if l and l.strip()]
    if start_lat is not None and start_lng is not None:
        center = (float(start_lat), float(start_lng))
        location_source = "coordinates"
    else:
        matched, center = resolve_city(city)
        location_source = "known_city" if matched else "default_center"

    coords, graph = _build_grid(center)

    # Waypoints on a loop. "fast" → round and compact; "scenic" → detours
    # towards the landmarks (more turns, more views).
    n_wp = max(6, min(12, len(landmarks) or 8))
    scenic = theme.lower() != "fast"
    start_node = (0, 0)

    def build_loop(radius_km: float) -> tuple[list[Node], list[Node], float]:
        wps: list[Node] = []
        for k in range(n_wp):
            ang = 2 * math.pi * k / n_wp
            wobble = 1.25 if (scenic and k % 2) else 1.0
            wps.append(_nearest_node(coords, radius_km * wobble * math.cos(ang),
                                     radius_km * wobble * math.sin(ang)))
        stops = [start_node, *wps, start_node]
        path, total = [start_node], 0.0
        for a, b in zip(stops, stops[1:]):
            seg, d = _dijkstra(graph, a, b)
            path.extend(seg[1:])
            total += d
        return wps, path, total

    # Pick the largest loop that fits in 42.195 km (leaving ≥1 km for the
    # out-and-back segment that fixes the exact distance).
    radius_km = 7.0
    wp_nodes, path, loop_km = build_loop(radius_km)
    while loop_km > MARATHON_KM - 1.0 and radius_km > 1.0:
        radius_km -= 0.25
        wp_nodes, path, loop_km = build_loop(radius_km)

    line = [coords[n] for n in path]

    # Adjustment: out-and-back segment from the start to land on 42.195 km.
    spur_km = (MARATHON_KM - loop_km) / 2
    if spur_km > 0:
        probe = _haversine_km(center, _offset(center, 0.0, -spur_km))
        spur_end = _offset(center, 0.0, -spur_km * spur_km / probe)
        line = [center, spur_end, center, *line[1:]]
    total_km = sum(_haversine_km(a, b) for a, b in zip(line, line[1:]))

    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[round(p[1], 6), round(p[0], 6)] for p in line]},
            "properties": {
                "name": f"{city} Marathon route",
                "distance_km": round(total_km, 3),
                "distance_miles": round(total_km / KM_PER_MILE, 2),
                "theme": theme,
            },
        },
        _point_feature(center, kind="start_finish", name="Start / Finish line"),
    ]

    waypoint_names: list[str] = []
    for idx, node in enumerate(wp_nodes):
        name = landmarks[idx] if idx < len(landmarks) else f"Waypoint {idx + 1}"
        waypoint_names.append(name)
        features.append(_point_feature(coords[node], kind="landmark", name=name, order=idx + 1))

    water = add_water_stations(line_coordinates=[[p[1], p[0]] for p in line],
                               interval_km=water_interval_km)
    medical = add_medical_tents(line_coordinates=[[p[1], p[0]] for p in line])
    features.extend(water["features"])
    features.extend(medical["features"])

    summary = (
        f"Certified {MARATHON_KM} km (26.2 mile) loop in {city} starting and finishing at the "
        f"city center, passing {len(waypoint_names)} waypoints, with "
        f"{len(water['features'])} water stations and {len(medical['features'])} medical tents."
    )
    if location_source == "default_center":
        # Never pretend: say the geometry is a placeholder for this city.
        summary = (
            f"WARNING: '{city}' is not in the built-in city list, so the GeoJSON is drawn "
            f"around a placeholder center (San Pedro Sula). Tell the user, or call again "
            f"with start_lat/start_lng. " + summary
        )

    return {
        "city": city,
        "location_source": location_source,
        "theme": theme,
        "distance_km": round(total_km, 3),
        "distance_miles": round(total_km / KM_PER_MILE, 2),
        "waypoints": ["Start line", *waypoint_names, "Finish line"],
        "water_stations": len(water["features"]),
        "medical_tents": len(medical["features"]),
        # Listed so the Planner can copy them into the plan: the Evaluator and
        # the Simulator only read the plan text, never this GeoJSON.
        "water_station_km": [f["properties"]["km"] for f in water["features"]],
        "medical_tent_km": [f["properties"]["km"] for f in medical["features"]],
        "summary": summary,
        "geojson": {"type": "FeatureCollection", "features": features},
    }


def add_water_stations(line_coordinates: list[list[float]], interval_km: float = 5.0) -> dict[str, Any]:
    """Place water stations every `interval_km` along a route.

    Args:
        line_coordinates: Route as a list of [lng, lat] pairs (GeoJSON order).
        interval_km: Distance between stations (IAAF guidance: ~5 km).

    Returns:
        GeoJSON FeatureCollection of water-station points.
    """
    line = [(c[1], c[0]) for c in line_coordinates]
    pts = _points_along(line, interval_km)
    return {
        "type": "FeatureCollection",
        "features": [
            _point_feature(p, kind="water_station", name=f"Water station km {km:g}", km=km)
            for km, p in pts if km < MARATHON_KM - 0.5
        ],
    }


def add_medical_tents(line_coordinates: list[list[float]], interval_km: float = 8.0) -> dict[str, Any]:
    """Place medical tents every `interval_km` plus one at the finish.

    Args:
        line_coordinates: Route as a list of [lng, lat] pairs (GeoJSON order).
        interval_km: Distance between medical tents.

    Returns:
        GeoJSON FeatureCollection of medical-tent points.
    """
    line = [(c[1], c[0]) for c in line_coordinates]
    pts = _points_along(line, interval_km)
    feats = [_point_feature(p, kind="medical_tent", name=f"Medical tent km {km:g}", km=km)
             for km, p in pts if km < MARATHON_KM - 0.5]
    feats.append(_point_feature(line[-1], kind="medical_tent", name="Medical tent at finish", km=MARATHON_KM))
    return {"type": "FeatureCollection", "features": feats}
