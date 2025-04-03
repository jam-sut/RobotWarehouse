import warehouse
import robot
import os

if __name__ == "__main__":
    os.environ["ROBOTSIM_TRANSMIT"] = "FALSE"
    warehouse = warehouse.Warehouse("whouse.txt", 10, 3)
    continue_step = True
    while continue_step:
        continue_step = not warehouse.step()
    print("SIMULATION COMPLETE - TOOK %s steps" % warehouse.get_total_steps())





