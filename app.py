"""Excel FEB is the sole application data source; Colab supplies algorithms."""
from io import BytesIO, StringIO
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
import json
import altair as alt
import pandas as pd
import streamlit as st
from campus.data import load_workbook, build_search_indexes
from campus.feb_views import available_weeks, room_inputs, room_search_table, scheduling_inputs
from campus.hash_table import HashTableChaining
from campus.trie import bilingual_autocomplete
from campus.search_pairs import pair_indexes, expand_course_ids
from campus.adapters import RoomView
from campus.dp import optimize_schedule, optimize_schedule_memo, naive_recursive, earliest_finish_reference, explain_dp_table, brute_force_reference
from campus.dp_ui import compare_schedule_methods, MEMO_UI_LIMIT
from campus.models import VALUE
from campus.capabilities import SOURCE_LABEL, SNAPSHOT_HASH, status_rows, STATUS
from campus.workspace import AllocationWorkspace, week_of
from campus.queue_ui import render_queue
from campus.schedule_ui import render_schedule
from campus.learning_ui import trie_delete_preview, room_algorithm_details
from campus.full_pages import allocation_page, experiments_page, test_panel

ROOT=Path(__file__).resolve().parent
PAGES=["Ringkasan","Cari jadwal","Antrean kegiatan","Simulasi alokasi","Ruangan","Pilih jadwal","Eksperimen","Data & panduan"]
st.set_page_config(page_title="Smart Campus · Kelompok 2",page_icon="◫",layout="wide")
st.markdown('''<style>
:root { --brand:oklch(0.48 0.10 91); --ink:oklch(0.27 0.02 240); --muted:oklch(0.47 0.02 240); --surface:oklch(0.96 0 0); --accent:oklch(0.31 0.05 235); }
.stApp { background:oklch(1 0 0); color:var(--ink); }
.block-container { padding-top:2.5rem; padding-bottom:3rem; max-width:1280px; }
h1 { font-size:2.25rem!important; font-weight:650!important; letter-spacing:-0.035em; }
h2 { font-size:1.4rem!important; font-weight:600!important; }
h3 { font-size:1.1rem!important; font-weight:600!important; }
h1,h2,h3 { text-wrap:balance; }
p { text-wrap:pretty; }
section[data-testid="stSidebar"] { background:var(--surface); }
section[data-testid="stSidebar"] .block-container { padding-top:2rem; }
.st-key-sidebar_navigation, .st-key-sidebar_navigation [data-testid="stVerticalBlock"] { gap:.25rem; }
.st-key-sidebar_navigation button { justify-content:flex-start; min-height:44px; padding:.65rem .85rem; border:0; border-radius:8px; box-shadow:none; }
.st-key-sidebar_navigation button > div { justify-content:flex-start; }
.st-key-sidebar_navigation button[kind="secondary"] { background:transparent; color:var(--ink); }
.st-key-sidebar_navigation button[kind="secondary"]:hover { background:#E5E7E9; }
.st-key-sidebar_navigation button[kind="primary"] { background:#E8E3CD; color:#564500; font-weight:650; }
.st-key-sidebar_navigation button[kind="primary"]:hover { background:#DDD7BC; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color:#4B5860!important; opacity:1; }
input::placeholder { color:#53616A!important; opacity:1; }
.campus-wordmark { font-size:1.5rem; font-weight:750; letter-spacing:-.03em; margin-bottom:.2rem; }
.campus-mark { color:var(--brand); font-size:1.8rem; margin-right:.35rem; }
.intro { color:var(--muted); max-width:70ch; margin-bottom:1.5rem; font-size:1.05rem; }
.rule { border-top:1px solid oklch(.87 0 0); margin:1.5rem 0; }
button:focus-visible, input:focus-visible { outline:3px solid var(--brand)!important; outline-offset:3px; }
@media(max-width:640px) { .block-container{padding:1.5rem 1rem;} h1{font-size:1.9rem!important;} }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none!important; transition:none!important; scroll-behavior:auto!important; } }
</style>''', unsafe_allow_html=True)


