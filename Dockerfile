FROM python:3.9

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

# Poetry location so future commands (below) work
ENV PATH $PATH:/root/.local/bin

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml ./
COPY poetry.lock ./
# Want poetry to use system (docker container) python
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

RUN poetry install

WORKDIR /app
