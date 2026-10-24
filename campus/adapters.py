"""Read-only view containers; all algorithm operations remain Colab definitions."""
from .hash_table import HashTableChaining
from .avl import AVLTree


class RoomView:
    def __init__(self, rooms):
        self.table = HashTableChaining()
        self.capacity = AVLTree("capacity")
        self.usage = AVLTree("utilization")
        for room in rooms:
            self.table.put(room.room_id, room)
            self.capacity.insert(room)
            self.usage.insert(room)

    def validate(self):
        return self.capacity.validate() and self.usage.validate()
