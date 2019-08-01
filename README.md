# Codalab Competitions v2

## Installation


```
$ cp .env_sample .env
$ docker-compose up -d

# and if you'd like to make a user for testing...
$ docker-compose exec django python manage.py createsuperuser
```

## Running tests

```
# Non "end to end tests"
$ docker-compose exec django py.test -m "not e2e"

# "End to end tests" (a shell script to launch a selenium docker container)
$ ./run_selenium_tests.sh
```