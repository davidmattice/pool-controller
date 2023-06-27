import asyncio
import string
import json
import argparse
import sys
import pprint
from flask import Flask, render_template, request, url_for, flash, redirect
from screenlogicpy.gateway import ScreenLogicGateway

app = Flask(__name__)

SPA_CIRCUIT = 500
BLOWER_CIRCUIT = 501
POOL_LIGHT_CIRCUIT = 502
SPA_LIGHT_CIRCUIT = 503
POOL_CIRCUIT = 505

CIRCUIT_OFF = 0
CIRCUIT_ON = 1

POOL_BODY = 0
SPA_BODY = 1


async def setTemp(gateway, body, setTemp, tempchange = None):
  if tempchange == "increase":
    newTemp = setTemp + 1
  elif tempchange == "decrease":
    newTemp = setTemp - 1
  if newTemp != setTemp:
    success = await gateway.async_set_heat_temp(body, newTemp)
  return newTemp

async def setCircuit(gateway, circuit, state):
  success = await gateway.async_set_circuit(circuit, state)
  if success == True:
    if state == CIRCUIT_ON:
      return CIRCUIT_OFF
    else:
      return CIRCUIT_ON
  return state


async def getGatewayData():
  gateway = ScreenLogicGateway()
  hosts = [{"ip": "192.168.1.174", "port": "80"}]
  await gateway.async_connect(**hosts[0])
  await gateway.async_update()
  await gateway.async_disconnect()
  return( gateway )

@app.route('/', methods=['GET', 'POST'])
async def index():
  HeatActive = False
  tempchange = None
  activate = None
  success = None

  gateway = await getGatewayData()
  systemStatus = gateway.get_data("controller", "sensor", "state", "value")
  airTemp = gateway.get_data("controller", "sensor", "air_temperature", "value")
  poolRunning = gateway.get_data("circuit", POOL_CIRCUIT, "value")
  poolTemp = gateway.get_data("body", 0, "last_temperature", "value")
  poolSetTemp = gateway.get_data("body", 0, "heat_setpoint", "value")
  poolHeatMode = gateway.get_data("body", 0, "heat_mode", "value")
  poolHeatState = gateway.get_data("body", 0, "heat_state", "value")
  spaRunning = gateway.get_data("circuit", SPA_CIRCUIT, "value")
  spaTemp = gateway.get_data("body", 1, "last_temperature", "value")
  spaSetTemp = gateway.get_data("body", 1, "heat_setpoint", "value")
  spaHeatMode = gateway.get_data("body", 1, "heat_mode", "value")
  spaHeatState = gateway.get_data("body", 1, "heat_state", "value")
  blowerRunning = gateway.get_data("circuit", BLOWER_CIRCUIT, "value")
  
  
  if request.method == 'POST':
    activate = request.form.get('activate')
    if activate is not None:
      if activate == "poolon":
        #spaRunning = await setCircuit(gateway, SPA_CIRCUIT, CIRCUIT_OFF)
        poolRunning = await setCircuit(gateway, POOL_CIRCUIT, CIRCUIT_ON)
        HeatActive = False
        BlowerActive = False
      elif activate == "pooloff":
        poolRunning = await setCircuit(gateway, POOL_CIRCUIT, CIRCUIT_OFF)
        HeatActive = False
        BlowerActive = False
      elif activate == "spaon":
        #poolRunning = await setCircuit(gateway, POOL_CIRCUIT, CIRCUIT_OFF)
        poolRunning = 0
        spaRunning = await setCircuit(gateway, SPA_CIRCUIT, CIRCUIT_ON)
        HeatActive = False
        BlowerActive = False
      elif activate == "spaoff":
        spaRunning = await setCircuit(gateway, SPA_CIRCUIT, CIRCUIT_OFF)
        HeatActive = False
        BlowerActive = False
      elif activate == "heaton":
        HeatActive = True
      elif activate == "heatoff":
        HeatActive = False
      elif activate == "bloweron":
        BlowerActive = True
      elif activate == "bloweroff":
        BlowerActive = False

    tempchange = request.form.get('temp')
    if tempchange is not None:
      if poolRunning:
        poolSetTemp = await setTemp(gateway, POOL_BODY, poolSetTemp, tempchange)
      elif spaRunning:
        spaSetTemp = await setTemp(gateway, SPA_BODY, spaSetTemp, tempchange)
     
  return render_template('index.html', systemstatus=systemStatus, poolactive=poolRunning, spaactive=spaRunning, heatactive=HeatActive, bloweractive=blowerRunning, 
                         airtemp=airTemp, pooltemp=poolTemp, poolsettemp=poolSetTemp, spatemp=spaTemp, spasettemp=spaSetTemp, 
                         debug=None)
