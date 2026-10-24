# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .hash_table import HashTableChaining

room_ids = [f"F{floor}{number:02d}" for floor in (7, 8) for number in range(1, 9)]

rooms = [Room(rid, 60) for rid in room_ids]

room_overrides = {
    "F708": Room("F708", 30, used_slots=4),
    "F705": Room("F705", 40, used_slots=7),
    "F701": Room("F701", 45, used_slots=8),
    "F802": Room("F802", 60, used_slots=9),
    "F807": Room("F807", 80, used_slots=12),
    "F805": Room("F805", 100, used_slots=14),
}

rooms = [room_overrides.get(r.room_id, r) for r in rooms]

courses = [
    Course("MGT92119", "Principles of Management", "INT"),
    Course("MGT12119", "Dasar-Dasar Manajemen", "NAS"),
    Course("ACC93105", "Cost Accounting", "INT"),
    Course("ACC13101", "Akuntansi Biaya", "NAS"),
    Course("ACC93106", "Management Accounting", "INT"),
    Course("ACC13102", "Akuntansi Manajerial", "NAS"),
    Course("DEMO-AUD", "Audit Kecurangan", "NAS"),
    Course("DEMO-EKO", "Ekonomi Mikro", "NAS"),
]

equivalent_pairs = [("MGT92119", "MGT12119"), ("ACC93105", "ACC13101"),
                    ("ACC93106", "ACC13102")]

lecturers = [SearchEntry("DOS-01", "Dosen Anonim A", "lecturer"),
             SearchEntry("DOS-02", "Dosen Anonim B", "lecturer")]

search_entries = [SearchEntry(c.course_code, c.name, "course") for c in courses] + lecturers

class_records = [
    ClassRecord("DEMO-K01", "MGT92119", 15, "DOS-01", "F705", DEMO_DAY,
                minutes("10:15"), minutes("12:45")),
    ClassRecord("DEMO-K02", "MGT12119", 20, "DOS-01", "F705", DEMO_DAY,
                minutes("10:15"), minutes("12:45")),
]

activity_rows = [
    ("J1", "Seminar HIMA", "Event", "07:15", "08:15", 20),
    ("J2", "Kelas pengganti 1 SKS", "Regular Class", "08:15", "09:05", 25),
    ("J3", "UTS Akuntansi Manajerial", "Examination", "07:15", "09:15", 35),
    ("J4", "Sosialisasi KRS", "Event", "09:15", "10:15", 30),
    ("J5", "UTS LAB Pengantar Akuntansi", "Practicum", "10:15", "11:45", 35),
    ("J6", "Kelas pengganti 2 SKS", "Regular Class", "11:00", "12:40", 25),
]

requests = [ScheduleRequest(rid, title, kind, people, "F802", DEMO_DAY,
                           minutes(start), minutes(end), VALUE[kind])
            for rid, title, kind, start, end, people in activity_rows]

candidate_schedules = list(requests)

def build_indexes():
    room_table, class_table = HashTableChaining(), HashTableChaining()
    equivalence_table, course_table = HashTableChaining(), HashTableChaining()
    for room in rooms:
        room_table.put(room.room_id, room)
    for record in class_records:
        class_table.put(record.class_code, record)
    for course in courses:
        course_table.put(course.course_code, course)
    for international, national in equivalent_pairs:
        equivalence_table.put(international, national)
        equivalence_table.put(national, international)
    return room_table, class_table, equivalence_table, course_table
