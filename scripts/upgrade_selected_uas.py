"""Apply reviewed source parts to the canonical notebook, then use sync_notebook."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/'scripts/uas_sources'
TARGET=ROOT/'references/UTS_Group2_Smart_Campus.ipynb'
notebook=json.loads(TARGET.read_text())


def definitions(path):
    source=path.read_text();lines=source.splitlines(keepends=True)
    return {n.name:''.join(lines[n.lineno-1:n.end_lineno]).rstrip()
            for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}


parts=[('sorting_source.py',3),('heap_source.py',21),('hash_source.py',23),
       ('trie_source.py',28),('avl_source.py',32),('greedy_source.py',34),
       ('examples_source.py',40),('tests_source.py',40)]
all_defs={};placements={}
for filename,index in parts:
    for name,source in definitions(PARTS/filename).items():
        all_defs[name]=source;placements[name]=index
existing=set()
for index,cell in enumerate(notebook['cells']):
    if cell['cell_type']!='code':continue
    source=''.join(cell['source']);lines=source.splitlines(keepends=True)
    edits=[]
    for node in ast.parse(source).body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
            existing.add(node.name)
            if node.name in all_defs:
                edits.append((node.lineno-1,node.end_lineno,all_defs[node.name]+'\n'))
    for start,end,text in reversed(edits):lines[start:end]=[text]
    cell['source']=''.join(lines).splitlines(keepends=True)
for index in set(placements.values()):
    added=[source for name,source in all_defs.items() if name not in existing and placements[name]==index]
    cell=notebook['cells'][index]
    cell['source']=('\n\n'.join(added)+'\n\n'+''.join(cell['source'])).splitlines(keepends=True)

# Preserve the PR's DP interfaces. Only replace built-in sorting in core DP paths.
cell=notebook['cells'][34]
cell['source']=''.join(cell['source']).replace('ordered = sorted(candidates, key=', 'ordered = manual_merge_sort(candidates, key=').splitlines(keepends=True)

cell=notebook['cells'][26];s=''.join(cell['source'])
s=s.replace('["U1", "U2", "P", "K1", "K2", "E"]','["U2", "U1", "P", "K2", "K1", "E"]')
s=s.replace('assert queue.peek() is batch[2] and len(queue) == 3','assert queue.peek() is batch[0] and len(queue) == 3')
s=s.replace('["Jam-lebih-awal", "Masuk-1", "Masuk-2"]','["Masuk-1", "Masuk-2", "Jam-lebih-awal"]')
s=s.replace('["Baru", "Event-lama", "Ujian-baru"]','["Event-lama", "Ujian-baru", "Baru"]')
s=s.replace('(item[0].priority, item[0].start, item[1])','(item[0].priority, item[1])')
s=s.replace('(item[1].priority, item[1].start, item[0])','(item[1].priority, item[0])')
cell['source']=s.splitlines(keepends=True)
cell=notebook['cells'][40];s=''.join(cell['source']);lines=s.splitlines(keepends=True)
for node in reversed(ast.parse(s).body):
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('TEST_IDS','TEST_RUNNERS') for t in node.targets):
        name=node.targets[0].id
        replacement='TEST_IDS = [f"T{i:02d}" for i in range(1, 29)]' if name=='TEST_IDS' else 'TEST_RUNNERS = {'+', '.join(f'"T{i:02d}": test_t{i:02d}' for i in range(1,29))+'}'
        lines[node.lineno-1:node.end_lineno]=[replacement+'\n']
cell['source']=''.join(lines).splitlines(keepends=True)
cell=notebook['cells'][42];s=''.join(cell['source'])
s=s.replace('(request.priority, request.start, i)','(request.priority, i)').replace('(request.priority, request.start, n + i)','(request.priority, n + i)')
s=s.replace('    warm_state = setup()\n    action(warm_state)  # Warm-up terpisah dari run yang diukur.\n    del warm_state\n','')
s=s.replace('    durations, metrics = [], []\n','    warm_state = setup()\n    action(warm_state)  # Warm-up terpisah dari run yang diukur.\n    del warm_state\n    durations, metrics = [], []\n')
cell['source']=s.splitlines(keepends=True)
for cell in notebook['cells']:
    if cell['cell_type']=='code':
        cell['outputs']=[];cell['execution_count']=None
    else:
        s=''.join(cell.get('source',[])).replace('(prioritas efektif, jam mulai, counter masuk)','(prioritas efektif, counter FIFO)').replace('FIFO berlaku saat prioritas dan jam sama','FIFO berlaku pada prioritas yang sama')
        cell['source']=s.splitlines(keepends=True)
notebook['cells']=[c for c in notebook['cells'] if not (c['cell_type']=='markdown' and ''.join(c.get('source',[])).startswith('## Penyempurnaan UAS terpilih'))]
notebook['cells'].append({'cell_type':'markdown','metadata':{},'source':[
    '## Penyempurnaan UAS terpilih — 26 Oktober 2026\n',
    'DP memoization dan rekursi naif mempertahankan implementasi PR #17. MinHeap/PQ sekarang FIFO per prioritas dan menyediakan override prioritas lokal. MaxHeap dan heap sort manual tersedia. Hash linear probing memakai tombstone; Trie mendukung delete; AVL mencatat jenis/pivot serta cuplikan before/after.\n',
    '\n### Greedy: tujuan dan bukti kebenaran\n',
    'Activity selection memaksimalkan **jumlah** kegiatan dalam satu ruang/hari. Ambil kegiatan g yang selesai paling awal. Pada solusi optimum O, kegiatan pertama o tidak selesai sebelum g. Ganti o dengan g: semua kegiatan setelah o tetap kompatibel, dan jumlah pilihan tidak berubah. Ulangi pada kegiatan yang mulai setelah g selesai. Induksi memberi solusi jumlah maksimum. Argumen ini tidak menjamin total bobot maksimum.\n',
    'Fixture A 08:00–09:00 nilai 2, B 09:00–10:00 nilai 2, C 08:00–10:00 nilai 10: greedy memilih A+B (jumlah 2, nilai 4), DP memilih C (nilai 10). Ini batas masalah berbeda, bukan kegagalan klaim optimalitas kardinalitas.\n',
    '\n### Biaya operasi dan batas\n',
    'Greedy memakai merge sort manual O(n log n) lalu scan O(n), ruang O(n). Heap sort O(n log n), build heap O(n). Hash linear probing ekspektasi O(L + probe), dapat O(n) probe ketika padat; tombstone menjaga rantai pencarian. Trie delete O(L) ditambah biaya Hash anak; autocomplete memakai Hash untuk deduplikasi ID. AVL insert/delete/search O(log n); trace lokal dibatasi kedalaman dan jumlah event.\n',
    'T20–T28 adalah fixture pengujian terkontrol; seluruh input jadwal aplikasi tetap berasal dari Excel FEB. Simulasi aging membandingkan workload terbatas, bukan klaim bebas starvation pada semua kemungkinan beban. Instrumen trace tidak menjadi sumber data jadwal.\n']})
TARGET.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n')
print('Updated notebook definitions; run sync_notebook.py and tests before publishing.')
