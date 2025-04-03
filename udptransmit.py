import socket
import os
IP = "127.0.0.1"
PORT = 35891
SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
commands = {}


def send_udp_message(message: str):
    if os.environ["ROBOTSIM_TRANSMIT"] == "TRUE":
        SOCK.sendto(bytes(message, "utf-8"), (IP, PORT))


def transmit_start():
    message = '{"command":"START"}'
    send_udp_message(message)


def transmit_warehouse_size(x: int, y: int):
    message = '{"command":"WAREHOUSESIZE", "posX":%s, "posY":%s}' % (x, y)
    send_udp_message(message)


def transmit_robot_position(name: str, x: int, y: int):
    message = '{"command":"MOVEROBOT", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_robot_creation(name: str, x: int, y: int):
    message = '{"command":"CREATEROBOT", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_shelf_creation(name: str, item: str, x: int, y: int):
    message = '{"command":"CREATESHELF", "posX":%s, "posY":%s, "objName":"%s", "itemName":"%s"}' % (x, y, name, item)
    send_udp_message(message)


def transmit_goal_creation(name: str, x: int, y: int):
    message = '{"command":"CREATEGOAL", "posX":%s, "posY":%s, "objName":"%s"}' % (x, y, name)
    send_udp_message(message)


def transmit_item_existence(name: str, item_dep: int):
    message = '{"command":"ITEM", "itemName":"%s", "posX":%s}' % (name, item_dep)
    send_udp_message(message)


def transmit_item_gained(objname: str, item_name: str):
    message = '{"command":"ITEMGAINED", "objName":"%s", "itemName":"%s"}' % (objname, item_name)
    send_udp_message(message)


def transmit_item_lost(objname: str, item_name: str):
    message = '{"command":"ITEMLOST", "objName":"%s", "itemName":"%s"}' % (objname, item_name)
    send_udp_message(message)


def transmit_clear_inventory(objname: str):
    message = '{"command":"CLEARINV", "objName":"%s"}' % objname
    send_udp_message(message)




