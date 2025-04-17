import random

import udptransmit
import entitywithinventory
import shelf
import orderstation
import customexceptions

class Robot(entitywithinventory.InventoryEntity):
    def __init__(self, name: str, x: int, y: int, max_inv_size: int, fault_rates: list):
        self._x = x
        self._y = y
        self.wait_steps = 0
        self._movement_path = []
        self._current_target = None
        self._steps_halted = 0
        self._prio = None

        self.battery_fault_rate = fault_rates[0]
        self.sensor_fault_rate = fault_rates[1]
        self.actuator_fault_rate = fault_rates[2]

        self.battery_faulted = False
        self.sensors_faulted = False
        self.actuators_faulted = False

        super().__init__(name, max_inv_size)

    def get_position(self):
        return self._x, self._y

    def set_prio(self, prio):
        self._prio = prio

    def get_prio(self):
        return self._prio

    def set_wait_steps(self, step_amount):
        self.wait_steps = step_amount

    def get_wait_steps(self):
        return self.wait_steps

    def decrement_wait_steps(self):
        self.wait_steps = self.wait_steps - 1

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
        if target is None:
            self._prio = None

    def get_target(self):
        return self._current_target

    def interact_with_target(self):
        print("interacting with %s" % self._current_target)
        if self.get_position() != self._current_target.get_position():
            message = "Robot %s tried to interact with object %s, when they were not occupying the same cell."
            raise customexceptions.SimulationError(message % (self._name, self._current_target.get_name()))

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

    def maybe_introduce_fault(self):
        if random.random() < self.battery_fault_rate:
            self.battery_faulted = True
        if random.random() < self.actuator_fault_rate:
            self.actuators_faulted = True
        if random.random() < self.sensor_fault_rate:
            self.sensors_faulted = True

    def __repr__(self):
        return self._name
