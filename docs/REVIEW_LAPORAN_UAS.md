# Catatan sinkronisasi draft laporan anggota

Sumber yang dibaca: `Laporan_UAS_DSA_Group2.docx` dari Downloads. File asli belum diedit. Catatan ini memisahkan pembaruan yang dibuktikan repo dari eksperimen tambahan anggota yang perlu disertai sumbernya.

## Pembaruan yang diperlukan

| Bagian | Draft saat ditinjau | Pembaruan berdasarkan implementasi |
|---|---|---|
| Cakupan | S9–S12 belum tersedia; belum ada MST | Tambahkan Greedy S10 dan MST S11 (Kruskal + Prim). S9 DP lanjut, S12 shortest path, S13 flow dan S7 RB/B-Tree belum diimplementasikan pada main yang diperiksa |
| Heap/PQ | MaxHeap/heap sort belum ada; key memasukkan jam mulai | MaxHeap/heap sort manual tersedia. Key PQ sekarang `(prioritas efektif,counter masuk)` sehingga FIFO berlaku per prioritas, terlepas dari jam ujian |
| Hash | Open addressing belum ada | Linear probing manual, tombstone, update setelah tombstone, load-factor benchmark |
| Trie | Delete belum ada | Delete ID/kata dan pruning; DFS iteratif, deduplikasi Hash |
| Greedy | Belum masuk | Earliest-finish untuk jumlah kelas; argumen pertukaran; pembanding earliest-start; beda tujuan dari weighted DP |
| MST baru | Belum ada | Tambahkan node Excel, asumsi sisi/bobot, kedua metode manual, validator minimalitas/cut witness, forest, 24 benchmark dan screenshot |
| Pengujian | 49 pytest, 19 notebook | Ambil angka terbaru dari keluaran pytest dan `references/verification.json`; T01–T33 terdaftar setelah MST. Kedua jumlah tidak dijumlahkan karena sebagian skenario dijalankan oleh pytest |
| Metode eksperimen | Disebut tanpa warm-up; metadata mesin lama | Satu warm-up, lima run, median dan waktu mentah; setup/validator di luar timer, peak Python memory terpisah. Cantumkan timestamp/hash pengukuran baru |
| Klaim rubrik | Dua belas sesi disebut opsional | Tulis cakupan implementasi yang dipilih dan sesi yang belum dipenuhi. Jangan menyatakan ada pembebasan kewajiban tanpa arahan dosen |

## Bagian yang belum aman dijadikan klaim hasil

- Draft memuat Lingkungan B dan menyebut `docs/laporan/experiments_report.py`/`build_report.py`. Kedua berkas tidak ditemukan pada main saat ditinjau. Simpan eksperimen anggota tersebut, tetapi minta kode, input, CSV mentah, dan metadata sebelum menyatukannya dengan pengukuran repo. Ketiadaan pada main tidak membuktikan eksperimen itu tidak dikerjakan.
- Flow S13 masih ditulis “sedang dikerjakan”. Tidak ada implementasi flow pada main yang diperiksa. Hipotesis flow ≥189 belum menjadi hasil teruji. Model class→room-slot dengan kapasitas satu perlu memodelkan interval yang menyentuh beberapa slot; memilih satu slot saja tidak menjamin bebas bentrok sepanjang interval.
- Hasil 189 diterima / 7 ditolak / 47 dikecualikan telah terulang pada notebook baru. Jumlah percobaan penempatan atau identitas penolakan lain harus diperiksa lagi setelah perubahan FIFO sebelum disalin dari hasil lama.
- Screenshot, NIM/kontribusi/commit, beberapa field lingkungan, dan bagian flow masih memiliki placeholder. Isi dengan bukti aktual atau nyatakan keterbatasannya.
- Daftar penggunaan AI perlu mengikuti pemakaian aktual, termasuk bantuan Codex pada implementasi/verifikasi ini.

## Bahan MST siap disisipkan

Gunakan `docs/MST.md`, CSV dan metadata pengukuran, keluaran T29–T33, serta halaman Koneksi ruang. Hasil template: 16 node Excel, 22 sisi asumsi, 15 sisi terpilih, biaya simulasi 17, satu komponen. Jangan menyebutnya pengukuran jarak atau biaya pemasangan kampus nyata.

Tabel perbandingan metode dan diagram/benchmark MST dapat menjadi bukti baru pada metode, hasil, pembahasan dan lampiran. Ruang lingkup laporan perlu mengakui tambahan model koneksi ruang sebagai simulasi terpisah dari alokasi jadwal.
