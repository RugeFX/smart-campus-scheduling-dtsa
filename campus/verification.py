# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .sorting import manual_merge_sort
from .heap import MaxHeap, heap_sort
from .hash_table import HashTableLinearProbing
from .greedy import *
from .uas_examples import *
from .models import *
from .demo import *
from .heap_tests import *
from .notebook_tests import test_t04, test_t05, test_t06
from .service import *
from .avl import AVLTree
from .trie import Trie, bilingual_autocomplete
from .dp import *

from .mst import *
def test_t20():
    rng=Random(42)
    values=[rng.randrange(-100,101) for _ in range(150)]
    heap=MaxHeap(values,trace=True)
    assert heap.is_heap() and heap.trace
    assert [heap.pop() for _ in range(len(heap))]==sorted(values,reverse=True)
    assert heap_sort(values)==sorted(values)
    heap=MaxHeap([2,7,4,1]);heap.change_key(3,20);assert heap.peek()==20 and heap.validate()
    heap.change_key(0,-1);assert heap.peek()==7 and heap.validate()
    heap.delete(1);assert heap.validate()

def test_t21():
    a,b=heap_test_request("A",start=900),heap_test_request("B",start=435)
    q=MinHeapPriorityQueue(trace=True);q.build([a,b])
    assert q.peek() is a  # FIFO per prioritas, bukan jam kegiatan.
    q.change_priority("A",4);assert q.peek() is b
    q.change_priority("A",1);assert q.peek() is a
    assert a.priority==1 and a.start==900 and q.entries[q.position_map.get("A")][2]==0
    q.apply_aging(90,30);assert q.validate() and q.peek() is a
    before=list(q.entries)
    try:q.change_priority("A",0)
    except ValueError:pass
    else:raise AssertionError("Prioritas tidak valid diterima.")
    assert q.entries==before
    q.remove("A");assert q.peek() is b and q.validate() and q.trace

def test_t22():
    table=HashTableLinearProbing(8,0.95)
    for key,value in [("AA",None),("AI",2),("AQ",3)]:table.put(key,value)
    assert table.contains("AA") and table.get("AA") is None and table.collisions>0
    assert table.delete("AA") and table.tombstones==1
    assert table.get("AI")==2 and table.get("AQ")==3
    table.put("AI",7);assert len(table)==2 and table.get("AI")==7
    table.put("AY",8);assert table.tombstones==0 and table.validate()
    oracle={"AI":7,"AQ":3,"AY":8}
    rng=Random(42)
    for _ in range(500):
        key=f"K-{rng.randrange(50)}"
        if rng.random()<0.35:assert table.delete(key)==(key in oracle);oracle.pop(key,None)
        else:
            value=rng.randrange(1000);table.put(key,value);oracle[key]=value
        assert table.validate() and dict(table.items())==oracle
    assert table.rehashes>0

def test_t23():
    trie=Trie()
    trie.insert("Alpha","A");trie.insert("ALPHA","B");trie.insert("Alphabet","A")
    assert trie.delete(" alpha ","A") and trie.search("alpha")==["B"]
    assert set(trie.autocomplete("alp"))=={"A","B"}
    assert not trie.delete("alp") and not trie.delete("alpha","missing")
    assert trie.delete("ALPHA") and trie.search("alphabet")==["A"]
    assert trie.delete("alphabet") and trie.count_nodes()==1

def test_t24():
    for example in avl_rotation_examples():
        assert example["valid"] and example["log"][-1]["kind"]==example["kind"]
        event=example["log"][-1]
        assert event["after"]["key"][0]==20 and event["before"]["key"]==event["pivot"]
    tree=AVLTree()
    for i in range(40):tree.insert(Room(f"R{i}",i+1));assert tree.check_avl()
    tree.rotation_log.clear()
    for i in range(25):assert tree.delete((i+1,f"R{i}")) and tree.validate()
    assert any(row["operation"]=="delete" for row in tree.rotation_log)
    assert tree.node_accesses>0

def test_t25():
    assert verify_greedy_random_cases(100,42).startswith("100 kasus")

def test_t26():
    example=greedy_weight_counterexample()
    assert example["greedy_count"]==2 and example["greedy_value"]==4 and example["dp_value"]==10
    earlier_long=[replace(r,start=479) if r.request_id=="C" else r for r in example["candidates"]]
    assert select_activities(earlier_long,"earliest_start")[0]==1
    assert brute_force_activity_count(example["candidates"])[0]==2

def test_t27():
    without,with_aging=simulate_priority_dispatch(False),simulate_priority_dispatch(True)
    assert len(with_aging["trace"])>=50 and without["events"]==with_aging["events"]
    assert without["event_wait"]==600 and with_aging["event_wait"]==30
    assert with_aging["max_wait"]<without["max_wait"]

def test_t28():
    pairs=[(2,"a"),(1,"b"),(2,"c"),(0,"d")]
    assert manual_merge_sort(pairs,key=lambda x:x[0])==[(0,"d"),(1,"b"),(2,"a"),(2,"c")]
    assert select_activities([])==(0,[]) and brute_force_activity_count([])==(0,[])
    assert manual_merge_sort([])==[]

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

