import random

import item
import udptransmit
import shelf
import orderstation
import robot
import heapq
import utils
import ordermanager
import scheduler
import time
from dataclasses import dataclass, field

class Warehouse:
    def __init__(self, w_house_filename: str, num_items: int, robot_max_inventory: int):
        self._current_orders = []
        self._cells = []
        self._robots = {}
        self._order_stations = {}
        self._shelves = {}

        self._items = {}
        self.generate_items(num_items)

        self._order_manager = ordermanager.OrderManager(5, 5, self._items)

        self._robot_max_inventory = robot_max_inventory
        # Warehouse cell (x,y) is accessed via self._cells[y][x]
        self._cells = self.parse_warehouse_file(w_house_filename)

        self._scheduler = scheduler.Scheduler(self._robots, self._shelves, self._order_stations, self._order_manager.get_init_orders())
        self._scheduler.simple_single_robot_schedule()

        self._width = len(self._cells[0])
        self._height = len(self._cells)
        udptransmit.transmit_start()
        self.transmit_initial_warehouse_layout()
        self._total_steps = 0

    def step(self):
        for robot_obj in self._robots.values():
            self.decide_robot_action(robot_obj)
        self.print_layout_simple()
        self._total_steps = self._total_steps + 1
        for station in self._order_stations.values():
            if self._scheduler.is_this_a_complete_order(station.report_inventory()):
                station.clear_inventory()
        return self._scheduler.are_all_orders_complete()

    def get_total_steps(self):
        return self._total_steps

    def cell_is_full(self, x, y):
        return ("robot" in "".join(self._cells[y][x])) or ("wall" in "".join(self._cells[y][x]))

    def get_robots(self):
        return self._robots

    def decide_robot_action(self, robot_obj):
        if robot_obj.get_target() is not None:
            if not robot_obj.is_at_target():
                #self.move_robot_towards_naive(robot_obj)
                self.move_robot_towards_astar_collision_detect(robot_obj)
            else:
                robot_obj.interact_with_target()
        else:
            self._scheduler.direct_robot(robot_obj)

    def move_robot_towards_naive(self, robot_obj):
        robot_x, robot_y = robot_obj.get_position()
        target_x, target_y = robot_obj.get_target.get_position()
        if robot_x != target_x:
            if robot_x < target_x:
                self.update_robot_position_obj(robot_obj, robot_x, robot_y, robot_x + 1, robot_y)
            elif robot_x > target_x:
                self.update_robot_position_obj(robot_obj, robot_x, robot_y, robot_x - 1, robot_y)
        elif robot_y != target_y:
            if robot_y < target_y:
                self.update_robot_position_obj(robot_obj, robot_x, robot_y, robot_x, robot_y + 1)
            else:
                self.update_robot_position_obj(robot_obj, robot_x, robot_y, robot_x, robot_y - 1)

    def move_robot_towards_astar_collision_detect(self, robot_obj):
        # If the robot has no planned path when we ask it to move, it should try and compute one
        if not robot_obj.get_movement_path():
            robot_obj.set_movement_path(self.compute_robot_astar_path(robot_obj))

        amount_steps_halted = robot_obj.get_steps_halted()
        if amount_steps_halted > 1:
            if random.random() < amount_steps_halted/10:
                print("ATTEMPTING TO RESOLVE DEADLOCK")
                print("RECOMPUTING ROBOT %s" % robot_obj.get_name())
                robot_obj.set_movement_path(self.compute_robot_astar_path(robot_obj))


        next_position = None
        # The robot might not have found a valid path, it could be blocked in by other robots
        if robot_obj.get_movement_path():
            next_position = robot_obj.get_movement_path()[0]

            # If a robot has moved into the way of a computed path and blocked this robot then it shouldn't move on this
            # step.
            if self.cell_is_full(next_position[0], next_position[1]):
                next_position = None

        # If we have a next position after the end of this, the robot should move to it
        if next_position is not None:
            robot_x, robot_y = robot_obj.get_position()
            self.update_robot_position_obj(robot_obj, robot_x, robot_y, next_position[0], next_position[1])
            robot_obj.get_movement_path().pop(0)
        else:
            robot_obj.increment_steps_halted()

    def compute_robot_astar_path(self, robot_obj):
        robot_x, robot_y = robot_obj.get_position()
        target_x, target_y = robot_obj.get_target().get_position()

        @dataclass(order=True)
        class PrioNode:
            x: int = field(compare=False)
            y: int = field(compare=False)
            f_score: int

            def __eq__(self, other):
                return self.x == other.x and self.y == other.y
        g_scores = {}
        f_scores = {}
        came_from = {}
        search_frontier = []
        f_scores[(robot_x, robot_y)] = utils.taxicab_dist(robot_x, robot_y, target_x, target_y)
        g_scores[(robot_x, robot_y)] = 0
        heapq.heappush(search_frontier,
                       PrioNode(robot_x, robot_y, f_scores[(robot_x, robot_y)]))
        while len(search_frontier) != 0:
            current = heapq.heappop(search_frontier)
            if current.x == target_x and current.y == target_y:
                # We don't need the first element of the path, that's where we already are
                return self.reconstruct_path(came_from, (current.x, current.y))[1:]

            offsets = [(current.x + 1, current.y),
                       (current.x - 1, current.y),
                       (current.x, current.y + 1),
                       (current.x, current.y - 1)]

            for n in offsets:
                if not ((0 <= n[0] <= self._width - 1) and (0 <= n[1] <= self._height - 1)):
                    continue
                neigh_tup = (n[0], n[1])
                cur_tup = (current.x, current.y)
                if not self.cell_is_full(n[0], n[1]):
                    possible_g_score = g_scores[cur_tup] + 1
                    if neigh_tup in g_scores.keys():
                        if not possible_g_score < g_scores[neigh_tup]:
                            continue
                    came_from[neigh_tup] = cur_tup
                    g_scores[neigh_tup] = possible_g_score
                    f_scores[neigh_tup] = possible_g_score + utils.taxicab_dist(current.x, current.y+1,
                                                                                target_x, target_y)
                    if PrioNode(n[0], n[1], 0) not in search_frontier:
                        heapq.heappush(search_frontier,
                                       PrioNode(n[0], n[1], f_scores[neigh_tup]))
        return []

    def reconstruct_path(self, came_from: dict, current):
        total_path = [current]
        while current in came_from.keys():
            current = came_from[current]
            total_path.insert(0, current)
        return total_path

    def transmit_initial_warehouse_layout(self):
        udptransmit.transmit_warehouse_size(self._width, self._height)
        for row in self._cells:
            for cell in row:
                for obj_name in cell:
                    if "robot" in obj_name:
                        self._robots[obj_name].transmit_creation()
                    elif "shelf" in obj_name:
                        self._shelves[obj_name].transmit_creation()
                    elif "goal" in obj_name:
                        self._order_stations[obj_name].transmit_creation()

    def print_layout_simple(self):
        for i in range(len(self._cells[0]) + 2):
            print("-", end="")
        print("")
        for row in reversed(self._cells):
            print("|", end="")
            for cell in row:
                for obj in cell:
                    if "robot" in obj:
                        if len(cell) == 1:
                            print("R", end="")
                        else:
                            print("r", end="")
                    elif ("shelf" in obj) and (len(cell) == 1):
                        print("S", end="")
                    elif ("goal" in obj) and (len(cell) == 1):
                        print("G", end="")
                    elif "wall" in obj:
                        print("W", end="")
                if len(cell) == 0:
                    print(" ", end="")
            print("|")
        for i in range(len(self._cells[0]) + 2):
            print("-", end="")
        print("")

    def parse_warehouse_file(self, filename: str):
        robot_name_ctr = 0
        shelf_name_ctr = 0
        goal_name_ctr = 0
        row_ctr = 0
        col_ctr = 0

        prev_width = None

        cells_copy = []
        lines = []

        f = open(filename, "r")
        for line_raw in f:
            lines.append(line_raw.strip())
        f.close()

        for line in list(reversed(lines)):
            width = len(line)
            if prev_width is None:
                prev_width = width
            else:
                if width != prev_width:
                    raise ValueError("Warehouse file is not a complete rectangle")
            cells_copy.append([])
            col_ctr = 0
            for char in line:
                if char == "R":
                    new_robot_name = "robot%s" % robot_name_ctr
                    new_robot = robot.Robot(new_robot_name, col_ctr, row_ctr, self._robot_max_inventory)
                    self._robots[new_robot_name] = new_robot

                    cells_copy[row_ctr].append([new_robot_name])
                    robot_name_ctr = robot_name_ctr + 1
                elif char == "S":
                    new_shelf_name = "shelf%s" % shelf_name_ctr
                    possible_item_name = "item%s" % shelf_name_ctr

                    if possible_item_name in self._items.keys():
                        new_shelf = shelf.Shelf(col_ctr, row_ctr, new_shelf_name, self._items[possible_item_name])
                    else:
                        new_shelf = shelf.Shelf(col_ctr, row_ctr, new_shelf_name)
                    self._shelves[new_shelf_name] = new_shelf

                    cells_copy[row_ctr].append([new_shelf_name])
                    shelf_name_ctr = shelf_name_ctr + 1
                elif char == "G":
                    new_goal_name = "goal%s" % goal_name_ctr
                    new_goal = orderstation.OrderStation(col_ctr, row_ctr, new_goal_name)
                    self._order_stations[new_goal_name] = new_goal

                    cells_copy[row_ctr].append([new_goal_name])
                    goal_name_ctr = goal_name_ctr + 1
                elif char == "W":
                    cells_copy[row_ctr].append(["wall"])
                else:
                    cells_copy[row_ctr].append([])
                col_ctr = col_ctr + 1
            row_ctr = row_ctr + 1
        return cells_copy

    def transmit(self):
        udptransmit.transmit_warehouse_size(self._width, self._height)

    def generate_items(self, num_items):
        for i in range(num_items):
            item_name = "item%s" % i
            self._items[item_name] = item.Item(item_name, i)

    def update_robot_position(self, robot_name: str, new_x, new_y):
        robot_obj = self._robots[robot_name]
        old_x, old_y = robot_obj.get_position()
        robot_obj.set_position(new_x, new_y)
        self._cells[old_y][old_x].remove(robot_name)
        self._cells[new_y][new_x].append(robot_name)
        udptransmit.transmit_robot_position(robot_name, new_x, new_y)

    def update_robot_position_obj(self, robot_obj: robot.Robot, old_x, old_y, new_x, new_y):
        robot_obj.set_position(new_x, new_y)
        self._cells[old_y][old_x].remove(robot_obj.get_name())
        self._cells[new_y][new_x].append(robot_obj.get_name())
        udptransmit.transmit_robot_position(robot_obj.get_name(), new_x, new_y)




