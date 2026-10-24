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
