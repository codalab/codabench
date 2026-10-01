!!! note "After upgrading from Codabench <1.20, you will need to rebuild containers, run Django migrations and upgrade compute workers."

1. Rebuild containers

```sh
docker compose build
docker compose up -d
```

2. Run migrations and collect static

```sh
docker compose exec django ./manage.py makemigrations
docker compose exec django ./manage.py migrate
docker compose exec django ./manage.py collectstatic --noinput
```

3. Upgrade compute workers

For every compute worker associated to the instance (default queue) or to a custom queue, you need to update the worker:

```sh
<ssh into worker>
docker compose down
docker compose up -d --pull always
```
