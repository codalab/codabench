```bash
# Without "end to end" tests
$ docker compose exec django py.test -m "not e2e"

# Playwright tests (make sure to install uv first: https://docs.astral.sh/uv/getting-started/installation/) 
uv sync --frozen
uv add playwright
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

### Codabench (v2) test data

Competition bundles:

```
codabench/tests/test_files/competitions/competition_v2_miniautoml.zip
codabench/tests/test_files/competitions/competition_v2_multi_task.zip
codabench/tests/test_files/competitions/competition_v2_multi_task_fact_sheet.zip
codabench/tests/test_files/competitions/competition_v2_wheat_code.zip
codabench/tests/test_files/competitions/competition_v2_wheat_results.zip
```

And the corresponding submissions:

```
codabench/tests/test_files/submissions/submission_v2_miniautoml.zip
codabench/tests/test_files/submissions/submission_v2_wheat_code.zip
codabench/tests/test_files/submissions/submission_v2_wheat_results.zip
codabench/tests/test_files/submissions/submission_v2_wheat_results_failure.zip
```

### CodaLab (v1.8) test data

Competition bundle:

```
codabench/tests/test_files/competitions/competition_v18_autowsl.zip
```

And the corresponding submission:

```
codabench/tests/test_files/submissions/submission_v18_autowsl.zip
```

### CodaLab (v1.5) test data

Competition bundles:

```
codabench/tests/test_files/competitions/competition_v15_iris.zip
codabench/tests/test_files/competitions/competition_v15_sncf.zip
```

And the corresponding submissions:

```
codabench/tests/test_files/submissions/submission_v15_iris_code.zip
codabench/tests/test_files/submissions/submission_v15_iris_results.zip
codabench/tests/test_files/submissions/submission_v15_sncf.zip
```
 
### Other competition examples

The following repository contains Codabench and CodaLab competition examples:

[https://github.com/codalab/competition-examples/](https://github.com/codalab/competition-examples/)
