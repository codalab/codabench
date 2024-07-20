FROM node:10

WORKDIR /app

# Install packages
ADD package.json .

COPY ./src ./src

RUN npm install && export PATH=./node_modules/.bin:$PATH && npm run build-stylus && npm run build-riot && npm run concat-riot

FROM python:3.9

RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1


RUN curl -sSL https://install.python-poetry.org | python3 -
# Poetry location so future commands (below) work
ENV PATH $PATH:/root/.local/bin
# Want poetry to use system python of docker container
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

COPY pyproject.toml ./
COPY poetry.lock ./

RUN poetry install

WORKDIR /app

COPY ./src ./src
COPY manage.py .
COPY package.json .

COPY --from=0 /app/src/static/generated /app/src/static/generated
