import warehouse
import robot
import os
import argparse
import time
import statistics

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
    faulty = [0.001, 0, 0, 0.001]
    perfect_scenario = [0, 0, 0, 0]

    for i in range(50):
        sim = warehouse.Warehouse("whouse.txt", 10, 3,
                                  "simple-interrupt", faulty, True, 300)
        continue_step = True
        skip = False
        while continue_step:
            t1 = time.perf_counter_ns()
            try:
                continue_step = not sim.step()
            except Exception as e:
                if "Item" in str(e) or "list" in str(e) or "Cannot" in str(e):
                    print(sim.get_scheduler()._order_robot_assignment)
                    print(sim.get_scheduler()._order_goal_assignment)
                    raise e
                errors.append(e)
                faulted_sims += 1
                skip = True
                break
            elapsed_time = time.perf_counter_ns() - t1
            step_times_1.append(elapsed_time)
            print("=========================================================================================")
        if skip:
            continue
        print("SIMULATION COMPLETE - TOOK %s steps" % sim.get_total_steps())
        step_amounts_1.append(sim.get_total_steps())
        sim.get_order_manager().print_order_completion_times()
        orders_1 = orders_1 + sim.get_order_manager().return_mapping_prio_to_completion_times()
        print("completed sim %s" % i)

    '''
    step_times_2 = []
    step_amounts_2 = []
    orders_2 = []
    for i in range(1000):
        sim = warehouse.Warehouse("whouse.txt", 10, 3, "simple-interrupt")
        continue_step = True
        skip = False
        while continue_step:
            t1 = time.perf_counter_ns()
            try:
                continue_step = not sim.step()
            except:
                faulted_sims += 1
                skip = True
                break
            elapsed_time = time.perf_counter_ns() - t1
            step_times_2.append(elapsed_time)
            print("=========================================================================================")
        if skip:
            continue
        print("SIMULATION COMPLETE - TOOK %s steps" % sim.get_total_steps())
        step_amounts_2.append(sim.get_total_steps())
        sim.get_order_manager().print_order_completion_times()
        orders_2 = orders_2 + sim.get_order_manager().return_mapping_prio_to_completion_times()
        print("completed sim %s" % i)

    times_1 = [[], [], [], [], []]
    times_2 = [[], [], [], [], []]

    for i in range(5):
        for order in orders_1:
            if order[0] == i+1:
                times_1[i].append(order[1])

        for order in orders_2:
            if order[0] == i+1:
                times_2[i].append(order[1])

        print("Average amount of steps for prio %s completion: simple: %s,  simple-interrupt: %s" % (i+1, statistics.mean(times_1[i]), statistics.mean(times_2[i])))

'''
    #print("Max step time %sns, Min step time %sns" % (max(step_times), min(step_times)))
    #print("Mean step time %0.2fns" % statistics.mean(step_times))

    print("Average amount of steps for simple, %s" % statistics.mean(step_amounts_1))
    #print("Average amount of steps for simple-interrupt, %s" % statistics.mean(step_amounts_2))
    print("%s SIMS BROKE" % faulted_sims)
    for er in errors:
        print(er)








