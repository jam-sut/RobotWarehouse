import order
import random

class OrderManager:
    def __init__(self, num_init_orders: int, num_dynamic_orders: int, item_set: dict):
        self._num_init_orders = num_init_orders
        self._num_dynamic_orders = num_dynamic_orders
        self._item_set = item_set

        self._init_orders = []
        self._dynamic_orders = []
        self.generate_orders_static(num_init_orders, num_dynamic_orders, 10)

    def generate_orders_static(self, num_init_orders: int, num_dynamic_orders: int, order_size: int):
        order_id_ctr = 0
        for i in range(num_init_orders):
            current_items = []
            for j in range(order_size):
                selected_item_index = random.randint(0, len(self._item_set.keys()) - 1)
                current_items.append(self._item_set["item%s" % selected_item_index])
            order_prio = random.randint(1, 5)
            current_order = order.Order(current_items, order_prio, order_id_ctr)
            order_id_ctr = order_id_ctr + 1
            self._init_orders.append(current_order)

        for i2 in range(num_dynamic_orders):
            current_items = []
            for j2 in range(order_size):
                selected_item_index = random.randint(0, len(self._item_set.keys()) - 1)
                current_items.append(self._item_set["item%s" % selected_item_index])
            order_prio = random.randint(1, 5)
            current_order = order.Order(current_items, order_prio, order_id_ctr)
            order_id_ctr = order_id_ctr + 1
            self._dynamic_orders.append(current_order)

    def get_init_orders(self):
        return self._init_orders


    def print_orders(self):
        print("Initial Orders:")
        for order_obj in self._init_orders:
            print(order_obj)
        print("Dynamic Orders:")
        for order_obj in self._dynamic_orders:
            print(order_obj)









