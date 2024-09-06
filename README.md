# RPI-temperature
Raspberry pi temperature measurement server and client

<b> Adding a new sensor: </b> 

1. Copy the SD-card from an existing RPI zero using Balena-Etcher.

2. In the file /home/pi/Documents/sht31.py change the variable ID to one that is not in use.

3. Create a new panel on Grafana by clicking on an existing panel ...->more->duplicate
   On the new panel ...->edit change the WHERE ID="x" to the new ID -> save -> apply. Repeat this for both temperature and humidity.

<b> Switching to a new network: </b>
All the IP adresses have to be manually reconfigured in the sht31.py and server.py files respectively. 
