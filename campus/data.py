"""File/UI adapter around the unchanged Colab data pipeline."""
from pathlib import Path
import hashlib
import pandas as pd
from .data_core import (
    KOLOM_WAJIB, PERBEDAAN_RUANG_PDF, rapikan_dan_validasi,
    siapkan_bahan_pencarian_feb,
)
from .search_bridge import hubungkan_pencarian_feb


def load_workbook(source, source_name="dataset_jadwal_uts_feb_uph.xlsx"):
    with pd.ExcelFile(source, engine="openpyxl") as book:
        missing = set(KOLOM_WAJIB) - set(book.sheet_names)
        if missing:
            raise ValueError("Lembar Excel belum lengkap: " + ", ".join(sorted(missing)))
        raw = {}
        for name, required in KOLOM_WAJIB.items():
            frame = pd.read_excel(book, sheet_name=name, dtype=object)
            absent = set(required) - set(frame.columns)
            if absent:
                raise ValueError(f"Kolom pada {name} belum lengkap: {', '.join(sorted(absent))}")
            raw[name] = frame
    content = source.getvalue() if hasattr(source, "getvalue") else Path(source).read_bytes()
    bundled = Path(__file__).resolve().parents[1] / "data/dataset_jadwal_uts_feb_uph.xlsx"
    verified = hashlib.sha256(content).digest() == hashlib.sha256(bundled.read_bytes()).digest()
    clean, issues = rapikan_dan_validasi(raw, PERBEDAAN_RUANG_PDF if verified else PERBEDAAN_RUANG_PDF.iloc[:0])
    for frame in clean.values():
        frame["berkas_sumber"] = source_name
    ingredients, display = siapkan_bahan_pencarian_feb(clean, issues)
    return {"raw": raw, "clean": clean, "issues": issues, "ingredients": ingredients,
            "display": display, "pdf_findings_applied": verified,
            "source_name": source_name, "sha256": hashlib.sha256(content).hexdigest()}


def build_search_indexes(ingredients, strategy="chaining"):
    # The user explicitly selected Excel for all app data. Reuse the implemented
    # Colab bridge; keep the saved notebook flag and algorithm definitions intact.
    indexes = hubungkan_pencarian_feb(ingredients)
    result = {"classes": indexes["kelas"], "courses": indexes["mata_kuliah"],
              "names": indexes["nama"], "codes": indexes["kode"]}
    if strategy not in ("chaining", "linear"):
        raise ValueError("Strategi indeks tidak dikenal.")
    if strategy == "linear":
        from .hash_table import HashTableLinearProbing
        for kind in ("classes", "courses"):
            table = HashTableLinearProbing()
            for key, value in result[kind].items(): table.put(key, value)
            result[kind] = table
    return result
