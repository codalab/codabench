!!! note "This intervention is needed when upgrading from a version lower than [v1.38.0](https://github.com/codalab/codabench/releases/tag/v1.38.0)"

## Compute Workers

Compute workers need to be upgraded (#2669): see [Upgrade compute workers](index.md#upgrade-compute-workers).

!!! warning
    Upgrade the main instance as well. Running an upgraded worker with an instance that is not up to date can cause bugs.

## Manually fetch the papers citing Codabench

To populate manually the Hall of Papers (#2782). Anyway, a daily task does it.

```bash
docker compose exec django python manage.py shell -c "from papers.tasks import sync_citing_papers; sync_citing_papers()"
```

## Convert existing email addresses to lowercase

A 500 error happened at signup when a user entered an email already registered, but with different capital letters (for example `John@example.com` instead of `john@example.com`). Signup now converts emails to lowercase (#2611). After the upgrade, convert the existing emails to lowercase as well.

Open shell_plus:

```sh
docker compose exec django ./manage.py shell_plus
```

Count the users with capital letters in their email:

```python
User.objects.exclude(email__isnull=True).filter(email__regex=r'[A-Z]').count()
```

Convert the emails to lowercase:

```python
from django.db import IntegrityError, transaction
from profiles.models import User

failed_users = []

for user in User.objects.exclude(email__isnull=True):
    if user.email != user.email.lower():
        original_email = user.email
        user.email = user.email.lower()
        try:
            # Each save is undone on its own if it fails, so the loop keeps going
            with transaction.atomic():
                user.save()
        except IntegrityError:
            # Another account already has this email in lowercase, e.g. "Foo@x.com" when "foo@x.com" exists
            failed_users.append((user.id, user.username, original_email))

for user_id, username, email in failed_users:
    print(f"Could not convert id={user_id} username={username} email={email}")
```

Count the users with capital letters in their email again to verify:

```python
User.objects.exclude(email__isnull=True).filter(email__regex=r'[A-Z]').count()
```

The remaining users are the ones printed by the script: their email is already used, in lowercase, by another account. They have to be handled manually.
