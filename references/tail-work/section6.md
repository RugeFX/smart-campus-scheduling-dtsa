## 6. Integrasi — Zacky

**Terimplementasi:** penggabungan kelas, pembaruan registry secara transaksional,
antrean PQ, DP per ruang/hari, percobaan ruang alternatif, dan simulasi Excel.
Operasi delete AVL bagian 4 dilengkapi karena diperlukan untuk menghapus key lama.

### Alur dan kontrak

1. `merge_equivalent_classes(records, equivalence_table, room_table)` menerima
   pasangan **eksplisit dua arah yang telah diverifikasi caller**. Hanya kelas dengan
   hari, jam, ruang, dosen yang terisi, dan kategori sama yang digabung. Kedua kode
   pasangan harus hadir; kelas satu kode saja tidak otomatis digabung. Kapasitas
   diperiksa setelah peserta dijumlahkan. Hasil `MergedClassRecord` menyimpan
   `source_ids` dan `course_codes`; ID asal berulang ditolak. Input tidak diubah.
2. `make_room_registry(rooms)` membangun Hash ruang serta AVL kapasitas/pemakaian.
   `update_room_usage(table, usage_avl, room_id, slots, capacity_avl=None)` memvalidasi
   0..15, menghapus key lama, mengganti Room, dan memasukkan key/payload baru.
   Berikan indeks kapasitas sebagai argumen kelima agar **kedua indeks** ikut baru.
   Staging salinan dan validasi selesai sebelum commit; kegagalan uji tidak
   meninggalkan registry setengah berubah. Biaya transaksi mencakup salinan O(R),
   berbeda dari operasi AVL murni O(log R).
3. `schedule_across_rooms(requests, table, capacity_avl, usage_avl, ...)` membangun
   PQ terpisah per tanggal. Prioritas lalu jam lalu FIFO menentukan urutan masukan;
   DP memilih kombinasi bernilai terbesar pada batch **satu ruang/hari**.
   Ruang yang diminta dicoba lebih dahulu, lalu calon ruang menurut kapasitas/ID.
4. Kapasitas, interval booking yang sudah diterima, dan kebutuhan jenis ruang
   eksplisit diperiksa. `required_room_types` opsional; tanpa metadata tersebut,
   fasilitas tidak diklaim sudah diperiksa. `allow_alternative_rooms=False`
   membatasi percobaan pada ruang awal/calon pertama.
5. Permintaan yang tidak terpilih boleh mencoba ruang lain. Setiap pasangan
   `(request_id, room_id)` dicoba paling banyak sekali; maksimal N×R percobaan.
   Booking yang telah diterima tidak digeser pada putaran berikutnya. Hasil memuat
   `bookings`, `rejected` beserta alasan, `attempts`, `tried_rooms`, `priority_order`,
   `total_value`, dan `occupied_slots`. Setiap input berakhir diterima atau ditolak.

### Pemakaian ruang dan kondisi awal

Pemakaian dihitung dari himpunan `(tanggal, indeks slot reguler)` yang tersentuh,
bukan `used_slots += jumlah_kegiatan`. Dua kegiatan bersebelahan pada slot reguler
yang sama menambah **satu** slot unik. Akhir pekan tidak masuk penyebut 15 slot
Senin–Jumat. Input dibatasi satu minggu ISO; minggu berbeda disimulasikan terpisah.

Untuk ruang yang sudah terpakai, berikan `existing_bookings` atau `occupied_slots`
yang sesuai `used_slots`. Angka total saja tidak cukup untuk mengetahui waktu kosong.
Slot terpakai tanpa interval rinci diblokir secara konservatif. Booking awal yang
saling bentrok ditolak sebelum registry diubah.

### Data FEB dan contoh pengujian

`simulate_feb_allocation(data_bersih, bahan_pencarian_feb)` memakai kelas dari Excel.
**Simulasi dimulai dari ruang kosong**, bukan mengubah atau memvalidasi seluruh
jadwal resmi. Kapasitas memakai `kapasitas_asumsi`; jenis/fasilitas ruang Unknown.
Baris online, durasi/ruang yang perlu pemeriksaan, dan input tidak valid dilaporkan
terpisah beserta baris Excel. Semua kandidat adalah ujian prioritas 1/bobot 10.
Pasangan INT–NAS pada Excel belum dikonfirmasi resmi sehingga tidak digabung otomatis.

Fixture J1–J6 tetap khusus pengujian: nilai DP 19 dan 2 slot reguler unik.
Fixture pasangan 15+20=35 memeriksa aturan penggabungan, bukan fakta kapasitas FEB.

**Batas:** strategi beberapa ruang tidak menjamin optimum global. DP tidak
menjadikan prioritas Heap sebagai batas wajib, belum memodelkan konflik
dosen/mahasiswa atau kegiatan wajib. Semua alokasi berada di memori simulasi;
fungsi tidak menulis perubahan ke Excel.
