# Deploy
```bash
docker compose up -d
docker compose up -d --build
docker compose down

docker compose logs -f
docker compose logs -f django
docker compose logs -f minio
docker compose logs -f db
docker compose logs -f compute_worker
docker compose logs -f site_worker
docker compose logs -f rabbit

docker compose restart django
docker compose restart site_worker
```

# Initial setup
```bash
docker compose exec django ./manage.py collectstatic --no-input
docker compose exec django ./manage.py makemigrations
# docker compose exec django ./manage.py makemigrations --merge
docker compose exec django ./manage.py migrate
```

# Full restart and purge
```bash
ls var
# Purge data
sudo rm -r var/postgres/*
sudo rm -r var/minio/*
sudo rm -r var/rabbit/* # not needed but here is the command if rabbit is acting up

```
# Restart services and run
* collectstatic
* migrate

# Debugging
## Debugger
pdb works but for workers you need more advanced settings.

Add the following to docker-compose.yml for either worker:
```bash
  #-----------------------------------------------
  #   Celery Service
  #-----------------------------------------------
  site_worker:
  ...
    stdin_open: true 
    tty: true
    ports:
      - 6900-7000:6900-7000
    environment:
      - CELERY_RDB_HOST=0.0.0.0
      - PYTHONUNBUFFERED=1
  ...
```
* Then you can drop this almost anywhere. Thing is obviously it will work in compute_worker and most tasks assigned to site worker.
* Where it gets interesting is model instances or util funcs\methods used by the workers no matter how deep can be debugged with this.
* Ex: A Competion model instance you want to save with .save(). You can drop the below in that method if you want.

```python
from celery.contrib import rdb
rdb.set_trace()
# You will get instructions to `telnet` inside logs from django, site\compute worker or etc.
```
## Can't connect to workers but site is working and rabbit is working
`.env` sometimes needs `AWS_S3_ENDPOINT_URL` set to your current internal ip:
```bash
# $(ip add show | grep -oP 'inet \K[^/]+' | awk 'NR==2')
AWS_S3_ENDPOINT_URL=http://192.168.7.223:9000
```


# Tests
```bash
docker compose exec django flake8 src/ # python code formatting test
docker compose exec django py.test -m "not e2e"
# Circleci simulation
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/ -m "not e2e"
docker compose -f docker-compose.yml -f docker-compose.selenium.yml down
docker compose -f docker-compose.yml -f docker-compose.selenium.yml up -d
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/ -m e2e
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_login.py
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_competitions.py
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_competitions.py::TestCompetitions::test_upload_v15_competition
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_competitions.py::TestCompetitions::test_upload_v18_competition
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_competitions.py::TestCompetitions::test_upload_v2_competition
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_competitions.py::TestCompetitions::test_manual_competition_creation
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_submissions.py
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_submissions.py::TestSubmissions::test_v15_iris_result_submission_end_to_end
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_submissions.py::TestSubmissions::test_v15_iris_code_submission_end_to_end
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_submissions.py::TestSubmissions::test_v18_submission_end_to_end
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/test_submissions.py::TestSubmissions::test_v2_submission_end_to_end

# Specific test example
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/apps/api/tests/test_competitions.py -k "CompetitionTests"
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/apps/api/tests/test_tasks.py
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/apps/api/tests/test_competitions.py::CompetitionTests::test_adding_organizer_creates_accepted_participant
```

# Create Storage Analytics
```bash
docker compose exec django bash
python manage.py shell_plus --plain
from analytics.tasks import create_storage_analytics_snapshot
create_storage_analytics_snapshot()
```

# Make accounts
```bash
docker compose exec django bash
python manage.py shell_plus
```

```python
u = User.objects.get(username='bbearce') # can also use email
u = User.objects.get(username='guest') # can also use email
u.delete()
u = User(username='bbearce'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest1'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest2'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest3'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest4'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest5'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest6'); u.set_password('testtest'); u.is_active = True; u.save();
u = User(username='guest7'); u.set_password('testtest'); u.is_active = True; u.save();
u.set_password('testtest')
u.is_active = True
u.is_staff = True
u.is_superuser = True
u.save()
```

# DB
## Shell into DB
```bash
docker compose exec -it db bash
psql -U postgres postgres
```

## Then SQL:
```sql
\dt

select
id, username, is_active, is_superuser, is_staff, email
from profiles_user;
where username = 'bbearce';

update profiles_user
set is_active = 'true'
where username = 'guest';

select *
select
id, name, competition_id,
public_data_id, starting_kit_id 
from competitions_phase where competition_id = 15;
-- from competitions_phase limit 1;
```

# Navigating a competition 
```python
p = competition.phases.order_by('index').first()
competition.phases.order_by('index').first().tasks
competition.phases.order_by('index').first().tasks.all()[0]
competition.phases.order_by('index').first().tasks.all()[0].solutions.all()[0]
competition.phases.order_by('index').first().tasks.all()[0].get_chahub_data(include_solutions=True)['solutions']
# ---------- #
input_data = instance.task.input_data
ingestion_program = instance.task.ingestion_program
scoring_program = instance.task.scoring_program
reference_data = instance.task.reference_data
input_data.id
qs = instance.task.starting_kit # part of phases not tasks
qs = instance.task.solutions.all()
```