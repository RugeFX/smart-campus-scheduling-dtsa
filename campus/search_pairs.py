"""Read explicit INT–NAS links from Excel for search-result expansion only."""
import pandas as pd
from .hash_table import HashTableChaining


def pair_indexes(data, catalog):
    rows, rejected = [], []
    neighbors = HashTableChaining()
    for _, row in data["clean"]["pasangan_int_nas"].iterrows():
        a,b=row["kode_mk_int"],row["kode_mk_nas"]
        item={"Kode INT":a,"Kode NAS":b,"Metode Excel":row["metode"],
              "Status Excel":row["status"],"Verifikasi":row["status_verifikasi"],
              "Baris Excel":int(row["baris_excel"])}
        if pd.isna(a) or pd.isna(b) or not str(a).strip() or not str(b).strip():
            rejected.append({**item,"Alasan":"Pasangan kode belum lengkap"}); continue
        if a==b or not catalog.contains(a) or not catalog.contains(b):
            rejected.append({**item,"Alasan":"Kode pasangan tidak valid/tidak ada di katalog"}); continue
        rows.append(item)
        for key,other in [(a,b),(b,a)]:
            values=neighbors.get(key) or []
            if other not in values: values.append(other)
            neighbors.put(key,values)
    lookup,accepted=HashTableChaining(),[]
    for item in rows:
        a,b=item["Kode INT"],item["Kode NAS"]
        if len(neighbors.get(a))!=1 or len(neighbors.get(b))!=1:
            rejected.append({**item,"Alasan":"Satu kode memiliki lebih dari satu pasangan; perlu pemeriksaan"})
            continue
        lookup.put(a,b);lookup.put(b,a)
        accepted.append(item)
    columns=["Kode INT","Kode NAS","Metode Excel","Status Excel","Verifikasi","Baris Excel"]
    return lookup,pd.DataFrame(accepted,columns=columns),pd.DataFrame(rejected,columns=columns+["Alasan"])


def expand_course_ids(direct_ids, pairs, catalog):
    """Preserve exact-search semantics, expanding by one explicit link only."""
    result=[]
    seen=HashTableChaining()
    for code in direct_ids:
        other=pairs.get(code)
        for item in [code]+([other] if other and catalog.contains(other) else []):
            if not seen.contains(item):
                seen.put(item,True);result.append(item)
    return result
