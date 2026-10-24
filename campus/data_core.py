# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from datetime import datetime, date, time
import re
import pandas as pd
from .models import SearchEntry

KOLOM_WAJIB = {
    "jadwal_uts": ["hari", "mulai", "selesai", "durasi_menit", "kode_mk", "nama_mk",
                   "prodi_mk", "tipe_kelas", "jenis_sesi", "sks", "kode_kelas", "angkatan",
                   "peserta", "sifat_ujian", "mode_ujian", "ruang", "dosen_id", "pengawas_id",
                   "keterangan", "prodi_dokumen"],
    "mata_kuliah": ["kode_mk", "nama_mk", "tipe_kelas", "prodi_mk", "jumlah_kelas"],
    "pasangan_int_nas": ["kode_mk_int", "nama_int", "kode_mk_nas", "nama_nas", "metode", "status"],
    "ruang": ["ruang", "gedung", "lantai", "sesi_ujian", "peserta_maks_per_kelas",
              "peserta_maks_per_slot", "kapasitas_asumsi"],
}

BULAN = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
         "jul": 7, "agu": 8, "ags": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

PERBEDAAN_RUANG_PDF = pd.DataFrame([
    ["2217/BIKM", "F704", 1, "F708", 1],
    ["2185/BIKM", "F804", 3, "F703", 1],
    ["2226/AIKM", "F805", 3, "F708", 2],
], columns=["kode_kelas", "ruang_manajemen", "halaman_manajemen",
            "ruang_akuntansi", "halaman_akuntansi"])

def rapikan_teks(value):
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        hasil = re.sub(r"\s+", " ", value).strip()
        return hasil if hasil else pd.NA
    return value

def baca_tanggal(value):
    if pd.isna(value):
        return pd.NaT
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(value).normalize()
    teks = str(value).split(",")[-1].strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", teks):
            return pd.Timestamp(date.fromisoformat(teks))
        cocok = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", teks)
        if cocok:
            d, bulan, y = cocok.groups()
            return pd.Timestamp(date(int(y), BULAN[bulan.lower()], int(d)))
    except (ValueError, KeyError):
        pass
    return pd.NaT

def baca_jam(value):
    if pd.isna(value):
        return pd.NA
    if isinstance(value, (datetime, time)):
        return value.hour * 60 + value.minute if value.second == 0 else pd.NA
    cocok = re.fullmatch(r"(\d{1,2})[.:](\d{2})", str(value).strip())
    if cocok:
        jam, menit = map(int, cocok.groups())
        if 0 <= jam <= 23 and 0 <= menit <= 59:
            return jam * 60 + menit
    return pd.NA

