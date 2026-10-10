# Methodology

## Standard Assignment Mode

### Application
A tourist begins at Gaston Park, visits six required Cagayan de Oro landmarks exactly once, and returns to Gaston Park. The objective is to minimize total geographic distance.

### Graph model
- S = Gaston Park
- A = St. Augustine Cathedral
- B = Duaw Park
- C = Xavier University
- D = Cogon Public Market
- E = Centrio Mall
- F = Limketkai Mall

The graph is complete and **undirected**. Each required location is a vertex. Each pair of vertices has an edge. The edge weight is Haversine geographic distance in kilometres. Since Haversine distance is symmetric, weight(A,B) = weight(B,A).

### Brute Force
The starting point is fixed. The six destinations have 6! = 720 possible orders. For each permutation, the program prepends the start, appends the start, sums all edge weights, and stores the candidate. After every candidate is evaluated, the results are sorted from shortest to longest.

### Verification
The program separately checks the closed tour, checks that every vertex occurs exactly once before the return, and recalculates the total from the edge weights. See `optimal_route_edge_calculation.csv` and `verification_report.txt`.

## Interactive Road Mode

Interactive Mode is an extension. The user chooses a starting point and 2–8 destinations. Nominatim resolves coordinates and OSRM supplies road distances. The road matrix is treated as **directed** because real roads can be asymmetric due to one-way streets. Brute Force then evaluates all destination permutations. OSRM supplies weights; it does not solve the TSP.
