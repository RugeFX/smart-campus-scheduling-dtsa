# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import ScheduleRequest, PRIORITY, VALUE, Random, replace
from .heap import MinHeapPriorityQueue

def heap_test_request(identifier, kind="Examination", start=600, submitted_at=0):
    # Fixture pengujian saja, bukan sumber jadwal aplikasi.
    return ScheduleRequest(identifier, identifier, kind, 20, "F802", "2026-10-08",
                           start, start + 60, VALUE[kind], submitted_at)

def test_t01():
    batch = [heap_test_request("E", "Event", 435),
             heap_test_request("K2", "Regular Class", 700),
             heap_test_request("U2", "Examination", 700),
             heap_test_request("P", "Practicum", 500),
             heap_test_request("U1", "Examination", 600),
             heap_test_request("K1", "Regular Class", 600)]
    queue = MinHeapPriorityQueue()
    for request in batch:
        queue.push(request)
        assert queue.validate()
    assert [queue.pop().request_id for _ in batch] == ["U2", "U1", "P", "K2", "K1", "E"]
    assert queue.validate()

def test_t02():
    queue = MinHeapPriorityQueue()
    batch = [heap_test_request("Masuk-1"), heap_test_request("Masuk-2"),
             heap_test_request("Jam-lebih-awal", start=500)]
    queue.build(batch)
    assert queue.peek() is batch[0] and len(queue) == 3
    assert [queue.pop().request_id for _ in batch] == ["Masuk-1", "Masuk-2", "Jam-lebih-awal"]

def test_t03():
    queue = MinHeapPriorityQueue()
    for action in (queue.pop, queue.peek):
        try:
            action()
        except IndexError:
            assert len(queue) == 0 and queue.validate()
        else:
            raise AssertionError("Antrean kosong harus menghasilkan IndexError.")

def test_heap_aging():
    event = heap_test_request("Event-lama", "Event", 500)
    exam = heap_test_request("Ujian-baru", "Examination", 600, 85)
    queue = MinHeapPriorityQueue()
    queue.build([event, exam])
    assert queue.peek() is exam
    counters = {r.request_id: c for _, r, c in queue.entries}
    queue.apply_aging(90, 30)
    assert queue.peek() is event and event.priority == 4
    once = list(queue.entries)
    queue.apply_aging(90, 30)
    assert queue.entries == once  # Tidak mengurangi prioritas lagi secara kumulatif.
    assert counters == {r.request_id: c for _, r, c in queue.entries}
    queue.push(heap_test_request("Baru", "Event", 435, 90))
    assert queue.entries[queue.position_map.get("Baru")][0][0] == 4
    for now, step in [(89, 30), (100, 0), (100, -1), (100, True), (100.5, 30)]:
        before = (list(queue.entries), queue.now, queue.aging_step)
        try:
            queue.apply_aging(now, step)
        except ValueError:
            assert (queue.entries, queue.now, queue.aging_step) == before
        else:
            raise AssertionError("Parameter aging tidak valid seharusnya ditolak.")
    assert queue.validate()
    queue.apply_aging(180, 30)
    assert [queue.pop().request_id for _ in range(len(queue))] == ["Event-lama", "Ujian-baru", "Baru"]

def test_heap_random():
    rng = Random(42)
    queue = MinHeapPriorityQueue()
    reference = []
    counter = 0
    for i in range(1000):
        if reference and rng.random() < 0.45:
            reference.sort(key=lambda item: (item[0].priority, item[1]))
            expected, _ = reference.pop(0)
            assert queue.peek() is expected
            assert queue.pop() is expected
        else:
            kind = rng.choice(list(PRIORITY))
            request = heap_test_request(f"ACAK-{i}", kind, rng.randrange(435, 900))
            queue.push(request)
            reference.append((request, counter))
            counter += 1
        assert queue.validate()
    expected = [r for r, c in sorted(reference, key=lambda item: (item[0].priority, item[1]))]
    before = (list(queue.entries), queue.comparisons, queue.next_counter)
    assert [entry[1] for entry in queue.ordered_entries()] == expected
    assert (queue.entries, queue.comparisons, queue.next_counter) == before
    assert [queue.pop() for _ in expected] == expected
    # Heapify batch, bukan sort; pembanding hanya digunakan sebagai oracle tes.
    batch = [heap_test_request(f"B-{i}", rng.choice(list(PRIORITY)), rng.randrange(435, 900)) for i in range(1000)]
    queue.build(batch)
    assert queue.validate() and queue.comparisons <= 2 * len(batch)
    expected = sorted(enumerate(batch), key=lambda item: (item[1].priority, item[0]))
    assert [queue.pop() for _ in batch] == [r for _, r in expected]

def test_heap_invalid():
    queue = MinHeapPriorityQueue()
    first = heap_test_request("A")
    queue.push(first)
    invalid = [first, replace(first, request_id=""), replace(first, activity_type="Unknown"),
               replace(first, start=700, end=650), replace(first, submitted_at=-1),
               replace(first, start=True)]
    for request in invalid:
        before = (list(queue.entries), queue.next_counter, queue.comparisons)
        try:
            queue.push(request)
        except ValueError:
            assert (queue.entries, queue.next_counter, queue.comparisons) == before
            assert queue.validate()
        else:
            raise AssertionError("Masukan tidak valid/ID berulang harus ditolak.")
    try:
        queue.build([heap_test_request("B"), heap_test_request("B")])
    except ValueError:
        assert len(queue) == 1 and queue.peek() is first and queue.validate()
    else:
        raise AssertionError("Batch dengan ID berulang harus ditolak tanpa mengubah antrean.")
    queue = MinHeapPriorityQueue()
    queue.push(heap_test_request("Masa-depan", submitted_at=100))
    try:
        queue.apply_aging(90, 30)
    except ValueError:
        assert queue.now is None and queue.aging_step is None and queue.validate()
    else:
        raise AssertionError("Jam aging mendahului waktu masuk harus ditolak.")

def run_heap_tests():
    for name, action in [("T01", test_t01), ("T02", test_t02), ("T03", test_t03),
                         ("Aging", test_heap_aging), ("Acak + build", test_heap_random),
                         ("Validasi", test_heap_invalid)]:
        action()
        print(f"Heap {name}: LULUS")
