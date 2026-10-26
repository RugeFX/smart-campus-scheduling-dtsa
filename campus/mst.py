# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from dataclasses import dataclass
from math import isfinite, fsum, isclose
from numbers import Real
from .sorting import manual_merge_sort

@dataclass(frozen=True)
class MSTEdge:
    u: str
    v: str
    weight: float

@dataclass(frozen=True)
class MSTResult:
    nodes: tuple
    edges: tuple
    components: tuple
    total_cost: float
    algorithm: str
    trace: tuple = ()

class UnionFind:
    """Disjoint sets manual: union by rank dan iterative path compression."""
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in self.parent}

    def find(self, node):
        root = node
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[node] != node:
            parent = self.parent[node]
            self.parent[node] = root
            node = parent
        return root

    def union(self, u, v):
        a, b = self.find(u), self.find(v)
        if a == b:
            return False
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1
        return True

class PrimMinHeap:
    """Binary min-heap manual untuk tuple (biaya, asal, tujuan); bukan heapq."""
    def __init__(self):
        self.data = []

    def __bool__(self):
        return bool(self.data)

    def push(self, value):
        self.data.append(value)
        i = len(self.data) - 1
        while i:
            parent = (i - 1) // 2
            if self.data[parent] <= self.data[i]:
                break
            self.data[parent], self.data[i] = self.data[i], self.data[parent]
            i = parent

    def pop(self):
        if not self.data:
            raise IndexError("Heap kosong")
        first, last = self.data[0], self.data.pop()
        if self.data:
            self.data[0] = last
            i = 0
            while 2 * i + 1 < len(self.data):
                child = 2 * i + 1
                if child + 1 < len(self.data) and self.data[child + 1] < self.data[child]:
                    child += 1
                if self.data[i] <= self.data[child]:
                    break
                self.data[i], self.data[child] = self.data[child], self.data[i]
                i = child
        return first

def validate_mst_graph(nodes, edges):
    """Simple undirected graph; reject duplicates, loops, unknown endpoints/NaN.

    Negative/zero weights are mathematically valid for MST. UI costs restrict >=0.
    Input copied; neither algorithm mutates caller data.
    """
    nodes = tuple(nodes)
    if any(not isinstance(n, str) or not n or n.strip() != n for n in nodes):
        raise ValueError("Kode ruang harus berupa teks terisi tanpa spasi tepi.")
    if len(set(nodes)) != len(nodes):
        raise ValueError("Kode ruang berulang.")
    known, pairs, clean = set(nodes), set(), []
    for raw in edges:
        if isinstance(raw, MSTEdge):
            u, v, weight = raw.u, raw.v, raw.weight
        else:
            try:
                u, v, weight = raw
            except (TypeError, ValueError):
                raise ValueError("Setiap koneksi harus berisi asal, tujuan, biaya.") from None
        if not isinstance(u, str) or not isinstance(v, str) or u not in known or v not in known:
            raise ValueError("Ujung koneksi harus merupakan ruang dari Excel aktif.")
        if u == v:
            raise ValueError("Ruang tidak dapat dihubungkan ke dirinya sendiri.")
        if isinstance(weight, bool) or not isinstance(weight, Real) or not isfinite(weight):
            raise ValueError("Biaya harus angka hingga (bukan kosong/NaN/infinity).")
        if v < u:
            u, v = v, u
        if (u, v) in pairs:
            raise ValueError(f"Koneksi {u}–{v} berulang; arah sebaliknya adalah koneksi yang sama.")
        pairs.add((u, v))
        clean.append(MSTEdge(u, v, float(weight)))
    return nodes, tuple(clean)

def mst_components(nodes, edges):
    adjacency = {n: [] for n in nodes}
    for edge in edges:
        adjacency[edge.u].append(edge.v)
        adjacency[edge.v].append(edge.u)
    seen, groups = set(), []
    for start in nodes:
        if start in seen:
            continue
        stack, group = [start], []
        seen.add(start)
        while stack:
            node = stack.pop()
            group.append(node)
            for other in adjacency[node]:
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        groups.append(tuple(group))
    return tuple(groups)

def kruskal_mst(nodes, edges, trace_limit=0):
    """Minimum spanning FOREST. O(V + E log E), O(V+E) ruang.

    Stable manual merge sort + UnionFind rank/compression. Trace bounded/optional.
    """
    nodes, edges = validate_mst_graph(nodes, edges)
    if type(trace_limit) is not int or trace_limit < 0:
        raise ValueError("Batas trace harus bilangan bulat nonnegatif.")
    uf, selected, trace = UnionFind(nodes), [], []
    for edge in manual_merge_sort(edges, key=lambda e: (e.weight, e.u, e.v)):
        accepted = uf.union(edge.u, edge.v)
        if accepted:
            selected.append(edge)
        if len(trace) < trace_limit:
            trace.append((edge.u, edge.v, edge.weight, "pilih" if accepted else "tolak siklus"))
    return MSTResult(nodes, tuple(selected), mst_components(nodes, selected),
                     fsum(e.weight for e in selected), "Kruskal", tuple(trace))

