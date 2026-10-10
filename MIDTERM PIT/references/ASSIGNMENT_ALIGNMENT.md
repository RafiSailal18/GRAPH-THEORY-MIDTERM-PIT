# Assignment Alignment Checklist

## 1. Assigned algorithm discussion

**Requirement:** explain Brute Force step by step, advantages/limitations, and optimality.

**Evidence:** `main.py -> brute_force_tsp()` and `references/METHODOLOGY.md`.

Correct statement:
> Brute Force is exact for the supplied weight matrix because every possible destination order is evaluated. The smallest total is therefore proven optimal for that graph/weight model.

## 2. Problem and objective

**Application:** tourist landmark itinerary in Cagayan de Oro City.

**Start:** Gaston Park.

**Required locations:** Gaston Park, St. Augustine Cathedral, Duaw Park, Xavier University, Cogon Public Market, Centrio Mall, Limketkai Mall.

**Objective:** minimize total geographic distance in kilometres.

**Constraints:** visit every required location exactly once, return to the start, fixed start, no traffic model in Standard Mode.

## 3. Methodology and graph model

Standard graph:
- weighted;
- complete;
- undirected;
- vertices = locations;
- edges = pairwise connections;
- weights = Haversine km.

Generated evidence:
- `weighted_graph_model.png`
- `distance_matrix.csv`
- `input_locations_used.csv`
- `google_maps_locations.csv`
- `google_maps_best_route.txt`

The Standard coordinates are explicitly labeled frozen PPT data. Google Maps links are used for visual verification rather than falsely claiming the Standard weights were downloaded from Google Maps.

## 4. Python implementation

Run:
```powershell
py main.py --standard
```

The terminal shows the input, route count, result, units, leg-by-leg recalculation, and validation. This is intended for the required live screen recording.

## 5. Solution / conclusion

`verification_report.txt` proves that:
- the route is closed;
- every required location is present;
- every required location is visited exactly once before return;
- the final total is independently recalculated from the edge matrix;
- the recalculated total matches the algorithm output.

## Submission

Minimum:
1. audio-video presentation;
2. `main.py`;
3. `data/standard_assignment_locations.csv`.

Recommended: submit the whole ZIP so the graph, matrix, references, and verification evidence are included.
