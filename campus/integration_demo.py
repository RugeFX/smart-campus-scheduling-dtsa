# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .demo import *
from .service import *

def demo_integration():
    table, classes, pairs, catalog = build_indexes()
    names = Trie()
    for course in courses:
        names.insert(course.name, course.course_code)
    assert set(bilingual_autocomplete(names, "Dasar", pairs, catalog)) == {"MGT12119", "MGT92119"}
    merged = merge_equivalent_classes([record for _, record in classes.items()], pairs, table)
    assert len(merged) == 1 and merged[0].participants == 35
    # Registry kosong untuk simulasi J1–J6; bukan reset pemakaian kampus nyata.
    registry = make_room_registry([Room("F802", 60)])
    report = schedule_across_rooms(requests, *registry, allow_alternative_rooms=False)
    assert report["total_value"] == 19
    assert {r.request_id for r in report["bookings"]} == {"J3", "J4", "J5"}
    assert registry[0].get("F802").used_slots == 2
    print("Integrasi fixture: pasangan 15+20=35, DP=19, slot unik F802=2.")
    return report
