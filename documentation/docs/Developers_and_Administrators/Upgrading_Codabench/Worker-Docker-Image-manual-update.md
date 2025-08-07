!!! note "This intervention is needed when upgrading from a version equal or lower than [v1.3.1](https://github.com/codalab/codabench/releases/tag/v1.3.1)"

To update your worker docker image, you can launch the following code in the terminal on the machine where your worker is located.

```bash
docker stop compute_worker
docker rm compute_worker
docker pull codalab/competitions-v2-compute-worker:latest
docker run \
    -v /codabench:/codabench \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -d \
    --env-file .env \
    --name compute_worker \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    codalab/competitions-v2-compute-worker:latest 
```