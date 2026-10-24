# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .generators import generate_requests

def validate_candidates(candidates):
    if len({r.request_id for r in candidates}) != len(candidates):
        raise ValueError("ID kegiatan harus unik.")
    if len({(r.room_id, r.day) for r in candidates}) > 1:
        raise ValueError("DP hanya menerima satu ruangan dan satu hari.")
    if any(not (0 <= r.start < r.end <= 1440) or r.value < 0 for r in candidates):
        raise ValueError("Waktu atau nilai kegiatan tidak valid.")

def find_previous_compatible(ordered, j):
    """p(j) versi 1..n: posisi terakhir i < j dengan ordered[i-1].end <= ordered[j-1].start.
    Pencarian biner manual pada kegiatan 1..j-1 (sudah terurut berdasarkan end)."""
    target = ordered[j - 1].start
    low, high, answer = 1, j - 1, 0
    while low <= high:
        mid = (low + high) // 2
        if ordered[mid - 1].end <= target:
            answer = mid
            low = mid + 1
        else:
            high = mid - 1
    return answer

def optimize_schedule(candidates):
    validate_candidates(candidates)
    if not candidates:
        return 0, []

    # 1) Urutkan berdasarkan selesai, lalu mulai, lalu ID agar hasil konsisten.
    ordered = sorted(candidates, key=lambda r: (r.end, r.start, r.request_id))
    n = len(ordered)

    # 2) Hitung p(j) untuk j = 1..n dengan binary search. p[0] tidak dipakai.
    p = [0] * (n + 1)
    for j in range(1, n + 1):
        p[j] = find_previous_compatible(ordered, j)

    # 3) Isi tabel DP secara iteratif (bottom-up).
    dp = [0] * (n + 1)
    for j in range(1, n + 1):
        skip = dp[j - 1]
        take = ordered[j - 1].value + dp[p[j]]
        dp[j] = max(skip, take)

    # 4) Trace-back: jika seri, pilih cabang lewati.
    selected, j = [], n
    while j > 0:
        take = ordered[j - 1].value + dp[p[j]]
        if take > dp[j - 1]:
            selected.append(ordered[j - 1].request_id)
            j = p[j]
        else:
            j -= 1
    selected.reverse()
    return dp[n], selected

def explain_dp_table(candidates):
    """Cetak tabel j, kegiatan, waktu, nilai, p(j), DP[j] seperti markdown slide 15."""
    validate_candidates(candidates)
    ordered = sorted(candidates, key=lambda r: (r.end, r.start, r.request_id))
    n = len(ordered)
    p = [0] + [find_previous_compatible(ordered, j) for j in range(1, n + 1)]
    dp = [0] * (n + 1)
    for j in range(1, n + 1):
        dp[j] = max(dp[j - 1], ordered[j - 1].value + dp[p[j]])
    _, chosen = optimize_schedule(candidates)
    fmt = lambda m: f"{m // 60:02d}.{m % 60:02d}"
    print(f"{'j':>2} | {'ID':<4} | {'Kegiatan':<28} | {'Waktu':<11} | {'Nilai':>5} | {'p(j)':>4} | {'DP[j]':>5} | Terpilih")
    for j in range(1, n + 1):
        r = ordered[j - 1]
        print(f"{j:>2} | {r.request_id:<4} | {r.title[:28]:<28} | {fmt(r.start)}–{fmt(r.end)} | "
              f"{r.value:>5} | {p[j]:>4} | {dp[j]:>5} | {'Ya' if r.request_id in chosen else 'Tidak'}")

def no_overlap(selected):
    ordered = sorted(selected, key=lambda r: (r.start, r.end, r.request_id))
    return all(a.end <= b.start for a, b in zip(ordered, ordered[1:]))

def brute_force_reference(candidates):
    validate_candidates(candidates)
    if len(candidates) > 15:
        raise ValueError("Pembanding dibatasi 15 kegiatan.")
    candidates = sorted(candidates, key=lambda r: (r.start, r.end, r.request_id))
    best_value, best_ids = 0, []
    for size in range(len(candidates) + 1):
        for chosen in combinations(candidates, size):
            if all(a.end <= b.start for a, b in zip(chosen, chosen[1:])):
                value = sum(r.value for r in chosen)
                if value > best_value:
                    best_value = value
                    best_ids = [r.request_id for r in chosen]
    return best_value, best_ids

def earliest_finish_reference(candidates):
    validate_candidates(candidates)
    selected, last_end = [], -1
    for request in sorted(candidates, key=lambda r: (r.end, r.start, r.request_id)):
        if request.start >= last_end:
            selected.append(request)
            last_end = request.end
    return sum(r.value for r in selected), [r.request_id for r in selected]

def verify_dp_random_cases(case_count=100, seed=SEED):
    rng = Random(seed)
    for case in range(case_count):
        sample = generate_requests(rng.randrange(0, 16), seed=rng.randrange(1_000_000))
        expected, _ = brute_force_reference(sample)
        actual, ids = optimize_schedule(sample)
        selected = [r for r in sample if r.request_id in set(ids)]
        assert len(ids) == len(set(ids)) == len(selected), f"ID salah pada kasus {case}"
        assert no_overlap(selected) and sum(r.value for r in selected) == actual
        assert actual == expected, f"Nilai berbeda pada kasus {case}"
    return f"{case_count} kasus acak DP sesuai pembanding."
