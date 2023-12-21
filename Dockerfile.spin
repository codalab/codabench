FROM python:3.8

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

WORKDIR /app

# add copy command to copy . to /app
COPY . /app

RUN pip install -U pip
RUN pip install -r /app/requirements.dev.txt