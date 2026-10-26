class TrieNode:
    def __init__(self):
        self.children = HashTableChaining()
        self.entry_ids = []
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.visited_nodes = 0

    def insert(self, text, entry_id):
        if not isinstance(text, str):
            return
        normalized = text.strip().casefold()
        current = self.root
        for char in normalized:
            self.visited_nodes += 1
            if not current.children.contains(char):
                current.children.put(char, TrieNode())
            current = current.children.get(char)
        current.is_end = True
        if entry_id not in current.entry_ids:
            current.entry_ids.append(entry_id)

    def search(self, text):
        if not isinstance(text, str):
            return []
        normalized = text.strip().casefold()
        current = self.root
        for char in normalized:
            if not current.children.contains(char):
                return []
            current = current.children.get(char)
        if current.is_end:
            return list(current.entry_ids)
        return []

    def starts_with(self, prefix):
        if not isinstance(prefix, str):
            return False
        normalized = prefix.strip().casefold()
        current = self.root
        for char in normalized:
            if not current.children.contains(char):
                return False
            current = current.children.get(char)
        return True

    def autocomplete(self, prefix):
        if not isinstance(prefix, str):
            return []
        normalized = prefix.strip().casefold()
        current = self.root
        for char in normalized:
            if not current.children.contains(char):
                return []
            current = current.children.get(char)

        results, seen, stack = [], HashTableChaining(), [current]
        while stack:
            node = stack.pop()
            if node.is_end:
                for entry_id in node.entry_ids:
                    marker = str(entry_id)
                    if not seen.contains(marker):
                        seen.put(marker, True); results.append(entry_id)
            children = list(node.children.items())
            for _, child_node in reversed(children): stack.append(child_node)
        return results

    def delete(self, text, entry_id=None):
        """Hapus satu ID, atau seluruh kata bila entry_id=None; prefix lain tetap."""
        if not isinstance(text, str): return False
        current, path = self.root, []
        for char in text.strip().casefold():
            child = current.children.get(char)
            if child is None: return False
            path.append((current, char, child)); current = child
        if not current.is_end: return False
        if entry_id is None: current.entry_ids.clear()
        elif entry_id in current.entry_ids: current.entry_ids.remove(entry_id)
        else: return False
        current.is_end = bool(current.entry_ids)
        for parent, char, child in reversed(path):
            if child.is_end or len(child.children): break
            parent.children.delete(char)
        return True

    def count_nodes(self):
        count, stack = 0, [self.root]
        while stack:
            node = stack.pop(); count += 1
            stack.extend(child for _, child in node.children.items())
        return count


def bilingual_autocomplete(trie, prefix, equivalence_table, course_table):
    # 1. Dapatkan hasil autocomplete langsung dari trie
    direct_results = trie.autocomplete(prefix)
    final_results = []

    for entry_id in direct_results:
        if entry_id not in final_results:
            final_results.append(entry_id)

        # 2. Cari padanan bahasa (INT <-> NAS) di equivalence_table jika ada
        equivalent_id = equivalence_table.get(entry_id)
        if equivalent_id:
            # Pastikan padanan tersebut ada di katalog course_table
            if course_table.contains(equivalent_id):
                if equivalent_id not in final_results:
                    final_results.append(equivalent_id)

    return final_results
