import os
import uuid

from datetime import timedelta

from utils.storage import BundleStorage

from azure.storage.blob import BlobPermissions

from django.conf import settings
from django.utils.timezone import now
from django.utils.deconstruct import deconstructible


@deconstructible
class PathWrapper(object):
    """Helper to generate UUID's in file names while maintaining their extension"""

    def __init__(self, base_directory):
        self.path = base_directory

    def __call__(self, instance, filename):
        name, extension = os.path.splitext(filename)
        truncated_uuid = uuid.uuid4().hex[0:12]
        truncated_name = name[0:35]

        return os.path.join(
            self.path,
            now().strftime('%Y-%m-%d-%s'),
            truncated_uuid,
            "{0}{1}".format(truncated_name, extension)
        )


def make_url_sassy(path, permission='r', duration=60 * 60 * 24, content_type='application/zip'):
    assert permission in ('r', 'w'), "SASSY urls only support read and write ('r' or 'w' permission)"

    client_method = None  # defined based on storage backend

    if settings.STORAGE_IS_S3:
        # Remove the beginning of the URL (before bucket name) so we just have the path to the file
        path = path.split(settings.AWS_STORAGE_PRIVATE_BUCKET_NAME)[-1]

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
            client_method = BlobPermissions.READ
        elif permission == 'w':
            client_method = BlobPermissions.WRITE

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
