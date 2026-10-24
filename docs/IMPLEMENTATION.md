# Implementasi versi penuh

## Kontrak sumber

Notebook lengkap 21 Oktober 2026 disalin menjadi snapshot lokal tanpa perubahan. Definisi kelas/fungsi diekstrak verbatim lewat AST, termasuk decorator. Sel notebook tidak dieksekusi saat aplikasi dimuat. Modul service hanya memuat layanan produksi dan dependensinya; demo dipisahkan ke integration_demo.py. Fixture dimuat hanya untuk pengujian yang diminta pengguna.

Sumber jadwal aplikasi tetap satu workbook Excel aktif. Tabel asli, hasil normalisasi, catatan dan nomor baris disimpan terpisah. Perubahan aturan LAB belum diterapkan sesuai arahan pengguna.

## Siklus sesi

State penuh diikat ke (sha256 Excel, sha256 notebook). Pergantian sumber mengosongkan workspace mingguan, hasil pengukuran dan state antrean. AllocationWorkspace terpisah per minggu ISO; kandidat, kapasitas dan provenance selalu dari workbook aktif.

Registry simulasi dimulai dari Room Excel dengan used_slots=0 dan room_type Unknown. Ini tidak menghapus jadwal nyata: workspace adalah alternatif penempatan. schedule_across_rooms menerima booking yang sudah tersimpan sehingga alokasi bertahap tidak mengabaikan bentrok. Kelas asal yang sudah terwakili dikeluarkan dari pilihan, termasuk sumber pada record gabungan.

Pembatalan menghapus satu alokasi, menghitung ulang slot reguler unik dari booking ruang yang tersisa, lalu memanggil update_room_usage dengan kedua indeks. Hash, AVL kapasitas, dan AVL pemakaian divalidasi konsisten. Tidak ada pembaruan manual count yang memutus hubungan dengan interval booking.

## Penggabungan dan penelusuran

Relasi pencarian INT–NAS tidak berarti izin penggabungan kelas. UI menawarkan pasangan eksplisit Excel yang lengkap/tidak ambigu. Pilihan pengguna adalah konfirmasi khusus simulasi. Fungsi merge_equivalent_classes memeriksa seluruh syarat Colab; kapasitas berlebih menghasilkan pesan validasi dan tidak mengubah workspace. Semua hasil mencatat source_ids dan baris Excel; ID gabungan bukan kegiatan sintetis baru.

## Pengukuran dan pengujian

Benchmark langsung memakai data Excel: Hash vs scan kode identik; Trie vs scan awalan dan deduplikasi identik; Heap build+drain vs list terurut pada satu tanggal; AVL top-k vs list+sort; DP vs brute force pada satu ruang/hari maksimal 15 kandidat. Setup berada di luar timer dan pengukuran memori terpisah, menggunakan helper persis dari Colab.

58 hasil tersimpan hanya ditampilkan sebagai arsip eksperimen Colab, dengan label sumber sintetis dan lingkungan lokal. Hash notebook pada provenance diperiksa sebelum ditampilkan. Arsip tidak masuk alur jadwal atau alokasi. UI pengujian memakai fixture terkontrol untuk T01–T18 dan menampilkan hasil aktual sesi, bukan status lulus statis.

Pengujian proyek memeriksa kesetaraan AST, transaksi gagal, slot unik, alokasi/pembatalan, gabungan dan pelepasan sumbernya, handoff antrean, kontinuitas booking, pergantian workbook, serta UI dan benchmark. Catatan kapasitas resmi, fasilitas, pasangan resmi, dan konflik dosen/mahasiswa tetap keterbatasan model yang dijelaskan pada konteks hasil.
