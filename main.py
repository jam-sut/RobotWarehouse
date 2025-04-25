import customexceptions
import warehouse
import robot
import os
import argparse
import time
import statistics
import shutil
import random
import math
import matplotlib

class Simulation:
    def __init__(self, num_sims:int, whouse:str, num_items:int, inv_size:int, schedule_mode:str, fault_rates, fault_mode, step_limit, side_len = None):
        self._side_len = side_len
        self._num_sims = num_sims
        self.warehouse_file = whouse
        self._num_items = num_items
        self._inv_size = inv_size
        self._schedule_mode = schedule_mode
        self._fault_rates = fault_rates
        self._fault_mode = fault_mode
        self._step_limit = step_limit

        self.num_robots = None

        self.step_amounts = []
        self.step_times = []
        self.error_strings = []

        self.order_prio = []
        self.order_prio_sorted_completion_time_lists = [[], [], [], [], []]

        self.order_completion_steps_by_num_robots = {}

    def run_simulation(self, fault_on_error=False):
        for sim_num in range(self._num_sims):
            print("Starting sim %s" % sim_num)
            sim_step_times = []
            try:
                simu = warehouse.Warehouse(self.warehouse_file, self._num_items, self._inv_size,
                                           self._schedule_mode, self._fault_rates, self._fault_mode, self._step_limit)
                keep_step = True
                while keep_step:
                    before_step_time = time.perf_counter_ns()
                    keep_step = not simu.step()
                    elapsed_time_between = time.perf_counter_ns() - before_step_time
                    sim_step_times.append(elapsed_time_between)

            except customexceptions.SimulationError as err:
                if fault_on_error:
                    raise err
                if not ("limit" in str(err) or "collided" in str(err)):
                    pass

                self.error_strings.append(err)
                continue

            self.step_times.extend(sim_step_times)

            self.step_amounts.append(simu.get_total_steps())
            self.order_prio = self.order_prio + simu.get_order_manager().return_mapping_prio_to_completion_times()

            orders_to_amount_robots = simu.get_scheduler().get_order_to_amount_of_robots_assigned()
            order_start_times = simu.get_order_manager().get_order_start_work_times()
            order_finish_times = simu.get_order_manager().get_order_finish_work_times()

            for order_name in orders_to_amount_robots.keys():
                order_total_time = order_finish_times[order_name] - order_start_times[order_name]
                amount_robots = orders_to_amount_robots[order_name]
                if amount_robots not in self.order_completion_steps_by_num_robots.keys():
                    self.order_completion_steps_by_num_robots[amount_robots] = [order_total_time]
                else:
                    self.order_completion_steps_by_num_robots[amount_robots].append(order_total_time)

            self.num_robots = simu.get_number_of_robots()

        for prio_num in range(5):
            for order_list in self.order_prio:
                if order_list[0] == prio_num + 1:
                    self.order_prio_sorted_completion_time_lists[prio_num].append(order_list[1])

    def print_priority_info(self):
        import matplotlib.pyplot as plt
        import numpy as np
        fig = plt.figure(figsize=(8,8))

        for j in range(5):
            if self.order_prio_sorted_completion_time_lists[j]:
                sel = self.order_prio_sorted_completion_time_lists[j]
                print("Average amount of steps for prio %s completion: %s" % (j + 1, statistics.mean(sel)))
        plt.boxplot(self.order_prio_sorted_completion_time_lists)

        ax = plt.gca()
        plt.title("Order prioritisation statistics for scheduling algorithm %s" % self._schedule_mode)
        ax.set_xlabel("Order priority")
        ax.set_ylabel("Amount of steps to complete order after introduction")

        plt.show()

    def print_num_robots_info(self):
        for amount_bots in self.order_completion_steps_by_num_robots.keys():
            print("Average amount of time taken for an order with %s bots: %s" % (
                amount_bots, statistics.mean(self.order_completion_steps_by_num_robots[amount_bots])))

    def print_error_info(self):
        for err in self.error_strings:
            print(err)
        print("%s simulations faulted critically." % len(self.error_strings))
        return self.error_strings

    def print_steps_taken(self):
        print("Simulation %s took an average of %s steps" % (self._schedule_mode, statistics.mean(self.step_amounts)))
        return self.step_amounts

    def print_step_time_info(self):
        print("Max step time %sms, Min step time %sms" % (max(self.step_times) / 10**6, min(self.step_times) / 10**6))
        print("Mean step time %sms" % (statistics.mean(self.step_times) / 10**6))

        return [self.num_robots, self._side_len, statistics.mean(self.step_times) / 10**6]


