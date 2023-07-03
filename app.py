import asyncio
import string
import json
import argparse
import sys
import pprint
import time
from flask import Flask, render_template, request, url_for, flash, redirect
from screenlogicpy.gateway import ScreenLogicGateway

LOCAL_TESTING = True

SPA_CIRCUIT = 500
BLOWER_CIRCUIT = 501
POOL_LIGHT_CIRCUIT = 502
SPA_LIGHT_CIRCUIT = 503
POOL_CIRCUIT = 505

CIRCUIT_OFF = 0
CIRCUIT_ON = 1

POOL_BODY = 0
SPA_BODY = 1

HEAT_OFF = 0
HEATER_ON = 3

gateway = None

equipment_status = {
  'last_pass': None,
  'last_updated': None,
  'systemStatus': 0,
  'airTemp': 0, 
  'poolRunning': 0,
  'poolTemp': 0,
  'poolSetTemp': 0,
  'poolHeatMode': 0,
  'poolHeatState': 0,
  'spaRunning': 0,
  'spaTemp': 0,
  'spaSetTemp': 0,
  'spaHeatMode': 0,
  'spaHeatState': 0,
  'blowerRunning': 0,
  'heaterRunning': 0
}
TEST_DEFAULTS = [None, None, 1, 99, 1, 75, 70, 0, 0, 0, 75, 95, 0, 0, 0, 0]

#
# Configure the app for Flask
#
app = Flask(__name__)

#
# Ensure we don't run too often
#
def time_passed(oldepoch, seconds):
  return time.time() - oldepoch >= seconds

#
# Adjust the temperature setting on the specific body of water
#
async def setTemp(body, setTemp, tempchange = None):
  if tempchange == "increase":
    newTemp = setTemp + 1
  elif tempchange == "decrease":
    newTemp = setTemp - 1
  
  if LOCAL_TESTING:
    return( newTemp )
  
  if newTemp != setTemp:
    success = await gateway.async_set_heat_temp(body, newTemp)
  if success:
    return newTemp
  return setTemp

#
# Turn the heater on or off
#
async def setHeatMode(body, mode):
  global gateway

  if LOCAL_TESTING:
    return( mode )
  
  success = await gateway.async_set_heat_mode(body, mode)
  if success != True:
    if mode == HEATER_ON:
      return HEAT_OFF
    else:
      return HEATER_ON
  return mode

#
# Turn on or off a circuit
#
async def setCircuit(circuit, state):
  global gateway

  if LOCAL_TESTING:
    return(state)
  
  success = await gateway.async_set_circuit(circuit, state)
  if success != True:
    if state == CIRCUIT_ON:
      return CIRCUIT_OFF
    else:
      return CIRCUIT_ON
  return state

#
# Connect to the Gateway
#
async def gatewayConnect():
  global gateway

  if LOCAL_TESTING:
    return( True )
  
  hosts = [{"ip": "192.168.1.174", "port": "80"}]
  success = await gateway.async_connect(**hosts[0])
  return( success )

#
# Disconnect from the Gateway
#
async def gatewayDisconnect():
  global gateway

  if LOCAL_TESTING:
    return( True )
  
  success = await gateway.async_disconnect()
  return( success )

#
# Pull updated data from the gateway
#
async def gatewayUpdate():
  global gateway

  if LOCAL_TESTING:
    if equipment_status['last_updated'] == None:
      equipment_status.update(zip(equipment_status,TEST_DEFAULTS))
    return( True )
  
  success = await gateway.async_update()  
  return( success )

def gatewayGetData(*args):
  global gateway

  data = gateway.get_data(*args)
  return( data )



