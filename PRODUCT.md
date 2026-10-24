# Product

## Register

product

## Users

Kelompok 2 UTS DtSA dan dosen saat demonstrasi algoritma Smart Campus. Mereka mencari jadwal FEB dan mencoba permintaan ruangan dalam simulasi lokal.

## Product Purpose

Membungkus algoritma Colab sebagai aplikasi Streamlit dengan Excel FEB sebagai satu-satunya sumber data UI. Definisi algoritma dan layanan mengikuti snapshot Colab lengkap. Pengguna secara eksplisit meminta semua data aplikasi berasal dari Excel; penghubung FEB yang sudah tersedia dipakai tanpa mengubah flag pada snapshot asli. Hasil harus dapat ditelusuri ke baris Excel dan algoritma notebook.

## Brand Personality

Rapi, jelas, tenang. Bahasa Indonesia; disetujui pengguna sebagai arah dashboard demo.

## Anti-references

Hindari dekorasi yang mengalihkan dari jadwal, tabel, dan keputusan; hindari angka hasil eksperimen buatan dan klaim kapasitas resmi.

## Design Principles

- Pencarian dan keputusan kegiatan menjadi tindakan utama.
- Pisahkan data FEB dan simulasi booking dengan label yang terlihat.
- Tampilkan alasan hasil dan batas algoritma dekat hasilnya.
- Detail teknis disediakan lewat panel penjelasan untuk presentasi.
- Seluruh pencarian, input antrean, ruangan, ranking, dan kandidat DP berasal dari workbook Excel aktif; tidak ada pilihan data contoh di UI.
- Pengguna meminta versi penuh Streamlit yang mengikuti Colab lengkap. Semua layanan dan algoritma diekstrak tanpa mengubah definisi sumber. Simulasi alokasi, penggabungan terkonfirmasi untuk simulasi, pembatalan, perubahan kedua AVL, eksperimen dan 18 pengujian tersedia.
- Eksperimen langsung menggunakan Excel aktif. Arsip 58 benchmark Colab diberi label input sintetis dan mesin lokal, terpisah dari data jadwal. Fixture uji hanya dijalankan melalui panel pengujian.
- Pembahasan perubahan aturan LAB ditunda sesuai permintaan pengguna. Slot dan aturan waktu tetap mengikuti snapshot Colab saat ini.

## Accessibility & Inclusion

Kontrol standar Streamlit dengan label, navigasi keyboard, kontras terbaca, tanpa animasi dekoratif. Status memakai teks selain warna.
