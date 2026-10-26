# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
def weak_hash(key, bucket_count):
    return sum(map(ord, key)) % bucket_count

def polynomial_hash(key, bucket_count):
    h = 0
    for character in key:
        h = (h * 31 + ord(character)) % bucket_count
    return h

class HashTableChaining:
    def __init__(self, bucket_count=8, max_load=0.7):
        if bucket_count < 1 or max_load <= 0:
            raise ValueError("Jumlah bucket dan ambang harus positif.")
        self.buckets = [[] for _ in range(bucket_count)]
        self.max_load = max_load
        self.size = 0
        self.probes = 0
        self.collisions = 0
        self.rehashes = 0

    def _hash(self, key):
        return polynomial_hash(key, len(self.buckets))

    def _check_key(self, key):
        if not isinstance(key, str):
            raise TypeError(
                f"Key harus berupa teks (str), bukan {type(key).__name__}.")

    def _find(self, chain, key):
        """Cari key di satu chain. Hasil: posisi di chain, atau -1 bila tidak ada."""
        for position, (stored_key, _) in enumerate(chain):
            self.probes += 1
            if stored_key == key:
                return position
        return -1

    def put(self, key, value):
        self._check_key(key)
        chain = self.buckets[self._hash(key)]
        position = self._find(chain, key)
        self.collisions += len(chain) if position == -1 else position

        if position != -1:
            # Key sudah ada -> perbarui value saja, size tidak bertambah.
            chain[position] = (key, value)
            return

        # Key baru -> tambahkan ke chain.
        chain.append((key, value))
        self.size += 1

        # Cek kepenuhan hanya setelah INSERT BARU (bukan setelah update).
        if self.size / len(self.buckets) > self.max_load:
            self._rehash(len(self.buckets) * 2)

    def get(self, key):
        """Kembalikan value, atau None bila key tidak ada."""
        self._check_key(key)
        chain = self.buckets[self._hash(key)]
        position = self._find(chain, key)
        if position == -1:
            return None
        return chain[position][1]

    def contains(self, key):
        """True bila key ada. Dipakai untuk membedakan 'key tidak ada'
        dari 'key ada tetapi value-nya None'."""
        self._check_key(key)
        chain = self.buckets[self._hash(key)]
        return self._find(chain, key) != -1

    def delete(self, key):
        """True bila berhasil dihapus, False bila key tidak ditemukan."""
        self._check_key(key)
        chain = self.buckets[self._hash(key)]
        position = self._find(chain, key)
        if position == -1:
            return False
        chain.pop(position)
        self.size -= 1
        return True

    def items(self):
        """Hasilkan semua pasangan (key, value), laci demi laci."""
        for chain in self.buckets:
            for pair in chain:
                yield pair

    def _rehash(self, new_bucket_count):
        if new_bucket_count < 1:
            raise ValueError("Jumlah bucket baru harus positif.")
        # 1) Simpan dulu semua pasangan lama.
        self.rehashes += 1
        old_pairs = list(self.items())
        # 2) Ganti laci dengan yang baru. Harus SEBELUM menghitung hash ulang,
        #    karena _hash memakai len(self.buckets).
        self.buckets = [[] for _ in range(new_bucket_count)]
        # 3) Masukkan lagi langsung ke chain. Tidak perlu cek duplikat
        #    (key lama sudah pasti unik) dan size tidak berubah.
        for key, value in old_pairs:
            self.buckets[self._hash(key)].append((key, value))

    def __len__(self):
        return self.size

    def __repr__(self):
        return f"HashTableChaining(size={self.size}, buckets={len(self.buckets)})"

class HashTableLinearProbing:
    """Open addressing manual; tombstone tidak memutus rantai pencarian.

    Probes menghitung slot diperiksa pada operasi publik. Collisions menghitung
    key berbeda yang ditemui saat put. Rehash internal tidak menambah keduanya.
    """
    TOMBSTONE = object()

    def __init__(self, bucket_count=8, max_load=0.7):
        if type(bucket_count) is not int or bucket_count < 1 or not 0 < max_load < 1:
            raise ValueError("Jumlah slot positif dan ambang load harus di antara 0 dan 1.")
        self.slots = [None] * bucket_count
        self.max_load, self.size, self.tombstones = max_load, 0, 0
        self.probes = self.collisions = self.rehashes = 0

    def _hash(self, key): return polynomial_hash(key, len(self.slots))

    def _check_key(self, key):
        if not isinstance(key, str): raise TypeError("Key harus berupa str.")

    def _locate(self, key, inserting=False):
        first_deleted = None
        start = self._hash(key)
        for offset in range(len(self.slots)):
            index = (start + offset) % len(self.slots)
            self.probes += 1
            item = self.slots[index]
            if item is None: return (first_deleted if first_deleted is not None else index), False
            if item is self.TOMBSTONE:
                if first_deleted is None: first_deleted = index
            elif item[0] == key: return index, True
            elif inserting: self.collisions += 1
        return first_deleted, False

    def put(self, key, value):
        self._check_key(key)
        index, found = self._locate(key, True)
        if found:
            self.slots[index] = (key, value); return
        if index is None or (self.size + 1) / len(self.slots) > self.max_load:
            self._rehash(max(2, len(self.slots) * 2))
            index, _ = self._locate(key, True)
        if self.slots[index] is self.TOMBSTONE: self.tombstones -= 1
        self.slots[index] = (key, value); self.size += 1

    def get(self, key):
        self._check_key(key)
        index, found = self._locate(key)
        return self.slots[index][1] if found else None

    def contains(self, key):
        self._check_key(key)
        return self._locate(key)[1]

    def delete(self, key):
        self._check_key(key)
        index, found = self._locate(key)
        if not found: return False
        self.slots[index] = self.TOMBSTONE
        self.size -= 1; self.tombstones += 1
        return True

    def _rehash(self, new_bucket_count):
        pairs = list(self.items())
        if new_bucket_count < 1 or new_bucket_count < len(pairs): raise ValueError("Slot rehash tidak cukup.")
        self.slots = [None] * new_bucket_count; self.tombstones = 0; self.rehashes += 1
        for key, value in pairs:
            start = self._hash(key)
            for offset in range(new_bucket_count):
                index = (start + offset) % new_bucket_count
                if self.slots[index] is None:
                    self.slots[index] = (key, value); break

    def items(self):
        for item in self.slots:
            if item is not None and item is not self.TOMBSTONE: yield item

    def validate(self):
        assert self.size == sum(x is not None and x is not self.TOMBSTONE for x in self.slots)
        assert self.tombstones == sum(x is self.TOMBSTONE for x in self.slots)
        keys = set()
        for key, value in self.items():
            assert key not in keys; keys.add(key)
            # Validator tidak menambah metrik operasi publik.
            start = self._hash(key)
            for offset in range(len(self.slots)):
                item = self.slots[(start + offset) % len(self.slots)]
                assert item is not None, "Key terputus oleh slot kosong."
                if item is not self.TOMBSTONE and item[0] == key: break
            else: raise AssertionError("Key tidak terjangkau.")
        return True

    def __len__(self): return self.size
