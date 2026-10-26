def test_t20():
    rng=Random(42)
    values=[rng.randrange(-100,101) for _ in range(150)]
    heap=MaxHeap(values,trace=True)
    assert heap.is_heap() and heap.trace
    assert [heap.pop() for _ in range(len(heap))]==sorted(values,reverse=True)
    assert heap_sort(values)==sorted(values)
    heap=MaxHeap([2,7,4,1]);heap.change_key(3,20);assert heap.peek()==20 and heap.validate()
    heap.change_key(0,-1);assert heap.peek()==7 and heap.validate()
    heap.delete(1);assert heap.validate()


def test_t21():
    a,b=heap_test_request("A",start=900),heap_test_request("B",start=435)
    q=MinHeapPriorityQueue(trace=True);q.build([a,b])
    assert q.peek() is a  # FIFO per prioritas, bukan jam kegiatan.
    q.change_priority("A",4);assert q.peek() is b
    q.change_priority("A",1);assert q.peek() is a
    assert a.priority==1 and a.start==900 and q.entries[q.position_map.get("A")][2]==0
    q.apply_aging(90,30);assert q.validate() and q.peek() is a
    before=list(q.entries)
    try:q.change_priority("A",0)
    except ValueError:pass
    else:raise AssertionError("Prioritas tidak valid diterima.")
    assert q.entries==before
    q.remove("A");assert q.peek() is b and q.validate() and q.trace


def test_t22():
    table=HashTableLinearProbing(8,0.95)
    for key,value in [("AA",None),("AI",2),("AQ",3)]:table.put(key,value)
    assert table.contains("AA") and table.get("AA") is None and table.collisions>0
    assert table.delete("AA") and table.tombstones==1
    assert table.get("AI")==2 and table.get("AQ")==3
    table.put("AI",7);assert len(table)==2 and table.get("AI")==7
    table.put("AY",8);assert table.tombstones==0 and table.validate()
    oracle={"AI":7,"AQ":3,"AY":8}
    rng=Random(42)
    for _ in range(500):
        key=f"K-{rng.randrange(50)}"
        if rng.random()<0.35:assert table.delete(key)==(key in oracle);oracle.pop(key,None)
        else:
            value=rng.randrange(1000);table.put(key,value);oracle[key]=value
        assert table.validate() and dict(table.items())==oracle
    assert table.rehashes>0


def test_t23():
    trie=Trie()
    trie.insert("Alpha","A");trie.insert("ALPHA","B");trie.insert("Alphabet","A")
    assert trie.delete(" alpha ","A") and trie.search("alpha")==["B"]
    assert set(trie.autocomplete("alp"))=={"A","B"}
    assert not trie.delete("alp") and not trie.delete("alpha","missing")
    assert trie.delete("ALPHA") and trie.search("alphabet")==["A"]
    assert trie.delete("alphabet") and trie.count_nodes()==1


def test_t24():
    for example in avl_rotation_examples():
        assert example["valid"] and example["log"][-1]["kind"]==example["kind"]
        event=example["log"][-1]
        assert event["after"]["key"][0]==20 and event["before"]["key"]==event["pivot"]
    tree=AVLTree()
    for i in range(40):tree.insert(Room(f"R{i}",i+1));assert tree.check_avl()
    tree.rotation_log.clear()
    for i in range(25):assert tree.delete((i+1,f"R{i}")) and tree.validate()
    assert any(row["operation"]=="delete" for row in tree.rotation_log)
    assert tree.node_accesses>0


def test_t25():
    assert verify_greedy_random_cases(100,42).startswith("100 kasus")


def test_t26():
    example=greedy_weight_counterexample()
    assert example["greedy_count"]==2 and example["greedy_value"]==4 and example["dp_value"]==10
    earlier_long=[replace(r,start=479) if r.request_id=="C" else r for r in example["candidates"]]
    assert select_activities(earlier_long,"earliest_start")[0]==1
    assert brute_force_activity_count(example["candidates"])[0]==2


def test_t27():
    without,with_aging=simulate_priority_dispatch(False),simulate_priority_dispatch(True)
    assert len(with_aging["trace"])>=50 and without["events"]==with_aging["events"]
    assert without["event_wait"]==600 and with_aging["event_wait"]==30
    assert with_aging["max_wait"]<without["max_wait"]


def test_t28():
    pairs=[(2,"a"),(1,"b"),(2,"c"),(0,"d")]
    assert manual_merge_sort(pairs,key=lambda x:x[0])==[(0,"d"),(1,"b"),(2,"a"),(2,"c")]
    assert select_activities([])==(0,[]) and brute_force_activity_count([])==(0,[])
    assert manual_merge_sort([])==[]
