from flask import Flask, render_template, request, url_for, flash, redirect
import sys

app = Flask(__name__)

PoolActive = True
PoolTempSet = 80
SpaTempSet = 96

def PoolTempSetting(tempchange):
  global PoolTempSet
  if tempchange == "increase":
    PoolTempSet += 1
  else:
    PoolTempSet -= 1
  return PoolTempSet

def SpaTempSetting(tempchange):
  global SpaTempSet
  if tempchange == "increase":
    SpaTempSet += 1
  else:
    SpaTempSet -= 1
  return SpaTempSet

@app.route('/', methods=['GET', 'POST'])
def index():
  global PoolActive
  PoolTemp=80
  SpaTemp=96
  if request.method == 'POST':
    activate = request.form.get('activate')
    if activate is not None:
      if activate == "poolon":
        PoolActive=True
      else:
        PoolActive=False
    tempchange = request.form.get('temp')
    if tempchange is not None:
      if PoolActive == True:
        PoolTemp = PoolTempSetting(tempchange)
      else:
        SpaTemp = SpaTempSetting(tempchange)
     
  # return render_template('index.html', PoolTemp=PoolTemp, SpaTemp=SpaTemp)
  return render_template('index.html', pooltemp=PoolTemp, spatemp=SpaTemp, poolactive=PoolActive, debug=None)
