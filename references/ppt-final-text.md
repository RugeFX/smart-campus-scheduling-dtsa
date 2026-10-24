## Slide 1
01
Smart
Campus
Pencarian ruangan dan
pemilihan jadwal
UTS DtSA
Kelompok 2


## Slide 2
Kebutuhan pengelolaan ruangan
02
Pencarian
Nama belum lengkap dan ID ruangan perlu menghasilkan informasi yang sesuai.
Pemilihan ruangan
Kapasitas harus cukup untuk seluruh peserta.
Pengaturan kegiatan
Permintaan memiliki prioritas dan waktu kegiatan bisa bertabrakan.
35
peserta
Kapasitas terkecil
yang cukup: 40 kursi


## Slide 3
Lima kebutuhan, lima pilihan algoritma
03
Kebutuhan sistem
Operasi utama
Pilihan
Prioritas permintaan
Ambil permintaan terpenting berikutnya
Heap + Priority Queue
Pencarian ruangan
Cari berdasarkan ID lengkap
Hash Table
Pencarian nama
Temukan nama dari awalan
Trie
Pilihan kapasitas
Cari kapasitas terkecil yang cukup
AVL Tree
Pemilihan jadwal terbaik
Pilih kegiatan tanpa bentrok
Pemrograman Dinamis
Urutan permintaan dan kombinasi jadwal menjawab kebutuhan yang berbeda.


## Slide 4
Heap untuk prioritas permintaan
04
Kegiatan
Prioritas
Ujian
1
Praktikum
2
Kuliah
3
Acara kampus
4
Angka lebih kecil
didahulukan


## Slide 5
Urutan penanganan permintaan
05
Urutan
Permintaan
Prioritas
1
Ujian Basis Data
1
2
Ujian Pemrograman
1
3
Praktikum Jaringan
2
4
Kuliah Algoritma
3
5
Seminar Kampus
4
Prioritas sama
Permintaan yang datang lebih awal diproses lebih dahulu.
Permintaan baru
Heap menyesuaikan urutan tanpa mengurutkan ulang seluruh daftar.


## Slide 6
Hash Table untuk pencarian ID
06
ID yang sudah diketahui
Cari LAB-301 untuk memperoleh detail Lab Komputer 301.
LAB-301
Lab Komputer 301
Kapasitas 40 peserta
Bucket
ID yang tersimpan
0
R101, LAB-301
1
Kosong
2
R202
3
AULA
Dua ID pada bucket yang sama
tetap tersimpan melalui chaining.


## Slide 7
Trie untuk pencarian awalan nama
07
Pengguna mengetik “Dat”
Jalur karakter
yang sama
Sistem menelusuri awalan, lalu menampilkan nama yang sesuai.
Huruf besar dan kecil menghasilkan pencarian yang sama.


## Slide 8
AVL untuk memilih kapasitas ruangan
08
Ruangan
Kapasitas
R101
30
LAB-301
40
R202
40
AULA
120
35 peserta
LAB-301
40 kursi
Pilih kapasitas terkecil
yang masih mencukupi.
Kapasitas sama tetap memakai ID ruangan yang berbeda.


## Slide 9
Keseimbangan AVL dan rotasi
09
Selisih tinggi
kiri dan kanan
−1, 0, atau 1
LL: rotasi kanan
RR: rotasi kiri
LR dan RL: dua rotasi


## Slide 10
DP untuk pemilihan jadwal terbaik
10
Kegiatan
Waktu
Nilai
A
08.00–10.00
5
B
09.00–11.00
8
C
11.00–13.00
4
D
13.00–15.00
6
B + C + D
18
Total nilai kepentingan
Waktu tidak bentrok
Perhitungan awal: satu ruangan dalam satu hari.


## Slide 11
Perhitungan DP: ambil atau lewati
11
Lewati kegiatan i
Gunakan nilai terbaik sebelumnya.
Ambil kegiatan i
Nilai kegiatan i + nilai terbaik
dari kegiatan yang sudah selesai.
DP[i] = max(DP[i−1], nilai_i + DP[p(i)])
Kegiatan
p(i)
DP[i]
A
0
5
B
0
8
C
2
12
D
3
18
Nilai awal DP[0] = 0
p(i): kegiatan terakhir sebelum i yang selesai paling lambat saat i dimulai.


## Slide 12
Alur penggunaan sistem
12
Langkah
Bagian sistem
Hasil
1
Cari mata kuliah atau dosen
Nama yang sesuai dengan awalan
2
Cari detail dan kapasitas ruangan
Informasi dan pilihan ruangan yang cukup
3
Masukkan permintaan kegiatan
Urutan penanganan menurut prioritas
4
Evaluasi kandidat jadwal
Kombinasi tanpa bentrok dengan nilai terbaik
Kapasitas menentukan kecocokan ruangan. Waktu menentukan bentrok jadwal.


## Slide 13
Kompleksitas operasi utama
13
Algoritma
Operasi
Waktu
Heap
Tambah / ambil teratas
Lihat teratas
O(log n)
O(1)
Hash Table
Cari ID, rata-rata
Kasus terburuk
O(1)*
O(n)
Trie
Cari nama lengkap
Awalan dan seluruh hasil
O(m)
O(p + s + k)
AVL
Cari kapasitas yang cukup
Tampilkan seluruh urutan
O(log n)
O(n)
DP
Urutkan, hitung, ambil hasil
O(n log n)
*ID dianggap pendek, distribusi hash baik, dan jumlah entri per bucket terkendali.


## Slide 14
Rencana pengujian
14
Bagian
Kasus uji
Hasil yang diharapkan
Heap
Prioritas sama
Urutan kedatangan tetap
Hash
Dua key pada satu bucket
Kedua ruangan tetap ditemukan
Trie
Dat dan dat
Daftar nama yang sama
AVL
35 dan 121 peserta
LAB-301 dan tidak ada ruangan
DP
Kandidat A–D
B + C + D, nilai 18
Implementasi algoritma masih menjadi pekerjaan lanjutan pada scaffold.


## Slide 15
Pembagian penjelasan kelompok
15
Anggota
Bagian
Fokus penjelasan
Zacky
Overview dan integrasi
Kebutuhan sistem dan hubungan antarbagian
Ikin + Deni
Heap + Priority Queue
Konsep heap dan urutan permintaan
Adit
Hash Table
ID ruangan dan collision
Zilan
Trie
Pencarian berdasarkan awalan
Wildan + Asep
AVL Tree
Keseimbangan dan kapasitas ruangan
Rifqi + Abdur
Pemrograman Dinamis
Tujuan, perhitungan, dan pilihan kegiatan


## Slide 16
Batas rancangan dan referensi
16
Cakupan saat ini
DP menghitung satu ruangan per hari.

Nilai kepentingan pada contoh
masih perlu aturan kelompok.

Kegiatan wajib dan konflik dosen
memerlukan aturan tambahan.
Dasar konsep
Dokumentasi Python: heapq
Princeton: Hash Table
Princeton: Trie
MIT: AVL Tree
Princeton: Pemrograman Dinamis
Kasus dan dataset mengikuti notebook Smart Campus kelompok.
