"""
CDO BRUTE FORCE ROUTE OPTIMIZER — PIT FINAL

This file is intentionally kept as one readable Python program for the
screen-recorded Performance Innovative Task.

STANDARD MODE
-------------
Uses the same seven locations as the PowerPoint. It creates a weighted,
complete, undirected graph whose edge weights are Haversine distances in km.
It evaluates all 6! = 720 routes, verifies the closed tour, and recalculates
the final total from the edge weights.

INTERACTIVE MODE
----------------
Lets the user choose a start and destinations from a citywide CDO catalog (or
enter a custom point). Nominatim resolves coordinates and OSRM supplies road
weights. Brute Force still performs the TSP optimization.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    requests = None

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# =============================================================================
# 1) PATHS AND CONSTANTS
# =============================================================================
BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUTPUT = BASE / "output"
CACHE = BASE / "cache"

STANDARD_DATA = DATA / "standard_assignment_locations.csv"
MASTER_CATALOG = DATA / "cdo_master_catalog.csv"
GEOCODE_CACHE = CACHE / "geocode_cache.json"

EARTH_RADIUS_KM = 6371.0088
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "CDO-Brute-Force-PIT/educational-project"

OUTPUT.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)


# =============================================================================
# 2) SMALL FILE HELPERS
# =============================================================================
def load_csv(path: Path) -> list[dict]:
    """Read a CSV file into a list of dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_dict_csv(path: Path, rows: list[dict]) -> None:
    """Write dictionaries to CSV using keys from the first row."""
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# =============================================================================
# 3) GRAPH EDGE WEIGHTS
# =============================================================================
def haversine(a: dict, b: dict) -> float:
    """Straight-line geographic distance in kilometres."""
    lat1 = math.radians(float(a["latitude"]))
    lon1 = math.radians(float(a["longitude"]))
    lat2 = math.radians(float(b["latitude"]))
    lon2 = math.radians(float(b["longitude"]))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def build_haversine_matrix(points: list[dict]) -> list[list[float]]:
    """Build the symmetric matrix for the standard UNDIRECTED graph."""
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(points[i], points[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def route_total(route: tuple[int, ...], matrix: list[list[float]]) -> float:
    """Add the weights of every edge in one complete route."""
    return sum(matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))


# =============================================================================
# 4) BRUTE FORCE TSP — THE ASSIGNED ALGORITHM
# =============================================================================
def brute_force_tsp(points, distance_matrix, duration_matrix=None):
    """
    Fix vertex 0 as the start, generate EVERY permutation of the remaining
    vertices, return to the start, calculate each total, then rank all routes.

    Because every possible order is tested, the first ranked route is proven
    optimal for the exact weight matrix supplied to this function.
    """
    destinations = tuple(range(1, len(points)))
    results = []
    started = time.perf_counter()

    for route_number, permutation in enumerate(itertools.permutations(destinations), start=1):
        route = (0,) + permutation + (0,)
        distance = route_total(route, distance_matrix)
        duration = None if duration_matrix is None else route_total(route, duration_matrix)
        results.append({
            "original_route_number": route_number,
            "route_indices": route,
            "distance_km": distance,
            "duration_seconds": duration,
        })

    results.sort(key=lambda row: row["distance_km"])
    for rank, row in enumerate(results, start=1):
        row["rank"] = rank

    return results, time.perf_counter() - started


# =============================================================================
# 5) VALIDATION — REQUIRED BY THE PIT INSTRUCTIONS
# =============================================================================
def verify_route(route, n_locations, matrix, algorithm_total):
    """Check the closed tour and independently recalculate the total."""
    closed = route[0] == route[-1]
    visit_sequence = route[:-1]  # ignore repeated start at the end
    all_present = set(visit_sequence) == set(range(n_locations))
    exactly_once = len(visit_sequence) == len(set(visit_sequence))
    recalculated = route_total(route, matrix)
    totals_match = math.isclose(algorithm_total, recalculated, abs_tol=1e-12)

    return {
        "closed_tour": closed,
        "all_locations_present": all_present,
        "each_location_visited_once": exactly_once,
        "algorithm_total_km": algorithm_total,
        "recalculated_total_km": recalculated,
        "totals_match": totals_match,
        "valid_tsp_tour": closed and all_present and exactly_once and totals_match,
    }


def edge_calculation(route, points, matrix):
    """Create the leg-by-leg calculation used to verify the final total."""
    rows = []
    cumulative = 0.0
    for leg in range(1, len(route)):
        i, j = route[leg - 1], route[leg]
        weight = matrix[i][j]
        cumulative += weight
        rows.append({
            "leg": leg,
            "from_vertex": points[i]["vertex"],
            "from_location": points[i]["name"],
            "to_vertex": points[j]["vertex"],
            "to_location": points[j]["name"],
            "edge_weight_km": round(weight, 6),
            "cumulative_km": round(cumulative, 6),
        })
    return rows


# =============================================================================
# 6) OUTPUT HELPERS
# =============================================================================
def route_names(route, points):
    return [points[i]["name"] for i in route]


def route_labels(route, points):
    return [points[i]["vertex"] for i in route]


def save_matrix(path, points, matrix, decimals=4):
    """Save the graph weight matrix required by the PIT."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        labels = [f'{p["vertex"]} - {p["name"]}' for p in points]
        writer.writerow(["FROM / TO"] + labels)
        for i, p in enumerate(points):
            writer.writerow([labels[i]] + [f"{matrix[i][j]:.{decimals}f}" for j in range(len(points))])


def save_ranked_routes(folder, results, points):
    """Save every candidate route as evidence of exhaustive search."""
    rows = []
    for result in results:
        row = {
            "rank": result["rank"],
            "original_route_number": result["original_route_number"],
            "distance_km": round(result["distance_km"], 6),
            "route": " -> ".join(route_names(result["route_indices"], points)),
        }
        if result["duration_seconds"] is not None:
            row["estimated_duration_minutes"] = round(result["duration_seconds"] / 60, 3)
        rows.append(row)

    write_dict_csv(folder / "all_routes_ranked.csv", rows)
    (folder / "all_routes_ranked.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (folder / "top_10_routes.txt").open("w", encoding="utf-8") as f:
        for row in rows[:10]:
            f.write(f'Rank {row["rank"]}: {row["distance_km"]:.3f} km\n')
            f.write(row["route"] + "\n\n")


def google_maps_route_url(route, points):
    """Google Maps Directions link for visual verification in the presentation."""
    names = route_names(route, points)
    origin = quote_plus(f"{names[0]}, Cagayan de Oro City, Philippines")
    destination = quote_plus(f"{names[-1]}, Cagayan de Oro City, Philippines")
    waypoints = "|".join(quote_plus(f"{n}, Cagayan de Oro City, Philippines") for n in names[1:-1])
    return ("https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}&destination={destination}"
            f"&waypoints={waypoints}&travelmode=driving")


def plot_weighted_graph(path, points, matrix):
    """Create the labeled complete weighted graph required by the PIT."""
    if plt is None:
        return
    n = len(points)
    pos = {}
    for i in range(n):
        angle = math.pi / 2 + 2 * math.pi * i / n
        pos[i] = (math.cos(angle), math.sin(angle))

    fig, ax = plt.subplots(figsize=(12, 9))
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = pos[i]; x2, y2 = pos[j]
            ax.plot([x1, x2], [y1, y2], linewidth=0.8, alpha=0.25)
            ax.text((x1+x2)/2, (y1+y2)/2, f"{matrix[i][j]:.2f}",
                    fontsize=6, ha="center", va="center", alpha=0.75)

    for i, p in enumerate(points):
        x, y = pos[i]
        ax.scatter([x], [y], s=900, zorder=3)
        ax.text(x, y, p["vertex"], ha="center", va="center", fontweight="bold", zorder=4)
        ax.text(x, y-0.13, p["name"], ha="center", va="top", fontsize=8)

    ax.set_title("Weighted Graph Model — Complete Undirected Graph\nEdge weights in kilometres")
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_route(path, points, route, title, geometry=None):
    """Plot the resulting optimal route."""
    if plt is None:
        return
    fig, ax = plt.subplots(figsize=(11, 8))
    if geometry:
        ax.plot([p[0] for p in geometry], [p[1] for p in geometry], linewidth=2)
    else:
        ordered = [points[i] for i in route]
        ax.plot([p["longitude"] for p in ordered], [p["latitude"] for p in ordered], marker="o", linewidth=2)

    for p in points:
        ax.scatter([p["longitude"]], [p["latitude"]], s=60)
        ax.annotate(f'{p.get("vertex", "")} {p["name"]}'.strip(),
                    (p["longitude"], p["latitude"]), xytext=(5,5), textcoords="offset points", fontsize=8)
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


# =============================================================================
# 7) STANDARD ASSIGNMENT MODE — USE THIS IN THE RECORDED VIDEO
# =============================================================================
def run_standard():
    raw = load_csv(STANDARD_DATA)
    points = []
    for row in raw:
        row = dict(row)
        row["latitude"] = float(row["latitude"])
        row["longitude"] = float(row["longitude"])
        points.append(row)

    matrix = build_haversine_matrix(points)
    expected_routes = math.factorial(len(points) - 1)

    print("\n" + "=" * 78)
    print("STANDARD ASSIGNMENT MODE — CDO TOURIST ITINERARY")
    print("=" * 78)
    print("Problem   : Start at Gaston Park, visit every required landmark once,")
    print("            then return to Gaston Park.")
    print("Objective : Minimize TOTAL GEOGRAPHIC DISTANCE in kilometres.")
    print("Graph     : Weighted, complete, UNDIRECTED")
    print("Vertices  : Required locations")
    print("Edges     : Travel connections between every pair of vertices")
    print("Weights   : Haversine geographic distance (km)")
    print(f"Routes    : (7 - 1)! = 6! = {expected_routes:,}\n")

    print("INPUT DATA")
    for p in points:
        print(f'{p["vertex"]}: {p["name"]:<28} ({p["latitude"]:.5f}, {p["longitude"]:.5f})')

    results, elapsed = brute_force_tsp(points, matrix)
    best = results[0]
    check = verify_route(best["route_indices"], len(points), matrix, best["distance_km"])
    legs = edge_calculation(best["route_indices"], points, matrix)

    folder = OUTPUT / "standard_assignment"
    folder.mkdir(parents=True, exist_ok=True)

    # Save the exact inputs, graph/matrix, every route, and verification evidence.
    write_dict_csv(folder / "input_locations_used.csv", raw)
    save_matrix(folder / "distance_matrix.csv", points, matrix)
    save_ranked_routes(folder, results, points)
    write_dict_csv(folder / "optimal_route_edge_calculation.csv", legs)
    plot_weighted_graph(folder / "weighted_graph_model.png", points, matrix)
    plot_route(folder / "optimal_route.png", points, best["route_indices"],
               f'Optimal Brute Force Route — {best["distance_km"]:.3f} km')

    # Google Maps evidence requested by the PIT instructions.
    with (folder / "google_maps_locations.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["vertex", "location", "google_maps_url"])
        for p in points:
            w.writerow([p["vertex"], p["name"], p["google_maps_url"]])

    maps_route = google_maps_route_url(best["route_indices"], points)
    (folder / "google_maps_best_route.txt").write_text(
        "GOOGLE MAPS VISUAL-VERIFICATION LINK\n" + "="*50 + "\n\n" + maps_route +
        "\n\nNote: Google Maps is used here for visual verification. "
        "The Standard Mode numeric weights are the Haversine values saved in distance_matrix.csv.\n",
        encoding="utf-8"
    )

    verification_text = (
        "ROUTE VERIFICATION\n" + "="*72 + "\n"
        f'Closed tour: {"YES" if check["closed_tour"] else "NO"}\n'
        f'All locations present: {"YES" if check["all_locations_present"] else "NO"}\n'
        f'Each location visited exactly once before return: {"YES" if check["each_location_visited_once"] else "NO"}\n'
        f'Recalculated total: {check["recalculated_total_km"]:.6f} km\n'
        f'Algorithm total: {check["algorithm_total_km"]:.6f} km\n'
        f'Totals match: {"YES" if check["totals_match"] else "NO"}\n'
        f'Valid TSP tour: {"YES" if check["valid_tsp_tour"] else "NO"}\n'
    )
    (folder / "verification_report.txt").write_text(verification_text, encoding="utf-8")

    route_text = " -> ".join(route_names(best["route_indices"], points))
    label_text = " -> ".join(route_labels(best["route_indices"], points))
    summary = (
        "CDO BRUTE FORCE ROUTE OPTIMIZER — STANDARD ASSIGNMENT RESULT\n" + "="*78 + "\n\n"
        "Application: tourist itinerary / landmark visit in Cagayan de Oro City\n"
        "Start: Gaston Park\n"
        "Objective: minimize total geographic distance\n"
        "Graph: weighted complete undirected graph\n"
        "Units: kilometres\n"
        "Data status: Standard coordinates are frozen PPT data; Google Maps links are provided for visual verification.\n\n"
        f'Routes evaluated: {len(results):,}\n'
        f'Execution time: {elapsed:.6f} seconds\n'
        f'Optimal route labels: {label_text}\n'
        f'Optimal route: {route_text}\n'
        f'Minimum total distance: {best["distance_km"]:.6f} km\n\n'
        "Optimality: PROVEN OPTIMAL for this exact weight matrix because every possible route permutation was evaluated.\n\n"
        + verification_text
    )
    (folder / "result_summary.txt").write_text(summary, encoding="utf-8")

    # Clear on-screen output for the required execution recording.
    print("\n" + "-"*78)
    print("BRUTE FORCE RESULT")
    print("-"*78)
    print(f'Routes evaluated : {len(results):,}')
    print(f'Optimal route    : {label_text}')
    print(f'Minimum distance : {best["distance_km"]:.3f} km')
    print(f'Execution time   : {elapsed:.6f} seconds')
    print("\nROUTE WITH LOCATION NAMES")
    print(route_text)

    print("\nLEG-BY-LEG RECALCULATION")
    for row in legs:
        print(f'Leg {row["leg"]}: {row["from_vertex"]} -> {row["to_vertex"]} = {row["edge_weight_km"]:.6f} km')
    print(f'Recalculated total = {check["recalculated_total_km"]:.6f} km')

    print("\nVALIDATION")
    print(f'Closed tour: {"YES" if check["closed_tour"] else "NO"}')
    print(f'Every required location exactly once: {"YES" if check["each_location_visited_once"] else "NO"}')
    print(f'Total matches edge weights: {"YES" if check["totals_match"] else "NO"}')
    print("Proven optimal for this matrix: YES")
    print(f'\nOutput folder: {folder}')


# =============================================================================
# 8) INTERACTIVE ROAD MODE — OPTIONAL EXTENSION
# =============================================================================
def load_cache():
    if not GEOCODE_CACHE.exists():
        return {}
    try:
        return json.loads(GEOCODE_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    GEOCODE_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def geocode(query):
    """Resolve a place name using OpenStreetMap/Nominatim."""
    if requests is None:
        raise RuntimeError("Install requirements first: py -m pip install -r requirements.txt")
    cache = load_cache()
    key = query.strip().lower()
    if key in cache:
        return dict(cache[key])

    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "ph",
                "viewbox": "124.45,8.70,124.90,8.20", "bounded": 1},
        headers={"User-Agent": USER_AGENT}, timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError(f"No result found for: {query}")

    point = {
        "name": query,
        "vertex": "",
        "latitude": float(data[0]["lat"]),
        "longitude": float(data[0]["lon"]),
        "display_name": data[0].get("display_name", query),
        "source": "OpenStreetMap/Nominatim",
    }
    cache[key] = point
    save_cache(cache)
    time.sleep(1.1)
    return dict(point)


def osrm_matrix(points):
    """Get directed driving-road distance and duration matrices from OSRM."""
    if requests is None:
        raise RuntimeError("Install requirements first: py -m pip install -r requirements.txt")
    coords = ";".join(f'{p["longitude"]:.7f},{p["latitude"]:.7f}' for p in points)
    response = requests.get(
        f"{OSRM_TABLE_URL}/{coords}", params={"annotations": "distance,duration"},
        headers={"User-Agent": USER_AGENT}, timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {data}")
    distances = [[float(v)/1000 if v is not None else float("inf") for v in row] for row in data["distances"]]
    durations = [[float(v) if v is not None else float("inf") for v in row] for row in data["durations"]]
    return distances, durations


def route_geometry(route, points):
    """Fetch the best road line for the interactive route image."""
    if requests is None:
        return None
    ordered = [points[i] for i in route]
    coords = ";".join(f'{p["longitude"]:.7f},{p["latitude"]:.7f}' for p in ordered)
    try:
        r = requests.get(f"{OSRM_ROUTE_URL}/{coords}",
                         params={"overview":"full", "geometries":"geojson"},
                         headers={"User-Agent":USER_AGENT}, timeout=45)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "Ok":
            return data["routes"][0]["geometry"]["coordinates"]
    except Exception:
        return None
    return None


def show_catalog(catalog):
    print("\nAVAILABLE CDO LOCATIONS")
    print("-"*78)
    for r in catalog:
        print(f'{r["catalog_id"]:<7} {r["name"]:<32} {r["record_type"]}')


def resolve_location(token, catalog_map):
    token = token.strip()
    if token.upper() in catalog_map:
        record = catalog_map[token.upper()]
        point = geocode(record["geocode_query"])
        point["name"] = record["name"]
        return point

    if "," in token:
        parts = [x.strip() for x in token.split(",")]
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0]), float(parts[1])
                name = input("Name for this coordinate: ").strip() or token
                return {"name":name,"vertex":"","latitude":lat,"longitude":lon,
                        "display_name":name,"source":"User-supplied coordinate"}
            except ValueError:
                pass

    query = token if "cagayan de oro" in token.lower() else token + ", Cagayan de Oro City, Philippines"
    point = geocode(query)
    point["name"] = token.split(",")[0].strip()
    return point


def ask_location(prompt, catalog_map):
    while True:
        token = input(prompt).strip()
        if not token:
            continue
        try:
            point = resolve_location(token, catalog_map)
            print("Resolved:", point.get("display_name", point["name"]))
            print(f'Coordinate: {point["latitude"]:.6f}, {point["longitude"]:.6f}')
            if input("Use this location? [Y/n]: ").strip().lower() in ("", "y", "yes"):
                return point
        except Exception as e:
            print("Could not use that location:", e)


def run_interactive():
    """User-generated road-distance TSP extension."""
    if requests is None:
        print("Install requirements first: py -m pip install -r requirements.txt")
        return

    catalog = load_csv(MASTER_CATALOG)
    catalog_map = {r["catalog_id"].upper(): r for r in catalog}
    print("\n" + "="*78)
    print("INTERACTIVE CDO ROAD MODE")
    print("="*78)
    print("Graph: weighted DIRECTED graph using OSRM driving-road distance.")
    print("Brute Force remains the optimization algorithm.\n")

    if input("Show the full citywide catalog? [Y/n]: ").strip().lower() in ("", "y", "yes"):
        show_catalog(catalog)

    start = ask_location("\nChoose START: ", catalog_map)
    while True:
        try:
            count = int(input("How many destinations? (2-8): "))
            if 2 <= count <= 8:
                break
        except ValueError:
            pass
        print("Enter a number from 2 to 8.")

    points = [start]
    used = {start["name"].lower()}
    for number in range(1, count + 1):
        while True:
            p = ask_location(f'Destination {number}/{count}: ', catalog_map)
            if p["name"].lower() not in used:
                points.append(p); used.add(p["name"].lower()); break
            print("That location is already selected.")

    points[0]["vertex"] = "S"
    for i in range(1, len(points)):
        points[i]["vertex"] = chr(ord("A") + i - 1)

    possible = math.factorial(len(points)-1)
    print(f'\nBrute Force will evaluate {possible:,} routes.')
    if input("Continue? [Y/n]: ").strip().lower() not in ("", "y", "yes"):
        return

    distances, durations = osrm_matrix(points)
    results, elapsed = brute_force_tsp(points, distances, durations)
    best = results[0]
    check = verify_route(best["route_indices"], len(points), distances, best["distance_km"])
    legs = edge_calculation(best["route_indices"], points, distances)

    folder = OUTPUT / ("interactive_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    folder.mkdir(parents=True, exist_ok=True)
    save_matrix(folder / "distance_matrix_km.csv", points, distances)
    save_ranked_routes(folder, results, points)
    write_dict_csv(folder / "optimal_route_edge_calculation.csv", legs)
    write_dict_csv(folder / "input_locations_used.csv", [
        {"vertex":p["vertex"],"name":p["name"],"latitude":p["latitude"],
         "longitude":p["longitude"],"source":p.get("source", "OSM/Nominatim")}
        for p in points
    ])
    geom = route_geometry(best["route_indices"], points)
    plot_route(folder / "optimal_route.png", points, best["route_indices"],
               f'Interactive Optimal Route — {best["distance_km"]:.3f} km', geom)

    route_text = " -> ".join(route_names(best["route_indices"], points))
    minutes = None if best["duration_seconds"] is None else best["duration_seconds"] / 60
    summary = (
        "INTERACTIVE CDO ROAD RESULT\n" + "="*70 + "\n"
        "Graph: weighted directed graph\n"
        "Weights: OSRM driving-road distance in km\n"
        f'Routes evaluated: {len(results):,}\n'
        f'Optimal route: {route_text}\n'
        f'Minimum distance: {best["distance_km"]:.3f} km\n'
        + (f'Estimated matrix travel time: {minutes:.1f} min\n' if minutes is not None else "")
        + f'Brute Force runtime: {elapsed:.6f} sec\n'
        + f'Valid closed tour: {"YES" if check["valid_tsp_tour"] else "NO"}\n'
        + "Optimality: proven optimal for this selected OSRM matrix because every permutation was evaluated.\n"
        + "Data: © OpenStreetMap contributors; geocoding Nominatim; road matrix OSRM.\n"
    )
    (folder / "result_summary.txt").write_text(summary, encoding="utf-8")
    print("\n" + summary)
    print("Output folder:", folder)


# =============================================================================
# 9) DATASET BROWSER AND MAIN MENU
# =============================================================================
def browse_dataset():
    catalog = load_csv(MASTER_CATALOG)
    show_catalog(catalog)
    barangays = sum(r["record_type"] == "barangay" for r in catalog)
    landmarks = sum(r["record_type"] == "landmark" for r in catalog)
    print(f'\nOfficial barangays: {barangays}')
    print(f'Other landmarks: {landmarks}')
    print(f'Total selectable records: {len(catalog)}')
    print("The large catalog provides citywide coverage; each Brute Force run uses a small selected subset.")


def main():
    import sys
    if "--standard" in sys.argv:
        run_standard(); return
    if "--interactive" in sys.argv:
        run_interactive(); return

    while True:
        print("\n" + "="*78)
        print("CDO BRUTE FORCE ROUTE OPTIMIZER — PIT FINAL")
        print("="*78)
        print("1. PIT Demo")
        print("2. Interactive CDO Road Mode (user-generated)")
        print("3. Browse Full CDO Dataset")
        print("4. Exit")
        choice = input("\nChoose 1-4: ").strip()
        if choice == "1": run_standard()
        elif choice == "2": run_interactive()
        elif choice == "3": browse_dataset()
        elif choice == "4": break
        else: print("Invalid choice.")


if __name__ == "__main__":
    main()