#
# Main application code
#
# 
@app.route('/', methods=['GET', 'POST'])
async def index():
  global equipment_status
  global gateway
  heatRunning = 0
  tempchange = None
  activate = None
  success = None

  # Initialize the fist time in
  if equipment_status['last_pass'] == None:
    equipment_status['last_pass'] = time.time() - 60

  # Ensure we don't call this too often - leave at least XX seconds between calls
  if time_passed(equipment_status['last_pass'], 20):
    equipment_status['last_pass'] = time.time()
    success = await gatewayConnect()
    if success:
      await gatewayUpdate()
      equipment_status['last_updated'] = time.time()
      if LOCAL_TESTING == False:
        equipment_status['systemStatus'] = gateway.get_data("controller", "sensor", "state", "value")
        equipment_status['airTemp'] = gateway.get_data("controller", "sensor", "air_temperature", "value")
        equipment_status['poolRunning'] = gateway.get_data("circuit", POOL_CIRCUIT, "value")
        equipment_status['poolTemp'] = gateway.get_data("body", 0, "last_temperature", "value")
        equipment_status['poolSetTemp'] = gateway.get_data("body", 0, "heat_setpoint", "value")
        equipment_status['poolHeatMode'] = gateway.get_data("body", 0, "heat_mode", "value")
        equipment_status['poolHeatState'] = gateway.get_data("body", 0, "heat_state", "value")
        equipment_status['spaRunning'] = gateway.get_data("circuit", SPA_CIRCUIT, "value")
        equipment_status['spaTemp'] = gateway.get_data("body", 1, "last_temperature", "value")
        equipment_status['spaSetTemp'] = gateway.get_data("body", 1, "heat_setpoint", "value")
        equipment_status['spaHeatMode'] = gateway.get_data("body", 1, "heat_mode", "value")
        equipment_status['spaHeatState'] = gateway.get_data("body", 1, "heat_state", "value")
        equipment_status['blowerRunning'] = gateway.get_data("circuit", BLOWER_CIRCUIT, "value")
      await gatewayDisconnect()
    
  if request.method == 'POST':
    success = await gatewayConnect()
    if success:
      await gatewayUpdate()
      activate = request.form.get('activate')
      if activate is not None:
        if activate == "poolon":
          #spaRunning = await setCircuit(gateway, SPA_CIRCUIT, CIRCUIT_OFF)
          equipment_status['spaRunning'] = 0
          equipment_status['poolRunning'] = await setCircuit(POOL_CIRCUIT, CIRCUIT_ON)
        elif activate == "pooloff":
          equipment_status['poolRunning'] = await setCircuit(POOL_CIRCUIT, CIRCUIT_OFF)
        elif activate == "spaon":
          #poolRunning = await setCircuit(gateway, POOL_CIRCUIT, CIRCUIT_OFF)
          equipment_status['poolRunning'] = 0
          equipment_status['spaRunning'] = await setCircuit(SPA_CIRCUIT, CIRCUIT_ON)
        elif activate == "spaoff":
          equipment_status['spaRunning'] = await setCircuit(SPA_CIRCUIT, CIRCUIT_OFF)
        elif activate == "heaton":
          if equipment_status['poolRunning']:
            equipment_status['poolHeatMode'] = await setHeatMode(POOL_BODY, HEATER_ON)
          elif equipment_status['spaRunning']:
            equipment_status['spaHeatMode'] = await setHeatMode(SPA_BODY, HEATER_ON)
        elif activate == "heatoff":
          if equipment_status['poolRunning']:
            equipment_status['poolHeatMode'] = await setHeatMode(POOL_BODY, HEAT_OFF)
          elif equipment_status['spaRunning']:
            equipment_status['spaHeatMode'] = await setHeatMode(SPA_BODY, HEAT_OFF)
        elif activate == "bloweron":
          if equipment_status['spaRunning']:
            equipment_status['blowerRunning'] = await setCircuit(BLOWER_CIRCUIT, CIRCUIT_ON)
        elif activate == "bloweroff":
          equipment_status['blowerRunning'] = await setCircuit(BLOWER_CIRCUIT, CIRCUIT_OFF)

      tempchange = request.form.get('temp')
      if tempchange is not None:
        if equipment_status['poolRunning']:
          equipment_status['poolSetTemp'] = await setTemp(POOL_BODY, equipment_status['poolSetTemp'], tempchange)
        elif equipment_status['spaRunning']:
          equipment_status['spaSetTemp'] = await setTemp(SPA_BODY, equipment_status['spaSetTemp'], tempchange)
      
      # At the end of the POST disconnect
      await gatewayDisconnect()

  # Update the heater information based on any changes made
  if equipment_status['poolRunning']:
    if equipment_status['poolHeatMode'] != 0 and equipment_status['poolHeatState'] != 0:
      heatRunning = 2
    elif equipment_status['poolHeatMode'] != 0 and equipment_status['poolHeatState'] == 0:
      heatRunning = 1
    else:
      heatRunning = 0
  if equipment_status['spaRunning']:
    if equipment_status['spaHeatMode'] != 0 and equipment_status['spaHeatState'] != 0:
      heatRunning = 2
    elif equipment_status['spaHeatMode'] != 0 and equipment_status['spaHeatState'] == 0:
      heatRunning = 1
    else:
      heatRunning = 0

  # Update the page
  return render_template('index.html', 
                         systemstatus=equipment_status['systemStatus'], 
                         poolactive=equipment_status['poolRunning'], 
                         spaactive=equipment_status['spaRunning'], 
                         heatactive=heatRunning, 
                         bloweractive=equipment_status['blowerRunning'], 
                         airtemp=equipment_status['airTemp'], 
                         pooltemp=equipment_status['poolTemp'], 
                         poolsettemp=equipment_status['poolSetTemp'], 
                         spatemp=equipment_status['spaTemp'],
                         spasettemp=equipment_status['spaSetTemp'], 
                         debug=equipment_status)

if __name__ == "__app__":
  gateway = ScreenLogicGateway()
