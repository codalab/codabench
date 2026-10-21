## Upgrade Codabench

Run these commands for every upgrade. They put the site in maintenance mode, pull the new version, rebuild and restart the containers, apply the Django migrations and collect the static files:

```sh
cd codabench
touch maintenance_mode/maintenance.on
git pull
docker compose build && docker compose up -d
docker compose exec django ./manage.py migrate
docker compose exec django ./manage.py collectstatic --noinput
rm maintenance_mode/maintenance.on
```

Then check the manual interventions below for every version between yours and the new one, and apply them in order.

## Upgrade compute workers

Some versions also change the compute worker. In that case, upgrade every compute worker connected to your instance, for the default queue and for custom queues.

Before upgrading a worker, check that no submission is running on it:

```sh
docker ps
```

**Docker** (worker started with `docker compose`, as described in [Compute Worker Management & Setup](../../Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md)). In the folder containing the worker's `docker-compose.yml`:

```sh
docker compose down
docker compose pull
docker compose up -d
```

If your `docker-compose.yml` pins an image tag instead of `latest`, change it to the new version first.

**Podman** (worker started with `run_podman.sh`, as described in [Compute Worker Management with Podman](../../Organizers/Running_a_benchmark/Compute-worker-installation-with-Podman.md)):

```sh
podman stop compute_worker && podman rm compute_worker
podman pull codalab/codabench-compute-worker:latest
./run_podman.sh
```

!!! note
    Old workers started with `docker run`, or using the old `codalab/competitions-v2-compute-worker` image, should be replaced by a worker set up as described in [Compute Worker Management & Setup](../../Organizers/Running_a_benchmark/Compute-Worker-Management---Setup.md).

## Manual interventions

Manual interventions needed depending on which version you are upgrading from:

- [Upgrade RabbitMQ](Upgrade-RabbitMQ.md) (version < 1.0.0)
- [Upgrade compute workers](#upgrade-compute-workers) (version < 1.3.1)
- [Create new logos for each competition](Create-new-logos-for-each-competition.md) (version < 1.4.1)
- [Add line into `.env` for default queue worker duration](Add-line-into-.env-for-default-queue-worker-duration.md) (version < 1.7.0)
- [Uncomment a line in your `.env` file](Uncomment-a-line-in-your-.env-file.md) (version < 1.8.0)
- [Move the last storage_inconsistency files from logs folder to var logs folder](Move-the-last-storage_inconsistency-files-from--logs-folder-to--var-logs--folder.md) (version < 1.12.0)
- [Submissions and Participants Counts](Submissions-and-Participants-Counts.md) (version < 1.14.0)
- [Homepage counters](Homepage-counters.md) (version < 1.15.0)
- [Database size Fix](Database-size-fixes.md) (version < 1.18.0)
- [Upgrade compute workers](#upgrade-compute-workers) for Django 3.0 (version < 1.20.0)
- [Minio image](Minio-image.md) and [upgrade compute workers](#upgrade-compute-workers) (version < 1.21.1)
- [Docker-py](Docker-py.md) and [upgrade compute workers](#upgrade-compute-workers) (version < 1.22.0)
- [Django 4.2](Django-4.md) (version < 1.23.0)
- [Postgres 18](Postgres-18.md) (version < 1.24.0)
