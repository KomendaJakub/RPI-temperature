#!/usr/bin/env python3

import os
import json
import getpass
import pwd
import subprocess

try:
    import smbus
except ImportError:
    print("You don't have the smbus library installed.")
    print("Trying to install.")
    err = subprocess.run(f"sudo apt install python3-smbus", shell=True)


os.chdir(os.path.dirname(os.path.abspath(__file__)))
DIR_PATH = os.path.dirname(__file__)
SCRIPT_PATH = os.path.join(DIR_PATH, 'sht31.py')
SYSTEMD_PATH = "/etc/systemd/system/"


def process_answer(answer):
    answer = answer.strip().lower()
    if answer == "y" or answer == "yes":
        return True
    else:
        return False


answer = input("Do you wish to set up the config file? (y/n) ")
if process_answer(answer):
    server_IP = input("Please provide your server's IP: ")
    server_port = input(
        "Please provide the port your server is listening on: ")
    sensor_ID = input("Please provide this sensor's ID: ")

    CONFIG_PATH = os.path.join(DIR_PATH, 'sensor_config.json')

    json_dict = {
        "SERVER_IP": server_IP.strip(),
        "SERVER_PORT": server_port.strip(),
        "SENSOR_ID": sensor_ID.strip()
    }

    with open(CONFIG_PATH, 'w') as file:
        file.write(json.dumps(json_dict, indent=4))

    print("Finished config file setup.")


# From this point on the script is completely unsafe as it allows the user
# to inject arbitrary code to the shell and execute it.
# This script is meant for personal use only and is not production grade.

answer = input(
    "Do you wish to set up a systemd service to measure data periodically? (y/n) ")
if process_answer(answer):

    user = getpass.getuser()

    if user != 'root':
        print("This script needs to be executed with administrative privileges so that systemd can be configured, try again with sudo.")
        raise SystemExit()

    service_user = input(
        "Which user would you like to execute the sensor script? (default: pi) ").strip()

    if service_user == "":
        service_user = "pi"
    try:
        pwd.getpwnam(service_user)
    except KeyError:
        print(f"User {service_user} does not exist.")
        raise SystemExit()

    service_name = input(
        "What should be the name of your service? (default: sensor) ")
    service_name = service_name.strip()
    if service_name == "":
        service_name = "sensor"

    service_path = os.path.join(SYSTEMD_PATH, f"{service_name}.service")
    timer_path = os.path.join(SYSTEMD_PATH, f"{service_name}.timer")
    if os.path.isfile(service_path) or os.path.isfile(timer_path):
        answer = input(
            "Service with this name already exists. Do you wish to override it? (y/n) ")
        if not process_answer(answer):
            raise SystemExit()

    service_period = input(
        "Input the measurement period for the server in seconds: (default: 60) ").strip()
    if service_period == "":
        service_period = 60
    else:
        service_period = int(service_period)

    print("Creating the service!")

    lines = [
        "[Unit]\n",
        "Description=Running the sensor\n",
        "\n",
        "[Service]\n",
        "Type=oneshot\n",
        f"ExecStart=/usr/bin/python3 {SCRIPT_PATH}\n",
        f"User={service_user}\n"
    ]

    with open(f'/etc/systemd/system/{service_name}.service', 'w') as file:
        file.writelines(lines)

    lines = [
        "[Unit]\n",
        f"Description=Run my python script every {service_period} seconds\n",
        "\n",
        "[Timer]\n",
        f"OnUnitActiveSec={service_period}s\n"
        "OnBootSec=60s\n",
        f"AccuracySec={60 if service_period >= 60 else service_period/2}s\n",
        "\n",
        "[Install]\n",
        "WantedBy=timers.target\n"
    ]

    with open(f'/etc/systemd/system/{service_name}.timer', 'w') as file:
        file.writelines(lines)

    print("Reloading the systemctl daemon!")
    err = subprocess.run("sudo systemctl daemon-reload",
                         shell=True, check=True)
    if err.returncode != 0:
        print(err)
        print("Error could not reload daemon.")
        raise SystemExit()

    print("Enabling the timer!")
    err = subprocess.run(f"sudo systemctl enable {
                         service_name}.timer", shell=True)
    if err.returncode != 0:
        print(err)
        print("Error could not enable the timer")
        raise SystemExit()

    print("Starting the timer!")
    err = subprocess.run(f"sudo systemctl start {
                         service_name}.timer", shell=True)
    if err.returncode != 0:
        print(err)
        print("Error could start the timer")
        raise SystemExit()
