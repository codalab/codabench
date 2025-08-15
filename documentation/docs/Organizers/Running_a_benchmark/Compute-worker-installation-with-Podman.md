Here is the specification for compute worker installation by using Podman. 
## Requirements for the host machine

We need to install Podman on the VM. We use Debian based OS, like Ubuntu. Ubuntu is recommended, because it has better Nvidia driver support. 

`sudo apt install podman `

After installing Podman, you will need to launch the service associated to it with `systemctl --user enable --now podman`

Then, configure where Podman will download the images: Podman will use Dockerhub by adding this line into `/etc/containers/registries.conf `:

`unqualified-search-registries = ["docker.io"] `

Create the `.env` file in order to add the compute worker into a queue (here, the default queue is used. If you use a particular queue, then, fill in your BROKER_URL generated when creating this particular queue) : 

```ini title=".env"
BROKER_URL=pyamqp://<login>:<password>@codabench-test.lri.fr:5672 
HOST_DIRECTORY=/codabench
# If SSL isn't enabled, then comment or remove the following line
BROKER_USE_SSL=True
CONTAINER_ENGINE_EXECUTABLE=podman
```

You will also need to create the `codabench` folder defined in the `.env` file, as well as change its permissions to the user that is running the compute worker.

```bash title="In your terminal"
sudo mkdir /codabench
sudo mkdir /codabench/data
sudo chown -R $(id -u):$(id -g) /codabench
```

## For GPU compute worker VM

You need to install nvidia packages supporting Podman and nvidia drivers:

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
    && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-container.list
sudo apt update
sudo apt install nvidia-container-runtime nvidia-containe-toolkit nvidia-driver-<version>
```

Edit the nvidia runtime config

```bash
sudo sed -i 's/^#no-cgroups = false/no-cgroups = true/;' /etc/nvidia-container-runtime/config.toml
```

Check if nvidia driver is working, by executing:

```bash
nvidia-smi

+-----------------------------------------------------------------------------+
| NVIDIA-SMI 520.61.05    Driver Version: 520.61.05    CUDA Version: 11.8     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  On   | 00000000:01:00.0 Off |                  N/A |
| 27%   26C    P8    20W / 250W |      1MiB / 11264MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+

```

The result should show gpu card information.

We need to configure the OCI hook (entry point to inject code) script for nvidia. Create this file `/usr/share/containers/oci/hooks.d/oci-nvidia-hook.json` if not exists:

```json title="oci-nvidia-hook.json"
{
    "version": "1.0.0",
    "hook": {
        "path": "/usr/bin/nvidia-container-toolkit",
        "args": ["nvidia-container-toolkit", "prestart"],
        "env": [
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ]
    },
    "when": {
        "always": true,
        "commands": [".*"]
    },
    "stages": ["prestart"]
}
```

Validating if all are working by running a test container:

```bash
podman run --rm -it \
 --security-opt="label=disable" \
 --hooks-dir=/usr/share/containers/oci/hooks.d/ \
 nvidia/cuda:11.6.2-base-ubuntu20.04 nvidia-smi
```
The result should show as same as the command `nvidia-smi` above.


## Compute worker installation 

### For CPU container 

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
 --cap-drop all \
 --volume /codabench:/codabench:U,z \
 codalab/codabench_worker_podman:latest 
```

### For GPU container

Run the GPU compute worker container

```bash
podman run -d \
    --env-file .env \
    --device nvidia.com/gpu=all \
    --name gpu_compute_worker \
    --device /dev/fuse \
    --security-opt="label=disable" \
    --restart unless-stopped \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    --hostname ${HOSTNAME} \
    --userns host \
    --volume /home/codalab/worker/codabench:/codabench:z,U \
    --cap-drop=all \
    --volume /run/user/$(id -u)/podman/podman.sock:/run/user/1000/podman/podman.sock:U \
    codalab/codabench_worker_podman_gpu:latest
```