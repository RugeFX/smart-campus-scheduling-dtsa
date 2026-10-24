# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from dataclasses import dataclass, replace
from typing import Optional
from random import Random
from itertools import combinations
from time import perf_counter
from statistics import median
import csv
import tracemalloc

PRIORITY = {"Examination": 1, "Practicum": 2, "Regular Class": 3, "Event": 4}

VALUE = {"Examination": 10, "Practicum": 7, "Regular Class": 5, "Event": 2}

WEEKLY_SLOTS = 15

AGING_STEP_MINUTES = None

DEMO_DAY = "2026-10-08"  # Hari contoh, bukan hasil impor jadwal resmi.

SEED = 42

def minutes(hhmm: str) -> int:
    hour, minute = map(int, hhmm.replace(".", ":").split(":"))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("Waktu harus berada dalam 00.00–23.59.")
    return hour * 60 + minute

REGULAR_SLOTS = [(minutes(a), minutes(b)) for a, b in
                 [("07:15", "09:45"), ("10:15", "12:45"), ("13:15", "15:45")]]

@dataclass(frozen=True)
class Room:
    room_id: str
    capacity: int
    room_type: str = "Classroom"
    used_slots: int = 0
    @property
    def utilization(self):
        return self.used_slots / WEEKLY_SLOTS

@dataclass(frozen=True)
class Course:
    course_code: str
    name: str
    language: str  # INT atau NAS

@dataclass(frozen=True)
class ClassRecord:
    class_code: str
    course_code: str
    participants: int
    lecturer_id: str
    room_id: str
    day: str
    start: int
    end: int
    activity_type: str = "Regular Class"

@dataclass(frozen=True)
class SearchEntry:
    entry_id: str
    name: str
    kind: str  # course atau lecturer

@dataclass(frozen=True)
class ScheduleRequest:
    request_id: str
    title: str
    activity_type: str
    participants: int
    room_id: str
    day: str
    start: int
    end: int
    value: int
    submitted_at: int = 0  # Menit pada jam simulasi antrean; terpisah dari jam kegiatan.
    @property
    def priority(self):
        return PRIORITY[self.activity_type]
