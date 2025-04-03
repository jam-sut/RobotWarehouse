import udptransmit
import entitywithinventory
import shelf
import orderstation


class Robot(entitywithinventory.InventoryEntity):
    def __init__(self, name: str, x: int, y: int, max_inv_size: int):
        self._x = x
        self._y = y
        self._movement_path = []
        self._current_target = None
        self._steps_halted = 0
        super().__init__(name, max_inv_size)

    def get_position(self):
        return self._x, self._y

    def set_position(self, x, y):
        self._steps_halted = 0
        self._x = x
        self._y = y

    def increment_steps_halted(self):
        self._steps_halted = self._steps_halted + 1
        if self._steps_halted > 10:
            self._steps_halted = 0

    def get_steps_halted(self):
        return self._steps_halted

    def set_movement_path(self, path):
        self._movement_path = path

    def get_movement_path(self):
        return self._movement_path

    def set_target(self, target):
        self._current_target = target

    def get_target(self):
        return self._current_target

    def interact_with_target(self):
        print("interacting with %s" % self._current_target)
        self._current_target.interact(self)
        self._current_target = None

    def is_at_target(self):
        if self._current_target is None:
            return False

        target_x, target_y = self._current_target.get_position()
        if (self._x == target_x) and (self._y == target_y):
            return True
        else:
            return False

    def get_name(self):
        return self._name

    def transmit_creation(self):
        udptransmit.transmit_robot_creation(self._name, self._x, self._y)

    def transmit_position(self):
        udptransmit.transmit_robot_position(self._name, self._x, self._y)

    def interact_with_shelf(self, shelf_obj: shelf.Shelf):
        self.add_item_to_inventory(shelf_obj.get_item())

    def interact_with_order_station(self, station_obj: orderstation.OrderStation):
        station_obj.add_item_to_inventory(self.pop_item_from_inventory())

    def __repr__(self):
        return self._name
