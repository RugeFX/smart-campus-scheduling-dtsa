"""Bind artifacts from a completed local notebook execution to exact source bytes."""
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
snapshot=ROOT/'references/UTS_Group2_Smart_Campus.ipynb'
notebook=json.loads(snapshot.read_text())
verification=json.loads((ROOT/'references/verification.json').read_text())
assert all(row[1]=='LULUS' for row in verification['test_report'])
code=[c for c in notebook['cells'] if c['cell_type']=='code']
assert [c['execution_count'] for c in code]==list(range(1,len(code)+1))
assert verification['code_cells']==len(code)
assert len(verification['test_report'])==33
for source,target in [('smart_campus_benchmark.csv','colab_benchmarks.csv')]:
    shutil.copyfile(ROOT/'data'/source,ROOT/'data'/target)
frames={name:pd.read_csv(ROOT/'data'/name) for name in ['colab_benchmarks.csv','uas_selected_benchmarks.csv','mst_benchmarks.csv']}
assert [len(frame) for frame in frames.values()]==[79,43,24]
assert all(set(frame['runs'])=={5} for frame in frames.values())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fingerprint=sha(snapshot)
assert verification['notebook_sha256']==fingerprint, 'Notebook changed after execution; run verification again.'
environment=json.loads((ROOT/'data/smart_campus_benchmark_environment.json').read_text())
assert environment==verification['environment']
environment.update(environment_status='verified_local_run',records=79,additional_records=43,mst_records=24,notebook_sha256=fingerprint)
(ROOT/'data/colab_benchmark_environment.json').write_text(json.dumps(environment,indent=2)+'\n')
verification['notebook_sha256']=fingerprint
(ROOT/'references/verification.json').write_text(json.dumps(verification,indent=2)+'\n')
provenance={'notebook_sha256':fingerprint,
    'source':'Executed saved notebook locally on 27-10-2026; synthetic benchmark fixtures, not application schedule',
    'records':79,'additional_records':43,'mst_records':24,
    'benchmark_sha256':sha(ROOT/'data/colab_benchmarks.csv'),
    'additional_sha256':sha(ROOT/'data/uas_selected_benchmarks.csv'),
    'mst_sha256':sha(ROOT/'data/mst_benchmarks.csv'),
    'mst_environment_sha256':sha(ROOT/'data/mst_benchmark_environment.json')}
(ROOT/'references/benchmark-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
manifest=json.loads((ROOT/'references/manifest.json').read_text())
for entry in manifest['files']:
    if entry['file']==str(snapshot.relative_to(ROOT)):entry['sha256']=fingerprint
(ROOT/'references/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Recorded verified artifacts:',fingerprint,'; measured rows 79 + 43 + 24')
