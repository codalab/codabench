# Codabench 
## (formerly Codalab Competitions v2)

## Installation


```
$ cp .env_sample .env
$ docker-compose up -d
$ docker-compose exec django ./manage.py migrate
$ docker-compose exec django ./manage.py generate_data
$ docker-compose exec django ./manage.py collectstatic --noinput
```

You can now login as username "admin" with password "admin" at http://localhost:8000

If you ever need to reset the database, use the script `./reset_db.sh`

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

The repo comes with a couple examples that are used during tests:

### v2 test data
 ```
 src/tests/functional/test_files/submission.zip
 src/tests/functional/test_files/competition.zip
 ```
### v1.5 legacy test data
 ```
 src/tests/functional/test_files/submission15.zip
 src/tests/functional/test_files/competition15.zip
 ```
 
### Other Codalab Competition examples
https://github.com/codalab/competition-examples/tree/master/v2/


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

Make a file `.env` and put this in it:
```
# Queue URL
BROKER_URL=<desired broker url>

# Location to store submissions/cache -- absolute path!
HOST_DIRECTORY=/your/path/to/codabench/storage

# If SSL is enabled, then uncomment the following line
#BROKER_USE_SSL=True
```

NOTE `/your/path/to/codabench` -- this path needs to be volumed into `/codabench` on the worker, as you can 
see below.

```bash
$ docker run \
    -v /your/path/to/codabench/storage:/codabench \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -d \
    --env-file .env \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    codalab/competitions-v2-compute-worker:latest 
```


## Start GPU worker

[nvidia installation instructions](https://github.com/NVIDIA/nvidia-docker#quickstart)

```bash
$ nvidia-docker run \
    -v /your/path/to/codabench/storage:/codabench \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /var/lib/nvidia-docker/nvidia-docker.sock:/var/lib/nvidia-docker/nvidia-docker.sock \
    -d \
    --env-file .env \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    codalab/competitions-v2-compute-worker:nvidia 
```

# Worker management

Outside of docker containers install [Fabric](http://fabfile.org/) like so:

```bash
pip install fab-classic==1.17.0
```

Create a `server_config.yaml` in the root of this repository using:
```
cp server_config_sample.yaml server_config.yaml
```

Below is an example `server_config.yaml` that defines 2 roles `comp-gpu` and `comp-cpu`,
one with gpu style workers (`is_gpu` and the nvidia `docker_image`) and one with cpu style workers

```yaml
comp-gpu:
  hosts:
    - ubuntu@12.34.56.78
    - ubuntu@12.34.56.79
  broker_url: pyamqp://user:pass@host:port/vhost-gpu
  is_gpu: true
  docker_image: codalab/competitions-v2-compute-worker:nvidia

comp-cpu:
  hosts:
    - ubuntu@12.34.56.80
  broker_url: pyamqp://user:pass@host:port/vhost-cpu
  is_gpu: false
  docker_image: codalab/competitions-v2-compute-worker:latest
```

You can of course create your own `docker_image` and specify it here.

You can execute commands against a role:

```bash
❯ fab -R comp-gpu status
..
[ubuntu@12.34.56.78] out: CONTAINER ID        IMAGE                                           COMMAND                  CREATED             STATUS              PORTS               NAMES
[ubuntu@12.34.56.78] out: 1d318268bee1        codalab/competitions-v2-compute-worker:nvidia   "/bin/sh -c 'celery …"   2 hours ago         Up 2 hours                              hardcore_greider
..

❯ fab -R comp-gpu update
..
(updates workers)
```

See available commands with `fab -l`