def heading(title,description):
    st.title(title)
    st.write(description)


def minute_text(value):
    return f"{value//60:02d}:{value%60:02d}"


def request_frame(items):
    return pd.DataFrame([{"Kode kelas":r.request_id,"Mata kuliah":r.title,"Kategori":"Ujian",
        "Peserta":r.participants,"Ruang":r.room_id,"Tanggal":r.day,"Mulai":minute_text(r.start),
        "Selesai":minute_text(r.end),"Nilai":r.value} for r in items],columns=["Kode kelas","Mata kuliah",
        "Kategori","Peserta","Ruang","Tanggal","Mulai","Selesai","Nilai"])


def room_frame(items):
    return pd.DataFrame([{"Ruang":r.room_id,"Kapasitas asumsi":r.capacity,"Slot terpakai":r.used_slots,
        "Pemakaian (%)":round(r.utilization*100,1)} for r in items])


def timeline(items,selected=None,method="DP"):
    if not items:
        st.info("Tidak ada baris jadwal yang memenuhi filter."); return
    frame=request_frame(items)
    frame["Awal"]=pd.to_datetime(frame["Tanggal"]+" "+frame["Mulai"])
    frame["Akhir"]=pd.to_datetime(frame["Tanggal"]+" "+frame["Selesai"])
    frame["Kelas"]=frame["Kode kelas"]+" · "+frame["Mata kuliah"]
    frame["Status"]=["Tercatat di Excel" if selected is None else f"Masuk kombinasi {method}" if r.request_id in selected else f"Di luar kombinasi {method}" for r in items]
    labels=["Tercatat di Excel",f"Masuk kombinasi {method}",f"Di luar kombinasi {method}"]
    chart=alt.Chart(frame).mark_bar(cornerRadius=3,height=24).encode(
        x=alt.X("Awal:T",title="Waktu",axis=alt.Axis(format="%H:%M")),x2="Akhir:T",
        y=alt.Y("Kelas:N",sort=None,title=None),
        color=alt.Color("Status:N",scale=alt.Scale(domain=labels,range=["#344F60","#796000","#C6CCD1"]),legend=alt.Legend(title=None)),
        tooltip=["Kode kelas","Mata kuliah","Tanggal","Ruang","Mulai","Selesai","Peserta","Status"]
    ).properties(height=max(170,len(items)*38)).configure_view(strokeWidth=0)
    st.altair_chart(chart,width="stretch")


@st.cache_data(show_spinner=False)
def read_data(content,name):
    return load_workbook(BytesIO(content),name)


def init():
    if st.session_state.get("app_data_version")!="full-excel-v2":
        for key in ["queue","queue_initialized","processed","simulation","experiments","allocation_report",
                    "acceptance_report","requests","hash_report","dp_report","candidate_mode","room_scenario"]:
            st.session_state.pop(key,None)
        for key in ["allocation_workspaces","full_source","excel_benchmark_result","colab_test_report","queue_signature"]:
            st.session_state.pop(key,None)
        st.session_state.app_data_version="full-excel-v2"
    if "workbook_bytes" not in st.session_state:
        st.session_state.workbook_bytes=(ROOT/"data/dataset_jadwal_uts_feb_uph.xlsx").read_bytes()
    if "workbook_name" not in st.session_state:
        st.session_state.workbook_name="dataset_jadwal_uts_feb_uph.xlsx"


def navigate(page): st.session_state.page=page


def queue_to_allocation():
    st.session_state.page="Simulasi alokasi"
    st.session_state.allocation_scope="Dari antrean yang sudah diproses"
    processed=st.session_state.get('queue_processed',[])
    if processed: st.session_state.allocation_week=week_of(processed[0].day)


