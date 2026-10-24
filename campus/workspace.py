"""Session adapter: Excel provenance and lifecycle around unchanged Colab services."""
from dataclasses import replace
from datetime import date
from .data import build_search_indexes
from .feb_views import room_inputs, scheduling_inputs
from .hash_table import HashTableChaining
from .models import ClassRecord, ScheduleRequest, VALUE
from .search_pairs import pair_indexes
from .service import (make_room_registry, merge_equivalent_classes, schedule_across_rooms,
                      touched_regular_slots, update_room_usage, validate_room_registry)


def week_of(day):
    return tuple(date.fromisoformat(day).isocalendar()[:2])


class AllocationWorkspace:
    """One simulation week. Source workbook remains unchanged."""
    def __init__(self, data, week):
        self.data = data
        self.week = week
        rooms, self.room_notes = room_inputs(data, week)
        self.registry = make_room_registry([replace(room, used_slots=0, room_type="Unknown") for room in rooms])
        self.bookings = []
        self.provenance = {}
        self.reports = []
        self.events = []

    @property
    def reserved_class_ids(self):
        return {source for request in self.bookings for source in self.provenance[request.request_id]}

    def candidates(self, include_review=False):
        candidates, excluded = scheduling_inputs(self.data, include_review)
        return [r for r in candidates if week_of(r.day) == self.week], excluded

    def prepare(self, codes, confirmed_pairs=(), include_review=False):
        candidates, _ = self.candidates(include_review)
        lookup = {r.request_id: r for r in candidates}
        codes = list(codes)
        if len(codes) != len(set(codes)):
            raise ValueError("Kelas dipilih berulang.")
        if any(code not in lookup for code in codes):
            raise ValueError("Pilihan memuat kelas yang bukan kandidat Excel pada minggu ini.")
        if set(codes) & self.reserved_class_ids:
            raise ValueError("Sebagian kelas sudah dialokasikan. Batalkan alokasinya untuk mencoba ulang.")
        batch = [lookup[code] for code in codes]
        origins = {r.request_id: (r.request_id,) for r in batch}
        if not confirmed_pairs:
            return batch, origins
        indexes = build_search_indexes(self.data["ingredients"])
        _, accepted, _ = pair_indexes(self.data, indexes["courses"])
        valid = {(r["Kode INT"], r["Kode NAS"]) for _, r in accepted.iterrows()}
        pairs = HashTableChaining()
        for pair in confirmed_pairs:
            if tuple(pair) not in valid:
                raise ValueError("Pasangan harus berasal dari relasi Excel yang lengkap dan tidak ambigu.")
            a, b = pair
            pairs.put(a, b)
            pairs.put(b, a)
        details = dict(self.data["ingredients"]["kelas"])
        records, untouched = [], []
        for request in batch:
            detail = details[request.request_id]
            room = self.registry[0].get(request.room_id)
            if not pairs.contains(detail["course_code"]) or room is None or request.participants > room.capacity:
                untouched.append(request)
                continue
            records.append(ClassRecord(request.request_id, detail["course_code"], request.participants,
                detail["lecturer_id"], request.room_id, request.day, request.start, request.end, request.activity_type))
        merged = merge_equivalent_classes(records, pairs, self.registry[0])
        result = list(untouched)
        for record in merged:
            origins[record.class_code] = record.source_ids
            names = list(dict.fromkeys(details[code]["name"] for code in record.source_ids))
            result.append(ScheduleRequest(record.class_code, " / ".join(names), record.activity_type,
                record.participants, record.room_id, record.day, record.start, record.end, VALUE[record.activity_type]))
        # Preserve the earliest source position after aggregation for FIFO ties.
        position = {code: i for i, code in enumerate(codes)}
        result.sort(key=lambda r: min(position[code] for code in origins[r.request_id]))
        return result, origins

    def allocate(self, codes, *, confirmed_pairs=(), include_review=False, alternatives=True):
        prepared, origins = self.prepare(codes, confirmed_pairs, include_review)
        if not prepared:
            raise ValueError("Pilih minimal satu kandidat kelas Excel yang belum dialokasikan.")
        report = schedule_across_rooms(prepared, *self.registry, existing_bookings=self.bookings,
                                       allow_alternative_rooms=alternatives)
        self.bookings.extend(report["bookings"])
        self.provenance.update(origins)
        report["provenance"] = origins
        self.reports.append(report)
        self.events.append({"Tindakan": "Alokasi", "Diterima": len(report["bookings"]),
                            "Ditolak": len(report["rejected"]), "Detail": f"{len(codes)} kelas Excel"})
        self.validate()
        return report

    def cancel(self, request_id):
        target = next((r for r in self.bookings if r.request_id == request_id), None)
        if target is None:
            raise ValueError("Alokasi tidak ditemukan.")
        remaining = [r for r in self.bookings if r.request_id != request_id]
        slots = set()
        for request in remaining:
            if request.room_id == target.room_id:
                slots.update(touched_regular_slots(request))
        update_room_usage(self.registry[0], self.registry[2], target.room_id, len(slots), self.registry[1])
        self.bookings = remaining
        self.events.append({"Tindakan": "Pembatalan", "Diterima": 0, "Ditolak": 0,
                            "Detail": ", ".join(self.provenance[target.request_id])})
        self.validate()

    def validate(self):
        return validate_room_registry(self.registry[0], self.registry[2], self.registry[1])

    def source_rows(self, request):
        ids = self.provenance.get(request.request_id, (request.request_id,))
        return self.data["display"][self.data["display"]["Kode kelas"].isin(ids)].copy()
