import customexceptions
import order
import entitywithinventory
import udptransmit
import math


class OrderStation(entitywithinventory.InventoryEntity):
    def __init__(self, x_pos: int, y_pos: int, name: str):
        self._x = x_pos
        self._y = y_pos
        self._currentOrder = None
        self._last_robot_interacted = None
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
        recieved = obj.transfer_inventory()
        print("Order station %s recieved %s" % (self.get_name(), recieved))
        print("Already had %s" % self._inventory)
        self._last_robot_interacted = obj.get_name()
        if len(recieved) == 0:
            raise customexceptions.SimulationError("INVENTORY SIZE zero transferred")
        self.receive_inventory(recieved)

    def get_position(self):
        return self._x, self._y

    def get_name_last_robot(self):
        return self._last_robot_interacted

    def get_name(self):
        return self._name

    def __repr__(self):
        return self._name
