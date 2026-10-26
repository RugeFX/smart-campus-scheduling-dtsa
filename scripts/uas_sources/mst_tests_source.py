def test_t29():
    nodes = ("A", "B", "C", "D")
    edges = [("A", "B", 1), ("B", "C", 2), ("A", "C", 8), ("C", "D", 3), ("A", "D", 9)]
    for algorithm in (kruskal_mst, prim_mst):
        result = algorithm(nodes, edges, trace_limit=2)
        assert result.total_cost == 6 and len(result.edges) == 3
        assert len(result.trace) == 2 and validate_mst(nodes, edges, result)["valid"]
        assert mst_cut_witness(nodes, edges, result)["safe"]


def test_t30():
    for nodes, edges, cost, components in [((), [], 0, 0), (("A",), [], 0, 1),
            (("A", "B", "C", "D"), [("A", "B", 2)], 2, 3)]:
        for algorithm in (kruskal_mst, prim_mst):
            result = algorithm(nodes, edges)
            assert result.total_cost == cost and len(result.components) == components
            assert len(result.edges) == len(nodes) - components
            assert validate_mst(nodes, edges, result)["valid"]


def test_t31():
    nodes = ("A", "B", "C", "D")
    edges = [("A", "B", -4), ("B", "C", 0), ("A", "C", 0), ("C", "D", 2), ("B", "D", 2)]
    for algorithm in (kruskal_mst, prim_mst):
        result = algorithm(nodes, edges)
        assert result.total_cost == -2 and validate_mst(nodes, edges, result)["valid"]
    uf = UnionFind(nodes)
    assert uf.union("A", "B") and uf.union("C", "D") and uf.union("B", "D")
    assert not uf.union("A", "C") and len({uf.find(n) for n in nodes}) == 1
    heap = PrimMinHeap()
    for value in [(2, "A", "B"), (-1, "A", "C"), (2, "A", "A")]:
        heap.push(value)
    assert [heap.pop() for _ in range(3)] == [(-1, "A", "C"), (2, "A", "A"), (2, "A", "B")]


def test_t32():
    bad = [(("A", "A"), []), (("A",), [("A", "A", 1)]), (("A", "B"), [("A", "X", 1)]),
           (("A", "B"), [("A", "B", float("nan"))]), (("A", "B"), [("A", "B", True)]),
           (("A", "B"), [("A", "B", 1), ("B", "A", 2)])]
    for nodes, edges in bad:
        for algorithm in (kruskal_mst, prim_mst):
            try:
                algorithm(nodes, edges)
            except ValueError:
                pass
            else:
                raise AssertionError("Graf tidak valid harus ditolak")
    nodes, edges = ("A", "B", "C"), [("A", "B", 1), ("B", "C", 1), ("A", "C", 5)]
    # Spans all vertices and is acyclic, but deliberately more expensive.
    wrong = MSTResult(nodes, (MSTEdge("A", "B", 1), MSTEdge("A", "C", 5)), (nodes,), 6, "wrong")
    assert not validate_mst(nodes, edges, wrong)["valid"]


def mst_bruteforce_cost(nodes, edges):
    """Independent exhaustive subset oracle for SMALL graphs, never UI input."""
    from itertools import combinations
    nodes, edges = validate_mst_graph(nodes, edges)
    groups = mst_components(nodes, edges)
    count = len(nodes) - len(groups)
    target = {frozenset(group) for group in groups}
    best = None
    for subset in combinations(edges, count):
        if {frozenset(group) for group in mst_components(nodes, subset)} == target:
            cost = sum(e.weight for e in subset)
            best = cost if best is None else min(best, cost)
    return 0 if best is None and not nodes else best


def test_t33():
    rng = Random(42)
    for _ in range(60):
        nodes = tuple(f"R{i}" for i in range(rng.randint(1, 6)))
        edges = [(u, v, rng.randint(-5, 9)) for i, u in enumerate(nodes)
                 for v in nodes[i + 1:] if rng.random() < .5]
        expected = mst_bruteforce_cost(nodes, edges)
        for algorithm in (kruskal_mst, prim_mst):
            result = algorithm(nodes, edges)
            assert result.total_cost == expected and validate_mst(nodes, edges, result)["valid"]
