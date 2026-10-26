"""Targeted, idempotent MST section authoring; preserves existing teammate cells."""
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'references/UTS_Group2_Smart_Campus.ipynb'
n = json.loads(path.read_text())

def cell(kind, source, identifier):
    result = {'cell_type': kind, 'id': identifier, 'metadata': {}, 'source': source.splitlines(keepends=True)}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result

n['cells'] = [c for c in n['cells'] if not c.get('id', '').startswith('uas-mst-')]
core = (ROOT/'scripts/uas_sources/mst_source.py').read_text()
# Keep manual_merge_sort in shared notebook setup; core source is extracted verbatim.
core += '\n\nmst_nodes_feb, mst_edges_simulasi = mst_room_scenario(data_bersih["ruang"])\n'
core += '''mst_kruskal_feb = kruskal_mst(mst_nodes_feb, mst_edges_simulasi, trace_limit=100)
mst_prim_feb = prim_mst(mst_nodes_feb, mst_edges_simulasi, trace_limit=100)
assert mst_kruskal_feb.total_cost == mst_prim_feb.total_cost
for hasil in (mst_kruskal_feb, mst_prim_feb):
    print(hasil.algorithm, "ruang:", len(hasil.nodes), "sisi:", len(hasil.edges),
          "komponen:", len(hasil.components), "biaya simulasi:", hasil.total_cost)
    print("Sertifikat:", validate_mst(mst_nodes_feb, mst_edges_simulasi, hasil))
print("ASUMSI SIMULASI: Excel hanya menyediakan ruang/gedung/lantai, bukan sisi atau biaya.")
'''
# Find cleaned dataframe variable, not hard-coded cell indexes.
all_source = '\n'.join(''.join(c['source']) for c in n['cells'] if c['cell_type']=='code')
if 'data_bersih' not in all_source:
    raise RuntimeError('Inspect cleaned workbook variable before patching')
index = next(i for i,c in enumerate(n['cells']) if ''.join(c['source']).startswith('## 6. Integrasi'))
n['cells'][index:index] = [cell('markdown', '''## UAS · S11 — Minimum Spanning Tree: koneksi ruang

**Satu fitur MST, dua implementasi manual: Kruskal dan Prim.** Node berasal dari lembar `ruang` Excel FEB aktif. Excel tidak berisi konektivitas, koordinat, jarak, atau biaya instalasi. Semua sisi/bobot di bawah adalah **asumsi simulasi yang dapat diganti**, bukan peta fisik atau estimasi biaya nyata.

Template awal: kode ruang berurutan dalam gedung/lantai yang sama dihubungkan dengan biaya 1; ruang pada urutan yang sama di dua lantai berurutan diberi biaya 3. Urutan kode tidak membuktikan kedekatan fisik. Streamlit menyediakan editor koneksi dan biaya; workbook asli tidak berubah. Gedung terpisah tidak diberi koneksi otomatis.

Kruskal mengurutkan sisi dengan merge sort manual lalu menerima sisi yang menggabungkan dua komponen melalui Union-Find (rank + path compression). Prim mengembangkan jaringan dari satu ruang dengan min-heap array manual; sisi menuju ruang yang sudah dikunjungi dilewati. Keduanya menghasilkan **minimum spanning forest** bila graf terputus, termasuk ruang terisolasi.

Validator terpisah memeriksa sisi input, V−C sisi, tidak bersiklus, cakupan komponen, total biaya, serta cycle property (tidak ada sisi nonpohon yang lebih murah dari sisi terbesar pada jalur pohon). Cut witness menunjukkan bahwa satu sisi terpilih merupakan sisi termurah yang melintasi potongan. Kesamaan biaya dua metode saja bukan bukti optimalitas.

Waktu keduanya O(V + E log E), memori O(V+E). Lazy Prim menyimpan sampai O(E) item heap; untuk graf simple log E = O(log V). Validator O(V(V+E)) berada di luar pengukuran algoritma. MST menghubungkan jaringan, tidak memilih jadwal atau rute terpendek.
''', 'uas-mst-guide'), cell('code', core, 'uas-mst-core')]
for c in n['cells']:
    if c['cell_type'] == 'code' and 'TEST_IDS = ' in ''.join(c['source']):
        s=''.join(c['source'])
        if '\ndef test_t29():' in s:
            begin=s.index('\ndef test_t29():')
            end=s.index('TEST_IDS = ')
            s=s[:begin]+'\n\n'+s[end:]
        start=s.index('TEST_IDS = ')
        s=s[:start]+(ROOT/'scripts/uas_sources/mst_tests_source.py').read_text()+'\n\n'+s[start:]
        s=s.replace('range(1, 29)', 'range(1, 34)')
        s=s.replace('"T28": test_t28}', '"T28": test_t28, '+', '.join(f'"T{i}": test_t{i}' for i in range(29,34))+'}')
        c['source']=s.splitlines(keepends=True)
    elif c['cell_type']=='markdown' and ''.join(c['source']).startswith('## 7. Pengujian'):
        c['source']=['## 7. Pengujian Lengkap — Semua anggota\n\nT01–T33 terdaftar. T29–T33 menguji MST dengan graf terhubung, forest/ruang terisolasi/kosong, tie/bobot nol/negatif, validasi input dan sertifikat salah, serta 60 graf kecil acak dibanding enumerasi subset independen.\n']
# Benchmarks execute after shared measure functions have been defined.
n['cells'].extend([cell('markdown', '''## UAS · S11 — Bukti eksperimen MST

Graf sintetis sparse, dense, dan forest; V=16,32,64,128. Seed 42, satu warm-up, lima pengulangan, median dan semua waktu mentah disimpan. Kruskal dan Prim memakai graf yang sama. Pembuatan input, validator optimalitas, dan penulisan CSV berada di luar timer; pengukuran peak memory dijalankan terpisah. Hasil mesin lokal ini tidak membuktikan satu metode selalu lebih cepat.
''','uas-mst-bench-guide'), cell('code', (ROOT/'scripts/uas_sources/mst_benchmark_source.py').read_text()+'''

mst_benchmark_results = run_mst_benchmarks()
pd.DataFrame(mst_benchmark_results).to_csv("mst_benchmarks.csv", index=False)
mst_benchmark_environment = dict(benchmark_environment, records=len(mst_benchmark_results),
    scenario_sizes=[16, 32, 64, 128], scenarios=["sparse", "dense", "forest"],
    measured_at_utc=datetime.now(timezone.utc).isoformat(),
    timestamp_scope="after MST measurements completed", environment_status="verified_local_run")
Path("mst_benchmark_environment.json").write_text(json.dumps(mst_benchmark_environment, indent=2))
print(pd.DataFrame(mst_benchmark_results).to_string(index=False))
mst_benchmark_chart = alt.Chart(pd.DataFrame(mst_benchmark_results)).mark_line(point=True).encode(
    x=alt.X("n:Q", title="Jumlah ruang sintetis"), y=alt.Y("median_seconds:Q", title="Median detik"),
    color="algorithm:N", column="scenario:N", tooltip=["algorithm", "scenario", "n", "edges", "median_seconds", "peak_bytes"])
try:
    from IPython.display import display
except ImportError:
    print("Grafik tersimpan sebagai HTML pada output Run all lokal.")
else:
    display(mst_benchmark_chart)
''','uas-mst-bench')])
for c in n['cells']:
    if c['cell_type']=='code':
        ast.parse(''.join(c['source']))
path.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
print('MST section added; prior source sections preserved.')
