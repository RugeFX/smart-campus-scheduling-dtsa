from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from campus.data import load_workbook
from campus.feb_views import available_weeks
from campus.workspace import AllocationWorkspace
from campus.excel_benchmark import measure_excel

ROOT=Path(__file__).resolve().parents[1]


def dataset(): return load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
def button(at,label): return next(b for b in at.button if b.label==label)


def test_excel_allocation_and_cancel_keep_provenance_and_indexes():
    data=dataset(); before=data['display'].copy(deep=True)
    workspace=AllocationWorkspace(data,available_weeks(data)[0])
    candidates,_=workspace.candidates()
    report=workspace.allocate([r.request_id for r in candidates])
    assert (len(report['bookings']),len(report['rejected']))==(189,7)
    assert workspace.reserved_class_ids<={r.request_id for r in candidates}
    assert workspace.validate()
    assert data['display'].equals(before)
    target=workspace.bookings[0]
    with pytest.raises(ValueError): workspace.allocate([target.request_id])
    workspace.cancel(target.request_id)
    assert len(workspace.bookings)==188 and target.request_id not in workspace.reserved_class_ids
    assert workspace.validate()
    assert data['display'].equals(before)


@pytest.mark.parametrize('algorithm',['Hash Table','Trie','Heap/PQ','AVL','DP'])
def test_live_measurement_uses_active_excel(algorithm):
    data=dataset()
    result=measure_excel(data,algorithm,limit=15,repeat=1)
    assert len(result)==2
    assert {r['SHA256 Excel'] for r in result}=={data['sha256']}
    assert {r['Berkas'] for r in result}=={data['source_name']}
    assert all(0<r['n']<=15 and r['Median (ms)']>=0 for r in result)


def test_full_ui_allocation_cancel_and_room_state():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_'+'Simulasi alokasi').click().run()
    assert not at.exception
    button(at,'Jalankan alokasi').click().run()
    assert not at.exception
    workspace=next(iter(at.session_state['allocation_workspaces'].values()))
    assert len(workspace.bookings)==189
    button(at,'Batalkan alokasi terpilih').click().run()
    assert len(workspace.bookings)==188 and not at.exception
    at.button(key='nav_'+'Ruangan').click().run()
    at.radio(key='room_view').set_value('Hasil simulasi alokasi').run()
    assert not at.exception
    expected={r.room_id:r.used_slots for r in workspace.registry[1].inorder()}
    actual=at.dataframe[-1].value
    assert actual.set_index('Ruang')['Slot terpakai'].to_dict()==expected
    at.button(key='nav_'+'Simulasi alokasi').click().run()
    assert len(next(iter(at.session_state['allocation_workspaces'].values())).bookings)==188
    button(at,'Mulai ulang simulasi minggu ini').click().run()
    assert len(next(iter(at.session_state['allocation_workspaces'].values())).bookings)==0
    assert not at.exception


def test_ui_measurement_and_dp_allocation():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_'+'Eksperimen').click().run()
    at.selectbox(key='benchmark_repeat').set_value(1).run()
    button(at,'Jalankan percobaan').click().run()
    assert len(at.session_state['excel_benchmark_result'])==2 and not at.exception
    at.button(key='nav_'+'Pilih jadwal').click().run()
    button(at,'Alokasikan kandidat ruang/hari ini').click().run()
    assert sum(len(w.bookings) for w in at.session_state['allocation_workspaces'].values())>0
    assert not at.exception


def test_explicit_excel_pair_merge_and_cancel_release_both_source_classes():
    data=dataset(); workspace=AllocationWorkspace(data,available_weeks(data)[0])
    codes=['2503/ARK','2506/CRK']
    prepared,origins=workspace.prepare(codes,[('ACC93106','ACC13102')])
    assert len(prepared)==1 and set(origins[prepared[0].request_id])==set(codes)
    assert prepared[0].participants==sum(dict(data['ingredients']['kelas'])[code]['participants'] for code in codes)
    report=workspace.allocate(codes,confirmed_pairs=[('ACC93106','ACC13102')])
    assert len(report['bookings'])==1 and workspace.reserved_class_ids==set(codes)
    workspace.cancel(report['bookings'][0].request_id)
    assert not workspace.reserved_class_ids and workspace.validate()
    with pytest.raises(ValueError): workspace.prepare(codes,[('INVALID','MADEUP')])


def test_queue_handoff_selects_processed_excel_class():
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_'+'Antrean kegiatan').click().run()
    at.selectbox(key='queue_class').set_value('2871/ARK').run()
    button(at,'Masukkan ke antrean').click().run()
    button(at,'Proses permintaan berikutnya').click().run()
    expected=at.session_state['queue_processed'][0].request_id
    button(at,'Lanjutkan ke simulasi alokasi').click().run()
    assert at.session_state['page']=='Simulasi alokasi'
    assert at.radio(key='allocation_scope').value=='Dari antrean yang sudah diproses'
    button(at,'Jalankan alokasi').click().run()
    assert expected in next(iter(at.session_state['allocation_workspaces'].values())).reserved_class_ids
    assert not at.exception


def test_ui_pair_confirmation_and_workbook_replacement_clear_old_results():
    from io import BytesIO
    import zipfile
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_'+'Simulasi alokasi').click().run()
    at.radio(key='allocation_scope').set_value('Pilih kelas Excel').run()
    at.multiselect(key='allocation_selected').set_value(['2503/ARK','2506/CRK']).run()
    at.multiselect(key='allocation_pairs').set_value([('ACC93106','ACC13102')]).run()
    button(at,'Jalankan alokasi').click().run()
    workspace=next(iter(at.session_state['allocation_workspaces'].values()))
    assert len(workspace.bookings)==1 and workspace.reserved_class_ids=={'2503/ARK','2506/CRK'}
    assert not at.exception
    # A distinct valid XLSX with identical table values still represents a new source.
    blob=BytesIO((ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx').read_bytes())
    with zipfile.ZipFile(blob,'a') as book: book.comment=b'new-workbook-session'
    at.session_state['workbook_bytes']=blob.getvalue()
    at.session_state['workbook_name']='workbook_pengganti.xlsx'
    at.session_state['excel_benchmark_result']=[{'stale':True}]
    at.run()
    assert all(not w.bookings for w in at.session_state['allocation_workspaces'].values())
    assert 'excel_benchmark_result' not in at.session_state
    assert not at.exception
