from io import BytesIO
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from campus.data import load_workbook
from campus.feb_views import scheduling_inputs, queue_inputs
from campus.dp import optimize_schedule

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app.py'


def app(): return AppTest.from_file(str(APP),default_timeout=30).run()
def button(at,label): return next(b for b in at.button if b.label==label)


def test_all_pages_render_with_excel():
    at=app()
    assert not at.exception
    for page in ['Cari jadwal','Antrean kegiatan','Simulasi alokasi','Ruangan','Pilih jadwal','Koneksi ruang','Eksperimen','Data & panduan']:
        at.button(key='nav_'+page).click().run()
        assert not at.exception,page


def test_search_uses_real_excel_names_and_capacity():
    at=app(); at.button(key='nav_'+'Cari jadwal').click().run()
    at.checkbox(key='search_include_pairs').set_value(False).run()
    at.selectbox(key='search_mode').set_value('Kode MK lengkap').run()
    at.text_input(key='search_query').set_value('ACC93105').run()
    frame=at.dataframe[0].value
    assert len(frame)==6
    assert 'Accounting Principles 1 + LAB' in set(frame['Mata kuliah'])
    assert 'Cost Accounting' not in set(frame['Mata kuliah'])
    at.selectbox(key='search_mode').set_value('ID ruang lengkap').run()
    at.text_input(key='search_query').set_value('F705').run()
    assert at.dataframe[0].value.iloc[0]['kapasitas_asumsi']==85
    assert all(r.label!='Sumber pencarian' for r in at.radio)
    assert not at.exception


def test_queue_uses_excel_and_preserves_peek_pop_state():
    at=app(); at.button(key='nav_'+'Antrean kegiatan').click().run()
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    candidates,_=queue_inputs(data)
    batch=[r for r in candidates if r.day==at.selectbox(key='queue_day').value]
    assert len(at.selectbox(key='queue_class').options)==len(batch)
    assert not at.warning  # First Excel row is not flagged for review.
    assert button(at,'Masukkan ke antrean').disabled
    assert button(at,'Proses permintaan berikutnya').disabled
    assert button(at,'Terapkan peningkatan prioritas').disabled
    button(at,'Tambahkan semua kelas').click().run()
    queue=at.session_state['queue']
    assert len(queue)==len(batch) and queue.validate()
    expected=[r for i,r in sorted(enumerate(batch),key=lambda x:(x[1].priority,x[0]))]
    assert queue.peek().request_id==expected[0].request_id
    assert button(at,'Tambahkan semua kelas').disabled
    before=queue.comparisons
    at.run()
    assert len(at.session_state['queue'])==len(batch) and at.session_state['queue'].comparisons==before
    at.number_input(key='queue_clock').set_value(90).run()
    button(at,'Terapkan peningkatan prioritas').click().run()
    assert at.session_state['queue'].now==90 and at.session_state['queue'].validate()
    assert [e[1].request_id for e in at.session_state['queue'].ordered_entries()]==[r.request_id for r in expected]
    button(at,'Proses permintaan berikutnya').click().run()
    assert len(at.session_state['queue'])==len(batch)-1
    assert at.session_state['queue_processed'][0].request_id==expected[0].request_id
    assert not at.exception
    at.button(key='nav_'+'Ruangan').click().run()
    assert not button(at,'Kelola alokasi dan pembatalan').disabled and not at.exception
    assert set(next(df.value for df in at.dataframe if 'Kapasitas asumsi' in df.value.columns and len(df.value)==16)['Kapasitas asumsi'])!={30,40,45,60,80,100}


