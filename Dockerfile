FROM python:3.10.0

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
# Poetry location so future commands (below) work

ENV PATH=$PATH:/root/.local/bin
# Want poetry to use system python of docker container
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install 


WORKDIR /app
