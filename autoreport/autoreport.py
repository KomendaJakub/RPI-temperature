#!/usr/bin/env python3

import datetime as dt
from calendar import monthrange
import sqlite3
import zipfile
import os
import json

import smtplib
from email.message import EmailMessage

with open("/home/pi/Documents/RPI-temperature/autoreport/autoreport_config.json") as file:
    config = json.load(file)

EMAIL = config["EMAIL"]
PASSWORD = config["PASSWORD"]
MAIL_SERVER = config["MAIL_SERVER"]
DESTINATION = config["DESTINATION"]

today = dt.datetime.now()
first_day = today.replace(day=1, hour=0, minute=0,
                          second=0, microsecond=0) - dt.timedelta(1)
last_date = monthrange(today.year, today.month)[1]
last_day = today.replace(day=last_date, hour=23,
                         minute=59, second=59, microsecond=0)
data = [str(int(first_day.timestamp())), str(int(last_day.timestamp()))]

con = sqlite3.connect("/media/temp_data.db")
cur = con.cursor()

res = cur.execute("SELECT * FROM sensors WHERE (time BETWEEN ? AND ?);", data)
lines = res.fetchall()

month_year = today.strftime("%m_%y")
file_name = month_year + "_raw_temp" + ".zip"
with open(file_name, "w") as file:
    for line in lines:
        mp = map(float, line)
        mp = map(str, mp)
        file.write(",".join(list(mp)) + "\n")


with zipfile.ZipFile(file_name, "w", zipfile.ZIP_DEFLATED) as zipped:
    zipped.write(file_name)

msg = EmailMessage()

msg.set_content("Dobry den, \n Prosim pripravte spravu z interneho merania teploty a vlhkosti za mesiac " + month_year.replace("_", "/") +
                " podla manualu. \n V prilohe najdete data, ktore treba prilozit. \n Dakujem! \n\n\n Toto je automatizovana sprava, prosim neodpovedajte na nu.")

msg['Subject'] = "Data z merania " + month_year
msg['From'] = EMAIL
msg['To'] = DESTINATION

try:
    with open(file_name, 'rb') as file:
        data = file.read()
    msg.add_attachment(data, maintype='application',
                       subtype='zip', filename=file_name)

except Exception as err:
    print(err)

try:
    with smtplib.SMTP_SSL(MAIL_SERVER, 465) as smtp:
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)

except Exception as err:
    print(err)

os.remove(file_name)
