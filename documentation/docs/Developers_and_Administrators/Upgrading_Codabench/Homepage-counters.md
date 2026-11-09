!!! note "After upgrading from Codabench <1.15, you will need to follow these steps to compute the homepage counters. See [this](https://github.com/codalab/codabench/pull/1694) for more information"

Update the homepage counters (to avoid waiting 1 day):

```bash
docker compose exec django ./manage.py shell_plus
```

```python
from analytics.tasks import update_home_page_counters
eager_results = update_home_page_counters.apply_async()
```