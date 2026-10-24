# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from copy import deepcopy
from datetime import date
import json
import pandas as pd
from .models import *
from .hash_table import HashTableChaining
from .heap import MinHeapPriorityQueue
from .trie import Trie, bilingual_autocomplete
from .avl import AVLTree
from .dp import optimize_schedule

@dataclass(frozen=True)
class MergedClassRecord(ClassRecord):
    source_ids: tuple = ()
    course_codes: tuple = ()

def merge_equivalent_classes(records, equivalence_table, room_table):
    """Gabung hanya pasangan eksplisit dua arah yang telah diverifikasi caller.

    Kelas dengan dosen kosong tidak digabung. ID asal disimpan agar hasil dapat
    ditelusuri, tidak dihitung dua kali, dan aman dipanggil ulang (idempoten).
    Tidak mengubah records, tabel pasangan, atau tabel ruang.
    """
    groups, seen = HashTableChaining(), HashTableChaining()
    for record in records:
        if not isinstance(record, ClassRecord) or not record.class_code:
            raise ValueError("Record/kode kelas tidak valid.")
        if type(record.participants) is not int or record.participants <= 0:
            raise ValueError("Peserta harus bilangan bulat positif.")
        if not record.day or not 0 <= record.start < record.end <= 1440:
            raise ValueError("Tanggal atau interval kelas tidak valid.")
        date.fromisoformat(record.day)
        if record.activity_type not in PRIORITY:
            raise ValueError("Kategori tidak dikenal.")
        room = room_table.get(record.room_id)
        if room is None or record.participants > room.capacity:
            raise ValueError(f"Ruang tidak tersedia/kapasitas kurang: {record.class_code}")
        origins = getattr(record, "source_ids", ()) or (record.class_code,)
        for identifier in origins:
            if not isinstance(identifier, str) or not identifier or seen.contains(identifier):
                raise ValueError("ID asal kosong/berulang; peserta berisiko dihitung ganda.")
            seen.put(identifier, True)
        codes = getattr(record, "course_codes", ()) or (record.course_code,)
        partner = equivalence_table.get(record.course_code)
        pair = tuple(sorted((record.course_code, partner))) if (
            isinstance(partner, str) and partner != record.course_code and
            equivalence_table.get(partner) == record.course_code) else (record.course_code,)
        identity = [pair, record.day, record.start, record.end, record.room_id,
                    record.lecturer_id, record.activity_type]
        # Tanpa dosen atau pasangan eksplisit, setiap record tetap terpisah.
        if len(pair) != 2 or not record.lecturer_id:
            identity.append(record.class_code)
        key = json.dumps(identity, ensure_ascii=False)
        batch = groups.get(key)
        if batch is None:
            batch = []
            groups.put(key, batch)
        batch.append((record, tuple(origins), tuple(codes), pair))
    result = []
    for _, group in groups.items():
        all_codes = tuple(sorted({code for _, _, codes, _ in group for code in codes}))
        pair = group[0][3]
        batches = [group] if len(pair) == 2 and set(pair) <= set(all_codes) else [[entry] for entry in group]
        for batch in batches:
            first = batch[0][0]
            origins = tuple(sorted(origin for _, ids, _, _ in batch for origin in ids))
            codes = tuple(sorted({code for _, _, codes, _ in batch for code in codes}))
            people = sum(record.participants for record, _, _, _ in batch)
            if people > room_table.get(first.room_id).capacity:
                raise ValueError(f"Gabungan {origins} melebihi kapasitas ruang.")
            identifier = first.class_code if len(batch) == 1 else "MERGE:" + json.dumps(origins)
            result.append(MergedClassRecord(identifier, first.course_code, people,
                first.lecturer_id, first.room_id, first.day, first.start, first.end,
                first.activity_type, origins, codes))
    if len({r.class_code for r in result}) != len(result):
        raise ValueError("Kode hasil gabungan bertabrakan dengan kode kelas lain.")
    return result

