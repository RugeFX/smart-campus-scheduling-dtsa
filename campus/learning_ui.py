"""Optional algorithm explanations, kept outside the ordinary task flow."""
import json
import pandas as pd
import streamlit as st
from .data import build_search_indexes
from .heap import MaxHeap, heap_sort
from .uas_examples import avl_rotation_examples, simulate_priority_dispatch


def trie_delete_preview(data):
    with st.expander("Coba hapus dari indeks nama"):
        st.caption("Pratinjau pada salinan indeks Excel. File Excel dan hasil pencarian utama tetap utuh.")
        entries=data['ingredients']['nama']
        if not entries: return
        choice=st.selectbox('Nama yang akan dihapus',range(len(entries)),
            format_func=lambda i:f'{entries[i].name} · {entries[i].entry_id}',key='trie_delete_choice')
        entry=entries[choice]
        if st.button('Uji hapus dari salinan indeks',key='trie_delete_preview'):
            trie=build_search_indexes(data['ingredients'])['names']
            before=trie.autocomplete(entry.name)
            nodes=trie.count_nodes()
            removed=trie.delete(entry.name,entry.entry_id)
            after=trie.autocomplete(entry.name)
            st.success('Entri dihapus dari salinan indeks.' if removed else 'Entri tidak ditemukan.')
            st.write({'ID sebelum':before,'ID sesudah':after,'Node sebelum':nodes,'Node sesudah':trie.count_nodes()})
            st.caption('Nama lain dengan awalan sama tetap tersimpan. Cabang kosong dipangkas.')


def _rotation_dot(node):
    lines=[]
    def walk(item,path='root'):
        if not item: return
        lines.append(f'{path} [label={json.dumps(str(item.get("key",item.get("room_id",""))))}];')
        for side in ('left','right'):
            if item.get(side):
                child=path+'_'+side
                lines.append(f'{path} -> {child};');walk(item[side],child)
    walk(node)
    return 'digraph G { node [shape=box]; '+ ' '.join(lines)+' }'


def room_algorithm_details(room_list):
    with st.expander('Kapasitas terbesar dengan MaxHeap dan Heap Sort'):
        st.caption('Masukan berasal dari kapasitas ruang pada Excel aktif. Urutan alokasi tetap mengikuti kebutuhan peserta.')
        values=[(room.capacity,room.room_id) for room in room_list]
        heap=MaxHeap(trace=True);heap.build(values)
        st.write(f'Kapasitas terbesar: **{heap.peek()[1]} · {heap.peek()[0]} kursi**')
        st.dataframe(pd.DataFrame(heap_sort(values),columns=['Kapasitas','Ruang']),hide_index=True,width='stretch')
        st.caption(f'Heap valid: {heap.validate()} · {heap.comparisons} perbandingan saat membangun. Heap Sort mengeluarkan nilai terbesar lalu membalik urutannya.')
        st.dataframe(pd.DataFrame([{key:json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict,tuple)) else value for key,value in event.items()} for event in heap.trace]),hide_index=True,width='stretch')
    with st.expander('Lihat cara AVL menyeimbangkan pohon'):
        st.caption('Empat fixture kecil untuk menjelaskan rotasi; bukan data ruang atau input alokasi.')
        examples=avl_rotation_examples()
        kind=st.selectbox('Kasus rotasi',['LL','RR','LR','RL'],key='avl_rotation_kind')
        item=next(item for item in examples if item['kind']==kind)
        st.write('Urutan kapasitas dimasukkan: '+ ' → '.join(map(str,item['values'])))
        log=item['log'][-1]
        left,right=st.columns(2)
        with left:
            st.write('**Sebelum rotasi**');st.graphviz_chart(_rotation_dot(log['before']))
        with right:
            st.write('**Sesudah rotasi**');st.graphviz_chart(_rotation_dot(log['after']))
        st.caption(f"{item['rotations']} rotasi dasar · urutan, tinggi, dan keseimbangan valid.")
        st.json(log,expanded=False)


def dispatch_example():
    with st.expander('Mengapa ada aging? · contoh uji'):
        st.caption('Simulasi terkontrol: satu Event lama bersaing dengan 60 ujian baru. Ini tidak mengubah jam ujian Excel.')
        if st.button('Jalankan contoh waktu tunggu',key='dispatch_example'):
            plain=simulate_priority_dispatch(False);aged=simulate_priority_dispatch(True)
            st.dataframe(pd.DataFrame([{'Metode':'Tanpa aging','Tunggu Event (menit)':plain['event_wait'],'Tunggu terlama (menit)':plain['max_wait']},
                {'Metode':'Dengan aging','Tunggu Event (menit)':aged['event_wait'],'Tunggu terlama (menit)':aged['max_wait']}]),hide_index=True,width='stretch')
            st.caption('Hasil berlaku pada pola kedatangan ini. Aging menaikkan prioritas efektif; urutan pada prioritas sama mengikuti FIFO.')
            st.dataframe(pd.DataFrame(aged['trace']),hide_index=True,width='stretch')
