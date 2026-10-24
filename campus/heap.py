# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .hash_table import HashTableChaining
from .models import ScheduleRequest, PRIORITY

class MinHeapPriorityQueue:
    """Min-heap manual: (prioritas efektif, jam mulai, urutan masuk).

    Antrean dipakai untuk satu tanggal kegiatan. Jam simulasi submitted_at/now
    terpisah dari jam mulai kegiatan. Hash tim menyimpan ID -> posisi array.
    """
    def __init__(self):
        self.entries = []  # (key, ScheduleRequest asli, counter asli)
        self.next_counter = 0
        self.position_map = HashTableChaining()
        self.comparisons = 0
        self.now = None
        self.aging_step = None

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
            raise ValueError("Waktu masuk tidak boleh melewati jam aging aktif.")

    def _key(self, request, counter):
        priority = request.priority
        if self.aging_step is not None:
            waited = self.now - request.submitted_at
            priority = max(1, priority - waited // self.aging_step)
        return (priority, request.start, counter)

    def _less(self, left, right):
        self.comparisons += 1
        return self.entries[left][0] < self.entries[right][0]

    def _swap(self, left, right):
        self.entries[left], self.entries[right] = self.entries[right], self.entries[left]
        self.position_map.put(self.entries[left][1].request_id, left)
        self.position_map.put(self.entries[right][1].request_id, right)

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if not self._less(index, parent):
                break
            self._swap(index, parent)
            index = parent

    def _sift_down(self, index):
        while 2 * index + 1 < len(self.entries):
            child = 2 * index + 1
            right = child + 1
            if right < len(self.entries) and self._less(right, child):
                child = right
            if not self._less(child, index):
                break
            self._swap(index, child)
            index = child

    def _heapify(self):
        # Daun sudah heap; perbaiki hanya simpul internal dari bawah ke atas.
        for index in range(len(self.entries) // 2 - 1, -1, -1):
            self._sift_down(index)

    def build(self, requests):
        """Ganti antrean dengan batch baru dalam O(n), mempertahankan jam aging.

        Validasi seluruh batch sebelum mengubah antrean. Counter baru mengikuti
        urutan batch. ID duplikat ditolak memakai Hash buatan tim.
        """
        entries = []
        positions = HashTableChaining()
        for counter, request in enumerate(requests):
            self._check_request(request)
            if positions.contains(request.request_id):
                raise ValueError(f"ID berulang: {request.request_id}")
            positions.put(request.request_id, counter)
            entries.append((self._key(request, counter), request, counter))
        self.entries = entries
        self.position_map = positions
        self.next_counter = len(entries)
        self.comparisons = 0
        self._heapify()

    def push(self, request):
        self._check_request(request)
        if self.position_map.contains(request.request_id):
            raise ValueError(f"ID sudah berada dalam antrean: {request.request_id}")
        counter = self.next_counter
        self.entries.append((self._key(request, counter), request, counter))
        self.position_map.put(request.request_id, len(self.entries) - 1)
        self.next_counter += 1
        self._sift_up(len(self.entries) - 1)

    def pop(self):
        if not self.entries:
            raise IndexError("Antrean kosong.")
        request = self.entries[0][1]
        last = self.entries.pop()
        self.position_map.delete(request.request_id)
        if self.entries:
            self.entries[0] = last
            self.position_map.put(last[1].request_id, 0)
            self._sift_down(0)
        return request

    def peek(self):
        if not self.entries:
            raise IndexError("Antrean kosong.")
        return self.entries[0][1]

    def apply_aging(self, now, step_minutes):
        """Hitung ulang dari prioritas AWAL; panggilan ulang tidak menumpuk aging.

        Counter/FIFO dan objek request tidak berubah. O(n) untuk hitung key lalu
        heapify O(n). Jam simulasi harus maju/diam dan tidak mendahului pengajuan.
        """
        if type(step_minutes) is not int or step_minutes <= 0:
            raise ValueError("Interval aging harus bilangan bulat positif.")
        if type(now) is not int or now < 0:
            raise ValueError("Jam simulasi harus bilangan bulat tidak negatif.")
        if self.now is not None and now < self.now:
            raise ValueError("Jam simulasi tidak boleh mundur.")
        if any(request.submitted_at > now for _, request, _ in self.entries):
            raise ValueError("Jam simulasi mendahului waktu masuk permintaan.")
        self.now, self.aging_step = now, step_minutes
        self.entries = [(self._key(request, counter), request, counter)
                        for _, request, counter in self.entries]
        self._heapify()

    def ordered_entries(self):
        """Pratinjau O(n log n) lewat pop pada salinan; antrean asli tidak berubah."""
        copy = MinHeapPriorityQueue()
        copy.entries = list(self.entries)
        for index, (_, request, _) in enumerate(copy.entries):
            copy.position_map.put(request.request_id, index)
        result = []
        while copy:
            result.append(copy.entries[0])
            copy.pop()
        return result

    def validate(self):
        """Periksa heap, counter unik, key, dan Hash posisi tanpa menambah metrik."""
        assert len(self.position_map) == len(self.entries)
        assert len({counter for _, _, counter in self.entries}) == len(self.entries)
        for index, (key, request, counter) in enumerate(self.entries):
            assert self.position_map.get(request.request_id) == index
            assert key == self._key(request, counter)
            assert counter < self.next_counter
            if index > 0:
                assert self.entries[(index - 1) // 2][0] <= key
        return True

    def __len__(self):
        return len(self.entries)
