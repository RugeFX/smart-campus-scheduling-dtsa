"""Extract saved Colab definitions verbatim, without executing notebook cells.

Usage: python scripts/sync_notebook.py references/UTS_Group2_Smart_Campus.ipynb
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "references/UTS_Group2_Smart_Campus.ipynb"
notebook = json.loads(SNAPSHOT.read_text())
cells = {}
definitions = {}
assignments = {}
for index, cell in enumerate(notebook["cells"]):
    if cell["cell_type"] != "code":
        continue
    source = "".join(cell["source"])
    tree = ast.parse(source)
    cells[index] = (source, tree)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions[node.name] = (index, node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = (index, node)


def segment(index, node):
    # ast.get_source_segment alone omits decorators such as @dataclass.
    lines = cells[index][0].splitlines(keepends=True)
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return "".join(lines[start - 1:node.end_lineno]).rstrip()


def defs(*names):
    return "\n\n".join(segment(*definitions[name]) for name in names)


def assigns(*names):
    return "\n\n".join(segment(*assignments[name]) for name in names)


def write(name, source):
    output = ROOT / "campus" / name
    header = '# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.\n'
    compile(header + source, str(output), "exec")
    output.write_text(header + source.rstrip() + "\n")


model_cell = definitions["Room"][0]
imports = "\n".join(segment(model_cell, node) for node in cells[model_cell][1].body if isinstance(node, (ast.Import, ast.ImportFrom)))
write("models.py", imports + "\n\n" + assigns("PRIORITY", "VALUE", "WEEKLY_SLOTS", "AGING_STEP_MINUTES", "DEMO_DAY", "SEED") +
      "\n\n" + defs("minutes") + "\n\n" + assigns("REGULAR_SLOTS") + "\n\n" +
      defs("Room", "Course", "ClassRecord", "SearchEntry", "ScheduleRequest"))
demo_cell = assignments["room_ids"][0]
write("demo.py", "from .models import *\nfrom .hash_table import HashTableChaining\n\n" + "\n\n".join(segment(demo_cell, node) for node in cells[demo_cell][1].body if isinstance(node, ast.Assign)) + "\n\n" + defs("build_indexes"))
write("sorting.py", defs("manual_merge_sort"))
write("hash_table.py", defs("weak_hash", "polynomial_hash", "HashTableChaining", "HashTableLinearProbing"))
write("heap.py", "from .hash_table import HashTableChaining\nfrom .models import ScheduleRequest, PRIORITY\n\n" + defs("MinHeapPriorityQueue", "MaxHeap", "heap_sort"))
write("trie.py", "from .hash_table import HashTableChaining\n\n" + defs("TrieNode", "Trie", "bilingual_autocomplete"))
write("avl.py", "from typing import Optional, List\nfrom .models import Room\n\n" + defs("AVLNode", "AVLTree"))
write("generators.py", "from .models import *\n\n" + defs("generate_rooms", "generate_requests", "generate_search_entries"))
write("dp.py", "from .models import *\nfrom .generators import generate_requests\nfrom .sorting import manual_merge_sort\n\n" +
      defs("validate_candidates", "find_previous_compatible", "optimize_schedule", "optimize_schedule_memo", "explain_dp_table", "no_overlap", "brute_force_reference", "earliest_finish_reference", "verify_dp_random_cases", "naive_recursive", "chain_requests", "compare_dp_methods"))
write("greedy.py", "from .models import *\nfrom .sorting import manual_merge_sort\nfrom .dp import validate_candidates, no_overlap, optimize_schedule\nfrom .generators import generate_requests\n\n" + defs("select_activities", "brute_force_activity_count", "verify_greedy_random_cases", "greedy_weight_counterexample"))
write("uas_examples.py", "from .models import *\nfrom .heap import MinHeapPriorityQueue\nfrom .avl import AVLTree\n\n" + defs("simulate_priority_dispatch", "avl_rotation_examples"))
service_names = ["MergedClassRecord", "merge_equivalent_classes", "validate_room_registry",
    "stage_room_updates", "commit_room_registry", "update_room_usage", "touched_regular_slots",
    "schedule_across_rooms", "make_room_registry", "simulate_feb_allocation"]
write("service.py", "from copy import deepcopy\nfrom datetime import date\nimport json\nimport pandas as pd\nfrom .models import *\nfrom .hash_table import HashTableChaining\nfrom .heap import MinHeapPriorityQueue\nfrom .trie import Trie, bilingual_autocomplete\nfrom .avl import AVLTree\nfrom .dp import optimize_schedule\n\n" + defs(*service_names))
write("uas_experiments.py", "from .models import *\nfrom .generators import generate_requests\nfrom .dp import optimize_schedule, optimize_schedule_memo, naive_recursive, chain_requests\nfrom .greedy import select_activities, brute_force_activity_count\nfrom .hash_table import HashTableChaining, HashTableLinearProbing\nfrom .heap import MinHeapPriorityQueue\nfrom .experiments import measure_operation, measure_peak_memory\n\n" + defs("run_selected_benchmarks"))
write("integration_demo.py", "from .models import *\nfrom .demo import *\nfrom .service import *\n\n" + defs("demo_integration"))
benchmark_names = [name for name in definitions if name.startswith("benchmark_") or name in ("measure_operation", "measure_peak_memory", "run_benchmarks")]
write("experiments.py", "from .models import *\nfrom .generators import *\nfrom .hash_table import HashTableChaining\nfrom .heap import MinHeapPriorityQueue\nfrom .avl import AVLTree\nfrom .trie import Trie\nfrom .dp import optimize_schedule, optimize_schedule_memo, naive_recursive, chain_requests, brute_force_reference\nfrom bisect import insort\nimport gc\n\n" + defs(*benchmark_names) + "\n\n" + assigns("BENCHMARK_SIZES"))
heap_tests = ["heap_test_request", "test_t01", "test_t02", "test_t03", "test_heap_aging", "test_heap_random", "test_heap_invalid", "run_heap_tests"]
if "run_heap_tests" in definitions:
    write("heap_tests.py", "from .models import ScheduleRequest, PRIORITY, VALUE, Random, replace\nfrom .heap import MinHeapPriorityQueue\n\n" + defs(*heap_tests))
verification_imports = "from .sorting import manual_merge_sort\nfrom .heap import MaxHeap, heap_sort\nfrom .hash_table import HashTableLinearProbing\nfrom .greedy import *\nfrom .uas_examples import *\nfrom .models import *\nfrom .demo import *\nfrom .heap_tests import *\nfrom .notebook_tests import test_t04, test_t05, test_t06\nfrom .service import *\nfrom .avl import AVLTree\nfrom .trie import Trie, bilingual_autocomplete\nfrom .dp import *\n\n"
extra_tests = [name for name in definitions if name in [f"test_t{i:02d}" for i in range(7,29)] or name in ["test_rotation_sequence", "test_avl_delete_and_atomic_updates", "test_integration_boundaries"]]
write("verification.py", verification_imports + defs(*extra_tests) + "\n\n" + assigns("TEST_IDS", "TEST_RUNNERS", "RUN_TESTS") + "\n\n" + defs("run_test_plan"))
write("notebook_tests.py", "from .hash_table import HashTableChaining, weak_hash\n\n" + defs("WeakHashTable", "test_t04", "test_t05", "test_t06", "test_hash_tambahan", "run_hash_tests"))
write("search_bridge.py", "from .hash_table import HashTableChaining\nfrom .trie import Trie\n\n" + defs("hubungkan_pencarian_feb") + "\n\n" + assigns("AKTIFKAN_PENCARIAN_FEB"))
write("data_core.py", "from datetime import datetime, date, time\nimport re\nimport pandas as pd\nfrom .models import SearchEntry\n\n" +
      assigns("KOLOM_WAJIB", "BULAN", "HARI", "PERBEDAAN_RUANG_PDF") + "\n\n" +
      defs("rapikan_teks", "baca_tanggal", "baca_jam", "rapikan_dan_validasi", "nilai_biasa", "jam_tampil", "tipe_kelas_singkat", "siapkan_bahan_pencarian_feb"))


def pending(node):
    return any(isinstance(x, ast.Raise) and "NotImplementedError" in ast.unparse(x) or isinstance(x, ast.Pass)
               for x in ast.walk(node))


operations = {}
for name in ["HashTableChaining", "HashTableLinearProbing", "MinHeapPriorityQueue", "MaxHeap", "Trie", "AVLTree"]:
    index, node = definitions[name]
    for method in node.body:
        if isinstance(method, ast.FunctionDef):
            operations[f"{name}.{method.name}"] = {"implemented": not pending(method), "cell": index}
for name in ["select_activities", "heap_sort", "manual_merge_sort", "optimize_schedule", "optimize_schedule_memo", "merge_equivalent_classes", "update_room_usage", "schedule_across_rooms", "demo_integration", "hubungkan_pencarian_feb"]:
    index, node = definitions[name]
    operations[name] = {"implemented": not pending(node), "cell": index}
flags = {name: ast.literal_eval(assignments[name][1].value) for name in ["AKTIFKAN_PENCARIAN_FEB", "RUN_TESTS", "AGING_STEP_MINUTES"]}
status = {"sha256": hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
          "modified_time": sys.argv[2] if len(sys.argv) > 2 else None,
          "operations": operations, "flags": flags,
          "benchmark_ready": "run_benchmarks" in definitions and not pending(definitions["run_benchmarks"][1]),
          "test_runners": [ast.literal_eval(key) for key in assignments["TEST_RUNNERS"][1].value.keys]}
(ROOT / "references/colab-status.json").write_text(json.dumps(status, indent=2))
print("Synced Colab definitions. Pending:", ", ".join(name for name, value in operations.items() if not value["implemented"]))
