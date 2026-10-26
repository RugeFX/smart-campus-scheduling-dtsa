"""Full application views. All scheduling inputs come from the active Excel."""
import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from .capabilities import SNAPSHOT_HASH, SOURCE_LABEL, STATUS
from .data import build_search_indexes
from .feb_views import available_weeks
from .search_pairs import pair_indexes
from .excel_benchmark import measure_excel

ROOT = Path(__file__).resolve().parents[1]


def allocation_table(workspace, bookings):
    rows = []
    for request in bookings:
        sources = workspace.source_rows(request)
        rows.append({"ID alokasi": request.request_id, "Kelas asal": ", ".join(sources["Kode kelas"]),
            "Mata kuliah": request.title, "Tanggal": request.day, "Ruang alokasi": request.room_id,
            "Ruang Excel": ", ".join(sources["Ruang"].dropna().astype(str).unique()),
            "Mulai": f"{request.start//60:02d}:{request.start%60:02d}",
            "Selesai": f"{request.end//60:02d}:{request.end%60:02d}", "Peserta": request.participants,
            "Baris Excel": ", ".join(sources["Baris Excel"].astype(str))})
    return pd.DataFrame(rows, columns=["ID alokasi", "Kelas asal", "Mata kuliah", "Tanggal", "Ruang alokasi",
        "Ruang Excel", "Mulai", "Selesai", "Peserta", "Baris Excel"])


