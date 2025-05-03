#!/usr/bin/env python3

import datetime as dt
import sqlite3
import zipfile
import os
import json

import smtplib
from email.message import EmailMessage

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR_PATH, 'autoreport_config.json')

with open(CONFIG_PATH) as file:
    config = json.load(file)

EMAIL = config["EMAIL"]
PASSWORD = config["PASSWORD"]
MAIL_SERVER = config["MAIL_SERVER"]
DESTINATION = config["DESTINATION"]
DATABASE_PATH = config["DATABASE_PATH"]

today = dt.datetime.now()
last_day = today.replace(day=1, hour=23, minute=59,
                         second=59, microsecond=0) - dt.timedelta(days=1)

first_day = last_day.replace(day=1)

data = [str(int(first_day.timestamp())), str(int(last_day.timestamp()))]

con = sqlite3.connect(DATABASE_PATH)
cur = con.cursor()

res = cur.execute("SELECT * FROM sensors WHERE (time BETWEEN ? AND ?);", data)
lines = res.fetchall()

month_year = today.strftime("%m_%y")
file_name = month_year + "_raw_temp"
with open(file_name + ".csv", "w") as file:
    for line in lines:
        mp = map(float, line)
        mp = map(str, mp)
        file.write(",".join(list(mp)) + "\n")


with zipfile.ZipFile("zip.zip", "w", zipfile.ZIP_DEFLATED) as zipped:
    zipped.write(file_name + ".csv")

msg = EmailMessage()

msg.set_content(f"""Dobrý deň, \n Prosím pripravte správu z interného merania teploty a vlhkosti za mesiac {month_year.replace(
    "_", "/")} podľa manuálu. \n V prílohe nájdete dáta, ktoré treba priložiť. \n Ďakujem! \n\n\n Toto je automatizovaná správa, prosím neodpovedajte na ňu.""")

msg['Subject'] = "Dáta z merania " + month_year
msg['From'] = EMAIL
msg['To'] = DESTINATION

try:
    with open("zip.zip", 'rb') as file:
        data = file.read()
    msg.add_attachment(data, maintype='application',
                       subtype='zip', filename=file_name + ".zip")

except Exception as err:
    print(err)

try:
    with smtplib.SMTP_SSL(MAIL_SERVER, 465) as smtp:
        smtp.login(EMAIL, PASSWORD)
        smtp.send_message(msg)

except Exception as err:
    print(err)

os.remove(file_name + ".csv")
os.remove("zip.zip")