def rapikan_dan_validasi(data, perbedaan_ruang=PERBEDAAN_RUANG_PDF):
    bersih, masalah = {}, []

    def catat(tabel, mask, jenis, kolom, detail):
        mask = pd.Series(mask, index=tabel.index).fillna(False).astype(bool)
        for _, row in tabel.loc[mask].iterrows():
            masalah.append({
                "lembar": row["lembar_sumber"], "baris_excel": row["baris_excel"],
                "kode": row.get("kode_kelas", row.get("kode_mk_int", row.get("kode_mk", row.get("ruang")))),
                "jenis": jenis, "kolom": kolom, "detail": detail,
            })

    def bilangan_bulat(tabel, nama, minimum=0):
        angka = pd.to_numeric(tabel[nama], errors="coerce")
        sah = angka.notna() & angka.ge(minimum) & angka.mod(1).eq(0)
        # Nilai yang gagal dibaca ditandai, tidak diganti menjadi nol.
        catat(tabel, ~sah, "angka_tidak_valid", nama, f"Harus bilangan bulat minimal {minimum}.")
        tabel[nama] = angka.where(sah).astype("Int64")

    for nama, asli in data.items():
        tabel = asli.copy(deep=True)
        for kolom in tabel.columns:
            if tabel[kolom].dtype == "object":
                tabel[kolom] = tabel[kolom].map(rapikan_teks)
        tabel["lembar_sumber"] = nama
        tabel["baris_excel"] = tabel.index + 2
        tabel["berkas_sumber"] = "dataset_jadwal_uts_feb_uph.xlsx"
        bersih[nama] = tabel

    jadwal = bersih["jadwal_uts"]
    for nama in ["kode_kelas", "kode_mk", "nama_mk", "dosen_id", "mode_ujian", "jenis_sesi"]:
        catat(jadwal, jadwal[nama].isna(), "kolom_kosong", nama, "Kolom ini perlu diisi.")
    for nama in ["kode_kelas", "kode_mk", "ruang", "dosen_id", "pengawas_id"]:
        jadwal[nama] = jadwal[nama].astype("string")
    for nama, minimal in [("peserta", 1), ("durasi_menit", 1), ("sks", 0), ("angkatan", 1)]:
        bilangan_bulat(jadwal, nama, minimal)
    jadwal["durasi_menit_sumber"] = jadwal["durasi_menit"].copy()
    jadwal["tanggal"] = pd.to_datetime(jadwal["hari"].map(baca_tanggal))
    jadwal["mulai_menit"] = jadwal["mulai"].map(baca_jam).astype("Int64")
    jadwal["selesai_menit"] = jadwal["selesai"].map(baca_jam).astype("Int64")
    jadwal["durasi_dari_jam"] = jadwal["selesai_menit"] - jadwal["mulai_menit"]
    jadwal["hari_baku"] = jadwal["tanggal"].map(lambda x: HARI[x.weekday()] if pd.notna(x) else pd.NA)
    catat(jadwal, jadwal["tanggal"].isna(), "tanggal_tidak_valid", "hari", "Tanggal tidak terbaca.")
    punya_nama_hari = jadwal["hari"].astype("string").str.contains(",", na=False)
    nama_hari = jadwal["hari"].astype("string").str.split(",").str[0].str.strip().str.casefold()
    catat(jadwal, punya_nama_hari & nama_hari.ne(jadwal["hari_baku"].astype("string").str.casefold()),
          "nama_hari_berbeda", "hari", "Nama hari berbeda dengan tanggal kalender.")
    jam_valid = jadwal[["mulai_menit", "selesai_menit"]].notna().all(axis=1)
    catat(jadwal, ~jam_valid, "jam_tidak_valid", "mulai/selesai", "Jam harus dalam format HH.MM atau HH:MM.")
    catat(jadwal, jam_valid & jadwal["durasi_dari_jam"].le(0), "urutan_jam_tidak_valid",
          "mulai/selesai", "Jam selesai harus lebih besar dari jam mulai.")
    catat(jadwal, jam_valid & jadwal["durasi_dari_jam"].gt(0)
          & jadwal["durasi_dari_jam"].ne(jadwal["durasi_menit_sumber"]),
          "durasi_berbeda", "durasi_menit", "Durasi tertulis berbeda dengan selisih jam.")
    mode = jadwal["mode_ujian"].astype("string").str.casefold()
    catat(jadwal, ~mode.isin(["online", "onsite"]), "mode_tidak_valid", "mode_ujian", "Mode harus Online atau Onsite.")
    catat(jadwal, mode.eq("onsite") & jadwal["ruang"].isna(),
          "ruang_kosong", "ruang", "Ujian Onsite perlu memiliki ruang.")
    catat(jadwal, mode.eq("online") & jadwal["ruang"].notna(),
          "ruang_ujian_online", "ruang", "Periksa alasan ruang terisi pada ujian Online.")
    catat(jadwal, jadwal.duplicated("kode_kelas", keep=False) & jadwal["kode_kelas"].notna(),
          "kode_kelas_berulang", "kode_kelas", "Periksa sesi atau duplikasi; baris tetap disimpan.")

    ruang = bersih["ruang"]
    ruang["ruang"] = ruang["ruang"].astype("string")
    catat(ruang, ruang["ruang"].isna(), "kolom_kosong", "ruang", "Kode ruang perlu diisi.")
    catat(ruang, ruang.duplicated("ruang", keep=False), "kode_ruang_berulang", "ruang", "Kode ruang harus unik.")
    for nama in ["lantai", "sesi_ujian", "peserta_maks_per_kelas", "peserta_maks_per_slot"]:
        bilangan_bulat(ruang, nama)
    bilangan_bulat(ruang, "kapasitas_asumsi", 1)
    ruang["status_kapasitas"] = "asumsi; belum kapasitas resmi"
    catat(jadwal, jadwal["ruang"].notna() & ~jadwal["ruang"].isin(ruang["ruang"]),
          "ruang_tidak_dikenal", "ruang", "Kode ruang tidak terdapat pada tabel ruang.")

    mk = bersih["mata_kuliah"]
    mk["kode_mk"] = mk["kode_mk"].astype("string")
    for nama in ["kode_mk", "nama_mk"]:
        catat(mk, mk[nama].isna(), "kolom_kosong", nama, "Kolom ini perlu diisi.")
    bilangan_bulat(mk, "jumlah_kelas", 1)
    catat(mk, mk.duplicated("kode_mk", keep=False), "kode_mk_berulang", "kode_mk", "Kode mata kuliah harus unik.")
    catat(jadwal, jadwal["kode_mk"].notna() & ~jadwal["kode_mk"].isin(mk["kode_mk"]),
          "kode_mk_tidak_dikenal", "kode_mk", "Kode tidak terdapat pada tabel mata kuliah.")

    pasangan = bersih["pasangan_int_nas"]
    for nama in ["kode_mk_int", "kode_mk_nas"]:
        pasangan[nama] = pasangan[nama].astype("string")
        catat(pasangan, pasangan[nama].notna() & ~pasangan[nama].isin(mk["kode_mk"]),
              "kode_pasangan_tidak_dikenal", nama, "Kode tidak terdapat pada tabel mata kuliah.")
    catat(pasangan, pasangan["kode_mk_int"].isna(), "kolom_kosong", "kode_mk_int", "Kode INT perlu diisi.")
    perlu_cek = pasangan["status"].astype("string").str.casefold().ne("otomatis").fillna(True) | pasangan["kode_mk_nas"].isna()
    catat(pasangan, perlu_cek, "pasangan_perlu_periksa", "kode_mk_int/kode_mk_nas",
          "Periksa pasangan pada dokumen; kode NAS kosong tetap dibiarkan kosong.")
    # Aturan digit pada Excel merupakan dugaan, bukan bukti kesetaraan resmi.
    pasangan["status_verifikasi"] = "belum dikonfirmasi resmi"

    for _, beda in perbedaan_ruang.iterrows():
        mask = jadwal["kode_kelas"].eq(beda["kode_kelas"])
        detail = (f"PDF Manajemen hlm. {beda['halaman_manajemen']}: {beda['ruang_manajemen']}; "
                  f"PDF Akuntansi hlm. {beda['halaman_akuntansi']}: {beda['ruang_akuntansi']}. "
                  "Nilai Excel tetap disimpan; pastikan ruang yang berlaku.")
        catat(jadwal, mask, "ruang_berbeda_antar_pdf", "ruang", detail)

    laporan = pd.DataFrame(masalah, columns=["lembar", "baris_excel", "kode", "jenis", "kolom", "detail"])
    for nama, tabel in bersih.items():
        perlu_periksa = set(laporan.loc[laporan["lembar"].eq(nama), "baris_excel"])
        tabel["perlu_periksa"] = tabel["baris_excel"].isin(perlu_periksa)
    jadwal["kategori_kegiatan"] = "Ujian"  # Jenis sesi LAB tidak mengubah ujian menjadi praktikum.
    return bersih, laporan

