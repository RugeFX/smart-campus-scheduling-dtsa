# Implementasi versi penuh

## Kontrak sumber

Snapshot notebook bersama diperbarui dan dijalankan penuh; definisinya menjadi acuan kode algoritma aplikasi. Definisi kelas/fungsi diekstrak verbatim lewat AST, termasuk decorator. Sel notebook tidak dieksekusi saat aplikasi dimuat. Modul service hanya memuat layanan produksi dan dependensinya; demo dipisahkan ke integration_demo.py. Fixture dimuat hanya untuk pengujian yang diminta pengguna.

Sumber jadwal aplikasi tetap satu workbook Excel aktif. Tabel asli, hasil normalisasi, catatan dan nomor baris disimpan terpisah. Perubahan aturan LAB belum diterapkan sesuai arahan pengguna.

## Siklus sesi

State penuh diikat ke (sha256 Excel, sha256 notebook). Pergantian sumber mengosongkan workspace mingguan, hasil pengukuran dan state antrean. AllocationWorkspace terpisah per minggu ISO; kandidat, kapasitas dan provenance selalu dari workbook aktif.

Registry simulasi dimulai dari Room Excel dengan used_slots=0 dan room_type Unknown. Ini tidak menghapus jadwal nyata: workspace adalah alternatif penempatan. schedule_across_rooms menerima booking yang sudah tersimpan sehingga alokasi bertahap tidak mengabaikan bentrok. Kelas asal yang sudah terwakili dikeluarkan dari pilihan, termasuk sumber pada record gabungan.

Pembatalan menghapus satu alokasi, menghitung ulang slot reguler unik dari booking ruang yang tersisa, lalu memanggil update_room_usage dengan kedua indeks. Hash, AVL kapasitas, dan AVL pemakaian divalidasi konsisten. Tidak ada pembaruan manual count yang memutus hubungan dengan interval booking.

## Penggabungan dan penelusuran

Relasi pencarian INT–NAS tidak berarti izin penggabungan kelas. UI menawarkan pasangan eksplisit Excel yang lengkap/tidak ambigu. Pilihan pengguna adalah konfirmasi khusus simulasi. Fungsi merge_equivalent_classes memeriksa seluruh syarat Colab; kapasitas berlebih menghasilkan pesan validasi dan tidak mengubah workspace. Semua hasil mencatat source_ids dan baris Excel; ID gabungan bukan kegiatan sintetis baru.

## Pengukuran dan pengujian

Benchmark langsung memakai data Excel: Hash vs scan kode identik; Trie vs scan awalan dan deduplikasi identik; Heap build+drain vs list terurut pada satu tanggal; AVL top-k vs list+sort; DP vs brute force pada satu ruang/hari maksimal 15 kandidat. Setup berada di luar timer dan pengukuran memori terpisah, menggunakan helper persis dari Colab.

79 hasil utama dan 43 tambahan tersimpan hanya ditampilkan sebagai arsip eksperimen Colab, dengan label sumber sintetis dan lingkungan lokal. Hash notebook pada provenance diperiksa sebelum ditampilkan. Arsip tidak masuk alur jadwal atau alokasi. UI pengujian memakai fixture terkontrol untuk T01–T33 dan menampilkan hasil aktual sesi, bukan status lulus statis.

Pengujian proyek memeriksa kesetaraan AST, transaksi gagal, slot unik, alokasi/pembatalan, gabungan dan pelepasan sumbernya, handoff antrean, kontinuitas booking, pergantian workbook, serta UI dan benchmark. Catatan kapasitas resmi, fasilitas, pasangan resmi, dan konflik dosen/mahasiswa tetap keterbatasan model yang dijelaskan pada konteks hasil.


### Peningkatan terpilih 26 Oktober 2026

Definisi baru berasal dari notebook, lalu `sync_notebook.py` mengekstraknya tanpa menjalankan sel. `scripts/uas_sources/` menyimpan sumber pengembangan; notebook beserta hash AST tetap acuan yang diuji. `verification.json` mencatat Run all lokal sebenarnya: 23 sel kode, T01–T33 lulus, alokasi 189/7/47.

Priority Queue membandingkan prioritas efektif dan counter masuk, tanpa jam mulai pada key; jam ujian tetap payload Excel. Override prioritas milik antrean dan tidak mengubah ScheduleRequest. Hash posisi dan override ikut diperiksa validator. Aging dihitung ulang dari prioritas awal/override sehingga tidak menumpuk saat waktu sama.

MaxHeap manual mendukung build/push/pop/peek/delete/change-key; Heap Sort menghasilkan salinan naik. Trie delete mempertahankan terminal dan cabang milik entri lain. Open addressing memakai linear probing dan tombstone; put terus mencari melewati tombstone agar update tidak menduplikasi key.

Greedy earliest-finish optimal untuk kardinalitas pada satu ruang/hari; DP optimal untuk bobot pada batch yang sama. Keduanya memakai merge sort manual. Validasi 100 instance kecil menggunakan oracle brute force kardinalitas khusus, bukan penjumlahan bobot.

79 benchmark utama dan 43 tambahan dijalankan ulang pada Python lokal; metadata run, hash CSV, dan hash notebook ada di provenance. Tambahan mengukur PQ vs list tidak terurut/terurut, Hash load factor, naif/memo/tabulasi, dan Greedy vs oracle. Setup di luar timer; sorting pembanding list terurut berada di dalam action build+drain.

UI menaruh trace, fixture, dan eksperimen dalam expander. `schedule_ui.py` memisahkan tujuan pengguna dari metode DP; `learning_ui.py` menampilkan demonstrasi yang jelas berlabel uji dan tidak dapat masuk alokasi. Memoization dibatasi 400 kandidat, naif 15, dengan tabulasi sebagai fallback.


### MST S11 · 27 Oktober 2026

Satu fitur baru dengan Kruskal dan Prim manual, validator independen dan cut witness. Node dari Excel aktif; seluruh sisi/bobot asumsi simulasi yang dapat diedit. Graph editor memiliki state sendiri diikat hash workbook/notebook, menyembunyikan hasil stale, bertahan lintas navigasi, dan reset pada sumber baru. UI memisahkan hasil pengguna dari trace dan benchmark. Rincian: [MST.md](MST.md).

24 pengukuran MST ditambah benchmark sebelumnya dijalankan kembali pada namespace notebook baru. CSV menyimpan lima waktu mentah, median, memori, input fingerprint dan metadata. `record_verified_artifacts.py` memeriksa output aktual dan mengikatnya ke hash snapshot/CSV. T29–T33 mencakup 60 graf kecil dengan oracle enumerasi subset, bukan hanya kesamaan dua metode.
