# Administrative Procedures

## Maintenance mode
You can turn on maintenance mode by creating a `maintenance.on` file in the `maintenance_mode` folder. This will change the front page of the website, showing a customizable page (the `maintenance.html` file in the same folder).

Simply remove the `maintenance_mode/maintenance.on` file to end maintenance mode.

```bash
touch maintenance_mode/maintenance.on  ## entering maintenance mode
rm maintenance_mode/maintenance.on  ## exiting maintenance mode
```

## Restart one service at a time

During testing, if you want to update or restart some services (e.g : Django), you should follow the following steps:

```bash
docker compose stop django
docker compose rm django ## remove old django container
docker compose create django ## create new django container with the changes from your development
docker compose start django
```

This procedure helps you update changes of your development on Django without having to restart every Codabench container.

## Give superuser privileges to a user

With superuser privileges, the user can edit any benchmark and can access the Django admin interface.

```python
docker compose exec django ./manage.py shell_plus
u = User.objects.get(username='<USERNAME>') ## can also use email
u.is_staff = True
u.is_superuser = True
u.save()
```

## Django migration

Migrations are how Django keeps the database structure (tables, columns...) in sync with the models defined in the code. When a model changes (e.g. a new field is added), the database must be updated accordingly.

```bash
docker compose exec django ./manage.py makemigrations
```

- `makemigrations` looks at the changes made to the models and **writes** migration files (Python scripts in each app's `migrations/` folder) describing these changes. It does not touch the database.

    !!! note
        There is usually no need to run `makemigrations` on a production server: migration files come from the repository, and generating new ones locally may conflict with those shipped in future updates.

    It is mainly used by developers, and the generated files should be committed with the code.

```bash
docker compose exec django ./manage.py migrate
```

- `migrate` **applies** the pending migration files to the database, actually modifying its structure. This is what needs to be run on a server after pulling new code.

## Collect static files

This copies all static files (CSS, JavaScript, images...) from the apps into a single folder served by the web server. Run it after any change to the front-end files.

```bash
docker compose exec django ./manage.py collectstatic --noinput
```

## Delete POSTGRESDB and MINIO :
!!! warning
    This will delete all your data !

```bash
## Begin in codabench root directory
cd codabench
```

#### Purge data

```bash
sudo rm -r var/postgres/*
sudo rm -r var/minio/*
```

#### See data we are going to purge
```bash
ls var
```

#### Restart services and recreate database tables

```bash
docker compose down
docker compose up -d
docker compose exec django ./manage.py migrate
```

## Feature competitions in home page

There are two ways of setting a competition as featured:
1. Use [Django admin](Django-Admin.md) -> click the competition -> scroll down to is featured field -> Check/Uncheck it
2. Use competition ID in the django bash to feature or unfeature a competition
```python
docker compose exec django ./manage.py shell_plus
comp = Competition.objects.get(id=<ID>)  ## replace <ID> with competition id
comp.is_featured = True  ## set to False if you want to unfeature a competition
comp.save()
```

## Shell Based Admin Features
If you're running your own Codabench instance, there are different ways to interact with the application. Inside the `django` container (`#!bash docker compose exec django bash`) you can use `#!bash python manage.py help` to display all available commands and a brief description. By far the most useful are `createsuperuser` and `shell/shell_plus`.

## Additional Procedures

- [Django Admin Interface](Django-Admin.md) : Announcements, news, deleting and banning users
- [RabbitMQ Management](RabbitMQ-Management.md) : Queues, virtual hosts, and changing RabbitMQ credentials
- [Flower Management](Flower-Management.md) : Monitoring and administrating Celery clusters
- [Storage Analytics & Statistics](Analytics-and-Statistics.md) : Storage snapshots, homepage counters, and CSV statistics
- [User Quota Management](User-Quota-Management.md) : Increasing or updating user storage quotas
- [Tag Management](Tag-Management.md) : Creating tags, `init_tags`, and auto-tagging existing competitions

