# syntax=docker/dockerfile:1

FROM python:3.12-slim-bullseye

WORKDIR /python-docker

ENV IP_ADDR=192.168.1.156
ENV PC_VERSION=v2.0.0

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]