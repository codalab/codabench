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
