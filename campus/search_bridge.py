# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .hash_table import HashTableChaining
from .trie import Trie

def hubungkan_pencarian_feb(bahan):
    # Hindari key berulang menimpa detail kelas yang belum diperiksa.
    for nama in ["kelas", "mata_kuliah"]:
        keys = [key for key, _ in bahan[nama]]
        if any(key is None or not str(key).strip() for key in keys):
            raise ValueError(f"Kode pada bahan {nama} masih kosong; periksa laporan data.")
        if len(keys) != len(set(keys)):
            raise ValueError(f"Kode pada bahan {nama} berulang; pastikan sesi/duplikasi sebelum membangun indeks.")
    tabel_kelas, tabel_mk = HashTableChaining(), HashTableChaining()
    trie_nama, trie_kode = Trie(), Trie()
    for key, detail in bahan["kelas"]:
        tabel_kelas.put(key, detail)
    for key, detail in bahan["mata_kuliah"]:
        tabel_mk.put(key, detail)
    for entry in bahan["nama"]:
        trie_nama.insert(entry.name, entry.entry_id)
    for entry in bahan["kode"]:
        trie_kode.insert(entry.name, entry.entry_id)
    return {"kelas": tabel_kelas, "mata_kuliah": tabel_mk, "nama": trie_nama, "kode": trie_kode}

AKTIFKAN_PENCARIAN_FEB = True  # Ubah setelah implementasi anggota siap.