def validate_room_registry(room_table, usage_avl, capacity_avl=None):
    if usage_avl.index != "utilization" or (capacity_avl is not None and capacity_avl.index != "capacity"):
        raise ValueError("Jenis indeks AVL tidak sesuai.")
    usage_avl.validate()
    if capacity_avl is not None:
        capacity_avl.validate()
    for key, room in room_table.items():
        if key != room.room_id or type(room.capacity) is not int or room.capacity <= 0:
            raise ValueError("Identitas/kapasitas ruang tidak valid.")
        if type(room.used_slots) is not int or not 0 <= room.used_slots <= WEEKLY_SLOTS:
            raise ValueError("Pemakaian ruang harus 0..15 slot.")
    for tree in [usage_avl] + ([capacity_avl] if capacity_avl is not None else []):
        entries = tree.inorder()
        if len(entries) != len(room_table):
            raise ValueError("Hash dan payload kedua indeks AVL tidak konsisten.")
        visited = HashTableChaining()
        for room in entries:
            if visited.contains(room.room_id) or room_table.get(room.room_id) != room:
                raise ValueError("Hash dan payload kedua indeks AVL tidak konsisten.")
            visited.put(room.room_id, True)
    return True

def stage_room_updates(room_table, usage_avl, capacity_avl, updates):
    """Salin registry untuk transaksi: validasi/gagal tidak merusak state asal.

    Biaya salinan/validasi O(R + bucket), berbeda dari delete/insert AVL O(log R).
    """
    validate_room_registry(room_table, usage_avl, capacity_avl)
    table, usage, capacity = deepcopy((room_table, usage_avl, capacity_avl))
    for room_id, used_slots in updates:
        old = table.get(room_id)
        if old is None:
            raise KeyError(f"Ruang tidak ditemukan: {room_id}")
        if type(used_slots) is not int or not 0 <= used_slots <= WEEKLY_SLOTS:
            raise ValueError("Pemakaian ruang harus bilangan bulat 0..15.")
        new = replace(old, used_slots=used_slots)
        if not usage.delete((old.utilization, room_id)):
            raise ValueError("Key pemakaian lama tidak ditemukan.")
        usage.insert(new)
        if capacity is not None:
            if not capacity.delete((old.capacity, room_id)):
                raise ValueError("Key kapasitas lama tidak ditemukan.")
            capacity.insert(new)
        table.put(room_id, new)
    validate_room_registry(table, usage, capacity)
    return table, usage, capacity

def commit_room_registry(room_table, usage_avl, capacity_avl, staged):
    table, usage, capacity = staged
    room_table.buckets, room_table.size = table.buckets, table.size
    room_table.probes = table.probes
    usage_avl.root, usage_avl.rotations = usage.root, usage.rotations
    if capacity_avl is not None:
        capacity_avl.root, capacity_avl.rotations = capacity.root, capacity.rotations

def update_room_usage(room_table, usage_avl, room_id, new_used_slots, capacity_avl=None):
    """Kompatibel 4 argumen; berikan capacity_avl agar payload kedua indeks ikut baru."""
    staged = stage_room_updates(room_table, usage_avl, capacity_avl, [(room_id, new_used_slots)])
    commit_room_registry(room_table, usage_avl, capacity_avl, staged)
    return room_table.get(room_id)

def touched_regular_slots(request):
    day = date.fromisoformat(request.day)
    if day.weekday() >= 5:
        return set()
    return {(request.day, index) for index, (start, end) in enumerate(REGULAR_SLOTS)
            if request.start < end and start < request.end}

