def simulate_priority_dispatch(aging=False, ticks=60):
    """Fixture dispatcher terkontrol, bukan input jadwal aplikasi.

    Satu Event lama bersaing dengan satu ujian baru per tick. Ada enqueue dan
    dequeue dengan jam simulasi eksplisit; metrik menghitung waktu tunggu nyata
    pada simulasi ini, bukan waktu perjalanan atau perubahan jam ujian.
    """
    queue, trace, waits = MinHeapPriorityQueue(), [], []
    def request(code, kind, submitted):
        return ScheduleRequest(code, code, kind, 1, "UJI", "2026-10-05", 600, 660, VALUE[kind], submitted)
    queue.push(request("WAIT", "Event", 0))
    trace.append({"Waktu":0,"Aksi":"Masuk","ID":"WAIT","Tunggu":None})
    event_wait = None
    for tick in range(ticks):
        now = tick * 10
        if aging: queue.apply_aging(now,10)
        item = request(f"EXAM-{tick}","Examination",now)
        queue.push(item)
        trace.append({"Waktu":now,"Aksi":"Masuk","ID":item.request_id,"Tunggu":None})
        item = queue.pop(); wait = now-item.submitted_at
        waits.append(wait)
        if item.request_id == "WAIT": event_wait = wait
        trace.append({"Waktu":now,"Aksi":"Proses","ID":item.request_id,"Tunggu":wait})
        assert queue.validate()
    now=ticks*10
    while queue:
        if aging: queue.apply_aging(now,10)
        item=queue.pop();wait=now-item.submitted_at;waits.append(wait)
        if item.request_id=="WAIT": event_wait=wait
        trace.append({"Waktu":now,"Aksi":"Proses","ID":item.request_id,"Tunggu":wait})
        now += 10
    return {"fixture":True,"aging":aging,"events":len(trace),"trace":trace,
            "average_wait":sum(waits)/len(waits),"max_wait":max(waits),"event_wait":event_wait}


def avl_rotation_examples():
    """Empat kasus uji kecil untuk visual before/after; kapasitas adalah fixture."""
    examples=[]
    for kind,values in [("LL",[30,20,10]),("RR",[10,20,30]),("LR",[30,10,20]),("RL",[10,30,20])]:
        tree=AVLTree()
        for value in values:
            tree.insert(Room(f"R-{value}",value));tree.validate()
        examples.append({"fixture":True,"kind":kind,"values":values,
                         "rotations":tree.rotations,"log":tree.rotation_log,"valid":tree.validate()})
    return examples