def get_workspace(data,week):
    if week not in st.session_state.allocation_workspaces:
        st.session_state.allocation_workspaces[week]=AllocationWorkspace(data,week)
    return st.session_state.allocation_workspaces[week]


def overview(data):
    heading("Smart Campus · Jadwal FEB","Seluruh data pencarian, ruangan, dan analisis jadwal berasal dari Excel aktif.")
    st.caption(f"Sumber: {data['source_name']}")
    a,b,c,d=st.columns(4)
    a.metric("Baris jadwal",len(data["display"]))
    b.metric("Kode mata kuliah",len(data["ingredients"]["mata_kuliah"]))
    c.metric("Ruangan",len(data["clean"]["ruang"]))
    d.metric("Catatan pemeriksaan",len(data["issues"]))
    left,right=st.columns([2,1],gap="large")
    with left:
        st.subheader("Jadwal dari Excel")
        candidates,excluded=scheduling_inputs(data)
        if candidates:
            groups=sorted({(r.room_id,r.day) for r in candidates})
            group=st.selectbox("Ruang dan tanggal",groups,format_func=lambda g:f"{g[0]} · {g[1]}",key="overview_group")
            timeline([r for r in candidates if (r.room_id,r.day)==group])
        else: st.info("Belum ada jadwal onsite yang dapat ditampilkan setelah pemeriksaan.")
        st.caption("Baris yang perlu diperiksa tetap tersedia di Data & panduan. Beberapa kelas dapat berbagi ruang dan waktu.")
    with right:
        st.subheader("Mulai dari kebutuhanmu")
        st.button("Cari jadwal Excel",on_click=navigate,args=("Cari jadwal",),width="stretch")
        st.button("Lihat ruangan Excel",on_click=navigate,args=("Ruangan",),width="stretch")
        st.button("Analisis pilihan jadwal",on_click=navigate,args=("Pilih jadwal",),width="stretch")
        st.button("Coba antrean Excel",on_click=navigate,args=("Antrean kegiatan",),width="stretch")
        st.button("Simulasikan alokasi ruang",on_click=navigate,args=("Simulasi alokasi",),width="stretch")
        st.caption("Seluruh algoritma telah tersinkron dengan Colab. Alokasi dan perubahan ruang berlangsung pada sesi simulasi.")
    st.subheader("Status fitur")
    st.dataframe(status_rows(),hide_index=True,width="stretch")
    total=sum(len(w.bookings) for w in st.session_state.allocation_workspaces.values())
    if total: st.info(f"Sesi ini menyimpan {total} alokasi simulasi. Lihat atau batalkan melalui Simulasi alokasi.")


