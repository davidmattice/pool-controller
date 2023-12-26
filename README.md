# Simple Pentair Screenlogic Pool Controller

Flask Web Application to controller a Pentair Screenlogic System

With special thanks to the developers of [screenlogic.py](https://github.com/dieselrabbit/screenlogicpy/tree/master)


Building and Running
- docker build --tag pool-controller --build-arg VERSION=$(head -1 version.txt | cut -d = -f 2).
- docker stop pool-controller;docker rm pool-controller;docker run -d -p 5000:5000 --name pool-controller pool-controller
