# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .generators import generate_requests
from .sorting import manual_merge_sort

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
    ordered = manual_merge_sort(candidates, key=lambda r: (r.end, r.start, r.request_id))
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

def optimize_schedule_memo(candidates):
    """Versi memoization (top-down): recurrence yang sama, ditulis rekursif.

    Definisi formal (sama untuk ketiga implementasi DP di notebook ini):
      OPT(0) = 0
      OPT(j) = max(OPT(j-1), nilai[j] + OPT(p(j)))
    Cache berupa dict {j: nilai} yang ditulis manual, bukan functools.lru_cache,
    supaya mekanisme DP-nya terlihat. Tie-break seri tetap "lewati j" sehingga
    daftar ID terpilih identik dengan optimize_schedule (tabulation).
    Return (nilai_optimum, daftar_id, jumlah_pemanggilan_OPT).
    """
    validate_candidates(candidates)
    if not candidates:
        return 0, [], 0
    ordered = manual_merge_sort(candidates, key=lambda r: (r.end, r.start, r.request_id))
    n = len(ordered)
    p = [0] * (n + 1)
    for j in range(1, n + 1):
        p[j] = find_previous_compatible(ordered, j)
    cache = {0: 0}
    calls = 0

    def opt(j):
        nonlocal calls
        calls += 1
        if j not in cache:
            skip = opt(j - 1)
            take = ordered[j - 1].value + opt(p[j])
            cache[j] = skip if skip >= take else take  # seri -> lewati j.
        return cache[j]

    try:
        best = opt(n)  # Kedalaman rekursi ~n+1; untuk n besar gunakan tabulasi.
    except RecursionError:
        raise RecursionError("Batas rekursi Python terlampaui; gunakan tabulasi untuk n besar.")
    selected, j = [], n  # Trace-back memakai cache yang sudah terisi penuh.
    while j > 0:
        take = ordered[j - 1].value + cache[p[j]]
        if take > cache[j - 1]:
            selected.append(ordered[j - 1].request_id)
            j = p[j]
        else:
            j -= 1
    selected.reverse()
    return best, selected, calls

def explain_dp_table(candidates):
    """Cetak tabel j, kegiatan, waktu, nilai, p(j), DP[j] seperti markdown slide 15."""
    validate_candidates(candidates)
    ordered = manual_merge_sort(candidates, key=lambda r: (r.end, r.start, r.request_id))
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

def naive_recursive(candidates):
    """Rekursi naif: recurrence yang sama tanpa cache, pembanding O(2^n).

    Setiap OPT(j) memanggil OPT(j-1) dan OPT(p(j)) dari nol, sehingga sub-masalah
    dihitung ulang dan jumlah pemanggilan tumbuh eksponensial pada kasus terburuk
    (input rantai kompatibel, p(j)=j-1: tepat 2^(n+1)-1 pemanggilan).
    Return (nilai_optimum, jumlah_pemanggilan_OPT); tanpa rekonstruksi daftar ID
    karena tujuannya mengukur biaya, bukan menghasilkan jadwal.
    """
    validate_candidates(candidates)
    if len(candidates) > 26:
        raise ValueError("Rekursi naif dibatasi 26 kegiatan karena eksponensial.")
    if not candidates:
        return 0, 0
    ordered = sorted(candidates, key=lambda r: (r.end, r.start, r.request_id))
    n = len(ordered)
    p = [0] * (n + 1)
    for j in range(1, n + 1):
        p[j] = find_previous_compatible(ordered, j)
    calls = 0

    def opt(j):
        nonlocal calls
        calls += 1
        if j == 0:
            return 0
        skip = opt(j - 1)
        take = ordered[j - 1].value + opt(p[j])
        return skip if skip >= take else take

    return opt(n), calls

def chain_requests(n, seed=SEED):
    """Rantai kegiatan pendek yang saling kompatibel: p(j) = j-1 untuk semua j.

    Kasus terburuk rekursi naif (kedua cabang recurrence menyelam penuh,
    2^(n+1)-1 pemanggilan) sekaligus kasus normal bagi memo/tabulasi (O(n)).
    Dipakai bersama generate_requests sebagai dua jenis input pembanding yang
    sama untuk ketiga metode. Seed hanya menggeser jam mulai; rantai tetap
    kompatibel apa pun seed-nya.
    """
    rng = Random(seed)
    first = 420 + rng.randrange(0, 30)
    return [ScheduleRequest(f"CHAIN-{i:02d}", f"Kegiatan rantai {i}", "Event", 10, "F802",
                            DEMO_DAY, first + 30 * i, first + 30 * i + 30, 5, i)
            for i in range(n)]

def compare_dp_methods(sizes=(5, 10, 15, 20, 25), chain_sizes=(5, 10, 15, 20), seed=SEED):
    """Tabel naif vs memoization vs tabulation pada input yang sama.

    Dua jenis input: "padat" (generate_requests; tabrakan banyak, p(j) kecil)
    dan "rantai" (chain_requests; p(j)=j-1, kasus terburuk rekursi naif).
    Kolom pemanggilan menghitung masuknya OPT() untuk naif/memo; tabulation
    menghitung sel DP yang diisi, yaitu n. Return daftar dict baris dan
    mencetak tabel; nilai optimum ketiga metode dan ID memo vs tabulasi
    di-assert sama.
    """
    rows = []
    for label, batch_sizes, make in (("padat", sizes, generate_requests),
                                     ("rantai", chain_sizes, chain_requests)):
        for n in batch_sizes:
            batch = make(n, seed)
            started = perf_counter()
            naive_value, naive_calls = naive_recursive(batch)
            naive_seconds = perf_counter() - started
            started = perf_counter()
            memo_value, memo_ids, memo_calls = optimize_schedule_memo(batch)
            memo_seconds = perf_counter() - started
            started = perf_counter()
            tab_value, tab_ids = optimize_schedule(batch)
            tab_seconds = perf_counter() - started
            assert naive_value == memo_value == tab_value, f"Nilai berbeda pada {label} n={n}."
            assert memo_ids == tab_ids, f"ID memo != tabulasi pada {label} n={n}."
            rows.append({"input": label, "n": n, "nilai": tab_value,
                         "naif_pemanggilan": naive_calls, "naif_detik": round(naive_seconds, 6),
                         "memo_pemanggilan": memo_calls, "memo_detik": round(memo_seconds, 6),
                         "tab_sel": n, "tab_detik": round(tab_seconds, 6)})
    print("naif vs memo vs tabulasi (pemanggilan OPT; tabulasi = sel yang diisi)")
    print(f"{'input':>6} | {'n':>3} | {'naif':>12} {'detik':>9} | {'memo':>8} {'detik':>9} | {'tab':>4} {'detik':>9}")
    for row in rows:
        print(f"{row['input']:>6} | {row['n']:>3} | {row['naif_pemanggilan']:>12} {row['naif_detik']:>9.6f} | "
              f"{row['memo_pemanggilan']:>8} {row['memo_detik']:>9.6f} | "
              f"{row['tab_sel']:>4} {row['tab_detik']:>9.6f}")
    return rows
