#!/usr/bin/env bash

docker-compose -f docker-compose.yml -f docker-compose.selenium.yml up -d &&
klass=
if [ "$1" == "-k" ]; then
    shift
    klass=$1
    docker exec -it django py.test -k $klass
else
    docker exec -it django py.test -m e2e
fi
docker stop selenium &&
docker rm selenium