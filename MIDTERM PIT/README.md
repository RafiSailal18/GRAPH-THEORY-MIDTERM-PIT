# CDO Brute Force Route Optimizer — PIT Final

This version is organized specifically around the supplied **Performance Innovative Task** instructions.

## Recommended video run

```powershell
py -m pip install -r requirements.txt
py main.py --standard
```

The standard run visibly shows the problem, objective, graph type, vertices, edge-weight model, input data, all 720 routes evaluated, optimal route, total distance, leg-by-leg recalculation, route validation, and optimality statement.

## Standard real-life application

A tourist begins at **Gaston Park**, visits six required Cagayan de Oro landmarks exactly once, and returns to Gaston Park. The quantity minimized is **total geographic distance in kilometres**.

The graph is:
- weighted;
- complete;
- undirected;
- vertices = locations;
- edges = possible connections between every pair;
- weight = Haversine geographic distance in kilometres.

With Gaston Park fixed and six destinations:

```text
6! = 720 routes
```

Expected shortest Standard Mode distance: approximately **4.189 km**.

## Evidence generated

`output/standard_assignment/` contains:
- `input_locations_used.csv`
- `distance_matrix.csv`
- `weighted_graph_model.png`
- `all_routes_ranked.csv`
- `all_routes_ranked.json`
- `top_10_routes.txt`
- `optimal_route_edge_calculation.csv`
- `verification_report.txt`
- `result_summary.txt`
- `optimal_route.png`
- `google_maps_locations.csv`
- `google_maps_best_route.txt`

## Google Maps requirement

The PIT instructions explicitly say to use Google Maps. The project therefore includes a Google Maps link for every Standard Mode vertex and a Google Maps Directions link for the winning stop order.

To stay scientifically accurate, the program does **not** call those Google Maps links the numerical source of the Standard Mode edge weights. The current PPT uses the frozen coordinate/Haversine model, and that distinction is shown in the dataset and output files.

## Strong citywide dataset + interactive extension

`data/psgc_cdo_barangays_2025.csv` contains all 80 official CDO barangays from the PSA PSGC dataset. `data/cdo_master_catalog.csv` combines those barangays with selected landmarks/facilities.

Run:

```powershell
py main.py --interactive
```

The user chooses the start and destinations. Nominatim resolves coordinates, OSRM supplies driving-road distances, and **Brute Force still evaluates every route order**.

See `references/ASSIGNMENT_ALIGNMENT.md` before recording.
