# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .hash_table import HashTableChaining
from .models import ScheduleRequest, PRIORITY

class MinHeapPriorityQueue:
    """Antrean manual: (prioritas efektif, counter FIFO), satu tanggal.

    Jam ujian adalah payload. Override prioritas bersifat lokal pada antrean,
    sehingga objek dan data Excel tidak diubah. Trace opt-in dan dibatasi.
    """
    def __init__(self, trace=False, trace_limit=200):
        self.entries = []
        self.next_counter = 0
        self.position_map = HashTableChaining()
        self.priority_overrides = HashTableChaining()
        self.comparisons = 0
        self.now = self.aging_step = None
        self.trace_enabled = trace
        self.trace_limit = trace_limit
        self.trace = []

    def _check_request(self, request):
        if not isinstance(request, ScheduleRequest):
            raise TypeError("Masukan harus ScheduleRequest.")
        if not isinstance(request.request_id, str) or not request.request_id.strip():
            raise ValueError("ID permintaan harus teks tidak kosong.")
        if request.activity_type not in PRIORITY:
            raise ValueError("Kategori kegiatan tidak dikenal.")
        for name in ("start", "end", "submitted_at"):
            value = getattr(request, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} harus bilangan bulat tidak negatif.")
        if not 0 <= request.start < request.end <= 1440:
            raise ValueError("Jam kegiatan harus berurutan dalam satu hari.")
        if self.now is not None and request.submitted_at > self.now:
            raise ValueError("Waktu masuk melewati jam aging aktif.")
        if self.entries and request.day != self.entries[0][1].day:
            raise ValueError("Antrean hanya menerima satu tanggal.")

    def _key(self, request, counter):
        override = self.priority_overrides.get(request.request_id)
        priority = request.priority if override is None else override
        if self.aging_step is not None:
            priority = max(1, priority - (self.now - request.submitted_at) // self.aging_step)
        return (priority, counter)

    def _record(self, operation, **detail):
        if self.trace_enabled and len(self.trace) < self.trace_limit:
            self.trace.append({"operation": operation, **detail})

    def _less(self, left, right):
        self.comparisons += 1
        return self.entries[left][0] < self.entries[right][0]

    def _swap(self, left, right):
        before = [r.request_id for _, r, _ in self.entries[:15]] if self.trace_enabled else None
        self.entries[left], self.entries[right] = self.entries[right], self.entries[left]
        self.position_map.put(self.entries[left][1].request_id, left)
        self.position_map.put(self.entries[right][1].request_id, right)
        self._record("swap", left=left, right=right, before=before,
                     after=[r.request_id for _, r, _ in self.entries[:15]] if self.trace_enabled else None)

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if not self._less(index, parent): break
            self._swap(index, parent); index = parent

    def _sift_down(self, index):
        while 2 * index + 1 < len(self.entries):
            child, right = 2 * index + 1, 2 * index + 2
            if right < len(self.entries) and self._less(right, child): child = right
            if not self._less(child, index): break
            self._swap(index, child); index = child

    def _repair(self, index):
        if index and self._less(index, (index - 1) // 2): self._sift_up(index)
        else: self._sift_down(index)

    def _heapify(self):
        for index in range(len(self.entries) // 2 - 1, -1, -1): self._sift_down(index)

    def build(self, requests):
        """Batch baru O(n); validasi atomik, override lama direset."""
        requests = list(requests)
        entries, positions = [], HashTableChaining()
        if len({r.day for r in requests if isinstance(r, ScheduleRequest)}) > 1:
            raise ValueError("Antrean hanya menerima satu tanggal.")
        # Jangan membandingkan tanggal batch baru dengan antrean yang diganti.
        validator = MinHeapPriorityQueue()
        validator.now = self.now
        for counter, request in enumerate(requests):
            validator._check_request(request)
            if positions.contains(request.request_id): raise ValueError(f"ID berulang: {request.request_id}")
            positions.put(request.request_id, counter)
            entries.append((None, request, counter))
        self.priority_overrides = HashTableChaining()
        self.entries = [(self._key(r, c), r, c) for _, r, c in entries]
        self.position_map, self.next_counter = positions, len(entries)
        self.comparisons = 0; self.trace.clear()
        self._record("build_start", ids=[r.request_id for r in requests[:15]])
        self._heapify()

    def push(self, request):
        self._check_request(request)
        if self.position_map.contains(request.request_id): raise ValueError("ID sudah berada dalam antrean.")
        counter = self.next_counter
        self.entries.append((self._key(request, counter), request, counter))
        self.position_map.put(request.request_id, len(self.entries) - 1)
        self.next_counter += 1
        self._sift_up(len(self.entries) - 1)
        self._record("push", request_id=request.request_id, counter=counter)

    def remove(self, request_id):
        index = self.position_map.get(request_id)
        if index is None: raise KeyError(request_id)
        request = self.entries[index][1]
        last = self.entries.pop()
        self.position_map.delete(request_id); self.priority_overrides.delete(request_id)
        if index < len(self.entries):
            self.entries[index] = last
            self.position_map.put(last[1].request_id, index)
            self._repair(index)
        self._record("remove", request_id=request_id)
        return request

    def pop(self):
        if not self.entries: raise IndexError("Antrean kosong.")
        return self.remove(self.entries[0][1].request_id)

    def peek(self):
        if not self.entries: raise IndexError("Antrean kosong.")
        return self.entries[0][1]

    def change_priority(self, request_id, priority):
        """Ubah prioritas dasar 1..4; counter dan waktu masuk tetap."""
        if type(priority) is not int or not 1 <= priority <= 4:
            raise ValueError("Prioritas harus bilangan bulat 1 sampai 4.")
        index = self.position_map.get(request_id)
        if index is None: raise KeyError(request_id)
        _, request, counter = self.entries[index]
        self.priority_overrides.put(request_id, priority)
        self.entries[index] = (self._key(request, counter), request, counter)
        self._repair(index)
        self._record("change_priority", request_id=request_id, priority=priority)

    def apply_aging(self, now, step_minutes):
        if type(step_minutes) is not int or step_minutes <= 0:
            raise ValueError("Interval aging harus bilangan bulat positif.")
        if type(now) is not int or now < 0 or (self.now is not None and now < self.now):
            raise ValueError("Jam simulasi tidak boleh negatif atau mundur.")
        if any(r.submitted_at > now for _, r, _ in self.entries):
            raise ValueError("Jam simulasi mendahului pengajuan.")
        self.now, self.aging_step = now, step_minutes
        self.entries = [(self._key(r, c), r, c) for _, r, c in self.entries]
        self._heapify(); self._record("aging", now=now, interval=step_minutes)

    def ordered_entries(self):
        copy = MinHeapPriorityQueue()
        copy.entries = list(self.entries)
        copy.now, copy.aging_step, copy.next_counter = self.now, self.aging_step, self.next_counter
        for key, value in self.priority_overrides.items(): copy.priority_overrides.put(key, value)
        for i, (_, r, _) in enumerate(copy.entries): copy.position_map.put(r.request_id, i)
        result = []
        while copy:
            result.append(copy.entries[0]); copy.pop()
        return result

    def validate(self):
        assert len(self.position_map) == len(self.entries)
        assert len({c for _, _, c in self.entries}) == len(self.entries)
        for i, (key, request, counter) in enumerate(self.entries):
            assert self.position_map.get(request.request_id) == i
            assert key == self._key(request, counter) and counter < self.next_counter
            if i: assert self.entries[(i - 1) // 2][0] <= key
        return True

    def is_heap(self): return self.validate()

    def __len__(self): return len(self.entries)

class MaxHeap:
    """MaxHeap array manual untuk nilai/kunci yang dapat dibandingkan."""
    def __init__(self, values=(), trace=False, trace_limit=200):
        self.values = []
        self.trace_enabled, self.trace_limit, self.trace = trace, trace_limit, []
        self.comparisons = 0
        self.build(values)

    def _greater(self, a, b):
        self.comparisons += 1
        return self.values[a] > self.values[b]

    def _swap(self, a, b):
        before = list(self.values[:15]) if self.trace_enabled else None
        self.values[a], self.values[b] = self.values[b], self.values[a]
        if self.trace_enabled and len(self.trace) < self.trace_limit:
            self.trace.append({"operation":"swap", "left":a, "right":b,
                               "before":before, "after":list(self.values[:15])})

    def _up(self, i):
        while i and self._greater(i, (i - 1) // 2):
            p = (i - 1) // 2; self._swap(i, p); i = p

    def _down(self, i):
        while 2 * i + 1 < len(self.values):
            c = 2 * i + 1
            if c + 1 < len(self.values) and self._greater(c + 1, c): c += 1
            if not self._greater(c, i): break
            self._swap(i, c); i = c

    def build(self, values):
        self.values = list(values); self.comparisons = 0; self.trace.clear()
        for i in range(len(self.values) // 2 - 1, -1, -1): self._down(i)

    def push(self, value):
        self.values.append(value); self._up(len(self.values) - 1)

    def peek(self):
        if not self.values: raise IndexError("Heap kosong.")
        return self.values[0]

    def delete(self, index):
        if type(index) is not int or not 0 <= index < len(self.values): raise IndexError("Indeks heap tidak valid.")
        result = self.values[index]; last = self.values.pop()
        if index < len(self.values):
            self.values[index] = last
            if index and self._greater(index, (index - 1) // 2): self._up(index)
            else: self._down(index)
        return result

    def pop(self):
        if not self.values: raise IndexError("Heap kosong.")
        return self.delete(0)

    def change_key(self, index, value):
        if type(index) is not int or not 0 <= index < len(self.values): raise IndexError("Indeks heap tidak valid.")
        old = self.values[index]; self.values[index] = value
        if value > old: self._up(index)
        else: self._down(index)

    def validate(self):
        assert all(self.values[(i - 1) // 2] >= v for i, v in enumerate(self.values) if i)
        return True

    def is_heap(self): return self.validate()

    def __len__(self): return len(self.values)

def heap_sort(values):
    """O(n log n); hasil naik, input asli tetap, memakai MaxHeap manual."""
    heap = MaxHeap(values)
    result = [heap.pop() for _ in range(len(heap))]
    result.reverse()
    return result
