# S11 — Minimum Spanning Tree

Satu tambahan fitur UAS dengan **dua metode manual**, sesuai pilihan pengguna: Kruskal dan Prim. Buka halaman **Koneksi ruang** di Streamlit.

## Kasus dan batas sumber

Node diambil dari lembar `ruang` workbook aktif. Dataset bawaan berisi 16 ruang F701–F708 dan F801–F808, seluruhnya gedung F, lantai 7/8. Excel tidak memuat sisi, jarak, koordinat, maupun biaya instalasi. MST dipakai untuk **simulasi rancangan koneksi ruang berbiaya minimum**, bukan menyelesaikan bentrok jadwal atau mencari rute terpendek.

Seluruh sisi/biaya adalah asumsi simulasi yang disetujui pengguna dan dapat diedit. Template awal menghubungkan kode berurutan dalam satu gedung/lantai (biaya 1), lalu ruang pada ordinal yang sama antar-lantai berurutan (biaya 3). Urutan kode tidak membuktikan kedekatan fisik. Tidak ada koneksi otomatis antar-gedung. Bobot dalam satuan simulasi, bukan meter atau rupiah.

Template bawaan: **V=16, E=22; kedua metode memilih 15 sisi dengan biaya 17 dan satu komponen**. Menghapus semua koneksi menghasilkan 16 komponen dengan biaya 0; hasil ini disebut minimum spanning forest, bukan jaringan yang sudah terhubung. Ruang terisolasi selalu disertakan.

## Implementasi

- `kruskal_mst`: merge sort manual berdasarkan `(weight,u,v)`; UnionFind manual dengan union by rank dan path compression iteratif; sisi pembentuk siklus ditolak.
- `prim_mst`: adjacency list dan min-heap array manual berisi `(weight,u,v)`. Lazy Prim melewati sisi stale, lalu mulai ulang dari node yang belum dikunjungi untuk forest. Tidak menggunakan `heapq` atau MST pustaka.
- Graph simple dan tidak berarah. Sisi berulang termasuk arah terbalik, self-loop, node tidak dikenal, kode kosong/berulang, bobot boolean/NaN/infinity ditolak. Core mendukung bobot negatif/nol karena sah untuk MST; editor biaya membatasi 0–1 triliun satuan per koneksi.
- `validate_mst` terpisah: sisi harus berasal dari graf input, jumlah sisi V−C, tidak bersiklus, cakupan komponen sama, total biaya benar, dan cycle property. Untuk setiap sisi nonpohon, bobotnya tidak boleh lebih kecil daripada sisi terbesar di jalur pohon antara kedua ujungnya. Pemeriksaan minimalitas ini lebih kuat daripada sekadar menyamakan biaya dua metode.
- `mst_cut_witness`: lepas salah satu sisi hasil, tampilkan potongan dan seluruh sisi asli yang melintasinya. Sisi terpilih harus memiliki bobot minimum di potongan tersebut; tie sah.

Waktu kedua metode O(V + E log E); ruang O(V+E). Pada graf simple, log E = O(log V), tetapi lazy Prim tetap dapat menyimpan O(E) item heap. Validator sengaja sederhana dan independen, O(V(V+E)); tidak masuk timer benchmark. Trace opsional dibatasi 100 langkah pada UI dan dimatikan pada benchmark.

## UI dan sesi

Hasil default langsung terlihat. Editor koneksi/biaya berada dalam expander. Setelah perubahan, hasil lama disembunyikan sampai pengguna menghitung ulang. Tiga tab memisahkan hasil koneksi, perbandingan, serta cara kerja/bukti. Graf skematis menyorot sisi terpilih; alternatif memakai garis putus-putus. Tabel dan JSON memberi alternatif akses di luar grafik. JSON mencatat semua node, semua sisi, hasil, komponen, metode, hash Excel dan notebook, serta status asumsi biaya.

Skenario bertahan saat berpindah halaman dalam sesi yang sama; mengganti workbook/snapshot mengembalikan template sesuai ruang sumber baru. Tombol reset hanya mengembalikan skenario lokal. Tidak ada perubahan pada Excel atau alokasi jadwal.

## Bukti pengujian dan eksperimen

T29–T33 melengkapi T01–T28: optimum diketahui; kosong/satu node/forest; ties/nol/negatif dan struktur manual; input salah dan pohon nonminimum; 60 graf kecil acak dibanding enumerasi subset independen. Tes proyek tambahan memeriksa AST identik notebook, heap interleaved, rank/compression, Excel unggahan, editor invalid/stale, navigasi dan reset sumber.

`data/mst_benchmarks.csv`: 24 pengukuran (2 metode × 3 skenario × V=16,32,64,128). Sparse memakai chain plus sisi acak; dense lengkap; forest terdiri dari dua subgraf terpisah. Seed 42, satu warm-up, lima run; median, waktu mentah, peak Python bytes, E, komponen, biaya dan fingerprint input disimpan. Setup graf, oracle/validator dan CSV di luar timer; memori diukur terpisah. Kedua metode memakai input yang sama. Pengukuran lokal tidak menjamin salah satu metode selalu lebih cepat. Metadata di `data/mst_benchmark_environment.json`; hash sumber/CSV di `references/benchmark-provenance.json`.

Notebook tetap sumber algoritma. `scripts/add_mst_notebook.py` menambahkan sel S11 dan tes/benchmark secara terarah; `scripts/sync_notebook.py` mengekstrak definisi verbatim ke `campus/mst.py`, `campus/mst_experiments.py`, serta registrasi tes. `scripts/verify_completed_notebook.py` menjalankan seluruh sel, merekam output dan sertifikat pengujian lokal. Hasil mesin lokal tidak diberi label seolah dijalankan pada VM Colab.
