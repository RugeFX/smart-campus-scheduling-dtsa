## 8. Percobaan Kecepatan — Wildan dan tim

**Rangkaian benchmark sudah diimplementasikan dan dijalankan.** Ada 58 baris hasil
aktual untuk 240, 1.000, 10.000, dan 100.000 input, ditambah pembanding DP kecil.
Semua menggunakan data **sintetis**, bukan Excel FEB. Angka 240 adalah ukuran
percobaan; jumlah baris Excel tetap dihitung dari berkas impor.

| Percobaan | Pembanding dan kendali |
|---|---|
| Heap build | Heapify diukur sendiri; tidak dibandingkan dengan satu pop |
| Heap push N | Sorted-list insertion untuk N input yang sama |
| Heap push-pop | Maksimal 100 pasangan operasi pada antrean awal berukuran N yang sama |
| Hash get | 100 key yang sama, 50% ditemukan; pembanding linear scan |
| Trie sparse | Prefix sama, satu hasil pada semua ukuran; pembanding startswith |
| Trie dense | Prefix banyak hasil hanya N≤1.000; biaya output/deduplikasi dicatat |
| AVL update + top-k | Delete/insert satu key dan k=10; list melakukan update+sort+ambil k |
| DP skala besar | Berdiri sendiri; tidak dibandingkan langsung dengan BF input kecil |
| DP vs BF | Input identik N=8,12,15; nilai hasil harus sama sebelum diukur |

Setiap waktu adalah **median 5 pengulangan** dengan seed 42. State mutable dibuat
ulang di luar timer; struktur read-only boleh dipakai ulang dengan counter direset.
Setup dan pembacaan counter berada di luar timer. Hasil menyimpan waktu setiap run,
jumlah perbandingan Heap, probe Hash, dan rotasi AVL yang benar-benar dihasilkan
operasi. Tidak ada counter Trie yang direka.

`tracemalloc` dijalankan terpisah untuk **alokasi Python tambahan selama action**.
Angka `peak_bytes` bukan seluruh RAM proses, bukan memori struktur yang sudah
dibangun di setup, dan tidak mencakup seluruh alokasi native. Untuk Heap build,
pembangunan memang berada di action sehingga biaya pembangunannya ikut terukur.

Sel menulis `smart_campus_benchmark.csv`, metadata lingkungan `.json`, grafik
`.html`, dan spesifikasi `.vl.json`. Grafik dikelompokkan per operasi; sumbu log
dan skala vertikal independen tidak boleh dibaca sebagai peringkat seluruh algoritma.
HTML memerlukan internet untuk memuat pustaka grafik. Pada Colab grafik juga
ditampilkan inline jika IPython tersedia.

Output tersimpan diverifikasi dengan Python lokal, **bukan klaim pengukuran pada
mesin Colab**. Versi Python, arsitektur, sistem operasi, waktu UTC, seed, jumlah run,
dan fingerprint input dicatat di `benchmark_environment`. Jalankan ulang di Colab
untuk memperoleh angka mesin tersebut. Implementasi Python manual bisa kalah dari
list bawaan yang operasinya memakai C; hasil tidak dipaksa sesuai ekspektasi teori.

`RUN_BENCHMARKS=True` menjalankan seluruh rentang. Pengguna dapat menggantinya ke
False untuk melewati pengukuran saat sedang memperbaiki kode. Pemanggilan
`run_benchmarks(sizes=[240], repeat=5)` tersedia untuk percobaan singkat.

UI Streamlit dasar sudah tersedia sebagai proyek terpisah. Pekerjaan pada bagian
ini menyediakan layanan simulasi dan kontrak hasil; sinkronisasi kontrol booking
dan dashboard benchmark UI merupakan pekerjaan terpisah dari penyelesaian Colab ini.
