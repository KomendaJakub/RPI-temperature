#!/usr/bin/env python3

# Imports
import socket
import smbus
import logging
import time
import random
import os
import json


# Constants
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR_PATH, 'sensor_config.json')
LOG_PATH = os.path.join(DIR_PATH, 'sensor.log')

with open(CONFIG_PATH) as file:
    config = json.load(file)

# Set up the TCP client
SERVER_IP = config["SERVER_IP"]
SERVER_PORT = int(config["SERVER_PORT"])
BUFFER_SIZE = 1024
SENSOR_ID = int(config["SENSOR_ID"])

if SENSOR_ID == '':
    raise SystemExit()

# Set up the logger
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(filename=LOG_PATH, format=FORMAT)


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
    err = s.connect_ex((SERVER_IP, SERVER_PORT))
    if (err):
        if (err == 113):
            logging.error(f"Error {err} the server is down")
            time.sleep(random.randrange(0, 60))
        else:
            logging.critical(
                f"Error {err} unhandled case while connecting to server")
            time.sleep(random.randrange(0, 60))

    else:
        s.send(message)
#        data = s.recv(BUFFER_SIZE)
        s.close()
        time.sleep(60)


# Get I2C bus
bus = smbus.SMBus(1)


logging.info("Starting the program")

while True:
    try:
        data = get_measurement()
        message = data_to_message(data)
        send_to_server(message)

    except OSError as OSe:
        if OSe.errno == 110:
            logging.error(f"{OSe}")
            os.system("sudo reboot")
        logging.error(f"{OSe} I2C down")
        time.sleep(60)
    except Exception as e:
        logging.critical(f"Error {e} unhandled exception")
        time.sleep(60)
