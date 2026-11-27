!!! note "This intervention is needed when upgrading from a version lower than [v1.37.0](https://github.com/codalab/codabench/releases/tag/v1.37.0)"

After the upgrade, initialize the default tag categories and tags in the database:

```sh
docker compose exec django ./manage.py init_tags
```

More information in [Tag Management](../Administrator-procedures.md#tag-management).
