Here is the specification for compute worker installation by using Podman. 
## Requirements for the host machine

We need to install Podman on the VM. We use Debian based OS, like Ubuntu. Ubuntu is recommended, because it has better Nvidia driver support. 

`sudo apt install podman `

After installing Podman, you will need to launch the service associated to it with 
```bash
systemctl --user enable --now podman
```

Then, configure where Podman will download the images: Podman will use Dockerhub by adding this line into `/etc/containers/registries.conf `:
```ini
unqualified-search-registries = ["docker.io"]
```

Create the `.env` file in order to add the compute worker into a queue (here, the default queue is used. If you use a particular queue, then, fill in your BROKER_URL generated when creating this particular queue) : 

```ini title=".env"
BROKER_URL=pyamqp://<login>:<password>@www.codabench.org:5672/
HOST_DIRECTORY=/codabench
# If SSL isn't enabled, then comment or remove the following line
BROKER_USE_SSL=True
CONTAINER_ENGINE_EXECUTABLE=podman
#USE_GPU=True
#GPU_DEVICE=nvidia.com/gpu=all
```


You will also need to create the `codabench` folder defined in the `.env` file, as well as change its permissions to the user that is running the compute worker.

```bash title="In your terminal"
sudo mkdir /codabench
sudo mkdir /codabench/data
sudo chown -R $(id -u):$(id -g) /codabench
```

You should also run the following command if you don't want the container to be shutdown when you log out of the user:
```bash
sudo loginctl enable-linger *username*
```
Make sure to use the username of the user running the podman container.


## For GPU compute worker VM
You will need to install the `nvidia-container-toolkit` package by following the instructions on this [link](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/index.html)


If you have multiple Nvidia GPUs, you can uncomment `#GPU_DEVICE=nvidia.com/gpu=all` and put the name of the GPU you want the compute worker to use. You can get the name by launching the following command :
```bash
nvidia-ctk cdi list
```

You will also need to uncomment this line in your `.env` file:
```ini title=".env"
USE_GPU=True
```


## Compute worker installation 
!!! note
    Starting from `codalab/competitions-v2-compute-worker:v1.22` the images are now unifed for Podman and Docker CPU/GPU and has been renamed to `codalab/codabench-compute-worker:latest`

Run the compute worker container : 

```bash
podman run -d \
 --volume /run/user/$(id -u)/podman/podman.sock:/run/user/1000/podman/podman.sock:U \
 --env-file .env \
 --name compute_worker \
 --security-opt="label=disable" \
 --userns host \
 --restart unless-stopped \
 --log-opt max-size=50m \
 --log-opt max-file=3 \
 --hostname ${HOSTNAME} \
 --cap-drop all \
 --volume /codabench:/codabench:U,z \
 codalab/codabench-compute-worker:latest
```

!!! warning
    To launch a Podman compatible GPU worker, you will need to have podman version 5.4.2 minimum
    
    Don't forget the `USE_GPU=true` in the `.env` if you want to use a GPU runner
