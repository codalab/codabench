```bash
# Without "end to end" tests
$ docker compose exec django py.test -m "not e2e"

# Playwright tests (make sure to install uv first: https://docs.astral.sh/uv/getting-started/installation/) 
uv sync --frozen
uv run playwright install
docker compose exec -e DJANGO_SUPERUSER_PASSWORD=codabench django python manage.py createsuperuser --username codabench --email codabench@test.mail --no-input
uv run pytest test_auth.py test_account_creation.py test_competition.py test_submission.py
```

## CircleCI

To simulate the tests run by CircleCI locally, run the following command:

```sh
docker compose -f docker-compose.yml exec django py.test src/ -m "not e2e"
```

## Example competitions

The repo comes with a couple examples that are used during tests:

### v2 test data
 ```
 src/tests/functional/test_files/submission.zip
 src/tests/functional/test_files/competition.zip
 ```
### v1.5 legacy test data
 ```
 src/tests/functional/test_files/submission15.zip
 src/tests/functional/test_files/competition15.zip
 ```
 
### Other Codalab Competition examples
[https://github.com/codalab/competition-examples/tree/master/v2/](https://github.com/codalab/competition-examples/tree/master/v2/)