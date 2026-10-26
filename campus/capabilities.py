"""Availability comes from the saved notebook, not locally completed algorithms."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATUS = json.loads((ROOT / "references/colab-status.json").read_text())
SNAPSHOT_HASH = STATUS["sha256"]
SOURCE_LABEL = (datetime.fromisoformat(STATUS["modified_time"].replace("Z", "+00:00"))
                .astimezone(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y · %H.%M WIB")
                if STATUS.get("modified_time") else "versi tersimpan lokal")


def ready(*operations):
    return all(STATUS["operations"].get(name, {}).get("implemented", False) for name in operations)


def status_rows():
    return [
        {"Fitur":"MST · Kruskal / Prim", "Status":"Siap · koneksi & biaya simulasi" if ready("kruskal_mst", "prim_mst", "validate_mst") else "TODO"},
        {"Fitur":"Hash linear probing / tombstone", "Status":"Siap" if ready("HashTableLinearProbing.delete") else "TODO"},
        {"Fitur":"Greedy activity selection", "Status":"Siap" if ready("select_activities") else "TODO"},
        {"Fitur":"MaxHeap / Heap Sort", "Status":"Siap" if ready("MaxHeap.pop","heap_sort") else "TODO"},
        {"Fitur":"Trie delete", "Status":"Siap" if ready("Trie.delete") else "TODO"},
        {"Fitur": "Hash Table", "Status": "Siap" if ready("HashTableChaining.put", "HashTableChaining.get") else "TODO"},
        {"Fitur": "Trie", "Status": "Siap" if ready("Trie.insert", "Trie.autocomplete") else "TODO"},
        {"Fitur": "Heap/PQ", "Status": "Siap" if ready("MinHeapPriorityQueue.push", "MinHeapPriorityQueue.pop") else "TODO"},
        {"Fitur": "AVL insert / kapasitas / ranking", "Status": "Siap" if ready("AVLTree.insert", "AVLTree.ceiling_capacity", "AVLTree.top_k_utilization") else "TODO"},
        {"Fitur": "AVL delete", "Status": "Siap" if ready("AVLTree.delete") else "TODO"},
        {"Fitur": "DP", "Status": "Siap" if ready("optimize_schedule") else "TODO"},
        {"Fitur": "DP memoization", "Status": "Siap" if ready("optimize_schedule_memo") else "TODO"},
        {"Fitur": "Pencarian Excel FEB", "Status": "Aktif di Streamlit"},
        {"Fitur": "Booking / update / penggabungan", "Status": "Siap" if ready("schedule_across_rooms", "update_room_usage", "merge_equivalent_classes") else "TODO"},
        {"Fitur": "Benchmark algoritma", "Status": "Siap · pengukuran Excel & arsip Colab" if STATUS["benchmark_ready"] else "Belum tersedia"},
        {"Fitur": "Rencana pengujian", "Status": f"{len(STATUS['test_runners'])} fungsi terdaftar"},
    ]