def allocation_page(data, get_workspace, request_frame, timeline, room_frame):
    st.title("Simulasi alokasi ruang")
    st.write("Pilih kelas Excel, jalankan alokasi, lalu periksa ruang, penolakan, dan perubahan pemakaiannya.")
    st.caption("Integrasi Heap, Hash, AVL, dan DP · Zacky / Deni")
    st.caption("Simulasi dimulai dari ruang kosong dan disimpan selama sesi aplikasi. Jadwal Excel tetap menjadi acuan asli. Kapasitas masih asumsi; fasilitas dan konflik dosen/mahasiswa belum diperiksa.")
    weeks = available_weeks(data)
    if not weeks:
        st.warning("Tanggal Excel belum valid. Periksa Data & panduan."); return
    settings_left,settings_right=st.columns([2,1])
    with settings_left:
        week = st.selectbox("Minggu simulasi", weeks, format_func=lambda w: f"{w[0]} · minggu {w[1]}", key="allocation_week")
    workspace = get_workspace(data, week)
    with settings_right:
        include_review = st.checkbox("Sertakan baris dengan catatan pemeriksaan", value=False, key="allocation_review")
    candidates, excluded = workspace.candidates(include_review)
    available = [r for r in candidates if r.request_id not in workspace.reserved_class_ids]
    scope = st.radio("Permintaan yang akan dialokasikan", ["Seluruh kandidat Excel", "Pilih kelas Excel", "Dari antrean yang sudah diproses"], horizontal=True, key="allocation_scope")
    if scope == "Pilih kelas Excel":
        names = {r.request_id: r.title for r in available}
        codes = st.multiselect("Kelas yang akan dicoba", list(names), format_func=lambda code: f"{code} · {names[code]}", key="allocation_selected")
    elif scope == "Dari antrean yang sudah diproses":
        signature = st.session_state.get("queue_signature")
        valid_queue = bool(signature and signature[:2] == (data["sha256"], SNAPSHOT_HASH))
        processed = st.session_state.get("queue_processed", []) if valid_queue else []
        queued_ids = {r.request_id for r in processed}
        codes = [r.request_id for r in available if r.request_id in queued_ids]
        if not codes: st.info("Proses kelas melalui Antrean kegiatan terlebih dahulu. Hanya kandidat onsite valid pada minggu ini yang dapat dialokasikan.")
    else:
        codes = [r.request_id for r in available]
    alternatives = st.checkbox("Coba ruang lain jika ruang awal tidak dapat dipakai", value=True, key="allocation_alternatives")
    confirmed_pairs = []
    with st.expander("Penggabungan kelas INT–NAS (opsional)"):
        st.caption("Pencarian pasangan dan penggabungan kelas adalah dua tindakan berbeda. Pilih pasangan Excel yang ingin dikonfirmasi untuk simulasi ini. Hari, jam, ruang, dosen, kategori, serta kapasitas tetap diperiksa oleh Colab.")
        indexes = build_search_indexes(data["ingredients"])
        _, pairs, rejected_pairs = pair_indexes(data, indexes["courses"])
        options = list(dict.fromkeys((r["Kode INT"], r["Kode NAS"]) for _, r in pairs.iterrows()))
        confirmed_pairs = st.multiselect("Pasangan yang dikonfirmasi untuk simulasi", options,
            format_func=lambda pair: " ↔ ".join(pair), key="allocation_pairs")
        if not pairs.empty: st.dataframe(pairs, hide_index=True, width="stretch")
        st.caption("Konfirmasi ini hanya berlaku pada simulasi lokal, tidak mengubah status resmi pada Excel.")
    try:
        prepared, origins = workspace.prepare(codes, confirmed_pairs, include_review)
    except ValueError as error:
        st.error(f"Masukan belum dapat dipakai: {error}")
        prepared, origins = [], {}
    st.write(f"**Untuk percobaan berikutnya: {len(codes)} kelas · {len(prepared)} permintaan setelah penggabungan · {len(workspace.bookings)} alokasi tersimpan**")
    if confirmed_pairs and prepared:
        st.dataframe(pd.DataFrame([{"Kelas asal": ", ".join(origins[r.request_id]), "Peserta": r.participants,
            "Ruang awal": r.room_id} for r in prepared]), hide_index=True, width="stretch")
    if st.button("Jalankan alokasi", type="primary", disabled=not prepared, key="allocation_run"):
        try:
            with st.spinner("Memeriksa kandidat dan menyusun alokasi…"):
                report = workspace.allocate(codes, confirmed_pairs=confirmed_pairs,
                    include_review=include_review, alternatives=alternatives)
            st.rerun()
        except (ValueError, KeyError, AssertionError) as error: st.error(f"Alokasi belum berhasil: {error}")
    if workspace.reports:
        last=workspace.reports[-1]
        st.success(f"Percobaan terakhir: {len(last['bookings'])} permintaan diterima, {len(last['rejected'])} ditolak.")
    a,b,c = st.columns(3)
    a.metric("Alokasi tersimpan", len(workspace.bookings))
    b.metric("Kelas Excel terwakili", len(workspace.reserved_class_ids))
    c.metric("Nilai total", sum(r.value for r in workspace.bookings))
    results, attempts_tab, rooms_tab = st.tabs(["Hasil & pembatalan", "Penolakan & percobaan", "Pemakaian ruang"])
    with results:
        if workspace.bookings:
            booked = allocation_table(workspace, workspace.bookings)
            st.dataframe(booked, hide_index=True, width="stretch")
            st.download_button("Unduh alokasi CSV", booked.to_csv(index=False).encode("utf-8-sig"), "alokasi_simulasi.csv", "text/csv")
            pairs = sorted({(r.room_id,r.day) for r in workspace.bookings})
            group = st.selectbox("Timeline hasil alokasi", pairs, format_func=lambda pair: " · ".join(pair), key="allocation_timeline")
            timeline([r for r in workspace.bookings if (r.room_id,r.day)==group])
            selected = st.selectbox("Alokasi yang akan dibatalkan", [r.request_id for r in workspace.bookings],
                format_func=lambda code: ", ".join(workspace.provenance[code]), key="allocation_cancel_id")
            if st.button("Batalkan alokasi terpilih"):
                workspace.cancel(selected)
                st.rerun()
            if st.button("Mulai ulang simulasi minggu ini"):
                st.session_state.allocation_workspaces.pop(week, None)
                st.rerun()
        else:
            st.info("Belum ada alokasi. Pilih permintaan di atas, lalu jalankan alokasi. Hasil dan riwayat akan muncul di sini.")
        if workspace.events:
            with st.expander("Riwayat sesi"):
                st.dataframe(pd.DataFrame(workspace.events), hide_index=True, width="stretch")
    with attempts_tab:
        if workspace.reports:
            report = workspace.reports[-1]
            st.write("**Percobaan terakhir**")
            rejected = pd.DataFrame([{"Kelas asal": ", ".join(report["provenance"][v["request"].request_id]),
                "Alasan": v["reason"]} for v in report["rejected"]], columns=["Kelas asal","Alasan"])
            st.dataframe(rejected, hide_index=True, width="stretch")
            attempts = pd.DataFrame(report["attempts"])
            if not attempts.empty:
                attempts["Kelas asal"] = attempts["request_id"].map(lambda key: ", ".join(report["provenance"][key]))
            st.dataframe(attempts, hide_index=True, width="stretch")
            st.download_button("Unduh percobaan CSV", attempts.to_csv(index=False).encode("utf-8-sig"), "percobaan_ruang.csv", "text/csv")
        else: st.caption("Belum ada percobaan alokasi pada minggu ini.")
        with st.expander(f"Baris yang dikecualikan ({len(excluded)})"):
            st.dataframe(excluded, hide_index=True, width="stretch")
    with rooms_tab:
        workspace.validate()
        st.success("Hash ruang dan kedua indeks AVL konsisten.")
        st.dataframe(room_frame(workspace.registry[1].inorder()), hide_index=True, width="stretch")
        st.caption("Slot reguler unik / 15 per minggu mengikuti model Colab saat ini. Pembatalan menghitung ulang slot dari alokasi yang masih tersimpan.")
    with st.expander("Cara alokasi bekerja"):
        st.write("PQ mengurutkan permintaan per tanggal. Kapasitas dan booking yang telah diterima diperiksa, lalu DP memilih satu batch ruang/hari. Permintaan yang tidak terpilih dapat mencoba ruang lain sekali per ruang. Keputusan memperbarui Hash dan kedua AVL. Strategi beberapa ruang tidak menjamin optimum global.")


