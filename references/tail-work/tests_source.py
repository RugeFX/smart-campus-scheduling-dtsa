def test_t07():
    trie = Trie()
    for code, name in [("ACC13101", "Akuntansi Biaya"), ("ACC13102", "Akuntansi Manajerial")]:
        trie.insert(name, code)
    trie.insert("AKUNTANSI BIAYA", "ACC13101")
    assert set(trie.autocomplete(" ak ")) == {"ACC13101", "ACC13102"}
    assert len(trie.autocomplete("ak")) == 2


def test_t08():
    trie = Trie()
    trie.insert("Akuntansi", "ACC")
    assert trie.autocomplete("tidak-ada") == []
    assert trie.search("Akun") == []
    assert trie.search("Akuntansi") == ["ACC"]


def test_t09():
    trie = Trie()
    trie.insert("Dasar-Dasar Manajemen", "MGT12119")
    eq, catalog = HashTableChaining(), HashTableChaining()
    eq.put("MGT12119", "MGT92119")
    eq.put("MGT92119", "MGT12119")
    for code in ["MGT12119", "MGT92119"]:
        catalog.put(code, True)
    assert set(bilingual_autocomplete(trie, "Dasar", eq, catalog)) == {"MGT12119", "MGT92119"}


def test_rotation_sequence(values):
    tree = AVLTree()
    for value in values:
        tree.insert(Room(f"R-{value}", value))
        assert tree.validate()
    assert tree.root.key[0] == 20 and tree.rotations > 0


def test_t10():
    test_rotation_sequence([10, 20, 30])
    test_rotation_sequence([30, 20, 10])


def test_t11():
    test_rotation_sequence([30, 10, 20])
    test_rotation_sequence([10, 30, 20])


def test_t12():
    tree = AVLTree()
    for room in [Room("F708", 30), Room("F705", 40), Room("F701", 45), Room("A", 40), Room("BIG", 100)]:
        tree.insert(room)
    assert tree.ceiling_capacity(35).room_id == "A"  # Tie dipecahkan room_id.
    assert tree.ceiling_capacity(101) is None
    assert tree.validate()
    original = AVLTree()
    for room in rooms:
        original.insert(room)
    assert original.ceiling_capacity(35).room_id == "F705"


def test_t13():
    assert verify_dp_random_cases(100, SEED).startswith("100 kasus")


def test_t14():
    batch = [heap_test_request(str(i), start=435 + 60 * i) for i in range(4)]
    assert optimize_schedule(batch) == (40, ["0", "1", "2", "3"])
    assert optimize_schedule([]) == (0, [])
    assert no_overlap(batch)


def test_t15():
    batch = [replace(heap_test_request(str(i)), value=i + 1) for i in range(5)]
    assert optimize_schedule(batch) == (5, ["4"])
    for invalid in [[batch[0], batch[0]], [batch[0], replace(batch[1], room_id="OTHER")],
                    [batch[0], replace(batch[1], day="2026-10-09")]]:
        try:
            optimize_schedule(invalid)
        except ValueError:
            continue
        raise AssertionError("DP harus menolak ID berulang/lintas ruang atau hari.")


def test_t16():
    registry = make_room_registry([Room("F802", 60)])
    report = schedule_across_rooms(requests, *registry, allow_alternative_rooms=False)
    assert report["priority_order"] == ["J3", "J5", "J2", "J6", "J1", "J4"]
    assert report["total_value"] == 19
    assert {r.request_id for r in report["bookings"]} == {"J3", "J4", "J5"}
    assert registry[0].get("F802").used_slots == 2  # Bukan +=3 kegiatan.
    assert validate_room_registry(registry[0], registry[2], registry[1])
    assert len(report["bookings"]) + len(report["rejected"]) == len(requests)


def test_t17():
    batch = [replace(heap_test_request("A"), room_id="R1"),
             replace(heap_test_request("B"), room_id="R1")]
    registry = make_room_registry([Room("R1", 30), Room("R2", 40)])
    report = schedule_across_rooms(batch, *registry)
    assert len(report["bookings"]) == 2 and not report["rejected"]
    pairs = [(a["request_id"], a["room_id"]) for a in report["attempts"]]
    assert len(pairs) == len(set(pairs)) <= 4
    # Ruang habis: tetap berhenti dengan laporan penolakan, bukan loop antrean.
    third = replace(heap_test_request("C"), room_id="R1")
    registry = make_room_registry([Room("R1", 30), Room("R2", 40)])
    report = schedule_across_rooms(batch + [third], *registry)
    assert len(report["bookings"]) == 2 and len(report["rejected"]) == 1
    assert len(report["attempts"]) <= 6
    assert sum(len(ids) for _, ids in report["tried_rooms"].items()) <= 6


def test_t18():
    table, _, eq, _ = build_indexes()
    merged = merge_equivalent_classes(class_records, eq, table)
    assert len(merged) == 1 and merged[0].participants == 35
    assert set(merged[0].source_ids) == {"DEMO-K01", "DEMO-K02"}
    assert merge_equivalent_classes(merged, eq, table) == merged
    try:
        merge_equivalent_classes([class_records[0], replace(class_records[1], participants=30)], eq, table)
    except ValueError:
        pass
    else:
        raise AssertionError("Gabungan 45 peserta melebihi kapasitas 40.")
    for changed in [replace(class_records[1], lecturer_id="OTHER"),
                    replace(class_records[1], day="2026-10-09"),
                    replace(class_records[1], start=500, end=600),
                    replace(class_records[1], activity_type="Event")]:
        assert len(merge_equivalent_classes([class_records[0], changed], eq, table)) == 2


