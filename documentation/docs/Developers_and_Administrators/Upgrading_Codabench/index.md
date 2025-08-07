## Upgrade Codabench

```sh
cd codabench
git pull
docker compose build && docker compose up -d
docker compose exec django ./manage.py migrate
docker compose exec django ./manage.py collectstatic --noinput
```

## Manual interventions

You can find here various manual intervention needed depending on which version you are upgrading from:

- [Upgrade RabbitMQ](Upgrade-RabbitMQ.md) (version < 1.0.0)
- [Create new logos for each competition](Create-new-logos-for-each-competition.md) (version < 1.4.1)
- [Worker Docker Image manual update](Worker-Docker-Image-manual-update.md) (version < 1.3.1)
- [Add line into `.env` for default queue worker duration](Add-line-into-.env-for-default-queue-worker-duration.md) (version < 1.7.0)
- [Uncomment a line in your `.env` file](Uncomment-a-line-in-your-.env-file.md) (version < 1.8.0)
- [Rebuilding all docker images](Rebuilding-all-docker-images.md) (version < 1.9.2)
- [Move the last storage_inconsistency files from logs folder to var logs folder](Move-the-last-storage_inconsistency-files-from--logs-folder-to--var-logs--folder.md) (version < 1.12.0)
- [Submissions and Participants Counts](Submissions-and-Participants-Counts.md) (version < 1.14.0)
- [Homepage counters](Homepage-counters.md) (version < 1.15.0)
- [User removal](User-removal.md) (version < 1.17.0)
- [Database size Fix](Database-size-fixes.md) (version < 1.18.0)