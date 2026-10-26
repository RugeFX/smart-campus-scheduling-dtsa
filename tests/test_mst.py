"""MST correctness certificates, source parity, and Excel/UI boundaries."""
import ast
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path
from random import Random

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from campus import mst, mst_experiments
from campus.data import load_workbook
from campus.mst_ui import graph_from_editor, edge_frame
from campus.verification import TEST_RUNNERS

ROOT = Path(__file__).resolve().parents[1]


def test_mst_definitions_match_colab_verbatim():
    definitions = {node.name:node for c in json.loads((ROOT/'references/UTS_Group2_Smart_Campus.ipynb').read_text())['cells'] if c['cell_type']=='code'
                   for node in ast.parse(''.join(c['source'])).body if isinstance(node,(ast.ClassDef,ast.FunctionDef))}
    for module in (mst, mst_experiments):
        for name, value in vars(module).items():
            if getattr(value,'__module__',None)==module.__name__:
                assert ast.dump(ast.parse(inspect.getsource(value)).body[0]) == ast.dump(definitions[name])
    source=inspect.getsource(mst)
    assert 'import heapq' not in source and 'sorted(' not in source


@pytest.mark.parametrize('number',range(29,34))
def test_registered_mst_cases(number):
    TEST_RUNNERS[f'T{number}']()


def test_heap_random_interleaved_operations_and_uf_compression():
    rng=Random(9); heap=mst.PrimMinHeap(); oracle=[]
    for _ in range(800):
        if oracle and rng.random()<.4:
            expected=min(oracle);oracle.remove(expected);assert heap.pop()==expected
        else:
            value=(rng.randint(-10,10),'R',str(rng.randint(0,20)))
            heap.push(value);oracle.append(value)
    assert [heap.pop() for _ in range(len(oracle))]==sorted(oracle)
    with pytest.raises(IndexError):heap.pop()
    uf=mst.UnionFind('ABCDE')
    # Force a valid chain to inspect compression independently of union order.
    uf.parent.update(A='B',B='C',C='D',D='E')
    assert uf.find('A')=='E'
    assert all(uf.parent[n]=='E' for n in 'ABCDE')
    ranked=mst.UnionFind('ABCD')
    ranked.union('A','B');ranked.union('C','D');ranked.union('B','D')
    assert max(ranked.rank.values())==2


def test_excel_nodes_and_editable_assumptions_keep_workbook_unchanged():
    workbook=ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx'
    before=workbook.read_bytes();data=load_workbook(workbook)
    nodes,edges=mst.mst_room_scenario(data['clean']['ruang'])
    assert set(nodes)==set(data['clean']['ruang']['ruang']) and len(nodes)==16
    assert len(edges)==22 and {e.weight for e in edges}=={1.,3.}
    for fn in (mst.kruskal_mst,mst.prim_mst):
        result=fn(nodes,edges)
        assert result.total_cost==17 and len(result.edges)==15
    edited=edge_frame(edges);edited.loc[0,'Biaya simulasi']=50
    n,e=graph_from_editor(nodes,edited)
    assert mst.kruskal_mst(n,e).total_cost>17  # Both UI and algorithms use edits.
    assert workbook.read_bytes()==before
    # Different workbook room codes, no fallback to the FEB fixture.
    custom=pd.DataFrame([{'ruang':'Z1','gedung':'Z','lantai':1},{'ruang':'Y1','gedung':'Y','lantai':1}])
    n,e=mst.mst_room_scenario(custom)
    assert set(n)=={'Z1','Y1'} and not e and len(mst.prim_mst(n,e).components)==2
    with pytest.raises(ValueError,match='negatif'):
        graph_from_editor(nodes,pd.DataFrame([['F701','F702',-1]],columns=edited.columns))
    with pytest.raises(ValueError,match='Excel aktif'):
        graph_from_editor(nodes,pd.DataFrame([['Unknown','F702',1]],columns=edited.columns))


def test_certificate_rejects_wrong_cost_cycle_and_component_claims():
    nodes=('A','B','C');edges=[('A','B',1),('B','C',2),('A','C',3)]
    result=mst.kruskal_mst(nodes,edges)
    assert not mst.validate_mst(nodes,edges,replace(result,total_cost=0))['valid']
    assert not mst.validate_mst(nodes,edges,replace(result,edges=tuple(mst.MSTEdge(*e) for e in edges),total_cost=6))['valid']
    assert not mst.validate_mst(nodes,edges,replace(result,components=(('A','B'),('C',))))['valid']
    assert not mst.validate_mst(nodes,edges,replace(result,edges=(mst.MSTEdge('A','B',99),)))['valid']
    for fn in (mst.kruskal_mst,mst.prim_mst):
        with pytest.raises(ValueError):fn(nodes,edges,trace_limit=-1)


