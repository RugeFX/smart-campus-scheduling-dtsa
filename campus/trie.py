# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from .hash_table import HashTableChaining

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

        results = []
        def dfs(node):
            if node.is_end:
                for entry_id in node.entry_ids:
                    if entry_id not in results:
                        results.append(entry_id)
            for _, child_node in node.children.items():
                dfs(child_node)

        dfs(current)
        return results

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
