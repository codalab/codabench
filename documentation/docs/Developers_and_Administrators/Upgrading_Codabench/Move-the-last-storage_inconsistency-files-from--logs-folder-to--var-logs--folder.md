!!! note "This intervention is needed when upgrading from a version equal or lower than [v1.11.0](https://github.com/codalab/codabench/releases/tag/v1.11.0)"

You will need to move the last storage_inconsistency files from /logs folder to /var/logs/ folder.

```bash
cd codabench
cp -r logs/* var/logs
```

You will also need to rebuild the celery image because of a version change that's needed.
```bash
docker compose down 
docker images # Take the ID of the celery image
docker rmi *celery_image_id*
docker compose up -d
```
More information [here](https://github.com/codalab/codabench/pull/1575)