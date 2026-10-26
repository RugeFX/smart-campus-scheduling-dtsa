"""Bounded, explicit measurements; ordinary scheduling does not run experiments."""
from time import perf_counter
from .dp import optimize_schedule, optimize_schedule_memo, naive_recursive

NAIVE_UI_LIMIT = 15
MEMO_UI_LIMIT = 400


def compare_schedule_methods(batch):
    rows = []
    methods = [("Rekursi naif", naive_recursive, NAIVE_UI_LIMIT),
               ("Memoization (top-down)", optimize_schedule_memo, MEMO_UI_LIMIT),
               ("Tabulation (bottom-up)", optimize_schedule, None)]
    for name, action, limit in methods:
        if limit is not None and len(batch) > limit:
            rows.append({"Metode":name,"Nilai":None,"Pemanggilan OPT / sel":None,
                         "Detik":None,"Status":f"Dilewati: maksimal {limit} kandidat"})
            continue
        started = perf_counter()
        try:
            result = action(batch)
        except RecursionError:
            rows.append({"Metode":name,"Nilai":None,"Pemanggilan OPT / sel":None,
                         "Detik":None,"Status":"Batas rekursi; gunakan tabulasi"})
        else:
            calls = result[1] if name == "Rekursi naif" else result[2] if name.startswith("Memo") else len(batch)
            rows.append({"Metode":name,"Nilai":result[0],"Pemanggilan OPT / sel":calls,
                         "Detik":perf_counter()-started,"Status":"Selesai"})
    return rows
