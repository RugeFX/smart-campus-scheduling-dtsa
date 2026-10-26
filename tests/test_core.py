import ast
from dataclasses import fields
import inspect
import json
from pathlib import Path
import pytest
from campus import heap, trie, avl, dp, hash_table, service, data_core, demo, integration_demo, experiments
from campus.models import Room, ScheduleRequest
from campus.demo import requests, rooms
from campus.data import load_workbook, build_search_indexes
from campus.notebook_tests import run_hash_tests
from campus.verification import run_test_plan, TEST_RUNNERS, RUN_TESTS
from campus.capabilities import ready, STATUS
from campus.adapters import RoomView

ROOT=Path(__file__).resolve().parents[1]


def notebook_definitions():
    result={}
    for cell in json.loads((ROOT/'references/UTS_Group2_Smart_Campus.ipynb').read_text())['cells']:
        if cell['cell_type']=='code':
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node,(ast.ClassDef,ast.FunctionDef)): result[node.name]=node
    return result


@pytest.mark.parametrize('module,names',[
    (heap,['MinHeapPriorityQueue','MaxHeap','heap_sort']),
    (trie,['TrieNode','Trie','bilingual_autocomplete']),
    (avl,['AVLNode','AVLTree']),
    (dp,['optimize_schedule','optimize_schedule_memo','naive_recursive','chain_requests','compare_dp_methods','find_previous_compatible','validate_candidates','explain_dp_table','verify_dp_random_cases']),
    (hash_table,['HashTableChaining','HashTableLinearProbing','polynomial_hash']),
    (demo,['build_indexes']),
    (service,['MergedClassRecord','merge_equivalent_classes','update_room_usage','schedule_across_rooms','validate_room_registry','stage_room_updates','commit_room_registry','make_room_registry','touched_regular_slots','simulate_feb_allocation']),
    (integration_demo,['demo_integration']),
    (experiments,['measure_operation','measure_peak_memory','run_benchmarks']),
    (data_core,['rapikan_dan_validasi','siapkan_bahan_pencarian_feb']),
])
def test_algorithm_definitions_match_colab(module,names):
    original=notebook_definitions()
    for name in names:
        local=ast.parse(inspect.getsource(getattr(module,name))).body[0]
        assert ast.dump(local,include_attributes=False)==ast.dump(original[name],include_attributes=False),name


def test_heap_implements_colab_contract():
    queue=heap.MinHeapPriorityQueue()
    queue.build(requests)
    assert queue.validate()
    assert [queue.pop().request_id for _ in requests]==['J3','J5','J2','J6','J1','J4']
    assert ready('MinHeapPriorityQueue.push','MinHeapPriorityQueue.pop','MinHeapPriorityQueue.apply_aging')
    from campus.heap_tests import run_heap_tests
    run_heap_tests()


def test_avl_read_operations_and_delete():
    view=RoomView(rooms)
    assert view.validate()
    assert view.capacity.ceiling_capacity(35).room_id=='F705'
    assert view.capacity.ceiling_capacity(101) is None
    assert [r.room_id for r in view.usage.top_k_utilization(3)]==['F805','F807','F802']
    assert view.capacity.delete((40,'F705'))
    assert 'F705' not in {r.room_id for r in view.capacity.inorder()}
    assert view.capacity.validate()
    assert not view.capacity.delete((40,'F705'))


def test_integrations_are_ready_and_tested():
    assert ready('merge_equivalent_classes','update_room_usage','schedule_across_rooms','demo_integration','AVLTree.delete')
    assert integration_demo.demo_integration()['total_value']==19
    from campus.verification import test_avl_delete_and_atomic_updates, test_integration_boundaries
    test_avl_delete_and_atomic_updates()
    test_integration_boundaries()


def test_hash_notebook_tests(): run_hash_tests()


def test_updated_trie_from_colab():
    t=trie.Trie(); t.insert(' Alpha ','a'); t.insert('Alphabet','a'); t.insert('ALPHA','b')
    assert set(t.autocomplete(' al '))=={'a','b'}
    assert set(t.search('alpha'))=={'a','b'}
    assert t.search('alp')==[] and t.autocomplete(None)==[]
    assert ready('Trie.insert','Trie.autocomplete')


def test_dp_and_source_contract():
    assert dp.optimize_schedule(requests)==(19,['J3','J4','J5'])
    assert dp.verify_dp_random_cases().startswith('100 kasus')
    assert 'flexible_time' not in {f.name for f in fields(ScheduleRequest)}


def test_dp_memoization_naive_and_tabulation_agree():
    from random import Random
    from campus.generators import generate_requests
    from campus.dp import optimize_schedule_memo,naive_recursive,chain_requests,compare_dp_methods
    rng=Random(7)
    for _ in range(10):
        sample=generate_requests(rng.randrange(0,16),seed=rng.randrange(1_000_000))
        expected=dp.optimize_schedule(sample)
        value,ids,memo_calls=optimize_schedule_memo(sample)
        naive_value,naive_calls=naive_recursive(sample)
        assert (value,ids)==expected,'Memoisasi harus identik dengan tabulasi.'
        assert naive_value==value,'Nilai optimum naif harus sama.'
        assert memo_calls<=2*len(sample)+1<=naive_calls or not sample
    chain=chain_requests(11)
    assert optimize_schedule_memo(chain)[:2]==dp.optimize_schedule(chain)
    assert naive_recursive(chain)==(5*11,2**12-1),'Rantai kompatibel = 2^(n+1)-1 pemanggilan naif.'
    assert optimize_schedule_memo([])==(0,[],0) and naive_recursive([])==(0,0)
    rows=compare_dp_methods()
    assert len(rows)==9 and all(row['naif_pemanggilan']>=row['memo_pemanggilan'] for row in rows)


def test_excel_search_uses_bridge_while_saved_notebook_flag_is_preserved():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    assert len(data['display'])==243 and len(data['ingredients']['mata_kuliah'])==122
    assert len(data['ingredients']['nama'])==137
    indexes=build_search_indexes(data['ingredients'])
    assert len(indexes['classes'])==243 and len(indexes['courses'])==122
    assert indexes['courses'].get('ACC93105')['name']=='Accounting Principles 1 + LAB'
    assert STATUS['flags']['AKTIFKAN_PENCARIAN_FEB'] is True


def test_plan_has_no_invented_registered_tests():
    assert set(TEST_RUNNERS)=={f'T{i:02d}' for i in range(1,29)} and RUN_TESTS is True
    assert len(run_test_plan())==28
    assert [status for _,status,_ in run_test_plan()]==['LULUS']*28


def test_saved_benchmarks_are_verified_against_snapshot():
    import hashlib
    import pandas as pd
    assert STATUS['benchmark_ready']
    assert STATUS['sha256']==hashlib.sha256((ROOT/'references/UTS_Group2_Smart_Campus.ipynb').read_bytes()).hexdigest()
    provenance=json.loads((ROOT/'references/benchmark-provenance.json').read_text())
    assert provenance['notebook_sha256']==STATUS['sha256']
    measured=pd.read_csv(ROOT/'data/colab_benchmarks.csv')
    assert len(measured)==79 and set(measured['runs'])=={5}
