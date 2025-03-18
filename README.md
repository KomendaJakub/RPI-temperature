# RPI-temperature

Raspberry pi temperature measurement sensor and server code for environmental monitoring at HHES. 
The SHT31 sensor periodically takes temperature and humidity measurements.
It sends the processed data to the server using TCP.
The server stores the data in a sqlite3 database.


<b> SET UP </b>
The user should set up a cronjob or some other scheduling task to keep both the server and sensor code running. 
The user needs to set up a sqlite3 database that the server will use. You can find sample code in the sensor/sensor.py 

OPT: The user could set up a GUI for viewing the gathered data. In our case GRAFANA was used.


<b> Adding a new sensor: </b> 

1. Copy the SD-card from an existing RPI zero using Balena-Etcher.


2. In the file [a sensor_config.json](/sensor/sensor_config.json) change the variable ID to one that is not in use.


3. Create a new panel on Grafana by clicking on an existing panel ...->more->duplicate On the new panel ...->edit change the ID by which the table is selected to the new sensor’s ID.


<b> Switching to a new network: </b>
First the sensors should be given the new network’s SSID and PASSWORD, do this as documented here in: 
[a Method 2: Enable Wifi via wpa_supplicant do this using an SD-card reader.](https://www.seeedstudio.com/blog/2021/01/25/three-methods-to-configure-raspberry-pi-wifi/?srsltid=AfmBOopN5twctvxUWjDAO6SzB95za2vgWbr4DA9oEp3GeQ7nkWzSwtuG)
<b>Do not try to power up the sensor before doing this as it will go into a boot loop!<b/>

Then you should connect the server and get its new IP address that will be used later. 
In the next step all the IP addresses have to be manually reconfigured in the following files:
[a sensor_config.json](/sensor/sensor_config.json)
[a server_config.json](/server/server_config.json)
for the sensor and server respectively.

For the sensors this has to be done without booting them, else they will go into a bootloop because they cannot connect to the server. 

