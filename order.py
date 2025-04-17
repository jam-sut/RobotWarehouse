class Order:
    def __init__(self, items: list, prio: int, idnum: int):
        self._items = items
        self._prio = prio
        self._id = idnum

    def get_items(self):
        return self._items

    def get_id(self):
        return self._id

    def get_prio(self):
        return self._prio

    def get_highest_item_dep(self):
        highest = 0
        for item in self._items:
            if item.get_dependency() > highest:
                highest = item.get_dependency()
        return highest

    def __repr__(self):
        ret_string = "Order ID number %s, priority %s\n" % (self._id, self._prio)
        for item in self._items:
            ret_string += "%s\n" % item
        return ret_string
