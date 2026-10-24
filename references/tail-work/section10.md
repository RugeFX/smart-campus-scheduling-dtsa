## 10. Langkah Menuju UAS dan Review

| Tahap | Hasil | Status implementasi notebook |
|---|---|---|
| M1 | Impor/validasi Excel dan generator | Tersedia |
| M1–M2 | Heap/PQ dan Hash | Tersedia, uji T01–T06 |
| M2–M3 | Trie dan dua AVL termasuk delete | Tersedia, uji T07–T12 dan uji delete tambahan |
| M3–M4 | DP dan pembanding semua kombinasi | Tersedia, T13–T15 |
| M4–M5 | Integrasi, 18 pengujian, eksperimen | Tersedia; hasil aktual dicetak pada bagian 6–8 |
| M6 | Laporan dan latihan demo kelompok | Penjelasan di bawah dapat dipakai untuk latihan |

M1 mengikuti “minggu pertama setelah UTS” pada PPT; tabel ini tidak menetapkan
tanggal UAS atau mengklaim anggota sudah melakukan presentasi.

### Checklist yang dapat diverifikasi melalui kode

- [x] Heap/PQ, Hash, Trie, AVL termasuk delete, dan DP terimplementasi manual.
- [x] Integrasi memakai kontrak Room/ClassRecord/ScheduleRequest yang sama.
- [x] Kapasitas asumsi, bobot kegiatan, waktu tunggu simulasi, dan data sintetis diberi label.
- [x] Hash dan kedua indeks AVL diperiksa konsisten setelah pembaruan.
- [x] T01–T18 memiliki fungsi terdaftar dan hasil eksekusi aktual; fixture DP bernilai 19.
- [x] Benchmark membandingkan operasi/input setara, median 5 run, memori terpisah.
- [x] Kode kelas/baris Excel dan source_ids gabungan tersedia untuk penelusuran.
- [x] Retry berhenti; strategi beberapa ruang dan batas optimalitas dijelaskan.

### Hal yang memerlukan konfirmasi manusia/data resmi

Kapasitas_asumsi belum kapasitas resmi; pasangan INT–NAS pada Excel belum
dikonfirmasi. Konflik tiga ruang antar-PDF, durasi tertentu, metadata fasilitas,
dan konflik dosen/mahasiswa belum diselesaikan oleh algoritma. ID dosen/pengawas
mengikuti data impor; kecukupan anonimisasi untuk publikasi perlu ditinjau pemilik
data. Laporan/presentasi akhir dan pemahaman setiap anggota tidak diklaim selesai
hanya karena pengujian program lulus.

### Alur penjelasan untuk demo

1. Tunjukkan jumlah dan catatan Excel bagian 0.4; bedakan data resmi/asumsi/fixture.
2. Jelaskan Hash untuk kode lengkap dan Trie untuk awalan/pasangan.
3. Jelaskan PQ sebagai urutan penanganan, AVL sebagai indeks kapasitas/pemakaian,
   dan DP sebagai pemilih kombinasi pada satu ruang/hari.
4. Jalankan bagian 6: fixture 15+20=35, DP=19, serta simulasi berbasis Excel.
   Jelaskan alasan penolakan dan jumlah slot unik, bukan hanya total diterima.
5. Tampilkan T01–T18 dan uji tambahan, kemudian tabel/grafik benchmark beserta
   ukuran, k, jumlah pengulangan, mesin, serta cakupan pengukuran memorinya.
6. Tutup dengan batas model: simulasi tidak menulis jadwal Excel dan bukan optimum
   global, pemeriksaan fasilitas/dosen/mahasiswa masih memerlukan data/aturan.

### Referensi dan adaptasi

Implementasi struktur inti menggunakan kode manual tim; pustaka `heapq` tidak
dipakai sebagai mesin antrean, dan dict tidak menggantikan Hash inti.
`bisect.insort` hanya digunakan sebagai **pembanding sorted list** pada benchmark.
`deepcopy` dipakai untuk staging transaksi, bukan implementasi Hash/AVL pengganti.

| Topik | Rujukan konsep yang dapat ditelusuri |
|---|---|
| Heap/PQ | [Dokumentasi Python — heapq, heap invariant dan priority queue notes](https://docs.python.org/3/library/heapq.html) |
| Hash chaining | [MIT 6.006 — Lecture 08: Hashing with chaining](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/mit6_006f11_lec08/) |
| Trie/prefix | [Princeton Algorithms 4e — §5.2 Tries](https://algs4.cs.princeton.edu/52trie/) |
| AVL/rotasi | [MIT 6.006 — Lecture 7: Binary Trees, Part 2: AVL](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/resources/lecture-7-binary-trees-part-2-avl/) |
| Weighted interval scheduling | [Kevin Wayne, Princeton — Dynamic Programming I, weighted interval scheduling](https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/06DynamicProgrammingI.pdf) |
| Dataset dan implementasi kelompok | [Excel FEB](https://drive.google.com/file/d/14ssmxLs2leJDNAUBvTpuk2ukbxm8b-iP/view) dan notebook ini |

Nomor halaman materi kelas S1–S7 tidak direka karena berkas tersebut belum tersedia
pada workspace tugas ini. Referensi di atas adalah sumber konsep tambahan yang
bernama jelas; bukan klaim telah memetakan halaman materi kelas yang belum dibaca.