def prim_mst(nodes, edges, trace_limit=0):
    """Lazy Prim forest, manual min-heap. O(V + E log E), O(V+E) ruang.

    Sisi stale dilewati. Mulai ulang di node belum dikunjungi untuk graf terputus.
    Graf simple: log E = O(log V); heap lazy dapat menyimpan O(E) item.
    """
    nodes, edges = validate_mst_graph(nodes, edges)
    if type(trace_limit) is not int or trace_limit < 0:
        raise ValueError("Batas trace harus bilangan bulat nonnegatif.")
    adjacency = {n: [] for n in nodes}
    for e in edges:
        adjacency[e.u].append((e.weight, e.u, e.v))
        adjacency[e.v].append((e.weight, e.v, e.u))
    visited, selected, trace = set(), [], []
    heap = PrimMinHeap()
    for start in nodes:
        if start in visited:
            continue
        visited.add(start)
        for item in adjacency[start]:
            heap.push(item)
        while heap:
            weight, u, v = heap.pop()
            accepted = v not in visited
            if len(trace) < trace_limit:
                trace.append((u, v, weight, "pilih" if accepted else "lewati sisi stale"))
            if not accepted:
                continue
            visited.add(v)
            a, b = (u, v) if u < v else (v, u)
            selected.append(MSTEdge(a, b, weight))
            for item in adjacency[v]:
                if item[2] not in visited:
                    heap.push(item)
    return MSTResult(nodes, tuple(selected), mst_components(nodes, selected),
                     fsum(e.weight for e in selected), "Prim", tuple(trace))

def mst_path_max(adjacency, start, end):
    stack = [(start, None, None)]
    while stack:
        node, parent, maximum = stack.pop()
        if node == end:
            return maximum
        for other, weight in adjacency[node]:
            if other != parent:
                stack.append((other, node, weight if maximum is None else max(maximum, weight)))
    return None

def validate_mst(nodes, edges, result):
    """Independent forest/cycle-property certificate, O(V*(V+E)).

    On a forest, every non-tree edge must weigh >= max edge on its tree path.
    This certifies minimality even with ties/negative weights, beyond cost equality.
    Validator is intentionally outside benchmark timers.
    """
    nodes, edges = validate_mst_graph(nodes, edges)
    try:
        _, selected = validate_mst_graph(nodes, result.edges)
    except ValueError:
        return {"valid": False, "reason": "Sisi hasil tidak valid."}
    original = {(e.u, e.v): e.weight for e in edges}
    if result.nodes != nodes or any(original.get((e.u, e.v)) != e.weight for e in selected):
        return {"valid": False, "reason": "Sisi/node hasil tidak sesuai graf input."}
    groups, expected = mst_components(nodes, selected), mst_components(nodes, edges)
    partition = lambda parts: {frozenset(group) for group in parts}
    acyclic = len(selected) == len(nodes) - len(groups)
    spans = partition(groups) == partition(expected) == partition(result.components)
    cost_ok = isclose(fsum(e.weight for e in selected), result.total_cost, rel_tol=1e-12, abs_tol=1e-12)
    if not acyclic or not spans or not cost_ok:
        return {"valid": False, "reason": "Jumlah sisi, cakupan komponen, siklus, atau total biaya salah."}
    adjacency = {n: [] for n in nodes}
    for e in selected:
        adjacency[e.u].append((e.v, e.weight))
        adjacency[e.v].append((e.u, e.weight))
    tree_pairs = {(e.u, e.v) for e in selected}
    for e in edges:
        if (e.u, e.v) not in tree_pairs:
            maximum = mst_path_max(adjacency, e.u, e.v)
            if maximum is None or maximum > e.weight:
                return {"valid": False, "reason": "Cycle property gagal: ada penggantian sisi yang lebih murah."}
    return {"valid": True, "components": len(groups), "edge_count": len(selected),
            "acyclic": True, "spans": True, "minimal": True, "cost_ok": True}

def mst_cut_witness(nodes, edges, result, edge_index=0):
    """Remove a selected edge: show its cut and cheapest original crossing edge."""
    if not validate_mst(nodes, edges, result)["valid"]:
        raise ValueError("Hasil MST harus valid sebelum menampilkan bukti cut.")
    chosen = result.edges[edge_index]
    remaining = result.edges[:edge_index] + result.edges[edge_index + 1:]
    side = next(set(group) for group in mst_components(result.nodes, remaining) if chosen.u in group)
    _, clean = validate_mst_graph(nodes, edges)
    crossing = [e for e in clean if (e.u in side) != (e.v in side)]
    cheapest = min(e.weight for e in crossing)
    return {"edge": chosen, "side_a": tuple(n for n in nodes if n in side),
            "side_b": tuple(n for n in nodes if n not in side),
            "crossing": tuple(crossing), "minimum": cheapest, "safe": chosen.weight == cheapest}

def mst_room_scenario(room_frame):
    """Excel supplies nodes/floor metadata ONLY; ALL edges/costs are assumptions.

    Template: chain room codes within each building/floor (cost 1), connect rooms
    of the same ordinal across consecutive floors of that building (cost 3).
    No claim of physical adjacency, metres, route, or real installation cost.
    """
    rows = room_frame.to_dict("records")
    nodes = tuple(str(row["ruang"]) for row in rows)
    validate_mst_graph(nodes, [])
    groups = {}
    for row in rows:
        group = (str(row["gedung"]), str(row["lantai"]))
        groups.setdefault(group, []).append(str(row["ruang"]))
    ordered = manual_merge_sort(groups, key=lambda group: group)
    groups = {key: manual_merge_sort(groups[key]) for key in ordered}
    edges = []
    for rooms in groups.values():
        edges.extend(MSTEdge(a, b, 1.0) for a, b in zip(rooms, rooms[1:]))
    for a, b in zip(ordered, ordered[1:]):
        if a[0] == b[0]:
            edges.extend(MSTEdge(u, v, 3.0) for u, v in zip(groups[a], groups[b]))
    return validate_mst_graph(nodes, edges)
