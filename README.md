# Codalab Competitions v2

## Installation


```
$ cp .env_sample .env
$ docker-compose up -d

# TODO: add how to generate dummy data

# and if you'd like to make a user for testing...
$ docker-compose exec django python manage.py createsuperuser
```

## Running tests

```
# Non "end to end tests"
$ docker-compose exec django py.test -m "not e2e"

# "End to end tests" (a shell script to launch a selenium docker container)
$ ./run_selenium_tests.sh

# If you are on Mac OSX it is easy to watch these tests, no need to install
# anything just do:
$ open vnc://0.0.0.0:5900

# And login with password "secret"
```

## Example competitions

_NOTE: Pisano Period competition may be out of date_

https://github.com/codalab/competition-examples/tree/master/v2/pisano_period

_TODO: Wheat Seed competition_


## Building compute worker

To build the normal image:

```bash
docker build -t codalab/competitions-v2-compute-worker:latest -f Dockerfile.compute_worker .
```

To build the GPU version:
```bash
docker build -t codalab/competitions-v2-compute-worker:nvidia -f Dockerfile.compute_worker_gpu .
```

Updating the image

```bash
docker push codalab/competitions-v2-compute-worker
```


# Worker setup

```bash
# install docker
$ curl https://get.docker.com | sudo sh
$ sudo usermod -aG docker $USER

# >>> reconnect <<<
```

## Start CPU worker

```bash
$ docker run \
    -v /tmp/codalab-v2:/tmp/codalab-v2 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -d \
    --env BROKER_URL=<queue broker url> \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    codalab/competitions-v2-compute-worker:latest 
```


## Start GPU worker

[nvidia installation instructions](https://github.com/NVIDIA/nvidia-docker#quickstart)

```bash
$ nvidia-docker run \
    -v /tmp/codalab-v2:/tmp/codalab-v2 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /var/lib/nvidia-docker/nvidia-docker.sock:/var/lib/nvidia-docker/nvidia-docker.sock \
    -d \
    --env BROKER_URL=<queue broker url> \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    codalab/competitions-v2-compute-worker:nvidia 
```
