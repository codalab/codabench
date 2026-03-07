import os
import uuid
from datetime import timedelta

import requests
from azure.storage.blob import BlobSasPermissions
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.utils.timezone import now

from utils.storage import BundleStorage

import logging
logger = logging.getLogger(__name__)


@deconstructible
class PathWrapper(object):
    """Helper to generate UUID's in file names while maintaining their extension"""

    def __init__(self, base_directory, manual_override=False):
        self.path = base_directory
        self.manual_override = manual_override

    def __call__(self, instance, filename):
        if not self.manual_override:
            name, extension = os.path.splitext(filename)
            truncated_uuid = uuid.uuid4().hex[0:12]
            truncated_name = name[0:35]

            path = os.path.join(
                self.path,
                now().strftime('%Y-%m-%d-%s'),
                truncated_uuid,
                "{0}{1}".format(truncated_name, extension)
            )
        else:
            path = os.path.join(
                filename
            )

        return path


def make_url_sassy(path, permission='r', duration=60 * 60 * 24 * 5, content_type='application/zip'):
    assert permission in ('r', 'w'), "SASSY urls only support read and write ('r' or 'w' permission)"

    client_method = None  # defined based on storage backend

    if settings.STORAGE_IS_S3:
        # Remove the beginning of the URL (before bucket name) so we just have the path to the file
        path = path.split(settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)[-1]

        # remove prepended slash
        if path.startswith('/'):
            path = path[1:]

        # Spaces replaced with +'s, so we have to replace those...
        path = path.replace('+', ' ')

        params = {
            'Bucket': settings.AWS_STORAGE_PRIVATE_BUCKET_NAME,
            'Key': path,
        }

        # AWS uses method instead of permission
        if permission == 'r':
            client_method = 'get_object'
        elif permission == 'w':
            client_method = 'put_object'

            if content_type:
                params["ContentType"] = content_type

        return BundleStorage.bucket.meta.client.generate_presigned_url(
            client_method,
            Params=params,
            ExpiresIn=duration,
        )
    elif settings.STORAGE_IS_GCS:
        if permission == 'r':
            client_method = 'GET'
        elif permission == 'w':
            client_method = 'PUT'

        bucket = BundleStorage.client.get_bucket(settings.GS_PRIVATE_BUCKET_NAME)
        return bucket.blob(path).generate_signed_url(
            expiration=now() + timedelta(seconds=duration),
            method=client_method,
            content_type=content_type,
        )
    elif settings.STORAGE_IS_AZURE:
        if permission == 'r':
            client_method = BlobSasPermissions(read=True)
        elif permission == 'w':
            client_method = BlobSasPermissions(read=True, write=True)

        sas_token = BundleStorage.service.generate_blob_shared_access_signature(
            BundleStorage.azure_container,
            path,
            client_method,
            expiry=now() + timedelta(seconds=duration),
        )

        return BundleStorage.service.make_blob_url(
            container_name=BundleStorage.azure_container,
            blob_name=path,
            sas_token=sas_token,
        )


def put_blob(url, file_path):
    return requests.put(
        url,
        data=open(file_path, 'rb'),
        headers={
            # Only for Azure but AWS ignores this fine
            'x-ms-blob-type': 'BlockBlob',
        }
    )


def pretty_bytes(bytes, decimal_places=1, suffix="B", binary=False, return_0_for_invalid=False):

    # Ensure bytes is a valid number
    try:
        bytes = float(bytes)
    except (ValueError, TypeError):
        return 0 if return_0_for_invalid else ""  # Return 0 or empty string for invalid inputs

    if bytes < 0:
        return 0 if return_0_for_invalid else ""  # Return 0 or empty string for invalid inputs

    factor = 1024.0 if binary else 1000.0
    units = ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'] if binary else ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']

    for unit in units:
        if abs(bytes) < factor or unit == (units[-1] + "B"):
            return f"{bytes:.{decimal_places}f} {unit}{suffix}"
        bytes /= factor

    return f"{bytes:.{decimal_places}f}{units[-1]}{suffix}"


def gb_to_bytes(gb, binary=False):
    factor = 1024**3 if binary else 1000**3
    return gb * factor
