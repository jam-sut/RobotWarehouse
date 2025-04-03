import order
import entitywithinventory
import udptransmit
import math


class OrderStation(entitywithinventory.InventoryEntity):
    def __init__(self, x_pos: int, y_pos: int, name: str):
        self._x = x_pos
        self._y = y_pos
        self._currentOrder = None
        super().__init__(name, math.inf)

    def transmit_creation(self):
        udptransmit.transmit_goal_creation(self._name, self._x, self._y)

    def assign_order(self, order_to_assign: order.Order):
        self._currentOrder = order_to_assign

    def verify_if_order_complete(self):
        if self._inventory.sorted() == self._currentOrder.get_items().sorted():
            return True
        else:
            return False

    def interact(self, obj):
        print("Goal has %s before" % self._inventory)
        self.receive_inventory(obj.transfer_inventory())
        print("Goal has %s now" % self._inventory)
    def get_position(self):
        return self._x, self._y

    def __repr__(self):
        return self._name