def test_mst_benchmark_raw_runs_provenance_and_both_methods():
    frame=pd.read_csv(ROOT/'data/mst_benchmarks.csv')
    assert len(frame)==24 and set(frame.scenario)=={'sparse','dense','forest'}
    assert set(frame.n)=={16,32,64,128} and set(frame.runs)=={5} and set(frame.warmups)=={1}
    for _,row in frame.iterrows():
        runs=ast.literal_eval(row.run_seconds)
        assert len(runs)==5 and abs(sorted(runs)[2]-row.median_seconds)<1e-12
    for _,group in frame.groupby(['n','scenario']):
        assert len(group)==2 and group.cost.nunique()==1 and group.edges.nunique()==1
    provenance=json.loads((ROOT/'references/benchmark-provenance.json').read_text())
    assert provenance['mst_records']==len(frame)
    assert provenance['mst_sha256']==hashlib.sha256((ROOT/'data/mst_benchmarks.csv').read_bytes()).hexdigest()


def test_mst_ui_result_method_change_edit_stale_invalid_forest_and_reset():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_Koneksi ruang').click().run()
    assert not at.exception and 'biaya simulasi: 17' in at.success[0].value
    assert any('asumsi simulasi' in item.value for item in at.info)
    at.selectbox(key='mst_method').set_value('Prim').run()
    assert not at.exception
    # data_editor uses the real widget protobuf state, including its edit delta.
    editor_key=f'mst_editor_{at.session_state["mst_source"][0]}_{at.session_state["mst_revision"]}'
    at.session_state[editor_key]={'edited_rows':{0:{'Biaya simulasi':50}},'added_rows':[],'deleted_rows':[]}
    at.run()
    assert not at.exception and any('Koneksi berubah' in i.value for i in at.info) and not at.success
    at.button(key='mst_run').click().run()
    assert not at.exception and 'biaya simulasi: 17' not in at.success[0].value
    at.session_state[editor_key]={'edited_rows':{0:{'Ke ruang':'F701'}},'added_rows':[],'deleted_rows':[]}
    at.run();assert not at.exception and any('dirinya sendiri' in i.value for i in at.error)
    at.session_state[editor_key]={'edited_rows':{},'added_rows':[],'deleted_rows':list(range(22))}
    at.run();at.button(key='mst_run').click().run()
    assert not at.exception and any('16 jaringan terpisah' in i.value for i in at.warning)
    at.button(key='mst_reset').click().run()
    assert not at.exception and 'biaya simulasi: 17' in at.success[0].value


def test_scenario_persists_navigation_and_resets_for_uploaded_workbook():
    from io import BytesIO
    import zipfile
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_Koneksi ruang').click().run()
    key=f'mst_editor_{at.session_state["mst_source"][0]}_0'
    at.session_state[key]={'edited_rows':{0:{'Biaya simulasi':50}},'added_rows':[],'deleted_rows':[]}
    at.run();at.button(key='mst_run').click().run()
    edited_cost=at.session_state['mst_report'][1].total_cost
    at.button(key='nav_Ringkasan').click().run()
    at.button(key='nav_Koneksi ruang').click().run()
    assert not at.exception and at.session_state['mst_report'][1].total_cost==edited_cost
    assert at.session_state['mst_draft_snapshot'].iloc[0]['Biaya simulasi']==50
    assert not any('Koneksi berubah' in i.value for i in at.info)
    blob=BytesIO((ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx').read_bytes())
    with zipfile.ZipFile(blob,'a') as book:book.comment=b'mst-new-source'
    at.session_state['workbook_bytes']=blob.getvalue()
    at.session_state['workbook_name']='unggahan_baru.xlsx'
    at.run()
    assert not at.exception and at.session_state['mst_report'][1].total_cost==17
    assert at.session_state['mst_draft_snapshot'].iloc[0]['Biaya simulasi']==1


def test_mst_page_handles_duplicate_or_empty_room_data_without_exception():
    setup="""from campus.data import load_workbook
from campus.mst_ui import render_mst
import pandas as pd
data=load_workbook('data/dataset_jadwal_uts_feb_uph.xlsx')
"""
    duplicate="data['clean']['ruang']=pd.concat([data['clean']['ruang'],data['clean']['ruang'].iloc[:1]])\nrender_mst(data)"
    at=AppTest.from_string(setup+duplicate).run()
    assert not at.exception and any('Kode ruang berulang' in i.value for i in at.error)
    at=AppTest.from_string(setup+"data['clean']['ruang']=data['clean']['ruang'].iloc[:0]\nrender_mst(data)").run()
    assert not at.exception and any('Belum ada ruang' in i.value for i in at.warning)