def test_avl_delete_and_atomic_updates():
    rng = Random(SEED)
    tree = AVLTree()
    values = list(range(1, 201))
    rng.shuffle(values)
    for value in values:
        tree.insert(Room(f"R-{value}", value))
    rng.shuffle(values)
    remaining = set(values)
    for value in values:
        assert tree.delete((value, f"R-{value}"))
        remaining.remove(value)
        assert tree.validate()
        assert {r.capacity for r in tree.inorder()} == remaining
        assert not tree.delete((value, f"R-{value}"))
    assert tree.root is None
    registry = make_room_registry([Room("R", 40, used_slots=9)])
    old_key = (9 / 15, "R")
    update_room_usage(registry[0], registry[2], "R", 10, registry[1])
    assert registry[0].get("R").used_slots == 10
    assert old_key not in [(r.utilization, r.room_id) for r in registry[2].inorder()]
    assert validate_room_registry(registry[0], registry[2], registry[1])
    for invalid in [-1, 16, True, 1.5]:
        before = (list(registry[0].items()), registry[1].root, registry[2].root)
        try:
            update_room_usage(registry[0], registry[2], "R", invalid, registry[1])
        except ValueError:
            assert before == (list(registry[0].items()), registry[1].root, registry[2].root)
        else:
            raise AssertionError("Update tidak valid harus ditolak tanpa mutasi.")
    # Simulasikan kegagalan insert pada salinan untuk memeriksa transaksi.
    class FailingUsageAVL(AVLTree):
        def insert(self, key, room=None):
            target = key if room is None else room
            if target.used_slots == 11:
                raise RuntimeError("Kegagalan uji yang disengaja")
            return super().insert(key, room)
    bad = FailingUsageAVL("utilization")
    bad.insert(registry[0].get("R"))
    before = (registry[0].get("R"), registry[1].root, bad.root)
    try:
        update_room_usage(registry[0], bad, "R", 11, registry[1])
    except RuntimeError:
        assert before == (registry[0].get("R"), registry[1].root, bad.root)
    else:
        raise AssertionError("Uji kegagalan tidak berjalan.")


def test_integration_boundaries():
    first = replace(heap_test_request("A", start=435), end=495, room_id="R")
    adjacent = replace(first, request_id="B", start=495, end=555)
    registry = make_room_registry([Room("R", 40)])
    report = schedule_across_rooms([first, adjacent], *registry)
    assert len(report["bookings"]) == 2 and registry[0].get("R").used_slots == 1
    # Existing exact interval permits a non-overlapping booking in the same slot.
    registry = make_room_registry([Room("R", 40, used_slots=1)])
    report = schedule_across_rooms([adjacent], *registry, existing_bookings=[first])
    assert len(report["bookings"]) == 1 and registry[0].get("R").used_slots == 1
    # An unknown interval in an occupied slot is conservatively blocked.
    registry = make_room_registry([Room("R", 40, used_slots=1)])
    report = schedule_across_rooms([adjacent], *registry,
        occupied_slots={"R": {(first.day, 0)}})
    assert not report["bookings"] and len(report["rejected"]) == 1
    for batch in [[first, first], [first, replace(adjacent, day="2026-10-19")]]:
        registry = make_room_registry([Room("R", 40)])
        try:
            schedule_across_rooms(batch, *registry)
        except ValueError:
            assert registry[0].get("R").used_slots == 0
        else:
            raise AssertionError("ID berulang/lintas minggu harus ditolak.")
    registry = make_room_registry([Room("R", 40)])
    report = schedule_across_rooms([first], *registry, required_room_types={"A": "Laboratory"})
    assert not report["bookings"] and "fasilitas" in report["rejected"][0]["reason"]
    empty = schedule_across_rooms([], *make_room_registry([]))
    assert empty["bookings"] == [] and empty["rejected"] == []


TEST_IDS = [f"T{i:02d}" for i in range(1, 19)]
TEST_RUNNERS = {"T01": test_t01, "T02": test_t02, "T03": test_t03,
                "T04": test_t04, "T05": test_t05, "T06": test_t06,
                "T07": test_t07, "T08": test_t08, "T09": test_t09,
                "T10": test_t10, "T11": test_t11, "T12": test_t12,
                "T13": test_t13, "T14": test_t14, "T15": test_t15,
                "T16": test_t16, "T17": test_t17, "T18": test_t18}
RUN_TESTS = True


def run_test_plan():
    report = []
    for test_id in TEST_IDS:
        action = TEST_RUNNERS.get(test_id)
        if action is None:
            report.append((test_id, "BELUM DIISI", "Fungsi uji belum didaftarkan."))
            continue
        try:
            action()
        except NotImplementedError:
            report.append((test_id, "BELUM DIIMPLEMENTASIKAN", "Algoritma masih TODO."))
        except Exception as error:
            report.append((test_id, "GAGAL", f"{type(error).__name__}: {error}"))
        else:
            report.append((test_id, "LULUS", ""))
    return report


if RUN_TESTS:
    test_report = run_test_plan()
    for row in test_report:
        print(*row, sep=" | ")
    assert all(status == "LULUS" for _, status, _ in test_report), "Periksa pengujian yang gagal."
    test_avl_delete_and_atomic_updates()
    test_integration_boundaries()
    print("Tambahan: delete AVL acak, transaksi gagal, slot unik, booking awal, fasilitas, batas minggu: LULUS.")