def schedule_across_rooms(requests, room_table, capacity_avl, usage_avl,
                          existing_bookings=(), occupied_slots=None,
                          allow_alternative_rooms=True, required_room_types=None):
    """Simulasi alokasi satu minggu: PQ -> batch DP per ruang/hari -> retry.

    Booking yang diterima tidak digeser pada putaran berikutnya. Tiap pasangan
    (request_id, room_id) dicoba paling banyak sekali. Bukan optimum global;
    prioritas mengatur urutan antrean, DP memaksimalkan value dalam batch.
    Fasilitas hanya diperiksa bila required_room_types diberikan secara eksplisit.
    """
    validate_room_registry(room_table, usage_avl, capacity_avl)
    requests, existing = list(requests), list(existing_bookings)
    seen = HashTableChaining()
    weeks = set()
    for request in requests + existing:
        # Validasi kontrak Heap tanpa mengubah registry.
        MinHeapPriorityQueue()._check_request(request)
        if seen.contains(request.request_id):
            raise ValueError("ID permintaan/booking berulang.")
        seen.put(request.request_id, True)
        if type(request.participants) is not int or request.participants <= 0 or request.value < 0:
            raise ValueError("Peserta/nilai permintaan tidak valid.")
        day = date.fromisoformat(request.day)
        weeks.add(tuple(day.isocalendar()[:2]))
    if len(weeks) > 1:
        raise ValueError("Pemakaian /15 memerlukan input dari satu minggu ISO.")
    occupied, known, calendar = HashTableChaining(), HashTableChaining(), HashTableChaining()
    for room_id, room in room_table.items():
        occupied.put(room_id, set())
        known.put(room_id, set())
    for booking in existing:
        room = room_table.get(booking.room_id)
        if room is None or booking.participants > room.capacity:
            raise ValueError("Booking awal memakai ruang/kapasitas tidak valid.")
        key = json.dumps((booking.room_id, booking.day))
        batch = calendar.get(key) or []
        if any(booking.start < other.end and other.start < booking.end for other in batch):
            raise ValueError("Booking awal saling bertabrakan.")
        calendar.put(key, batch + [booking])
        known.get(booking.room_id).update(touched_regular_slots(booking))
    for room_id, room in room_table.items():
        supplied = set(occupied_slots.get(room_id, ())) if occupied_slots is not None else set(known.get(room_id))
        if not known.get(room_id) <= supplied or len(supplied) != room.used_slots:
            raise ValueError("Butuh posisi slot awal yang sesuai used_slots, bukan hanya totalnya.")
        for day_text, index in supplied:
            day = date.fromisoformat(day_text)
            if day.weekday() >= 5 or type(index) is not int or not 0 <= index < len(REGULAR_SLOTS):
                raise ValueError("Posisi slot awal tidak valid.")
            if weeks and tuple(day.isocalendar()[:2]) not in weeks:
                raise ValueError("Slot awal berasal dari minggu berbeda.")
        occupied.put(room_id, supplied)

    queues = HashTableChaining()
    for request in requests:
        queue = queues.get(request.day)
        if queue is None:
            queue = MinHeapPriorityQueue()
            queues.put(request.day, queue)
        queue.push(request)
    pending = []
    for day, queue in sorted(queues.items()):
        while queue:
            pending.append(queue.pop())
    priority_order = [r.request_id for r in pending]
    room_order = capacity_avl.inorder()
    tried, reasons = HashTableChaining(), HashTableChaining()
    for request in requests:
        tried.put(request.request_id, [])
    attempts, bookings, rejected = [], [], []
    while pending:
        batches = HashTableChaining()
        retry = []
        for request in pending:
            preferred = room_table.get(request.room_id)
            candidates = ([preferred] if preferred else []) + [r for r in room_order if r.room_id != request.room_id]
            if not allow_alternative_rooms:
                candidates = candidates[:1] if preferred or not request.room_id else []
            selected_room = None
            for room in candidates:
                history = tried.get(request.request_id)
                if room.room_id in history:
                    continue
                history.append(room.room_id)
                reason = None
                if room.capacity < request.participants:
                    reason = "Kapasitas kurang"
                required = required_room_types.get(request.request_id) if required_room_types else None
                if reason is None and required and room.room_type != required:
                    reason = "Jenis/fasilitas ruang tidak sesuai atau tidak diketahui"
                batch_key = json.dumps((room.room_id, request.day))
                if reason is None and any(request.start < other.end and other.start < request.end
                                          for other in calendar.get(batch_key) or []):
                    reason = "Bertabrakan dengan booking yang sudah diterima"
                if reason is None and touched_regular_slots(request) & (occupied.get(room.room_id) - known.get(room.room_id)):
                    reason = "Slot awal terpakai, interval rinci belum diketahui"
                if reason:
                    attempts.append({"request_id": request.request_id, "room_id": room.room_id,
                                     "status": "DITOLAK", "reason": reason})
                    reasons.put(request.request_id, reason)
                    continue
                selected_room = room
                batch = batches.get(batch_key) or []
                batch.append(replace(request, room_id=room.room_id))
                batches.put(batch_key, batch)
                break
            if selected_room is None:
                rejected.append({"request": request, "reason": reasons.get(request.request_id) or "Tidak ada ruang yang dapat dicoba"})
        for batch_key, batch in batches.items():
            _, ids = optimize_schedule(batch)
            chosen = set(ids)
            for request in batch:
                accepted = request.request_id in chosen
                attempts.append({"request_id": request.request_id, "room_id": request.room_id,
                    "status": "DITERIMA" if accepted else "DITOLAK",
                    "reason": "Terpilih DP batch" if accepted else "Tidak terpilih DP batch"})
                if accepted:
                    bookings.append(request)
                    calendar.put(batch_key, (calendar.get(batch_key) or []) + [request])
                    slots = touched_regular_slots(request)
                    occupied.get(request.room_id).update(slots)
                    known.get(request.room_id).update(slots)
                else:
                    reasons.put(request.request_id, "Tidak terpilih DP batch")
                    retry.append(request)
        pending = retry
    updates = [(room_id, len(slots)) for room_id, slots in occupied.items()]
    staged = stage_room_updates(room_table, usage_avl, capacity_avl, updates)
    commit_room_registry(room_table, usage_avl, capacity_avl, staged)
    return {"bookings": bookings, "rejected": rejected, "attempts": attempts,
            "tried_rooms": tried, "priority_order": priority_order,
            "total_value": sum(r.value for r in bookings), "occupied_slots": occupied,
            "limits": ["Simulasi satu minggu; bukan perubahan jadwal Excel.",
                       "DP optimal per batch ruang/hari, bukan optimum global beberapa ruang.",
                       "Konflik dosen/mahasiswa belum dimodelkan; fasilitas memerlukan metadata eksplisit."]}

