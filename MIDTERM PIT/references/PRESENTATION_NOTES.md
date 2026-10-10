# Presentation Notes

Use these exact ideas in the recording:

> Our standard graph is a weighted complete undirected graph. Each vertex is a required Cagayan de Oro location, and each edge weight is a Haversine geographic distance in kilometres.

> Gaston Park is fixed, leaving six destinations. Therefore Brute Force evaluates 6! or 720 possible route orders.

> Because every one of the 720 orders is evaluated, the minimum result is proven optimal for this exact distance matrix.

Do **not** call the 4.189 km result the shortest real driving route. Say:

> It is the shortest route under the Standard Mode geographic-distance model.

## Google Maps portion

The assignment specifically says to use Google Maps. After running the program, open `output/standard_assignment/google_maps_best_route.txt`, copy the URL into a browser, and show the required places/stop order in Google Maps.

Be explicit that Google Maps is used for visual verification while Standard Mode numerical weights are the Haversine values in `distance_matrix.csv`.

## Graph theory terms worth saying
- vertex
- edge
- edge weight
- weighted graph
- complete graph
- undirected graph
- Hamiltonian cycle
- Traveling Salesperson Problem
- exhaustive search
- factorial growth

A valid TSP tour is a Hamiltonian cycle because it visits every required vertex exactly once and returns to the start.
