# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from typing import Optional, List
from .models import Room

class AVLNode:
    def __init__(self, key: tuple, room: 'Room'):
        self.key = key  # (nilai_indeks, room_id)
        self.room = room
        self.left: Optional[AVLNode] = None
        self.right: Optional[AVLNode] = None
        self.height: int = 1

class AVLTree:
    def __init__(self, index="capacity"):
        if index not in ("capacity", "utilization"):
            raise ValueError("Indeks harus capacity atau utilization.")
        self.index = index
        self.rotations = 0
        self.root: Optional[AVLNode] = None

    def get_height(self, node: Optional[AVLNode]) -> int:
        return node.height if node else 0

    def get_balance(self, node: Optional[AVLNode]) -> int:
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    def update_height(self, node: AVLNode):
        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))

    def rotate_right(self, y: AVLNode) -> AVLNode:
        self.rotations += 1
        x = y.left
        assert x is not None
        T2 = x.right

        x.right = y
        y.left = T2

        self.update_height(y)
        self.update_height(x)
        return x

    def rotate_left(self, x: AVLNode) -> AVLNode:
        self.rotations += 1
        y = x.right
        assert y is not None
        T2 = y.left

        y.left = x
        x.right = T2

        self.update_height(x)
        self.update_height(y)
        return y

    def insert(self, key, room=None):
        # Gunakan insert(room) atau insert(key, room).
        if room is None:
            room = key
            key = (getattr(room, self.index), room.room_id)
        if key != (getattr(room, self.index), room.room_id):
            raise ValueError("Key tidak cocok dengan indeks dan data ruangan.")
        self.root = self._insert(self.root, key, room)

    def _insert(self, node: Optional[AVLNode], key: tuple, room: 'Room') -> AVLNode:
        if not node:
            return AVLNode(key, room)

        if key == node.key:
            node.room = room
            return node

        if key < node.key:
            node.left = self._insert(node.left, key, room)
        else:
            node.right = self._insert(node.right, key, room)

        self.update_height(node)
        balance = self.get_balance(node)

        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self.rotate_right(node)

        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self.rotate_left(node)

        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)

        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)

        return node

    def in_order_traversal(self) -> List['Room']:
        rooms_list = []
        self._in_order(self.root, rooms_list)
        return rooms_list

    def _in_order(self, node: Optional[AVLNode], rooms_list: list):
        if node:
            self._in_order(node.left, rooms_list)
            rooms_list.append(node.room)
            self._in_order(node.right, rooms_list)

    def find_suitable_room(self, participants: int) -> Optional['Room']:
        if self.index != "capacity":
            raise ValueError("Pencarian kapasitas harus memakai indeks capacity.")
        if type(participants) is not int or participants <= 0:
            raise ValueError("Jumlah peserta harus berupa bilangan bulat positif.")

        candidate: Optional['Room'] = None
        current = self.root

        while current:
            # Key format is (capacity, room_id)
            if current.room.capacity >= participants:
                candidate = current.room
                current = current.left  # Try to find a smaller but still sufficient capacity
            else:
                current = current.right # Capacity is too small, look for larger ones

        return candidate

    def check_balance(self) -> bool:
        return self._check_balance(self.root)

    def _check_balance(self, node: Optional[AVLNode]) -> bool:
        if not node:
            return True
        balance = self.get_balance(node)
        if abs(balance) > 1:
            return False
        return self._check_balance(node.left) and self._check_balance(node.right)



    # Operasi pencarian, ranking, dan validasi.
    def delete(self, key):
        """Hapus key O(log n); True bila ditemukan, False bila tidak ada."""
        def rebalance(node):
            self.update_height(node)
            balance = self.get_balance(node)
            if balance > 1:
                if self.get_balance(node.left) < 0:
                    node.left = self.rotate_left(node.left)
                return self.rotate_right(node)
            if balance < -1:
                if self.get_balance(node.right) > 0:
                    node.right = self.rotate_right(node.right)
                return self.rotate_left(node)
            return node

        def remove(node, target):
            if node is None:
                return None, False
            if target < node.key:
                node.left, found = remove(node.left, target)
            elif target > node.key:
                node.right, found = remove(node.right, target)
            else:
                found = True
                if node.left is None:
                    return node.right, True
                if node.right is None:
                    return node.left, True
                successor = node.right
                while successor.left is not None:
                    successor = successor.left
                node.key, node.room = successor.key, successor.room
                node.right, _ = remove(node.right, successor.key)
            return (rebalance(node), True) if found else (node, False)

        self.root, found = remove(self.root, key)
        return found

    def inorder(self):
        return self.in_order_traversal()

    def ceiling_capacity(self, participants):
        return self.find_suitable_room(participants)

    def top_k_utilization(self, k):
        if self.index != "utilization":
            raise ValueError("Ranking harus memakai indeks utilization.")
        if type(k) is not int or k < 0:
            raise ValueError("k harus bilangan bulat tidak negatif.")
        stack, result, node = [], [], self.root
        while (node or stack) and len(result) < k:
            while node:
                stack.append(node)
                node = node.right
            node = stack.pop()
            result.append(node.room)
            node = node.left
        return result

    def validate(self):
        def visit(node, lower=None, upper=None):
            if node is None:
                return 0
            assert lower is None or lower < node.key, "Urutan BST salah."
            assert upper is None or node.key < upper, "Urutan BST salah."
            assert node.key == (getattr(node.room, self.index), node.room.room_id)
            left_height = visit(node.left, lower, node.key)
            right_height = visit(node.right, node.key, upper)
            height = 1 + max(left_height, right_height)
            assert node.height == height, "Tinggi tersimpan salah."
            assert abs(left_height - right_height) <= 1, "Pohon tidak seimbang."
            return height
        visit(self.root)
        return True
