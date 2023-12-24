import asyncio
import string
import json
import argparse
import sys
import pprint
import time
import os
from flask import Flask, render_template, request, url_for, flash, redirect
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const.common import ScreenLogicException

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

lights = [
  { "name": "Off", "id": 0 },
  { "name": "On", "id": 1 },
  { "name": "Color Swim", "id": 4 },
  { "name": "Party", "id": 5 },
  { "name": "Romance", "id": 6 },
  { "name": "Caribbean", "id": 7 },
  { "name": "American", "id": 8 },
  { "name": "Sunset", "id": 9 },
  { "name": "Royal", "id": 10 },
  { "name": "Blue", "id": 13 },
  { "name": "Green", "id": 14 },
  { "name": "Red", "id": 15 },
  { "name": "White", "id": 16 },
  { "name": "Magenta", "id": 17 },
  { "name": "Thumper", "id": 18 }
]
  
equipment_status = {
  'last_pass': None,
  'last_updated': None,
  'last_msg': "",
  'systemStatus': 0,
  'airTemp': 0, 
  'poolRunning': 0,
  'poolTemp': 0,
  'poolSetTemp': 0,
  'poolHeatMode': 0,
  'poolHeatState': 0,
  'poolLight': 0,
  'poolLightSetting': 0,
  'spaRunning': 0,
  'spaTemp': 0,
  'spaSetTemp': 0,
  'spaHeatMode': 0,
  'spaHeatState': 0,
  'spaLight': 0,
  'blowerRunning': 0,
  'heaterRunning': 0
}

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
# Set the mode for the pool light
#
async def setLightMode(current_mode, new_mode):
  global gateway
  global equipment_status
  ip = None                 # IP pulle dfrom Environment variable IP_ADDR
  hosts = None              # Hosts list to be passed to gateway connect
  msg = ""                  # Return an error message on error

  ip = os.getenv("IP_ADDR")
  if ip != None:
    hosts = [{"ip": ip, "port": "80"}]

    try:
      await gateway.async_connect(**hosts[0])
      await gateway.async_set_color_lights(new_mode)
      await gateway.async_disconnect()

    except ScreenLogicException as err:
      equipment_status['last_msg'] = err
      return(current_mode)

  return(new_mode)

#
# Adjust the temperature setting on the specific body of water
#
async def setTemp(body, set_temp, tempchange = None):
  new_temp = set_temp
  global gateway
  global equipment_status
  ip = None                 # IP pulle dfrom Environment variable IP_ADDR
  hosts = None              # Hosts list to be passed to gateway connect
  msg = ""                  # Return an error message on error

  if tempchange == "increase":
    new_temp = set_temp + 1
  elif tempchange == "decrease":
    new_temp = set_temp - 1

  if new_temp != set_temp:
    ip = os.getenv("IP_ADDR")
    if ip != None:
      hosts = [{"ip": ip, "port": "80"}]

      try:
        await gateway.async_connect(**hosts[0])
        await gateway.async_set_heat_temp(body, new_temp)
        await gateway.async_disconnect()

      except ScreenLogicException as err:
        equipment_status['last_msg'] = err
        return(set_temp)

      return(new_temp)

  return(set_temp)

#
# Turn the heater on or off
#
async def setHeatMode(body, current_mode, new_mode):
  global gateway
  global equipment_status
  ip = None                 # IP pulle dfrom Environment variable IP_ADDR
  hosts = None              # Hosts list to be passed to gateway connect
  msg = ""                  # Return an error message on error

  ip = os.getenv("IP_ADDR")
  if ip != None:
    hosts = [{"ip": ip, "port": "80"}]

    try:
      await gateway.async_connect(**hosts[0])
      await gateway.async_set_heat_mode(body, new_mode)
      await gateway.async_disconnect()

    except ScreenLogicException as err:
      equipment_status['last_msg'] = err
      return(current_mode)

  return(new_mode)