def gen_nxn_warehouse(robot_num, side_len):
    robots_left_to_place = robot_num
    goals_left_to_place = robot_num
    filename = "wt%sx%sr%s.txt" % (side_len, side_len, robot_num)
    f = open(filename, "a")

    lines = []

    if robots_left_to_place <= side_len - 2:
        robot_section = ["R" for i in range(robots_left_to_place)]
        left_section = ["X" for i in range(side_len - 2 - robots_left_to_place)]
        middle_section = ''.join(robot_section) + ''.join(left_section)
        robots_left_to_place = 0
    else:
        middle_section = ''.join(["R" for i in range(side_len - 2)])
        robots_left_to_place = robots_left_to_place - (side_len - 2)

    first_line = "X%sX\n" % middle_section


    if goals_left_to_place <= side_len - 2:
        goal_section = ["G" for i in range(goals_left_to_place)]
        left_section = ["X" for i in range(side_len - 2 - goals_left_to_place)]
        middle_section = ''.join(goal_section) + ''.join(left_section)
        goals_left_to_place = 0
    else:
        middle_section = ''.join(["G" for i in range(side_len - 2)])
        goals_left_to_place = goals_left_to_place - (side_len - 2)

    last_line = "X%sX" % middle_section

    lines.append(first_line)

    for i in range(side_len - 2):
        line = ''.join(["X" for i in range(side_len)]) + "\n"
        lines.append(line)

    lines.append(last_line)

    for i in range(robots_left_to_place):
        lines[i+1] = "R" + lines[i+1][1:]
        lines[len(lines) - 2 - i] = lines[len(lines) - 2 - i][:-2] + "G\n"
        if i+1 == side_len - 1:
            raise Exception("not enough space for that amount of robots")

    middle_index = ((side_len + 1) // 2) - 1
    one_above = middle_index - 1
    one_below = middle_index + 1

    spacing = ''.join(["X" for i in range((side_len - 7) // 2)])

    lines[one_above] = lines[one_above][0] + spacing + "SSXSS" + spacing + lines[one_above][-2] + "\n"
    lines[middle_index] = lines[middle_index][0] + spacing + "SSXSS" + spacing + lines[middle_index][-2] + "\n"
    lines[one_below] = lines[one_below][0] + spacing + "SSXSS" + spacing + lines[one_below][-2] + "\n"

    for line in lines:
        f.write(line)

    f.close()

    return filename

def run_simulation_performance_test(scheduling_mode:str, robots_max:int, size_max:int, step_limit:int):
    try:
        os.makedirs("tmp")
    except FileExistsError:
        shutil.rmtree("tmp")
        os.makedirs("tmp")
    os.chdir("tmp")
    results = []
    by_sim_size = []
    ctr = 0
    for i in range(7, size_max, 2):
        by_sim_size.append([])
        for j in range(1, robots_max+1):
            print("starting %s %s" % (j, i))
            file_name = gen_nxn_warehouse(j, i)
            sim_1 = Simulation(50, file_name, 12, 3, scheduling_mode,
                     [0, 0, 0, 0], True, step_limit, i)
            sim_1.run_simulation()
            results.append(sim_1.print_step_time_info())
            by_sim_size[ctr].append(sim_1.print_step_time_info())
        ctr += 1
    print(results)

    import numpy
    import matplotlib.pyplot as plt
    import matplotlib
    import matplotlib.ticker as ticker
    from mpl_toolkits.mplot3d import proj3d

    res = numpy.array(results)
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(111, projection='3d')
    x = res[:, 0]
    y = res[:, 1]
    z = res[:, 2]
    plt.title("Simulation performance for scheduling algorithm %s" % scheduling_mode)


    for robot_line in by_sim_size:
        mini_res = numpy.array(robot_line)
        ax.plot(mini_res[:, 0], mini_res[:, 1], mini_res[:, 2], color="grey")
    ax.scatter(x, y, z, c=z, cmap=matplotlib.colormaps.get_cmap("inferno"))



    ax.set_xlabel('Amount of Robots')
    ax.set_ylabel('Warehouse side length')
    ax.set_zlabel('Average step time (ms)')

    ax.xaxis.set_major_locator(ticker.IndexLocator(1,0))
    ax.yaxis.set_major_locator(ticker.IndexLocator(2, 0))

    plt.show()


def run_completion_time_test():
    sim = Simulation(500, "whouse2.txt", 10, 3, "simple",
                     [0, 0, 0, 0], True, 500)

    sim_1 = Simulation(500, "whouse2.txt", 10, 3, "simple-interrupt",
                       [0, 0, 0, 0], True, 500)

    sim_2 = Simulation(500, "whouse2.txt", 10, 3, "multi-robot",
                       [0, 0, 0, 0], True, 500)

    sim.run_simulation()
    sim_1.run_simulation()
    sim_2.run_simulation()

    steps = [sim.print_steps_taken(), sim_1.print_steps_taken(), sim_2.print_steps_taken()]

    import matplotlib.pyplot as plt
    import numpy as np

    fig = plt.figure(figsize=(8, 8))
    plt.boxplot(steps)
    ax = plt.gca()
    plt.title("Amount of time to complete simulation for each simulation type")
    plt.xticks([1, 2, 3], ['simple', 'simple-interrupt', 'multi-robot'])
    ax.set_xlabel("Simulation type")
    ax.set_ylabel("Amount of steps")

    plt.show()

def run_fault_test():
    fault_mode = True
    faulty = [0.0001, 0.001, 0.001, 0.001]
    num_sims = 500

    random.seed(10)
    sim = Simulation(num_sims, "whouse2.txt", 10, 3, "simple",
                     faulty, fault_mode, 500)

    sim_1 = Simulation(num_sims, "whouse2.txt", 10, 3, "simple-interrupt",
                       faulty, fault_mode, 500)

    sim_2 = Simulation(num_sims, "whouse2.txt", 10, 3, "multi-robot",
                       faulty, fault_mode, 500)


    fault_mode = False

    random.seed(10)
    sim_3 = Simulation(num_sims, "whouse2.txt", 10, 3, "simple",
                     faulty, fault_mode, 500)

    sim_4 = Simulation(num_sims, "whouse2.txt", 10, 3, "simple-interrupt",
                       faulty, fault_mode, 500)

    sim_5 = Simulation(num_sims, "whouse2.txt", 10, 3, "multi-robot",
                       faulty, fault_mode, 500)

    sim.run_simulation()
    sim_1.run_simulation()
    sim_2.run_simulation()

    sim_3.run_simulation()
    sim_4.run_simulation()
    sim_5.run_simulation()

    all_errors_1 = [sim.print_error_info(), sim_1.print_error_info(), sim_2.print_error_info()]
    all_errors_2 = [sim_3.print_error_info(), sim_4.print_error_info(), sim_5.print_error_info()]


    collisions_1 = []
    overruns_1 = []
    invalid_schedule_1 = []
    all_error_nums_1 = []
    ctr = 0

    for sim_1 in all_errors_1:
        collisions_1.append(0)
        overruns_1.append(0)
        invalid_schedule_1.append(0)
        all_error_nums_1.append(0)
        for thing in sim_1:
            if "collided" in str(thing):
                collisions_1[ctr] += 1
            if "limit" in str(thing):
                overruns_1[ctr] += 1
            if "empty" in str(thing) or "violated" in str(thing):
                invalid_schedule_1[ctr] += 1
            all_error_nums_1[ctr] += 1
        ctr += 1

    collisions_2 = []
    overruns_2 = []
    invalid_schedule_2 = []
    all_error_nums_2 = []
    ctr = 0

    for sim_2 in all_errors_2:
        collisions_2.append(0)
        overruns_2.append(0)
        invalid_schedule_2.append(0)
        all_error_nums_2.append(0)
        for thing in sim_2:
            if "collided" in str(thing):
                collisions_2[ctr] += 1
            if "limit" in str(thing):
                overruns_2[ctr] += 1
            if "empty" in str(thing) or "violated" in str(thing):
                invalid_schedule_2[ctr] += 1
            all_error_nums_2[ctr] += 1
        ctr += 1

    import matplotlib.pyplot as plt
    import numpy as np
    types = ("simple", "simple-interrupt", "multi-robot")

    x = np.arange(len(types))  # the label locations
    width = 0.1  # the width of the bars
    multiplier = 1

    groups = {
        "Number of Simulations": [500, 500, 500],

        "Total Critically Faulted Simulations - Fault tolerant strategy enabled": all_error_nums_1,
        "Total Critically Faulted Simulations - Fault tolerant strategy disabled": all_error_nums_2,

        "Collisions - Fault tolerant strategy enabled": collisions_1,
        "Collisions - Fault tolerant strategy disabled": collisions_2,

        "Scheduling Violation - Fault tolerant strategy enabled": invalid_schedule_1,
        "Scheduling Violation - Fault tolerant strategy disabled": invalid_schedule_2,

        "Overruns - Fault tolerant strategy enabled": overruns_1,
        "Overruns - Fault tolerant strategy disabled": overruns_2
    }

    colors = [
        (0.0, 0.0, 1.0, 1.0),

        (1.0, 0.0, 0.0, 0.5),
        (1.0, 0.0, 0.0, 1.0),

        (1.0, 1.0, 0.0, 0.5),
        (1.0, 1.0, 0.0, 1.0),

        (0.0, 1.0, 1.0, 0.5),
        (0.0, 1.0, 1.0, 1.0),

        (1.0, 0.0, 1.0, 0.5),
        (1.0, 0.0, 1.0, 1.0)
    ]

    fig = plt.figure(figsize=(20,8))
    ax = fig.gca()

    color_ctr = 0
    for attribute in groups.keys():
        measurement_1 = groups[attribute]

        offset = width * multiplier
        rects = ax.bar(x + offset, measurement_1, width, label=attribute, color=colors[color_ctr])
        ax.bar_label(rects, padding=3)
        multiplier += 1
        color_ctr += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount')
    ax.set_title('Fault tolerant strategy')
    ax.set_xticks(x + width, types)
    ax.legend(loc='upper left', ncols=3)
    ax.set_ylim(0, 600)
    plt.show()








if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", action="store_true", help="Whether or not to transmit UDP"
                                                                                  " packets.")
    args = parser.parse_args()

    print("Transmit mode is %s" % args.t)

    os.environ["ROBOTSIM_TRANSMIT"] = str(args.t)
    print(os.environ["ROBOTSIM_TRANSMIT"])
    step_times_1 = []
    step_amounts_1 = []
    orders_1 = []
    errors = []

    faulted_sims = 0
    faulty = [0.0001, 0.001, 0.001, 0.001]
    perfect_scenario = [0, 0, 0, 0]

    #run_fault_test()
    #run_simulation_performance_test("multi-robot", 10, 25, 2000)

    #run_fault_test()
    #random.seed(23)

    #sim = Simulation(1, "whouse2.txt", 10, 3, "simple-interrupt",
    #                perfect_scenario, True, 500)

    sim = Simulation(500, "whouse2.txt", 10, 3, "multi-robot",
                    perfect_scenario, True, 500)

    sim.run_simulation(True)
    sim.print_error_info()




    #sim.print_priority_info()

    #sim.print_error_info()









