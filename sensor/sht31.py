#!/usr/bin/env python3

# Imports
import socket
import smbus
import time
import os
import json


# Function definitions
def udp_send(command):
    udp_server = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_server.settimeout(1)

    message = {
        "MAGIC": MAGIC,
        "VERSION": VERSION,
        "COMMAND": command
    }

    message = str.encode(json.dumps(message, indent=4))

    udp_server.sendto(message, ("255.255.255.255", UDP_PORT))
    data, addr = udp_server.recvfrom(BUFFER_SIZE)

    try:
        data = json.loads(data.decode())
    except json.JSONDecodeError as err:
        print(err)
        print()
        print(f"Incorrect json format {data} sent from {addr}")
        raise SystemExit()

    foreign_keys = data.keys().sort()
    if command == "GET_ID":
        expected_keys = ["MAGIC", "VERSION", "TCP_PORT", "SENSOR_ID"]
    elif command == "GET_IP":
        expected_keys = ["MAGIC", "VERSION", "TCP_PORT"]

    if expected_keys != foreign_keys:
        print(f"Incorrect keys in data {data} sent from {addr}")
        raise SystemExit()

    # Validate data
    if not (data["MAGIC"] == MAGIC and data["VERSION"] == VERSION):
        print(f"Incorrect MAGIC or VERSION in data {data} sent from {addr}")
        raise SystemExit()

    return data, addr


def get_measurement():
    # Interact with hardware
    bus = smbus.SMBus(1)
    bus.write_i2c_block_data(0x45, 0x2C, [0x06])
    time.sleep(0.5)
# SHT31 address, 0x45(68)
# Read data back from 0x00(00), 6 bytes
# Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
    data = bus.read_i2c_block_data(0x45, 0x00, 6)
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
        "sensor_id": SENSOR_ID,
        "temperature": cTemp,
        "humidity": humidity,
        "MAGIC": MAGIC,
        "VERSION": VERSION
    }

    message = str.encode(json.dumps(message, indent=4))
    return message


def tcp_send(message):
    # Send data over TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, TCP_PORT))
    s.sendall(message)
    # TODO: Add if there is an error connecting to the server, go find server IP.

    # data = s.recv(BUFFER_SIZE)
    s.close()


if __name__ == "__main__":
    # Constants
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DIR_PATH = os.path.dirname(__file__)
    CONFIG_PATH = os.path.join(DIR_PATH, 'sensor_config.json')

    with open(CONFIG_PATH) as file:
        config = json.load(file)

    # Set up the TCP client
    SERVER_IP = config["SERVER_IP"]
    TCP_PORT = config["TCP_PORT"]
    UDP_PORT = int(config["UDP_PORT"])
    BUFFER_SIZE = int(config["BUFFER_SIZE"])
    SENSOR_ID = config["SENSOR_ID"]
    VERSION = config["VERSION"]
    MAGIC = config["MAGIC"]

    if SENSOR_ID == '':
        # Request an ID from the server
        data, addr = udp_send("GET_ID")

        SERVER_IP = addr[0]
        TCP_PORT = data["TCP_PORT"]
        SENSOR_ID = data["SENSOR_ID"]

        config["SERVER_IP"] = SERVER_IP
        config["TCP_PORT"] = TCP_PORT
        config["SENSOR_ID"] = SENSOR_ID

        with open(CONFIG_PATH, 'w') as file:
            json.dump(config, file, indent=4)

    if SERVER_IP == '' or TCP_PORT == '':
        # Request an IP from the server
        data, addr = udp_send("GET_IP")

        SERVER_IP = addr[0]
        TCP_PORT = data["TCP_PORT"]

        config["SERVER_IP"] = SERVER_IP
        config["TCP_PORT"] = TCP_PORT

        with open(CONFIG_PATH, 'w') as file:
            json.dump(config, file, indent=4)

    SENSOR_ID = int(SENSOR_ID)
    TCP_PORT = int(TCP_PORT)

    data = get_measurement()
    message = data_to_message(data)
    tcp_send(message)
