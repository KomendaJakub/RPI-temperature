#!/usr/bin/env python3

import socket
import sqlite3
import re
import logging

# Set up the logger
logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(filename="./server.log", format=FORMAT)

# Setup the database connection
con = sqlite3.connect("/media/temp_data.db")
cur = con.cursor()
#cur.execute("CREATE TABLE sensor0(time, temperature, humidity)")
#cur.execute("CREATE TABLE sensor1(time, temperature, humidity)")
#cur.execute("CREATE TABLE sensor2(time, temperature, humidity)")

# Set up regex
matcher = re.compile(r"(\d*\.\d*), (\d*), (\d*\.\d*), (\d*\.\d*)")

# Setup the TCP server
TCP_IP = '192.168.0.247'
TCP_PORT = 51378
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
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
    id = d[1]
    temperature = float(d[2])
    humidity = float(d[3])

    cur.execute("INSERT INTO sensor" + id +" VALUES (?, ?, ?)", (time, temperature, humidity))
    con.commit()


