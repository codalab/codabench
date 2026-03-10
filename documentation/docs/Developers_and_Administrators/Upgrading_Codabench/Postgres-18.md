!!! note "After upgrading from Codabench <1.24.0, you will need to perform important manual interventions."

## Rabbit (#2061)
We also need to log into the RabbitMQ interface and enable the flags it wants us to enable after upgrading.

RabbitMQ port, username and password to access the interface are defined in the `.env` file.

<img width="1401" height="403" alt="Capture d’écran 2026-02-25 à 12 50 32" src="https://github.com/user-attachments/assets/6659efd8-e953-42dd-b885-629c41beb1c7" />

More information about feature flags [here](https://www.rabbitmq.com/docs/feature-flags)


## Database (Postgres 12 -> 18) (#2091)
### 1. Maintenance mode on to avoid update on the database during the upgrade:

```sh
touch maintenance_mode/maintenance.on
git pull
```

### 2. Create the new `postgres.conf` file from the sample:

```sh
cp my-postgres_sample.conf my-postgres.conf
```

### 3. Rebuild docker containers to take into account the new images:

```sh
docker compose build --no-cache
```

### 4. Dump the database, remove it and reload it on the new configuration:

```sh
# Dump database
docker compose exec db bash -lc 'PGPASSWORD="$DB_PASSWORD" pg_dump -Fc -U "$DB_USERNAME" -d "$DB_NAME" -f /app/backups/upgrade-1.24.dump'
```

```sh
# Check that dump file is not empty
docker compose exec db bash -lc 'ls -lh /app/backups/upgrade-1.24.dump && pg_restore -l /app/backups/upgrade-1.24.dump | head'
```

**/!\ Dangerous operation here: confirm that your dump worked before removing the database!**

```sh
# Remove database
sudo rm -rf var/postgres
```

```sh
# Launch the new containers (containing the updated databse image and Restore from backup)
docker compose up -d db
docker compose exec db bash -lc 'PGPASSWORD="$DB_PASSWORD" pg_restore --verbose --clean --no-acl --no-owner -h $DB_HOST -U "$DB_USERNAME" -d "$DB_NAME" /app/backups/upgrade-1.24.dump'
```

_See [this](https://www.postgresql.org/docs/18/upgrading.html) for more details._

### 5 Restart the rest of the services and disable maintenance mode:

```sh
docker compose up -d
rm maintenance_mode/maintenance.on
```

