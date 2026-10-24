"""A simple queue workflow with technical controls disclosed on demand."""
from dataclasses import replace
import json
import pandas as pd
import streamlit as st
from .capabilities import SNAPSHOT_HASH
from .feb_views import queue_inputs
from .heap import MinHeapPriorityQueue


def render_queue(data, minute_text, request_frame, handoff):
    st.title("Antrean kegiatan")
    st.write("Tambahkan kelas yang ingin ditangani, lalu proses satu per satu sebelum mengalokasikan ruang.")
    requests, excluded = queue_inputs(data)
    if not requests:
        st.info("Belum ada kelas yang dapat dimasukkan. Periksa jadwal pada Data & panduan.")
        if not excluded.empty: st.dataframe(excluded, hide_index=True, width="stretch")
        return
    days = sorted({r.day for r in requests})
    if "queue_day" not in st.session_state and st.session_state.get("queue_saved_day") in days:
        st.session_state.queue_day = st.session_state.queue_saved_day
    day = st.selectbox("Tanggal kegiatan", days, key="queue_day",
        help="Mengganti tanggal memulai antrean baru. Riwayat untuk tanggal sebelumnya akan dikosongkan.")
    st.caption("Mengganti tanggal akan mengosongkan antrean dan riwayatnya.")
    st.session_state.queue_saved_day = day
    signature = (data["sha256"], SNAPSHOT_HASH, day)
    if st.session_state.get("queue_signature") != signature:
        st.session_state.queue_signature = signature
        st.session_state.queue = MinHeapPriorityQueue()
        st.session_state.queue_processed = []
        st.session_state.queue_last_clock = 0
        st.session_state.queue_clock = 0
        st.session_state.queue_saved_clock = 0
        st.session_state.pop("queue_class", None)
        st.session_state.pop("queue_notice", None)
    queue = st.session_state.queue
    processed = st.session_state.queue_processed
    batch = [r for r in requests if r.day == day]
    frame = data["display"][data["display"]["Tanggal"].eq(day)]
    done = {r.request_id for r in processed}
    remaining = [r for r in batch if r.request_id not in done and not queue.position_map.contains(r.request_id)]
    if "queue_clock" not in st.session_state:
        st.session_state.queue_clock = st.session_state.queue_saved_clock
    clock = int(st.session_state.queue_clock)

    def advance_clock():
        if clock < st.session_state.queue_last_clock:
            raise ValueError("Waktu simulasi tidak boleh mundur. Periksa Pengaturan lanjutan.")
        if queue.aging_step is not None: queue.apply_aging(clock, queue.aging_step)
        st.session_state.queue_last_clock = clock

    def notify(message):
        st.session_state.queue_notice = message
        st.rerun()

    if st.session_state.get("queue_notice"):
        st.success(st.session_state.pop("queue_notice"))
    left, right = st.columns([1,1], gap="large")
    with left:
        st.subheader("Tambahkan kelas")
        available = {r.request_id:r for r in remaining}
        code = st.selectbox("Pilih kelas", list(available), index=None, key="queue_class",
            placeholder="Cari nama mata kuliah atau kode kelas",
            format_func=lambda key: f"{available[key].title} · {key}")
        if code:
            selected = available[code]
            st.caption(f"{minute_text(selected.start)}–{minute_text(selected.end)} · {selected.room_id or 'Online'} · {selected.participants} peserta")
            source = frame[frame["Kode kelas"].eq(code)].iloc[0]
            if source["Perlu diperiksa"] == "Ya":
                st.warning("Kelas ini memiliki catatan pada Excel. Periksa sumber sebelum mengalokasikan ruang.")
        elif not remaining:
            st.caption("Seluruh kelas pada tanggal ini sudah masuk antrean atau sudah diproses.")
        if st.button("Masukkan ke antrean", type="primary" if not queue else "secondary", disabled=not code):
            try:
                advance_clock()
                queue.push(replace(available[code], submitted_at=clock))
                notify(f"{available[code].title} ditambahkan ke antrean.")
            except ValueError as error: st.error(str(error))
        if st.button("Tambahkan semua kelas", disabled=not remaining, type="tertiary"):
            try:
                advance_clock()
                incoming = [replace(r, submitted_at=clock) for r in remaining]
                if not queue: queue.build(incoming)
                else:
                    for request in incoming: queue.push(request)
                notify(f"{len(incoming)} kelas ditambahkan ke antrean.")
            except ValueError as error: st.error(str(error))
    with right:
        st.subheader("Berikutnya diproses")
        if queue:
            top = queue.peek()
            st.write(f"**{top.title}**")
            st.caption(f"{top.request_id} · {minute_text(top.start)}–{minute_text(top.end)} · {top.room_id or 'Online'}")
        else:
            st.info("Antrean kosong. Pilih kelas di sebelah kiri untuk memulai.")
        if st.button("Proses permintaan berikutnya", type="primary" if queue else "secondary", disabled=not queue):
            try:
                advance_clock()
                request = queue.pop()
                processed.append(request)
                notify(f"{request.title} selesai diproses dan siap untuk alokasi ruang.")
            except (ValueError,IndexError) as error: st.error(str(error))
        if processed:
            st.button("Lanjutkan ke simulasi alokasi", on_click=handoff, key="queue_to_allocation")
            st.caption(f"{len(processed)} kelas siap dialokasikan. Pemrosesan antrean belum membuat booking.")

    waiting, history = st.tabs([f"Menunggu ({len(queue)})", f"Sudah diproses ({len(processed)})"])
    ordered = queue.ordered_entries()
    simple_rows = [{"Urutan":i,"Mata kuliah":r.title,"Kode kelas":r.request_id,
        "Jam":f"{minute_text(r.start)}–{minute_text(r.end)}","Ruang":r.room_id or "Online"}
        for i, (_,r,_) in enumerate(ordered,1)]
    with waiting:
        if ordered:
            st.dataframe(pd.DataFrame(simple_rows), hide_index=True, width="stretch")
            st.caption("Jam mulai lebih awal didahulukan. Jika jam sama, kelas yang masuk lebih dahulu diproses lebih dulu.")
            st.download_button("Unduh antrean CSV",pd.DataFrame(simple_rows).to_csv(index=False).encode("utf-8-sig"),"antrean_excel.csv","text/csv")
        else:
            st.caption("Kelas yang ditambahkan akan muncul di sini sesuai urutan penanganannya.")
    with history:
        if processed: st.dataframe(request_frame(processed)[["Mata kuliah","Kode kelas","Mulai","Selesai","Ruang"]], hide_index=True, width="stretch")
        else: st.caption("Belum ada kelas yang diproses.")

    with st.expander("Pengaturan & penjelasan lanjutan"):
        settings, algorithm, source = st.tabs(["Waktu simulasi", "Cara kerja algoritma", "Sumber Excel"])
        with settings:
            clock = int(st.number_input("Jam simulasi antrean (menit)", min_value=0, step=1, key="queue_clock"))
            st.session_state.queue_saved_clock = clock
            st.caption("Opsional untuk demonstrasi waktu tunggu. Dimulai dari 0 dan berbeda dari jam ujian pada Excel.")
            step = int(st.number_input("Interval aging T (menit)",min_value=1,value=30,step=1,key="queue_aging_step"))
            st.caption("Aging menaikkan prioritas setelah menunggu. Semua ujian FEB sudah berprioritas 1, sehingga pengaturan ini tidak mengubah urutannya. Angka 30 menit merupakan pengaturan simulasi.")
            if queue.aging_step is not None: st.caption(f"Aging aktif: setiap {queue.aging_step} menit; terakhir dihitung pada menit {queue.now}.")
            if st.button("Terapkan peningkatan prioritas", disabled=not queue):
                try:
                    if clock < st.session_state.queue_last_clock: raise ValueError("Waktu simulasi tidak boleh mundur.")
                    queue.apply_aging(clock,step)
                    st.session_state.queue_last_clock = clock
                    notify("Pengaturan prioritas diterapkan. Seluruh ujian tetap berprioritas 1.")
                except ValueError as error: st.error(str(error))
            if st.button("Mulai ulang antrean", disabled=not queue and not processed,
                         help="Mengosongkan antrean dan riwayat pada tanggal ini."):
                st.session_state.pop("queue_signature",None)
                st.rerun()
        with algorithm:
            st.write("**Heap & Priority Queue · Ikin & Deni**")
            st.write("Key: (prioritas efektif, jam mulai, counter masuk). Push melakukan sift-up; pop mengganti akar dan melakukan sift-down. Hash tim melacak posisi ID. FIFO berlaku saat prioritas dan jam sama.")
            st.caption("Push/pop O(log n), peek O(1), build dan aging O(n). Pratinjau menguras salinan O(n log n), sehingga antrean asli tetap utuh.")
            queue.validate()
            st.caption(f"Heap dan Hash posisi valid · {queue.comparisons} perbandingan key pada operasi antrean.")
            st.dataframe(pd.DataFrame([{"Indeks":i,"Kode kelas":r.request_id,"Key":str(key),"Masuk (menit simulasi)":r.submitted_at,"Counter FIFO":counter,
                "Posisi Hash":queue.position_map.get(r.request_id)} for i,(key,r,counter) in enumerate(queue.entries)]),hide_index=True,width="stretch")
            if queue:
                nodes=[f'n{i} [label={json.dumps(f"{r.request_id} | p={key[0]} | {minute_text(r.start)} | #{counter}")}];'
                       for i,(key,r,counter) in enumerate(queue.entries[:15])]
                edges=[f'n{(i-1)//2} -> n{i};' for i in range(1,min(15,len(queue)))]
                st.graphviz_chart("digraph Heap { node [shape=box]; "+" ".join(nodes+edges)+"}")
                if len(queue)>15: st.caption("Diagram menampilkan 15 simpul pertama. Tabel memuat seluruh antrean.")
        with source:
            st.caption(f"Sumber: {data['source_name']}. Semua kelas, termasuk LAB dan online, mengikuti baris Excel. Seluruhnya kategori ujian dengan prioritas 1 dan bobot 10.")
            st.caption("Antrean dipisahkan per tanggal. Mengganti tanggal atau workbook memulai antrean baru.")
            st.dataframe(frame,hide_index=True,width="stretch")
            if not excluded.empty: st.dataframe(excluded,hide_index=True,width="stretch")
