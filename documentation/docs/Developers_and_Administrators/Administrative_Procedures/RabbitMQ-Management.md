# RabbitMQ Management

The RabbitMQ management tool allows you to see the status of various queues, virtual hosts, and jobs. By default, you can access it at: `http://<your_codabench_instance>:15672/`. The username/password is your RabbitMQ `.env` settings for username and password. The port defaults to 15672 and can be changed with `RABBITMQ_MANAGEMENT_PORT` in `.env`. For more information, see:
https://www.rabbitmq.com/management.html

## Change RabbitMQ username or password

RabbitMQ only reads `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS` from `.env` the first time it starts with an empty data folder (`var/rabbit`). After that, the users are loaded from `var/rabbit`, so changing `.env` and restarting is not enough: RabbitMQ keeps the old credentials while the other services try the new ones, and the logs show `login refused ... invalid credentials`. `docker compose down --volumes` does not help either, because `var/rabbit` is a folder on the host, not a Docker volume.

Choose one of the two options below.

### Option 1: New instance (RabbitMQ data can be deleted)

!!! warning
    This deletes all RabbitMQ data: pending tasks, and the users and virtual hosts of custom queues. Custom queues created before will stop working. Only use this on a new instance or when you don't need this data.

1. Update `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS` in `.env`
2. Stop the services, delete the RabbitMQ data and start again:

```bash
docker compose down
sudo rm -rf var/rabbit
docker compose up -d
```

RabbitMQ starts empty and creates the user from `.env`.

### Option 2: Instance in use (keep RabbitMQ data)

Use this when the platform is already in use. The RabbitMQ data is kept, and the new credentials are applied directly in RabbitMQ.

1. Update `RABBITMQ_DEFAULT_USER` and/or `RABBITMQ_DEFAULT_PASS` in `.env`
2. Recreate the containers so they use the new values:

```bash
docker compose up -d
```

At this point the workers cannot log in to RabbitMQ yet. This is expected and fixed by the next step.

3. Apply the new credentials in RabbitMQ. The commands read the new values from the `rabbit` container, so the password does not need to be typed.

**If only the password changed:**

```bash
docker compose exec rabbit sh -c 'rabbitmqctl change_password "$RABBITMQ_DEFAULT_USER" "$RABBITMQ_DEFAULT_PASS"'
```

**If the username changed:** create the new user and give it the same permissions as the old user. The old user has access to the main virtual host (`/`) and to the virtual host of every custom queue, so all of them are copied. Replace `<old-username>` with the previous `RABBITMQ_DEFAULT_USER`:

```bash
docker compose exec -e OLD_USER=<old-username> rabbit sh -c '
set -e
NEW_USER="$RABBITMQ_DEFAULT_USER"
rabbitmqctl add_user "$NEW_USER" "$RABBITMQ_DEFAULT_PASS"
rabbitmqctl set_user_tags "$NEW_USER" administrator
rabbitmqctl -q list_user_permissions "$OLD_USER" | tail -n +2 |
while IFS="$(printf "\t")" read -r vhost perm_configure perm_write perm_read; do
  rabbitmqctl set_permissions -p "$vhost" "$NEW_USER" "$perm_configure" "$perm_write" "$perm_read"
done
'
```

4. Restart the services that connect to RabbitMQ:

```bash
docker compose restart django site_worker compute_worker flower
```

5. Check that the services can log in. The `rabbit` logs should show `user '<new-username>' authenticated` and no `login refused` errors:

```bash
docker compose logs --since 2m rabbit | grep -E "authenticated|refused"
```

6. Update `BROKER_URL` on any compute worker running on another machine that connects to the default queue with these credentials (see [Link compute workers to default queue](../How-to-deploy-Codabench-on-your-server.md#link-compute-workers-to-default-queue)). Workers on custom queues use their own RabbitMQ users and don't need any change.

!!! note "Delete the old user"
    If the username changed, the old user is kept in RabbitMQ but is no longer used. If you want to delete it, run this command once everything works (replace `<old-username>` with the previous `RABBITMQ_DEFAULT_USER`):

    ```bash
    docker compose exec rabbit rabbitmqctl delete_user <old-username>
    ```
