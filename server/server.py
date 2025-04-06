#!/usr/bin/env python3

import socket
import sqlite3
import json
import os
import selectors


def udp_command_handle(socket, mask):
    udp_data, addr = udp_client.recvfrom(BUFFER_SIZE)
    # print(udp_data)

    try:
        params = json.loads(udp_data.decode())

    except json.JSONDecodeError as err:
        print(err)
        print()
        print(f"Incorrect json format {udp_data} sent from {addr}")
        return False

    foreign_keys = params.keys().sort()
    expected_keys = ["MAGIC", "COMMAND", "VERSION"].sort()
    if expected_keys != foreign_keys:
        print(f"Incorrect keys in udp_data {udp_data} sent from {addr}")
        return False

    elif params["MAGIC"] != MAGIC:
        print(f"Incorrect magic in udp_data {udp_data} sent from {addr}")
        return False

    expected_commands = ["GET_ID", "GET_IP"]
    if params["COMMAND"] not in expected_commands:
        print(f"Incorrect command in udp_data {udp_data} sent from {addr}")
        return False

    command = params["COMMAND"]
    version = params["VERSION"]

    if command == "GET_ID":
        message = {
            "MAGIC": MAGIC,
            "VERSION": version,
            "TCP_PORT": TCP_PORT,
            "SENSOR_ID": CURRENT_ID
        }

        config["CURRENT_ID"] = int(config["CURRENT_ID"]) + 1
        with open(CONFIG_PATH, 'w') as file:
            json.dump(config, file, indent=4)

    elif command == "GET_IP":
        message = {
            "MAGIC": MAGIC,
            "VERSION": version,
            "TCP_PORT": TCP_PORT,
        }

    message = str.encode(json.dumps(message, indent=4))
    udp_client.sendto(message, addr)
    return True


def tcp_accept(socket, mask):
    conn, addr = tcp_server.accept()
    # print("Connection address: ", addr)

    while True:
        tcp_data = conn.recv(BUFFER_SIZE)
        if not tcp_data:
            break
        params = tcp_data
        # print("Received data:", data)
        # conn.sendall(data)
    conn.close()

    try:
        params = json.loads(params.decode())
    except json.JSONDecodeError as err:
        print(err)
        print()
        print(f"Incorrect json format {tcp_data} sent from {addr}")
        return False

    expected_keys = ["time", "sensor_id", "temperature",
                     "humidity", "MAGIC", "VERSION"].sort()
    foreign_keys = params.keys().sort()
    if expected_keys != foreign_keys:
        print(f"Incorrect keys in tcp_data {tcp_data} sent from {addr}")
        return False

    elif params["MAGIC"] != MAGIC:
        print(f"Incorrect magic in tcp_data {tcp_data} sent from {addr}")
        return False

    time = params["time"]
    sensor_id = int(params["sensor_id"])
    temperature = float(params["temperature"])
    humidity = float(params["humidity"])

    cur.execute("INSERT INTO sensors (sensor_id, time, temperature, humidity) VALUES (?, ?, ?, ?)",
                (sensor_id, time, temperature, humidity))
    con.commit()
    return True


if __name__ == "__main__":

    # Constants
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DIR_PATH = os.path.dirname(__file__)
    CONFIG_PATH = os.path.join(DIR_PATH, 'server_config.json')
    LOG_PATH = os.path.join(DIR_PATH, 'sensor.log')

    with open(CONFIG_PATH) as file:
        config = json.load(file)

    # TODO: Get your own IP address at init
    SERVER_IP = config["SERVER_IP"]
    TCP_PORT = int(config["TCP_PORT"])
    UDP_PORT = int(config["UDP_PORT"])
    DATABASE_PATH = config["DATABASE_PATH"]
    BUFFER_SIZE = int(config["BUFFER_SIZE"])
    CURRENT_ID = int(config["CURRENT_ID"])
    MAGIC = config["MAGIC"]
    VERSION = config["VERSION"]

    # Setup the database connection

    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()

    # TODO: If table does not exist, create a table

    # cur.execute("CREATE TABLE sensors(sensor_id, time, temperature, humidity)")

    # Setup udp client
    udp_client = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_client.bind(("", UDP_PORT))
    udp_client.setblocking(False)

    # Setup the TCP server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((SERVER_IP, TCP_PORT))
    tcp_server.listen(25)
    tcp_server.setblocking(False)

    # Setup for multiplexing
    selector = selectors.DefaultSelector()
    selector.register(udp_client, selectors.EVENT_READ, udp_command_handle)
    selector.register(tcp_server, selectors.EVENT_READ, tcp_accept)

    while True:
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