def experiments_page(data):
    st.title("Eksperimen algoritma")
    st.write("Ukur operasi pada Excel aktif atau baca hasil pengukuran yang tersimpan bersama Colab.")
    st.caption("Eksperimen performa · Wildan dan tim")
    live, saved = st.tabs(["Ukur data Excel aktif", "Arsip benchmark Colab"])
    with live:
        st.caption(f"Sumber input: {data['source_name']}. Tidak ada kegiatan buatan yang ditambahkan ke data aplikasi.")
        st.dataframe(pd.DataFrame([{"Tabel":name,"Baris Excel":len(frame)} for name,frame in data["raw"].items()]), hide_index=True, width="stretch")
        algorithm = st.selectbox("Algoritma", ["Hash Table","Heap/PQ","Trie","AVL","DP"], key="benchmark_algorithm")
        upper = max(1,len(data["display"]))
        limit = st.slider("Batas jumlah baris masukan", 1, upper, min(100,upper), key="benchmark_limit") if upper>1 else 1
        repeat = st.selectbox("Pengulangan pengukuran", [5,3,1], key="benchmark_repeat")
        query = st.text_input("Awalan nama untuk Trie", value="akun", key="benchmark_prefix") if algorithm=="Trie" else "akun"
        st.caption("Jumlah aktual mengikuti data tiap algoritma. Heap memakai satu tanggal; DP memakai satu ruang/hari, maksimal 15 kandidat untuk pembanding semua kombinasi. Setup tidak masuk timer. Memori adalah tambahan selama operasi, bukan seluruh RAM.")
        if st.button("Jalankan percobaan", type="primary"):
            try:
                with st.spinner("Mengukur operasi pada data Excel…"):
                    measured = measure_excel(data,algorithm,limit,int(repeat),query)
                st.session_state.excel_benchmark_result = measured
            except (ValueError,AssertionError) as error: st.error(str(error))
        if st.session_state.get("excel_benchmark_result"):
            frame = pd.DataFrame(st.session_state.excel_benchmark_result)
            st.caption(f"Hasil terakhir: {frame.iloc[0]['Algoritma']} · {frame.iloc[0]['Berkas']} · {frame.iloc[0]['Pengulangan']} pengulangan.")
            st.dataframe(frame, hide_index=True, width="stretch")
            st.altair_chart(alt.Chart(frame).mark_bar().encode(x=alt.X("Median (ms):Q"), y=alt.Y("Implementasi:N",sort=None), tooltip=list(frame.columns[:7])), width="stretch")
            st.download_button("Unduh pengukuran Excel CSV",frame.to_csv(index=False).encode("utf-8-sig"),"benchmark_excel.csv","text/csv")
    with saved:
        provenance = json.loads((ROOT/"references/benchmark-provenance.json").read_text())
        if provenance["notebook_sha256"] != SNAPSHOT_HASH:
            st.warning("Arsip benchmark berasal dari snapshot berbeda. Sinkronkan arsip sebelum memakainya."); return
        frame = pd.read_csv(ROOT/"data/colab_benchmarks.csv")
        environment = json.loads((ROOT/"data/colab_benchmark_environment.json").read_text())
        st.info(f"Arsip {len(frame)} hasil dari Colab: input sintetis untuk uji performa, diukur pada Python lokal. Arsip ini tidak menjadi sumber jadwal atau alokasi Excel.")
        metadata=json.loads((ROOT/"data/colab_benchmark_environment.json").read_text())
        if metadata.get("environment_status")=="unavailable_for_imported_run":
            st.info("Lingkungan mesin untuk arsip 79 hasil belum tersedia. Metadata pengukuran lama tidak digunakan untuk mengidentifikasi run ini.")
        selected = st.selectbox("Bagian eksperimen Colab", list(frame["module"].unique()), key="saved_benchmark_module")
        filtered = frame[frame["module"].eq(selected)]
        operation = st.selectbox("Operasi Colab", list(filtered["operation"].unique()), key="saved_benchmark_operation")
        filtered = filtered[filtered["operation"].eq(operation)]
        st.dataframe(filtered, hide_index=True, width="stretch")
        chart = alt.Chart(filtered).mark_line(point=True).encode(
            x=alt.X("n:Q",scale=alt.Scale(type="log"),title="Jumlah data"),
            y=alt.Y("median_seconds:Q",title="Median detik"),color="implementation:N",
            tooltip=["n","k","implementation","median_seconds","peak_bytes"])
        st.altair_chart(chart, width="stretch")
        st.download_button("Unduh arsip benchmark CSV",(ROOT/"data/colab_benchmarks.csv").read_bytes(),"benchmark_colab.csv","text/csv")
        with st.expander("Lingkungan dan metode pengukuran"):
            st.json(environment)
            st.caption("Input, operasi, ukuran, k, seed, dan pengulangan harus sama untuk perbandingan setara. DP skala besar dipisahkan dari pembanding kecil.")


