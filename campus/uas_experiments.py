# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .models import *
from .generators import generate_requests
from .dp import optimize_schedule, optimize_schedule_memo, naive_recursive, chain_requests
from .greedy import select_activities, brute_force_activity_count
from .hash_table import HashTableChaining, HashTableLinearProbing
from .heap import MinHeapPriorityQueue
from .experiments import measure_operation, measure_peak_memory

def run_selected_benchmarks(repeat=5, seed=SEED):
    """Eksperimen tambahan pada fixture sintetis dengan operasi yang setara."""
    rows=[]
    def record(module,operation,implementation,n,setup,action,metric=None,load=None):
        result=measure_operation(setup,action,repeat,metric)
        rows.append({"module":module,"operation":operation,"implementation":implementation,
                     "n":n,"load_factor":load,"source":"synthetic fixture; not application schedule",
                     "seed":seed,"runs":repeat,"warmup_runs":1,
                     "median_seconds":result["median_seconds"],"run_seconds":result["run_seconds"],
                     "operation_metrics":result["metrics"],"peak_bytes":measure_peak_memory(setup,action)})
    for n in (50,500,5000):
        batch=generate_requests(n,seed)
        expected=sorted(enumerate(batch),key=lambda pair:(pair[1].priority,pair[0]))
        def heap_action(queue):
            queue.build(batch)
            while queue:queue.pop()
        def unsorted_action(items):
            items.extend((r.priority,i) for i,r in enumerate(batch))
            while items:
                index=min(range(len(items)),key=lambda i:items[i])  # Oracle list, bukan inti PQ.
                items.pop(index)
        def sorted_action(items):
            items.extend((r.priority,i) for i,r in sorted(enumerate(batch),key=lambda pair:(pair[1].priority,pair[0])))
            while items:items.pop(0)
        record("PQ","build + drain","heap manual",n,MinHeapPriorityQueue,heap_action,
               lambda state,result:{"comparisons":state.comparisons})
        record("PQ","build + drain","list tidak terurut",n,list,unsorted_action)
        record("PQ","build + drain","list terurut",n,list,sorted_action)
    for slots in (128,512):
        for load in (0.3,0.5,0.7,0.9):
            n=int(slots*load)
            pairs=[(f"ID-{i}",i) for i in range(n)]
            queries=[f"ID-{i%n}" if i%2 else f"MISSING-{i}" for i in range(100)]
            for name,cls in [("chaining",HashTableChaining),("linear probing",HashTableLinearProbing)]:
                def setup(cls=cls):
                    t=cls(slots,0.99)
                    for key,value in pairs:t.put(key,value)
                    t.probes=t.collisions=0
                    return t
                record("Hash","100 lookup · 50% hit",name,n,setup,
                       lambda t:[t.get(q) for q in queries],
                       lambda t,result:{"probes":t.probes,"average_probes":t.probes/len(queries)},n/slots)
    for n in (8,12,15):
        batch=chain_requests(n,seed)
        assert naive_recursive(batch)[0]==optimize_schedule_memo(batch)[0]==optimize_schedule(batch)[0]
        for name,action in [("naif",naive_recursive),("memoization",optimize_schedule_memo),("tabulasi",optimize_schedule)]:
            counter=(lambda state,result:{"calls":result[1]}) if name=="naif" else (lambda state,result:{"calls":result[2]}) if name=="memoization" else (lambda state,result:{"states":len(state)})
            record("DP","rantai kompatibel",name,n,lambda:batch,action,counter)
    for n in (8,10,12):
        batch=generate_requests(n,seed)
        expected,_=brute_force_activity_count(batch)
        assert select_activities(batch)[0]==expected
        for strategy in ("earliest_finish","earliest_start"):
            record("Greedy","pilih jumlah kegiatan",strategy,n,lambda:batch,
                   lambda state,strategy=strategy:select_activities(state,strategy))
        record("Greedy","pilih jumlah kegiatan","brute force kardinalitas",n,lambda:batch,brute_force_activity_count)
    return rows