def make_room_registry(room_list):
    table, capacity, usage = HashTableChaining(), AVLTree("capacity"), AVLTree("utilization")
    for room in room_list:
        if table.contains(room.room_id):
            raise ValueError("ID ruang berulang.")
        table.put(room.room_id, room)
        capacity.insert(room)
        usage.insert(room)
    validate_room_registry(table, usage, capacity)
    return table, capacity, usage

def simulate_feb_allocation(clean_data, ingredients):
    """Excel sebagai permintaan simulasi, bukan penulisan ulang jadwal resmi.

    Durasi/ruang bermasalah dan online dilaporkan terpisah. Kapasitas asumsi dan
    jenis ruang tidak diketahui diberi label; pasangan belum resmi tidak digabung.
    """
    room_list = []
    invalid_rooms = []
    for _, row in clean_data["ruang"].iterrows():
        if pd.isna(row["ruang"]) or pd.isna(row["kapasitas_asumsi"]) or row["kapasitas_asumsi"] <= 0:
            invalid_rooms.append(int(row["baris_excel"]))
        else:
            room_list.append(Room(str(row["ruang"]), int(row["kapasitas_asumsi"]), "Unknown", 0))
    candidates, excluded, provenance = [], [], HashTableChaining()
    for code, detail in ingredients["kelas"]:
        reason = None
        if str(detail["exam_mode"]).casefold() != "onsite": reason = "Online: tidak memakai ruang fisik"
        elif detail["needs_review"]: reason = "Durasi/ruang perlu pemeriksaan"
        elif not detail["day"] or detail["start"] is None or detail["end"] is None: reason = "Tanggal/jam belum valid"
        elif not 0 <= detail["start"] < detail["end"] <= 1440: reason = "Interval tidak valid"
        elif detail["participants"] is None or detail["participants"] <= 0: reason = "Peserta tidak valid"
        if reason:
            excluded.append({"class_code": code, "excel_row": detail["source"]["excel_row"], "reason": reason})
            continue
        candidates.append(ScheduleRequest(code, detail["name"], "Examination", int(detail["participants"]),
            detail["room_id"] or "", detail["day"], int(detail["start"]), int(detail["end"]), VALUE["Examination"]))
        provenance.put(code, detail["source"])
    by_week = HashTableChaining()
    for request in candidates:
        key = str(tuple(date.fromisoformat(request.day).isocalendar()[:2]))
        by_week.put(key, (by_week.get(key) or []) + [request])
    reports = []
    for week, batch in sorted(by_week.items()):
        registry = make_room_registry(room_list)
        report = schedule_across_rooms(batch, *registry)
        report["week"] = week
        report["registry"] = registry
        reports.append(report)
    return {"weeks": reports, "excluded": excluded, "invalid_room_rows": invalid_rooms,
            "provenance": provenance, "pairs_merged": 0,
            "assumptions": "Simulasi mulai ruang kosong; kapasitas asumsi Excel, fasilitas belum diketahui, pasangan belum resmi tidak digabung."}
