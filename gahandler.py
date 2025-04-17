import customexceptions
import copy
import math
import entitywithinventory


def encode_string_utf8_to_int(string1):
    bytes_value = string1.encode('utf-8')
    int_value = int.from_bytes(bytes_value, 'little')
    return int_value


def decode_utf8_int_to_string(int1):
    int_val = int(int1)
    recovered_bytes = int_val.to_bytes((int_val.bit_length() + 7) // 8, 'little')
    recovered_string = recovered_bytes.decode('utf-8')
    return recovered_string

def return_equivalent_full_order(orders, inventory):
    for order in orders:
        if len(order) != len(inventory):
            continue

        comp_items = copy.deepcopy(inventory)
        should_continue = False
        for order_item in order:
            if order_item not in comp_items:
                should_continue = True
                break
            else:
                comp_items.remove(order_item)

        if should_continue:
            continue

        return order

def return_how_close(orders, inventories):
    order_size = len(orders[0])
    total_items = order_size * len(orders)
    correct_ctr = 0

    for order in orders:
        for inventory in inventories:
            comp_items = copy.deepcopy(inventory)
            should_break = False

            for order_item in order:
                if order_item in comp_items:
                    correct_ctr += 1
                    comp_items.remove(order_item)
                    should_break = True
                else:
                    correct_ctr -= 1
            if should_break:
                break

    return (float(correct_ctr) / total_items)



def schedules_have_not_completed(schedules):
    for schedule in schedules:
        if not is_schedule_complete(schedule):
            return True
    return False

def is_schedule_complete(schedule):
    if schedule[2] == len(schedule[1]):
        return True
    return False

def fitness_func(ga_instance, solution, solution_idx):
    class MockRobot(entitywithinventory.InventoryEntity):
        def __init__(self, name, inv_size):
            super().__init__(name, inv_size, False)

    class MockGoal(entitywithinventory.InventoryEntity):
        def __init__(self, name):
            super().__init__(name, math.inf, False)

    handler = GAHandler.get_instance()
    solution_decoded = []
    for int_gene in solution:
        decoded = decode_utf8_int_to_string(int_gene)
        if decoded not in handler.get_all_string_genes():
            raise customexceptions.SimulationError("Invalid gene in solution %s" % decoded)
        solution_decoded.append(decoded)

    #print(solution_decoded)
    robot_indices = []
    goals_in_solution = []
    robot_counter = {}
    orders_to_fulfill = copy.deepcopy(handler.get_orders())
    item_mapping = handler.get_shelf_item_mapping()

    ctr = 0
    for string_gene in solution_decoded:
        if "robot" in string_gene:
            robot_indices.append(ctr)
            if string_gene not in robot_counter.keys():
                robot_counter[string_gene] = 1
            else:
                return -10
        if "goal" in string_gene:
            if string_gene.split("|")[0] not in goals_in_solution:
                goals_in_solution.append(string_gene.split("|")[0])
        ctr = ctr + 1

    if not robot_indices:
        return -10

    if "robot" not in solution_decoded[0]:
        return -10


    robot_indices.append(len(solution_decoded))

    robot_schedules_sep = []
    for i in range(len(robot_indices)-1):
        robot_schedules_sep.append(solution_decoded[robot_indices[i]:robot_indices[i+1]])

    goalctrs = {}
    for schedule in robot_schedules_sep:
        if len(schedule) == 1:
            return -9
        found = False
        for place in schedule:
            if "goal" in place:
                if place.split("|")[0] not in goalctrs.keys():
                    goalctrs[place.split("|")[0]] = 1
                else:
                    goalctrs[place.split("|")[0]] += 1
                found = True
        if not found:
            return -8

    if len(goalctrs.keys()) > len(orders_to_fulfill):
        return -8

    mock_robots = []
    mock_goals = {}
    robots_distance_accumulated = []
    robots_last_actual_location = []

    for robot in robot_schedules_sep:
        mock_robots.append(MockRobot(robot[0], handler.get_max_inventory()))
        robots_distance_accumulated.append(0)
        robots_last_actual_location.append(None)

    for goal in goals_in_solution:
        mock_goals[goal] = MockGoal(goal)


    robot_ctr = 0
    schedules_with_execution_progress = []
    for schedule in robot_schedules_sep:
        # [robot id, schedule, progress]
        schedules_with_execution_progress.append([robot_ctr, schedule, 0])
        robot_ctr += 1

    while schedules_have_not_completed(schedules_with_execution_progress):
        smallest_time = math.inf
        smallest_sched = None
        for schedule in schedules_with_execution_progress:
            if robots_distance_accumulated[schedule[0]] < smallest_time and not is_schedule_complete(schedule):
                smallest_time = robots_distance_accumulated[schedule[0]]
                smallest_sched = schedule

        target = smallest_sched[1][smallest_sched[2]]
        robot_id = smallest_sched[0]

        if "shelf" in target:
            try:
                mock_robots[robot_id].add_item_to_inventory(item_mapping[target])
            except customexceptions.SimulationError:
                return -5

        elif "goal" in target:
            goal_name = target.split("|")[0]
            amount_items = int(target.split("|")[1])
            mock_robots[robot_id].set_amount_of_items_to_transfer_next_time(amount_items)
            try:
                mock_goals[goal_name].receive_inventory(mock_robots[robot_id].transfer_inventory())
            except customexceptions.SimulationError as e:
                return -5

            order1 = return_equivalent_full_order(orders_to_fulfill,
                                                  mock_goals[goal_name].report_inventory_item_names())
            if order1 is not None:
                orders_to_fulfill.remove(order1)

        smallest_sched[2] = smallest_sched[2] + 1

        if not is_schedule_complete(smallest_sched):
            next_target = smallest_sched[1][smallest_sched[2]]

            new_accumulated_dist = 0

            if "goal" in target:
                target_name = target.split("|")[0]
            else:
                target_name = target

            if "goal" in next_target:
                next_target_name = next_target.split("|")[0]
            else:
                next_target_name = next_target

            if ("wait" != next_target) and ("wait" != target):
                new_accumulated_dist = handler.get_distance_between(target_name, next_target_name)

            if ("wait" == target) and ("wait" != next_target):
                new_accumulated_dist = handler.get_distance_between(robots_last_actual_location[robot_id], next_target_name)

            if (next_target == "wait") and (target_name != "wait"):
                new_accumulated_dist = 1
                robots_last_actual_location[robot_id] = target_name
            robots_distance_accumulated[robot_id] += new_accumulated_dist

    if len(orders_to_fulfill) != 0:
        #print("Not all orders were completed")
        inventories = []
        for goal in mock_goals.values():
            inventories.append(goal.report_inventory_item_names())
        return return_how_close(orders_to_fulfill, inventories)

    print("SUCCESS")

    for robot in mock_robots:
        if robot.get_inventory_usage() != 0:
            print("Some robots didnt use their inventory to full efficiency")
            return 1 + 1.0 / max(robots_distance_accumulated)

    return 1.5 + 1.0 / max(robots_distance_accumulated)



class GAHandler:
    instance = None

    @staticmethod
    def get_instance():
        if GAHandler.instance is None:
            GAHandler.instance = GAHandler()
        return GAHandler.instance

    def __init__(self):
        self._all_gene_strings = []
        self._all_gene_ints = []
        self._shelf_item_mapping = {}
        self._orders = []
        self._robot_max_inv = 3
        self._distance_graph = {}

    def set_genes(self, all_gene_strings):
        self._all_gene_strings = all_gene_strings
        for string1 in self._all_gene_strings:
            self._all_gene_ints.append(encode_string_utf8_to_int(string1))

    def get_int_genes(self):
        return self._all_gene_ints
    def set_distance_graph(self, graph):
        self._distance_graph = graph

    def set_shelf_item_mapping(self, mapping):
        self._shelf_item_mapping = mapping

    def get_shelf_item_mapping(self):
        return self._shelf_item_mapping

    def set_orders_to_fulfill(self, orders):
        self._orders = orders

    def get_all_string_genes(self):
        return self._all_gene_strings

    def get_orders(self):
        return self._orders

    def get_max_inventory(self):
        return self._robot_max_inv

    def get_distance_between(self, name1, name2):
        if name1 == name2:
            return 0
        if (name1, name2) not in self._distance_graph.keys():
            if (name2, name1) not in self._distance_graph.keys():
                tup = [name2, name1]
                print("%s not in distance graph" % tup)
                return None
            else:
                return self._distance_graph[(name2, name1)]
        else:
            return self._distance_graph[(name1, name2)]



