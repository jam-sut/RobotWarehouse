import item
import math

import udptransmit
import copy

# Models an entity with a LIFO stack inventory, where items within the stack must follow a dependency
class InventoryEntity:
    def __init__(self, name: str, max_inventory_size):
        self._name = name
        self._inventory = []
        self.last_item_dep = math.inf
        self._max_inv = max_inventory_size

    def add_item_to_inventory(self, item_to_add: item.Item) -> bool:
        new_dep = item_to_add.get_dependency()
        if new_dep <= self.last_item_dep:
            self._inventory.append(item_to_add)
            self.last_item_dep = new_dep
            udptransmit.transmit_item_gained(self._name, item_to_add.get_name())
            return True
        else:
            return False

    def pop_item_from_inventory(self) -> item.Item:
        popped_item = self._inventory.pop()
        if popped_item is not None:
            udptransmit.transmit_item_lost(self._name, popped_item.get_name())
            if len(self._inventory) == 0:
                self.last_item_dep = math.inf
            else:
                self.last_item_dep = self._inventory[-1].get_dependency()
        return popped_item

    def transfer_inventory(self):
        inventory_copy = copy.deepcopy(self._inventory)
        self._inventory = []
        udptransmit.transmit_clear_inventory(self._name)
        self.last_item_dep = math.inf
        return inventory_copy

    def receive_inventory(self, items):
        for itm in reversed(items):
            if not self.add_item_to_inventory(itm):
                raise "ITEM DEPENDENCY FAILED"

    def clear_inventory(self):
        self._inventory = []
        udptransmit.transmit_clear_inventory(self._name)
        self.last_item_dep = math.inf

    # For each item in the inventory
    # The dependency number must be smaller than any item previously
    # Returns false if dependency check fails, true otherwise
    def validate_complete_inventory(self) -> bool:
        previous = math.inf
        for itm in self._inventory:
            current = itm.get_dependency()
            if current <= previous:
                previous = current
            else:
                return False
        return True

    def report_inventory(self):
        return copy.deepcopy(self._inventory)
