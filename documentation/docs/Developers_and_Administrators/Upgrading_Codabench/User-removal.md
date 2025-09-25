!!! note "After upgrading from Codabench <1.17, you will need to perform a Django migration ([#1715](https://github.com/codalab/codabench/pull/1715), [#1741](https://github.com/codalab/codabench/pull/1741))"

```bash
docker compose exec django ./manage.py migrate
```