def search_page(data):
    heading("Cari jadwal","Cari nama, kode mata kuliah, kelas, ruang, dan ID dosen dari Excel aktif.")
    st.caption("Hash Table · Adit | Trie · Zilan")
    with st.expander("Pengaturan indeks pencarian"):
        strategy=st.selectbox("Cara menyimpan indeks kode",["Chaining","Linear probing"],key="search_hash_strategy")
        st.caption("Pilihan ini memengaruhi indeks kode MK dan kelas. Data serta hasil pencarian tetap sama; anak Trie tetap memakai chaining.")
    try:
        indexes=build_search_indexes(data["ingredients"],"linear" if strategy=="Linear probing" else "chaining")
        room_table=room_search_table(data)
    except (ValueError,NotImplementedError) as error:
        st.error(f"Indeks belum dapat dibangun: {error}"); return
    mode=st.selectbox("Cari berdasarkan",["Awalan nama","Awalan kode MK","Kode MK lengkap","Kode kelas lengkap","ID ruang lengkap","ID dosen lengkap"],key="search_mode")
    query=st.text_input("Nama atau kode",placeholder="Contoh: akun, ACC9, ACC93105, F701",key="search_query")
    pair_mode=mode in ["Awalan nama","Awalan kode MK","Kode MK lengkap"]
    include_pairs=st.checkbox("Sertakan pasangan INT–NAS dari Excel",value=True,disabled=not pair_mode,key="search_include_pairs") and pair_mode
    st.caption("Pasangan mengikuti tabel Excel dan belum dikonfirmasi resmi. Opsi berlaku untuk nama/kode MK; kelas dan jumlah peserta tidak digabung.")
    trie_delete_preview(data)
    if not query.strip():
        st.info("Masukkan nama atau kode untuk mencari jadwal."); return
    value=query.strip()
    frame=data["display"]
    pair_details=pd.DataFrame()
    skipped_pairs=pd.DataFrame()
    if mode=="ID ruang lengkap":
        item=room_table.get(value.upper())
        if item is None: st.info("Kode tidak ditemukan."); return
        st.write("**Detail ruang dari Excel**")
        st.dataframe(pd.DataFrame([item]),hide_index=True,width="stretch")
        result=frame[frame["Ruang"].eq(value.upper())]
    elif mode=="ID dosen lengkap":
        lecturers=HashTableChaining()
        for code,detail in data["ingredients"]["kelas"]:
            if detail["lecturer_id"]:
                key=detail["lecturer_id"]
                lecturers.put(key,(lecturers.get(key) or [])+[code])
        result=frame[frame["Kode kelas"].isin(lecturers.get(value.upper()) or [])]
    elif mode=="Kode kelas lengkap":
        detail=indexes["classes"].get(value.upper())
        result=frame[frame["Kode kelas"].eq(detail["class_code"])] if detail else frame.iloc[:0]
    else:
        if mode=="Awalan nama": ids=indexes["names"].autocomplete(value)
        elif mode=="Awalan kode MK": ids=indexes["codes"].autocomplete(value)
        else:
            detail=indexes["courses"].get(value.upper())
            ids=[detail["course_code"]] if detail else []
        direct_ids=list(ids)
        if include_pairs:
            pairs,pair_details,skipped_pairs=pair_indexes(data,indexes["courses"])
            if mode=="Awalan nama":
                ids=bilingual_autocomplete(indexes["names"],value,pairs,indexes["courses"])
            elif mode=="Awalan kode MK":
                ids=bilingual_autocomplete(indexes["codes"],value,pairs,indexes["courses"])
            else:
                ids=expand_course_ids(direct_ids,pairs,indexes["courses"])
            pair_details=pair_details.loc[
                pair_details["Kode INT"].isin(direct_ids)|pair_details["Kode NAS"].isin(direct_ids)]
        # Resolve Trie IDs through the Colab Hash Table, not a replacement scan.
        class_ids=[]
        for code in ids:
            detail=indexes["courses"].get(code)
            if detail: class_ids.extend(detail["class_codes"])
        result=frame[frame["Kode kelas"].isin(class_ids)]
        if include_pairs:
            result=result.copy()
            result["Asal hasil"]=["Cocok langsung" if code in direct_ids else "Pasangan INT–NAS" for code in result["Kode MK"]]
    if result.empty: st.info("Kode tidak ditemukan atau belum memiliki jadwal pada Excel ini.")
    else:
        st.write(f"**{result['Kode MK'].nunique()} mata kuliah · {len(result)} kelas**")
        st.dataframe(result,hide_index=True,width="stretch")
        st.download_button("Unduh hasil CSV",result.to_csv(index=False).encode("utf-8-sig"),"hasil_pencarian.csv","text/csv")
        if not pair_details.empty:
            st.caption("Hasil mencakup pasangan yang tercatat di Excel. Status ‘otomatis’ pada Excel bukan konfirmasi kesetaraan resmi.")
            with st.expander("Pasangan INT–NAS yang dipakai"):
                st.dataframe(pair_details,hide_index=True,width="stretch")
        if not skipped_pairs.empty:
            with st.expander("Pasangan Excel yang belum dapat dipakai"):
                st.dataframe(skipped_pairs,hide_index=True,width="stretch")
    with st.expander("Cara pencarian bekerja"):
        table=indexes["courses"]
        st.caption(f"Indeks {strategy}: {len(table)} kode · probes {table.probes} · collisions saat put {table.collisions} · rehash {table.rehashes}.")
        st.write("Fungsi penghubung Colab mengisi Hash kelas/MK dan Trie nama/kode dari Excel. Kode lengkap memakai Hash; awalan memakai Trie lalu detailnya diambil melalui Hash. Opsi pasangan memakai relasi eksplisit dua arah dari tabel Excel dan fungsi bilingual_autocomplete Colab. Kode/kelas hasil tidak digandakan; pasangan kosong atau ambigu tidak ditebak.")


