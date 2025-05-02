# RPI-temperature

Raspberry pi temperature measurement sensor and server code for environmental monitoring. 
The SHT31 sensor periodically takes temperature and humidity measurements.
It sends the processed data to the server using TCP.
The server stores the data in a sqlite3 database.

<b> DEPENDENCIES </b>
python3-smbus

<b> SET UP </b>
The user should set up a cronjob or some other scheduling task to keep both the server running.
The user also needs to set up a sqlite3 database that the server will use. 

<b>Optional</b> The user could set up a GUI for viewing the gathered data. In our case GRAFANA was used.


<b> Adding a new sensor: </b> 

1. Download the dependencies i.e. the smbus library for python


2. Use the sensor initialization [script](/sensor/sensor_init.py) to configure the server's IP, port and the sensor's ID. The script can also create a systemd service for you automatically. Manual configuration possible through [config_file](/sensor/sensor_config.py).


3. <b>Optional</b> Create a new panel on Grafana by clicking on an existing panel ...->more->duplicate. On the new panel ...->edit change the ID by which the table is selected to the new sensor’s ID.


<b> Switching to a new network: </b>
1. First the sensors and server should be given the new network’s SSID and PASSWORD e.g. 
[a Method 2: Enable Wifi via wpa_supplicant do this using an SD-card reader.](https://www.seeedstudio.com/blog/2021/01/25/three-methods-to-configure-raspberry-pi-wifi/?srsltid=AfmBOopN5twctvxUWjDAO6SzB95za2vgWbr4DA9oEp3GeQ7nkWzSwtuG)


2. Reconfigure the IP address in the following files:
[a sensor_config.json](/sensor/sensor_config.json), 
[a server_config.json](/server/server_config.json)
for the sensor and server respectively. For the sensor you can also use its initialization [script](/sensor/sensor_init.py)



