# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .generators import *
from .hash_table import HashTableChaining
from .heap import MinHeapPriorityQueue
from .avl import AVLTree
from .trie import Trie
from .dp import optimize_schedule, optimize_schedule_memo, naive_recursive, chain_requests, brute_force_reference
from bisect import insort
import gc

def measure_operation(setup, action, repeat=5, read_metrics=None):
    if type(repeat) is not int or repeat < 1:
        raise ValueError("Pengulangan harus bilangan bulat positif.")
    warm_state = setup()
    action(warm_state)  # Warm-up terpisah dari run yang diukur.
    del warm_state
    durations, metrics = [], []
    for _ in range(repeat):
        state = setup()  # State mutable baru; di luar waktu operasi.
        started = perf_counter()
        result = action(state)
        durations.append(perf_counter() - started)
        if read_metrics is not None:
            metrics.append(read_metrics(state, result))
        del state, result
    return {"median_seconds": median(durations), "runs": repeat,
            "run_seconds": durations, "metrics": metrics}

def measure_peak_memory(setup, action):
    state = setup()  # Memori state awal tidak masuk pengukuran action.
    gc.collect()
    tracemalloc.start()
    try:
        result = action(state)
        _, peak = tracemalloc.get_traced_memory()
        del result
        return peak
    finally:
        tracemalloc.stop()

def benchmark_heap_setup(batch, built=False):
    queue = MinHeapPriorityQueue()
    if built:
        queue.build(batch)
        queue.comparisons = 0
    return queue

def benchmark_sorted_insert(batch, values):
    for key, request in values:
        insort(batch, (key, request))

def benchmark_heap_insert(queue, values):
    for request in values:
        queue.push(request)

def benchmark_heap_cycle(queue, values):
    for request in values:
        queue.push(request)
        queue.pop()

def benchmark_list_cycle(batch, values):
    for key, request in values:
        insort(batch, (key, request))
        batch.pop(0)

def benchmark_hash_lookup(table, queries):
    return [table.get(key) for key in queries]

def benchmark_linear_lookup(pairs, queries):
    return [next((value for key, value in pairs if key == query), None) for query in queries]

def benchmark_avl_setup(room_list):
    tree = AVLTree("utilization")
    for room in room_list:
        tree.insert(room)
    tree.rotations = 0
    return tree

def benchmark_avl_update(tree, old, new, k):
    assert tree.delete((old.utilization, old.room_id))
    tree.insert(new)
    return tree.top_k_utilization(k)

def benchmark_list_update(room_list, old, new, k):
    index = next(i for i, room in enumerate(room_list) if room.room_id == old.room_id)
    room_list[index] = new
    return sorted(room_list, key=lambda room: (room.utilization, room.room_id), reverse=True)[:k]

