FROM python:3.9.19-slim-bullseye

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY ./ ./

EXPOSE 2999/tcp
EXPOSE 2999/udp