from dataclasses import replace
from pathlib import Path
import json
from streamlit.testing.v1 import AppTest
from campus import dp_ui
from campus.heap_tests import heap_test_request

ROOT = Path(__file__).resolve().parents[1]


def test_large_batch_keeps_tabulation_and_skips_recursive_methods(monkeypatch):
    def unexpected(_): raise AssertionError("Recursive comparator must not run.")
    monkeypatch.setattr(dp_ui,"naive_recursive",unexpected)
    monkeypatch.setattr(dp_ui,"optimize_schedule_memo",unexpected)
    batch=[replace(heap_test_request(str(i)),value=10) for i in range(1100)]
    rows=dp_ui.compare_schedule_methods(batch)
    assert [r['Status'].startswith('Dilewati') for r in rows]==[True,True,False]
    assert rows[-1]['Nilai']==10


def test_naive_limit_and_memo_recursion_fallback(monkeypatch):
    def unexpected(_): raise AssertionError("Naive limit must be enforced.")
    def recursion(_): raise RecursionError
    monkeypatch.setattr(dp_ui,"naive_recursive",unexpected)
    monkeypatch.setattr(dp_ui,"optimize_schedule_memo",recursion)
    batch=[heap_test_request(str(i)) for i in range(16)]
    rows=dp_ui.compare_schedule_methods(batch)
    assert rows[0]['Status'].startswith('Dilewati')
    assert rows[1]['Status'].startswith('Batas rekursi')
    assert rows[2]['Nilai']==10


def test_page_does_not_measure_until_explicit_click(monkeypatch):
    calls=[]
    original=dp_ui.naive_recursive
    def spy(batch): calls.append(len(batch));return original(batch)
    monkeypatch.setattr(dp_ui,"naive_recursive",spy)
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    at.button(key='nav_Pilih jadwal').click().run()
    assert not at.exception and calls==[]
    at.button(key='dp_compare').click().run()
    assert not at.exception and calls==[1]
    at.radio(key='dp_method').set_value('Memoization (top-down)').run()
    assert not at.exception and calls==[1]


def test_imported_benchmark_does_not_claim_old_environment():
    metadata=json.loads((ROOT/'data/colab_benchmark_environment.json').read_text())
    assert metadata['environment_status']=='unavailable_for_imported_run'
    assert metadata['timestamp_utc'] is None and metadata['system'] is None
    assert metadata['records']==79 and metadata['repeat']==5