def test_t19():
    rng = Random(SEED)
    for case in range(10):
        sample = generate_requests(rng.randrange(0, 16), seed=rng.randrange(1_000_000))
        expected = optimize_schedule(sample)
        memo_value, memo_ids, memo_calls = optimize_schedule_memo(sample)
        assert (memo_value, memo_ids) == expected, "Memoisasi harus identik dengan tabulasi."
        naive_value, naive_calls = naive_recursive(sample)
        assert naive_value == memo_value, "Nilai optimum naif harus sama."
        assert memo_calls <= naive_calls, "Memoisasi tidak boleh lebih boros pemanggilan dari naif."
    chain = chain_requests(12)
    assert optimize_schedule_memo(chain)[:2] == optimize_schedule(chain)
    assert naive_recursive(chain) == (5 * 12, 2 ** 13 - 1)  # Rantai: eksponensial murni.
    assert optimize_schedule_memo([]) == (0, [], 0) and naive_recursive([]) == (0, 0)

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

def test_t29():
    nodes = ("A", "B", "C", "D")
    edges = [("A", "B", 1), ("B", "C", 2), ("A", "C", 8), ("C", "D", 3), ("A", "D", 9)]
    for algorithm in (kruskal_mst, prim_mst):
        result = algorithm(nodes, edges, trace_limit=2)
        assert result.total_cost == 6 and len(result.edges) == 3
        assert len(result.trace) == 2 and validate_mst(nodes, edges, result)["valid"]
        assert mst_cut_witness(nodes, edges, result)["safe"]

def test_t30():
    for nodes, edges, cost, components in [((), [], 0, 0), (("A",), [], 0, 1),
            (("A", "B", "C", "D"), [("A", "B", 2)], 2, 3)]:
        for algorithm in (kruskal_mst, prim_mst):
            result = algorithm(nodes, edges)
            assert result.total_cost == cost and len(result.components) == components
            assert len(result.edges) == len(nodes) - components
            assert validate_mst(nodes, edges, result)["valid"]

def test_t31():
    nodes = ("A", "B", "C", "D")
    edges = [("A", "B", -4), ("B", "C", 0), ("A", "C", 0), ("C", "D", 2), ("B", "D", 2)]
    for algorithm in (kruskal_mst, prim_mst):
        result = algorithm(nodes, edges)
        assert result.total_cost == -2 and validate_mst(nodes, edges, result)["valid"]
    uf = UnionFind(nodes)
    assert uf.union("A", "B") and uf.union("C", "D") and uf.union("B", "D")
    assert not uf.union("A", "C") and len({uf.find(n) for n in nodes}) == 1
    heap = PrimMinHeap()
    for value in [(2, "A", "B"), (-1, "A", "C"), (2, "A", "A")]:
        heap.push(value)
    assert [heap.pop() for _ in range(3)] == [(-1, "A", "C"), (2, "A", "A"), (2, "A", "B")]

def test_t32():
    bad = [(("A", "A"), []), (("A",), [("A", "A", 1)]), (("A", "B"), [("A", "X", 1)]),
           (("A", "B"), [("A", "B", float("nan"))]), (("A", "B"), [("A", "B", True)]),
           (("A", "B"), [("A", "B", 1), ("B", "A", 2)])]
    for nodes, edges in bad:
        for algorithm in (kruskal_mst, prim_mst):
            try:
                algorithm(nodes, edges)
            except ValueError:
                pass
            else:
                raise AssertionError("Graf tidak valid harus ditolak")
    nodes, edges = ("A", "B", "C"), [("A", "B", 1), ("B", "C", 1), ("A", "C", 5)]
    # Spans all vertices and is acyclic, but deliberately more expensive.
    wrong = MSTResult(nodes, (MSTEdge("A", "B", 1), MSTEdge("A", "C", 5)), (nodes,), 6, "wrong")
    assert not validate_mst(nodes, edges, wrong)["valid"]

def mst_bruteforce_cost(nodes, edges):
    """Independent exhaustive subset oracle for SMALL graphs, never UI input."""
    from itertools import combinations
    nodes, edges = validate_mst_graph(nodes, edges)
    groups = mst_components(nodes, edges)
    count = len(nodes) - len(groups)
    target = {frozenset(group) for group in groups}
    best = None
    for subset in combinations(edges, count):
        if {frozenset(group) for group in mst_components(nodes, subset)} == target:
            cost = sum(e.weight for e in subset)
            best = cost if best is None else min(best, cost)
    return 0 if best is None and not nodes else best

def test_t33():
    rng = Random(42)
    for _ in range(60):
        nodes = tuple(f"R{i}" for i in range(rng.randint(1, 6)))
        edges = [(u, v, rng.randint(-5, 9)) for i, u in enumerate(nodes)
                 for v in nodes[i + 1:] if rng.random() < .5]
        expected = mst_bruteforce_cost(nodes, edges)
        for algorithm in (kruskal_mst, prim_mst):
            result = algorithm(nodes, edges)
            assert result.total_cost == expected and validate_mst(nodes, edges, result)["valid"]

TEST_IDS = [f"T{i:02d}" for i in range(1, 34)]

TEST_RUNNERS = {"T01": test_t01, "T02": test_t02, "T03": test_t03, "T04": test_t04, "T05": test_t05, "T06": test_t06, "T07": test_t07, "T08": test_t08, "T09": test_t09, "T10": test_t10, "T11": test_t11, "T12": test_t12, "T13": test_t13, "T14": test_t14, "T15": test_t15, "T16": test_t16, "T17": test_t17, "T18": test_t18, "T19": test_t19, "T20": test_t20, "T21": test_t21, "T22": test_t22, "T23": test_t23, "T24": test_t24, "T25": test_t25, "T26": test_t26, "T27": test_t27, "T28": test_t28, "T29": test_t29, "T30": test_t30, "T31": test_t31, "T32": test_t32, "T33": test_t33}

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
