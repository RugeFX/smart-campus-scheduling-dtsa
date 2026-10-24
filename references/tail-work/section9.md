## 9. Ringkasan Biaya Operasi

| Struktur/layanan | Operasi | Waktu | Batas implementasi |
|---|---|---|---|
| Heap/PQ | push/pop; peek | O(log n); O(1) | Hash posisi rata-rata O(1), key pendek |
| Heap/PQ | build; aging seluruh key | O(n); O(n) | Heapify dari bawah, counter FIFO tetap |
| Heap/PQ | pratinjau semua urutan | O(n log n) | Pop pada salinan, ruang O(n) |
| Hash | put/get/delete | Rata-rata O(L), terburuk O(L+n) | L=panjang key; O(1) bila L dibatasi |
| Hash | rehash | O(total panjang key + bucket baru) | Pertumbuhan bucket menjaga load |
| Trie | insert/exact | O(L) rata-rata per jalur | Anak menggunakan Hash tim |
| Trie saat ini | autocomplete | O(p+s+a×k) batas atas | Deduplikasi hasil memakai list membership |
| AVL | insert/delete/ceiling | O(log R) | Delete melakukan rebalance sepanjang jalur balik |
| AVL | top-k | O(log R+k) | Reverse inorder, tanpa sort seluruh ruang |
| DP | persiapan+tabel+traceback | O(n log n), ruang O(n) | Satu batch ruang/hari |
| Brute force | semua subset | O(2^n×n) | Hanya N≤15 pada pengujian/benchmark |
| Transaksi registry | salin, validasi, update satu ruang | O(R+bucket) rata-rata, ruang O(R+bucket) | Delete/insert AVL di dalamnya O(log R) |

n=jumlah permintaan/entri, R=jumlah ruang, L=panjang key/nama, p=panjang prefix,
s=jumlah simpul cabang yang dikunjungi, a=referensi ID yang diperiksa,
k=jumlah ID hasil unik. Untuk prefix dengan semua ID unik, komponen deduplikasi
Trie dapat menjadi O(k²). Karena itu benchmark sparse/dense dipisah; biaya
O(p+s+k) pada rancangan ideal bukan jaminan implementasi deduplikasi list ini.

Integrasi bukan satu operasi O(n log n). Selain DP batch, ada daftar calon ruang,
penelusuran riwayat percobaan, pemeriksaan interval booking, serta staging registry.
Batas N×R menyatakan **jumlah percobaan ruang**, bukan batas total operasi dasar.
Kedua indeks AVL dan Hash tetap harus konsisten setelah keputusan.

Tabel kompleksitas menjelaskan pertumbuhan teoretis dengan asumsi yang tercatat.
Angka median benchmark menjelaskan implementasi dan mesin tertentu; satu run atau
satu ukuran tidak membuktikan kompleksitas asimtotik maupun optimum global alokasi.
