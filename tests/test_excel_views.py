from copy import deepcopy
from pathlib import Path
import pandas as pd
from campus.data import load_workbook, build_search_indexes
from campus.feb_views import available_weeks, room_inputs, scheduling_inputs
from campus.models import REGULAR_SLOTS, VALUE

ROOT=Path(__file__).resolve().parents[1]


def dataset(): return load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')


def test_rooms_use_excel_capacity_and_unique_occupied_slots():
    data=dataset()
    week=available_weeks(data)[0]
    rooms,_=room_inputs(data,week)
    capacity=data['clean']['ruang'].set_index('ruang')['kapasitas_asumsi'].to_dict()
    assert all(r.capacity==capacity[r.room_id] for r in rooms)
    assert next(r for r in rooms if r.room_id=='F705').capacity==85
    before={r.room_id:r.used_slots for r in rooms}
    # Every shared class/session is repeated; occupied slot counts must not grow.
    data['clean']['jadwal_uts']=pd.concat([data['clean']['jadwal_uts']]*3,ignore_index=True)
    repeated,_=room_inputs(data,week)
    assert {r.room_id:r.used_slots for r in repeated}==before
    assert all(0<=r.used_slots<=15 for r in repeated)


def test_occupancy_keeps_weeks_separate_and_does_not_count_weekends():
    data=dataset()
    first=data['clean']['jadwal_uts'].iloc[[0]].copy()
    first['tanggal']=pd.Timestamp('2026-10-05')
    first['ruang']='F701'; first['mode_ujian']='Onsite'
    first['mulai_menit']=435;first['selesai_menit']=525
    next_week=first.copy();next_week['tanggal']=pd.Timestamp('2026-10-12')
    saturday=first.copy();saturday['tanggal']=pd.Timestamp('2026-10-10')
    online=first.copy();online['mode_ujian']='Online';online['ruang']='F702'
    data['clean']['jadwal_uts']=pd.concat([first,next_week,saturday,online],ignore_index=True)
    for week in [(2026,41),(2026,42)]:
        rooms,_=room_inputs(data,week)
        assert next(r for r in rooms if r.room_id=='F701').used_slots==1
        assert next(r for r in rooms if r.room_id=='F702').used_slots==0


def test_dp_rows_preserve_excel_fields_and_classify_all_exams_correctly():
    data=dataset()
    by_id=dict(data['ingredients']['kelas'])
    candidates,excluded=scheduling_inputs(data)
    assert len(candidates)==196 and len(excluded)==47
    assert len(candidates)+len(excluded)==243
    for r in candidates:
        original=by_id[r.request_id]
        assert (r.title,r.room_id,r.day,r.start,r.end,r.participants)==(original['name'],original['room_id'],original['day'],original['start'],original['end'],original['participants'])
        assert r.activity_type=='Examination' and r.value==VALUE['Examination']
        assert not original['needs_review']
    all_valid,_=scheduling_inputs(data,include_review=True)
    assert len(all_valid)==207
    assert {r.request_id for r in candidates}<={r.request_id for r in all_valid}


def test_excel_prefix_index_matches_source_names_and_keeps_notes():
    data=dataset(); indexes=build_search_indexes(data['ingredients'])
    expected={e.entry_id for e in data['ingredients']['nama'] if e.name.strip().casefold().startswith('akun')}
    assert set(indexes['names'].autocomplete('AKUN'))==expected
    flagged=next(detail for _,detail in data['ingredients']['kelas'] if detail['needs_review'])
    assert indexes['classes'].get(flagged['class_code'])['review_notes']==flagged['review_notes']


def test_app_has_no_imports_or_presets_from_example_datasets():
    source=(ROOT/'app.py').read_text()
    for old in ['campus.demo','presentation_examples','verify_dp_random_cases','generate_requests','DEMO_DAY','target 19','Ubah kandidat notebook']:
        assert old not in source
