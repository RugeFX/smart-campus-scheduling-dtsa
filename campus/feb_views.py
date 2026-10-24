"""Convert the active Excel tables into existing Colab input contracts.

No example data or new scheduling algorithm is supplied here.
"""
import pandas as pd
from .models import Room, ScheduleRequest, REGULAR_SLOTS, VALUE
from .hash_table import HashTableChaining


def available_weeks(data):
    dates = data["clean"]["jadwal_uts"]["tanggal"].dropna()
    return sorted({(int(d.isocalendar().year), int(d.isocalendar().week)) for d in dates})


def room_inputs(data, week):
    """Count occupied regular slots once per room/day, even for shared classes."""
    occupied = {}
    rejected = []
    for _, row in data["clean"]["jadwal_uts"].iterrows():
        if str(row["mode_ujian"]).strip().casefold() != "onsite":
            continue
        required = ["tanggal", "ruang", "mulai_menit", "selesai_menit"]
        if any(pd.isna(row[key]) for key in required) or row["mulai_menit"] >= row["selesai_menit"]:
            rejected.append(int(row["baris_excel"]))
            continue
        day = row["tanggal"]
        if (int(day.isocalendar().year), int(day.isocalendar().week)) != week or day.weekday() >= 5:
            continue
        key = str(row["ruang"])
        slots = occupied.setdefault(key, set())
        for index, (start, end) in enumerate(REGULAR_SLOTS):
            if row["mulai_menit"] < end and start < row["selesai_menit"]:
                slots.add((day.date().isoformat(), index))
    rooms, invalid = [], []
    frame = data["clean"]["ruang"]
    repeated = set(frame.loc[frame.duplicated("ruang", keep=False), "ruang"].dropna())
    for _, row in frame.iterrows():
        if pd.isna(row["ruang"]) or row["ruang"] in repeated or pd.isna(row["kapasitas_asumsi"]) or row["kapasitas_asumsi"] <= 0:
            invalid.append(int(row["baris_excel"]))
            continue
        key = str(row["ruang"])
        rooms.append(Room(key, int(row["kapasitas_asumsi"]), used_slots=len(occupied.get(key, set()))))
    return rooms, {"invalid_room_rows": invalid, "invalid_schedule_rows": rejected}


def room_search_table(data):
    table = HashTableChaining()
    for _, row in data["clean"]["ruang"].iterrows():
        key = row["ruang"]
        if pd.isna(key) or not str(key).strip() or table.contains(str(key)):
            raise ValueError("Kode ruang Excel kosong/berulang; periksa laporan data.")
        table.put(str(key), row.to_dict())
    return table


def scheduling_inputs(data, include_review=False):
    """Existing onsite exam rows -> one candidate per class, with provenance.

    Examination weight comes from Colab VALUE, not an invented Excel column.
    This is analysis only; co-located classes may belong to one shared session.
    """
    candidates, excluded = [], []
    seen = set()
    for key, detail in data["ingredients"]["kelas"]:
        reason = None
        if not key or not detail["name"]:
            reason = "Kode kelas/nama mata kuliah belum valid"
        elif str(detail["exam_mode"]).casefold() != "onsite":
            reason = "Online: tidak memakai ruang fisik"
        elif not detail["room_id"]:
            reason = "Ruang tidak tersedia"
        elif not detail["day"] or detail["start"] is None or detail["end"] is None:
            reason = "Tanggal/jam belum valid"
        elif not 0 <= detail["start"] < detail["end"] <= 1440:
            reason = "Urutan jam tidak valid"
        elif detail["participants"] is None or detail["participants"] <= 0:
            reason = "Jumlah peserta tidak valid"
        elif not key or key in seen:
            reason = "Kode kelas kosong/berulang"
        elif detail["needs_review"] and not include_review:
            reason = "Menunggu pemeriksaan durasi/ruang"
        if reason:
            excluded.append({"Kode kelas": key, "Baris Excel": detail["source"]["excel_row"], "Alasan": reason})
            continue
        seen.add(key)
        candidates.append(ScheduleRequest(key, detail["name"], "Examination", int(detail["participants"]),
            detail["room_id"], detail["day"], int(detail["start"]), int(detail["end"]), VALUE["Examination"]))
    return candidates, pd.DataFrame(excluded, columns=["Kode kelas", "Baris Excel", "Alasan"])


def queue_inputs(data):
    """All structurally valid exam rows, including online/review-marked rows.

    A queue orders requests; it does not allocate physical rooms or decide which
    exam is allowed. Arrival times are supplied explicitly by the simulation UI.
    """
    requests, excluded = [], []
    seen = set()
    for key, detail in data["ingredients"]["kelas"]:
        reason = None
        if not key or key in seen or not detail["name"]:
            reason = "Kode kelas/nama kosong atau kode berulang"
        elif not detail["day"] or detail["start"] is None or detail["end"] is None:
            reason = "Tanggal/jam belum valid"
        elif not 0 <= detail["start"] < detail["end"] <= 1440:
            reason = "Urutan jam tidak valid"
        elif detail["participants"] is None or detail["participants"] <= 0:
            reason = "Jumlah peserta tidak valid"
        if reason:
            excluded.append({"Kode kelas": key, "Baris Excel": detail["source"]["excel_row"], "Alasan": reason})
            continue
        seen.add(key)
        requests.append(ScheduleRequest(key, detail["name"], "Examination", int(detail["participants"]),
            detail["room_id"] or "", detail["day"], int(detail["start"]), int(detail["end"]), VALUE["Examination"]))
    return requests, pd.DataFrame(excluded, columns=["Kode kelas", "Baris Excel", "Alasan"])
