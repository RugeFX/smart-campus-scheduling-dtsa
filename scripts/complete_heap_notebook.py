"""Apply the authorized Heap/PQ section update to a freshly downloaded notebook.

Usage: python scripts/complete_heap_notebook.py input.ipynb output.ipynb
Only Heap cells, its deferred tests, and the T01–T03 registration are changed.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
notebook = json.loads(Path(sys.argv[1]).read_text())
work = ROOT / "references/heap-work"
for cell in notebook["cells"]:
    source = "".join(cell["source"])
    updated = source
    if source.startswith("# Smart Campus — Notebook Kelompok 2"):
        updated = source.replace("Setup, impor dan validasi Excel, data contoh, generator, pembanding jadwal, dan operasi dasar AVL sudah tersedia.\nLengkapi bagian **TODO** untuk Heap, Hash, Trie, DP, penghapusan AVL, dan integrasi.",
            "Setup, impor/validasi Excel, Heap/PQ, Hash, Trie, DP, generator, pembanding jadwal, "
            "dan operasi dasar AVL sudah tersedia.\nLengkapi bagian **TODO** untuk penghapusan AVL, integrasi, dan eksperimen.")
    elif source.startswith("class MinHeapPriorityQueue:"):
        updated = (work / "heap_source.py").read_text()
    elif source.startswith("## 1. Heap + Priority Queue"):
        updated = source.replace("**TODO:** tambah/hapus/peek, kasus kosong, tie yang benar, peta posisi, penghitung perbandingan.",
            "**Terimplementasi:** push/pop/peek, build O(n), aging, FIFO, kasus kosong, "
            "Hash posisi, penghitung perbandingan, dan pemeriksaan invariant. "
            "Implementasi memakai array manual, tanpa heapq/sort. ID duplikat dan parameter "
            "tidak valid ditolak sebelum mutasi. Aging dihitung ulang dari prioritas awal; "
            "counter dan request asli tetap disimpan.\n\n"
            "Heap mengacu ke HashTableChaining bagian 2. Karena itu demo dan tes dijalankan "
            "sesudah definisi Hash agar **Run all dari kernel baru** dapat berjalan. "
            "Fixture campuran kategori hanya untuk uji; UI memakai Excel FEB. "
            "Antrean UI dipisah per tanggal, lalu membandingkan jam mulai. "
            "Jam pengajuan/aging adalah simulasi terpisah, bukan waktu dari Excel.")
    elif source.startswith("## 7. Rencana 18 Pengujian"):
        updated = source.replace("**Belum ada klaim lulus**; daftarkan fungsi uji setelah\nimplementasi tersedia.",
            "**T01–T03 Heap telah diimplementasikan dan didaftarkan**; "
            "hasil dicetak ketika sel pengujian Heap dijalankan. "
            "Pengujian anggota lain tetap mengikuti implementasi dan registrasinya.")
    elif source.startswith("TEST_IDS ="):
        updated = source.replace('TEST_RUNNERS = {}  # TODO: fungsi tanpa argumen, misalnya TEST_RUNNERS["T01"] = test_t01.',
            'TEST_RUNNERS = {"T01": test_t01, "T02": test_t02, "T03": test_t03}\n'
            '# Daftarkan pengujian anggota lain setelah siap; tidak mengklaim T04–T18 di sini.')
        updated = updated.replace('print("18 skenario uji disiapkan. Pengujian algoritma belum dijalankan.")',
            'print("T01–T03 terdaftar dan dijalankan pada sel Heap. Aktifkan RUN_TESTS untuk rekap 18 skenario.")')
    if updated != source:
        cell["source"] = updated.splitlines(keepends=True)
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

if not any(cell.get("id") == "heap-pq-tests-ikin-deni" for cell in notebook["cells"]):
    after_hash = next(i for i, cell in enumerate(notebook["cells"])
                      if "def run_hash_tests():" in "".join(cell["source"]))
    notebook["cells"][after_hash + 1:after_hash + 1] = [
        {"cell_type": "markdown", "id": "heap-pq-tests-note", "metadata": {},
         "source": ["### Uji Heap/PQ — Ikin & Deni\n", "Dijalankan setelah Hash siap: demo J1–J6, T01–T03, aging, "
                    "1.000 operasi acak, build batch, dan validasi input. "
                    "Data contoh berikut khusus pengujian, bukan data UI.\n"]},
        {"cell_type": "code", "id": "heap-pq-tests-ikin-deni", "metadata": {},
         "source": (work / "heap_tests_source.py").read_text().splitlines(keepends=True),
         "outputs": [], "execution_count": None},
    ]
notebook["metadata"]["smart_campus"]["status"] = "Heap/PQ, Hash, Trie, DP and AVL read operations available; AVL delete/integration/benchmark TODO"
notebook["metadata"]["smart_campus"]["data_status"] = "Excel FEB imported; illustrative fixtures retained for algorithm tests"
Path(sys.argv[2]).write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
print("Heap/PQ and T01–T03 updated; unrelated source cells preserved.")
