from pathlib import Path
from dataclasses import replace
from campus.data import load_workbook
from campus.feb_views import queue_inputs
from campus.heap import MinHeapPriorityQueue

ROOT=Path(__file__).resolve().parents[1]


def test_all_excel_rows_ordered_per_day_with_source_fifo():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    requests,excluded=queue_inputs(data)
    assert len(requests)==243 and excluded.empty
    assert {r.request_id for r in requests}==set(data['display']['Kode kelas'])
    assert {r.activity_type for r in requests}=={'Examination'}
    online=set(data['display'].loc[data['display']['Mode'].eq('Online'),'Kode kelas'])
    assert online and online<={r.request_id for r in requests}
    for day in {r.day for r in requests}:
        batch=[r for r in requests if r.day==day]
        queue=MinHeapPriorityQueue()
        queue.build(batch)
        expected=[r for i,r in sorted(enumerate(batch),key=lambda x:(x[1].start,x[0]))]
        queue.apply_aging(100,30)
        for request in expected:
            assert queue.peek() is request
            assert queue.pop() is request
            assert queue.validate()


def test_invalid_excel_row_remains_traceable_but_not_enqueued():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    key,detail=data['ingredients']['kelas'][0]
    detail['end']=detail['start']
    requests,excluded=queue_inputs(data)
    assert len(requests)==242 and key not in {r.request_id for r in requests}
    assert excluded.iloc[0]['Baris Excel']==detail['source']['excel_row']
    assert len(data['display'])==243
