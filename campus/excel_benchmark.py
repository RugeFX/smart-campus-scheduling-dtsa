"""Measure the active Excel inputs with the Colab timing/memory helpers."""
from .data import build_search_indexes
from .experiments import measure_operation, measure_peak_memory
from .feb_views import queue_inputs, room_inputs, available_weeks, scheduling_inputs
from .heap import MinHeapPriorityQueue
from .hash_table import HashTableChaining
from .trie import Trie
from .avl import AVLTree
from .dp import optimize_schedule, brute_force_reference


def measure_excel(data, algorithm, limit=243, repeat=5, query="akun"):
    results = []
    def record(operation, implementation, n, k, setup, action, metric=None):
        measured = measure_operation(setup, action, repeat, metric)
        peak = measure_peak_memory(setup, action)
        results.append({"Algoritma": algorithm, "Operasi": operation, "Implementasi": implementation,
            "n": n, "k": k, "Median (ms)": measured["median_seconds"] * 1000,
            "Puncak tambahan (byte)": peak, "Pengulangan": repeat, "Berkas": data["source_name"],
            "SHA256 Excel": data["sha256"], "Detail counter": str(measured["metrics"])})
    if algorithm == "Hash Table":
        pairs = data["ingredients"]["kelas"][:limit]
        if not pairs: raise ValueError("Tidak ada kelas Excel untuk percobaan.")
        queries = [key for key, _ in pairs]
        def setup():
            table = HashTableChaining()
            for key, value in pairs: table.put(key, value)
            table.probes = 0
            return table
        record("Cari semua kode kelas", "Hash chaining", len(pairs), len(queries), setup,
            lambda t: [t.get(key) for key in queries], lambda t, value: {"probes": t.probes})
        record("Cari semua kode kelas", "Pencarian linear", len(pairs), len(queries), lambda: pairs,
            lambda values: [next((v for k, v in values if k == key), None) for key in queries])
    elif algorithm == "Trie":
        entries = data["ingredients"]["nama"][:limit]
        if not entries: raise ValueError("Tidak ada nama Excel untuk percobaan.")
        prefix = query.strip().casefold()
        if not prefix: raise ValueError("Awalan pencarian tidak boleh kosong.")
        def setup():
            trie = Trie()
            for e in entries: trie.insert(e.name, e.entry_id)
            return trie
        expected = {e.entry_id for e in entries if e.name.strip().casefold().startswith(prefix)}
        record("Cari awalan yang sama", "Trie", len(entries), len(expected), setup, lambda t: t.autocomplete(prefix))
        def scan(values):
            return list(dict.fromkeys(e.entry_id for e in values if e.name.strip().casefold().startswith(prefix)))
        record("Cari awalan yang sama", "Pencarian linear", len(entries), len(expected), lambda: entries, scan)
    elif algorithm == "Heap/PQ":
        batch, _ = queue_inputs(data)
        groups = {}
        for request in batch: groups.setdefault(request.day, []).append(request)
        batch = max(groups.values(), key=len)[:limit] if groups else []
        if not batch: raise ValueError("Tidak ada permintaan Excel untuk percobaan.")
        def build(queue):
            queue.build(batch)
            while queue: queue.pop()
        record("Bangun lalu ambil seluruh antrean", "Heap", len(batch), len(batch), MinHeapPriorityQueue, build,
            lambda t, result: {"comparisons": t.comparisons})
        def sorted_list(values):
            values.extend(sorted(enumerate(batch), key=lambda x: (x[1].priority, x[1].start, x[0])))
            while values: values.pop(0)
        record("Bangun lalu ambil seluruh antrean", "List terurut", len(batch), len(batch), list, sorted_list)
    elif algorithm == "AVL":
        weeks = available_weeks(data)
        rooms, _ = room_inputs(data, weeks[0] if weeks else None)
        rooms = rooms[:limit]
        if not rooms: raise ValueError("Tidak ada ruang Excel untuk percobaan.")
        k = min(10, len(rooms))
        def setup():
            tree = AVLTree("utilization")
            for room in rooms: tree.insert(room)
            return tree
        record("Ranking pemakaian", "AVL", len(rooms), k, setup, lambda tree: tree.top_k_utilization(k))
        record("Ranking pemakaian", "List + sort", len(rooms), k, lambda: rooms,
            lambda values: sorted(values, key=lambda r: (r.utilization, r.room_id), reverse=True)[:k])
    elif algorithm == "DP":
        candidates, _ = scheduling_inputs(data)
        if not candidates: raise ValueError("Tidak ada kandidat Excel untuk DP.")
        groups = {}
        for request in candidates: groups.setdefault((request.room_id, request.day), []).append(request)
        batch = max(groups.values(), key=len)[:min(limit, 15)]
        assert optimize_schedule(batch)[0] == brute_force_reference(batch)[0]
        record("Kombinasi satu ruang/hari", "DP", len(batch), None, lambda: batch, optimize_schedule)
        record("Kombinasi satu ruang/hari", "Semua kombinasi", len(batch), None, lambda: batch, brute_force_reference)
    else:
        raise ValueError("Algoritma tidak dikenal.")
    return results
