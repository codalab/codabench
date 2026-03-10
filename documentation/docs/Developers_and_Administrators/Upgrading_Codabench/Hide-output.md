!!! note "After upgrading from Codabench <1.19, you will need to perform a Django migration ([#1838](https://github.com/codalab/codabench/pull/1838), [#1851](https://github.com/codalab/codabench/pull/1851))"

```bash
docker compose exec django ./manage.py migrate
```