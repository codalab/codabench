import os
import yaml

from fabric.api import env, run


# Load in server config, here's a quick example:
#   role_name:
#     hosts:
#       - ubuntu@12.34.56.78
#     broker_url: pyamqp://user:pass@host:port/vhost-gpu
#     is_gpu: true
#     docker_image: codalab/competitions-v2-compute-worker:nvidia
#
# You select the role to run with like s:
#   $ fab -R role_name <command>
host_types = yaml.load(open('server_config.yaml').read())
env.roledefs = host_types


def status():
    """Gets status of all docker containers on server"""
    run("docker ps")


def update():
    """Updates docker image on server and restarts the worker, based on server_config.yaml settings.

    See README (Worker management section) for example settings."""
    # Ensure that we're referencing one and only 1 role, so we don't accidentally update CPUs to GPUs
    if not env.effective_roles:
        print("ERROR: You must specify a role when running this task. I.e. fab -R some-gpu task_name`")
        return
    if len(env.effective_roles) > 1:
        print("ERROR: Only specify 1 role (because we need 1 broker_url) when running this task")
        return

    # Read settings from our server_config.yaml config
    role = env.effective_roles[0]
    broker_url = env.roledefs[role]["broker_url"]
    is_gpu = env.roledefs[role]["is_gpu"]
    docker_image = env.roledefs[role]["docker_image"]

    if is_gpu:
        docker_process = "nvidia-docker"
        nvidia_sock = "-v /var/lib/nvidia-docker/nvidia-docker.sock:/var/lib/nvidia-docker/nvidia-docker.sock"
    else:
        docker_process = "docker"
        nvidia_sock = ""

    # Build our docker command ensuring the nvidia socket is attached if we're in gpu mode
    docker_command = f"""{docker_process} run \
        -v /tmp/codalab-v2:/tmp/codalab-v2 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        {nvidia_sock} \
        -d \
        --env BROKER_URL={broker_url} \
        --restart unless-stopped \
        --log-opt max-size=50m \
        --log-opt max-file=3 \
        {docker_image}"""

    # Stop and remove containers
    run("docker stop $(docker ps -aq)")
    run("docker rm $(docker ps -aq)")

    # Make sure we have latest image
    run(f"docker pull {docker_image}")
    run(f"{docker_command}")
