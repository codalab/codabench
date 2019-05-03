# Codalab Competitions v2

## Installation


```
$ cp .env_sample .env
$ docker-compose up -d

# and if you'd like to make a user for testing...
$ docker exec -it django python manage.py createsuperuser
```

## Running tests

```
# Non "end to end tests"
$ docker exec -it django py.test -m "not e2e"

# "End to end tests" (uses actual browser window to click around site and confirm actions work)
$ py.test -m e2e
```