#!/usr/bin/env python3

# Imports
import socket
import sqlite3
import json
import os
import selectors
import logging

# Define classes


class Config():

    def load(self, config_path):
        with open(config_path) as file:
            temp = json.load(file)

        self.server_ip = temp.get("SERVER_IP")
        self.tcp_port = int(temp.get("TCP_PORT"))
        self.udp_port = int(temp.get("UDP_PORT"))
        self.database_path = temp.get("DATABASE_PATH")
        self.buffer_size = int(temp.get("BUFFER_SIZE"))
        self.current_id = int(temp.get("CURRENT_ID"))
        self.magic = temp.get("MAGIC")
        self.version = int(temp.get("VERSION"))

    def save(self, config_path):
        temp = {
            "SERVER_IP": self.server_ip,
            "TCP_PORT": self.tcp_port,
            "UDP_PORT": self.udp_port,
            "DATABASE_PATH": self.database_path,
            "BUFFER_SIZE": self.buffer_size,
            "CURRENT_ID": self.current_id,
            "MAGIC": self.magic,
            "VERSION": self.version
        }

        with open(config_path, "w") as file:
            json.dump(temp, file)


def udp_command_handle(socket, mask):
    udp_data, addr = udp_client.recvfrom(config.buffer_size)
    # print(udp_data)

    try:
        params = json.loads(udp_data.decode())

    except json.JSONDecodeError:
        logging.warning(f"Incorrect json format {udp_data} sent from {addr}")
        return False

    foreign_keys = sorted(params.keys())
    expected_keys = sorted(["MAGIC", "COMMAND", "VERSION"])
    if expected_keys != foreign_keys:
        logging.warning(f"""Incorrect keys in udp_data {
                        udp_data} sent from {addr}""")
        return False

    elif params["MAGIC"] != config.magic:
        logging.warning(f"""Incorrect magic in udp_data {
                        udp_data} sent from {addr}""")
        return False

    expected_commands = ["GET_ID", "GET_IP"]
    if params["COMMAND"] not in expected_commands:
        logging.warning(f"""Incorrect command in udp_data {
                        udp_data} sent from {addr}""")
        return False

    command = params["COMMAND"]
    version = params["VERSION"]

    if command == "GET_ID":
        message = {
            "MAGIC": config.magic,
            "VERSION": version,
            "TCP_PORT": config.tcp_port,
            "SENSOR_ID": config.current_id
        }

        config.current_id += 1

        config.save(CONFIG_PATH)

        # TODO: Create a graphana panel through the API

    elif command == "GET_IP":
        message = {
            "MAGIC": config.magic,
            "VERSION": version,
            "TCP_PORT": config.tcp_port,
        }

    message = str.encode(json.dumps(message, indent=4))
    udp_client.sendto(message, addr)
    return True


def tcp_accept(socket, mask):
    conn, addr = tcp_server.accept()
    # print("Connection address: ", addr)

    while True:
        tcp_data = conn.recv(config.buffer_size)
        if not tcp_data:
            break
        params = tcp_data
        # print("Received data:", data)
        # conn.sendall(data)
    conn.close()

    try:
        params = json.loads(params.decode())
    except json.JSONDecodeError as err:
        logging.warning(f"Incorrect json format {tcp_data} sent from {addr}")
        return False

    expected_keys = sorted(
        ["time", "sensor_id", "temperature", "humidity", "MAGIC", "VERSION"])
    foreign_keys = sorted(params.keys())

    if expected_keys != foreign_keys:
        logging.warning(f"""Incorrect keys in tcp_data {
                        tcp_data} sent from {addr}""")
        return False

    elif params["MAGIC"] != config.magic:
        logging.warning(f"""Incorrect magic in tcp_data {
                        tcp_data} sent from {addr}""")
        return False

        time = params["time"]
        sensor_id = int(params["sensor_id"])
        temperature = float(params["temperature"])
        humidity = float(params["humidity"])

        cur.execute("""
            INSERT INTO sensors (sensor_id, time, temperature, humidity)
            VALUES (?, ?, ?, ?)
            """, (sensor_id, time, temperature, humidity))
        con.commit()
        return True

        # Connects to Google DNS server to determine the IP address
        # used for communication


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


if __name__ == "__main__":

    # Constants

    # Set current working directory to the directory of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DIR_PATH = os.path.dirname(__file__)
    CONFIG_PATH = os.path.join(DIR_PATH, 'server_config.json')
    LOG_PATH = os.path.join(DIR_PATH, 'server.log')

    # TODO: Get command line arguments and set up logging level based on them

    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=LOG_PATH, filemode="a",
                        format=FORMAT, level=logging.WARNING)

    config = Config()
    config.load(CONFIG_PATH)

    # Get the current IP of the server and save it for later
    config.server_ip = get_ip()
    config.save(CONFIG_PATH)

    con = sqlite3.connect(config.database_path)
    cur = con.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS sensors(
            sensor_id INTEGER,
            time INTEGER,
            temperature REAL,
            humidity REAL
            )
            """)

    # Setup udp client
    udp_client = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_client.bind(("", config.udp_port))
    udp_client.setblocking(False)

    # Setup the TCP server
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_server.bind((config.server_ip, config.tcp_port))
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
