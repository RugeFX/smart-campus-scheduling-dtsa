from pathlib import Path
import pandas as pd
from campus.data import load_workbook,build_search_indexes
from campus.search_pairs import pair_indexes,expand_course_ids

ROOT=Path(__file__).resolve().parents[1]


def test_pairs_only_follow_complete_explicit_excel_links():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    indexes=build_search_indexes(data['ingredients'])
    lookup,rows,skipped=pair_indexes(data,indexes['courses'])
    assert len(rows)==55 and len(skipped)==6
    assert lookup.get('ACC93105')=='ACC13101' and lookup.get('ACC13101')=='ACC93105'
    assert expand_course_ids(['ACC93105','ACC13101'],lookup,indexes['courses'])==['ACC93105','ACC13101']
    for code in skipped['Kode INT']:
        assert lookup.get(code) is None
        assert expand_course_ids([code],lookup,indexes['courses'])==[code]


def test_ambiguous_uploaded_links_are_not_silently_overwritten():
    data=load_workbook(ROOT/'data/dataset_jadwal_uts_feb_uph.xlsx')
    indexes=build_search_indexes(data['ingredients'])
    pair=data['clean']['pasangan_int_nas'].iloc[[0]].copy()
    pair['kode_mk_nas']='ACC13102'
    pair['baris_excel']=1000
    data['clean']['pasangan_int_nas']=pd.concat([data['clean']['pasangan_int_nas'],pair],ignore_index=True)
    lookup,_,skipped=pair_indexes(data,indexes['courses'])
    assert lookup.get('ACC93105') is None and lookup.get('ACC13101') is None
    assert lookup.get('ACC93106') is None and lookup.get('ACC13102') is None
    assert skipped['Alasan'].str.contains('lebih dari satu').sum()==3
