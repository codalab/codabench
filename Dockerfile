FROM python:3.8

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

ADD requirements.dev.txt .
ADD requirements.txt .
RUN pip install -U pip
RUN pip install -r requirements.dev.txt

WORKDIR /app
