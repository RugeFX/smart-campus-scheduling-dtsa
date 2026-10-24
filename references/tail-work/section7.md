## 7. Pengujian Lengkap — Semua anggota

T01–T18 sudah diimplementasikan dan didaftarkan pada TEST_RUNNERS. RUN_TESTS=True
menjalankan seluruhnya; kolom status berasal dari eksekusi assertion, bukan diisi
manual. Pengujian memakai fixture terkontrol, terpisah dari data aplikasi Excel.

| ID | Input/kondisi | Hasil yang harus diperiksa |
|---|---|---|
| T01 | Campuran empat kategori | Ujian, praktikum, kuliah, event; dalam kategori jam naik |
| T02 | Dua ujian, jam sama | Urutan masuk dipertahankan |
| T03 | Pop antrean kosong | IndexError yang ditangani |
| T04 | Put/get 10 ribu ID unik | Semua data kembali benar |
| T05 | F708 dan F807 pakai hash penjumlahan/8 bucket | Kedua key di chain tetap terbaca |
| T06 | Load factor melewati 0,7 | Ukuran berubah, semua key tetap ada |
| T07 | Prefix ak | ACC13101 dan ACC13102 |
| T08 | Prefix tidak ditemukan | Daftar kosong |
| T09 | Prefix Dasar + tabel pasangan | MGT12119 dan MGT92119 |
| T10 | Insert naik/turun | RR/LL; tinggi dan keseimbangan benar |
| T11 | Insert zig-zag | LR/RL; tinggi dan keseimbangan benar |
| T12 | Peserta 35 | F705, kapasitas 40; peserta 101 → None |
| T13 | 100 kasus acak n≤15 | Nilai DP sama dengan semua kombinasi; hasil valid |
| T14 | Kegiatan tidak bertabrakan, nilai positif | Semua terpilih |
| T15 | Semua saling bertabrakan | Salah satu bernilai paling besar |
| T16 | PQ → pemilihan jadwal → update | Data ruang dan kedua indeks tetap konsisten |
| T17 | Kegiatan ditolak lalu dicoba ruang lain | Diproses sekali per ruang; berhenti saat ruang habis |
| T18 | Gabung pasangan kelas 15+20 | Peserta 35≤40; kelebihan kapasitas ditolak |

Tambahan yang dijalankan: aging/FIFO dan build Heap, 1.000 operasi acak,
Hash update/delete/rehash, alias Trie, seluruh rotasi AVL, delete 200 key acak,
payload kedua indeks, kegagalan transaksi yang disengaja, slot unik,
booking awal, fasilitas eksplisit, ID berulang, input kosong, dan batas minggu.

Kasus DP acak n≤15 dibandingkan dengan brute force pada 100 seed/input yang
terkontrol. Uji retry memeriksa pasangan request–ruang tidak berulang dan berhenti
ketika ruang habis. Uji gabungan mempertahankan source_ids dan menolak kapasitas
berlebih. Kasus gagal menguji penolakan yang diharapkan; tidak dilaporkan sebagai
booking berhasil.