def test_queue_clock_validation_day_reset_and_no_duplicate():
    at=app(); at.button(key='nav_'+'Antrean kegiatan').click().run()
    at.selectbox(key='queue_class').set_value('2871/ARK').run()
    button(at,'Masukkan ke antrean').click().run()
    assert len(at.session_state['queue'])==1 and button(at,'Masukkan ke antrean').disabled
    at.number_input(key='queue_clock').set_value(60).run()
    button(at,'Terapkan peningkatan prioritas').click().run()
    at.number_input(key='queue_clock').set_value(30).run()
    button(at,'Proses permintaan berikutnya').click().run()
    assert len(at.session_state['queue'])==1 and at.error
    at.number_input(key='queue_clock').set_value(60).run()
    button(at,'Proses permintaan berikutnya').click().run()
    assert len(at.session_state['queue'])==0 and len(at.session_state['queue_processed'])==1
    button(at,'Mulai ulang antrean').click().run()
    assert len(at.session_state['queue'])==0 and at.session_state['queue_processed']==[]
    assert at.number_input(key='queue_clock').value==0
    at.selectbox(key='queue_class').set_value('2871/ARK').run()
    button(at,'Masukkan ke antrean').click().run()
    at.selectbox(key='queue_day').set_value(at.selectbox(key='queue_day').options[-1]).run()
    assert len(at.session_state['queue'])==0 and not at.exception


def test_queue_survives_page_navigation_and_resets_for_new_workbook():
    at=app(); at.button(key='nav_'+'Antrean kegiatan').click().run()
    day=at.selectbox(key='queue_day').options[-1]
    at.selectbox(key='queue_day').set_value(day).run()
    at.number_input(key='queue_clock').set_value(60).run()
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    choice=next(r.request_id for r in queue_inputs(data)[0] if r.day==day)
    at.selectbox(key='queue_class').set_value(choice).run()
    button(at,'Masukkan ke antrean').click().run()
    at.button(key='nav_'+'Cari jadwal').click().run()
    at.button(key='nav_'+'Antrean kegiatan').click().run()
    assert at.selectbox(key='queue_day').value==day
    assert len(at.session_state['queue'])==1 and at.number_input(key='queue_clock').value==60
    # Same structure/dates, distinct bytes: a new workbook must not inherit a queue.
    raw=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')['raw']
    blob=BytesIO()
    with pd.ExcelWriter(blob,engine='openpyxl') as writer:
        for name,frame in raw.items(): frame.to_excel(writer,sheet_name=name,index=False)
    at.session_state['workbook_bytes']=blob.getvalue()
    at.session_state['workbook_name']='salinan_excel.xlsx'
    at.run()
    assert len(at.session_state['queue'])==0 and at.session_state['queue_processed']==[]
    assert at.number_input(key='queue_clock').value==0 and not at.exception


def test_dp_inputs_are_excel_classes_and_not_notebook_fixtures():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    candidates,_=scheduling_inputs(data)
    at=app(); at.button(key='nav_'+'Pilih jadwal').click().run()
    group=at.selectbox(key='dp_group').value
    batch=[r for r in candidates if (r.room_id,r.day)==group]
    assert at.metric[0].value==str(optimize_schedule(batch)[0])
    assert not button(at,'Alokasikan kandidat ruang/hari ini').disabled
    assert all(s.key!='candidate_mode' for s in at.selectbox)
    frame=next(d.value for d in at.dataframe if 'Hasil' in d.value.columns)
    assert set(frame['Kode kelas'])<={key for key,_ in data['ingredients']['kelas']}
    assert set(frame['Kategori'])=={'Ujian'}
    assert 'J1' not in set(frame['Kode kelas']) and not at.exception


def test_experiments_use_excel_counts_and_full_registered_tests():
    at=app(); at.button(key='nav_'+'Eksperimen').click().run()
    assert not button(at,'Jalankan percobaan').disabled
    assert at.dataframe[0].value['Baris Excel'].tolist()==[243,122,61,16]
    at.button(key='nav_'+'Data & panduan').click().run()
    plan=next(df.value for df in at.dataframe if list(df.value.columns)==['ID','Status','Detail'])
    assert plan['Status'].tolist()==['TERDAFTAR']*33
    button(at,'Jalankan 33 pengujian Colab').click().run()
    plan=next(df.value for df in at.dataframe if list(df.value.columns)==['ID','Status','Detail'])
    assert plan['Status'].tolist()==['LULUS']*33
    assert not any('acak' in b.label or 'contoh' in b.label for b in at.button)


