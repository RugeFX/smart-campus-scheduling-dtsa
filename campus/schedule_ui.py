"""User goals first; algorithm traces and fixtures are disclosed on demand."""
from io import StringIO
from contextlib import redirect_stdout
import pandas as pd
import streamlit as st
from .dp import optimize_schedule, optimize_schedule_memo, explain_dp_table, brute_force_reference
from .greedy import select_activities, brute_force_activity_count, greedy_weight_counterexample
from .dp_ui import compare_schedule_methods, MEMO_UI_LIMIT
from .feb_views import scheduling_inputs
from .workspace import week_of
from .models import VALUE
from .capabilities import SNAPSHOT_HASH


def render_schedule(data, request_frame, timeline, get_workspace):
    st.title("Pilih jadwal")
    st.write("Pilih kombinasi kelas yang tidak bentrok pada satu ruangan dan tanggal dari Excel.")
    st.caption("DP · Rifqi & Abdur | Greedy · tambahan UAS")
    st.info("Hasil adalah alternatif simulasi. Jadwal Excel dan ujian yang tidak terpilih tidak diubah atau dibatalkan.")
    include_review=st.checkbox("Sertakan baris yang masih perlu diperiksa",value=False,key="dp_include_review")
    candidates,excluded=scheduling_inputs(data,include_review)
    with st.expander(f"Baris yang belum menjadi kandidat ({len(excluded)})"):
        st.dataframe(excluded,hide_index=True,width="stretch")
    if not candidates:
        st.info("Tidak ada kandidat onsite yang valid.");return
    groups=sorted({(r.room_id,r.day) for r in candidates})
    group=st.selectbox("Ruang dan hari yang dievaluasi",groups,format_func=lambda g:f"{g[0]} · {g[1]}",key="dp_group")
    batch=[r for r in candidates if (r.room_id,r.day)==group]
    goal=st.radio("Yang ingin diprioritaskan",["Total nilai kegiatan","Jumlah kelas"],horizontal=True,key="schedule_goal")
    greedy_mode=goal=="Jumlah kelas"
    trace=[]
    with st.expander("Pilihan cara perhitungan"):
        if not greedy_mode:
            methods=("Tabulation (bottom-up)","Memoization (top-down)") if len(batch)<=MEMO_UI_LIMIT else ("Tabulation (bottom-up)",)
            if st.session_state.get("dp_method") not in methods:st.session_state.pop("dp_method",None)
            method=st.radio("Metode DP",methods,horizontal=True,key="dp_method")
            if len(batch)>MEMO_UI_LIMIT:st.caption("Memoization rekursif dibatasi 400 kandidat; tabulasi tetap tersedia.")
        else:
            method="Greedy · selesai paling awal"
            st.write("Kelas yang selesai paling awal dipilih, lalu proses berlanjut pada kelas yang mulai setelahnya.")
    if greedy_mode:
        _,selected=select_activities(batch,trace=trace)
        total=sum(r.value for r in batch if r.request_id in selected)
        calls_note="Greedy mengoptimalkan jumlah, bukan total bobot."
    elif method.startswith("Memoization"):
        try:
            total,selected,calls=optimize_schedule_memo(batch)
            calls_note=f"{calls} pemanggilan OPT."
        except RecursionError:
            total,selected=optimize_schedule(batch)
            calls_note="Hasil tabulasi dipakai karena batas rekursi."
            st.warning("Batas rekursi tercapai. Hasil tabulasi tetap tersedia.")
    else:
        total,selected=optimize_schedule(batch)
        calls_note=f"{len(batch)} sel DP diisi."
    other_count,_=select_activities(batch)
    a,b,c=st.columns(3)
    a.metric("Nilai kombinasi Greedy" if greedy_mode else "Nilai kombinasi DP",total)
    b.metric("Kelas dalam kombinasi",f"{len(selected)} / {len(batch)}")
    c.metric("Jumlah pilihan selesai tercepat",other_count)
    st.caption(f"{method} · {calls_note}")
    st.caption(f"Seluruh kandidat FEB berbobot {VALUE['Examination']}. Dengan bobot sama, kedua tujuan memberi jumlah maksimum yang sama. Bobot adalah konfigurasi algoritma, bukan kolom Excel.")
    label="Greedy" if greedy_mode else "DP"
    timeline(batch,selected,label)
    st.dataframe(request_frame(batch).assign(Hasil=[f"Masuk kombinasi {label}" if r.request_id in selected else f"Di luar kombinasi {label}" for r in batch]),hide_index=True,width="stretch")
    with st.expander("Lihat langkah pemilihan" if greedy_mode else "Lihat perhitungan ambil atau lewati"):
        if greedy_mode:
            st.dataframe(pd.DataFrame(trace),hide_index=True,width="stretch")
            st.write("**Mengapa jumlahnya optimal?** Jika solusi optimum dimulai dengan kelas lain yang selesai lebih lambat, kelas pertamanya dapat diganti dengan kelas yang selesai paling awal. Sisa kelas tetap kompatibel dan jumlahnya tidak berkurang. Ulangi argumen pada sisa waktu.")
        else:
            output=StringIO()
            with redirect_stdout(output):explain_dp_table(batch)
            st.code(output.getvalue(),language=None)
        if len(batch)<=15:
            if st.button("Periksa dengan semua kombinasi"):
                value,_=(brute_force_activity_count(batch) if greedy_mode else brute_force_reference(batch))
                actual=len(selected) if greedy_mode else total
                if value==actual:st.success(f"Hasil sesuai pembanding: {value}.")
                else:st.error(f"Hasil berbeda: {actual}, pembanding {value}.")
        else:st.caption("Pembanding semua kombinasi dibatasi 15 kandidat.")
    with st.expander("Perbandingan biaya: rekursi naif vs memoization vs tabulation"):
        signature=(data["sha256"],SNAPSHOT_HASH,group,include_review)
        if st.session_state.get("dp_compare_signature")!=signature:
            st.session_state.pop("dp_compare_rows",None)
            st.session_state.dp_compare_signature=signature
        st.caption("Pengukuran hanya berjalan setelah tombol ditekan. Naif maksimal 15 kandidat, memoization rekursif 400. Ini satu pengukuran interaktif; benchmark laporan memakai median lima pengulangan.")
        if st.button("Jalankan perbandingan DP",key="dp_compare"):
            st.session_state.dp_compare_rows=compare_schedule_methods(batch)
        if st.session_state.get("dp_compare_rows"):
            st.dataframe(st.session_state.dp_compare_rows,hide_index=True,width="stretch")
    with st.expander("Batas Greedy pada kegiatan berbobot · contoh uji"):
        st.caption("Fixture pengujian terkontrol, terpisah dari kandidat Excel. Contoh ini tidak dapat dialokasikan.")
        example=greedy_weight_counterexample()
        st.dataframe(request_frame(example["candidates"]),hide_index=True,width="stretch")
        st.write("Greedy memilih A+B: 2 kegiatan, nilai 4. DP memilih C: 1 kegiatan, nilai 10. Jumlah terbesar dan total nilai terbesar adalah tujuan yang berbeda.")
    chosen=[r for r in batch if r.request_id in selected]
    st.download_button("Unduh hasil analisis CSV",request_frame(chosen).to_csv(index=False).encode("utf-8-sig"),"analisis_jadwal_excel.csv","text/csv")
    st.caption("Analisis ini belum memeriksa kapasitas, fasilitas atau konflik dosen/mahasiswa. Pemeriksaan kapasitas dan booking berjalan pada alokasi berikutnya.")
    st.subheader("Alokasi ruangan")
    alternatives=st.checkbox("Coba ruang lain jika belum teralokasi",value=False,key="dp_alternatives")
    workspace=get_workspace(data,week_of(group[1]))
    codes=[r.request_id for r in chosen if r.request_id not in workspace.reserved_class_ids]
    if st.button("Alokasikan kandidat ruang/hari ini",type="primary",disabled=not codes):
        try:
            report=workspace.allocate(codes,include_review=include_review,alternatives=alternatives)
            st.success(f"{len(report['bookings'])} alokasi ditambahkan; {len(report['rejected'])} ditolak.")
        except (ValueError,AssertionError) as error:st.error(str(error))
    st.button("Buka hasil simulasi alokasi",on_click=lambda:st.session_state.update(page="Simulasi alokasi"),key="dp_open_allocation")
