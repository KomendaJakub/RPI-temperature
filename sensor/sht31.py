#!/usr/bin/env python3

# Imports
import socket
import smbus
import time
import os
import json

# Class definitions


class Config():

    def __init__(self, data):
        self.server_ip = data["SERVER_IP"]
        self.tcp_port = int(data["TCP_PORT"])
        self.udp_port = int(data["UDP_PORT"])
        self.buffer_size = int(data["BUFFER_SIZE"])
        self.sensor_id = int(data["SENSOR_ID"])
        self.version = int(data["VERSION"])
        self.magic = data["MAGIC"]

    def load(self, config_path):
        with open(config_path) as file:
            temp = json.load(file)
            self.server_ip = temp["SERVER_IP"]
            self.tcp_port = int(temp["TCP_PORT"])
            self.udp_port = int(temp["UDP_PORT"])
            self.buffer_size = int(temp["BUFFER_SIZE"])
            self.sensor_id = int(temp["SENSOR_ID"])
            self.version = int(temp["VERSION"])
            self.magic = temp["MAGIC"]

    def save(self, config_path):
        temp = {
            "SERVER_IP": self.server_ip,
            "TCP_PORT": self.tcp_port,
            "UDP_PORT": self.udp_port,
            "BUFFER_SIZE": self.buffer_size,
            "SENSOR_ID": self.sensor_id,
            "VERSION": self.version,
            "MAGIC": self.magic
        }

        with open(config_path, "w") as file:
            json.dump(temp, file, indent=4)


# Function definitions
def udp_send(command):
    udp_server = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_server.settimeout(1)

    message = {
        "MAGIC": config.magic,
        "VERSION": config.version,
        "COMMAND": command
    }

    message = str.encode(json.dumps(message, indent=4))

    udp_server.sendto(message, ("255.255.255.255", config.udp_port))
    data, addr = udp_server.recvfrom(config.buffer_size)

    try:
        data = json.loads(data.decode())
    except json.JSONDecodeError as err:
        print(err)
        print()
        print(f"Incorrect json format {data} sent from {addr}")
        raise SystemExit()

    foreign_keys = sorted(data.keys())
    if command == "GET_ID":
        expected_keys = sorted(["MAGIC", "VERSION", "TCP_PORT", "SENSOR_ID"])
    elif command == "GET_IP":
        expected_keys = sorted(["MAGIC", "VERSION", "TCP_PORT"])

    if expected_keys != foreign_keys:
        print(f"Incorrect keys in data {data} sent from {addr}")
        raise SystemExit()

    # Validate data
    if not (data["MAGIC"] == config.magic and data["VERSION"] == config.version):
        print(f"Incorrect MAGIC or VERSION in data {data} sent from {addr}")
        raise SystemExit()

    return data, addr


def get_measurement():
    I2C_address = 0x45
    # Interact with hardware
    bus = smbus.SMBus(1)
    bus.write_i2c_block_data(I2C_address, 0x2C, [0x06])
    time.sleep(0.5)
# SHT31 address, 0x45(68)
# Read data back from 0x00(00), 6 bytes
# Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
    data = bus.read_i2c_block_data(I2C_address, 0x00, 6)
    return data


def data_to_message(data):
    # Process data
    temp = data[0] * 256 + data[1]
    cTemp = -45 + (175 * temp / 65535.0)
    # fTemp = -49 + (315 * temp / 65535.0)
    humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

    # Create message
    message = {
        "time": time.time(),
        "sensor_id": config.sensor_id,
        "temperature": cTemp,
        "humidity": humidity,
        "MAGIC": config.magic,
        "VERSION": config.version
    }

    message = str.encode(json.dumps(message, indent=4))
    return message


def get_ip():
    data, addr = udp_send("GET_IP")

    config.server_ip = addr[0]
    config.tcp_port = data["TCP_PORT"]

    config.save(CONFIG_PATH)


def tcp_send(message, server_address):
    # Send data over TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(server_address)
        s.sendall(message)

        # data = s.recv(BUFFER_SIZE)
        s.close()
    except ConnectionRefusedError as err:
        print(err)
        print("Error: Connection refused")
        print("Trying to get server IP")

        get_ip()

    except Exception as err:
        print(err)
        print("Error while sending data")
        print("Trying to get server IP")

        get_ip()


if __name__ == "__main__":
    # Constants
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DIR_PATH = os.path.dirname(__file__)
    CONFIG_PATH = os.path.join(DIR_PATH, 'sensor_config.json')

    config = Config()
    config.load(CONFIG_PATH)

    if config.sensor_id == '':
        # Request an ID from the server
        data, addr = udp_send("GET_ID")

        config.server_ip = addr[0]
        config.tcp_port = data["TCP_PORT"]
        config.sensor_id = data["SENSOR_ID"]

        config.save(CONFIG_PATH)

    if config.server_ip == '' or config.tcp_port == '':
        # Request an IP from the server
        get_ip()

    data = get_measurement()
    message = data_to_message(data)
    server_address = (config.server_ip, config.tcp_port)
    tcp_send(message, server_address)