def test_legacy_state_is_discarded_and_new_workbook_changes_all_views():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    raw={k:v.copy() for k,v in data['raw'].items()}
    raw['mata_kuliah'].loc[raw['mata_kuliah']['kode_mk'].eq('ACC93105'),'nama_mk']='Nama pada Excel Baru'
    raw['jadwal_uts'].loc[raw['jadwal_uts']['kode_mk'].eq('ACC93105'),'nama_mk']='Nama pada Excel Baru'
    raw['ruang'].loc[raw['ruang']['ruang'].eq('F705'),'kapasitas_asumsi']=99
    blob=BytesIO()
    with pd.ExcelWriter(blob,engine='openpyxl') as writer:
        for k,v in raw.items(): v.to_excel(writer,sheet_name=k,index=False)
    at=AppTest.from_file(str(APP),default_timeout=30)
    at.session_state['workbook_bytes']=blob.getvalue()
    at.session_state['workbook_name']='data_baru.xlsx'
    for key in ['simulation','queue','experiments','requests']: at.session_state[key]='stale'
    at.run()
    assert not at.exception
    for key in ['simulation','queue','experiments','requests']: assert key not in at.session_state
    at.button(key='nav_'+'Cari jadwal').click().run()
    at.checkbox(key='search_include_pairs').set_value(False).run()
    at.selectbox(key='search_mode').set_value('Kode MK lengkap').run()
    at.text_input(key='search_query').set_value('ACC93105').run()
    assert set(at.dataframe[0].value['Mata kuliah'])=={'Nama pada Excel Baru'}
    at.button(key='nav_'+'Ruangan').click().run()
    frame=next(df.value for df in at.dataframe if 'Kapasitas asumsi' in df.value.columns and len(df.value)==16)
    assert frame.loc[frame['Ruang'].eq('F705'),'Kapasitas asumsi'].iloc[0]==99
    at.button(key='nav_'+'Pilih jadwal').click().run()
    assert not at.exception


def test_int_nas_results_toggle_bidirectional_and_source_labels():
    at=app();at.button(key='nav_'+'Cari jadwal').click().run()
    at.selectbox(key='search_mode').set_value('Kode MK lengkap').run()
    at.text_input(key='search_query').set_value('ACC93105').run()
    frame=at.dataframe[0].value
    assert set(frame['Kode MK'])=={'ACC93105','ACC13101'}
    assert len(frame)==22 and frame['Kode kelas'].is_unique
    assert set(frame.loc[frame['Kode MK'].eq('ACC13101'),'Asal hasil'])=={'Pasangan INT–NAS'}
    links=at.dataframe[1].value
    assert links.iloc[0]['Status Excel']=='perlu verifikasi'
    assert links.iloc[0]['Verifikasi']=='belum dikonfirmasi resmi'
    at.text_input(key='search_query').set_value('ACC13101').run()
    assert set(at.dataframe[0].value['Kode MK'])=={'ACC13101','ACC93105'}
    at.checkbox(key='search_include_pairs').set_value(False).run()
    assert set(at.dataframe[0].value['Kode MK'])=={'ACC13101'}
    at.checkbox(key='search_include_pairs').set_value(True).run()
    at.selectbox(key='search_mode').set_value('Awalan nama').run()
    at.text_input(key='search_query').set_value('Accounting Principles 1').run()
    # The Excel contains two course codes with this name, each with an explicit pair.
    assert set(at.dataframe[0].value['Kode MK'])=={'ACC93105','ACC13101','FST9435004','FST1435004'}
    assert not at.exception
