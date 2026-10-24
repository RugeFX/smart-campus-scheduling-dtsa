# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *

def generate_rooms(n, seed=SEED):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Jumlah data harus bilangan bulat tidak negatif.")
    rng = Random(seed)
    return [Room(f"SYN-R{i:06d}", rng.choice([30, 40, 60, 80, 100]),
                 used_slots=rng.randrange(WEEKLY_SLOTS + 1)) for i in range(n)]

def generate_requests(n, seed=SEED):
    if not isinstance(n, int) or n < 0:
        raise ValueError("Jumlah data harus bilangan bulat tidak negatif.")
    rng = Random(seed)
    data = []
    for i in range(n):
        kind = rng.choice(list(PRIORITY))
        duration = rng.choice([60, 75, 90, 100, 120, 150])
        start = rng.randrange(435, 960 - duration + 1)
        data.append(ScheduleRequest(f"SYN-J{i:06d}", f"Kegiatan sintetis {i}", kind,
                                    rng.randrange(10, 61), "F802", DEMO_DAY,
                                    start, start + duration, VALUE[kind], i))
    return data

def generate_search_entries(n):
    # Dua awalan untuk eksperimen yang menghasilkan sedikit/banyak jawaban.
    return [SearchEntry(f"SYN-C{i:06d}", f"{('Akuntansi' if i % 2 else 'Manajemen')} {i:06d}",
                        "course") for i in range(n)]
