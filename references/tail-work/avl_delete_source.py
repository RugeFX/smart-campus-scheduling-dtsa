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
