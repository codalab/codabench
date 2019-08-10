#!/usr/bin/env bash

# Start containers
docker-compose -f docker-compose.yml -f docker-compose.selenium.yml up -d

# Run tests with optional arguments
klass=
if [ "$1" == "-k" ]; then
    shift
    klass=$1
    docker-compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/ -m e2e -k $klass
else
    docker-compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/ -m e2e
fi

# Clean up
docker-compose -f docker-compose.yml -f docker-compose.selenium.yml stop selenium
docker-compose -f docker-compose.yml -f docker-compose.selenium.yml rm -f selenium
