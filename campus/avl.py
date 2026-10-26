# Generated from the saved Colab snapshot. Do not fill notebook TODOs here.
from typing import Optional, List
from .models import Room

class AVLNode:
    def __init__(self, key, room):
        self.key, self.room, self.height = key, room, 1
        self.left = self.right = None

class AVLTree:
    def __init__(self, index="capacity", trace=True, trace_limit=200):
        if index not in ("capacity", "utilization"): raise ValueError("Indeks AVL tidak dikenal.")
        self.index, self.root, self.rotations, self.node_accesses = index, None, 0, 0
        self.trace_enabled, self.trace_limit, self.rotation_log = trace, trace_limit, []

    def get_height(self, node): return node.height if node else 0

    def get_balance(self, node):
        return self.get_height(node.left)-self.get_height(node.right) if node else 0

    def update_height(self, node): node.height = 1+max(self.get_height(node.left),self.get_height(node.right))

    def snapshot(self, node=None, depth=3):
        """Cuplikan lokal dibatasi kedalaman; biaya trace tetap konstan per rotasi."""
        def visit(current, level):
            if current is None or level == 0: return None
            return {"key":current.key,"height":current.height,
                    "left":visit(current.left,level-1),"right":visit(current.right,level-1)}
        return visit(self.root if node is None else node, depth)

    def rotate_right(self, y):
        self.rotations += 1
        x = y.left; assert x is not None
        y.left, x.right = x.right, y
        self.update_height(y); self.update_height(x)
        return x

    def rotate_left(self, x):
        self.rotations += 1
        y = x.right; assert y is not None
        x.right, y.left = y.left, x
        self.update_height(x); self.update_height(y)
        return y

    def _rebalance(self, node, operation):
        self.update_height(node)
        balance = self.get_balance(node)
        if abs(balance) <= 1: return node
        record = self.trace_enabled and len(self.rotation_log) < self.trace_limit
        before = self.snapshot(node) if record else None
        pivot = node.key
        if balance > 1:
            kind = "LR" if self.get_balance(node.left)<0 else "LL"
            if kind == "LR": node.left = self.rotate_left(node.left)
            node = self.rotate_right(node)
        else:
            kind = "RL" if self.get_balance(node.right)>0 else "RR"
            if kind == "RL": node.right = self.rotate_right(node.right)
            node = self.rotate_left(node)
        if record:
            self.rotation_log.append({"kind":kind,"pivot":pivot,"operation":operation,
                                      "before":before,"after":self.snapshot(node)})
        return node

    def insert(self, key, room=None):
        if room is None: room, key = key, (getattr(key,self.index),key.room_id)
        if key != (getattr(room,self.index),room.room_id): raise ValueError("Key tidak cocok dengan indeks ruangan.")
        self.root = self._insert(self.root,key,room)

    def _insert(self, node, key, room):
        self.node_accesses += 1
        if node is None: return AVLNode(key,room)
        if key == node.key: node.room=room; return node
        if key < node.key: node.left=self._insert(node.left,key,room)
        else: node.right=self._insert(node.right,key,room)
        return self._rebalance(node,"insert")

    def search(self, key):
        node=self.root
        while node:
            self.node_accesses += 1
            if key == node.key: return node.room
            node=node.left if key<node.key else node.right
        return None

    def in_order_traversal(self):
        result, stack, node = [], [], self.root
        while node or stack:
            while node:
                self.node_accesses += 1; stack.append(node); node=node.left
            node=stack.pop(); result.append(node.room); node=node.right
        return result

    def inorder(self): return self.in_order_traversal()

    def find_suitable_room(self, participants):
        if self.index!="capacity": raise ValueError("Gunakan indeks capacity.")
        if type(participants) is not int or participants<=0: raise ValueError("Peserta harus bilangan bulat positif.")
        node, candidate=self.root,None
        while node:
            self.node_accesses += 1
            if node.room.capacity>=participants: candidate,node=node.room,node.left
            else: node=node.right
        return candidate

    def ceiling_capacity(self, participants): return self.find_suitable_room(participants)

    def delete(self, key):
        def remove(node,target):
            self.node_accesses += 1
            if node is None: return None,False
            if target<node.key: node.left,found=remove(node.left,target)
            elif target>node.key: node.right,found=remove(node.right,target)
            else:
                found=True
                if node.left is None: return node.right,True
                if node.right is None: return node.left,True
                successor=node.right
                while successor.left:
                    self.node_accesses += 1; successor=successor.left
                node.key,node.room=successor.key,successor.room
                node.right,_=remove(node.right,successor.key)
            return (self._rebalance(node,"delete"),True) if found else (node,False)
        self.root,found=remove(self.root,key)
        return found

    def top_k_utilization(self,k):
        if self.index!="utilization": raise ValueError("Gunakan indeks utilization.")
        if type(k) is not int or k<0: raise ValueError("k harus bilangan bulat tidak negatif.")
        result,stack,node=[],[],self.root
        while (node or stack) and len(result)<k:
            while node:
                self.node_accesses += 1; stack.append(node); node=node.right
            node=stack.pop();result.append(node.room);node=node.left
        return result

    def validate(self):
        def visit(node,low=None,high=None):
            if node is None: return 0
            assert low is None or low<node.key
            assert high is None or node.key<high
            assert node.key==(getattr(node.room,self.index),node.room.room_id)
            left,right=visit(node.left,low,node.key),visit(node.right,node.key,high)
            assert node.height==1+max(left,right) and abs(left-right)<=1
            return node.height
        visit(self.root)
        return True

    def check_avl(self): return self.validate()

    def check_balance(self): return self.validate()
