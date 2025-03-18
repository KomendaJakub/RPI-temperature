#!/usr/bin/env python3

import socket
import sqlite3
import re
import logging
import json
import os

# Constants
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR_PATH, 'server_config.json')
LOG_PATH = os.path.join(DIR_PATH, 'sensor.log')

# Setup the TCP server
with open(CONFIG_PATH) as file:
    config = json.load(file)

SERVER_IP = config["SERVER_IP"]
SERVER_PORT = int(config["SERVER_PORT"])
DATABASE_PATH = config(["DATABASE_ABS_PATH"])
BUFFER_SIZE = 1024

# Set up the logger
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(filename=LOG_PATH, format=FORMAT)

# Setup the database connection

# TODO : Change this to be DATABASE_PATH when changing to systemd scheduling
con = sqlite3.connect("/media/temp_data.db")
cur = con.cursor()
# cur.execute("CREATE TABLE sensors(sensor_id, time, temperature, humidity)")

# Set up regex
matcher = re.compile(r"(\d*\.\d*), (\d*), (\d*\.\d*), (\d*\.\d*)")

# Setup the TCP server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((SERVER_IP, SERVER_PORT))
s.listen(1)

while True:
    conn, addr = s.accept()
#    print("Connection address: ", addr)
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        d = data
#        print("Received data:", data)
        conn.send(data)
    conn.close()

    d = d.decode('utf-8')
    if matcher.match(d) is None:
        logger.warning(f"Unexpected data {d} from {addr}")
        continue

    d = d.split(", ")
    time = d[0]
    sensor_id = d[1]
    temperature = float(d[2])
    humidity = float(d[3])

    cur.execute("INSERT INTO sensors (sensor_id, time, temperature, humidity) VALUES (?, ?, ?, ?)",
                (sensor_id, time, temperature, humidity))
    con.commit()
