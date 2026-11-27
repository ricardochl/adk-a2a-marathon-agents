"""Try the route tool for one city, without calling any model.

Usage:
    uv run python scripts/try_route.py "San Pedro Sula"
    uv run python scripts/try_route.py "Tegucigalpa, Honduras" --theme fast

Prints how the city was resolved and the route numbers, and saves the
route as route.geojson (you can open it at https://geojson.io).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "src/planner_agent/skills/route-planning/tools.py"


def load_route_tools():
    spec = importlib.util.spec_from_file_location("route_planning_tools", TOOLS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Try plan_marathon_route for one city")
    parser.add_argument("city", help='City name, e.g. "San Pedro Sula"')
    parser.add_argument("--theme", default="scenic", choices=["scenic", "fast"])
    parser.add_argument("--out", default="route.geojson", help="Where to save the GeoJSON")
    args = parser.parse_args()

    tools = load_route_tools()
    matched, center = tools.resolve_city(args.city)
    route = tools.plan_marathon_route(args.city, theme=args.theme)

    if matched:
        print(f"✔ '{args.city}' → known city '{matched}' at {center}")
    else:
        print(f"! '{args.city}' is not in CITY_CENTERS: the route uses a placeholder center.")
        print("  Add it to CITY_CENTERS in src/planner_agent/skills/route-planning/tools.py")
    print(f"  Distance: {route['distance_km']} km ({route['distance_miles']} mi)")
    print(f"  Water stations: {route['water_stations']} · Medical tents: {route['medical_tents']}")

    pathlib.Path(args.out).write_text(json.dumps(route["geojson"], indent=2))
    print(f"  GeoJSON saved to {args.out}")
    return 0 if matched else 1


if __name__ == "__main__":
    sys.exit(main())
