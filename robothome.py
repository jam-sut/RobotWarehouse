class RobotHome:
    def __init__(self, home_name: str, robot_name: str, x: int, y: int):
        self._x = x
        self._y = y
        self._name = home_name
        self._robot_name = robot_name

    def interact(self, obj):
        print("Robot %s returned home" % obj.get_name())
        if obj.get_name() != self._robot_name:
            print("That wasnt the expected robot %s for home expecting %s" % (obj.get_name(), self._robot_name))
        return

    def get_name(self):
        return self._name

    def get_position(self):
        return self._x, self._y

