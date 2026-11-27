!!! note "This intervention is needed when upgrading from a version lower than [v1.31.0](https://github.com/codalab/codabench/releases/tag/v1.31.0)"

The default number of queues a user can create went from 5 to 10. New users get the new limit automatically, but existing users keep the old one. After the upgrade, update the limit of existing users to 10.

Open shell_plus:

```sh
docker compose exec django ./manage.py shell_plus
```

Update the queue limit of existing users:

```python
from profiles.models import User
User.objects.filter(rabbitmq_queue_limit__lt=10).update(rabbitmq_queue_limit=10)
```

This only raises the limits lower than 10, so the users to whom you gave a higher limit keep it.
