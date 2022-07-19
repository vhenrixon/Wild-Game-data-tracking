# syntax=docker/dockerfile:1


FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python
COPY . .



CMD [ "python3", "app.py"]
