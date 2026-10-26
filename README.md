# Smart Campus · Versi penuh

Dashboard Streamlit Kelompok 2 UTS DtSA. **Excel FEB adalah sumber jadwal aplikasi; Colab adalah sumber algoritma.** Implementasi tersinkron ke notebook yang diperbarui 27 Oktober 2026, termasuk DP dari PR #17 dan peningkatan UAS terpilih.

## Menjalankan

Gunakan Python 3.12+. Di macOS, klik dua kali **Jalankan Smart Campus.command**, atau:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows: aktivasi memakai `.venv\Scripts\activate`. Buka alamat yang ditampilkan, biasanya http://localhost:8501.

## Halaman dan algoritma

| Halaman | Fitur | Algoritma / anggota |
|---|---|---|
| Ringkasan | Jumlah data, timeline Excel, status dan akses ke tiap alur | Seluruh modul |
| Cari jadwal | Kode/nama MK, kelas, ruang, dosen; pasangan INT–NAS, chaining/linear probing, pratinjau Trie delete, CSV | Hash / Adit; Trie / Zilan |
| Antrean kegiatan | Kelas Excel per tanggal, push, peek, pop, FIFO per prioritas, change-priority, aging, trace/peta posisi/pohon, riwayat, teruskan ke alokasi | Heap/PQ / Ikin & Deni |
| Simulasi alokasi | Pilih semua/sebagian/dari antrean; gabung pasangan terkonfirmasi untuk simulasi; ruang alternatif; hasil, alasan penolakan, percobaan, timeline, CSV, pembatalan dan reset | Integrasi / Zacky dan Deni |
| Ruangan | Kapasitas, ranking, pohon/pemeriksaan AVL, log dan visual empat rotasi; MaxHeap/Heap Sort kapasitas Excel; pilih pemakaian Excel atau hasil simulasi | Dua AVL / Wildan & Asep |
| Pilih jadwal | Tujuan jumlah kelas (Greedy) atau total nilai (DP); kombinasi ruang/hari, pilihan metode tabulasi/memoisasi, perbandingan biaya naif vs memo vs tabulasi, tabel DP, pembanding semua kombinasi, timeline, CSV; alokasi kandidat terpilih | DP / Rifqi & Abdur |
| Koneksi ruang | Editor koneksi/biaya asumsi; graf MST, perbandingan, forest, cut/cycle witness, JSON dan 24 benchmark | MST S11: Kruskal + Prim manual |
| Eksperimen | Pengukuran langsung data Excel untuk enam kelompok algoritma, tabel/grafik/CSV; 79 pengukuran utama + 43 tambahan terukur | Wildan dan tim |
| Data & panduan | Lihat/unggah/ganti Excel, catatan pemeriksaan, jalankan 33 pengujian Colab dan unduh hasil | Semua anggota |

## Alur demo

1. **Cari jadwal:** cari nama atau kode pada Excel, misalnya ACC93105. Opsi pasangan memperluas hasil, tidak otomatis menggabungkan peserta.
2. **Antrean:** pilih tanggal, masukkan kelas, lalu klik **Proses permintaan berikutnya**. Pengaturan waktu simulasi dan penjelasan algoritma tersedia di **Pengaturan & penjelasan lanjutan**. Tombol lanjut memilih riwayat antrean sebagai sumber alokasi.
3. **Simulasi alokasi:** pilih minggu dan kelas. Secara default ruang simulasi dimulai kosong. Jalankan alokasi, baca hasil dan alasan penolakan. Kelas yang sudah dialokasikan tidak dihitung dua kali.
4. **Ruangan:** pilih **Hasil simulasi alokasi** untuk melihat perubahan pemakaian pada minggu yang sama. Pembatalan alokasi memperbarui Hash dan kedua AVL melalui fungsi Colab.
5. **Eksperimen:** ukur Excel aktif, atau baca arsip benchmark Colab. **Data & panduan** menyediakan tombol menjalankan T01–T33.

## Sumber dan batas simulasi

- Dataset bawaan memuat 243 jadwal, 122 kode MK, 61 baris pasangan, dan 16 ruang. Jumlah dibaca ulang dari workbook aktif. Empat lembar wajib: jadwal_uts, mata_kuliah, pasangan_int_nas, ruang.
- Mengunggah workbook baru mereset simulasi alokasi, antrean, dan hasil pengukuran lama. Data tersimpan hanya selama sesi; unduh CSV untuk menyimpan hasil. Berkas Excel asli tidak diubah.
- Kapasitas menggunakan **kapasitas_asumsi**, bukan kapasitas resmi. Fasilitas/jenis ruang serta konflik dosen/mahasiswa belum dimodelkan. Model slot LAB tetap mengikuti Colab; perubahan aturan LAB sedang ditunda.
- Semua kandidat FEB adalah ujian, termasuk LAB: prioritas awal 1 dan bobot 10. Prioritas khusus dapat diubah pada antrean simulasi. Aging tidak mengubah urutan jika seluruh prioritas tetap 1. Jam masuk antrean adalah simulasi terpisah dari jam ujian.
- Alokasi memakai PQ dan DP per batch ruang/hari, dengan percobaan ruang lain yang terbatas. Ini simulasi alternatif, bukan perubahan atau pembatalan ujian resmi dan bukan jaminan optimum global beberapa ruang.
- Default alokasi mengecualikan online dan baris dengan catatan. Alasannya dapat dilihat; opsi menyertakan baris pemeriksaan tersedia. Pada data bawaan tanpa penggabungan: 196 kandidat, 189 alokasi, 7 penolakan dan 47 baris dikecualikan.
- Penggabungan memerlukan pemilihan pasangan Excel untuk dikonfirmasi dalam simulasi. Fungsi Colab memeriksa hari/jam/ruang/dosen/kategori dan kapasitas; ID asal disimpan. Konfirmasi lokal tidak mengubah status resmi Excel.
- Eksperimen langsung memakai Excel aktif dengan helper pengukuran Colab. Arsip 79 benchmark utama dan 43 benchmark tambahan berisi **input sintetis untuk uji performa**, terpisah dari sumber jadwal. Angka diukur pada Python lokal; metadata mesin/seed/run tersedia. Fixture penjelasan/tes diberi label terpisah dan tidak menjadi kandidat alokasi.
- Memori benchmark adalah alokasi Python tambahan selama action, tidak termasuk setup atau seluruh RAM. Perbandingan memakai operasi/input yang sama; DP besar tidak dicampur dengan brute force kecil.

