# syntax=docker/dockerfile:1

FROM python:3.13-slim-bullseye

WORKDIR /python-docker

# Allow setting/overriding the two environment variable as command line agruments
ARG IP_ADDR=192.168.81.124
ARG VERSION=Unknown

# Set the two environment variables
ENV PC_IP_ADDR=${IP_ADDR}
ENV PC_VERSION=${VERSION}

# Install required python libraries
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

# Run Flask
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
