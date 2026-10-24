"""Execute saved Python notebook cells in a fresh namespace; record real outputs.

The local Excel is supplied by running with data/ as cwd. No remote file is edited.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import sys

target = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[1]
notebook = json.loads(target.read_text())
namespace = {"__name__": "__main__"}
os.chdir(root / "data")
count = 0


class Tee(io.StringIO):
    def write(self, text):
        sys.__stdout__.write(text)
        sys.__stdout__.flush()
        return super().write(text)


for index, cell in enumerate(notebook["cells"]):
    if cell["cell_type"] != "code":
        continue
    count += 1
    print(f"EXECUTING CELL {index}", flush=True)
    output = Tee()
    with redirect_stdout(output):
        exec(compile("".join(cell["source"]), f"notebook-cell-{index}", "exec"), namespace)
    cell["execution_count"] = count
    cell["outputs"] = ([{"name": "stdout", "output_type": "stream",
                         "text": output.getvalue().splitlines(keepends=True)}] if output.getvalue() else [])
    if "benchmark_chart" in namespace and "def run_benchmarks(" in "".join(cell["source"]):
        cell["outputs"].append({"output_type": "display_data", "metadata": {},
            "data": {"text/html": [namespace["benchmark_chart"].to_html()]}})
    # Save progress in case the longest benchmark is interrupted.
    target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")

assert len(namespace["test_report"]) == 18
assert all(row[1] == "LULUS" for row in namespace["test_report"])
assert len(namespace["benchmark_results"]) == 58
assert all(row["runs"] == 5 for row in namespace["benchmark_results"])
assert {row["n"] for row in namespace["benchmark_results"]} >= {240, 1000, 10000, 100000}
summary = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "code_cells": count,
    "test_report": namespace["test_report"], "benchmark_records": len(namespace["benchmark_results"]),
    "environment": namespace["benchmark_environment"],
    "feb": {"accepted": sum(len(r["bookings"]) for r in namespace["feb_allocation_demo"]["weeks"]),
            "rejected": sum(len(r["rejected"]) for r in namespace["feb_allocation_demo"]["weeks"]),
            "excluded": len(namespace["feb_allocation_demo"]["excluded"])}}
(target.parent / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
print("VERIFIED:", count, "code cells; 18/18 tests; 58 measured benchmark records.")
