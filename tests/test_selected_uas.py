import ast
import hashlib
import inspect
import json
from pathlib import Path
from dataclasses import replace
from streamlit.testing.v1 import AppTest
from campus import greedy, sorting, uas_examples
from campus.data import load_workbook, build_search_indexes
from campus.heap import MinHeapPriorityQueue, MaxHeap, heap_sort
from campus.hash_table import HashTableLinearProbing
from campus.heap_tests import heap_test_request
from campus.excel_benchmark import measure_excel

ROOT=Path(__file__).resolve().parents[1]


def test_additional_definitions_match_authoritative_notebook():
    nodes={node.name:node for cell in json.loads((ROOT/'references/UTS_Group2_Smart_Campus.ipynb').read_text())['cells'] if cell['cell_type']=='code'
           for node in ast.parse(''.join(cell['source'])).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    for module,names in [(greedy,['select_activities','brute_force_activity_count','verify_greedy_random_cases','greedy_weight_counterexample']),
                         (sorting,['manual_merge_sort']),(uas_examples,['simulate_priority_dispatch','avl_rotation_examples'])]:
        for name in names:
            assert ast.dump(ast.parse(inspect.getsource(getattr(module,name))).body[0])==ast.dump(nodes[name])


def test_priority_override_fifo_and_source_payload_unchanged():
    first=replace(heap_test_request('first'),start=900,end=960)
    second=replace(heap_test_request('second'),start=480,end=540)
    queue=MinHeapPriorityQueue(trace=True);queue.build([first,second])
    assert queue.peek()==first  # FIFO, independent of appointment start time.
    queue.change_priority('first',4)
    assert queue.peek()==second and first.priority==1
    queue.apply_aging(90,30)
    assert queue.peek()==first and queue.validate()
    assert queue.trace and first.start==900


def test_tombstone_does_not_duplicate_existing_key_or_hide_none():
    table=HashTableLinearProbing(bucket_count=8)
    keys=[]
    for i in range(10000):
        key=f'collision-{i}'
        if table._hash(key)==0:keys.append(key)
        if len(keys)==3:break
    for key in keys:table.put(key,None)
    table.delete(keys[0]);table.put(keys[2],'updated')
    assert len(table)==2 and table.contains(keys[1]) and table.get(keys[2])=='updated'
    table.put('new','value');assert table.validate()


def test_excel_hash_strategies_have_identical_contents():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    chain=build_search_indexes(data['ingredients']);linear=build_search_indexes(data['ingredients'],'linear')
    for name in ('courses','classes'):
        assert len(chain[name])==len(linear[name])
        for key,value in chain[name].items():assert linear[name].get(key)==value
    for algorithm,expected in [('Hash Table',3),('Greedy',3)]:
        rows=measure_excel(data,algorithm,limit=10,repeat=1)
        assert len(rows)==expected and all(row['SHA256 Excel']==data['sha256'] for row in rows)


def test_selected_benchmarks_are_real_repeated_runs_with_bound_provenance():
    import pandas as pd
    frame=pd.read_csv(ROOT/'data/uas_selected_benchmarks.csv')
    assert len(frame)==43 and set(frame['module'])=={'PQ','Hash','DP','Greedy'}
    assert set(frame['runs'])=={5} and set(frame['warmup_runs'])=={1}
    for _,row in frame.iterrows():
        times=ast.literal_eval(row['run_seconds'])
        assert len(times)==5 and all(time>=0 for time in times)
        assert abs(sorted(times)[2]-row['median_seconds'])<1e-12
    provenance=json.loads((ROOT/'references/benchmark-provenance.json').read_text())
    assert provenance['additional_sha256']==hashlib.sha256((ROOT/'data/uas_selected_benchmarks.csv').read_bytes()).hexdigest()


def test_new_ui_controls_preserve_operational_excel_source():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_Cari jadwal').click().run()
    at.selectbox(key='search_hash_strategy').set_value('Linear probing').run()
    at.text_input(key='search_query').set_value('akun').run()
    assert not at.exception
    at.button(key='trie_delete_preview').click().run()
    assert not at.exception and any('salinan' in item.value for item in at.success)
    at.button(key='nav_Pilih jadwal').click().run()
    at.radio(key='schedule_goal').set_value('Jumlah kelas').run()
    assert not at.exception
    result=next(df.value for df in at.dataframe if 'Hasil' in df.value.columns)
    assert all('Greedy' in value for value in result['Hasil'])
    assert not any(str(code).startswith('J') for code in result['Kode kelas'])
    at.button(key='nav_Ruangan').click().run()
    at.selectbox(key='avl_rotation_kind').set_value('LR').run()
    assert not at.exception
