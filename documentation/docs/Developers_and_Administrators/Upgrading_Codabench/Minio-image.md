!!! note "After upgrading from Codabench <1.21.1, you will need to migrate MinIO, rebuild containers, run Django migrations and upgrade compute workers."


### 1. MinIO migration (depending on setup)
If you are running MinIO locally (defined by `.env` and `docker-compose.yml`), you may require to follow the following MinIO upgrade instructions, to duplicate and mirror your buckets and convert them to the new format:
https://docs.min.io/community/minio-object-store/operations/deployments/baremetal-migrate-fs-gateway.html

### 2. Rebuild all containers
```sh
docker compose build && docker compose up -d
```

### 3. Django migration

```sh
docker compose exec django ./manage.py migrate
```

### 4. Collect static files

```sh
docker compose exec django ./manage.py collectstatic --no-input
```

### 5. Upgrade compute workers

For every compute worker associated to the instance (default queue) or to a custom queue, you need to update the worker:

```sh
<ssh into worker>
docker compose down
docker compose up -d --pull always
```
