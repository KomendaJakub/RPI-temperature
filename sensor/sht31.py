#!/usr/bin/env python3

# Imports
import socket
import smbus
import time
import os
import json


# Constants
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR_PATH, 'sensor_config.json')

with open(CONFIG_PATH) as file:
    config = json.load(file)

# Set up the TCP client
SERVER_IP = config["SERVER_IP"]
SERVER_PORT = int(config["SERVER_PORT"])
BUFFER_SIZE = 1024
SENSOR_ID = int(config["SENSOR_ID"])

if SENSOR_ID == '':
    raise SystemExit(
        "No sensor ID was specified. Specify in sensor_config.json.")

# Function definitions


def get_measurement():

    bus.write_i2c_block_data(0x45, 0x2C, [0x06])
    time.sleep(0.5)
# SHT31 address, 0x45(68)
# Read data back from 0x00(00), 6 bytes
# Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
    data = bus.read_i2c_block_data(0x45, 0x00, 6)
    return data


def data_to_message(data):
    # Convert the data
    temp = data[0] * 256 + data[1]
    cTemp = -45 + (175 * temp / 65535.0)
#    fTemp = -49 + (315 * temp / 65535.0)
    humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
    message = str(time.time()) + ", " + str(SENSOR_ID) + ", " + \
        str(cTemp) + ", " + str(humidity)
    message = message.encode('utf-8')
    return message


def send_to_server(message):
    # Send data over TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    s.send(message)
#        data = s.recv(BUFFER_SIZE)
    s.close()


# Get I2C bus
bus = smbus.SMBus(1)
data = get_measurement()
message = data_to_message(data)
send_to_server(message)