## Sinkronisasi dan verifikasi

```sh
python scripts/sync_notebook.py references/UTS_Group2_Smart_Campus.ipynb 2026-10-26T17:48:23.606Z
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Script mengekstrak definisi/decorator tanpa mengeksekusi sel notebook. Modul algoritma dan layanan tetap identik dengan sumber Colab, diperiksa lewat AST. Metadata/hash snapshot berada di references/manifest.json dan references/colab-status.json. Arsip benchmark memiliki provenance terikat hash notebook.

campus/workspace.py mengelola sesi dan pelacakan kelas asal; campus/full_pages.py merender fitur tambahan; campus/excel_benchmark.py mengukur data Excel dengan helper Colab. Demo dan fixture uji terpisah dari modul layanan aplikasi. Pengujian mencakup alokasi/pembatalan, penggabungan, pergantian workbook, kedua indeks, enam kelompok benchmark Excel, dan interaksi UI.

## Sumber

- [Notebook Colab](https://colab.research.google.com/drive/1D0LHKRtp9G-LxFdl0vKPz_Gmcy5VNdS0)
- [Excel FEB](https://drive.google.com/file/d/14ssmxLs2leJDNAUBvTpuk2ukbxm8b-iP/view)

## Peningkatan UAS terpilih · 26 Oktober

- Heap/PQ: MaxHeap, Heap Sort, change-priority, key `(prioritas efektif, counter)` FIFO, trace terbatas. Contoh dispatcher 122 event menunjukkan waktu tunggu Event 600 → 30 menit pada pola uji tersebut, bukan jaminan bebas starvation untuk semua beban.
- Hash: chaining dibandingkan linear probing; tombstone mempertahankan jalur lookup setelah delete, counter probes/collisions/rehash dibedakan.
- Trie: delete satu ID atau seluruh kata, pruning cabang kosong, DFS iteratif dengan deduplikasi Hash. Ranking frekuensi belum dibuat.
- AVL: log LL/RR/LR/RL dengan cuplikan sebelum/sesudah; validator tidak menambah node-access counter.
- DP: implementasi tabulasi dan memoization PR #17 dipertahankan. DP dan Greedy memakai merge sort manual untuk urutan kandidat. Rekursi naif dan brute force hanya pembanding kecil, dipicu tombol.
- Greedy: earliest-finish memaksimalkan jumlah kelas; earliest-start pembanding. Argumen pertukaran, counterexample bobot (4 vs 10), dan 100 kasus acak dicocokkan dengan brute force kardinalitas.

72 tes proyek lulus; 33 skenario notebook lulus (sebagian dipanggil oleh tes proyek, tidak dijumlahkan). Benchmark memakai satu warm-up, median lima run dan memori tambahan. Semua ruang dan jadwal tetap berasal dari Excel aktif; sisi dan biaya MST adalah asumsi simulasi eksplisit yang disetujui pengguna. RB/B-Tree, DP lanjut, shortest path, dan flow tetap di luar peningkatan ini.


## MST S11 · tambahan 27 Oktober

Halaman **Koneksi ruang** memakai daftar ruang workbook aktif untuk simulasi jaringan termurah. **Excel tidak menyediakan koneksi, jarak, atau biaya**: seluruh sisi/bobot adalah asumsi yang bisa diedit. Template 16 ruang menghasilkan 15 koneksi terpilih dengan biaya 17 satuan simulasi. Kedua metode manual (Kruskal Union-Find rank/compression dan lazy Prim min-heap) diperiksa validator struktur dan cycle property; graf terputus menghasilkan minimum spanning forest. MST tidak mengubah jadwal atau alokasi.

Editor menyimpan perubahan selama sesi dan mereset ketika workbook diganti. Hasil lama disembunyikan setelah input berubah sampai dihitung ulang. Diagram, tabel dan JSON mencantumkan asumsi; panel lanjutan berisi cut witness dan 24 benchmark sparse/dense/forest dengan lima run. Penjelasan dan batas: [docs/MST.md](docs/MST.md). Catatan draft laporan: [docs/REVIEW_LAPORAN_UAS.md](docs/REVIEW_LAPORAN_UAS.md).

Untuk merekam ulang bukti secara lengkap:

```sh
python scripts/verify_completed_notebook.py references/UTS_Group2_Smart_Campus.ipynb
python scripts/record_verified_artifacts.py
python scripts/sync_notebook.py
python -m pytest -q
```

Snapshot lokal tidak otomatis dipublikasikan oleh script; pembaruan notebook bersama dilakukan setelah memeriksa tidak ada perubahan anggota lain dan membaca balik bytes hasil publikasi.
