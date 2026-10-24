# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .hash_table import HashTableChaining, weak_hash

class WeakHashTable(HashTableChaining):
    """Khusus tes T05: memakai hash penjumlahan agar F708 dan F807 bertabrakan."""
    def _hash(self, key):
        return weak_hash(key, len(self.buckets))

def test_t04():
    # Put/get 10 ribu ID unik, semua data harus kembali benar.
    table = HashTableChaining()
    for i in range(10_000):
        table.put(f"ID-{i:05d}", i)
    assert len(table) == 10_000
    for i in range(10_000):
        assert table.get(f"ID-{i:05d}") == i
    assert table.get("ID-tidak-ada") is None

def test_t05():
    # F708 dan F807 bertabrakan (hash penjumlahan, 8 bucket) tapi tetap terbaca.
    table = WeakHashTable(bucket_count=8)
    table.put("F708", "ruang A")
    table.put("F807", "ruang B")
    assert len(table.buckets[5]) == 2          # keduanya satu chain di bucket 5
    assert table.get("F708") == "ruang A"
    assert table.get("F807") == "ruang B"

def test_t06():
    # Load factor melewati 0,7 -> jumlah bucket berubah, semua key tetap ada.
    table = HashTableChaining(bucket_count=8)
    keys = [f"KEY-{i:03d}" for i in range(100)]
    for n, key in enumerate(keys, start=1):
        table.put(key, n)
        if n == 5:
            assert len(table.buckets) == 8      # 5/8 = 0,625 -> belum resize
        if n == 6:
            assert len(table.buckets) == 16     # 6/8 = 0,75 > 0,7 -> resize
    assert len(table) == 100
    assert len(table.buckets) > 8
    for n, key in enumerate(keys, start=1):
        assert table.get(key) == n
    assert len(list(table.items())) == len(table)

def test_hash_tambahan():
    table = HashTableChaining()
    # update: size tidak bertambah, value berganti
    table.put("A", 1)
    table.put("A", 2)
    assert len(table) == 1 and table.get("A") == 2
    # delete: True bila ada, False bila tidak ada
    assert table.delete("A") is True
    assert table.delete("A") is False
    assert len(table) == 0 and table.get("A") is None
    # value None yang disimpan vs key tidak ada
    table.put("N", None)
    assert table.get("N") is None and table.contains("N")
    assert not table.contains("X")
    # key bukan teks ditolak
    for bad_key in (None, 123, 4.5):
        try:
            table.put(bad_key, "x")
        except TypeError:
            pass
        else:
            raise AssertionError("Key bukan teks seharusnya ditolak.")
    # delete lalu isi lagi, tetap benar
    table.put("B", 5)
    table.delete("B")
    table.put("B", 6)
    assert table.get("B") == 6
    # probes naik saat menelusuri chain
    before = table.probes
    table.get("B")
    assert table.probes > before

def run_hash_tests():
    for name, test in [("T04", test_t04), ("T05", test_t05),
                       ("T06", test_t06), ("Tambahan", test_hash_tambahan)]:
        test()
        print(f"{name}: LULUS")
