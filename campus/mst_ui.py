"""Room-network simulation. Excel supplies nodes; users own assumed edges/costs."""
import json
from pathlib import Path
from math import isclose
import altair as alt
import pandas as pd
import streamlit as st
from .mst import kruskal_mst, prim_mst, mst_room_scenario, validate_mst_graph, validate_mst, mst_cut_witness
from .capabilities import SNAPSHOT_HASH

COLUMNS = ['Dari ruang', 'Ke ruang', 'Biaya simulasi']


def edge_frame(edges):
    return pd.DataFrame([(e.u, e.v, e.weight) for e in edges], columns=COLUMNS)


def graph_from_editor(nodes, frame):
    nodes, edges = validate_mst_graph(nodes, frame[COLUMNS].itertuples(index=False, name=None))
    if any(e.weight < 0 for e in edges):
        raise ValueError('Biaya simulasi tidak boleh negatif.')
    if any(e.weight > 1e12 for e in edges):
        raise ValueError('Biaya simulasi per koneksi maksimal 1 triliun satuan.')
    return nodes, edges


def network_chart(nodes, edges, selected, show_all=False):
    positions = {node: (i % 8, -(i // 8)) for i, node in enumerate(nodes)}
    chosen = {(e.u, e.v) for e in selected}
    lines = []
    for e in edges:
        used = (e.u, e.v) in chosen
        if not used and not show_all:
            continue
        x, y = positions[e.u]; x2, y2 = positions[e.v]
        lines.append({'Dari': e.u, 'Ke': e.v, 'Biaya': e.weight,
                      'Status': 'Terpilih' if used else 'Alternatif', 'x': x, 'y': y, 'x2': x2, 'y2': y2})
    points = pd.DataFrame([{'Ruang': n, 'x': x, 'y': y} for n, (x, y) in positions.items()], columns=['Ruang','x','y'])
    base = alt.Chart(points).encode(x=alt.X('x:Q', axis=None, scale=alt.Scale(domain=[-.5,7.5])),
                                    y=alt.Y('y:Q', axis=None, scale=alt.Scale(domain=[-(max(len(nodes)-1,0)//8)-.6,.6])))
    layers = []
    if lines:
        layers.append(alt.Chart(pd.DataFrame(lines)).mark_rule(strokeWidth=3).encode(
            x=alt.X('x:Q', axis=None, scale=alt.Scale(domain=[-.5,7.5])),
            y=alt.Y('y:Q', axis=None, scale=alt.Scale(domain=[-(max(len(nodes)-1,0)//8)-.6,.6])),
            x2='x2:Q', y2='y2:Q',
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Terpilih','Alternatif'], range=['#796000','#A9B2BA']), legend=None),
            strokeDash=alt.StrokeDash('Status:N', scale=alt.Scale(domain=['Terpilih','Alternatif'], range=[[1,0],[5,5]]), legend=None),
            tooltip=['Dari:N','Ke:N','Biaya:Q','Status:N']))
    layers.extend([base.mark_circle(size=850, color='#344F60', opacity=1).encode(tooltip=['Ruang:N']),
                   base.mark_text(dy=-25, fontSize=13, color='#263740').encode(text='Ruang:N')])
    return alt.layer(*layers).properties(height=max(240, ((len(nodes)+7)//8)*120)).configure_view(strokeWidth=0)


def reset_scenario():
    st.session_state.mst_revision += 1
    for key in ('mst_report', 'mst_draft_snapshot', 'mst_editor_base'):
        st.session_state.pop(key, None)


def render_mst(data):
    st.title('Koneksi ruang')
    st.write('Hubungkan ruang dengan total biaya simulasi paling kecil. Bandingkan hasil Kruskal dan Prim.')
    st.info('Ruang berasal dari Excel aktif. Semua koneksi dan biaya di halaman ini adalah asumsi simulasi yang bisa diedit; bukan jarak atau biaya instalasi nyata.')
    try:
        nodes, defaults = mst_room_scenario(data['clean']['ruang'])
    except ValueError as error:
        st.error(f'Data ruang belum dapat dipakai: {error} Periksa lembar ruang di Data & panduan.')
        return
    signature = (data['sha256'], SNAPSHOT_HASH)
    if st.session_state.get('mst_source') != signature:
        st.session_state.mst_source = signature
        st.session_state.mst_revision = 0
        for key in ('mst_report', 'mst_draft_snapshot', 'mst_editor_base'):
            st.session_state.pop(key, None)
    if not nodes:
        st.warning('Belum ada ruang pada Excel aktif. Unggah workbook yang memiliki data ruang melalui Data & panduan.')
        return
    st.caption(f"{len(nodes)} ruang · {data['source_name']} · biaya dalam satuan simulasi")
    with st.expander('Atur koneksi & biaya'):
        st.write('Ubah biaya, tambah koneksi, atau hapus baris yang tidak tersedia. Setiap pasangan ruang cukup ditulis sekali.')
        st.caption('Template awal menghubungkan urutan kode di lantai yang sama (biaya 1) dan urutan yang sama antar-lantai dalam gedung yang sama (biaya 3). Ini asumsi, bukan bukti kedekatan fisik. Ruang yang tidak memiliki koneksi tetap ikut dihitung.')
        editor_key = f'mst_editor_{data["sha256"]}_{st.session_state.mst_revision}'
        if editor_key not in st.session_state:
            st.session_state.mst_editor_base = st.session_state.get('mst_draft_snapshot', edge_frame(defaults)).copy()
        edited = st.data_editor(st.session_state.mst_editor_base, num_rows='dynamic', hide_index=True, width='stretch',
            column_config={COLUMNS[0]: st.column_config.SelectboxColumn(COLUMNS[0], options=list(nodes), required=True),
                           COLUMNS[1]: st.column_config.SelectboxColumn(COLUMNS[1], options=list(nodes), required=True),
                           COLUMNS[2]: st.column_config.NumberColumn(COLUMNS[2], min_value=0, max_value=1e12, required=True)},
            key=editor_key)
        st.session_state.mst_draft_snapshot = edited.copy()
        st.button('Kembalikan template simulasi', key='mst_reset', on_click=reset_scenario)
        st.caption('Perubahan hanya berlaku dalam sesi ini. Excel asli tetap menjadi sumber daftar ruang.')
    try:
        nodes, edges = graph_from_editor(nodes, edited)
    except ValueError as error:
        st.error(f'Periksa koneksi: {error}')
        return
    graph_key = (nodes, edges)
    run = st.button('Hitung koneksi termurah', type='primary', key='mst_run')
    if run or 'mst_report' not in st.session_state:
        a, b = kruskal_mst(nodes, edges, trace_limit=100), prim_mst(nodes, edges, trace_limit=100)
        if not all(validate_mst(nodes, edges, r)['valid'] for r in (a,b)) or not isclose(a.total_cost,b.total_cost,rel_tol=1e-12,abs_tol=1e-12):
            st.error('Pemeriksaan hasil gagal. Hasil belum dapat ditampilkan.'); return
        st.session_state.mst_report = (graph_key, a, b)
    previous, a, b = st.session_state.mst_report
    if previous != graph_key:
        st.info('Koneksi berubah. Tekan “Hitung koneksi termurah” untuk memperbarui hasil.')
        return
    groups = len(a.components)
    if groups == 1:
        st.success(f'Seluruh {len(nodes)} ruang terhubung dengan {len(a.edges)} koneksi. Total biaya simulasi: {a.total_cost:g}.')
    else:
        st.warning(f'Terbentuk {groups} jaringan terpisah. Semua ruang belum terhubung; tambahkan koneksi antarjaringan jika memang tersedia dalam skenario Anda.')
    result_tab, compare_tab, learn_tab = st.tabs(['Hasil koneksi', 'Bandingkan metode', 'Cara kerja & bukti'])
    with result_tab:
        method = st.selectbox('Lihat hasil metode', ['Kruskal', 'Prim'], key='mst_method')
        result = a if method=='Kruskal' else b
        st.write(f'**{len(result.edges)} koneksi terpilih · biaya {result.total_cost:g} · {groups} jaringan**')
        show_all = st.checkbox('Tampilkan koneksi alternatif', key='mst_show_all')
        st.altair_chart(network_chart(nodes,edges,result.edges,show_all), width='stretch')
        st.caption('Diagram skematis berdasarkan urutan kode ruang. Garis penuh = terpilih; garis putus-putus = alternatif. Posisi bukan denah gedung. Biaya tiap koneksi tersedia pada tabel dan saat garis disorot.')
        st.dataframe(edge_frame(result.edges), hide_index=True, width='stretch')
        if groups>1:
            st.dataframe(pd.DataFrame([{'Jaringan':i+1,'Ruang':', '.join(group)} for i,group in enumerate(result.components)]), hide_index=True, width='stretch')
        report = {'source_excel':data['source_name'], 'excel_sha256':data['sha256'], 'notebook_sha256':SNAPSHOT_HASH,
                  'edge_cost_source':'Editable simulation assumptions; not physical distances/installation costs',
                  'nodes':list(nodes), 'edges':[{'u':e.u,'v':e.v,'cost':e.weight} for e in edges],
                  'method':method, 'selected':[{'u':e.u,'v':e.v,'cost':e.weight} for e in result.edges],
                  'total_cost':result.total_cost, 'components':result.components}
        st.download_button('Unduh skenario & hasil', json.dumps(report,ensure_ascii=False,indent=2), 'koneksi_ruang_simulasi.json', 'application/json', key='mst_download')
    with compare_tab:
        st.dataframe(pd.DataFrame([{'Metode':r.algorithm,'Biaya simulasi':r.total_cost,'Koneksi':len(r.edges),
            'Jaringan':len(r.components),'Validasi struktur & optimalitas':'Lulus'} for r in (a,b)]),hide_index=True,width='stretch')
        st.write('Kedua metode menghasilkan biaya minimum yang sama. Jika beberapa koneksi memiliki biaya sama, susunan koneksi optimum dapat berbeda.')
        st.caption('Validator memeriksa jumlah sisi V−C, tidak ada siklus, semua komponen tercakup, total biaya, dan cycle property. C adalah jumlah jaringan terpisah; untuk graf terhubung, sisi = V−1.')
        frame = pd.read_csv(Path(__file__).resolve().parents[1]/'data/mst_benchmarks.csv')
        with st.expander('Pengukuran sparse, dense & forest'):
            st.caption('Graf sintetis untuk menguji pertumbuhan, terpisah dari data ruang. Seed 42; 1 warm-up, 5 run, median. Setup dan validasi di luar timer; memori diukur terpisah. Pengukuran mesin lokal, bukan jaminan metode tercepat.')
            scenario = st.selectbox('Pola graf eksperimen', ['sparse','dense','forest'],
                format_func=lambda s: {'sparse':'Jarang terhubung (sparse)','dense':'Semua pasangan terhubung (dense)','forest':'Dua jaringan terpisah (forest)'}[s],
                key='mst_benchmark_scenario')
            chart = alt.Chart(frame[frame.scenario.eq(scenario)]).mark_line(point=True).encode(
                x=alt.X('n:Q',title='Jumlah ruang (sintetis)'), y=alt.Y('median_seconds:Q',title='Median waktu (detik)'),
                color=alt.Color('algorithm:N',title='Metode',scale=alt.Scale(domain=['Kruskal','Prim'],range=['#796000','#344F60']),legend=alt.Legend(orient='bottom')),
                tooltip=['algorithm','scenario','n','edges','median_seconds','peak_bytes']).properties(height=260)
            st.altair_chart(chart, width='stretch')
            st.dataframe(frame.drop(columns=['run_seconds']),hide_index=True,width='stretch')
            st.download_button('Unduh pengukuran MST CSV',frame.to_csv(index=False),'mst_benchmarks.csv','text/csv',key='mst_benchmark_download')
    with learn_tab:
        st.write('**Kruskal:** urutkan koneksi dari biaya terkecil. Tambahkan koneksi bila kedua ujung belum berada pada jaringan yang sama. Union-Find mencegah siklus.')
        st.write('**Prim:** mulai dari satu ruang. Min-heap memilih koneksi termurah menuju ruang baru. Bila jaringan terputus, mulai lagi dari ruang yang belum dikunjungi.')
        st.caption('Kruskal memakai merge sort manual dan Union-Find dengan rank/path compression. Prim memakai min-heap array manual (lazy). Waktu O(V + E log E), ruang O(V+E). MST menghubungkan ruang; keputusan jadwal tetap melalui DP/Greedy dan simulasi alokasi.')
        with st.expander('Bukti cut/cycle & langkah algoritma'):
            if a.edges:
                index = st.selectbox('Periksa sisi terpilih',list(range(len(a.edges))),format_func=lambda i:f'{a.edges[i].u} ↔ {a.edges[i].v} · {a.edges[i].weight:g}',key='mst_cut_edge')
                witness = mst_cut_witness(nodes,edges,a,index)
                st.write('Jika sisi ini dilepas, salah satu sisi potongannya berisi: '+', '.join(witness['side_a'])+'.')
                st.write(f'Biaya termurah melintasi potongan = {witness["minimum"]:g}; sisi terpilih memiliki biaya itu. Cut property terpenuhi (tie diperbolehkan).')
                st.dataframe(edge_frame(witness['crossing']), hide_index=True, width='stretch')
            st.write('Cycle property: setiap koneksi yang tidak dipilih tidak boleh lebih murah dari koneksi termahal pada jalur pohon antara dua ujungnya. Pemeriksaan ini lulus untuk kedua hasil.')
            st.caption('Trace dibatasi 100 langkah per metode. Validator independen berada di luar timer benchmark.')
            for r in (a,b):
                st.write(r.algorithm)
                st.dataframe(pd.DataFrame(r.trace,columns=['Dari','Ke','Biaya','Keputusan']),hide_index=True,width='stretch')
