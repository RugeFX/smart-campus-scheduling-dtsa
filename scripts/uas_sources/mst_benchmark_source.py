def run_mst_benchmarks(sizes=(16, 32, 64, 128), repeats=5, seed=42):
    """Synthetic sparse/dense/forest graphs; same graph for both methods.

    Setup and independent optimality certificate excluded from timer. Reuse the
    notebook's warmup + median timer and separate tracemalloc measurement.
    """
    from hashlib import sha256
    rows = []
    for n in sizes:
        if type(n) is not int or n < 2:
            raise ValueError("Ukuran graf minimal 2")
        nodes = tuple(f"R{i:04d}" for i in range(n))
        for scenario in ("sparse", "dense", "forest"):
            rng, edges = Random(seed + n), []
            for i, u in enumerate(nodes):
                for j in range(i + 1, n):
                    if scenario == "forest" and (i < n // 2) != (j < n // 2):
                        continue
                    if scenario == "dense" or j == i + 1 or rng.random() < 2 / n:
                        edges.append((u, nodes[j], rng.randint(1, 100)))
            for algorithm in (kruskal_mst, prim_mst):
                result = algorithm(nodes, edges)
                assert validate_mst(nodes, edges, result)["valid"]
                action = lambda algorithm=algorithm: algorithm(nodes, edges)
                elapsed = measure_operation(lambda: None, lambda _: action(), repeat=repeats)
                memory = measure_peak_memory(lambda: None, lambda _: action())
                rows.append({"algorithm": result.algorithm, "scenario": scenario,
                    "n": n, "edges": len(edges), "components": len(result.components),
                    "cost": result.total_cost, "median_seconds": elapsed["median_seconds"], "run_seconds": elapsed["run_seconds"], "peak_bytes": memory,
                    "runs": repeats, "warmups": 1, "seed": seed,
                    "input_sha256": sha256(repr((nodes, edges)).encode()).hexdigest()})
    return rows
