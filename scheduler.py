import copy
import math

import customexceptions
import gahandler
import ordermanager
import utils
import pygad


class Scheduler:
    def __init__(self, robots: dict, shelves: dict, goals: dict, homes:dict, init_orders: list, schedule_mode:str,
                 fault_tolerant_mode: bool):
        self._fault_tolerant_mode = fault_tolerant_mode
        self._robots = robots
        self._num_robots = len(robots.keys())
        self._shelves = shelves
        self._item_to_shelf_mapping = {}
        self._shelf_to_item_mapping = {}
        self._schedule_mode = schedule_mode

        if schedule_mode not in ["simple", "simple-interrupt"]:
            raise customexceptions.SimulationError("Invalid scheduling mode provided")

        for shelf_name, shelf in self._shelves.items():
            item_name = shelf.get_item().get_name()
            self._shelf_to_item_mapping[shelf_name] = shelf.get_item()

            if item_name not in self._item_to_shelf_mapping.keys():
                self._item_to_shelf_mapping[item_name] = [shelf_name]
            else:
                self._item_to_shelf_mapping[item_name] = self._item_to_shelf_mapping[item_name].append(shelf_name)

        self._goals = goals
        self._homes = homes

        self._ROBOTINVSIZE = 3

        self._orders_backlog = []
        self._orders_backlog.extend(init_orders)

        self._orders_active = []

        self._order_robot_assignment = {}
        self._order_goal_assignment = {}

        self._schedule = {}

        self._all_positions = {}
        self._all_genes = []
        self._all_distances = {}

        for robot_name, robot_obj in self._robots.items():
            self._all_positions[robot_name] = robot_obj.get_position()
            self._all_genes.append(robot_name)

        for shelf_name, shelf_obj in self._shelves.items():
            if shelf_name not in ["shelf0","shelf5","shelf6","shelf7","shelf8","shelf9"]:
                self._all_positions[shelf_name] = shelf_obj.get_position()
                self._all_genes.append(shelf_name)

        for goal_name, goal_obj in self._goals.items():
            if goal_name == "goal0":
                self._all_positions[goal_name] = goal_obj.get_position()
                for i in range(self._ROBOTINVSIZE):
                    self._all_genes.append("%s|%s" % (goal_name, i+1))

        for location1 in self._all_positions.keys():
            for location2 in self._all_positions.keys():
                if (location2, location1) not in self._all_distances.keys():
                    if location1 != location2:
                        x1 = self._all_positions[location1][0]
                        y1 = self._all_positions[location1][1]

                        x2 = self._all_positions[location2][0]
                        y2 = self._all_positions[location2][1]

                        self._all_distances[(location1, location2)] = utils.taxicab_dist(x1,y1,x2,y2)


        h = gahandler.GAHandler.get_instance()
        for i in range(10):
            self._all_genes.append("wait")
        h.set_genes(self._all_genes)
        h.set_distance_graph(self._all_distances)
        h.set_shelf_item_mapping(self._shelf_to_item_mapping)
        h.set_orders_to_fulfill([["item1","item2","item3","item4"]])

        test_solution = ["robot0", "shelf1", "wait", "wait", "wait", "wait","wait", "wait", "wait", "wait", "wait", "goal1|1", "robot1", "shelf2", "goal1|1", "robot2", "shelf3", "goal1|1", "robot3", "shelf4", "goal1|1"]
        encoded_solution = []
        for gene in test_solution:
            encoded_solution.append(gahandler.encode_string_utf8_to_int(gene))

        num_parents_mating = 50
        num_genes = 15
        gene_type = int
        gene_space = h.get_int_genes()
        fitness_func = gahandler.fitness_func
        num_generations = 100

        ga_instance = pygad.GA(num_generations=num_generations,
                               num_genes=num_genes,
                               gene_type=gene_type,
                               gene_space=gene_space,
                               sol_per_pop=300,
                               fitness_func=fitness_func,
                               num_parents_mating=num_parents_mating,
                               mutation_by_replacement=True)

        #ga_instance.run()


        #solution, solution_fitness, solution_idx = ga_instance.best_solution()
        #print("best:")
        #for gene in solution:
        #    print(gahandler.decode_utf8_int_to_string(gene))

        #ga_instance.plot_fitness()

        #raise Exception("break")


    def schedule(self):
        if self._schedule_mode == "simple":
            self.simple_single_robot_schedule()
        elif self._schedule_mode == "simple-interrupt":
            self.single_interrupt_robot_schedule()

    def get_items_already_delivered_for_order(self, order):
        order_goal_name = self._order_goal_assignment[order.get_id()]
        order_goal = self._goals[order_goal_name]
        return order_goal.report_inventory()

    def simple_single_robot_schedule(self, single_item_mode=False):
        break_outer_loop = False
        orders_to_move = []
        # For every order in the backlog (sorted by priority)
        for order in reversed(sorted(self._orders_backlog, key=lambda order1: order1.get_prio())):
            for robot_name, robot in self._robots.items():
                # Check whether there is a free robot to take it
                if robot_name not in self._order_robot_assignment.values():
                    for goal_name, goal in self._goals.items():

                        # Check whether there is a free goal to take it
                        if goal_name not in self._order_goal_assignment.values():

                            self._order_robot_assignment[order.get_id()] = robot_name
                            robot.set_prio(order.get_prio())
                            print("order %s assigned to robot %s" % (order.get_id(), robot_name))

                            self._order_goal_assignment[order.get_id()] = goal_name

                            if single_item_mode:
                                for item in reversed(sorted(order.get_items(), key=lambda itm: itm.get_dependency())):
                                    if item.get_name() not in self._item_to_shelf_mapping.keys():
                                        message = "Scheduling impossible, no shelf exists for item %s" % item.get_name()
                                        raise customexceptions.SimulationError(message)
                                    shelf_name = self._item_to_shelf_mapping[item.get_name()][0]
                                    self.add_to_schedule(robot_name, shelf_name)
                                    self.add_to_schedule(robot_name, goal_name)

                            if not single_item_mode:
                                robot_inventory_used = 0
                                for item in reversed(sorted(order.get_items(), key=lambda itm: itm.get_dependency())):
                                    if item.get_name() not in self._item_to_shelf_mapping.keys():
                                        message = "Scheduling impossible, no shelf exists for item %s" % item.get_name()
                                        raise customexceptions.SimulationError(message)
                                    shelf_name = self._item_to_shelf_mapping[item.get_name()][0]
                                    if robot_inventory_used == self._ROBOTINVSIZE:
                                        self.add_to_schedule(robot_name, goal_name)
                                        robot_inventory_used = 0
                                    self.add_to_schedule(robot_name, shelf_name)
                                    robot_inventory_used = robot_inventory_used + 1

                                self.add_to_schedule(robot_name, goal_name)
                            print("its complete schedule is %s" % self._schedule[robot_name])
                            orders_to_move.append(order)
                            break_outer_loop = True
                            break

                if break_outer_loop:
                    break_outer_loop = False
                    break

        for ordr in orders_to_move:
            self._orders_backlog.remove(ordr)
            self._orders_active.append(ordr)

    def single_interrupt_robot_schedule(self):
        orders_to_move = []
        for order in reversed(sorted(self._orders_backlog, key=lambda order1: order1.get_prio())):
            free_robot_obj = None
            free_goal_obj = None

            for robot_name, robot in self._robots.items():
                # Check whether there is a free robot to take the order
                if robot_name not in self._order_robot_assignment.values():
                    free_robot_obj = robot

            for goal_name, goal in self._goals.items():
                # Check whether there is a free goal to take it
                if goal_name not in self._order_goal_assignment.values():
                    free_goal_obj = goal

            if (free_robot_obj is not None) and (free_goal_obj is not None):
                robot_name = free_robot_obj.get_name()
                goal_name = free_goal_obj.get_name()

                self._order_robot_assignment[order.get_id()] = robot_name
                free_robot_obj.set_prio(order.get_prio())
                print("order %s assigned to robot %s" % (order.get_id(), robot_name))

                self._order_goal_assignment[order.get_id()] = goal_name

                robot_inventory_used = 0
                for item in reversed(sorted(order.get_items(), key=lambda itm: itm.get_dependency())):
                    if item.get_name() not in self._item_to_shelf_mapping.keys():
                        message = "Scheduling impossible, no shelf exists for item %s" % item.get_name()
                        raise customexceptions.SimulationError(message)
                    shelf_name = self._item_to_shelf_mapping[item.get_name()][0]
                    if robot_inventory_used == self._ROBOTINVSIZE:
                        self.add_to_schedule(robot_name, goal_name)
                        robot_inventory_used = 0
                    self.add_to_schedule(robot_name, shelf_name)
                    robot_inventory_used = robot_inventory_used + 1

                self.add_to_schedule(robot_name, goal_name)
                print("its complete schedule is %s" % self._schedule[robot_name])
                orders_to_move.append(order)

            elif free_robot_obj is None and free_goal_obj is not None:
                found_lower_prio_robot_name = None
                lowest_prio_found = order.get_prio()

                for order_id, robot_name in self._order_robot_assignment.items():
                    robot_obj = self._robots[robot_name]
                    robot_prio = robot_obj.get_prio()

                    if robot_prio < lowest_prio_found:
                        target_good = False
                        inventory_usage_good = False

                        if robot_obj.get_target() is None:
                            target_good = True
                        else:
                            # We don't want a robot with a shelf as its target as its inventory size will increase
                            # by one and invalidate the following calculations
                            if "shelf" not in robot_obj.get_target().get_name():
                                target_good = True

                        if robot_obj.get_inventory_usage() != 0:
                            if robot_obj.get_inventory_usage() != self._ROBOTINVSIZE:
                                if order.get_highest_item_dep() <= robot_obj.peek_inventory().get_dependency():
                                    inventory_usage_good = True
                        else:
                            inventory_usage_good = True

                        if inventory_usage_good and target_good:
                            lowest_prio_found = robot_prio
                            found_lower_prio_robot_name = robot_name

                if found_lower_prio_robot_name is not None:
                    print("entering")
                    print("Order ID is %s" % order.get_id())
                    print("New goal is %s" % free_goal_obj.get_name())
                    selected_bot = self._robots[found_lower_prio_robot_name]
                    print(selected_bot.get_inventory_usage())
                    self._order_robot_assignment[order.get_id()] = found_lower_prio_robot_name
                    selected_bot.set_prio(order.get_prio())
                    self._order_goal_assignment[order.get_id()] = free_goal_obj.get_name()

                    robot_inventory_already_used = selected_bot.get_inventory_usage()

                    prepend_schedule = []
                    robot_inventory_used_for_this_order = 0
                    for item in reversed(sorted(order.get_items(), key=lambda itm: itm.get_dependency())):
                        if item.get_name() not in self._item_to_shelf_mapping.keys():
                            message = "Scheduling impossible, no shelf exists for item %s" % item.get_name()
                            raise customexceptions.SimulationError(message)
                        shelf_name = self._item_to_shelf_mapping[item.get_name()][0]
                        if robot_inventory_used_for_this_order == self._ROBOTINVSIZE - robot_inventory_already_used:
                            prepend_schedule.append("%s|%s" % (free_goal_obj.get_name(),
                                                               robot_inventory_used_for_this_order))
                            robot_inventory_used_for_this_order = 0
                        prepend_schedule.append(shelf_name)
                        robot_inventory_used_for_this_order = robot_inventory_used_for_this_order + 1

                    prepend_schedule.append("%s|%s" % (free_goal_obj.get_name(), robot_inventory_used_for_this_order))

                    self.prepend_to_schedule(found_lower_prio_robot_name, prepend_schedule)

                    print("Interruption schedule complete for robot %s is %s" % (found_lower_prio_robot_name, self._schedule[found_lower_prio_robot_name]))
                    orders_to_move.append(order)

        for ordr in orders_to_move:
            self._orders_backlog.remove(ordr)
            self._orders_active.append(ordr)

    def add_to_schedule(self, robot_name, target_name):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name].append(target_name)

    def prepend_to_schedule(self, robot_name, targets_list):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name] = targets_list + self._schedule[robot_name]

    def add_order(self, order):
        self._orders_backlog.append(order)
        self.schedule()

    def direct_robot(self, robot_obj):
        robot_name = robot_obj.get_name()
        if robot_name in self._schedule.keys():
            # We shouldn't do anything if the scheduler has nothing more for this robot
            if self._schedule[robot_name]:
                robot_next_target_name = self._schedule[robot_name].pop(0)
                print("Robot %s directed to %s" % (robot_name,robot_next_target_name))
                print("Schedule remaining: %s" % self._schedule[robot_name])
                robot_next_target_obj = None
                if "shelf" in robot_next_target_name:
                    robot_next_target_obj = self._shelves[robot_next_target_name]
                elif "goal" in robot_next_target_name:
                    if "|" in robot_next_target_name:
                        print(robot_next_target_name)
                        goal_name = robot_next_target_name.split("|")[0]
                        amount_items = int(robot_next_target_name.split("|")[1])

                        robot_next_target_obj = self._goals[goal_name]
                        robot_obj.set_amount_of_items_to_transfer_next_time(amount_items)
                    else:
                        robot_next_target_obj = self._goals[robot_next_target_name]
                elif "home" in robot_next_target_name:
                    robot_next_target_obj = self._homes[robot_next_target_name]

                if robot_next_target_obj is None:
                    message = "Invalid target %s in schedule for robot %s" % (robot_next_target_name, robot_name)
                    raise customexceptions.SimulationError(message)

                robot_obj.set_target(robot_next_target_obj)

    def are_all_orders_complete(self):
        if self._orders_backlog:
            return False
        if self._orders_active:
            return False
        return True

    def is_this_a_complete_order(self, items: list, goal, ordermanagr: ordermanager.OrderManager, step_ctr):
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

            if len(comp_items) == 0 and goal.get_name_last_robot() == self._order_robot_assignment[order.get_id()]:

                self._orders_active.remove(order)

                robot_name = self._order_robot_assignment.pop(order.get_id())
                self._order_goal_assignment.pop(order.get_id())
                print("Order %s completed by robot %s" % (order.get_id(), robot_name))
                print("order %s complete" % order.get_id())
                ordermanagr.set_order_completion_time(order, step_ctr)

                # homeN is robotN's home
                print("setting %s to return home" % robot_name)
                self._robots[robot_name].set_target(self._homes["home%s" % robot_name[5:]])

                self.schedule()

                return True
        return False














