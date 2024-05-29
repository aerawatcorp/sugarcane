FROM python:3.8-slim-buster

WORKDIR /app

RUN apt update 
RUN apt install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install pip-tools

COPY ./requirements.txt /tmp/requirements.txt
RUN pip-sync /tmp/requirements.txt
