# Stage 1: Node.js builder
FROM node:10 AS builder

# Setup volume
WORKDIR /app

# Install packages
ADD package.json .
RUN npm install

COPY . .
RUN export PATH=./node_modules/.bin:$PATH && npm run build-stylus && npm run build-riot && npm run concat-riot

# Stage 2: Python/Django
FROM python:3.9.20

# Install system dependencies
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/root/.local/bin

RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install
RUN pip install kubernetes

COPY . /app

# Copy built files from builder stage
COPY --from=builder /app /app

RUN ./manage.py collectstatic --noinput