#
# Turn on or off a circuit
#
async def setCircuit(circuit, current_state, new_state):
  global gateway
  global equipment_status
  ip = None                 # IP pulle dfrom Environment variable IP_ADDR
  hosts = None              # Hosts list to be passed to gateway connect
  msg = ""                  # Return an error message on error

  ip = os.getenv("IP_ADDR")
  if ip != None:
    hosts = [{"ip": ip, "port": "80"}]

    try:
      await gateway.async_connect(**hosts[0])
      await gateway.async_set_circuit(circuit, new_state)
      await gateway.async_disconnect()

    except ScreenLogicException as err:
      equipment_status['last_msg'] = err
      return(current_state)

  return(new_state)

#
# Connect, pull adapter data and disconnect
#
async def updateGatewayData():
  global gateway
  global equipment_status
  ip = None                 # IP pulle dfrom Environment variable IP_ADDR
  hosts = None              # Hosts list to be passed to gateway connect
  msg = ""                  # Return an error message on error

  ip = os.getenv("IP_ADDR")
  if ip != None:
    hosts = [{"ip": ip, "port": "80"}]

    try:
      await gateway.async_connect(**hosts[0])
      await gateway.async_update()
      await gateway.async_disconnect()

    except ScreenLogicException as err:
      equipment_status['last_msg'] = err
      msg = err

  return(msg)