def run_benchmarks(sizes=(240, 1000, 10000, 100000), repeat=5, seed=SEED):
    if not sizes or any(type(n) is not int or n < 1 for n in sizes):
        raise ValueError("Ukuran benchmark harus bilangan bulat positif.")
    results = []
    def record(module, operation, implementation, n, k, setup, action, metric=None, query=None):
        timing = measure_operation(setup, action, repeat, metric)
        peak = measure_peak_memory(setup, action)
        row = {"module": module, "operation": operation, "implementation": implementation,
               "n": n, "k": k, "source": "synthetic", "seed": seed,
               "median_seconds": timing["median_seconds"], "peak_bytes": peak,
               "runs": repeat, "query": query,
               "run_seconds": timing["run_seconds"], "operation_metrics": timing["metrics"],
               "memory_scope": "allocation during action; setup excluded"}
        results.append(row)
        print(f"Benchmark {module}/{operation}/{implementation} n={n}: "
              f"{row['median_seconds']:.6f}s; peak action={peak} B", flush=True)

    for n in sizes:
        batch = generate_requests(n, seed)
        keyed = [((request.priority, i), request) for i, request in enumerate(batch)]
        extra = [replace(batch[i % n], request_id=f"EXTRA-{i}") for i in range(min(100, n))]
        extra_keyed = [((request.priority, n + i), request) for i, request in enumerate(extra)]
        metric = lambda queue, result: {"comparisons": queue.comparisons}
        record("Heap/PQ", "build", "manual heapify", n, n,
               MinHeapPriorityQueue, lambda queue: queue.build(batch), metric)
        record("Heap/PQ", "push n", "manual heap", n, n,
               MinHeapPriorityQueue, lambda queue: benchmark_heap_insert(queue, batch), metric)
        record("Heap/PQ", "push n", "sorted list", n, n,
               list, lambda values: benchmark_sorted_insert(values, keyed))
        record("Heap/PQ", "push-pop pairs", "manual heap", n, len(extra),
               lambda: benchmark_heap_setup(batch, True), lambda queue: benchmark_heap_cycle(queue, extra), metric)
        record("Heap/PQ", "push-pop pairs", "sorted list", n, len(extra),
               lambda: sorted(keyed), lambda values: benchmark_list_cycle(values, extra_keyed))

        pairs = [(f"ID-{i:06d}", i) for i in range(n)]
        table = HashTableChaining()
        for key, value in pairs:
            table.put(key, value)
        queries = [f"ID-{(i * 7919) % n:06d}" if i % 2 == 0 else f"MISSING-{i}" for i in range(100)]
        assert benchmark_hash_lookup(table, queries) == benchmark_linear_lookup(pairs, queries)
        def hash_setup():
            table.probes = 0
            return table  # Struktur read-only pada get; reset penghitung tiap run.
        record("Hash", "get 50% hit", "chaining", n, len(queries), hash_setup,
               lambda state: benchmark_hash_lookup(state, queries),
               lambda state, result: {"probes": state.probes})
        record("Hash", "get 50% hit", "linear scan", n, len(queries), lambda: pairs,
               lambda state: benchmark_linear_lookup(state, queries))

        entries = generate_search_entries(n)
        names = Trie()
        for entry in entries:
            names.insert(entry.name, entry.entry_id)
        # Satu hasil pada semua ukuran agar biaya output sebanding.
        for operation, prefix in [("prefix sparse", entries[-1].name.casefold())] + (
                [("prefix dense", "akuntansi ")] if n <= 1000 else []):
            expected = [entry.entry_id for entry in entries if entry.name.casefold().startswith(prefix)]
            assert set(names.autocomplete(prefix)) == set(expected)
            record("Trie", operation, "manual trie", n, len(expected), lambda: names,
                   lambda state: state.autocomplete(prefix), query=prefix)
            record("Trie", operation, "linear startswith", n, len(expected), lambda: entries,
                   lambda state: [entry.entry_id for entry in state if entry.name.casefold().startswith(prefix)], query=prefix)
        del names, entries
        gc.collect()

        room_list = generate_rooms(n, seed)
        old = room_list[-1]
        new = replace(old, used_slots=(old.used_slots + 1) % (WEEKLY_SLOTS + 1))
        k = min(10, n)
        expected = benchmark_list_update(list(room_list), old, new, k)
        assert benchmark_avl_update(benchmark_avl_setup(room_list), old, new, k) == expected
        record("AVL", "update + top-k", "manual AVL", n, k,
               lambda: benchmark_avl_setup(room_list), lambda state: benchmark_avl_update(state, old, new, k),
               lambda state, result: {"rotations": state.rotations})
        record("AVL", "update + top-k", "list update + sort", n, k,
               lambda: list(room_list), lambda state: benchmark_list_update(state, old, new, k))
        record("DP", "standalone large", "weighted intervals", n, None,
               lambda: batch, optimize_schedule)

    # Pembanding eksponensial selalu pada batch kecil yang sama, n <= 15.
    for n in (8, 12, 15):
        batch = generate_requests(n, seed)
        assert optimize_schedule(batch)[0] == brute_force_reference(batch)[0]
        record("DP", "same small input", "weighted intervals", n, None, lambda: batch, optimize_schedule)
        record("DP", "same small input", "brute force", n, None, lambda: batch, brute_force_reference)

    # S7: naif vs memo vs tabulasi pada input yang persis sama. Dua jenis input:
    # padat (realistis, banyak tabrakan) dan rantai (p(j)=j-1; kasus terburuk
    # rekursi naif O(2^n), karena itu ukurannya lebih kecil). Metrik "calls"
    # menghitung pemanggilan OPT() untuk naif/memo.
    for operation, sizes, make in (("padat: naif vs memo vs tabulasi", (10, 15, 20, 25), generate_requests),
                                   ("rantai: naif vs memo vs tabulasi", (10, 15, 20), chain_requests)):
        for n in sizes:
            batch = make(n, seed)
            assert naive_recursive(batch)[0] == optimize_schedule_memo(batch)[0] == optimize_schedule(batch)[0]
            record("DP", operation, "rekursi naif", n, None, lambda: batch, naive_recursive,
                   lambda state, result: {"calls": result[1]})
            record("DP", operation, "memoization", n, None, lambda: batch, optimize_schedule_memo,
                   lambda state, result: {"calls": result[2]})
            record("DP", operation, "tabulation", n, None, lambda: batch, optimize_schedule)
    return results

BENCHMARK_SIZES = [240, 1000, 10000, 100000]
