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
```

### Poetry for version control:

```bash
curl -sSL https://install.python-poetry.org | python3 -
PATH $PATH:/root/.local/bin
```

```bash
poetry config virtualenvs.create false
poetry config virtualenvs.in-project false
poetry install
```

#### View installed packages
```bash
poetry show --tree
poetry show requests # example to inspect a library
```


## Github Bumps

### Bump Jinja2
[Bump jinja2 from 3.1.3 to 3.1.4](https://github.com/codalab/codabench/pull/1494)
```bash
poetry add jinja2@3.1.4
poetry install
poetry show jinja2
```

### Bump Pillow
[Bump pillow from 8.0.1 to 10.3.0](https://github.com/codalab/codabench/pull/1493)
```bash
poetry add pillow@10.3.0
poetry install
poetry show pillow
```

### Poetry Lock
```bash
poetry lock
```

### Req Tree
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
docker build --no-cache -f Dockerfile -t codabench-django:latest ./
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