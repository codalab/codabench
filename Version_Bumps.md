# Upgrading Codabench Packages

## Make Virtual Environment To Iterate

### Use pyenv for easy venv creation

[Install pyenv](https://github.com/pyenv/pyenv-installer)
```bash
curl https://pyenv.run | bash
```

We are using `python3.9.19` for now so we need to start there. 
> See all available versions with `pyenv install --list'.

```bash
pyenv install 3.9.19
pyenv virtualenv 3.9.19 codabench_django
pyenv activate codabench_django
# pyenv uninstall codabench_django
```

### Poetry for version control:

```bash
curl -sSL https://install.python-poetry.org | python3 -
PATH $PATH:/root/.local/bin
```

```bash
poetry config virtualenvs.create false
poetry config virtualenvs.in-project false
poetry install # installs from lock file
```

#### View installed packages
```bash
poetry show --tree
poetry show requests # example to inspect a library
```


## Github Bumps
> Part of me thinks this file should have git and other bumps checked that were used in the last wave of updates. Then when a new wave of updates happens, we can add them here and delete the old ones. Thoughts?

### Bump Pillow
[Bump pillow from 8.0.1 to 10.3.0](https://github.com/codalab/codabench/pull/1493)
```bash
poetry add pillow@10.3.0
poetry install
poetry show pillow
```
### Bump Jinja2
[Bump jinja2 from 3.1.3 to 3.1.4](https://github.com/codalab/codabench/pull/1494)
```bash
poetry add jinja2@3.1.4
poetry install
poetry show jinja2
```

### Bump gunicorn from 20.0.4 to 22.0.0
[Bump gunicorn from 20.0.4 to 22.0.0](https://github.com/codalab/codabench/pull/1495)
```bash
poetry add gunicorn@22.0.0
poetry install
poetry show gunicorn
```

### Bump requests from 2.20.0 to 2.32.2
[Bump requests from 2.20.0 to 2.32.2](https://github.com/codalab/codabench/pull/1489)
```bash
poetry add requests@2.32.2
poetry install
poetry show requests
```

### Bump django from 2.2.17 to 2.2.18 and to 3.2.25 eventually
[Bump django from 2.2.17 to 3.2.25](https://github.com/codalab/codabench/pull/1492)
> We are going to go by smaller steps.

We are going to go slower.
```bash
poetry add django@2.2.18
poetry install
poetry show django
```

<!-- 
These might need to happen eventually but for now we will go slower with Django. We can delete from this file. 

Django 3.2.25 required a bump of djangorestframework from 3.9.1 to 3.12
```bash
poetry add djangorestframework@3.12
poetry install
poetry show djangorestframework
```

Django 3.2.25 required a bump of django-oauth-toolkit from 1.0.0 to 1.3
```bash
poetry add django-oauth-toolkit@1.3
poetry install
poetry show django-oauth-toolkit
```

Django 3.2.25 required a bump of django-storages from 1.7.2 to 1.11
```bash
poetry add django-storages@1.11 --extras "azure" --extras "google"
poetry install
poetry show django-storages
```

Django 3.2.25 required a bump of drf_writable_nested from 0.5.4 to 0.6.2
```bash
poetry add drf_writable_nested@0.6.2
poetry install
poetry show drf_writable_nested
```

Django 3.2.25 required a bump of drf_extra_fields from 0.9 to 3.1.0
```bash
poetry add drf_extra_fields@3.1.0
poetry install --no-cache
poetry show drf_extra_fields
```

Django 3.2.25 required a bump of drf_extra_fields from 0.9 to 3.1.0


```bash
# Poetry is somehow installing a <3.1.0 version of drf_extra_fields
# or there is a bug. When I do this in a pyenv virtualenv, it works.
# So we need to install that separately again and jostle the code
# as it is using not the right code for this. I think in the future,
# we can resolve this, but this is the only way I got it to work.
# RUN poetry add drf-extra-fields==3.1.0


poetry add drf_extra_fields@3.1.0
poetry install --no-cache
poetry show drf_extra_fields
``` -->



### Poetry Lock
```bash
poetry lock --no-cache
```

### Req Tree
This creates a file with the commit hash of the current branch that has the dependency tree.
```bash
req_tree_file="req_tree_$(git rev-parse HEAD).md"
echo '```bash' >> "$req_tree_file"
poetry show --tree >> "$req_tree_file"
echo '```' >> "$req_tree_file"
rm $req_tree_file
```


### Rebuilds, Flakes and Tests:
```bash
# Rebuild Django Image
docker build -f Dockerfile -t codabench-django:latest ./
# docker build --no-cache -f Dockerfile -t codabench-django:latest ./
# Python code formatting test
docker compose exec django flake8 src/ 
# Start Containers Including Selenium
docker compose -f docker-compose.yml -f docker-compose.selenium.yml up -d
# Non Selenium Tests
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/ -m "not e2e"
# Selenium Tests
docker compose -f docker-compose.yml -f docker-compose.selenium.yml exec django py.test src/tests/functional/ -m e2e
# Stop Containers
docker compose -f docker-compose.yml -f docker-compose.selenium.yml down
```