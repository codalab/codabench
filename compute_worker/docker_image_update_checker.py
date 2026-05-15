import json
import urllib.request
from datetime import datetime
import docker


class DockerImageStatus:
    UP_TO_DATE = "up_to_date"
    BEHIND = "behind"
    NEWER_LOCAL = "newer_local"
    DIFFERENT = "different"
    LOCAL_MISSING = "local_missing"
    REMOTE_UNAVAILABLE = "remote_unavailable"


class DockerImageUpdateChecker:

    def __init__(self, namespace: str, repository: str, tag: str, docker_base_url):
        self.image_name = f"{namespace}/{repository}:{tag}"
        self.url = f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repository}/tags/{tag}"
        self.client = docker.APIClient(base_url=docker_base_url, version="auto")

    @staticmethod
    def _parse_datetime(value: str):
        if not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _get_json(url: str):
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode())
        except Exception:
            return None

    def get_remote_info(self):

        data = self._get_json(self.url)
        if not data:
            return None

        return {
            "digest": data.get("digest"),
            "date": self._parse_datetime(
                data.get("tag_last_pushed") or data.get("last_updated")
            ),
        }

    def get_local_info(self):
        try:
            image = self.client.inspect_image(self.image_name)
            return {
                "id": image.get("Id"),
                "digests": image.get("RepoDigests", []),
                "date": self._parse_datetime(image.get("Created")),
            }
        except docker.errors.DockerException:
            return None

    def _get_status(self, remote: dict, local: dict):
        remote_digest = remote.get("digest")
        local_digests = local.get("digests", [])

        if remote_digest and any(
            remote_digest in digest for digest in local_digests
        ):
            return DockerImageStatus.UP_TO_DATE

        remote_date = remote.get("date")
        local_date = local.get("date")

        if remote_date and local_date:
            if remote_date > local_date:
                return DockerImageStatus.BEHIND

            if remote_date < local_date:
                return DockerImageStatus.NEWER_LOCAL

        return DockerImageStatus.DIFFERENT

    def compare_local_vs_remote_images(self):

        try:
            remote = self.get_remote_info()
            local = self.get_local_info()

            if not remote:
                return {
                    "status": DockerImageStatus.REMOTE_UNAVAILABLE,
                    "image_name": self.image_name,
                }

            if not local:
                return {
                    "status": DockerImageStatus.LOCAL_MISSING,
                    "image_name": self.image_name,
                    "remote": remote,
                }

            return {
                "status": self._get_status(remote, local),
                "image_name": self.image_name,
                "remote": remote,
                "local": local,
            }
        except Exception as exc:
            return {
                "status": "error",
                "image_name": self.image_name,
                "error": str(exc),
            }
