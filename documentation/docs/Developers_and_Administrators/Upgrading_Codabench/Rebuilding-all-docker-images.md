!!! note  "This intervention is needed when upgrading from a version equal or lower than [v1.9.2](https://github.com/codalab/codabench/releases/tag/v1.9.2)"


Since we are now using Poetry, we need to rebuild all our docker images to include it.

You can achieve this by running the following commands : 

!!! warning 
    If your machine has other images or containers that you want to keep, do not run `docker system prune -af`. Instead, manually delete all the images related to codabench

```bash
docker compose build && docker compose up -d
docker system prune -a
```

More information (and alternative commands) [here](https://github.com/codalab/codabench/pull/1416)