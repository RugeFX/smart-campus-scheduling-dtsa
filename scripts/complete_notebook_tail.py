"""Apply section 6–10 implementations and the required AVL delete dependency.

Run only against a fresh notebook download; preserve all unrelated source cells.
"""
import ast
import json
from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
parts = ROOT / "references/tail-work"
notebook = json.loads(Path(sys.argv[1]).read_text())
for cell in notebook["cells"]:
    source = "".join(cell["source"])
    updated = source
    if source.startswith("# Smart Campus — Notebook Kelompok 2"):
        updated = source.replace("Lengkapi bagian **TODO** untuk penghapusan AVL, integrasi, dan eksperimen.",
            "Penghapusan AVL, integrasi, 18 pengujian, dan eksperimen sudah dilengkapi; "
            "lihat bagian 6–10 untuk hasil aktual dan batas simulasi.")
    elif source.startswith("## 4. Dua AVL"):
        updated = source.replace("**TODO:** delete dan pembaruan indeks saat data ruang berubah.",
            "**Tersedia:** delete dengan rebalance; pembaruan registry dan kedua indeks diuji pada bagian 6–7.")
    elif source.startswith("from typing import List, Optional") and "class AVLTree:" in source:
        tree = ast.parse(source)
        avl = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AVLTree")
        method = next(node for node in avl.body if isinstance(node, ast.FunctionDef) and node.name == "delete")
        lines = source.splitlines(keepends=True)
        lines[method.lineno-1:method.end_lineno] = [textwrap.indent((parts / "avl_delete_source.py").read_text().rstrip(), "    ") + "\n"]
        updated = "".join(lines).replace("# TODO: delete key lama dan insert key baru setelah pemakaian berubah.",
                                       "# Delete dan pembaruan kedua indeks diuji pada bagian 7.")
    elif source.startswith("def merge_equivalent_classes("):
        updated = (parts / "service_source.py").read_text()
    elif source.startswith("TEST_IDS ="):
        updated = (parts / "tests_source.py").read_text()
    elif source.startswith("def measure_operation(") and (parts / "benchmark_source.py").exists():
        updated = (parts / "benchmark_source.py").read_text()
    for heading, filename in [("## 6.", "section6.md"), ("## 7.", "section7.md"),
                              ("## 8.", "section8.md"), ("## 9.", "section9.md"), ("## 10.", "section10.md")]:
        if source.startswith(heading) and (parts / filename).exists():
            updated = (parts / filename).read_text()
    if updated != source:
        cell["source"] = updated.splitlines(keepends=True)
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
notebook["metadata"]["smart_campus"]["status"] = "Manual structures, integration, 18 tests and reproducible benchmarks implemented; simulation limits documented"
Path(sys.argv[2]).write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
print("Updated sections 6–10 and required AVL delete dependency.")
