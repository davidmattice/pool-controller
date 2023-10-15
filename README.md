# Simple Pentair Screenlogic Pool Controller

Flask Web Application to controller a Pentair Screenlogic System

With special thanks to the developers of [screenlogic.py](https://github.com/dieselrabbit/screenlogicpy/tree/master)

Building and Running
- set IP_ADD to the IP address of the controller
- docker build --tag pool-controller .
- docker stop pool-controller;docker rm pool-controller;docker run -d -p 5000:5000 --name pool-controller pool-controller
