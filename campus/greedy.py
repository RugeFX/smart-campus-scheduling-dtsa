# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .sorting import manual_merge_sort
from .dp import validate_candidates, no_overlap, optimize_schedule
from .generators import generate_requests

def select_activities(candidates, strategy="earliest_finish", trace=None):
    """Maksimalkan JUMLAH kegiatan satu ruang/hari; bobot tidak dioptimalkan.

    Earliest finish optimal secara kardinalitas. Earliest start hanya strategi
    pembanding dan tidak dijamin optimal. Keduanya memakai merge sort manual.
    """
    validate_candidates(candidates)
    if strategy not in ("earliest_finish", "earliest_start"):
        raise ValueError("Strategi greedy tidak dikenal.")
    key = (lambda r: (r.end, r.start, r.request_id)) if strategy == "earliest_finish" else (lambda r: (r.start, r.end, r.request_id))
    ordered = manual_merge_sort(candidates, key=key)
    selected, last_end = [], -1
    for r in ordered:
        accept = r.start >= last_end
        if trace is not None:
            trace.append({"ID":r.request_id, "Mulai":r.start, "Selesai":r.end,
                          "Selesai sebelumnya":last_end, "Terpilih":accept,
                          "Alasan":"Tidak bentrok" if accept else "Bentrok dengan pilihan sebelumnya"})
        if accept: selected.append(r.request_id); last_end = r.end
    return len(selected), selected

def brute_force_activity_count(candidates):
    validate_candidates(candidates)
    if len(candidates) > 15: raise ValueError("Brute force kardinalitas dibatasi 15 kandidat.")
    best = []
    for size in range(len(candidates) + 1):
        for chosen in combinations(candidates, size):
            if no_overlap(chosen) and len(chosen) > len(best): best = [r.request_id for r in chosen]
    return len(best), best

def verify_greedy_random_cases(case_count=100, seed=SEED):
    rng = Random(seed)
    for case in range(case_count):
        batch = generate_requests(rng.randrange(0, 11), seed=rng.randrange(1_000_000))
        count, ids = select_activities(batch)
        expected, _ = brute_force_activity_count(batch)
        assert count == expected and no_overlap([r for r in batch if r.request_id in ids]), case
    return f"{case_count} kasus acak greedy cocok dengan brute force kardinalitas."

def greedy_weight_counterexample():
    """Fixture pengujian batas weighted vs unweighted, bukan jadwal Excel."""
    def request(code, start, end, value):
        return ScheduleRequest(code, code, "Event", 1, "UJI", "2026-10-05", start, end, value)
    batch = [request("A", 480, 540, 2), request("B", 540, 600, 2), request("C", 480, 600, 10)]
    count, ids = select_activities(batch)
    value, dp_ids = optimize_schedule(batch)
    return {"fixture":True, "candidates":batch, "greedy_count":count, "greedy_ids":ids,
            "greedy_value":sum(r.value for r in batch if r.request_id in ids), "dp_value":value, "dp_ids":dp_ids}
