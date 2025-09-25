
Codabench has a custom command that uploads a database backup, and copies it to the storage you are using under `/backups`. We'll see how to execute and automate that command, and how to restore from one of these backups in the event of a failure.

## Creating Backups
### Create
```bash
DB_NAME=
DB_USERNAME=
DB_PASSWORD=
DUMP_NAME=
docker exec codabench-db-1 bash -c "PGPASSWORD=$DB_PASSWORD pg_dump -Fc -U $DB_USERNAME $DB_NAME > /app/backups/$DUMP_NAME.dump"
```

### Upload
There's a custom command on codabench that we use to upload database backups to storage. It should be accessible from inside the Django container (`docker compose exec django bash`) with `python manage.py upload_backup <backup_path>`. It takes an argument `backup_path` which is the path relative to your backup folder, `codabench/backups` and storage bucket, `/backups`. For instance if I pass it as `2022/$DUMP_NAME.dump`, the backup should happen in `codabench/backups/2022/$DUMP_NAME.dump` and will be uploaded to `/backups/2022/$DUMP_NAME.dump` in your storage bucket.

## Scheduling Automatic Backups
To schedule automatic backups, we're going to schedule a daily cronjob. To start, open the cron editor in a shell with `crontab -e`.

Add a new entry like so, with the correct path to `pg_dump.py`:

```bash
@daily /home/ubuntu/codabench/bin/pg_dump.py
```

You should confirm this backup process works by setting some known cronjob time a few minutes in the future and see the dump in storage.

Once done, save and quit the crontab editor, and verify your changes held by listing out cronjobs with `crontab -l`. You should see your new crontab entry.

## Restoring From Backup

Re-install Codabench according to the documentation here: [Codabench Installation](Codabench-Installation.md).

Once Codabench is re-installed and working, we're ready to restore our database backup. Upload the database backup to the webserver. It should go under the `codabench` install folder in the `/backups` directory. For example your path might look like:
`/home/users/ubuntu/codabench/backups`

Once the backup is located in the `/backups` folder, you'll want to get into the postgres container (`docker compose exec db bash`). Make sure you know your `DB_NAME`, `DB_USERNAME`, and `DB_PASSWORD` variables from your .env.

You can restore two ways. The first would be manually dropping the db, re-creating it, then using pg_restore to restore the data:
```bash title="Inside the database container"
dropdb $DB_NAME -U $DB_USERNAME
createdb $DB_NAME -U $DB_USERNAME
pg_restore -U $DB_USERNAME -d $DB_NAME -1 /app/backups/<filename>.dump
```

Or, you can let `pg_restore` do that for you with a couple of flags/arguments:
```bash title="Inside the database container"
pg_restore --verbose --clean --no-acl --no-owner -h $DB_HOST -U $DB_USERNAME -d $DB_NAME /app/backups/<filename>.dump
```

The arguments `--no-acl` & `--no-owner` may be useful if you're restoring as a non-root user. The owner argument is used for: ```Do  not  output  commands to set ownership of objects to match the original database.```

The ACL argument is for: ```Prevent dumping of access privileges (grant/revoke commands).```

After running `pg_restore` successfully without errors, you should find everything has been restored.