#
# Main Flask loop
# 
@app.route('/', methods=['GET', 'POST'])
async def index():
  global equipment_status
  global gateway

  heatRunning = 0
  plightmode = None
  tempchange = None
  activate = None
  success = None
  msg = ""

  # Initialize the fist time so there will be a call to get the status
  if equipment_status['last_pass'] == None:
    equipment_status['last_pass'] = time.time() - 60

  # Ensure we don't call this too often - leave at least XX seconds between calls
  if time_passed(equipment_status['last_pass'], 20):
    equipment_status['last_pass'] = time.time()
    msg = await updateGatewayData()
    if msg == "":
      equipment_status['last_updated'] = time.time()
      equipment_status['systemStatus'] = gateway.get_data("controller", "sensor", "state", "value")
      equipment_status['airTemp'] = gateway.get_data("controller", "sensor", "air_temperature", "value")
      equipment_status['poolRunning'] = gateway.get_data("circuit", POOL_CIRCUIT, "value")
      equipment_status['poolTemp'] = gateway.get_data("body", 0, "last_temperature", "value")
      equipment_status['poolSetTemp'] = gateway.get_data("body", 0, "heat_setpoint", "value")
      equipment_status['poolHeatMode'] = gateway.get_data("body", 0, "heat_mode", "value")
      equipment_status['poolHeatState'] = gateway.get_data("body", 0, "heat_state", "value")
      equipment_status['poolLight'] = gateway.get_data("circuit", POOL_LIGHT_CIRCUIT, "value")
      equipment_status['spaRunning'] = gateway.get_data("circuit", SPA_CIRCUIT, "value")
      equipment_status['spaTemp'] = gateway.get_data("body", 1, "last_temperature", "value")
      equipment_status['spaSetTemp'] = gateway.get_data("body", 1, "heat_setpoint", "value")
      equipment_status['spaHeatMode'] = gateway.get_data("body", 1, "heat_mode", "value")
      equipment_status['spaHeatState'] = gateway.get_data("body", 1, "heat_state", "value")
      equipment_status['spaLight'] = gateway.get_data("circuit", SPA_LIGHT_CIRCUIT, "value")
      equipment_status['blowerRunning'] = gateway.get_data("circuit", BLOWER_CIRCUIT, "value")

      # if the pool light is on, but we don't know the color, just set it to On
      if equipment_status['poolLight'] == 1 and equipment_status['poolLightSetting'] == 0:
        equipment_status['poolLightSetting'] = 1
    
  if request.method == 'POST':
    activate = request.form.get('activate')
    if activate is not None:
      if activate == "poolon":
        equipment_status['spaRunning'] = CIRCUIT_OFF
        equipment_status['poolRunning'] = await setCircuit(POOL_CIRCUIT, equipment_status['poolRunning'], CIRCUIT_ON)
      elif activate == "pooloff":
        equipment_status['poolRunning'] = await setCircuit(POOL_CIRCUIT, equipment_status['poolRunning'], CIRCUIT_OFF)
      elif activate == "spaon":
        equipment_status['poolRunning'] = CIRCUIT_OFF
        equipment_status['spaRunning'] = await setCircuit(SPA_CIRCUIT, equipment_status['spaRunning'], CIRCUIT_ON)
      elif activate == "spaoff":
        equipment_status['spaRunning'] = await setCircuit(SPA_CIRCUIT, equipment_status['spaRunning'], CIRCUIT_OFF)
      elif activate == "spalighton":
        equipment_status['spaLight'] = await setCircuit(SPA_LIGHT_CIRCUIT, equipment_status['spaLight'], CIRCUIT_ON)
      elif activate == "spalightoff":
        equipment_status['spaLight'] = await setCircuit(SPA_LIGHT_CIRCUIT, equipment_status['spaLight'], CIRCUIT_OFF)
      elif activate == "heaton":
        if equipment_status['poolRunning']:
          equipment_status['poolHeatMode'] = await setHeatMode(POOL_BODY, equipment_status['poolHeatMode'], HEATER_ON)
        elif equipment_status['spaRunning']:
          equipment_status['spaHeatMode'] = await setHeatMode(SPA_BODY, equipment_status['spaHeatMode'], HEATER_ON)
      elif activate == "heatoff":
        if equipment_status['poolRunning']:
          equipment_status['poolHeatMode'] = await setHeatMode(POOL_BODY, equipment_status['poolHeatMode'], HEAT_OFF)
        elif equipment_status['spaRunning']:
          equipment_status['spaHeatMode'] = await setHeatMode(SPA_BODY, equipment_status['spaHeatMode'], HEAT_OFF)
      elif activate == "bloweron":
        if equipment_status['spaRunning']:
          equipment_status['blowerRunning'] = await setCircuit(BLOWER_CIRCUIT, equipment_status['blowerRunning'], CIRCUIT_ON)
      elif activate == "bloweroff":
        equipment_status['blowerRunning'] = await setCircuit(BLOWER_CIRCUIT, equipment_status['blowerRunning'], CIRCUIT_OFF)

    tempchange = request.form.get('temp')
    if tempchange is not None:
      if equipment_status['poolRunning']:
        equipment_status['poolSetTemp'] = await setTemp(POOL_BODY, equipment_status['poolSetTemp'], tempchange)
      elif equipment_status['spaRunning']:
        equipment_status['spaSetTemp'] = await setTemp(SPA_BODY, equipment_status['spaSetTemp'], tempchange)
    
    # Update the pool light setting, if changed
    if request.form.get('poollightvalue') is not None:
      if int(request.form.get('poollightvalue')) == 0:
        equipment_status['poolLight'] = await setCircuit(POOL_LIGHT_CIRCUIT, equipment_status['poolLight'], CIRCUIT_OFF)
        equipment_status['poolLightSetting'] = int(request.form.get('poollightvalue'))
      else:
        if equipment_status['poolLight'] == 0:
          equipment_status['poolLight'] = await setCircuit(POOL_LIGHT_CIRCUIT, equipment_status['poolLight'], CIRCUIT_ON)
        await setLightMode(equipment_status['poolLightSetting'], int(request.form.get('poollightvalue')))
        equipment_status['poolLightSetting'] = int(request.form.get('poollightvalue'))

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

  # Ensure the light dropdowns are updated if the lights are changed from somewhere
  if equipment_status['poolLight'] == 0:
    poolLightSetting = 0
  else:
    poolLightSetting = equipment_status['poolLightSetting']

  # Update the page
  if success != False:
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
                          poollightsetting=poolLightSetting,
                          spalight=equipment_status['spaLight'],
                          lights=lights,
                          debug=equipment_status['last_msg'])
                          # debug=equipment_status)
                          # debug=equipment_status['poolLightSetting'])
                          # debug=gateway.get_data())
  else:
    return render_template('error.html')

if __name__ == "app":
  gateway = ScreenLogicGateway()

