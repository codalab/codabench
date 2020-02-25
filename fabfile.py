import os
import yaml

from fabric.api import env, run


host_types = yaml.load(open('server_config.yaml').read())
env.roledefs = host_types


def status():
    run("docker ps")


def update():
    if not env.effective_roles:
        print("ERROR: You must specify a role when running this task. I.e. fab -R some-gpu task_name`")
        return
    if len(env.effective_roles) > 1:
        print("ERROR: Only specify 1 role (because we need 1 broker_url) when running this task")
        return

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

    docker_command = f"""{docker_process} run \
        -v /tmp/codalab-v2:/tmp/codalab-v2 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        {nvidia_sock} \
        -d \
        --env BROKER_URL={broker_url} \
        --restart unless-stopped \
        --log-opt max-size=50m \
        --log-opt max-file=3 \
        {docker_image}
    """

    # Stop and remove containers
    run("docker stop $(docker ps -aq)")
    run("docker rm $(docker ps -aq)")

    # Make sure we have latest image
    run(f"docker pull {docker_image}")
    run(f"{docker_command}")
