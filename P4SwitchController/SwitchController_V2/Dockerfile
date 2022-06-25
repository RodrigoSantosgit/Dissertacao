# syntax=docker/dockerfile:1
FROM python:3

RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    iproute2 \
    tcpdump

RUN pip3 install p4runtime && pip3 install ipython && pip3 install ipaddr && pip3 install protobuf==3.20.1

WORKDIR /usr/src/app

COPY . .