def queue_page(data):
    render_queue(data,minute_text,request_frame,queue_to_allocation)


def rooms_page(data):
    heading("Ruangan","Kapasitas berasal dari tabel ruang Excel; pemakaian dihitung dari tanggal dan jam jadwal pada Excel yang sama.")
    st.caption("AVL kapasitas dan pemakaian · Wildan & Asep")
    weeks=available_weeks(data)
    week=st.selectbox("Minggu jadwal",weeks,format_func=lambda w:f"{w[0]} · minggu {w[1]}",key="room_week") if weeks else None
    room_list,notes=room_inputs(data,week)
    if not room_list:
        st.info("Belum ada kapasitas ruang valid. Periksa tabel ruang pada Excel."); return
    registry=RoomView(room_list)
    workspace=get_workspace(data,week) if week else None
    view=st.radio("Tampilkan pemakaian",["Jadwal Excel","Hasil simulasi alokasi"],key="room_view")
    if view=="Hasil simulasi alokasi" and workspace:
        registry=SimpleNamespace(table=workspace.registry[0],capacity=workspace.registry[1],usage=workspace.registry[2],validate=workspace.validate)
        st.info(f"Pemakaian dari {len(workspace.bookings)} alokasi simulasi minggu ini. Kapasitas tetap dari Excel.")
    left,right=st.columns([1,2],gap="large")
    with left:
        source_participants=data["clean"]["jadwal_uts"]["peserta"].dropna()
        default=int(source_participants.iloc[0]) if not source_participants.empty else 1
        count=st.number_input("Peserta yang membutuhkan ruang",min_value=1,value=max(1,default),step=1)
        candidate=registry.capacity.ceiling_capacity(int(count))
        if candidate: st.success(f"{candidate.room_id} · {candidate.capacity} kursi (asumsi Excel)")
        else: st.info("Tidak ada ruangan dengan kapasitas yang mencukupi.")
        st.caption("kapasitas_asumsi pada Excel belum merupakan kapasitas resmi. Jenis/fasilitas ruang tidak tersedia; belum diperiksa oleh pencarian kapasitas.")
    with right:
        st.subheader("Pemakaian tertinggi")
        if week:
            k=st.slider("Jumlah ruang pada ranking",1,len(room_list),min(6,len(room_list))) if len(room_list)>1 else 1
            st.dataframe(room_frame(registry.usage.top_k_utilization(k)),hide_index=True,width="stretch",
                column_config={"Pemakaian (%)":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.1f%%")})
        else: st.info("Tanggal jadwal belum valid; ranking pemakaian belum tersedia.")
        st.caption("Slot reguler unik yang disentuh ujian onsite pada Senin–Jumat / 15 per minggu. Kelas yang berbagi ruang/jam tidak dihitung ganda. Jam aktual Excel dipakai; durasi yang berbeda tetap ditandai dalam laporan.")
    st.dataframe(room_frame(registry.capacity.inorder()),hide_index=True,width="stretch")
    if notes["invalid_room_rows"] or notes["invalid_schedule_rows"]:
        st.info(f"Baris yang tidak dapat dipetakan: ruang {notes['invalid_room_rows']}, jadwal {notes['invalid_schedule_rows']}. Baris tetap disimpan pada data sumber.")
    with st.expander("Pohon kapasitas dan pemeriksaan AVL"):
        registry.validate()
        st.success("Urutan, tinggi, dan keseimbangan AVL valid.")
        def dot(node):
            if not node: return []
            label=json.dumps(node.room.room_id)
            text=json.dumps(f"{node.room.room_id} | {node.room.capacity} kursi | h={node.height}")
            lines=[f"{label} [label={text}];"]
            for child in [node.left,node.right]:
                if child: lines.append(f"{label} -> {json.dumps(child.room.room_id)};")
            return lines+dot(node.left)+dot(node.right)
        st.graphviz_chart("digraph G { node [shape=box]; "+" ".join(dot(registry.capacity.root))+"}")
    room_algorithm_details(room_list)
    st.caption("Insert, delete, pencarian kapasitas, dan ranking AVL sudah aktif. Saat alokasi dibuat atau dibatalkan, fungsi Colab memperbarui Hash dan kedua indeks secara konsisten.")
    st.button("Kelola alokasi dan pembatalan",on_click=navigate,args=("Simulasi alokasi",),key="rooms_allocation")


def schedule_page(data):
    render_schedule(data,request_frame,timeline,get_workspace)


def guide_page(data):
    heading("Data & panduan","Excel aktif menjadi satu-satunya sumber data aplikasi. Implementasi algoritma mengikuti Colab.")
    tab1,tab2,tab3=st.tabs(["Data FEB","Pemeriksaan sumber","Panduan"])
    with tab1:
        st.caption(f"Berkas aktif: {data['source_name']}")
        st.dataframe(data["display"],hide_index=True,width="stretch")
        st.download_button("Unduh jadwal FEB CSV",data["display"].to_csv(index=False).encode("utf-8-sig"),"jadwal_feb.csv","text/csv")
        upload=st.file_uploader("Gunakan Excel dengan struktur yang sama",type=["xlsx"])
        if upload is not None and st.button("Baca & validasi Excel"):
            try:
                read_data(upload.getvalue(),upload.name)
                st.session_state.workbook_bytes=upload.getvalue()
                st.session_state.workbook_name=upload.name
                st.rerun()
            except Exception as error: st.error(f"Excel belum dapat dibaca: {error}")
        if st.button("Kembalikan dataset bawaan"):
            st.session_state.workbook_bytes=(ROOT/"data/dataset_jadwal_uts_feb_uph.xlsx").read_bytes()
            st.session_state.workbook_name="dataset_jadwal_uts_feb_uph.xlsx"
            st.rerun()
        st.caption("Unggahan mengganti sumber pada seluruh halaman dalam sesi ini. Empat lembar wajib: jadwal_uts, mata_kuliah, pasangan_int_nas, ruang. Berkas asli tidak diubah.")
    with tab2:
        st.warning("Kapasitas masih asumsi. Pasangan INT–NAS belum dikonfirmasi resmi. Catatan durasi dan ruang perlu diperiksa sebelum penggunaan operasional.")
        st.dataframe(data["issues"],hide_index=True,width="stretch")
        st.download_button("Unduh laporan pemeriksaan CSV",data["issues"].to_csv(index=False).encode("utf-8-sig"),"laporan_data.csv","text/csv")
        st.caption("Temuan tiga ruang antar-PDF adalah catatan notebook yang berlaku hanya pada Excel bawaan dengan hash yang cocok. PDF tidak dibandingkan ulang oleh aplikasi.")
        st.dataframe(data["clean"]["pasangan_int_nas"],hide_index=True,width="stretch")
    with tab3:
        st.markdown("""1. **Cari jadwal:** cari nama/kode dari Excel; misalnya akun, ACC9, ACC93105, ID kelas, ruang, atau dosen.
2. **Ruangan:** kapasitas dari kapasitas_asumsi Excel; pemakaian dihitung dari slot unik yang disentuh jadwal onsite.
3. **Pilih jadwal:** pilih ruang/hari aktual; DP menganalisis baris ujian dari Excel. Tidak ada target hasil buatan atau perubahan jadwal.
4. **Antrean:** masukkan kelas, lihat teratas, proses berikutnya, lalu teruskan ke simulasi alokasi.
5. **Simulasi alokasi:** pilih kelas Excel, coba ruang alternatif, lihat alasan penolakan, unduh hasil, atau batalkan alokasi. Pasangan INT–NAS harus dipilih untuk simulasi sebelum digabung.
6. **Eksperimen:** ukur data Excel aktif atau baca arsip benchmark Colab dengan sumber pengukuran yang jelas.
7. **Unggah Excel:** seluruh halaman mengikuti workbook baru; simulasi dan hasil pengukuran lama direset.""")
        st.dataframe(status_rows(),hide_index=True,width="stretch")
        test_panel()
        with st.expander("Status penghubung Colab"):
            st.caption(f"Snapshot Colab: {SOURCE_LABEL}. Definisi algoritma dan layanan disalin tanpa perubahan. Hash sumber: {SNAPSHOT_HASH}. Data jadwal tetap dari Excel aktif.")
        st.markdown("[Notebook algoritma](https://colab.research.google.com/drive/1D0LHKRtp9G-LxFdl0vKPz_Gmcy5VNdS0) · [Dataset Excel](https://drive.google.com/file/d/14ssmxLs2leJDNAUBvTpuk2ukbxm8b-iP/view)")


init()
try:
    data=read_data(st.session_state.workbook_bytes,st.session_state.workbook_name)
except Exception as error:
    st.error(f"Excel belum dapat dibaca: {error}")
    st.stop()
signature=(data['sha256'],SNAPSHOT_HASH)
if st.session_state.get('full_source')!=signature:
    st.session_state.full_source=signature
    st.session_state.allocation_workspaces={}
    for key in ['excel_benchmark_result','colab_test_report','queue_signature','allocation_selected','allocation_pairs']:
        st.session_state.pop(key,None)
with st.sidebar:
    st.markdown('<div class="campus-wordmark"><span class="campus-mark">◫</span>Smart Campus</div>',unsafe_allow_html=True)
    st.caption("Ruang, waktu, dan kegiatan.")
    st.divider()
    current=st.session_state.get("page","Ringkasan")
    st.session_state.page=current if current in PAGES else "Ringkasan"
    icons=["dashboard","search","format_list_numbered","calendar_month","meeting_room","event_available","science","description"]
    with st.container(key="sidebar_navigation"):
        for destination,icon in zip(PAGES,icons):
            st.button(destination,key=f"nav_{destination}",icon=f":material/{icon}:",
                type="primary" if st.session_state.page==destination else "secondary",
                width="stretch",on_click=navigate,args=(destination,),
                help="Halaman aktif" if st.session_state.page==destination else f"Buka {destination.lower()}")
    page=st.session_state.page
    st.divider()
    st.caption("Sumber data: Excel FEB aktif")
    st.caption(data["source_name"])
    st.caption("Seluruh algoritma aktif · sesi simulasi")
    st.caption(f"Snapshot algoritma · {SOURCE_LABEL}")
if page=="Ringkasan": overview(data)
elif page=="Cari jadwal": search_page(data)
elif page=="Antrean kegiatan": queue_page(data)
elif page=="Simulasi alokasi": allocation_page(data,get_workspace,request_frame,timeline,room_frame)
elif page=="Ruangan": rooms_page(data)
elif page=="Pilih jadwal": schedule_page(data)
elif page=="Eksperimen": experiments_page(data)
else: guide_page(data)
