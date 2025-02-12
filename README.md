# RPI-temperature
Raspberry pi temperature measurement server and client

<b> Adding a new sensor: </b> 

1. Copy the SD-card from an existing RPI zero using Balena-Etcher.

2. In the file /home/pi/Documents/sht31.py change the variable ID to one that is not in use.

3. Add a table to the sqlite3 database /media/temp_data.db in the format sensor{ID} i.e. sensor0..sensor1

4. Create a new panel on Grafana by clicking on an existing panel ...->more->duplicate
   On the new panel ...->edit change the FROM part to the new  table name sensor{ID} -> save -> apply. Repeat this for both temperature and humidity.

<b> Switching to a new network: </b>
All the IP adresses have to be manually reconfigured in the sht31.py and server.py files respectively. This needs to happen in the space of the old wifi else the RPIs will fall into a bootloop
