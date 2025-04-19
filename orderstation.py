import customexceptions
import entitywithinventory
import udptransmit
import math


class OrderStation(entitywithinventory.InventoryEntity):
    def __init__(self, x_pos: int, y_pos: int, name: str, warehouse):
        self._x = x_pos
        self._y = y_pos
        self._currentOrder = None
        self._last_robot_interacted = None
        self._warehouse_ref = warehouse
        super().__init__(name, math.inf)

    def transmit_creation(self):
        udptransmit.transmit_goal_creation(self._name, self._x, self._y)

    def interact(self, obj):
        received = obj.transfer_inventory()
        print("Order station %s recieved %s" % (self.get_name(), received))
        print("Already had %s" % self._inventory)
        self._last_robot_interacted = obj.get_name()
        if len(received) == 0:
            raise customexceptions.SimulationError("INVENTORY SIZE zero transferred")
        self.receive_inventory(received)

        if self._warehouse_ref.get_scheduler().is_this_a_complete_order(self.report_inventory(),
                                                                        self._warehouse_ref.get_order_manager(),
                                                                        obj.get_name(),
                                                                        self._name,
                                                                        self._warehouse_ref.get_total_steps()):
            self.clear_inventory()

    def get_position(self):
        return self._x, self._y

    def get_name_last_robot(self):
        return self._last_robot_interacted

    def get_name(self):
        return self._name

    def __repr__(self):
        return self._name
