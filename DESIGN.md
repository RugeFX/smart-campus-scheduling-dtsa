# Smart Campus

## Context

Dashboard dipakai mahasiswa dan dosen pada layar laptop/proyektor di ruang kelas terang. Tema terang menjaga keterbacaan tabel dan jadwal; kontrol standar Streamlit mempertahankan interaksi yang dikenal.

## Palette

Strategi restrained. Putih murni untuk area kerja, abu netral untuk navigasi, aksen mustard gelap dari seed hue 91 untuk tindakan dan kegiatan terpilih. Ink dan teks sekunder bernuansa slate.

```css
--background: oklch(1 0 0);
--surface: oklch(.96 0 0);
--ink: oklch(.27 .02 240);
--muted: oklch(.47 .02 240);
--primary: oklch(.48 .10 91);
--accent: oklch(.31 .05 235);
```

Streamlit dan grafik membutuhkan representasi warna hex yang kompatibel; CSS memakai OKLCH. Teks tombol putih dengan primary gelap. Status selalu disertai label kata.

## Type and layout

Satu keluarga sans bawaan Streamlit. Heading 2.25rem di desktop, 1.9rem pada layar sempit; section 1.4rem; subheading 1.1rem. Letter spacing heading -0.035em. Area kerja maksimum 1280px. Sidebar merangkum navigasi dan status sesi.

Timeline kegiatan menjadi ciri utama: waktu horizontal, nama vertikal, pilihan DP terlihat langsung. Form dan hasil memakai dua kolom pada layar lebar dan menyusun vertikal pada layar sempit. Tidak ada grid kartu dekoratif.

## Interaction and inclusion

Kontrol native Streamlit, fokus keyboard jelas, label selalu tersedia, tabel dapat digulir. Grafik mempunyai tooltip; keputusan juga tersedia dalam tabel/CSV. Tidak ada animasi dekoratif; reduced-motion mematikan transisi. Detail implementasi tersedia melalui expander pada konteks yang relevan.

Sidebar memakai tombol navigasi selebar kolom dengan ikon Material, teks rata kiri, area klik minimal 44px, dan latar berwarna pada halaman aktif. Pilihan isi/form tetap memakai kontrol sesuai kebutuhannya.

Halaman antrean menampilkan pemilihan kelas dan kelas berikutnya sebagai fokus utama. Daftar menunggu dan riwayat memakai tab. Jam simulasi, aging, counter, pohon Heap dan data sumber tersedia dalam satu panel lanjutan yang tertutup saat awal.
