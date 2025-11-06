# Stage 1: Node.js builder
FROM node:10 AS builder

# Setup volume
WORKDIR /app

# Install packages
ADD package.json .
RUN npm install

# Copy all files and build
COPY . .
RUN export PATH=./node_modules/.bin:$PATH && npm run build-stylus && npm run build-riot && npm run concat-riot

# Stage 2: Python/Django (identical to main Dockerfile)
FROM python:3.9.20

# Install system dependencies
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH=$PATH:/root/.local/bin

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

# Set work directory before copying files
WORKDIR /app

# Copy only dependency descriptors first (for caching)
COPY pyproject.toml poetry.lock ./
RUN poetry install

# Copy the rest of the application code
COPY . /app

# Copy built files from builder stage
COPY --from=builder /app /app

RUN ./manage.py collectstatic --noinput