def test_panel():
    total=len(STATUS["test_runners"])
    st.subheader("Pengujian algoritma Colab")
    st.caption(f"{total} skenario memakai fixture uji terkontrol. Fixture ini terpisah dari data jadwal aplikasi. Tombol menguji implementasi lokal yang disalin persis dari snapshot Colab.")
    if st.button(f"Jalankan {total} pengujian Colab"):
        from .verification import run_test_plan
        with st.spinner("Menjalankan pengujian…"):
            st.session_state.colab_test_report = run_test_plan()
    report = st.session_state.get("colab_test_report")
    if report:
        passed = sum(status=="LULUS" for _,status,_ in report)
        if passed==total: st.success(f"{total} dari {total} pengujian lulus.")
        else: st.error(f"{passed} dari {total} pengujian lulus. Periksa detail di bawah.")
    else:
        report = [(key,"TERDAFTAR","Belum dijalankan pada sesi ini.") for key in STATUS["test_runners"]]
    st.dataframe(pd.DataFrame(report,columns=["ID","Status","Detail"]),hide_index=True,width="stretch")
    if st.session_state.get("colab_test_report"):
        frame=pd.DataFrame(report,columns=["ID","Status","Detail"])
        st.download_button("Unduh hasil pengujian CSV",frame.to_csv(index=False).encode("utf-8-sig"),"pengujian_colab.csv","text/csv")
