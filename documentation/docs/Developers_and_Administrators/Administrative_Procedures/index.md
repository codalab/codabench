# Administrative Procedures

## Maintenance Mode
You can turn on maintenance mode by creating a `maintenance.on` file in the `maintenance_mode` folder. This will change the front page of the website, showing a customizable page (the `maintenance.html` file in the same folder).

Simply remove the `maintenance_mode/maintenance.on` file to end maintenance mode.

---
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

## Migration

```bash
docker compose exec django ./manage.py makemigrations
docker compose exec django ./manage.py migrate
```

## Collect static files

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