def nilai_biasa(value):
    """Ubah nilai pandas menjadi nilai Python; data kosong tetap None."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value

def jam_tampil(value):
    if pd.isna(value):
        return None
    value = int(value)
    return f"{value // 60:02d}:{value % 60:02d}"

def tipe_kelas_singkat(value):
    if pd.isna(value):
        return None
    pemetaan = {"internasional": "INT", "nasional": "NAS", "int": "INT", "nas": "NAS"}
    return pemetaan.get(str(value).strip().casefold(), str(value))

def siapkan_bahan_pencarian_feb(data, laporan):
    jadwal = data["jadwal_uts"]
    katalog = data["mata_kuliah"]
    kelas, mata_kuliah, nama, kode = [], [], [], []
    tabel_tampil = []

    for _, row in jadwal.iterrows():
        catatan = laporan.loc[
            laporan["lembar"].eq("jadwal_uts") & laporan["baris_excel"].eq(row["baris_excel"])]
        daftar_catatan = (catatan["jenis"] + ": " + catatan["detail"]).tolist()
        tanggal = row["tanggal"].strftime("%Y-%m-%d") if pd.notna(row["tanggal"]) else None
        detail = {
            "class_code": nilai_biasa(row["kode_kelas"]),
            "course_code": nilai_biasa(row["kode_mk"]),
            "name": nilai_biasa(row["nama_mk"]),
            "language": tipe_kelas_singkat(row["tipe_kelas"]),
            "language_source": nilai_biasa(row["tipe_kelas"]),
            "program": nilai_biasa(row["prodi_mk"]),
            "participants": nilai_biasa(row["peserta"]),
            "lecturer_id": nilai_biasa(row["dosen_id"]),
            "room_id": nilai_biasa(row["ruang"]),
            "day": tanggal,
            "start": nilai_biasa(row["mulai_menit"]),
            "end": nilai_biasa(row["selesai_menit"]),
            "exam_mode": nilai_biasa(row["mode_ujian"]),
            "session_type": nilai_biasa(row["jenis_sesi"]),
            "duration_source": nilai_biasa(row["durasi_menit_sumber"]),
            "duration_from_time": nilai_biasa(row["durasi_dari_jam"]),
            "needs_review": bool(row["perlu_periksa"]),
            "review_notes": daftar_catatan,
            "source": {"sheet": row["lembar_sumber"], "excel_row": int(row["baris_excel"]),
                       "source_programs": nilai_biasa(row["prodi_dokumen"])},
        }
        kelas.append((detail["class_code"], detail))
        tabel_tampil.append({
            "Kode MK": detail["course_code"], "Mata kuliah": detail["name"],
            "Kode kelas": detail["class_code"], "Prodi": detail["program"],
            "INT/NAS": detail["language"], "Tanggal": tanggal,
            "Jenis sesi": detail["session_type"],
            "Mulai": jam_tampil(row["mulai_menit"]), "Selesai": jam_tampil(row["selesai_menit"]),
            "Peserta": detail["participants"], "Mode": detail["exam_mode"], "Ruang": detail["room_id"],
            "Perlu diperiksa": "Ya" if detail["needs_review"] else "Tidak",
            "Catatan": " | ".join(daftar_catatan), "Baris Excel": detail["source"]["excel_row"],
        })

    # Gabungkan hanya nama dan kelas pada kode MK yang persis sama.
    kode_semua = pd.concat([katalog["kode_mk"], jadwal["kode_mk"]]).dropna().drop_duplicates()
    for course_code in sorted(kode_semua.tolist()):
        dari_katalog = katalog.loc[katalog["kode_mk"].eq(course_code)]
        dari_jadwal = jadwal.loc[jadwal["kode_mk"].eq(course_code)]
        variasi_nama = pd.concat([dari_katalog["nama_mk"], dari_jadwal["nama_mk"]]).dropna().drop_duplicates().tolist()
        baris_dasar = dari_katalog.iloc[0] if not dari_katalog.empty else dari_jadwal.iloc[0]
        detail = {
            "course_code": str(course_code), "name": nilai_biasa(baris_dasar["nama_mk"]),
            "language": tipe_kelas_singkat(baris_dasar["tipe_kelas"]),
            "language_source": nilai_biasa(baris_dasar["tipe_kelas"]),
            "program": nilai_biasa(baris_dasar["prodi_mk"]),
            "class_codes": dari_jadwal["kode_kelas"].dropna().tolist(),
            "name_variants": variasi_nama,
        }
        mata_kuliah.append((str(course_code), detail))
        for variasi in variasi_nama:
            nama.append(SearchEntry(str(course_code), variasi, "course"))
        kode.append(SearchEntry(str(course_code), str(course_code), "course"))

    bahan = {"kelas": kelas, "mata_kuliah": mata_kuliah, "nama": nama, "kode": kode}
    return bahan, pd.DataFrame(tabel_tampil)
