import copy


class Scheduler:
    def __init__(self, robots: dict, shelves: dict, goals: dict, init_orders: list):
        self._robots = robots
        self._num_robots = len(robots.keys())
        self._shelves = shelves
        self._goals = goals

        self._orders_backlog = []
        self._orders_backlog.extend(init_orders)

        self._orders_active = []

        self._order_robot_assignment = {}
        self._order_goal_assignment = {}

        self._schedule = {}

        self.orders_can_complete = False
        self.orders_complete = False

    def simple_single_robot_schedule(self):
        print("Current backlog is")
        for ordr in self._orders_backlog:
            print(ordr.get_id())
        print("Current active is")
        for ordr in self._orders_active:
            print(ordr.get_id())

        break_outer_loop = False
        orders_to_move = []
        if len(self._orders_backlog) != 0 and not self.orders_can_complete:
            # For every order in the backlog
            for order in self._orders_backlog:
                #print("Considering order %s" % order.get_id())
                for robot_name, robot in self._robots.items():
                    # Check whether there is a free robot to take it
                    if robot_name not in self._order_robot_assignment.values():
                        for goal_name, goal in self._goals.items():

                            # Check whether there is a free goal to take it
                            if goal_name not in self._order_goal_assignment.values():

                                #print("Scheduling a robot")
                                self._order_robot_assignment[order.get_id()] = robot_name
                                self._order_goal_assignment[order.get_id()] = goal_name

                                for item in reversed(sorted(order.get_items(), key=lambda itm: itm.get_dependency())):
                                    found = False
                                    for shelf in self._shelves.values():
                                        if shelf.get_item() == item:
                                            self.add_to_schedule(robot_name, shelf.get_name())
                                            found = True
                                    if not found:
                                        raise ValueError("ERROR")
                                    self.add_to_schedule(robot_name, goal_name)

                                orders_to_move.append(order)
                                break_outer_loop = True
                                break

                    if break_outer_loop:
                        break_outer_loop = False
                        break

            for ordr in orders_to_move:
                self._orders_backlog.remove(ordr)
                self._orders_active.append(ordr)
        print("After scheduling, the")
        print("Current backlog is")
        for ordr in self._orders_backlog:
            print(ordr.get_id())
        print("Current active is")
        for ordr in self._orders_active:
            print(ordr.get_id())

    def add_to_schedule(self, robot_name, target_name):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name].append(target_name)

    def direct_robot(self, robot_obj):
        robot_name = robot_obj.get_name()
        if robot_name in self._schedule.keys():
            if self._schedule[robot_name]:
                robot_next_target_name = self._schedule[robot_name].pop(0)
                robot_next_target_obj = None
                if "shelf" in robot_next_target_name:
                    robot_next_target_obj = self._shelves[robot_next_target_name]
                elif "goal" in robot_next_target_name:
                    robot_next_target_obj = self._goals[robot_next_target_name]

                if robot_next_target_obj is None:
                    print("INVALID TARGET IN SCHEDULE")
                    print(robot_next_target_name)

                print("setting robot %s target %s" % (robot_name, robot_next_target_name))

                robot_obj.set_target(robot_next_target_obj)

    def are_all_orders_complete(self):
        if self._orders_backlog:
            return False
        if self._orders_active:
            return False
        return True

    def is_this_a_complete_order(self, items: list):
        for order in self._orders_active:
            comp_items = copy.deepcopy(items)
            should_continue = False
            for order_item in order.get_items():
                if order_item not in comp_items:
                    should_continue = True
                    break
                else:
                    comp_items.remove(order_item)

            if should_continue:
                continue

            if len(comp_items) == 0:
                print("Complete order detected")
                self._orders_active.remove(order)

                self._order_robot_assignment.pop(order.get_id())
                self._order_goal_assignment.pop(order.get_id())

                self.simple_single_robot_schedule()

                return True
        return False


    def print_status(self):
        print("The current schedule is: ")
        print(self._schedule)
        for robot, ident in self._order_robot_assignment.items():
            print("Robot %s is assigned to order %s" % (robot, ident))
        print("The backlog is: ")
        print(self._orders_backlog)
        print("The goals are: ")
        print(self._goals)










