!!! note "After upgrading from Codabench <1.14, you will need to follow these steps to compute the submissions and participants counts on the competition pages. See [this](https://github.com/codalab/codabench/pull/1669) for more information"


## 1. Re-build containers

```bash
docker compose build && docker compose up -d
```

## 2. Migration

```sh
docker compose exec django ./manage.py migrate
```

## 3. Update counts for all competitions

Bash into django console
```
docker compose exec django ./manage.py shell_plus
```

Import and call the function
```python
from competitions.submission_participant_counts import compute_submissions_participants_counts
compute_submissions_participants_counts()
```

## 4. Feature some competitions in home page

There are two ways to do it:
1. Use Django admin -> click the competition -> scroll down to is featured filed -> Check/Uncheck it
2. Use competition ID in the django bash to feature / unfeature a competition
```bash
docker compose exec django ./manage.py shell_plus
```
```python
comp = Competition.objects.get(id=<ID>)  # replace <ID> with competition id
comp.is_featured = True  # set to False if you want to unfeature a competition
comp.save()
```
